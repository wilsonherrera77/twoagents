"""Centro de control para lanzar y observar la colaboración entre agentes."""

from __future__ import annotations

import argparse
import json
import signal
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import Optional

import requests

from V10.core.orchestrator_v10_async import OrchestratorSettings, OrchestratorV10Async
from V10.utils import get_runtime_root


class StreamForwarder(threading.Thread):
    """Reenvía líneas de un stream de proceso a la salida estándar."""

    def __init__(self, stream, prefix: str) -> None:
        super().__init__(daemon=True)
        self.stream = stream
        self.prefix = prefix
        self._stop_event = threading.Event()

    def run(self) -> None:  # pragma: no cover - flujo interactivo
        for line in iter(self.stream.readline, ""):
            if self._stop_event.is_set():
                break
            if not line:
                continue
            text = line.rstrip()
            if text:
                print(f"[{self.prefix}] {text}")

    def stop(self) -> None:
        self._stop_event.set()


class ControlCenter:
    """Orquesta el servicio Claude y el orquestador en una sola herramienta."""

    def __init__(
        self,
        objective: str,
        *,
        project_name: Optional[str] = None,
        workspace: Optional[Path] = None,
        start_service: bool = True,
        open_browser: bool = False,
        pm_timeout: int = 60,
        dev_timeout: int = 180,
        iterations: int = 3,
    ) -> None:
        self.objective = objective
        self.project_name = project_name
        self.workspace = workspace or get_runtime_root() / "projects"
        self.start_service = start_service
        self.open_browser = open_browser
        self.pm_timeout = pm_timeout
        self.dev_timeout = dev_timeout
        self.iterations = iterations

        self._service_process: Optional[subprocess.Popen[str]] = None
        self._service_forwarder: Optional[StreamForwarder] = None

    # ------------------------------------------------------------------
    # Ejecución principal
    # ------------------------------------------------------------------
    def run(self) -> int:
        print("🚀 Discovery Motor V10 - Centro de Control")
        print("📌 Objetivo:", self.objective)

        if self.start_service:
            self._launch_service()
        else:
            print("⚠️  Asumiendo que el servicio Claude ya está ejecutándose en http://localhost:5000")

        if self.open_browser:
            self._open_browser()

        self.workspace.mkdir(parents=True, exist_ok=True)
        settings = OrchestratorSettings(
            workspace_dir=self.workspace,
            pm_timeout=self.pm_timeout,
            dev_timeout=self.dev_timeout,
            max_iterations=self.iterations,
        )

        orchestrator = OrchestratorV10Async(settings=settings)
        orchestrator.bus.logger.level = "INFO"
        try:
            result = orchestrator.execute(self.objective, project_name=self.project_name)
            print("\n📄 Resultado final:")
            print(json.dumps(result, indent=2, ensure_ascii=False))
            status = result.get("status", "FAILED")
            return 0 if status == "SUCCESS" else 1
        except KeyboardInterrupt:  # pragma: no cover - modo interactivo
            print("\n❌ Ejecución interrumpida por el usuario")
            return 1
        finally:
            self.shutdown()

    # ------------------------------------------------------------------
    # Gestión del servicio Claude
    # ------------------------------------------------------------------
    def _launch_service(self) -> None:
        print("▶️  Iniciando servicio Claude local...")
        command = [sys.executable, "-m", "V10.claude_service"]
        self._service_process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        assert self._service_process.stdout is not None
        self._service_forwarder = StreamForwarder(self._service_process.stdout, "CLAUDE")
        self._service_forwarder.start()
        self._wait_for_service()

    def _wait_for_service(self, timeout: int = 30) -> None:
        deadline = time.time() + timeout
        url = "http://localhost:5000/health"
        while time.time() < deadline:
            try:
                response = requests.get(url, timeout=2)
                if response.status_code == 200:
                    print("✅ Servicio Claude listo en http://localhost:5000")
                    return
            except requests.RequestException:
                time.sleep(1)
        raise RuntimeError("No se pudo conectar con el servicio Claude en el tiempo esperado")

    def _open_browser(self) -> None:
        print("🌐 Abriendo interfaz web del servicio Claude...")
        try:
            import webbrowser

            webbrowser.open("http://localhost:5000", new=2)
        except Exception as exc:  # pragma: no cover - depende de OS
            print(f"⚠️  No se pudo abrir el navegador automáticamente: {exc}")

    # ------------------------------------------------------------------
    # Limpieza
    # ------------------------------------------------------------------
    def shutdown(self) -> None:
        if self._service_forwarder:
            self._service_forwarder.stop()
        if self._service_process and self._service_process.poll() is None:
            print("⏹️  Deteniendo servicio Claude...")
            if sys.platform != "win32":  # pragma: no cover - dependencia del entorno
                self._service_process.send_signal(signal.SIGINT)
                try:
                    self._service_process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    self._service_process.terminate()
            else:
                self._service_process.terminate()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Lanza el orquestador V10 y el servicio Claude desde una sola consola",
    )
    parser.add_argument("objective", help="Objetivo del proyecto a resolver")
    parser.add_argument("--project-name", help="Nombre opcional del proyecto")
    parser.add_argument(
        "--workspace",
        help="Directorio base para almacenar los proyectos generados",
    )
    parser.add_argument(
        "--skip-service",
        action="store_true",
        help="No iniciar el servicio Claude (usar si ya está ejecutándose)",
    )
    parser.add_argument(
        "--open-browser",
        action="store_true",
        help="Abrir la interfaz web del servicio Claude automáticamente",
    )
    parser.add_argument("--pm-timeout", type=int, default=60, help="Timeout del PM agent en segundos")
    parser.add_argument("--dev-timeout", type=int, default=180, help="Timeout del Dev agent en segundos")
    parser.add_argument("--iterations", type=int, default=3, help="Iteraciones máximas del feedback loop")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    workspace = Path(args.workspace).expanduser().resolve() if args.workspace else None
    control = ControlCenter(
        args.objective,
        project_name=args.project_name,
        workspace=workspace,
        start_service=not args.skip_service,
        open_browser=args.open_browser,
        pm_timeout=args.pm_timeout,
        dev_timeout=args.dev_timeout,
        iterations=args.iterations,
    )
    return control.run()


if __name__ == "__main__":  # pragma: no cover - CLI manual
    raise SystemExit(main())
