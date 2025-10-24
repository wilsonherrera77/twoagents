"""Dev Agent V10 - Genera código usando un servicio LLM local."""

from __future__ import annotations

import ast
import json
import threading
from pathlib import Path
from typing import Dict, List, Optional, Sequence

import requests

from V10.core.message_bus import FileMessageBus
from V10.utils import create_logger, ensure_directory, get_runtime_root


class DevAgentV10:
    """Agente de desarrollo que solicita código al servicio LLM local."""

    AGENT_NAME = "dev_agent"

    def __init__(
        self,
        message_bus: FileMessageBus,
        llm_endpoint: str = "http://localhost:5000/generate",
    ) -> None:
        self.message_bus = message_bus
        self.llm_endpoint = llm_endpoint
        self.logger = create_logger("DEV_AGENT")
        self.project_root = ensure_directory(get_runtime_root() / "projects")
        self.running = False
        self.thread: Optional[threading.Thread] = None
        self.projects: Dict[str, Dict[str, object]] = {}

    # ------------------------------------------------------------------
    # Ciclo de vida
    # ------------------------------------------------------------------
    def start(self) -> threading.Thread:
        if self.thread and self.thread.is_alive():
            return self.thread
        self.running = True
        self.thread = threading.Thread(target=self.run, name="DevAgentV10", daemon=True)
        self.thread.start()
        self.logger.set_state("RUNNING")
        return self.thread

    def stop(self) -> None:
        self.running = False
        if self.thread:
            self.thread.join(timeout=2)
            self.logger.info("Dev agent detenido")

    # ------------------------------------------------------------------
    # Bucle principal
    # ------------------------------------------------------------------
    def run(self) -> None:
        while self.running:
            message = self.message_bus.receive(self.AGENT_NAME, timeout=1.0)
            if message is None:
                continue

            payload = message.payload
            action = payload.get("action")

            if action == "fix_security":
                fixed = self._handle_security_fix(payload)
                self._reply(message, {"fixed": fixed})
                continue

            if action == "improve_quality":
                improved = self._handle_quality_improvement(payload)
                self._reply(message, {"improved": improved})
                continue

            self.logger.info("Recibida especificación para generación de proyecto")
            try:
                project_path = payload.get("project_path")
                project_dir = self._prepare_project_dir(project_path, payload.get("objective"))
                spec = payload.get("spec", {})
                generated_files = self._generate_modules(project_dir, spec)
                extra_files = self._create_support_files(project_dir, spec)
                all_files = generated_files + extra_files

                self.projects[str(project_dir)] = {
                    "spec": spec,
                    "files": all_files,
                }

                result_payload = {
                    "status": "SUCCESS",
                    "project_path": str(project_dir),
                    "files": all_files,
                    "spec": spec,
                }

                self.message_bus.send(
                    sender=self.AGENT_NAME,
                    recipient="orchestrator",
                    payload=result_payload,
                    conversation_id=message.conversation_id,
                    in_reply_to=message.message_id,
                )

                # Disparar análisis de seguridad inicial
                self.message_bus.send(
                    sender=self.AGENT_NAME,
                    recipient="security_agent",
                    payload={
                        "project_path": str(project_dir),
                        "trigger": "initial",
                    },
                    conversation_id=message.conversation_id,
                )

                self.logger.success("Proyecto generado", {"project_path": str(project_dir)})
            except Exception as exc:
                self.logger.error("Error generando proyecto", {"error": str(exc)})
                failure_payload = {
                    "status": "ERROR",
                    "error": str(exc),
                }
                self.message_bus.send(
                    sender=self.AGENT_NAME,
                    recipient="orchestrator",
                    payload=failure_payload,
                    conversation_id=message.conversation_id,
                    in_reply_to=message.message_id,
                )

    # ------------------------------------------------------------------
    # Generación de código
    # ------------------------------------------------------------------
    def _generate_modules(self, project_dir: Path, spec: Dict[str, object]) -> List[str]:
        modules = spec.get("modules", [])
        generated_files: List[str] = []

        for module_entry in modules:
            module_spec = self._normalize_module(module_entry)
            module_name = module_spec["name"]
            code = self._generate_module_code(module_name, module_spec, spec)
            file_path = self._write_module(project_dir, module_name, code)
            generated_files.append(str(file_path.relative_to(project_dir)))

        return generated_files

    def _generate_module_code(
        self,
        module_name: str,
        module_spec: Dict[str, object],
        project_spec: Dict[str, object],
        extra_context: Optional[str] = None,
    ) -> str:
        """Genera código Python usando el servicio LLM local."""

        dependencies = project_spec.get("dependencies", [])
        prompt = f"""Genera código Python profesional para este módulo:

PROYECTO: {project_spec.get('project_type', 'Unknown')}
ARQUITECTURA: {project_spec.get('architecture', 'N/A')}

MÓDULO: {module_name}
ESPECIFICACIONES DEL MÓDULO: {json.dumps(module_spec, indent=2, ensure_ascii=False)}
DEPENDENCIAS DISPONIBLES: {', '.join(dependencies)}
"""
        if extra_context:
            prompt += f"\nCONTEXTO ADICIONAL:\n{extra_context}\n"

        prompt += """
REQUERIMIENTOS ESTRICTOS:
1. Incluye docstrings completos en español
2. Usa type hints en todas las funciones
3. Maneja errores con try/except apropiados
4. Código listo para producción
5. Sigue PEP 8
6. Incluye logging donde sea relevante

FORMATO DE SALIDA:
- Genera SOLO código Python puro
- Sin bloques markdown (```python)
- Sin explicaciones adicionales
- Código debe ser sintácticamente válido

Genera el archivo {module_name}.py completo:
"""

        try:
            response = requests.post(
                self.llm_endpoint,
                json={"prompt": prompt},
                timeout=60,
            )
            response.raise_for_status()
            result = response.json()
            code = result["response"].strip()
            code = self._clean_code_blocks(code)
            self._validate_syntax(code)
            self.logger.info("Código generado para módulo", {"module": module_name})
            return code
        except requests.RequestException as exc:
            self.logger.error("Error conectando con servicio LLM", {"error": str(exc)})
            return self._generate_fallback_code(module_name)
        except (SyntaxError, ValueError) as exc:
            self.logger.error("Código inválido generado por LLM", {"error": str(exc)})
            return self._generate_fallback_code(module_name)

    def _clean_code_blocks(self, code: str) -> str:
        for marker in ("```python\n", "```python", "```", "``\n"):
            code = code.replace(marker, "")
        return code.strip()

    def _validate_syntax(self, code: str) -> None:
        ast.parse(code)

    def _generate_fallback_code(self, module_name: str) -> str:
        return f'''"""
Módulo {module_name} - Generado en modo fallback.
"""

import logging


def main() -> None:
    """Función principal del módulo."""
    logging.basicConfig(level=logging.INFO)
    logging.info("Módulo {module_name} - Servicio LLM no disponible")


if __name__ == "__main__":
    main()
'''

    # ------------------------------------------------------------------
    # Manejo de acciones correctivas
    # ------------------------------------------------------------------
    def _handle_security_fix(self, payload: Dict[str, object]) -> bool:
        project_path = payload.get("project_path")
        issues: Sequence[str] = payload.get("issues", [])  # type: ignore[assignment]
        if not project_path or str(project_path) not in self.projects:
            return False
        spec = self.projects[str(project_path)].get("spec")
        if not isinstance(spec, dict):
            return False
        targets = self._extract_targets_from_messages(issues)
        context = "\n".join(f"- {issue}" for issue in issues)
        return self._regenerate_modules(str(project_path), spec, targets, context)

    def _handle_quality_improvement(self, payload: Dict[str, object]) -> bool:
        project_path = payload.get("project_path")
        suggestions: Sequence[str] = payload.get("suggestions", [])  # type: ignore[assignment]
        if not project_path or str(project_path) not in self.projects:
            return False
        spec = self.projects[str(project_path)].get("spec")
        if not isinstance(spec, dict):
            return False
        targets = self._extract_targets_from_messages(suggestions)
        context = "\n".join(f"- {suggestion}" for suggestion in suggestions)
        return self._regenerate_modules(str(project_path), spec, targets, context)

    def _regenerate_modules(
        self,
        project_path: str,
        spec: Dict[str, object],
        targets: Sequence[str],
        context: str,
    ) -> bool:
        project_dir = Path(project_path)
        modules = spec.get("modules", [])
        if not modules:
            return False

        normalized_targets = {target for target in targets if target}
        if not normalized_targets:
            normalized_targets = {self._normalize_module(entry)["name"] for entry in modules}

        updated = False
        for module_entry in modules:
            module_spec = self._normalize_module(module_entry)
            module_name = module_spec["name"]
            if module_name not in normalized_targets:
                continue
            code = self._generate_module_code(module_name, module_spec, spec, extra_context=context)
            file_path = self._write_module(project_dir, module_name, code)
            updated = True
            rel_path = str(file_path.relative_to(project_dir))
            if project_path in self.projects:
                files_obj = self.projects[project_path].get("files", [])
                if isinstance(files_obj, list) and rel_path not in files_obj:
                    files_obj.append(rel_path)

        return updated

    def _extract_targets_from_messages(self, messages: Sequence[str]) -> List[str]:
        targets: List[str] = []
        for message in messages:
            if not message:
                continue
            parts = message.split()
            for part in parts:
                if part.endswith(".py"):
                    targets.append(part.replace(".py", ""))
        return targets

    # ------------------------------------------------------------------
    # Utilidades de escritura
    # ------------------------------------------------------------------
    def _write_module(self, project_dir: Path, module_name: str, code: str) -> Path:
        file_name = module_name if module_name.endswith(".py") else f"{module_name}.py"
        file_path = project_dir / file_name
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(code, encoding="utf-8")
        return file_path

    def _create_support_files(self, project_dir: Path, spec: Dict[str, object]) -> List[str]:
        files: List[str] = []
        requirements = project_dir / "requirements.txt"
        dependencies = spec.get("dependencies", [])
        if dependencies:
            requirements.write_text("\n".join(sorted(set(dependencies))) + "\n", encoding="utf-8")
        else:
            requirements.write_text("requests\n", encoding="utf-8")
        files.append(str(requirements.relative_to(project_dir)))

        readme = project_dir / "README.md"
        readme_content = self._render_readme(spec)
        readme.write_text(readme_content, encoding="utf-8")
        files.append(str(readme.relative_to(project_dir)))
        return files

    def _render_readme(self, spec: Dict[str, object]) -> str:
        modules = spec.get("modules", [])
        module_list = "\n".join(f"- {self._normalize_module(module)['name']}" for module in modules)
        dependencies = spec.get("dependencies", [])
        dependencies_list = "\n".join(f"- {dep}" for dep in dependencies)
        return f"""# {spec.get('project_type', 'Proyecto generado')}

## Arquitectura
{spec.get('architecture', 'No especificada')}

## Flujo de Datos
{spec.get('data_flow', 'No disponible')}

## Módulos
{module_list or '- Sin módulos definidos'}

## Dependencias
{dependencies_list or '- requests'}
"""

    def _prepare_project_dir(self, project_path: Optional[str], objective: Optional[str]) -> Path:
        if project_path:
            path = Path(project_path)
            ensure_directory(path)
            return path
        slug = "_".join((objective or "proyecto").lower().split())
        final_dir = self.project_root / slug
        counter = 1
        while final_dir.exists():
            counter += 1
            final_dir = self.project_root / f"{slug}_{counter}"
        ensure_directory(final_dir)
        return final_dir

    def _normalize_module(self, module_entry: object) -> Dict[str, object]:
        if isinstance(module_entry, dict) and "name" in module_entry:
            return module_entry
        if isinstance(module_entry, str):
            return {"name": module_entry}
        raise ValueError(f"Formato de módulo desconocido: {module_entry}")

    def _reply(self, message, payload: Dict[str, object]) -> None:
        self.message_bus.send(
            sender=self.AGENT_NAME,
            recipient=message.sender,
            payload=payload,
            conversation_id=message.conversation_id,
            in_reply_to=message.message_id,
        )
