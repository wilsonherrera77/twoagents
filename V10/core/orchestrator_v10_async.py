"""Orquestador asíncrono que coordina los agentes V10 vía servicio LLM local."""

from __future__ import annotations

import json
import threading
import uuid
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from V10.agents.dev_agent_v10 import DevAgentV10
from V10.agents.pm_agent_v10 import PMAgentV10
from V10.agents.qa_agent_v10 import QAAgentV10
from V10.agents.security_agent_v10 import SecurityAgentV10
from V10.core.feedback_loop import FeedbackLoop
from V10.core.message_bus import FileMessageBus
from V10.utils import create_logger, ensure_directory, get_runtime_root


@dataclass
class OrchestratorSettings:
    workspace_dir: Path
    use_feedback_loop: bool = True
    pm_timeout: int = 60
    dev_timeout: int = 180
    max_iterations: int = 3


class OrchestratorV10Async:
    """Coordina PM, Dev, Security y QA usando el bus de mensajes."""

    def __init__(self, settings: Optional[OrchestratorSettings] = None) -> None:
        runtime_root = get_runtime_root()
        default_workspace = runtime_root / "projects"
        settings = settings or OrchestratorSettings(workspace_dir=default_workspace)
        self.settings = settings

        self.logger = create_logger("ORCHESTRATOR")
        self.logger.set_state("INITIALIZED")

        ensure_directory(self.settings.workspace_dir)
        self.session_id = f"session_{datetime.now():%Y%m%d_%H%M%S}_{uuid.uuid4().hex[:6]}"
        agents_dir = ensure_directory(get_runtime_root() / "agents" / self.session_id)
        self.bus = FileMessageBus(base_dir=agents_dir)
        self.workspace_root = ensure_directory(self.settings.workspace_dir / self.session_id)

        self.logger.info(
            "Session initialized",
            {
                "session_id": self.session_id,
                "agents_dir": str(agents_dir),
                "workspace_root": str(self.workspace_root),
            },
        )

        self.pm_agent = PMAgentV10(self.bus)
        self.dev_agent = DevAgentV10(self.bus)
        self.feedback_loop = FeedbackLoop(self.bus, max_iterations=self.settings.max_iterations)

        self.stop_event = threading.Event()
        self.security_thread = threading.Thread(target=self._security_worker, name="SecurityWorker", daemon=True)
        self.qa_thread = threading.Thread(target=self._qa_worker, name="QAWorker", daemon=True)

        self.pm_agent.start()
        self.dev_agent.start()
        self.security_thread.start()
        self.qa_thread.start()

    # ------------------------------------------------------------------
    # API pública
    # ------------------------------------------------------------------
    def execute(self, objective: str, project_name: Optional[str] = None) -> Dict[str, Any]:
        self.logger.set_state("RUNNING")
        start_time = datetime.now()
        result: Dict[str, Any] = {
            "objective": objective,
            "status": "running",
            "stages": {},
        }
        result["session_id"] = self.session_id
        result["workspace_root"] = str(self.workspace_root)

        project_dir = self._prepare_project_dir(project_name or objective)

        try:
            architecture_payload = self._request_architecture(objective, project_dir)
            result["stages"]["pm"] = {
                "status": "SUCCESS",
                "spec": architecture_payload.get("spec", {}),
            }

            implementation_payload = self._wait_for_dev_completion()
            if implementation_payload.get("status") != "SUCCESS":
                raise RuntimeError(implementation_payload.get("error", "Dev agent error"))

            project_path = implementation_payload.get("project_path", str(project_dir))
            result["stages"]["dev"] = {
                "status": "SUCCESS",
                "project_dir": project_path,
                "files": implementation_payload.get("files", []),
            }

            if self.settings.use_feedback_loop:
                feedback_passed = self.feedback_loop.iterate_until_pass(project_path)
            else:
                feedback_passed = True

            security_payload = self._request_security_report(project_path)
            qa_payload = self._request_qa_report(project_path)

            result["stages"]["security"] = {
                "status": "PASS" if security_payload.get("passed") else "FAIL",
                "score": security_payload.get("score"),
                "issues": security_payload.get("issues", []),
                "critical_issues": security_payload.get("critical_issues", []),
            }

            result["stages"]["qa"] = {
                "status": "PASS" if qa_payload.get("passed") else "FAIL",
                "score": qa_payload.get("score"),
                "issues": qa_payload.get("issues", []),
                "warnings": qa_payload.get("warnings", []),
            }

            combined_score = 0.0
            if security_payload.get("score") is not None and qa_payload.get("score") is not None:
                combined_score = (security_payload.get("score", 0.0) + qa_payload.get("score", 0.0)) / 2

            result["combined_score"] = round(combined_score, 2)
            gates_passed = security_payload.get("passed") and qa_payload.get("passed")
            result["status"] = "SUCCESS" if gates_passed and feedback_passed else "REVIEW_REQUIRED"
            result["decision"] = "APPROVED" if gates_passed and feedback_passed else "MANUAL_REVIEW"
            result["project_path"] = project_path

            report_path = self._persist_report(result)
            result["report_path"] = str(report_path)
        except Exception as exc:
            self.logger.error("Pipeline failed", {"error": str(exc)})
            result["status"] = "FAILED"
            result["error"] = str(exc)
        finally:
            duration = self.logger.measure_time("Pipeline", start_time)
            result["duration"] = duration
            self.logger.set_state("COMPLETED")
            self._shutdown()
        return result

    # ------------------------------------------------------------------
    # Etapas internas
    # ------------------------------------------------------------------
    def _request_architecture(self, objective: str, project_dir: Path) -> Dict[str, Any]:
        self.logger.info("Solicitando especificaciones al PM agent")
        message = self.bus.send(
            sender="orchestrator",
            recipient="pm_agent",
            payload={"objective": objective, "project_path": str(project_dir)},
        )
        reply = self.bus.wait_for_reply(
            agent_name="orchestrator",
            in_reply_to=message.message_id,
            timeout=self.settings.pm_timeout,
        )
        if reply is None:
            raise TimeoutError("PM agent no respondió a tiempo")
        payload = reply.payload
        if payload.get("status") not in (None, "SUCCESS"):
            raise RuntimeError(payload.get("error", "PM agent retornó un error"))
        return payload

    def _wait_for_dev_completion(self) -> Dict[str, Any]:
        self.logger.info("Esperando a que Dev agent finalice el proyecto")
        timeout = self.settings.dev_timeout
        deadline = datetime.now().timestamp() + timeout
        while datetime.now().timestamp() < deadline:
            message = self.bus.receive("orchestrator", timeout=1.0)
            if message is None:
                continue
            if message.sender == "dev_agent":
                return message.payload
        raise TimeoutError("Dev agent no finalizó dentro del tiempo esperado")

    def _request_security_report(self, project_path: str) -> Dict[str, Any]:
        payload = self.feedback_loop.last_security_payload
        if payload.get("project_path") == project_path and payload:
            return payload
        message = self.bus.send(
            sender="orchestrator",
            recipient="security_agent",
            payload={"project_path": project_path},
        )
        reply = self.bus.wait_for_reply(
            agent_name="orchestrator",
            in_reply_to=message.message_id,
            timeout=60.0,
        )
        if reply is None:
            raise TimeoutError("Security agent no respondió")
        return reply.payload

    def _request_qa_report(self, project_path: str) -> Dict[str, Any]:
        payload = self.feedback_loop.last_qa_payload
        if payload.get("project_path") == project_path and payload:
            return payload
        message = self.bus.send(
            sender="orchestrator",
            recipient="qa_agent",
            payload={"project_path": project_path},
        )
        reply = self.bus.wait_for_reply(
            agent_name="orchestrator",
            in_reply_to=message.message_id,
            timeout=60.0,
        )
        if reply is None:
            raise TimeoutError("QA agent no respondió")
        return reply.payload

    def _persist_report(self, result: Dict[str, Any]) -> Path:
        reports_dir = get_runtime_root() / "reports"
        reports_dir.mkdir(parents=True, exist_ok=True)
        report_path = reports_dir / f"report_{datetime.now():%Y%m%d_%H%M%S}.json"
        with report_path.open("w", encoding="utf-8") as handle:
            json.dump(result, handle, indent=2)
        self.logger.success("Reporte generado", {"path": str(report_path)})
        return report_path

    def _prepare_project_dir(self, project_name: str) -> Path:
        slug = "_".join(project_name.lower().split())
        base = self.workspace_root / slug
        candidate = base
        counter = 1
        while candidate.exists():
            counter += 1
            candidate = self.workspace_root / f"{slug}_{counter}"
        ensure_directory(candidate)
        return candidate

    # ------------------------------------------------------------------
    # Workers auxiliares
    # ------------------------------------------------------------------
    def _security_worker(self) -> None:
        agent = SecurityAgentV10()
        while not self.stop_event.is_set():
            message = self.bus.receive("security_agent", timeout=1.0)
            if message is None:
                continue
            project_path = message.payload.get("project_path")
            if not project_path:
                self.bus.send(
                    sender="security_agent",
                    recipient=message.sender,
                    payload={"error": "project_path requerido"},
                    conversation_id=message.conversation_id,
                    in_reply_to=message.message_id,
                )
                continue
            result = agent.analyze(project_path)
            payload = {
                "project_path": project_path,
                "score": result.score,
                "issues": result.issues,
                "critical_issues": result.critical_issues,
                "warnings": result.warnings,
                "passed": result.passed,
            }
            self.bus.send(
                sender="security_agent",
                recipient=message.sender,
                payload=payload,
                conversation_id=message.conversation_id,
                in_reply_to=message.message_id,
            )

    def _qa_worker(self) -> None:
        agent = QAAgentV10()
        while not self.stop_event.is_set():
            message = self.bus.receive("qa_agent", timeout=1.0)
            if message is None:
                continue
            project_path = message.payload.get("project_path")
            if not project_path:
                self.bus.send(
                    sender="qa_agent",
                    recipient=message.sender,
                    payload={"error": "project_path requerido"},
                    conversation_id=message.conversation_id,
                    in_reply_to=message.message_id,
                )
                continue
            result = agent.analyze(project_path)
            payload = {
                "project_path": project_path,
                "score": result.score,
                "issues": result.issues,
                "warnings": result.warnings,
                "passed": result.passed,
                "suggestions": result.issues + result.warnings,
            }
            self.bus.send(
                sender="qa_agent",
                recipient=message.sender,
                payload=payload,
                conversation_id=message.conversation_id,
                in_reply_to=message.message_id,
            )

    def _shutdown(self) -> None:
        self.stop_event.set()
        self.pm_agent.stop()
        self.dev_agent.stop()
        self.security_thread.join(timeout=2)
        self.qa_thread.join(timeout=2)
        self.logger.info("Orquestador detenido")


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Run the V10 orchestrator asynchronously")
    parser.add_argument("objective", help="Project objective to be solved")
    parser.add_argument("--project-name", help="Optional project name")
    parser.add_argument("--workspace", help="Workspace directory", default=None)
    parser.add_argument("--pm-timeout", type=int, default=60)
    parser.add_argument("--dev-timeout", type=int, default=180)
    parser.add_argument("--iterations", type=int, default=3)

    args = parser.parse_args()

    workspace = Path(args.workspace) if args.workspace else get_runtime_root() / "projects"
    settings = OrchestratorSettings(
        workspace_dir=workspace,
        pm_timeout=args.pm_timeout,
        dev_timeout=args.dev_timeout,
        max_iterations=args.iterations,
    )

    orchestrator = OrchestratorV10Async(settings=settings)
    result = orchestrator.execute(args.objective, project_name=args.project_name)
    print(json.dumps(result, indent=2))
    return 0 if result.get("status") == "SUCCESS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
