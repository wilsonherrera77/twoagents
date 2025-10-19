#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Message Types for Discovery Motor V8
====================================

Define tipos de mensajes estandarizados para comunicación entre agentes.

Arquitectura:
- Filesystem-based message queue (.shared/ directory)
- JSON serialization
- Typed messages con validación
- Timestamping automático
"""

from enum import Enum
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime
import json
from pathlib import Path


class MessageType(Enum):
    """Tipos de mensajes entre agentes"""
    OBJECTIVE = "OBJECTIVE"
    PROPOSAL = "PROPOSAL"
    EVALUATION = "EVALUATION"
    COUNTER_PROPOSAL = "COUNTER_PROPOSAL"
    ACCEPTANCE = "ACCEPTANCE"
    IMPLEMENTATION = "IMPLEMENTATION"
    INSIGHTS = "INSIGHTS"
    VALIDATION_FEEDBACK = "VALIDATION_FEEDBACK"
    CONVERGENCE = "CONVERGENCE"


class AgentAction(Enum):
    """Acciones posibles de agentes"""
    PROPOSE = "PROPOSE"
    ADJUST = "ADJUST"
    AGREE = "AGREE"
    REJECT = "REJECT"
    ACCEPT = "ACCEPT"
    COUNTER = "COUNTER"
    IMPLEMENT = "IMPLEMENT"
    IMPROVE = "IMPROVE"


@dataclass
class BaseMessage:
    """Mensaje base con campos comunes"""
    type: str
    role: str  # "pm", "dev", "discovery", "orchestrator"
    iteration: int
    timestamp: str = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()

    def to_json(self) -> str:
        """Serializar a JSON"""
        return json.dumps(asdict(self), indent=2)

    def to_dict(self) -> Dict:
        """Convertir a diccionario"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict):
        """Crear desde diccionario"""
        return cls(**data)


@dataclass
class ObjectiveMessage(BaseMessage):
    """Mensaje de objetivo (Orchestrator → PM)"""
    objective: str
    constraints: Optional[Dict] = None

    def __init__(self, objective: str, iteration: int = 1, constraints: Optional[Dict] = None):
        super().__init__(
            type=MessageType.OBJECTIVE.value,
            role="orchestrator",
            iteration=iteration
        )
        self.objective = objective
        self.constraints = constraints or {}


@dataclass
class ProposalMessage(BaseMessage):
    """Mensaje de propuesta arquitectónica (PM → Dev)"""
    action: str  # "PROPOSE" | "ADJUST" | "AGREE"
    architecture: Dict
    reasoning: str
    response_to_dev: Optional[List[str]] = None

    def __init__(
        self,
        architecture: Dict,
        reasoning: str,
        iteration: int,
        action: str = "PROPOSE",
        response_to_dev: Optional[List[str]] = None
    ):
        super().__init__(
            type=MessageType.PROPOSAL.value,
            role="pm",
            iteration=iteration
        )
        self.action = action
        self.architecture = architecture
        self.reasoning = reasoning
        self.response_to_dev = response_to_dev or []


@dataclass
class EvaluationMessage(BaseMessage):
    """Mensaje de evaluación técnica (Dev → PM)"""
    action: str  # "ACCEPT" | "COUNTER"
    concerns: List[str]
    alternative_architecture: Optional[Dict] = None
    reasoning: Optional[str] = None

    def __init__(
        self,
        action: str,
        concerns: List[str],
        iteration: int,
        alternative_architecture: Optional[Dict] = None,
        reasoning: Optional[str] = None
    ):
        super().__init__(
            type=MessageType.EVALUATION.value,
            role="dev",
            iteration=iteration
        )
        self.action = action
        self.concerns = concerns
        self.alternative_architecture = alternative_architecture
        self.reasoning = reasoning


@dataclass
class ImplementationMessage(BaseMessage):
    """Mensaje de implementación (Dev → Orchestrator)"""
    status: str  # "implemented" | "improved"
    output_dir: str
    files: List[Dict]  # [{"path": "...", "content": "..."}]
    fixes_applied: Optional[List[str]] = None
    notes: Optional[str] = None

    def __init__(
        self,
        status: str,
        output_dir: str,
        files: List[Dict],
        iteration: int,
        fixes_applied: Optional[List[str]] = None,
        notes: Optional[str] = None
    ):
        super().__init__(
            type=MessageType.IMPLEMENTATION.value,
            role="dev",
            iteration=iteration
        )
        self.status = status
        self.output_dir = output_dir
        self.files = files
        self.fixes_applied = fixes_applied or []
        self.notes = notes


@dataclass
class InsightMessage(BaseMessage):
    """Mensaje de insights (Discovery Motor → Orchestrator)"""
    insights: List[Dict]  # [{"type": "...", "severity": "...", "issue": "...", "suggestion": "..."}]
    recommended_actions: List[str]
    analysis_summary: Optional[str] = None

    def __init__(
        self,
        insights: List[Dict],
        recommended_actions: List[str],
        iteration: int,
        analysis_summary: Optional[str] = None
    ):
        super().__init__(
            type=MessageType.INSIGHTS.value,
            role="discovery",
            iteration=iteration
        )
        self.insights = insights
        self.recommended_actions = recommended_actions
        self.analysis_summary = analysis_summary


