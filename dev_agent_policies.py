#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# -*- coding: utf-8 -*-
"""
Dev_Agent Policies por Nivel de Autonomía
Implementa políticas específicas según el nivel de autonomía: low/medium/high/max
"""


import os
import sys
if sys.platform == "win32":
    os.environ["PYTHONIOENCODING"] = "utf-8"

from typing import Dict, List, Any, Optional
from datetime import datetime
from dataclasses import dataclass
from enum import Enum


class AutonomyLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    MAX = "max"


@dataclass
class DevAgentPolicy:
    """Política específica para un nivel de autonomía"""
    level: AutonomyLevel
    system_prompt: str
    execution_rules: Dict[str, Any]
    approval_required: bool
    auto_replan_enabled: bool
    granular_reporting: bool
    blocker_handling: str


class DevAgentPolicyManager:
    """Gestor de políticas por nivel de autonomía para Dev_Agent"""

    def __init__(self):
        self.policies = self._initialize_policies()

    def _initialize_policies(self) -> Dict[AutonomyLevel, DevAgentPolicy]:
        """Inicializar políticas por nivel de autonomía"""

        policies = {}

        # LOW LEVEL POLICY
        policies[AutonomyLevel.LOW] = DevAgentPolicy(
            level=AutonomyLevel.LOW,
            system_prompt="""[DEV SYSTEM POLICY - low]
Actúas como Senior Full-Stack. Cumple el contrato de mensajes.
- low: no ejecutas sin "approval_response.approved=true".
Siempre incluye "implementation_approach" en "implementation_plan". Al entregar, lista archivos con hashes.

REGLAS ESTRICTAS NIVEL LOW:
1. NUNCA ejecutar implementación sin approval explícito del PM
2. Esperar mensaje "approval_response" con "approved=true"
3. Si no hay approval, enviar "blocker" y esperar
4. Reportar cada paso antes de ejecutar
5. Pedir confirmación para cambios no planificados""",
            execution_rules={
                "require_approval": True,
                "wait_for_approval": True,
                "auto_execute": False,
                "report_before_action": True,
                "ask_confirmation_for_changes": True
            },
            approval_required=True,
            auto_replan_enabled=False,
            granular_reporting=False,
            blocker_handling="wait_for_resolution"
        )

        # MEDIUM LEVEL POLICY
        policies[AutonomyLevel.MEDIUM] = DevAgentPolicy(
            level=AutonomyLevel.MEDIUM,
            system_prompt="""[DEV SYSTEM POLICY - medium]
Actúas como Senior Full-Stack. Cumple el contrato de mensajes.
- medium: ejecutas tras aprobar el plan; pides revisión solo al completar.
Siempre incluye "implementation_approach" en "implementation_plan". Al entregar, lista archivos con hashes.

REGLAS NIVEL MEDIUM:
1. Ejecutar automáticamente tras generar y enviar implementation_plan
2. No esperar approval_response para comenzar ejecución
3. Pedir revisión del PM solo cuando implementation_completed
4. Manejar problemas menores de forma autónoma
5. Reportar progreso periódicamente""",
            execution_rules={
                "require_approval": False,
                "wait_for_approval": False,
                "auto_execute": True,
                "report_before_action": False,
                "ask_confirmation_for_changes": False,
                "auto_start_after_plan": True
            },
            approval_required=False,
            auto_replan_enabled=False,
            granular_reporting=False,
            blocker_handling="try_autonomous_resolution"
        )

        # HIGH LEVEL POLICY
        policies[AutonomyLevel.HIGH] = DevAgentPolicy(
            level=AutonomyLevel.HIGH,
            system_prompt="""[DEV SYSTEM POLICY - high]
Actúas como Senior Full-Stack. Cumple el contrato de mensajes.
- high: divides tareas en subtareas internas y reportas progreso granular.
Siempre incluye "implementation_approach" en "implementation_plan". Al entregar, lista archivos con hashes.

REGLAS NIVEL HIGH:
1. Dividir automáticamente tareas en subtareas internas
2. Reportar progreso granular por cada subtarea
3. Manejar la mayoría de problemas de forma autónoma
4. Optimizar approach durante ejecución si es necesario
5. Reportar implementation_progress con detalles granulares""",
            execution_rules={
                "require_approval": False,
                "wait_for_approval": False,
                "auto_execute": True,
                "divide_into_subtasks": True,
                "granular_progress_reporting": True,
                "autonomous_optimization": True,
                "detailed_logging": True
            },
            approval_required=False,
            auto_replan_enabled=False,
            granular_reporting=True,
            blocker_handling="autonomous_resolution_with_fallback"
        )

        # MAX LEVEL POLICY
        policies[AutonomyLevel.MAX] = DevAgentPolicy(
            level=AutonomyLevel.MAX,
            system_prompt="""[DEV SYSTEM POLICY - max]
Actúas como Senior Full-Stack. Cumple el contrato de mensajes.
- max: auto-replan si un test falla; jamás te detengas por falta de campo opcional: solicita con "blocker" y propone fallback.
Siempre incluye "implementation_approach" en "implementation_plan". Al entregar, lista archivos con hashes.

REGLAS NIVEL MAX:
1. Auto-replanificar si tests fallan o hay problemas
2. NUNCA detenerse por campos opcionales faltantes
3. Usar "blocker" solo para información crítica + proponer fallback
4. Manejo autónomo completo de errores y problemas
5. Optimización continua del approach durante ejecución
6. Escalado automático solo en casos críticos""",
            execution_rules={
                "require_approval": False,
                "wait_for_approval": False,
                "auto_execute": True,
                "auto_replan_on_failure": True,
                "never_stop_for_optional_fields": True,
                "autonomous_error_handling": True,
                "continuous_optimization": True,
                "minimal_escalation": True,
                "divide_into_subtasks": True,
                "granular_progress_reporting": True
            },
            approval_required=False,
            auto_replan_enabled=True,
            granular_reporting=True,
            blocker_handling="autonomous_with_fallback_proposal"
        )

        return policies

    def get_policy(self, level: str) -> DevAgentPolicy:
        """Obtener política para un nivel específico"""
        try:
            autonomy_level = AutonomyLevel(level.lower())
            return self.policies[autonomy_level]
        except (ValueError, KeyError):
            # Default a medium si el nivel no es válido
            return self.policies[AutonomyLevel.MEDIUM]

    def get_system_prompt(self, level: str) -> str:
        """Obtener system prompt para un nivel específico"""
        policy = self.get_policy(level)
        return policy.system_prompt

    def should_require_approval(self, level: str) -> bool:
        """Verificar si se requiere approval para un nivel"""
        policy = self.get_policy(level)
        return policy.approval_required

    def should_auto_execute(self, level: str) -> bool:
        """Verificar si debe auto-ejecutar para un nivel"""
        policy = self.get_policy(level)
        return policy.execution_rules.get("auto_execute", False)

    def should_auto_replan(self, level: str) -> bool:
        """Verificar si debe auto-replanificar en caso de fallo"""
        policy = self.get_policy(level)
        return policy.auto_replan_enabled

    def should_use_granular_reporting(self, level: str) -> bool:
        """Verificar si debe usar reporte granular"""
        policy = self.get_policy(level)
        return policy.granular_reporting

    def get_blocker_handling_strategy(self, level: str) -> str:
        """Obtener estrategia de manejo de blockers"""
        policy = self.get_policy(level)
        return policy.blocker_handling

    def should_divide_into_subtasks(self, level: str) -> bool:
        """Verificar si debe dividir en subtareas (HIGH/MAX)"""
        policy = self.get_policy(level)
        return policy.execution_rules.get("divide_into_subtasks", False)

    def should_never_stop_for_optional_fields(self, level: str) -> bool:
        """Verificar si nunca debe detenerse por campos opcionales (MAX)"""
        policy = self.get_policy(level)
        return policy.execution_rules.get("never_stop_for_optional_fields", False)

    def get_execution_behavior(self, level: str) -> Dict[str, Any]:
        """Obtener comportamiento completo de ejecución para un nivel"""
        policy = self.get_policy(level)

        return {
            "level": level,
            "system_prompt": policy.system_prompt,
            "require_approval": policy.approval_required,
            "auto_execute": self.should_auto_execute(level),
            "auto_replan": self.should_auto_replan(level),
            "granular_reporting": self.should_use_granular_reporting(level),
            "blocker_handling": self.get_blocker_handling_strategy(level),
            "divide_subtasks": self.should_divide_into_subtasks(level),
            "never_stop_optional": self.should_never_stop_for_optional_fields(level),
            "execution_rules": policy.execution_rules
        }

    def validate_implementation_plan_requirements(self, plan: Dict[str, Any], level: str) -> tuple[bool, str]:
        """Validar que implementation_plan cumple requisitos del nivel"""

        # Verificar que siempre incluya implementation_approach
        if "implementation_approach" not in plan.get("payload", {}):
            return False, "implementation_approach es requerido en implementation_plan"

        # Verificaciones específicas por nivel
        policy = self.get_policy(level)

        if policy.level == AutonomyLevel.HIGH:
            # Para HIGH, verificar que hay subtareas definidas
            approach = plan.get("payload", {}).get("implementation_approach", [])
            if len(approach) < 2:
                return False, "HIGH level requiere al menos 2 pasos en implementation_approach"

        elif policy.level == AutonomyLevel.MAX:
            # Para MAX, verificar que hay fallbacks definidos
            payload = plan.get("payload", {})
            if "fallback_approach" not in payload and "error_handling" not in payload:
                # No es crítico para MAX, pero se recomienda
                pass

        return True, "implementation_plan válido para nivel " + level

    def generate_level_appropriate_response(self, level: str, situation: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generar respuesta apropiada según el nivel y situación"""

        policy = self.get_policy(level)

        if situation == "missing_optional_field":
            if policy.level == AutonomyLevel.MAX:
                # MAX: Proponer fallback y continuar
                return {
                    "action": "propose_fallback_and_continue",
                    "message": "Campo opcional faltante - proponiendo fallback y continuando",
                    "fallback_proposed": context.get("fallback", "valor por defecto")
                }
            elif policy.level == AutonomyLevel.LOW:
                # LOW: Enviar blocker y esperar
                return {
                    "action": "send_blocker_and_wait",
                    "message": "Campo faltante - enviando blocker y esperando resolución"
                }
            else:
                # MEDIUM/HIGH: Intentar resolución autónoma
                return {
                    "action": "try_autonomous_resolution",
                    "message": "Intentando resolución autónoma del campo faltante"
                }

        elif situation == "test_failure":
            if policy.level == AutonomyLevel.MAX:
                # MAX: Auto-replan inmediatamente
                return {
                    "action": "auto_replan",
                    "message": "Test falló - auto-replanificando approach"
                }
            elif policy.level == AutonomyLevel.HIGH:
                # HIGH: Analizar y ajustar subtareas
                return {
                    "action": "adjust_subtasks",
                    "message": "Test falló - ajustando subtareas afectadas"
                }
            else:
                # LOW/MEDIUM: Reportar error y esperar guidance
                return {
                    "action": "report_error_and_wait",
                    "message": "Test falló - reportando error y esperando guidance"
                }

        elif situation == "approval_needed":
            if policy.approval_required:
                # LOW: Esperar approval
                return {
                    "action": "wait_for_approval",
                    "message": "Esperando approval_response antes de ejecutar"
                }
            else:
                # MEDIUM/HIGH/MAX: Proceder sin approval
                return {
                    "action": "proceed_without_approval",
                    "message": "Nivel permite ejecución sin approval - procediendo"
                }

        return {
            "action": "default_behavior",
            "message": "Usando comportamiento por defecto para la situación"
        }


# Singleton para uso global
dev_agent_policy_manager = DevAgentPolicyManager()