"""Standalone orchestrator that coordinates multi-terminal agents."""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from V10.core.message_bus import FileMessageBus
from V10.core import message_types
from V10.protocols import Architecture, Implementation, ValidationResult
from V10.utils import create_logger, get_runtime_root


class MultiTerminalOrchestrator:
    """Coordinates PM, Dev, QA and Security agents via the FileMessageBus."""

    def __init__(self, *, workspace: Path, timeouts: Dict[str, float]):
        self.workspace = workspace
        self.timeouts = timeouts
        self.bus = FileMessageBus()
        self.logger = create_logger("ORCH_MAIN")
        self.logger.set_state("READY")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def run(self, objective: str, project_name: Optional[str] = None) -> Dict[str, Any]:
        self.logger.set_state("RUNNING")
        start_time = datetime.utcnow()
        result: Dict[str, Any] = {
            "objective": objective,
            "status": "RUNNING",
            "stages": {},
        }

        try:
            architecture = self._request_architecture(objective)
            result["stages"]["pm"] = {
                "status": "SUCCESS",
                "modules": len(architecture.proposed_modules),
                "technologies": architecture.technologies,
            }

            implementation = self._request_implementation(architecture, project_name)
            result["stages"]["dev"] = {
                "status": "SUCCESS",
                "project_dir": implementation.project_dir,
                "files_count": implementation.files_count,
            }

            security_report = self._request_security_review(implementation.project_dir)
            result["stages"]["security"] = {
                "status": "PASS" if security_report.passed else "FAIL",
                "score": security_report.score,
                "critical_issues": security_report.critical_issues,
            }

            qa_report = self._request_qa_review(implementation.project_dir)
            result["stages"]["qa"] = {
                "status": "PASS" if qa_report.passed else "FAIL",
                "score": qa_report.score,
                "issues": qa_report.issues,
            }

            combined_score = (security_report.score + qa_report.score) / 2
            result["combined_score"] = round(combined_score, 1)
            result["status"] = "SUCCESS"
            result["decision"] = "APPROVED"
            result["architecture"] = architecture.to_dict()
            result["implementation"] = implementation.to_dict()
            result["qa_report"] = qa_report.to_dict()
            result["security_report"] = security_report.to_dict()

            report_path = self._persist_report(result)
            result["report_path"] = str(report_path)
        except Exception as exc:  # pragma: no cover - safety
            self.logger.error("Pipeline failed", {"error": str(exc)})
            result["status"] = "FAILED"
            result["error"] = str(exc)
        finally:
            duration = (datetime.utcnow() - start_time).total_seconds()
            result["duration"] = duration
            self.logger.set_state("COMPLETED")
        return result

    # ------------------------------------------------------------------
    # Message helpers
    # ------------------------------------------------------------------
    def _request_architecture(self, objective: str) -> Architecture:
        self.logger.info("Requesting architecture", {"objective": objective})
        message = self.bus.send(
            sender="orchestrator",
            recipient="pm",
            payload={
                "type": message_types.REQUEST_ARCHITECTURE,
                "objective": objective,
            },
        )
        reply = self.bus.wait_for_reply(
            agent_name="orchestrator",
            in_reply_to=message.message_id,
            timeout=self.timeouts["pm"],
        )
        if reply is None:
            raise TimeoutError("PM agent did not respond in time")
        payload = reply.payload or {}
        if payload.get("status") != "SUCCESS":
            raise RuntimeError(payload.get("error", "PM agent reported failure"))
        arch_data = payload.get("architecture", {})
        return Architecture(
            proposed_modules=arch_data.get("proposed_modules", []),
            database_schema=arch_data.get("database_schema", {}),
            technologies=arch_data.get("technologies", {}),
            analysis=arch_data.get("analysis", ""),
            reasoning=arch_data.get("reasoning", ""),
        )

    def _request_implementation(self, architecture: Architecture, project_name: Optional[str]) -> Implementation:
        payload = {
            "type": message_types.REQUEST_IMPLEMENTATION,
            "architecture": architecture.to_dict(),
            "project_name": project_name,
        }
        self.logger.info("Requesting implementation", {"project_name": project_name})
        message = self.bus.send(
            sender="orchestrator",
            recipient="dev",
            payload=payload,
        )
        reply = self.bus.wait_for_reply(
            agent_name="orchestrator",
            in_reply_to=message.message_id,
            timeout=self.timeouts["dev"],
        )
        if reply is None:
            raise TimeoutError("Dev agent did not respond in time")
        resp_payload = reply.payload or {}
        if resp_payload.get("status") != "SUCCESS":
            raise RuntimeError(resp_payload.get("error", "Dev agent reported failure"))
        impl_data = resp_payload.get("implementation", {})
        return Implementation(
            project_dir=impl_data.get("project_dir", str(self.workspace)),
            files_created=impl_data.get("files_created", []),
            files_count=impl_data.get("files_count", 0),
            technologies=impl_data.get("technologies", {}),
            timestamp=impl_data.get("timestamp") or datetime.utcnow().isoformat(),
        )

    def _request_security_review(self, project_dir: str) -> ValidationResult:
        self.logger.info("Requesting security review", {"project_dir": project_dir})
        message = self.bus.send(
            sender="orchestrator",
            recipient="security",
            payload={
                "type": message_types.REQUEST_SECURITY_REVIEW,
                "project_dir": project_dir,
            },
        )
        reply = self.bus.wait_for_reply(
            agent_name="orchestrator",
            in_reply_to=message.message_id,
            timeout=self.timeouts["security"],
        )
        if reply is None:
            raise TimeoutError("Security agent did not respond in time")
        payload = reply.payload or {}
        if payload.get("status") != "SUCCESS":
            raise RuntimeError(payload.get("error", "Security agent reported failure"))
        report = payload.get("security_report", {})
        return ValidationResult(
            agent_type=report.get("agent_type", "security"),
            score=report.get("score", 0.0),
            issues=report.get("issues", []),
            critical_issues=report.get("critical_issues", []),
            warnings=report.get("warnings", []),
            passed=report.get("passed", False),
            timestamp=report.get("timestamp") or datetime.utcnow().isoformat(),
        )

    def _request_qa_review(self, project_dir: str) -> ValidationResult:
        self.logger.info("Requesting QA review", {"project_dir": project_dir})
        message = self.bus.send(
            sender="orchestrator",
            recipient="qa",
            payload={
                "type": message_types.REQUEST_QA_REVIEW,
                "project_dir": project_dir,
            },
        )
        reply = self.bus.wait_for_reply(
            agent_name="orchestrator",
            in_reply_to=message.message_id,
            timeout=self.timeouts["qa"],
        )
        if reply is None:
            raise TimeoutError("QA agent did not respond in time")
        payload = reply.payload or {}
        if payload.get("status") != "SUCCESS":
            raise RuntimeError(payload.get("error", "QA agent reported failure"))
        report = payload.get("qa_report", {})
        return ValidationResult(
            agent_type=report.get("agent_type", "qa"),
            score=report.get("score", 0.0),
            issues=report.get("issues", []),
            critical_issues=report.get("critical_issues", []),
            warnings=report.get("warnings", []),
            passed=report.get("passed", False),
            timestamp=report.get("timestamp") or datetime.utcnow().isoformat(),
        )

    def _persist_report(self, result: Dict[str, Any]) -> Path:
        reports_dir = get_runtime_root() / "reports"
        reports_dir.mkdir(parents=True, exist_ok=True)
        report_path = reports_dir / f"report_{datetime.utcnow():%Y%m%d_%H%M%S}.json"
        serializable = json.loads(json.dumps(result, default=_default_serializer))
        with report_path.open("w", encoding="utf-8") as handle:
            json.dump(serializable, handle, indent=2)
        self.logger.success("Report stored", {"path": str(report_path)})
        return report_path


