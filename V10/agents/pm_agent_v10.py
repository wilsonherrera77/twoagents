"""PM Agent V10 - Analiza objetivos usando el servicio LLM local."""

from __future__ import annotations

import json
import threading
from typing import Dict, Optional

import requests

from V10.core.message_bus import FileMessageBus
from V10.utils import create_logger


class PMAgentV10:
    """Agente de gestión de producto que delega el análisis a un LLM externo."""

    AGENT_NAME = "pm_agent"

    def __init__(
        self,
        message_bus: FileMessageBus,
        llm_endpoint: str = "http://localhost:5000/analyze",
    ) -> None:
        self.message_bus = message_bus
        self.llm_endpoint = llm_endpoint
        self.logger = create_logger("PM_AGENT")
        self.running = False
        self.thread: Optional[threading.Thread] = None

    # ------------------------------------------------------------------
    # Ciclo de vida
    # ------------------------------------------------------------------
    def start(self) -> threading.Thread:
        """Inicia el worker en un hilo independiente."""

        if self.thread and self.thread.is_alive():
            return self.thread
        self.running = True
        self.thread = threading.Thread(target=self.run, name="PMAgentV10", daemon=True)
        self.thread.start()
        self.logger.set_state("RUNNING")
        return self.thread

    def stop(self) -> None:
        """Detiene el worker y espera su finalización."""

        self.running = False
        if self.thread:
            self.thread.join(timeout=2)
            self.logger.info("PM agent detenido")

    # ------------------------------------------------------------------
    # Bucle principal
    # ------------------------------------------------------------------
    def run(self) -> None:
        """Worker principal que procesa mensajes del bus."""

        while self.running:
            message = self.message_bus.receive(self.AGENT_NAME, timeout=1.0)
            if message is None:
                continue

            objective = message.payload.get("objective", "")
            project_path = message.payload.get("project_path")

            self.logger.info("Analizando objetivo", {"objective": objective})
            spec = self._analyze_objective_with_llm(objective)

            response_payload = {
                "status": "SUCCESS",
                "objective": objective,
                "spec": spec,
            }
            if project_path:
                response_payload["project_path"] = project_path

            # Respuesta al solicitante original (normalmente el orquestador)
            self.message_bus.send(
                sender=self.AGENT_NAME,
                recipient=message.sender,
                payload=response_payload,
                conversation_id=message.conversation_id,
                in_reply_to=message.message_id,
            )

            # Enviar especificaciones al Dev Agent
            dev_payload = {
                "from": self.AGENT_NAME,
                "objective": objective,
                "spec": spec,
            }
            if project_path:
                dev_payload["project_path"] = project_path

            self.message_bus.send(
                sender=self.AGENT_NAME,
                recipient="dev_agent",
                payload=dev_payload,
                conversation_id=message.conversation_id,
            )

            self.logger.info("📤 Especificaciones enviadas a dev_agent")

    # ------------------------------------------------------------------
    # Lógica de negocio
    # ------------------------------------------------------------------
    def _analyze_objective_with_llm(self, objective: str) -> Dict:
        """Analiza el objetivo usando el servicio LLM vía HTTP local."""

        prompt = f"""Analiza este objetivo de proyecto y genera especificaciones técnicas:

OBJETIVO: {objective}

Genera un JSON estructurado con:
- project_type: tipo de proyecto inferido (string)
- modules: lista de módulos necesarios con nombres descriptivos (list)
- dependencies: librerías Python requeridas (list)
- architecture: descripción breve de arquitectura (string)
- data_flow: flujo de datos entre componentes (string)

IMPORTANTE: Responde ÚNICAMENTE con JSON válido, sin markdown ni explicaciones.
"""

        try:
            response = requests.post(
                self.llm_endpoint,
                json={"prompt": prompt},
                timeout=30,
            )
            response.raise_for_status()
            result = response.json()
            spec = json.loads(result["response"])
            self.logger.success("Especificaciones generadas", {"objective": objective})
            return spec
        except (requests.RequestException, ValueError, json.JSONDecodeError) as exc:
            self.logger.error("Error obteniendo especificaciones", {"error": str(exc)})
            return self._fallback_spec(objective)

    def _fallback_spec(self, objective: str) -> Dict:
        """Fallback básico si el servicio LLM no está disponible."""

        self.logger.warn("Usando especificaciones por defecto", {"objective": objective})
        return {
            "project_type": "generic_python_project",
            "modules": ["main", "utils"],
            "dependencies": ["requests"],
            "architecture": "Arquitectura básica - Servicio LLM no disponible",
            "data_flow": "main → utils",
        }
