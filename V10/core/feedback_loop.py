"""Feedback loop entre agentes para reforzar seguridad y calidad."""

from __future__ import annotations

from typing import Dict, List

from V10.core.message_bus import FileMessageBus
from V10.utils import create_logger


class FeedbackLoop:
    """Coordina iteraciones entre los agentes de seguridad, QA y desarrollo."""

    def __init__(self, message_bus: FileMessageBus, max_iterations: int = 3) -> None:
        self.bus = message_bus
        self.max_iterations = max_iterations
        self.logger = create_logger("FEEDBACK_LOOP")
        self.last_security_payload: Dict[str, object] = {}
        self.last_qa_payload: Dict[str, object] = {}

    def iterate_until_pass(self, project_path: str) -> bool:
        """Itera el código hasta que apruebe seguridad y QA."""

        for iteration in range(1, self.max_iterations + 1):
            self.logger.info(
                "Iniciando iteración de feedback",
                {"iteration": iteration, "max": self.max_iterations},
            )

            security_passed = self._run_security_cycle(project_path, iteration)
            if not security_passed:
                continue

            qa_passed = self._run_qa_cycle(project_path, iteration)
            if qa_passed:
                self.logger.success("Código aprobado", {"iteration": iteration})
                return True

        self.logger.error(
            "No se logró aprobar las validaciones",
            {"iterations": self.max_iterations},
        )
        return False

    # ------------------------------------------------------------------
    # Ciclos específicos
    # ------------------------------------------------------------------
    def _run_security_cycle(self, project_path: str, iteration: int) -> bool:
        message = self.bus.send(
            sender="feedback_loop",
            recipient="security_agent",
            payload={
                "project_path": project_path,
                "iteration": iteration,
            },
        )
        reply = self.bus.wait_for_reply(
            agent_name="feedback_loop",
            in_reply_to=message.message_id,
            timeout=30.0,
        )
        if reply is None:
            self.logger.error("Security agent no respondió")
            return False

        payload = reply.payload
        self.last_security_payload = dict(payload)
        issues: List[str] = payload.get("issues", [])
        critical: List[str] = payload.get("critical_issues", [])
        score = payload.get("score", 0.0)

        if issues or critical:
            total_issues = len(issues) + len(critical)
            self.logger.warn(
                "Problemas de seguridad detectados",
                {"count": total_issues, "score": score},
            )
            fix_message = self.bus.send(
                sender="feedback_loop",
                recipient="dev_agent",
                payload={
                    "action": "fix_security",
                    "project_path": project_path,
                    "issues": issues + critical,
                    "iteration": iteration,
                },
            )
            fix_reply = self.bus.wait_for_reply(
                agent_name="feedback_loop",
                in_reply_to=fix_message.message_id,
                timeout=60.0,
            )
            if not fix_reply or not fix_reply.payload.get("fixed"):
                self.logger.warn("El Dev agent no pudo corregir los problemas de seguridad")
                return False
            return False  # Requiere nueva iteración tras aplicar fixes

        self.logger.info("Seguridad aprobada", {"score": score})
        return True

    def _run_qa_cycle(self, project_path: str, iteration: int) -> bool:
        message = self.bus.send(
            sender="feedback_loop",
            recipient="qa_agent",
            payload={
                "project_path": project_path,
                "iteration": iteration,
            },
        )
        reply = self.bus.wait_for_reply(
            agent_name="feedback_loop",
            in_reply_to=message.message_id,
            timeout=30.0,
        )
        if reply is None:
            self.logger.error("QA agent no respondió")
            return False

        payload = reply.payload
        self.last_qa_payload = dict(payload)
        score = payload.get("score", 0.0)
        suggestions: List[str] = payload.get("suggestions", [])

        if score < 0.7:
            self.logger.warn(
                "Score de calidad insuficiente",
                {"score": score},
            )
            improve_message = self.bus.send(
                sender="feedback_loop",
                recipient="dev_agent",
                payload={
                    "action": "improve_quality",
                    "project_path": project_path,
                    "suggestions": suggestions,
                    "iteration": iteration,
                },
            )
            improve_reply = self.bus.wait_for_reply(
                agent_name="feedback_loop",
                in_reply_to=improve_message.message_id,
                timeout=60.0,
            )
            if not improve_reply or not improve_reply.payload.get("improved"):
                self.logger.warn("El Dev agent no pudo mejorar la calidad")
                return False
            return False

        self.logger.info("QA aprobado", {"score": score})
        return True
