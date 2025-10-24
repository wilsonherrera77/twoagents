"""Product Manager agent for the autonomous V10 system."""

from __future__ import annotations

import threading
from dataclasses import dataclass
from typing import Dict, List

from V10.core.message_bus import FileMessageBus
from V10.protocols import Architecture
from V10.utils import create_logger


@dataclass
class ArchitectureTemplate:
    name: str
    keywords: List[str]
    modules: List[str]
    technologies: Dict[str, str]


TEMPLATES: List[ArchitectureTemplate] = [
    ArchitectureTemplate(
        name="web_api",
        keywords=["api", "service", "backend", "rest", "graphql"],
        modules=[
            "main_api.py",
            "auth_service.py",
            "database_models.py",
            "config.py",
            "schemas.py",
            "tests/test_api.py",
        ],
        technologies={
            "framework": "FastAPI",
            "database": "PostgreSQL",
            "orm": "SQLAlchemy",
            "auth": "JWT",
            "testing": "pytest",
            "documentation": "OpenAPI",
        },
    ),
    ArchitectureTemplate(
        name="data_pipeline",
        keywords=["pipeline", "etl", "batch", "data"],
        modules=[
            "ingestion.py",
            "transformations.py",
            "orchestrator.py",
            "storage.py",
            "config.py",
            "tests/test_pipeline.py",
        ],
        technologies={
            "framework": "Prefect",
            "database": "BigQuery",
            "storage": "GCS",
            "scheduler": "Prefect Cloud",
            "testing": "pytest",
            "monitoring": "Prometheus",
        },
    ),
    ArchitectureTemplate(
        name="analytics_dashboard",
        keywords=["dashboard", "analytics", "insights", "report", "visualization"],
        modules=[
            "app.py",
            "data_access.py",
            "metrics.py",
            "auth.py",
            "config.py",
            "tests/test_dashboard.py",
        ],
        technologies={
            "framework": "Streamlit",
            "database": "Snowflake",
            "auth": "Auth0",
            "testing": "pytest",
            "monitoring": "Sentry",
            "ci": "GitHub Actions",
        },
    ),
]


class PMAgentV10:
    """Deterministic yet robust PM agent that generates architectures."""

    def __init__(self) -> None:
        self.logger = create_logger("PM_AGENT")
        self.logger.set_state("INITIALIZED")

    def propose_architecture(self, objective: str) -> Architecture:
        template = self._select_template(objective)
        modules = list(dict.fromkeys(template.modules))
        technologies = dict(template.technologies)
        analysis = self._build_analysis(objective, template)
        reasoning = self._build_reasoning(modules)
        database_schema = self._build_schema(modules)
        architecture = Architecture(
            proposed_modules=modules,
            database_schema=database_schema,
            technologies=technologies,
            analysis=analysis,
            reasoning=reasoning,
        )
        self.logger.success("Architecture created", {
            "modules": len(modules),
            "template": template.name,
        })
        return architecture

    # ------------------------------------------------------------------
    # Template helpers
    # ------------------------------------------------------------------
    def _select_template(self, objective: str) -> ArchitectureTemplate:
        objective_lower = objective.lower()
        for template in TEMPLATES:
            if any(keyword in objective_lower for keyword in template.keywords):
                self.logger.info("Selected template", {"template": template.name})
                return template
        self.logger.info("Falling back to web_api template")
        return TEMPLATES[0]

    def _build_analysis(self, objective: str, template: ArchitectureTemplate) -> str:
        return (
            f"The project '{objective}' is best served by the {template.name} template, "
            f"which balances modularity and scalability. The proposed stack emphasises "
            f"infrastructure-as-code, observability, and continuous delivery to ensure "
            f"the system can evolve safely over time."
        )

    def _build_reasoning(self, modules: List[str]) -> str:
        ordered = ", ".join(modules)
        return (
            f"The modules {ordered} follow a separation-of-concerns strategy: "
            f"interface layers remain isolated from business logic and persistence. "
            f"Each module is independently testable, enabling incremental delivery."
        )

    def _build_schema(self, modules: List[str]) -> Dict[str, Dict[str, str]]:
        schema: Dict[str, Dict[str, str]] = {
            "users": {
                "id": "UUID PRIMARY KEY",
                "email": "TEXT UNIQUE NOT NULL",
                "hashed_password": "TEXT NOT NULL",
                "created_at": "TIMESTAMP NOT NULL",
            },
            "audit_logs": {
                "id": "UUID PRIMARY KEY",
                "user_id": "UUID REFERENCES users(id)",
                "action": "TEXT NOT NULL",
                "created_at": "TIMESTAMP NOT NULL",
            },
        }
        if any("analytics" in module for module in modules):
            schema["metrics"] = {
                "id": "UUID PRIMARY KEY",
                "name": "TEXT NOT NULL",
                "value": "NUMERIC",
                "recorded_at": "TIMESTAMP NOT NULL",
            }
        return schema


def start_pm_worker(bus: FileMessageBus, poll_interval: float = 0.5) -> threading.Event:
    """Launch a background worker that processes PM messages."""

    stop_event = threading.Event()

    def _run() -> None:
        agent = PMAgentV10()
        agent.logger.set_state("WAITING")
        while not stop_event.is_set():
            try:
                message = bus.receive("pm", timeout=poll_interval, poll_interval=poll_interval)
            except Exception as exc:  # pragma: no cover - filesystem errors
                agent.logger.error("Message bus error", {"error": str(exc)})
                continue
            if message is None:
                continue
            agent.logger.set_state("PROCESSING")
            objective = message.payload.get("objective", "")
            try:
                architecture = agent.propose_architecture(objective)
                response_payload = {
                    "status": "SUCCESS",
                    "architecture": architecture.to_dict(),
                }
            except Exception as exc:  # pragma: no cover - safety net
                agent.logger.error("Failed to create architecture", {"error": str(exc)})
                response_payload = {
                    "status": "ERROR",
                    "error": str(exc),
                }
            bus.send(
                sender="pm",
                recipient=message.sender,
                payload=response_payload,
                conversation_id=message.conversation_id,
                in_reply_to=message.message_id,
            )
            agent.logger.set_state("WAITING")
        agent.logger.info("PM worker stopped")

    thread = threading.Thread(target=_run, name="pm-worker", daemon=True)
    thread.start()
    stop_event.thread = thread  # type: ignore[attr-defined]
    return stop_event