def _default_serializer(value: Any) -> Any:  # pragma: no cover - helper for JSON
    if hasattr(value, "to_dict"):
        return value.to_dict()
    if isinstance(value, datetime):
        return value.isoformat()
    return str(value)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the multi-terminal orchestrator")
    parser.add_argument("objective", help="Objective to solve")
    parser.add_argument("--project-name", help="Optional project name")
    parser.add_argument("--workspace", help="Workspace directory (default: runtime/workspace)")
    parser.add_argument("--pm-timeout", type=float, default=60.0, help="Timeout for PM responses in seconds")
    parser.add_argument("--dev-timeout", type=float, default=120.0, help="Timeout for Dev responses in seconds")
    parser.add_argument("--qa-timeout", type=float, default=60.0, help="Timeout for QA responses in seconds")
    parser.add_argument("--security-timeout", type=float, default=60.0, help="Timeout for Security responses in seconds")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    runtime_root = get_runtime_root()
    workspace = Path(args.workspace) if args.workspace else runtime_root / "workspace"
    workspace.mkdir(parents=True, exist_ok=True)

    orchestrator = MultiTerminalOrchestrator(
        workspace=workspace,
        timeouts={
            "pm": args.pm_timeout,
            "dev": args.dev_timeout,
            "qa": args.qa_timeout,
            "security": args.security_timeout,
        },
    )

    result = orchestrator.run(args.objective, project_name=args.project_name)
    print(json.dumps(result, indent=2))
    return 0 if result.get("status") == "SUCCESS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
