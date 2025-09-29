#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# -*- coding: utf-8 -*-
"""
Contratos de Mensaje v2.0 - Protocolo Estándar Estricto
Sistema uniforme de comunicación entre PM_Agent y Dev_Agent
"""


import os
import sys
if sys.platform == "win32":
    os.environ["PYTHONIOENCODING"] = "utf-8"

import uuid
import json
from datetime import datetime
from typing import Dict, Any, List, Optional, Union, Literal
from dataclasses import dataclass
from enum import Enum


# Tipos de mensaje permitidos (estricto)
MessageTypeEnum = Literal[
    "ack", "task_spec", "approval_request", "approval_response",
    "implementation_plan", "implementation_started", "implementation_progress",
    "implementation_completed", "data", "question", "answer", "blocker",
    "status_update", "error", "finish"
]

# Agentes permitidos (estricto)
AgentEnum = Literal["PM_Agent", "Dev_Agent"]


class StandardMessageContract:
    """Contrato estándar para todos los mensajes entre agentes"""

    SCHEMA_VERSION = "1.0"

    @staticmethod
    def create_message(
        from_agent: AgentEnum,
        to_agent: AgentEnum,
        message_type: MessageTypeEnum,
        payload: Dict[str, Any],
        correlation_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Crear mensaje estándar con esquema validado"""

        return {
            "schema_version": StandardMessageContract.SCHEMA_VERSION,
            "from": from_agent,
            "to": to_agent,
            "message_type": message_type,
            "correlation_id": correlation_id or str(uuid.uuid4()),
            "timestamp": datetime.now().isoformat(),
            "payload": payload
        }

    @staticmethod
    def validate_message(message: Dict[str, Any]) -> bool:
        """Validar que el mensaje cumple el esquema estándar"""

        required_fields = ["schema_version", "from", "to", "message_type",
                          "correlation_id", "timestamp", "payload"]

        # Verificar campos requeridos
        for field in required_fields:
            if field not in message:
                return False

        # Validar schema_version
        if message["schema_version"] != StandardMessageContract.SCHEMA_VERSION:
            return False

        # Validar agentes
        valid_agents = ["PM_Agent", "Dev_Agent"]
        if message["from"] not in valid_agents or message["to"] not in valid_agents:
            return False

        # Validar message_type
        valid_types = [
            "ack", "task_spec", "approval_request", "approval_response",
            "implementation_plan", "implementation_started", "implementation_progress",
            "implementation_completed", "data", "question", "answer", "blocker",
            "status_update", "error", "finish"
        ]
        if message["message_type"] not in valid_types:
            return False

        # Validar que payload es un diccionario
        if not isinstance(message["payload"], dict):
            return False

        return True


class TaskSpecContract:
    """Contrato para especificación de tarea (PM -> Dev)"""

    @staticmethod
    def create(
        task_id: str,
        task_name: str,
        description: str,
        priority: str = "medium",
        estimated_hours: float = 4.0,
        deliverables: List[str] = None,
        dependencies: List[str] = None,
        acceptance_criteria: List[str] = None
    ) -> Dict[str, Any]:
        """Crear especificación de tarea estándar"""

        payload = {
            "task_id": task_id,
            "task_name": task_name,
            "description": description,
            "priority": priority,
            "estimated_hours": estimated_hours,
            "deliverables": deliverables or [],
            "dependencies": dependencies or [],
            "acceptance_criteria": acceptance_criteria or []
        }

        return StandardMessageContract.create_message(
            from_agent="PM_Agent",
            to_agent="Dev_Agent",
            message_type="task_spec",
            payload=payload,
            correlation_id=task_id
        )

    @staticmethod
    def validate_payload(payload: Dict[str, Any]) -> bool:
        """Validar payload específico de task_spec"""
        required = ["task_id", "task_name", "description", "priority"]
        return all(field in payload for field in required)


class AckContract:
    """Contrato para confirmación de recepción (Dev -> PM)"""

    @staticmethod
    def create(
        task_id: str,
        task_name: str,
        acknowledged_at: str = None,
        estimated_analysis_time: str = "2-3 minutes"
    ) -> Dict[str, Any]:
        """Crear confirmación de recepción estándar"""

        payload = {
            "task_id": task_id,
            "task_name": task_name,
            "acknowledged_at": acknowledged_at or datetime.now().isoformat(),
            "estimated_analysis_time": estimated_analysis_time,
            "status": "received"
        }

        return StandardMessageContract.create_message(
            from_agent="Dev_Agent",
            to_agent="PM_Agent",
            message_type="ack",
            payload=payload,
            correlation_id=task_id
        )


class ImplementationPlanContract:
    """Contrato para plan de implementación (Dev -> PM)"""

    @staticmethod
    def create(
        task_id: str,
        task_name: str,
        technology_stack: List[str],
        implementation_approach: List[str],
        revised_estimate: float,
        deliverables_plan: List[str],
        potential_challenges: List[str] = None,
        risk_assessment: str = "low"
    ) -> Dict[str, Any]:
        """Crear plan de implementación estándar"""

        payload = {
            "task_id": task_id,
            "task_name": task_name,
            "technology_stack": technology_stack,
            "implementation_approach": implementation_approach,  # ⚡ Evita KeyError
            "revised_estimate": revised_estimate,
            "deliverables_plan": deliverables_plan,
            "potential_challenges": potential_challenges or [],
            "risk_assessment": risk_assessment,
            "complexity_level": "medium"
        }

        return StandardMessageContract.create_message(
            from_agent="Dev_Agent",
            to_agent="PM_Agent",
            message_type="implementation_plan",
            payload=payload,
            correlation_id=task_id
        )

    @staticmethod
    def validate_payload(payload: Dict[str, Any]) -> bool:
        """Validar payload específico de implementation_plan"""
        required = ["task_id", "technology_stack", "implementation_approach", "revised_estimate"]
        return all(field in payload for field in required)


class ApprovalResponseContract:
    """Contrato para respuesta de aprobación (PM -> Dev)"""

    @staticmethod
    def create(
        task_id: str,
        approved: bool,
        feedback: str,
        conditions: List[str] = None,
        revised_priority: str = None
    ) -> Dict[str, Any]:
        """Crear respuesta de aprobación estándar"""

        payload = {
            "task_id": task_id,
            "approved": approved,
            "feedback": feedback,
            "conditions": conditions or [],
            "revised_priority": revised_priority,
            "approval_timestamp": datetime.now().isoformat()
        }

        return StandardMessageContract.create_message(
            from_agent="PM_Agent",
            to_agent="Dev_Agent",
            message_type="approval_response",
            payload=payload,
            correlation_id=task_id
        )


class ImplementationStartedContract:
    """Contrato para inicio de implementación (Dev -> PM)"""

    @staticmethod
    def create(
        task_id: str,
        task_name: str,
        technology_stack: List[str],
        estimated_completion: str = None,
        workspace_path: str = None
    ) -> Dict[str, Any]:
        """Crear notificación de inicio estándar"""

        payload = {
            "task_id": task_id,
            "task_name": task_name,
            "technology_stack": technology_stack,
            "started_at": datetime.now().isoformat(),
            "estimated_completion": estimated_completion,
            "workspace_path": workspace_path,
            "status": "in_progress"
        }

        return StandardMessageContract.create_message(
            from_agent="Dev_Agent",
            to_agent="PM_Agent",
            message_type="implementation_started",
            payload=payload,
            correlation_id=task_id
        )


class ImplementationProgressContract:
    """Contrato para progreso de implementación (Dev -> PM)"""

    @staticmethod
    def create(
        task_id: str,
        progress_percentage: float,
        current_step: str,
        steps_completed: int = 0,
        total_steps: int = 0,
        files_created: List[str] = None,
        next_milestone: str = None
    ) -> Dict[str, Any]:
        """Crear update de progreso estándar"""

        payload = {
            "task_id": task_id,
            "progress_percentage": progress_percentage,
            "current_step": current_step,
            "steps_completed": steps_completed,
            "total_steps": total_steps,
            "files_created": files_created or [],
            "next_milestone": next_milestone,
            "timestamp": datetime.now().isoformat()
        }

        return StandardMessageContract.create_message(
            from_agent="Dev_Agent",
            to_agent="PM_Agent",
            message_type="implementation_progress",
            payload=payload,
            correlation_id=task_id
        )


class ImplementationCompletedContract:
    """Contrato para implementación completada (Dev -> PM)"""

    @staticmethod
    def create(
        task_id: str,
        task_name: str,
        completion_time: str,
        actual_hours: float,
        files_created: List[str],
        tests_created: List[str],
        documentation_created: List[str] = None,
        quality_metrics: Dict[str, Any] = None,
        final_status: str = "completed"
    ) -> Dict[str, Any]:
        """Crear notificación de completitud estándar"""

        payload = {
            "task_id": task_id,
            "task_name": task_name,
            "completion_time": completion_time,
            "actual_hours": actual_hours,
            "deliverables": {
                "files_created": files_created,
                "tests_created": tests_created,
                "documentation_created": documentation_created or [],
                "total_files": len(files_created) + len(tests_created) + len(documentation_created or [])
            },
            "quality_metrics": quality_metrics or {
                "code_quality": "high",
                "test_coverage": "85%",
                "documentation": "complete"
            },
            "final_status": final_status
        }

        return StandardMessageContract.create_message(
            from_agent="Dev_Agent",
            to_agent="PM_Agent",
            message_type="implementation_completed",
            payload=payload,
            correlation_id=task_id
        )


class DataContract:
    """Contrato para intercambio de datos generales"""

    @staticmethod
    def create(
        from_agent: AgentEnum,
        to_agent: AgentEnum,
        data_type: str,
        data_content: Dict[str, Any],
        correlation_id: str = None
    ) -> Dict[str, Any]:
        """Crear mensaje de datos estándar"""

        payload = {
            "data_type": data_type,
            "data_content": data_content,
            "data_timestamp": datetime.now().isoformat()
        }

        return StandardMessageContract.create_message(
            from_agent=from_agent,
            to_agent=to_agent,
            message_type="data",
            payload=payload,
            correlation_id=correlation_id
        )


class StatusUpdateContract:
    """Contrato para actualizaciones de estado"""

    @staticmethod
    def create(
        from_agent: AgentEnum,
        to_agent: AgentEnum,
        status_type: str,
        status_content: Dict[str, Any],
        correlation_id: str = None
    ) -> Dict[str, Any]:
        """Crear update de estado estándar"""

        payload = {
            "status_type": status_type,
            "status_content": status_content,
            "update_timestamp": datetime.now().isoformat()
        }

        return StandardMessageContract.create_message(
            from_agent=from_agent,
            to_agent=to_agent,
            message_type="status_update",
            payload=payload,
            correlation_id=correlation_id
        )


class FinishContract:
    """Contrato para finalización de proyecto (PM únicamente)"""

    @staticmethod
    def create(
        project_name: str,
        completion_summary: Dict[str, Any],
        final_deliverables: List[str],
        project_metrics: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Crear notificación de finalización de proyecto"""

        payload = {
            "project_name": project_name,
            "project_completed_at": datetime.now().isoformat(),
            "completion_summary": completion_summary,
            "final_deliverables": final_deliverables,
            "project_metrics": project_metrics,
            "status": "project_completed"
        }

        return StandardMessageContract.create_message(
            from_agent="PM_Agent",
            to_agent="Dev_Agent",
            message_type="finish",
            payload=payload,
            correlation_id=str(uuid.uuid4())
        )


class MessageSequenceValidator:
    """Validador de secuencia obligatoria de mensajes por tarea"""

    MANDATORY_SEQUENCE = [
        "task_spec",         # PM -> Dev
        "ack",               # Dev -> PM
        "implementation_plan", # Dev -> PM
        "approval_response",   # PM -> Dev
        "implementation_started", # Dev -> PM
        "implementation_progress", # Dev -> PM (puede ser múltiple)
        "implementation_completed" # Dev -> PM
    ]

    def __init__(self):
        self.task_sequences: Dict[str, List[str]] = {}

    def track_message(self, task_id: str, message_type: str) -> bool:
        """Trackear mensaje en secuencia de tarea"""

        if task_id not in self.task_sequences:
            self.task_sequences[task_id] = []

        # Permitir múltiples implementation_progress
        if message_type == "implementation_progress":
            if "implementation_progress" not in self.task_sequences[task_id]:
                self.task_sequences[task_id].append(message_type)
            return True

        # Para otros mensajes, verificar secuencia
        self.task_sequences[task_id].append(message_type)
        return self._validate_sequence(task_id)

    def _validate_sequence(self, task_id: str) -> bool:
        """Validar que la secuencia sea correcta"""

        sequence = self.task_sequences[task_id]

        # Verificar que cada mensaje esté en orden correcto
        mandatory_index = 0
        for msg in sequence:
            if msg == "implementation_progress":
                continue  # Puede aparecer en cualquier momento después de started

            if mandatory_index >= len(self.MANDATORY_SEQUENCE):
                return False

            if msg == self.MANDATORY_SEQUENCE[mandatory_index]:
                mandatory_index += 1
            else:
                return False

        return True

    def is_sequence_complete(self, task_id: str) -> bool:
        """Verificar si la secuencia está completa"""

        if task_id not in self.task_sequences:
            return False

        required_messages = set(self.MANDATORY_SEQUENCE)
        task_messages = set(self.task_sequences[task_id])

        return required_messages.issubset(task_messages)


class MessageContractFactory:
    """Factory para crear mensajes usando contratos estándar"""

    @staticmethod
    def create_task_spec(**kwargs) -> Dict[str, Any]:
        return TaskSpecContract.create(**kwargs)

    @staticmethod
    def create_ack(**kwargs) -> Dict[str, Any]:
        return AckContract.create(**kwargs)

    @staticmethod
    def create_implementation_plan(**kwargs) -> Dict[str, Any]:
        return ImplementationPlanContract.create(**kwargs)

    @staticmethod
    def create_approval_response(**kwargs) -> Dict[str, Any]:
        return ApprovalResponseContract.create(**kwargs)

    @staticmethod
    def create_implementation_started(**kwargs) -> Dict[str, Any]:
        return ImplementationStartedContract.create(**kwargs)

    @staticmethod
    def create_implementation_progress(**kwargs) -> Dict[str, Any]:
        return ImplementationProgressContract.create(**kwargs)

    @staticmethod
    def create_implementation_completed(**kwargs) -> Dict[str, Any]:
        return ImplementationCompletedContract.create(**kwargs)

    @staticmethod
    def create_data(**kwargs) -> Dict[str, Any]:
        return DataContract.create(**kwargs)

    @staticmethod
    def create_status_update(**kwargs) -> Dict[str, Any]:
        return StatusUpdateContract.create(**kwargs)

    @staticmethod
    def create_finish(**kwargs) -> Dict[str, Any]:
        return FinishContract.create(**kwargs)


class MessageValidator:
    """Validador centralizado con secuencia obligatoria"""

    def __init__(self):
        self.sequence_validator = MessageSequenceValidator()

    def validate_message(self, message: Dict[str, Any]) -> tuple[bool, str]:
        """Validar mensaje completo (esquema + secuencia)"""

        # 1. Validar esquema base
        if not StandardMessageContract.validate_message(message):
            return False, "Esquema de mensaje inválido"

        # 2. Validar payload específico
        message_type = message["message_type"]
        payload = message["payload"]

        if message_type == "task_spec" and not TaskSpecContract.validate_payload(payload):
            return False, "Payload task_spec inválido"

        if message_type == "implementation_plan" and not ImplementationPlanContract.validate_payload(payload):
            return False, "Payload implementation_plan inválido"

        # 3. Validar secuencia (solo para mensajes con task_id)
        correlation_id = message.get("correlation_id")
        if correlation_id and message_type in MessageSequenceValidator.MANDATORY_SEQUENCE:
            if not self.sequence_validator.track_message(correlation_id, message_type):
                return False, f"Secuencia inválida para tarea {correlation_id}"

        return True, "Mensaje válido"

    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """Obtener estado de secuencia de tarea"""

        sequence = self.sequence_validator.task_sequences.get(task_id, [])
        is_complete = self.sequence_validator.is_sequence_complete(task_id)

        return {
            "task_id": task_id,
            "current_sequence": sequence,
            "is_complete": is_complete,
            "next_expected": self._get_next_expected_message(sequence)
        }

    def _get_next_expected_message(self, sequence: List[str]) -> str:
        """Determinar siguiente mensaje esperado"""

        for expected in MessageSequenceValidator.MANDATORY_SEQUENCE:
            if expected not in sequence:
                return expected

        return "sequence_complete"


# Singleton para uso global
message_validator = MessageValidator()
message_factory = MessageContractFactory()