@dataclass
class ValidationFeedbackMessage(BaseMessage):
    """Mensaje de feedback de validación (Orchestrator → Dev)"""
    security_score: float
    qa_score: float
    security_issues: List[str]
    qa_issues: List[str]
    critical_issues: List[str]
    high_priority: List[str]

    def __init__(
        self,
        security_score: float,
        qa_score: float,
        security_issues: List[str],
        qa_issues: List[str],
        critical_issues: List[str],
        high_priority: List[str],
        iteration: int
    ):
        super().__init__(
            type=MessageType.VALIDATION_FEEDBACK.value,
            role="orchestrator",
            iteration=iteration
        )
        self.security_score = security_score
        self.qa_score = qa_score
        self.security_issues = security_issues
        self.qa_issues = qa_issues
        self.critical_issues = critical_issues
        self.high_priority = high_priority


@dataclass
class ConvergenceMessage(BaseMessage):
    """Mensaje de convergencia final"""
    success: bool
    security_score: float
    qa_score: float
    output_dir: str
    total_iterations: int
    reason: Optional[str] = None

    def __init__(
        self,
        success: bool,
        security_score: float,
        qa_score: float,
        output_dir: str,
        total_iterations: int,
        iteration: int,
        reason: Optional[str] = None
    ):
        super().__init__(
            type=MessageType.CONVERGENCE.value,
            role="orchestrator",
            iteration=iteration
        )
        self.success = success
        self.security_score = security_score
        self.qa_score = qa_score
        self.output_dir = output_dir
        self.total_iterations = total_iterations
        self.reason = reason


# ====================
# HELPER FUNCTIONS
# ====================

def write_message(message: BaseMessage, filepath: Path) -> bool:
    """
    Escribe mensaje a archivo de forma atómica.

    Args:
        message: Mensaje a escribir
        filepath: Ruta del archivo

    Returns:
        True si éxito
    """
    try:
        # Atomic write: write to temp file, then rename
        temp_file = filepath.with_suffix('.tmp')
        temp_file.write_text(message.to_json(), encoding='utf-8')

        # Atomic rename (works on Windows + Linux)
        temp_file.replace(filepath)

        return True
    except Exception as e:
        print(f"Error writing message to {filepath}: {e}")
        return False


def read_message(filepath: Path) -> Optional[Dict]:
    """
    Lee mensaje desde archivo.

    Args:
        filepath: Ruta del archivo

    Returns:
        Diccionario con datos del mensaje, o None si error
    """
    try:
        if not filepath.exists():
            return None

        data = json.loads(filepath.read_text(encoding='utf-8'))
        return data
    except Exception as e:
        print(f"Error reading message from {filepath}: {e}")
        return None


def parse_message(data: Dict) -> Optional[BaseMessage]:
    """
    Parsea diccionario a objeto Message apropiado.

    Args:
        data: Diccionario con datos del mensaje

    Returns:
        Objeto Message tipado, o None si tipo desconocido
    """
    msg_type = data.get("type")

    if msg_type == MessageType.OBJECTIVE.value:
        return ObjectiveMessage.from_dict(data)
    elif msg_type == MessageType.PROPOSAL.value:
        return ProposalMessage.from_dict(data)
    elif msg_type == MessageType.EVALUATION.value:
        return EvaluationMessage.from_dict(data)
    elif msg_type == MessageType.IMPLEMENTATION.value:
        return ImplementationMessage.from_dict(data)
    elif msg_type == MessageType.INSIGHTS.value:
        return InsightMessage.from_dict(data)
    elif msg_type == MessageType.VALIDATION_FEEDBACK.value:
        return ValidationFeedbackMessage.from_dict(data)
    elif msg_type == MessageType.CONVERGENCE.value:
        return ConvergenceMessage.from_dict(data)
    else:
        print(f"Unknown message type: {msg_type}")
        return None


# ====================
# EXAMPLE USAGE
# ====================

if __name__ == "__main__":
    # Example: PM sends proposal
    proposal = ProposalMessage(
        architecture={
            "modules": ["auth_service.py", "task_service.py"],
            "database": {"tables": ["users", "tasks"]},
            "technologies": {"framework": "FastAPI", "database": "PostgreSQL"}
        },
        reasoning="Modular design with clear separation of concerns",
        iteration=1
    )

    print("PM Proposal:")
    print(proposal.to_json())
    print()

    # Example: Dev sends evaluation
    evaluation = EvaluationMessage(
        action="COUNTER",
        concerns=[
            "Circular dependency between auth_service and task_service",
            "Missing index on user_id for performance"
        ],
        iteration=1,
        alternative_architecture={
            "modules": ["auth_service.py", "task_service.py", "shared_models.py"],
            "reasoning": "Shared models eliminate circular dependency"
        }
    )

    print("Dev Evaluation:")
    print(evaluation.to_json())
    print()

    # Example: Discovery sends insights
    insights = InsightMessage(
        insights=[
            {
                "type": "security",
                "severity": "critical",
                "file": "src/auth_service.py:45",
                "issue": "SQL injection vulnerability",
                "suggestion": "Use parameterized queries"
            }
        ],
        recommended_actions=["Fix SQL injection immediately"],
        iteration=1
    )

    print("Discovery Insights:")
    print(insights.to_json())
