"""Asynchronous orchestrator that coordinates all V10 agents."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Any

from V10.agents.dev_agent_v10 import DevAgentV10
from V10.agents.pm_agent_v10 import start_pm_worker
from V10.agents.qa_agent_v10 import QAAgentV10
from V10.agents.security_agent_v10 import SecurityAgentV10
from V10.core.message_bus import FileMessageBus
from V10.protocols import Architecture
from V10.utils import create_logger, get_runtime_root


@dataclass
class OrchestratorSettings:
    workspace_dir: Path
    use_pm_worker: bool = True
    pm_timeout: int = 60
    min_security_score: float = 7.0
    min_qa_score: float = 7.0


class OrchestratorV10Async:
    """Coordinates PM, Dev, Security and QA agents through the file bus."""

    def __init__(self, settings: Optional[OrchestratorSettings] = None) -> None:
        runtime_root = get_runtime_root()
        default_workspace = runtime_root / "workspace"
        settings = settings or OrchestratorSettings(workspace_dir=default_workspace)
        self.settings = settings
        self.logger = create_logger("ORCHESTRATOR")
        self.logger.set_state("INITIALIZED")

        self.bus = FileMessageBus()
        self.dev_agent = DevAgentV10(workspace_dir=str(self.settings.workspace_dir))
        self.security_agent = SecurityAgentV10()
        self.qa_agent = QAAgentV10()

        self.pm_worker_stop = None
        if self.settings.use_pm_worker:
            self.pm_worker_stop = start_pm_worker(self.bus)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def execute(self, objective: str, project_name: Optional[str] = None) -> Dict[str, Any]:
        self.logger.set_state("RUNNING")
        start_time = datetime.now()
        result: Dict[str, Any] = {
            "objective": objective,
            "status": "running",
            "stages": {},
        }

        try:
            architecture = self._run_pm_stage(objective)
            result["stages"]["pm"] = {
                "status": "SUCCESS",
                "modules": len(architecture.proposed_modules),
                "technologies": architecture.technologies,
            }

            implementation = self.dev_agent.generate_project(architecture, project_name)
            if implementation is None:
                raise RuntimeError("Developer agent failed to create the project")
            result["stages"]["dev"] = {
                "status": "SUCCESS",
                "project_dir": implementation.project_dir,
                "files_count": implementation.files_count,
            }

            security_result = self.security_agent.analyze(implementation.project_dir)
            result["stages"]["security"] = {
                "status": "PASS" if security_result.passed else "FAIL",
                "score": security_result.score,
                "critical_issues": security_result.critical_issues,
            }

            qa_result = self.qa_agent.analyze(implementation.project_dir)
            result["stages"]["qa"] = {
                "status": "PASS" if qa_result.passed else "FAIL",
                "score": qa_result.score,
                "issues": qa_result.issues,
            }

            combined_score = (security_result.score + qa_result.score) / 2
            gates_passed = (
                security_result.score >= self.settings.min_security_score
                and qa_result.score >= self.settings.min_qa_score
                and not security_result.critical_issues
            )
            result["combined_score"] = round(combined_score, 1)
            result["status"] = "SUCCESS" if gates_passed else "PARTIAL_SUCCESS"
            result["decision"] = "APPROVED" if gates_passed else "REVIEW_REQUIRED"

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
    # Internal helpers
    # ------------------------------------------------------------------
    def _run_pm_stage(self, objective: str) -> Architecture:
        self.logger.info("Requesting architecture from PM agent")
        message = self.bus.send(
            sender="orchestrator",
            recipient="pm",
            payload={"objective": objective},
        )
        reply = self.bus.wait_for_reply(
            agent_name="orchestrator",
            in_reply_to=message.message_id,
            timeout=self.settings.pm_timeout,
        )
        if reply is None:
            raise TimeoutError("PM agent did not respond on time")
        payload = reply.payload
        if payload.get("status") != "SUCCESS":
            raise RuntimeError(payload.get("error", "PM agent returned an error"))
        arch_data = payload["architecture"]
        return Architecture(
            proposed_modules=arch_data["proposed_modules"],
            database_schema=arch_data["database_schema"],
            technologies=arch_data["technologies"],
            analysis=arch_data["analysis"],
            reasoning=arch_data["reasoning"],
        )

    def _persist_report(self, result: Dict[str, Any]) -> Path:
        reports_dir = get_runtime_root() / "reports"
        reports_dir.mkdir(parents=True, exist_ok=True)
        report_path = reports_dir / f"report_{datetime.now():%Y%m%d_%H%M%S}.json"
        with report_path.open("w", encoding="utf-8") as handle:
            json.dump(result, handle, indent=2)
        self.logger.success("Pipeline report stored", {"path": str(report_path)})
        return report_path

    def _shutdown(self) -> None:
        if self.pm_worker_stop is not None:
            self.pm_worker_stop.set()
            thread = getattr(self.pm_worker_stop, "thread", None)
            if thread is not None:
                thread.join(timeout=2)
            self.logger.info("PM worker stopped")


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Run the V10 orchestrator asynchronously")
    parser.add_argument("objective", help="Project objective to be solved")
    parser.add_argument("--project-name", help="Optional name for the generated project")
    parser.add_argument("--workspace", help="Workspace directory", default=None)
    parser.add_argument("--pm-timeout", type=int, default=60, help="Timeout for PM responses")
    parser.add_argument("--no-worker", action="store_true", help="Do not spawn the PM worker (for manual tests)")

    args = parser.parse_args()

    workspace = Path(args.workspace) if args.workspace else None
    settings = OrchestratorSettings(
        workspace_dir=workspace or get_runtime_root() / "workspace",
        use_pm_worker=not args.no_worker,
        pm_timeout=args.pm_timeout,
    )

    orchestrator = OrchestratorV10Async(settings=settings)
    result = orchestrator.execute(args.objective, project_name=args.project_name)
    print(json.dumps(result, indent=2))
    return 0 if result.get("status") == "SUCCESS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
