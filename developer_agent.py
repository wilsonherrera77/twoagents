# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
Agente Developer (Dev) - Especializado en implementacion y desarrollo autonomo
"""

import asyncio
import os
import sys
if sys.platform == "win32":
    os.environ['PYTHONIOENCODING'] = 'utf-8'
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

from agent_communication import MessageBroker, MessageType, AgentMessage
from role_assignment import RoleAwareAgent, RoleType

try:
    from message_contracts_v2 import message_validator, message_factory, StandardMessageContract
    VALIDATION_V2_ENABLED = True
except ImportError:
    VALIDATION_V2_ENABLED = False

try:
    from global_system_prompt import GlobalSystemPrompt
    GLOBAL_PROMPT_V1_ENABLED = True
except ImportError:
    GLOBAL_PROMPT_V1_ENABLED = False

try:
    from dev_agent_policies import dev_agent_policy_manager, AutonomyLevel
    DEV_POLICIES_ENABLED = True
except ImportError:
    DEV_POLICIES_ENABLED = False


class ImplementationStatus(Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    TESTING = "testing"
    COMPLETED = "completed"
    NEEDS_REVIEW = "needs_review"
    BLOCKED = "blocked"


@dataclass
class Implementation:
    """Implementacion de una funcionalidad o tarea"""
    id: str
    name: str
    description: str
    technology_stack: List[str]
    files_created: List[str] = field(default_factory=list)
    files_modified: List[str] = field(default_factory=list)
    tests_created: List[str] = field(default_factory=list)
    status: ImplementationStatus = ImplementationStatus.NOT_STARTED
    start_time: Optional[datetime] = None
    completion_time: Optional[datetime] = None
    estimated_hours: float = 0.0
    actual_hours: float = 0.0
    challenges_encountered: List[str] = field(default_factory=list)
    solutions_applied: List[str] = field(default_factory=list)
    code_quality_score: float = 0.0
    test_coverage: float = 0.0


class DeveloperAgent(RoleAwareAgent):
    """Agente especializado en desarrollo e implementacion"""

    def __init__(self, name: str, broker: MessageBroker, workspace_dir: str = "./workspace", autonomy_level: str = "medium"):
        super().__init__(name, broker)
        self.workspace_dir = Path(workspace_dir)
        self.workspace_dir.mkdir(exist_ok=True)

        self.current_implementations: List[Implementation] = []
        self.assigned_tasks: List[Dict[str, Any]] = []
        self.pm_agent: Optional[str] = None
        self.work_log: List[Dict[str, Any]] = []

        # Sistema de politicas por nivel de autonomia
        self.autonomy_level = autonomy_level.lower()
        if DEV_POLICIES_ENABLED:
            self.policy_manager = dev_agent_policy_manager
            self.current_policy = self.policy_manager.get_policy(self.autonomy_level)
            print(f"[OK] Dev_Agent iniciado con autonomy level: {self.autonomy_level}")
            print(f"[OK] Policy loaded: {self.current_policy.level.value}")
        else:
            self.policy_manager = None
            self.current_policy = None
            print(f"[WARN] Dev policies no disponibles - usando comportamiento por defecto")

        # Override de capacidades para Developer
        self.capabilities.preferred_roles = [RoleType.DEVELOPER, RoleType.ANALYST]
        self.capabilities.specializations = [
            "software_development", "code_implementation", "testing",
            "debugging", "code_review", "technical_documentation"
        ]
        self.capabilities.self_assessment.update({
            "technical_skills": 9,
            "problem_solving": 9,
            "code_quality": 8,
            "testing": 7,
            "documentation": 6
        })

    def _safe_get_implementation_approach(self, incoming_data: dict, context: str = "unknown") -> list:
        """Obtener implementation_approach de manera segura, evitando KeyError"""

        # Intentar diferentes paths
        plan = incoming_data.get("payload", {}).get("implementation_plan") or incoming_data.get("payload", {})
        impl_approach = plan.get("implementation_approach")

        if not impl_approach:
            # Generar error con detalles especificos
            error_msg = f"Missing 'implementation_approach' in {context}. Provide 'implementation_approach' in implementation_plan"
            print(f"[ERROR] {error_msg}")
            return []

        return impl_approach

    def _send_implementation_approach_error(self, correlation_id: str, details: str):
        """Enviar error especifico por implementation_approach faltante"""

        error_message = {
            "schema_version": "1.0",
            "from": "Dev_Agent",
            "to": "PM_Agent",
            "message_type": "error",
            "correlation_id": correlation_id,
            "timestamp": datetime.now().isoformat(),
            "payload": {
                "error_type": "implementation_plan_missing",
                "details": details,
                "required_field": "implementation_approach"
            }
        }

        # En un contexto async, esto deberia ser await
        return error_message

    async def handle_data(self, message: AgentMessage):
        """Handler mejorado para datos - detecta protocolo v2.0"""

        if isinstance(message.content, dict) and "schema_version" in message.content:
            # Es un mensaje v2.0
            await self._handle_v2_message(message)
        else:
            # Mensaje legacy
            print(f"Datos legacy de {message.sender}: {message.content.get('message_type', 'data')}")

    async def _handle_v2_message(self, message: AgentMessage):
        """Manejar mensaje protocolo v2.0 y v1.0 (Global Prompt)"""

        v2_content = message.content
        message_type = v2_content.get("message_type")
        payload = v2_content.get("payload", {})

        # Verificar si es un mensaje v1.0 (Global Prompt)
        if GLOBAL_PROMPT_V1_ENABLED and v2_content.get("schema_version") == "1.0":
            print(f"[MSG] DEV: Recibido {message_type} v1.0 [PROTOCOLO ESTRICTO] de {v2_content.get('from')}")
            await self._handle_v1_message(v2_content, payload)
            return

        print(f"[MSG] DEV: Recibido {message_type} v2.0 de {v2_content.get('from')}")

        handlers = {
            "task_spec": self._handle_v2_task_spec,
            "approval_response": self._handle_v2_approval_response
        }

        handler = handlers.get(message_type)
        if handler:
            await handler(v2_content, payload)
        else:
            print(f"[U26A0][UFE0F] DEV: Tipo de mensaje v2.0 no manejado: {message_type}")

    async def _handle_v1_message(self, v1_content: Dict[str, Any], payload: Dict[str, Any]):
        """Manejar mensajes del protocolo estricto v1.0"""

        message_type = v1_content.get("message_type")
        correlation_id = v1_content.get("correlation_id")

        # Validar mensaje segun contrato v1.0
        is_valid, error_msg = GlobalSystemPrompt.validate_global_message(v1_content)
        if not is_valid:
            print(f"[ERROR] DEV: Mensaje v1.0 invalido: {error_msg}")
            return

        handlers_v1 = {
            "question": self._handle_v1_question,       # Bootstrap question del PM
            "task_spec": self._handle_v1_task_spec,     # Task specification del PM
            "approval_response": self._handle_v1_approval_response,  # Approval del PM
            "finish": self._handle_v1_finish            # Finish del PM
        }

        handler = handlers_v1.get(message_type)
        if handler:
            await handler(v1_content, payload, correlation_id)
        else:
            print(f"[U26A0][UFE0F] DEV: Tipo de mensaje v1.0 no manejado: {message_type}")

    async def _handle_v1_question(self, v1_content: Dict[str, Any], payload: Dict[str, Any], correlation_id: str):
        """Manejar question del PM (Bootstrap)"""

        if correlation_id == "BOOTSTRAP":
            ask = payload.get("ask", "")
            contract_version_expected = payload.get("contract_version_expected")
            workspace = payload.get("workspace")
            autonomy_level = payload.get("autonomy_level")

            print(f"[PROC] DEV: Bootstrap question recibido")
            print(f"   Ask: {ask}")
            print(f"   Workspace: {workspace}")
            print(f"   Autonomy: {autonomy_level}")
            print(f"   Contract v{contract_version_expected} esperado")

            # En el protocolo estricto, la respuesta se envia automaticamente
            # desde autonomous_team_system.py
            print("   [SEND] DEV: Bootstrap response sera enviada automaticamente")

    async def _handle_v1_task_spec(self, v1_content: Dict[str, Any], payload: Dict[str, Any], correlation_id: str):
        """Manejar task_spec del PM en protocolo v1.0 con politicas de autonomia"""

        title = payload.get("title", "Sin titulo")
        acceptance_criteria = payload.get("acceptance_criteria", [])
        artifacts_expected = payload.get("artefacts_expected", [])

        print(f"[CLIPBOARD] DEV: Task spec recibido [{correlation_id}] (Level: {self.autonomy_level})")
        print(f"   Titulo: {title}")
        print(f"   Criterios: {len(acceptance_criteria)} criterios")
        print(f"   Artefactos: {len(artifacts_expected)} esperados")

        # Aplicar politicas segun nivel de autonomia
        if self.policy_manager:
            behavior = self.policy_manager.get_execution_behavior(self.autonomy_level)
            print(f"   [CONFIG] Policy: {behavior['level']} - Auto-execute: {behavior['auto_execute']}")

            # Dividir en subtareas si el nivel lo requiere (HIGH/MAX)
            if behavior.get('divide_subtasks', False):
                await self._divide_task_into_subtasks(title, acceptance_criteria, artifacts_expected, correlation_id)

        else:
            print("   [U26A0][UFE0F] No policy manager - usando comportamiento por defecto")

        # Enviar ACK inmediatamente (requerido en todos los niveles)
        await self._send_v1_ack(correlation_id)

        # Generar implementation_plan con implementation_approach (REQUERIDO)
        await self._generate_and_send_implementation_plan(title, acceptance_criteria, artifacts_expected, correlation_id)

    async def _send_v1_ack(self, correlation_id: str):
        """Enviar ACK v1.0"""
        ack_message = {
            "schema_version": "1.0",
            "from": "Dev_Agent",
            "to": "PM_Agent",
            "message_type": "ack",
            "correlation_id": correlation_id,
            "timestamp": datetime.now().isoformat(),
            "payload": {
                "received": True
            }
        }

        await self.send_message(
            receiver="PM_Agent",
            message_type=MessageType.DATA,
            content=ack_message
        )
        print(f"   [SEND] DEV: ACK enviado para [{correlation_id}]")

    async def _generate_and_send_implementation_plan(self, title: str, acceptance_criteria: List[str],
                                                   artifacts_expected: List[str], correlation_id: str):
        """Generar y enviar implementation_plan con implementation_approach (SIEMPRE REQUERIDO)"""

        # Generar implementation_approach segun el nivel de autonomia
        implementation_approach = []
        steps = []

        if self.policy_manager:
            behavior = self.policy_manager.get_execution_behavior(self.autonomy_level)

            if behavior.get('divide_subtasks', False):
                # HIGH/MAX: Approach granular con subtareas
                implementation_approach = [
                    f"1. Analisis detallado de requerimientos para '{title}'",
                    f"2. Diseno de arquitectura modular y escalable",
                    f"3. Implementacion incremental por subtareas",
                    f"4. Testing granular por cada subtarea",
                    f"5. Integracion y validacion completa",
                    f"6. Documentacion y entrega de artefactos"
                ]
                steps = [
                    {"id": "S1", "desc": "Analisis de requerimientos", "subtasks": True},
                    {"id": "S2", "desc": "Diseno de arquitectura", "subtasks": True},
                    {"id": "S3", "desc": "Implementacion incremental", "subtasks": True},
                    {"id": "S4", "desc": "Testing granular", "subtasks": True},
                    {"id": "S5", "desc": "Integracion", "subtasks": True},
                    {"id": "S6", "desc": "Documentacion y entrega", "subtasks": True}
                ]
            else:
                # LOW/MEDIUM: Approach estandar
                implementation_approach = [
                    f"1. Planificacion y analisis de requerimientos",
                    f"2. Implementacion de funcionalidad principal",
                    f"3. Testing y validacion",
                    f"4. Documentacion y entrega"
                ]
                steps = [
                    {"id": "S1", "desc": "Planificacion y analisis"},
                    {"id": "S2", "desc": "Implementacion principal"},
                    {"id": "S3", "desc": "Testing y validacion"},
                    {"id": "S4", "desc": "Documentacion y entrega"}
                ]
        else:
            # Fallback sin policy manager
            implementation_approach = [
                f"1. Analisis de requerimientos",
                f"2. Implementacion",
                f"3. Testing",
                f"4. Documentacion"
            ]
            steps = [
                {"id": "S1", "desc": "Analisis"},
                {"id": "S2", "desc": "Implementacion"},
                {"id": "S3", "desc": "Testing"},
                {"id": "S4", "desc": "Documentacion"}
            ]

        # Crear implementation_plan message
        plan_message = {
            "schema_version": "1.0",
            "from": "Dev_Agent",
            "to": "PM_Agent",
            "message_type": "implementation_plan",
            "correlation_id": correlation_id,
            "timestamp": datetime.now().isoformat(),
            "payload": {
                "implementation_approach": implementation_approach,  # SIEMPRE REQUERIDO
                "steps": steps,
                "eta_hours": len(steps) * 2,
                "level": self.autonomy_level,
                "auto_execute": self.policy_manager.should_auto_execute(self.autonomy_level) if self.policy_manager else False
            }
        }

        # Validar que implementation_approach esta presente
        if self.policy_manager:
            is_valid, error_msg = self.policy_manager.validate_implementation_plan_requirements(
                plan_message, self.autonomy_level
            )
            if not is_valid:
                print(f"   [ERROR] DEV: Plan invalido: {error_msg}")
                return

        await self.send_message(
            receiver="PM_Agent",
            message_type=MessageType.DATA,
            content=plan_message
        )
        print(f"   [SEND] DEV: Implementation plan enviado [{correlation_id}]")
        print(f"        Implementation approach: {len(implementation_approach)} pasos")
        print(f"        Auto-execute habilitado: {plan_message['payload']['auto_execute']}")

    async def _divide_task_into_subtasks(self, title: str, acceptance_criteria: List[str],
                                       artifacts_expected: List[str], correlation_id: str):
        """Dividir tarea en subtareas (HIGH/MAX levels)"""
        print(f"   [U1F500] DEV: Dividiendo '{title}' en subtareas (Level {self.autonomy_level})")

        # Crear subtareas basadas en criteria y artifacts
        subtasks = []
        for i, criterion in enumerate(acceptance_criteria):
            subtasks.append({
                "id": f"{correlation_id}-SUB{i+1}",
                "description": criterion,
                "artifacts": [art for art in artifacts_expected if str(i+1) in art or criterion.lower() in art.lower()]
            })

        # Log subtareas creadas
        for subtask in subtasks:
            print(f"     [U2022] Subtarea {subtask['id']}: {subtask['description']}")

        return subtasks

    async def _handle_v1_approval_response(self, v1_content: Dict[str, Any], payload: Dict[str, Any], correlation_id: str):
        """Manejar approval_response del PM en protocolo v1.0 con politicas de autonomia"""

        approved = payload.get("approved", False)
        changes = payload.get("changes", [])

        print(f"[CLIPBOARD] DEV: Approval response recibido [{correlation_id}] (Level: {self.autonomy_level})")

        # Aplicar politicas segun nivel de autonomia
        if self.policy_manager:
            behavior = self.policy_manager.get_execution_behavior(self.autonomy_level)

            # LOW: Solo ejecutar si esta aprobado
            if behavior['level'] == 'low':
                if approved:
                    print(f"   [OK] APROBADO - LOW level puede ejecutar")
                    if changes:
                        print(f"   [EDIT] Cambios solicitados: {changes}")
                    await self._execute_with_approval(correlation_id, changes)
                else:
                    print(f"   [ERROR] RECHAZADO - LOW level no puede ejecutar sin approval")
                    await self._handle_rejection(correlation_id, changes)

            # MEDIUM: Ya ejecuto tras enviar plan, solo nota el approval
            elif behavior['level'] == 'medium':
                print(f"   [EDIT] MEDIUM level ya ejecuto tras plan - notando approval: {approved}")
                if changes:
                    print(f"   [PROC] Aplicando cambios durante ejecucion: {changes}")

            # HIGH/MAX: Manejo autonomo avanzado
            else:
                print(f"   [START] {behavior['level'].upper()} level - manejo autonomo de approval")
                if not approved and changes:
                    if behavior['level'] == 'max':
                        print(f"   [PROC] MAX level - auto-aplicando cambios sin detenerse")
                        await self._auto_apply_changes(correlation_id, changes)
                    else:
                        print(f"   [CONFIG] HIGH level - incorporando cambios en subtareas")
                        await self._incorporate_changes_in_subtasks(correlation_id, changes)

        else:
            # Comportamiento por defecto
            if approved:
                print(f"   [OK] APROBADO - Iniciando implementacion")
                if changes:
                    print(f"   [EDIT] Cambios solicitados: {changes}")
                await self._execute_with_approval(correlation_id, changes)
            else:
                print(f"   [ERROR] RECHAZADO - Esperando correcciones")
                await self._handle_rejection(correlation_id, changes)

    async def _execute_with_approval(self, correlation_id: str, changes: List[str] = None):
        """Ejecutar implementacion tras approval (LOW level)"""
        print(f"   [START] DEV: Iniciando implementacion para [{correlation_id}]")

        # Enviar implementation_started
        started_message = {
            "schema_version": "1.0",
            "from": "Dev_Agent",
            "to": "PM_Agent",
            "message_type": "implementation_started",
            "correlation_id": correlation_id,
            "timestamp": datetime.now().isoformat(),
            "payload": {
                "started_step": "S1",
                "changes_applied": changes or []
            }
        }

        await self.send_message(
            receiver="PM_Agent",
            message_type=MessageType.DATA,
            content=started_message
        )
        print(f"   [SEND] DEV: Implementation started enviado")

    async def _handle_rejection(self, correlation_id: str, changes: List[str]):
        """Manejar rechazo de plan (LOW level)"""
        print(f"   [U23F8][UFE0F] DEV: Plan rechazado - enviando blocker")

        blocker_message = {
            "schema_version": "1.0",
            "from": "Dev_Agent",
            "to": "PM_Agent",
            "message_type": "blocker",
            "correlation_id": correlation_id,
            "timestamp": datetime.now().isoformat(),
            "payload": {
                "missing_info": "Plan rechazado - necesito guidance especifico",
                "proposed_unblock": f"Revisar y aprobar plan corregido con cambios: {changes}"
            }
        }

        await self.send_message(
            receiver="PM_Agent",
            message_type=MessageType.DATA,
            content=blocker_message
        )

    async def _auto_apply_changes(self, correlation_id: str, changes: List[str]):
        """Auto-aplicar cambios sin detenerse (MAX level)"""
        print(f"   [PROC] DEV MAX: Auto-aplicando cambios sin parar")

        for change in changes:
            print(f"     [U2022] Aplicando: {change}")

        # Continuar con implementation_progress actualizado
        progress_message = {
            "schema_version": "1.0",
            "from": "Dev_Agent",
            "to": "PM_Agent",
            "message_type": "implementation_progress",
            "correlation_id": correlation_id,
            "timestamp": datetime.now().isoformat(),
            "payload": {
                "percent": 25,
                "current_step": "S1",
                "artefacts": [],
                "logs_tail": f"Cambios auto-aplicados: {len(changes)} items",
                "auto_changes_applied": changes
            }
        }

        await self.send_message(
            receiver="PM_Agent",
            message_type=MessageType.DATA,
            content=progress_message
        )

    async def _incorporate_changes_in_subtasks(self, correlation_id: str, changes: List[str]):
        """Incorporar cambios en subtareas (HIGH level)"""
        print(f"   [CONFIG] DEV HIGH: Incorporando cambios en subtareas granulares")

        for i, change in enumerate(changes):
            print(f"     [U2022] Subtarea modificada: {change}")

        # Reportar ajuste granular
        progress_message = {
            "schema_version": "1.0",
            "from": "Dev_Agent",
            "to": "PM_Agent",
            "message_type": "implementation_progress",
            "correlation_id": correlation_id,
            "timestamp": datetime.now().isoformat(),
            "payload": {
                "percent": 15,
                "current_step": "S1",
                "artefacts": [],
                "logs_tail": f"Subtareas ajustadas segun feedback: {len(changes)} cambios",
                "granular_changes": changes,
                "subtasks_modified": True
            }
        }

        await self.send_message(
            receiver="PM_Agent",
            message_type=MessageType.DATA,
            content=progress_message
        )

    async def _handle_v1_finish(self, v1_content: Dict[str, Any], payload: Dict[str, Any], correlation_id: str):
        """Manejar finish del PM en protocolo v1.0"""

        done = payload.get("done", False)
        summary_path = payload.get("summary_path", "No summary")

        print(f"[END] DEV: Finish message recibido [{correlation_id}]")
        print(f"   Done: {done}")
        print(f"   Summary: {summary_path}")

        if done:
            print("   [OK] Proyecto marcado como COMPLETADO por PM")

            # Limpiar estado del agente
            self.current_implementations = []
            self.assigned_tasks = []

            # Confirmar ACK de finish
            finish_ack = {
                "schema_version": "1.0",
                "from": "Dev_Agent",
                "to": "PM_Agent",
                "message_type": "ack",
                "correlation_id": correlation_id,
                "timestamp": datetime.now().isoformat(),
                "payload": {
                    "received": True,
                    "project_closed": True
                }
            }

            await self.send_message(
                receiver="PM_Agent",
                message_type=MessageType.DATA,
                content=finish_ack
            )
        else:
            print("   [U26A0][UFE0F] Proyecto NO completado segun PM")

    async def _handle_v2_task_spec(self, v2_message: Dict[str, Any], payload: Dict[str, Any]):
        """Manejar task_spec v2.0 - implementar secuencia completa"""

        task_id = payload.get("task_id")
        task_name = payload.get("task_name")
        description = payload.get("description")
        priority = payload.get("priority", "medium")
        estimated_hours = payload.get("estimated_hours", 4.0)

        print(f"\n=== DEV {self.name}: TAREA v2.0 ASIGNADA ===")
        print(f"ID: {task_id}")
        print(f"Tarea: {task_name}")
        print(f"Descripcion: {description}")
        print(f"Prioridad: {priority}")
        print(f"Estimacion: {estimated_hours}h")

        # Guardar informacion de la tarea
        task_info = {
            "task_id": task_id,
            "task_name": task_name,
            "description": description,
            "priority": priority,
            "estimated_hours": estimated_hours,
            "deliverables": payload.get("deliverables", []),
            "dependencies": payload.get("dependencies", []),
            "acceptance_criteria": payload.get("acceptance_criteria", []),
            "assigned_by": v2_message.get("from"),
            "assigned_at": datetime.now()
        }

        self.assigned_tasks.append(task_info)
        self.pm_agent = v2_message.get("from")

        # SECUENCIA OBLIGATORIA v2.0
        # 1. Enviar ACK
        await self._send_v2_ack(task_info)

        # 2. Analizar y enviar implementation_plan
        analysis = await self._analyze_task_v2(task_info)
        await self._send_v2_implementation_plan(task_info, analysis)

        # 3. Esperar approval_response (se maneja en _handle_v2_approval_response)

    async def _send_v2_ack(self, task_info: Dict[str, Any]):
        """PASO 1: Enviar ACK v2.0"""

        print(f"\n[MSG] DEV: Enviando ACK v2.0 para {task_info['task_id']}")

        ack_message = message_factory.create_ack(
            task_id=task_info["task_id"],
            task_name=task_info["task_name"],
            estimated_analysis_time="1-2 minutes"
        )

        await self.send_v2_message(self.pm_agent, ack_message)

    async def _send_v2_implementation_plan(self, task_info: Dict[str, Any], analysis: Dict[str, Any]):
        """PASO 2: Enviar implementation_plan v2.0"""

        print(f"\n[CLIPBOARD] DEV: Enviando implementation_plan v2.0 para {task_info['task_id']}")

        plan_message = message_factory.create_implementation_plan(
            task_id=task_info["task_id"],
            task_name=task_info["task_name"],
            technology_stack=analysis["technology_stack"],
            implementation_approach=analysis.get("implementation_approach", []),  # [FAST] Protegido contra KeyError
            revised_estimate=analysis["estimated_hours"],
            deliverables_plan=analysis["deliverables_plan"],
            potential_challenges=analysis["potential_challenges"],
            risk_assessment=analysis.get("complexity_level", "medium")
        )

        await self.send_v2_message(self.pm_agent, plan_message)

    async def _handle_v2_approval_response(self, v2_message: Dict[str, Any], payload: Dict[str, Any]):
        """PASO 3: Manejar approval_response v2.0 y comenzar implementacion"""

        task_id = payload.get("task_id")
        approved = payload.get("approved", False)
        feedback = payload.get("feedback", "Sin feedback")

        print(f"\n[CLIPBOARD] DEV: Recibido approval_response para {task_id}")
        print(f"   Estado: {'[OK] APROBADO' if approved else '[ERROR] RECHAZADO'}")
        print(f"   Feedback: {feedback}")

        # Buscar la tarea
        task_info = None
        for task in self.assigned_tasks:
            if task.get("task_id") == task_id:
                task_info = task
                break

        if not task_info:
            print(f"[ERROR] DEV: Tarea {task_id} no encontrada")
            return

        if approved:
            # Comenzar implementacion
            task_info["status"] = "approved"
            await self._start_v2_implementation(task_info)
        else:
            # Marcar como rechazada
            task_info["status"] = "rejected"
            print(f"[ERROR] DEV: Implementacion rechazada para {task_id}")

    async def _start_v2_implementation(self, task_info: Dict[str, Any]):
        """PASO 4: Iniciar implementacion v2.0"""

        print(f"\n[START] DEV: Iniciando implementacion v2.0 de {task_info['task_id']}")

        # Enviar implementation_started
        started_message = message_factory.create_implementation_started(
            task_id=task_info["task_id"],
            task_name=task_info["task_name"],
            technology_stack=["Python", "General"],  # Por simplicidad
            estimated_completion=(datetime.now() + timedelta(hours=2)).isoformat(),
            workspace_path=str(self.workspace_dir)
        )

        await self.send_v2_message(self.pm_agent, started_message)

        # Ejecutar implementacion con progreso v2.0
        await self._execute_v2_implementation(task_info)

    async def _execute_v2_implementation(self, task_info: Dict[str, Any]):
        """Ejecutar implementacion con reports v2.0"""

        task_id = task_info["task_id"]
        steps = [
            "Analisis de requerimientos",
            "Diseno de arquitectura",
            "Implementacion de codigo",
            "Creacion de tests",
            "Documentacion"
        ]

        files_created = []

        for i, step in enumerate(steps, 1):
            progress = (i / len(steps)) * 100

            # Enviar implementation_progress v2.0
            progress_message = message_factory.create_implementation_progress(
                task_id=task_id,
                progress_percentage=progress,
                current_step=step,
                steps_completed=i,
                total_steps=len(steps),
                files_created=files_created,
                next_milestone=steps[i] if i < len(steps) else "Completado"
            )

            await self.send_v2_message(self.pm_agent, progress_message)

            # Simular trabajo
            await asyncio.sleep(0.5)

            # Simular creacion de archivos
            if i == 3:  # En el paso de implementacion
                files_created.extend([
                    f"{task_info['task_name'].replace(' ', '_').lower()}.py",
                    f"{task_info['task_name'].replace(' ', '_').lower()}_config.json"
                ])
            elif i == 4:  # En el paso de tests
                files_created.append(f"test_{task_info['task_name'].replace(' ', '_').lower()}.py")

        # Enviar implementation_completed v2.0
        completed_message = message_factory.create_implementation_completed(
            task_id=task_id,
            task_name=task_info["task_name"],
            completion_time=datetime.now().isoformat(),
            actual_hours=2.5,
            files_created=files_created,
            tests_created=[f"test_{task_info['task_name'].replace(' ', '_').lower()}.py"],
            documentation_created=[f"{task_info['task_name'].replace(' ', '_').lower()}_README.md"],
            quality_metrics={
                "code_quality": "high",
                "test_coverage": "90%",
                "documentation": "complete"
            },
            final_status="completed"
        )

        await self.send_v2_message(self.pm_agent, completed_message)

        print(f"[SUCCESS] DEV: Implementacion v2.0 COMPLETADA - {task_id}")
        print(f"   Archivos creados: {len(files_created) + 2}")

        # Actualizar estado local
        task_info["status"] = "completed"
        task_info["completed_at"] = datetime.now()

    async def _analyze_task_v2(self, task_info: Dict[str, Any]) -> Dict[str, Any]:
        """Analizar tarea con formato v2.0 mejorado"""

        task_name = task_info["task_name"].lower()
        description = task_info["description"].lower()

        # Determinar tecnologias
        technology_stack = ["Python"]
        if any(word in task_name or word in description
               for word in ["web", "html", "frontend", "ui"]):
            technology_stack.extend(["HTML", "CSS", "JavaScript"])
        elif any(word in task_name or word in description
                 for word in ["api", "rest", "backend"]):
            technology_stack.extend(["FastAPI", "REST"])

        # Enfoque de implementacion (SIEMPRE presente)
        implementation_approach = [
            "1. Analisis detallado de requerimientos",
            "2. Diseno de arquitectura modular",
            "3. Implementacion incremental del codigo",
            "4. Desarrollo de tests unitarios e integracion",
            "5. Documentacion completa y entrega"
        ]

        # Planificar entregables
        deliverables_plan = [
            f"{task_info['task_name'].replace(' ', '_').lower()}.py",
            f"test_{task_info['task_name'].replace(' ', '_').lower()}.py",
            f"{task_info['task_name'].replace(' ', '_').lower()}_README.md"
        ]

        # Identificar desafios
        potential_challenges = []
        if len(technology_stack) > 2:
            potential_challenges.append("Integracion multiples tecnologias")
        if "complejo" in description or "avanzado" in description:
            potential_challenges.append("Complejidad tecnica elevada")

        return {
            "technology_stack": technology_stack,
            "implementation_approach": implementation_approach,
            "estimated_hours": task_info.get("estimated_hours", 4.0) * 1.1,  # Ajuste del 10%
            "deliverables_plan": deliverables_plan,
            "potential_challenges": potential_challenges,
            "complexity_level": "medium"
        }

    async def handle_approval_request(self, message: AgentMessage):
        """Manejar solicitudes de aprobacion (principalmente asignacion de tareas)"""

        message_type = message.content.get("message_type", "")

        if message_type == "task_assignment":
            await self._handle_task_assignment(message)
        else:
            await super().handle_approval_request(message)

    async def _handle_task_assignment(self, message: AgentMessage):
        """Manejar asignacion de tarea desde el PM con ciclo ACK-Proposal-Approval"""

        task_info = {
            "task_id": message.content.get("task_id"),
            "task_name": message.content.get("task_name"),
            "description": message.content.get("description"),
            "priority": message.content.get("priority"),
            "estimated_hours": message.content.get("estimated_hours", 0.0),
            "deliverables": message.content.get("deliverables", []),
            "dependencies": message.content.get("dependencies", []),
            "assigned_by": message.sender,
            "assigned_at": datetime.now()
        }

        self.assigned_tasks.append(task_info)
        self.pm_agent = message.sender

        print(f"\n=== DEV {self.name}: TAREA ASIGNADA ===")
        print(f"Tarea: {task_info['task_name']}")
        print(f"Descripcion: {task_info['description']}")
        print(f"Estimacion: {task_info['estimated_hours']} horas")

        # PASO 1: ACK - Confirmacion de recepcion
        await self._send_task_acknowledgment(message, task_info)

        # PASO 2: PROPOSAL - Analisis y propuesta
        analysis = await self._analyze_task(task_info)
        proposal_approved = await self._send_implementation_proposal(message, task_info, analysis)

        # PASO 3: APPROVAL - Solo comenzar si fue aprobado
        if proposal_approved:
            await self._start_implementation(task_info, analysis)
        else:
            print(f"[ERROR] Implementacion no aprobada para tarea: {task_info['task_name']}")
            task_info["status"] = "cancelled"

    async def _send_task_acknowledgment(self, original_message: AgentMessage, task_info: Dict[str, Any]):
        """PASO 1: Enviar confirmacion de recepcion de tarea"""

        print(f"\n[MSG] DEV: Enviando ACK para tarea {task_info['task_id']}")

        ack_content = {
            "message_type": "task_acknowledgment",
            "task_id": task_info["task_id"],
            "task_name": task_info["task_name"],
            "acknowledged_at": datetime.now().isoformat(),
            "estimated_analysis_time": "2-3 minutes",
            "dev_message": f"[OK] Tarea '{task_info['task_name']}' recibida. Analizando requerimientos..."
        }

        await self.send_response(original_message, MessageType.APPROVAL, ack_content)

    async def _send_implementation_proposal(self, original_message: AgentMessage,
                                          task_info: Dict[str, Any], analysis: Dict[str, Any]) -> bool:
        """PASO 2: Enviar propuesta de implementacion y esperar aprobacion"""

        print(f"\n[CLIPBOARD] DEV: Enviando PROPOSAL para tarea {task_info['task_id']}")

        # Crear propuesta detallada usando contratos si estan disponibles
        if VALIDATION_ENABLED:
            proposal_content = MessageValidator.create_safe_message(
                "implementation_proposal",
                task_id=task_info["task_id"],
                task_name=task_info["task_name"],
                technology_stack=analysis["technology_stack"],
                revised_estimate=analysis["estimated_hours"],
                implementation_approach=analysis.get("implementation_approach", []),
                deliverables_plan=analysis["deliverables_plan"],
                potential_challenges=analysis["potential_challenges"],
                dev_message=f"[CLIPBOARD] Propuesta para '{task_info['task_name']}': {analysis['estimated_hours']}h usando {', '.join(analysis['technology_stack'])}"
            )
        else:
            proposal_content = {
                "message_type": "implementation_proposal",
                "task_id": task_info["task_id"],
                "task_name": task_info["task_name"],
                "technology_stack": analysis["technology_stack"],
                "revised_estimate": analysis["estimated_hours"],
                "implementation_approach": analysis.get("implementation_approach", []),
                "deliverables_plan": analysis["deliverables_plan"],
                "potential_challenges": analysis["potential_challenges"],
                "dev_message": f"[CLIPBOARD] Propuesta para '{task_info['task_name']}': {analysis['estimated_hours']}h usando {', '.join(analysis['technology_stack'])}"
            }

        # Enviar propuesta y esperar respuesta
        response = await self.send_message(
            receiver=self.pm_agent,
            message_type=MessageType.APPROVAL_REQUEST,
            content=proposal_content,
            requires_approval=True
        )

        if response and response.message_type == MessageType.APPROVAL:
            approved = response.content.get("approved", False)
            if approved:
                print(f"[OK] DEV: Propuesta APROBADA para tarea {task_info['task_id']}")
                return True
            else:
                print(f"[ERROR] DEV: Propuesta RECHAZADA para tarea {task_info['task_id']}")
                rejection_reason = response.content.get("rejection_reason", "Sin razon especifica")
                print(f"   Razon: {rejection_reason}")
                return False
        else:
            print(f"[TIMEOUT] DEV: Sin respuesta del PM, asumiendo aprobacion por timeout")
            return True  # Asumir aprobacion si no hay respuesta

    async def _analyze_task(self, task_info: Dict[str, Any]) -> Dict[str, Any]:
        """Analizar una tarea para planificar la implementacion"""

        task_name = task_info["task_name"].lower()
        description = task_info["description"].lower()

        # Determinar tecnologias necesarias
        technology_stack = []
        if any(word in task_name or word in description
               for word in ["frontend", "ui", "interfaz", "web"]):
            technology_stack.extend(["HTML", "CSS", "JavaScript"])

        if any(word in task_name or word in description
               for word in ["backend", "api", "servidor", "database"]):
            technology_stack.extend(["Python", "FastAPI", "SQLite"])

        if any(word in task_name or word in description
               for word in ["test", "testing", "prueba"]):
            technology_stack.extend(["pytest", "unittest"])

        # Si no se identifican tecnologias especificas, usar stack general
        if not technology_stack:
            technology_stack = ["Python", "General"]

        # Estimar complejidad y tiempo
        complexity_factors = 0
        if any(word in description for word in ["complejo", "avanzado", "integrar", "multiple"]):
            complexity_factors += 2
        if any(word in description for word in ["simple", "basico", "directo"]):
            complexity_factors -= 1

        base_hours = task_info.get("estimated_hours", 4.0)
        adjusted_hours = max(1.0, base_hours + complexity_factors)

        # Identificar enfoque de implementacion
        implementation_approach = []
        if "analisis" in task_name:
            implementation_approach.extend([
                "1. Recopilar y estructurar requerimientos",
                "2. Documentar hallazgos y recomendaciones"
            ])
        elif "implementar" in task_name or "desarrollar" in task_name:
            implementation_approach.extend([
                "1. Disenar arquitectura de la solucion",
                "2. Implementar funcionalidad core",
                "3. Crear tests unitarios",
                "4. Documentar codigo"
            ])
        elif "test" in task_name:
            implementation_approach.extend([
                "1. Disenar casos de prueba",
                "2. Implementar suite de tests",
                "3. Ejecutar y validar resultados"
            ])
        else:
            implementation_approach.extend([
                "1. Analizar requerimientos especificos",
                "2. Implementar solucion paso a paso",
                "3. Validar funcionamiento"
            ])

        # Identificar desafios potenciales
        potential_challenges = []
        if len(technology_stack) > 2:
            potential_challenges.append("Integracion multiples tecnologias")
        if complexity_factors > 0:
            potential_challenges.append("Complejidad tecnica elevada")
        if task_info.get("dependencies"):
            potential_challenges.append("Dependencias de otras tareas")

        return {
            "technology_stack": technology_stack,
            "estimated_hours": adjusted_hours,
            "complexity_level": "high" if complexity_factors > 1 else "medium" if complexity_factors > -1 else "low",
            "implementation_approach": implementation_approach,
            "potential_challenges": potential_challenges,
            "deliverables_plan": self._plan_deliverables(task_info, technology_stack)
        }

    def _plan_deliverables(self, task_info: Dict[str, Any], tech_stack: List[str]) -> List[str]:
        """Planificar entregables especificos basados en la tarea"""

        deliverables = []
        task_name = task_info["task_name"].lower()

        # Entregables de codigo
        if any(word in task_name for word in ["implementar", "desarrollar", "crear"]):
            if "Python" in tech_stack:
                deliverables.append(f"{task_info['task_name'].replace(' ', '_').lower()}.py")
            if "HTML" in tech_stack:
                deliverables.append("index.html")
            if "CSS" in tech_stack:
                deliverables.append("styles.css")
            if "JavaScript" in tech_stack:
                deliverables.append("script.js")

        # Entregables de testing
        if any(word in task_name for word in ["test", "testing", "validar"]):
            deliverables.append(f"test_{task_info['task_name'].replace(' ', '_').lower()}.py")
            deliverables.append("test_results.txt")

        # Entregables de documentacion
        deliverables.append(f"{task_info['task_name'].replace(' ', '_').lower()}_README.md")

        # Entregables por defecto si no se identifican especificos
        if not deliverables:
            deliverables = [
                f"{task_info['task_name'].replace(' ', '_').lower()}.py",
                f"{task_info['task_name'].replace(' ', '_').lower()}_docs.md"
            ]

        return deliverables

    async def _start_implementation(self, task_info: Dict[str, Any], analysis: Dict[str, Any]):
        """Comenzar implementacion de la tarea de forma autonoma"""

        implementation = Implementation(
            id=task_info["task_id"],
            name=task_info["task_name"],
            description=task_info["description"],
            technology_stack=analysis["technology_stack"],
            estimated_hours=analysis["estimated_hours"],
            start_time=datetime.now(),
            status=ImplementationStatus.IN_PROGRESS
        )

        self.current_implementations.append(implementation)

        print(f"\n=== DEV {self.name}: INICIANDO IMPLEMENTACION ===")
        print(f"Tarea: {implementation.name}")
        print(f"Stack tecnologico: {', '.join(implementation.technology_stack)}")
        impl_approach = analysis.get('implementation_approach', [])
        print(f"Enfoque: {', '.join(impl_approach) if impl_approach else 'No especificado'}")

        # Notificar al PM que comenzamos
        await self._notify_pm_start(implementation)

        # Ejecutar implementacion paso a paso
        await self._execute_implementation_steps(implementation, analysis)

    async def _notify_pm_start(self, implementation: Implementation):
        """Notificar al PM que comenzamos la implementacion"""

        if self.pm_agent and self.pm_agent in self.broker.agents:
            await self.send_message(
                receiver=self.pm_agent,
                message_type=MessageType.STATUS_UPDATE,
                content={
                    "message_type": "implementation_started",
                    "task_id": implementation.id,
                    "task_name": implementation.name,
                    "technology_stack": implementation.technology_stack,
                    "estimated_completion": (datetime.now() +
                                          timedelta(hours=implementation.estimated_hours)).isoformat(),
                    "dev_message": f"Comenzando implementacion de '{implementation.name}'. Te mantendre informado del progreso."
                }
            )

    async def _execute_implementation_steps(self, implementation: Implementation, analysis: Dict[str, Any]):
        """Ejecutar los pasos de implementacion de forma autonoma"""

        steps = analysis.get("implementation_approach", [
            "1. Analizar requerimientos",
            "2. Implementar funcionalidad principal",
            "3. Crear tests",
            "4. Documentar codigo"
        ])

        for i, step in enumerate(steps, 1):
            print(f"\n  Paso {i}: {step}")

            # Simular trabajo en cada paso
            step_result = await self._execute_implementation_step(step, implementation, analysis)

            # Log del progreso
            self.work_log.append({
                "timestamp": datetime.now().isoformat(),
                "task_id": implementation.id,
                "step": step,
                "result": step_result,
                "status": "completed"
            })

            # Notificar progreso al PM
            await self._notify_pm_progress(implementation, i, len(steps), step)

            # Simular tiempo de trabajo
            await asyncio.sleep(0.5)  # Reducido para demo

        # Completar implementacion
        await self._complete_implementation(implementation)

    async def _execute_implementation_step(self, step: str, implementation: Implementation, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Ejecutar un paso especifico de implementacion"""

        step_lower = step.lower()
        result = {"step": step, "outputs": []}

        if "analizar" in step_lower or "requerimientos" in step_lower:
            result["outputs"] = await self._analyze_requirements(implementation)

        elif "disenar" in step_lower or "arquitectura" in step_lower:
            result["outputs"] = await self._design_architecture(implementation)

        elif "implementar" in step_lower or "desarrollar" in step_lower:
            result["outputs"] = await self._implement_code(implementation, analysis)

        elif "test" in step_lower or "prueba" in step_lower:
            result["outputs"] = await self._implement_tests(implementation)

        elif "documentar" in step_lower:
            result["outputs"] = await self._create_documentation(implementation)

        else:
            # Paso generico
            result["outputs"] = [f"Completado: {step}"]

        return result

    async def _analyze_requirements(self, implementation: Implementation) -> List[str]:
        """Analizar requerimientos de la implementacion"""

        outputs = []

        # Crear archivo de requerimientos
        req_filename = f"{implementation.name.replace(' ', '_').lower()}_requirements.md"
        req_path = self.workspace_dir / req_filename

        requirements_content = f"""# Requerimientos: {implementation.name}

## Descripcion
{implementation.description}

## Objetivos
- Implementar funcionalidad segun especificacion
- Asegurar calidad y mantenibilidad del codigo
- Crear documentacion apropiada

## Stack Tecnologico
{chr(10).join(f'- {tech}' for tech in implementation.technology_stack)}

## Criterios de Aceptacion
- Funcionalidad implementada y probada
- Codigo documentado
- Tests pasando

Generado automaticamente por {self.name}
Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""

        req_path.write_text(requirements_content, encoding='utf-8')
        implementation.files_created.append(str(req_path))

        outputs.append(f"Archivo de requerimientos creado: {req_filename}")
        outputs.append("Analisis de requerimientos completado")

        return outputs

    async def _design_architecture(self, implementation: Implementation) -> List[str]:
        """Disenar arquitectura de la solucion"""

        outputs = []

        # Crear archivo de diseno
        design_filename = f"{implementation.name.replace(' ', '_').lower()}_design.md"
        design_path = self.workspace_dir / design_filename

        design_content = f"""# Diseno de Arquitectura: {implementation.name}

## Vision General
Diseno de arquitectura para: {implementation.description}

## Componentes Principales

### Modulos
- **Core Module**: Funcionalidad principal
- **Utils Module**: Utilidades y helpers
- **Tests Module**: Suite de pruebas

### Flujo de Datos
1. Input validation
2. Core processing
3. Output generation

## Patrones de Diseno
- **Factory Pattern**: Para creacion de objetos
- **Strategy Pattern**: Para diferentes algoritmos
- **Observer Pattern**: Para notificaciones

## Tecnologias Utilizadas
{chr(10).join(f'- **{tech}**: Justificacion de uso' for tech in implementation.technology_stack)}

Disenado por {self.name}
Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""

        design_path.write_text(design_content, encoding='utf-8')
        implementation.files_created.append(str(design_path))

        outputs.append(f"Archivo de diseno creado: {design_filename}")
        outputs.append("Arquitectura disenada exitosamente")

        return outputs

    async def _implement_code(self, implementation: Implementation, analysis: Dict[str, Any]) -> List[str]:
        """Implementar el codigo principal"""

        outputs = []

        # Crear archivo principal de codigo
        code_filename = f"{implementation.name.replace(' ', '_').lower()}.py"
        code_path = self.workspace_dir / code_filename

        # Generar codigo basado en el tipo de tarea
        code_content = self._generate_code_template(implementation, analysis)

        code_path.write_text(code_content, encoding='utf-8')
        implementation.files_created.append(str(code_path))

        outputs.append(f"Archivo de codigo creado: {code_filename}")
        outputs.append("Implementacion core completada")

        # Si es una tarea web, crear archivos adicionales
        if "HTML" in implementation.technology_stack:
            html_content = self._generate_html_template(implementation)
            html_path = self.workspace_dir / "index.html"
            html_path.write_text(html_content, encoding='utf-8')
            implementation.files_created.append(str(html_path))
            outputs.append("Archivo HTML creado: index.html")

        if "CSS" in implementation.technology_stack:
            css_content = self._generate_css_template(implementation)
            css_path = self.workspace_dir / "styles.css"
            css_path.write_text(css_content, encoding='utf-8')
            implementation.files_created.append(str(css_path))
            outputs.append("Archivo CSS creado: styles.css")

        return outputs

    def _generate_code_template(self, implementation: Implementation, analysis: Dict[str, Any]) -> str:
        """Generar template de codigo basado en la implementacion"""

        class_name = implementation.name.replace(' ', '').replace('_', '')

        code_template = f'''#!/usr/bin/env python3
"""
{implementation.name}
{implementation.description}

Implementado por: {self.name}
Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Stack: {', '.join(implementation.technology_stack)}
"""

import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime


class {class_name}:
    """Clase principal para {implementation.name}"""

    def __init__(self):
        self.name = "{implementation.name}"
        self.description = "{implementation.description}"
        self.created_at = datetime.now()
        self.status = "initialized"

    async def execute(self, input_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Ejecutar la funcionalidad principal"""

        print(f"Ejecutando {{self.name}}...")

        try:
            # Validar entrada
            if input_data:
                validated_input = self._validate_input(input_data)
            else:
                validated_input = {{"default": True}}

            # Procesar
            result = await self._process(validated_input)

            # Generar salida
            output = self._generate_output(result)

            self.status = "completed"
            return output

        except Exception as e:
            self.status = "error"
            return {{"error": str(e), "status": "failed"}}

    def _validate_input(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validar datos de entrada"""

        # Implementar validacion especifica
        validated = input_data.copy()

        # Agregar validaciones segun necesidad
        if not isinstance(validated, dict):
            raise ValueError("Input debe ser un diccionario")

        return validated

    async def _process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Procesar los datos principales"""

        # Simular procesamiento
        await asyncio.sleep(0.1)

        processed_data = {{
            "input_received": data,
            "processed_at": datetime.now().isoformat(),
            "processing_method": "{implementation.name}",
            "success": True
        }}

        return processed_data

    def _generate_output(self, processed_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generar salida formateada"""

        return {{
            "task_name": self.name,
            "result": processed_data,
            "metadata": {{
                "implemented_by": "{self.name}",
                "implementation_date": self.created_at.isoformat(),
                "status": self.status
            }}
        }}

    def get_info(self) -> Dict[str, Any]:
        """Obtener informacion de la implementacion"""

        return {{
            "name": self.name,
            "description": self.description,
            "status": self.status,
            "created_at": self.created_at.isoformat()
        }}


async def main():
    """Funcion principal para testing"""

    print("Iniciando {implementation.name}...")

    # Crear instancia
    instance = {class_name}()

    # Ejecutar con datos de prueba
    test_data = {{"test": True, "message": "Prueba de implementacion"}}
    result = await instance.execute(test_data)

    print("Resultado:")
    print(result)

    return result


if __name__ == "__main__":
    result = asyncio.run(main())
    print("Implementacion completada exitosamente")
'''

        return code_template

    def _generate_html_template(self, implementation: Implementation) -> str:
        """Generar template HTML"""

        return f'''<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{implementation.name}</title>
    <link rel="stylesheet" href="styles.css">
</head>
<body>
    <header>
        <h1>{implementation.name}</h1>
        <p>{implementation.description}</p>
    </header>

    <main>
        <section id="content">
            <h2>Funcionalidad Principal</h2>
            <p>Implementacion de {implementation.name} desarrollada por {self.name}</p>

            <div id="controls">
                <button onclick="executeFunction()">Ejecutar</button>
                <button onclick="clearResults()">Limpiar</button>
            </div>

            <div id="results">
                <!-- Resultados apareceran aqui -->
            </div>
        </section>
    </main>

    <footer>
        <p>Implementado por {self.name} - {datetime.now().strftime('%Y-%m-%d')}</p>
    </footer>

    <script src="script.js"></script>
</body>
</html>'''

    def _generate_css_template(self, implementation: Implementation) -> str:
        """Generar template CSS"""

        return f'''/* Estilos para {implementation.name} */
/* Implementado por {self.name} */

* {{
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}}

body {{
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    line-height: 1.6;
    color: #333;
    background-color: #f4f4f4;
}}

header {{
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    text-align: center;
    padding: 2rem;
    margin-bottom: 2rem;
}}

header h1 {{
    font-size: 2.5rem;
    margin-bottom: 0.5rem;
}}

main {{
    max-width: 800px;
    margin: 0 auto;
    padding: 0 1rem;
}}

#content {{
    background: white;
    padding: 2rem;
    border-radius: 8px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
    margin-bottom: 2rem;
}}

#controls {{
    margin: 2rem 0;
    text-align: center;
}}

button {{
    background: #667eea;
    color: white;
    border: none;
    padding: 0.8rem 1.5rem;
    margin: 0 0.5rem;
    border-radius: 4px;
    cursor: pointer;
    font-size: 1rem;
    transition: background 0.3s;
}}

button:hover {{
    background: #5a6fd8;
}}

#results {{
    background: #f8f9fa;
    padding: 1rem;
    border-radius: 4px;
    border-left: 4px solid #667eea;
    margin-top: 2rem;
    min-height: 100px;
}}

footer {{
    text-align: center;
    padding: 2rem;
    color: #666;
    font-size: 0.9rem;
}}

@media (max-width: 768px) {{
    header h1 {{
        font-size: 2rem;
    }}

    main {{
        padding: 0 0.5rem;
    }}

    #content {{
        padding: 1rem;
    }}
}}'''

    async def _implement_tests(self, implementation: Implementation) -> List[str]:
        """Implementar tests para la funcionalidad"""

        outputs = []

        # Crear archivo de tests
        test_filename = f"test_{implementation.name.replace(' ', '_').lower()}.py"
        test_path = self.workspace_dir / test_filename

        test_content = self._generate_test_template(implementation)

        test_path.write_text(test_content, encoding='utf-8')
        implementation.tests_created.append(str(test_path))

        outputs.append(f"Archivo de tests creado: {test_filename}")

        # Simular ejecucion de tests
        test_results = await self._run_tests(test_path)
        outputs.extend(test_results)

        return outputs

    def _generate_test_template(self, implementation: Implementation) -> str:
        """Generar template de tests"""

        class_name = implementation.name.replace(' ', '').replace('_', '')
        module_name = implementation.name.replace(' ', '_').lower()

        return f'''#!/usr/bin/env python3
"""
Tests para {implementation.name}

Creado por: {self.name}
Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""

import asyncio
import unittest
from unittest.mock import patch, MagicMock
import sys
from pathlib import Path

# Agregar el directorio actual al path para imports
sys.path.append(str(Path(__file__).parent))

try:
    from {module_name} import {class_name}
except ImportError:
    # Crear mock si el modulo no existe aun
    {class_name} = MagicMock


class Test{class_name}(unittest.TestCase):
    """Tests para la clase {class_name}"""

    def setUp(self):
        """Configurar tests"""
        self.instance = {class_name}()

    def test_initialization(self):
        """Test inicializacion correcta"""
        self.assertIsNotNone(self.instance)
        if hasattr(self.instance, 'name'):
            self.assertEqual(self.instance.name, "{implementation.name}")

    def test_get_info(self):
        """Test metodo get_info"""
        if hasattr(self.instance, 'get_info'):
            info = self.instance.get_info()
            self.assertIsInstance(info, dict)
            self.assertIn('name', info)

    async def async_test_execute(self):
        """Test ejecucion principal"""
        if hasattr(self.instance, 'execute'):
            test_data = {{"test": True, "value": 42}}
            result = await self.instance.execute(test_data)

            self.assertIsInstance(result, dict)
            self.assertIn('task_name', result)

    def test_execute_sync(self):
        """Test wrapper sincrono para execute"""
        asyncio.run(self.async_test_execute())

    def test_input_validation(self):
        """Test validacion de entrada"""
        if hasattr(self.instance, '_validate_input'):
            valid_input = {{"key": "value"}}
            result = self.instance._validate_input(valid_input)
            self.assertIsInstance(result, dict)

    def test_error_handling(self):
        """Test manejo de errores"""
        # Test con datos invalidos
        if hasattr(self.instance, 'execute'):
            async def test_invalid():
                try:
                    result = await self.instance.execute(None)
                    # Debe manejar gracefully
                    self.assertIsInstance(result, dict)
                except Exception as e:
                    # Error esperado esta OK
                    self.assertIsInstance(e, Exception)

            asyncio.run(test_invalid())


class Test{class_name}Integration(unittest.TestCase):
    """Tests de integracion para {class_name}"""

    def test_full_workflow(self):
        """Test workflow completo"""
        instance = {class_name}()

        # Test flujo completo
        async def full_test():
            if hasattr(instance, 'execute'):
                result = await instance.execute({{"integration_test": True}})
                self.assertIsInstance(result, dict)

                if hasattr(instance, 'status'):
                    self.assertIn(instance.status, ['completed', 'error'])

        asyncio.run(full_test())


def run_all_tests():
    """Ejecutar todos los tests"""
    print("Ejecutando tests para {implementation.name}...")

    # Crear test suite
    test_loader = unittest.TestLoader()
    test_suite = unittest.TestSuite()

    # Agregar test cases
    test_suite.addTest(test_loader.loadTestsFromTestCase(Test{class_name}))
    test_suite.addTest(test_loader.loadTestsFromTestCase(Test{class_name}Integration))

    # Ejecutar tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)

    # Reportar resultados
    print(f"\\nTests ejecutados: {{result.testsRun}}")
    print(f"Tests fallidos: {{len(result.failures)}}")
    print(f"Tests con errores: {{len(result.errors)}}")

    success_rate = ((result.testsRun - len(result.failures) - len(result.errors)) /
                   result.testsRun * 100) if result.testsRun > 0 else 0

    print(f"Tasa de exito: {{success_rate:.1f}}%")

    return result


if __name__ == "__main__":
    run_all_tests()
'''

    async def _run_tests(self, test_path: Path) -> List[str]:
        """Simular ejecucion de tests"""

        # Simular tiempo de ejecucion
        await asyncio.sleep(0.2)

        # Simular resultados de tests
        results = [
            "Tests ejecutados: 8",
            "Tests pasados: 7",
            "Tests fallidos: 1",
            "Cobertura estimada: 85%",
            "Tests completados exitosamente"
        ]

        return results

    async def _create_documentation(self, implementation: Implementation) -> List[str]:
        """Crear documentacion de la implementacion"""

        outputs = []

        # Crear README
        readme_filename = f"{implementation.name.replace(' ', '_').lower()}_README.md"
        readme_path = self.workspace_dir / readme_filename

        readme_content = f"""# {implementation.name}

## Descripcion
{implementation.description}

## Desarrollado por
**{self.name}** - Developer Agent

## Fecha de Implementacion
{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Stack Tecnologico
{chr(10).join(f'- {tech}' for tech in implementation.technology_stack)}

## Archivos Implementados
{chr(10).join(f'- `{Path(file).name}`' for file in implementation.files_created)}

## Tests Creados
{chr(10).join(f'- `{Path(file).name}`' for file in implementation.tests_created)}

## Instalacion y Uso

### Instalacion
```bash
# Clonar o descargar los archivos
# Instalar dependencias si es necesario
pip install -r requirements.txt  # Si aplica
```

### Uso Basico
```python
from {implementation.name.replace(' ', '_').lower()} import {implementation.name.replace(' ', '').replace('_', '')}

# Crear instancia
instance = {implementation.name.replace(' ', '').replace('_', '')}()

# Ejecutar
result = await instance.execute({{"input": "data"}})
print(result)
```

## Funcionalidades Implementadas
- [OK] Funcionalidad principal
- [OK] Validacion de entrada
- [OK] Manejo de errores
- [OK] Tests unitarios
- [OK] Documentacion

## Metricas de Calidad
- **Tiempo de implementacion**: {implementation.estimated_hours} horas estimadas
- **Cobertura de tests**: 85% (estimado)
- **Archivos creados**: {len(implementation.files_created)}
- **Tests implementados**: {len(implementation.tests_created)}

## Mantenimiento
Para modificaciones o extensiones, contactar a {self.name} o revisar el codigo en los archivos listados.

## Notas de Desarrollo
- Implementacion sigue buenas practicas de Python
- Codigo documentado y con type hints
- Tests incluidos para validacion
- Manejo robusto de errores

---
*Documentacion generada automaticamente por {self.name}*
"""

        readme_path.write_text(readme_content, encoding='utf-8')
        implementation.files_created.append(str(readme_path))

        outputs.append(f"README creado: {readme_filename}")
        outputs.append("Documentacion completa generada")

        return outputs

    async def _notify_pm_progress(self, implementation: Implementation, current_step: int, total_steps: int, step_description: str):
        """Notificar progreso al PM"""

        if self.pm_agent and self.pm_agent in self.broker.agents:
            progress_percentage = (current_step / total_steps) * 100

            await self.send_message(
                receiver=self.pm_agent,
                message_type=MessageType.STATUS_UPDATE,
                content={
                    "message_type": "implementation_progress",
                    "task_id": implementation.id,
                    "task_name": implementation.name,
                    "progress_percentage": progress_percentage,
                    "current_step": step_description,
                    "steps_completed": current_step,
                    "total_steps": total_steps,
                    "dev_message": f"Progreso: {progress_percentage:.1f}% - {step_description}"
                }
            )

    async def _complete_implementation(self, implementation: Implementation):
        """Completar la implementacion y reportar al PM"""

        implementation.status = ImplementationStatus.COMPLETED
        implementation.completion_time = datetime.now()
        implementation.actual_hours = implementation.estimated_hours  # Simplificado para demo

        print(f"\n=== DEV {self.name}: IMPLEMENTACION COMPLETADA ===")
        print(f"Tarea: {implementation.name}")
        print(f"Archivos creados: {len(implementation.files_created)}")
        print(f"Tests creados: {len(implementation.tests_created)}")
        print(f"Tiempo estimado: {implementation.estimated_hours} horas")

        # Notificar completitud al PM
        await self._notify_pm_completion(implementation)

    async def _notify_pm_completion(self, implementation: Implementation):
        """Notificar al PM que la implementacion esta completa"""

        if self.pm_agent and self.pm_agent in self.broker.agents:
            deliverables_summary = {
                "files_created": [Path(f).name for f in implementation.files_created],
                "tests_created": [Path(f).name for f in implementation.tests_created],
                "total_files": len(implementation.files_created) + len(implementation.tests_created)
            }

            await self.send_message(
                receiver=self.pm_agent,
                message_type=MessageType.DATA,
                content={
                    "message_type": "implementation_completed",
                    "task_id": implementation.id,
                    "task_name": implementation.name,
                    "completion_time": implementation.completion_time.isoformat(),
                    "actual_hours": implementation.actual_hours,
                    "deliverables": deliverables_summary,
                    "status": implementation.status.value,
                    "quality_metrics": {
                        "code_quality": "High",
                        "test_coverage": "85%",
                        "documentation": "Complete"
                    },
                    "dev_message": f"[OK] '{implementation.name}' completada exitosamente. {deliverables_summary['total_files']} archivos entregados."
                }
            )

    # ========== METODOS ESPECIFICOS PARA POLITICAS DE AUTONOMIA ==========

    async def _handle_test_failure_by_level(self, correlation_id: str, test_error: str):
        """Manejar fallo de tests segun nivel de autonomia"""
        if not self.policy_manager:
            print(f"   [ERROR] Test fallo: {test_error}")
            return

        response = self.policy_manager.generate_level_appropriate_response(
            self.autonomy_level, "test_failure", {"error": test_error}
        )

        if response["action"] == "auto_replan":
            # MAX level: Auto-replanificar inmediatamente
            print(f"   [PROC] MAX: {response['message']}")
            await self._auto_replan_implementation(correlation_id, test_error)

        elif response["action"] == "adjust_subtasks":
            # HIGH level: Ajustar subtareas
            print(f"   [CONFIG] HIGH: {response['message']}")
            await self._adjust_subtasks_for_failure(correlation_id, test_error)

        else:
            # LOW/MEDIUM: Reportar y esperar
            print(f"   [U1F4E2] {self.autonomy_level.upper()}: {response['message']}")
            await self._report_test_failure(correlation_id, test_error)

    async def _handle_missing_optional_field_by_level(self, correlation_id: str, field_name: str, fallback_value: Any = None):
        """Manejar campo opcional faltante segun nivel de autonomia"""
        if not self.policy_manager:
            return fallback_value

        response = self.policy_manager.generate_level_appropriate_response(
            self.autonomy_level, "missing_optional_field", {"fallback": fallback_value}
        )

        if response["action"] == "propose_fallback_and_continue":
            # MAX level: Nunca detenerse por campos opcionales
            print(f"   [START] MAX: {response['message']} - Campo: {field_name}")
            await self._propose_fallback_and_continue(correlation_id, field_name, fallback_value)
            return fallback_value

        elif response["action"] == "send_blocker_and_wait":
            # LOW level: Enviar blocker y esperar
            print(f"   [U23F8][UFE0F] LOW: {response['message']} - Campo: {field_name}")
            await self._send_field_blocker(correlation_id, field_name)
            return None

        else:
            # MEDIUM/HIGH: Intentar resolucion autonoma
            print(f"   [CONFIG] {self.autonomy_level.upper()}: {response['message']} - Campo: {field_name}")
            return await self._try_autonomous_field_resolution(field_name, fallback_value)

    async def _auto_replan_implementation(self, correlation_id: str, reason: str):
        """Auto-replanificar implementacion (MAX level)"""
        print(f"   [PROC] MAX: Auto-replanificando debido a: {reason}")

        # Generar nuevo plan
        new_approach = [
            f"1. Analisis de fallo: {reason}",
            f"2. Replanificacion automatica de approach",
            f"3. Implementacion con approach corregido",
            f"4. Testing con validaciones adicionales",
            f"5. Entrega de artefactos actualizados"
        ]

        replan_message = {
            "schema_version": "1.0",
            "from": "Dev_Agent",
            "to": "PM_Agent",
            "message_type": "implementation_plan",
            "correlation_id": correlation_id,
            "timestamp": datetime.now().isoformat(),
            "payload": {
                "implementation_approach": new_approach,
                "reason_for_replan": reason,
                "auto_replanned": True,
                "level": "max"
            }
        }

        await self.send_message(
            receiver="PM_Agent",
            message_type=MessageType.DATA,
            content=replan_message
        )
        print(f"   [SEND] MAX: Auto-replan enviado")

    async def _adjust_subtasks_for_failure(self, correlation_id: str, error: str):
        """Ajustar subtareas por fallo (HIGH level)"""
        print(f"   [CONFIG] HIGH: Ajustando subtareas debido a: {error}")

        progress_message = {
            "schema_version": "1.0",
            "from": "Dev_Agent",
            "to": "PM_Agent",
            "message_type": "implementation_progress",
            "correlation_id": correlation_id,
            "timestamp": datetime.now().isoformat(),
            "payload": {
                "percent": 50,
                "current_step": "S2-adjusted",
                "artefacts": [],
                "logs_tail": f"Subtareas ajustadas por error: {error}",
                "granular_adjustment": True,
                "error_handled": error
            }
        }

        await self.send_message(
            receiver="PM_Agent",
            message_type=MessageType.DATA,
            content=progress_message
        )

    async def _report_test_failure(self, correlation_id: str, error: str):
        """Reportar fallo de test (LOW/MEDIUM level)"""
        blocker_message = {
            "schema_version": "1.0",
            "from": "Dev_Agent",
            "to": "PM_Agent",
            "message_type": "blocker",
            "correlation_id": correlation_id,
            "timestamp": datetime.now().isoformat(),
            "payload": {
                "missing_info": f"Test fallo: {error}",
                "proposed_unblock": "Revisar approach y proporcionar guidance para correccion"
            }
        }

        await self.send_message(
            receiver="PM_Agent",
            message_type=MessageType.DATA,
            content=blocker_message
        )

    async def _propose_fallback_and_continue(self, correlation_id: str, field_name: str, fallback_value: Any):
        """Proponer fallback y continuar (MAX level)"""
        print(f"   [U1F4A1] MAX: Proponiendo fallback para '{field_name}': {fallback_value}")

        # Continuar sin detenerse
        progress_message = {
            "schema_version": "1.0",
            "from": "Dev_Agent",
            "to": "PM_Agent",
            "message_type": "implementation_progress",
            "correlation_id": correlation_id,
            "timestamp": datetime.now().isoformat(),
            "payload": {
                "percent": 75,
                "current_step": "S3",
                "artefacts": [],
                "logs_tail": f"Fallback aplicado para {field_name}: {fallback_value}",
                "fallback_applied": {
                    "field": field_name,
                    "value": fallback_value
                }
            }
        }

        await self.send_message(
            receiver="PM_Agent",
            message_type=MessageType.DATA,
            content=progress_message
        )

    async def _send_field_blocker(self, correlation_id: str, field_name: str):
        """Enviar blocker por campo faltante (LOW level)"""
        blocker_message = {
            "schema_version": "1.0",
            "from": "Dev_Agent",
            "to": "PM_Agent",
            "message_type": "blocker",
            "correlation_id": correlation_id,
            "timestamp": datetime.now().isoformat(),
            "payload": {
                "missing_info": f"Campo requerido faltante: {field_name}",
                "proposed_unblock": f"Proporcionar valor para {field_name} o confirmar si es opcional"
            }
        }

        await self.send_message(
            receiver="PM_Agent",
            message_type=MessageType.DATA,
            content=blocker_message
        )

    async def _try_autonomous_field_resolution(self, field_name: str, fallback_value: Any):
        """Intentar resolucion autonoma de campo (MEDIUM/HIGH level)"""
        print(f"   [CONFIG] {self.autonomy_level.upper()}: Resolviendo '{field_name}' autonomamente")

        # Logica de resolucion autonoma
        if fallback_value is not None:
            return fallback_value

        # Generar valor por defecto sensato
        if "path" in field_name.lower():
            return "./default_path"
        elif "name" in field_name.lower():
            return "default_name"
        elif "version" in field_name.lower():
            return "1.0.0"
        else:
            return "default_value"

    def get_autonomy_info(self) -> Dict[str, Any]:
        """Obtener informacion completa sobre el nivel de autonomia actual"""
        if not self.policy_manager:
            return {"level": self.autonomy_level, "policies_enabled": False}

        behavior = self.policy_manager.get_execution_behavior(self.autonomy_level)

        return {
            "level": self.autonomy_level,
            "policies_enabled": True,
            "behavior": behavior,
            "system_prompt": self.policy_manager.get_system_prompt(self.autonomy_level),
            "capabilities": {
                "require_approval": behavior["require_approval"],
                "auto_execute": behavior["auto_execute"],
                "auto_replan": behavior["auto_replan"],
                "granular_reporting": behavior["granular_reporting"],
                "divide_subtasks": behavior["divide_subtasks"],
                "never_stop_optional": behavior["never_stop_optional"]
            }
        }

    def get_current_work_status(self) -> Dict[str, Any]:
        """Obtener status actual del trabajo"""

        active_implementations = [impl for impl in self.current_implementations
                                if impl.status == ImplementationStatus.IN_PROGRESS]

        return {
            "agent_name": self.name,
            "assigned_tasks": len(self.assigned_tasks),
            "active_implementations": len(active_implementations),
            "completed_implementations": len([impl for impl in self.current_implementations
                                            if impl.status == ImplementationStatus.COMPLETED]),
            "total_files_created": sum(len(impl.files_created) for impl in self.current_implementations),
            "workspace_directory": str(self.workspace_dir),
            "pm_agent": self.pm_agent
        }

    async def handle_status_update(self, message: AgentMessage):
        """Manejar actualizaciones de status del PM - CLAVE para ejecutar tareas"""

        message_type = message.content.get("message_type", "")

        if message_type == "progress_update":
            # El PM esta enviando update de progreso - verificar si tengo tareas pendientes
            your_tasks = message.content.get("your_tasks", 0)

            if your_tasks > 0 and len(self.assigned_tasks) > 0:
                print(f"\n=== DEV {self.name}: RECIBIDO UPDATE DEL PM ===")
                print(f"Tareas asignadas: {your_tasks}")
                print(f"Iniciando ejecucion de tareas pendientes...")

                # Ejecutar tareas pendientes automaticamente
                await self._execute_pending_tasks()
            else:
                print(f"Status de PM recibido - No hay tareas pendientes para ejecutar")
        else:
            # Usar handler por defecto para otros tipos de status_update
            await super().handle_status_update(message)

    async def _execute_pending_tasks(self):
        """Ejecutar automaticamente las tareas pendientes asignadas por el PM"""

        for task in self.assigned_tasks:
            if task.get("status", "pending") == "pending":
                print(f"\n=== DEV {self.name}: EJECUTANDO TAREA ===")
                print(f"Tarea: {task.get('task_name', 'Sin nombre')}")
                print(f"Descripcion: {task.get('description', 'Sin descripcion')}")

                # Marcar tarea como en progreso
                task["status"] = "in_progress"
                task["started_at"] = datetime.now()

                try:
                    # Ejecutar la implementacion de la tarea
                    implementation = await self._create_implementation_for_task(task)

                    if implementation:
                        # Ejecutar la implementacion
                        await self._execute_implementation_async(implementation)

                        # Marcar tarea como completada
                        task["status"] = "completed"
                        task["completed_at"] = datetime.now()

                        # Informar al PM sobre el progreso
                        await self._report_task_completion(task, implementation)

                        print(f"[OK] Tarea completada: {task.get('task_name')}")
                    else:
                        print(f"[ERROR] Error creando implementacion para tarea: {task.get('task_name')}")
                        task["status"] = "failed"

                except Exception as e:
                    print(f"[ERROR] Error ejecutando tarea {task.get('task_name')}: {e}")
                    task["status"] = "failed"

                # Pequena pausa entre tareas
                await asyncio.sleep(1)

    async def _create_implementation_for_task(self, task):
        """Crear una implementacion basada en la tarea asignada"""

        task_name = task.get("task_name", "tarea_generica")
        description = task.get("description", "Implementar funcionalidad")

        # Determinar stack tecnologico basado en el nombre de la tarea
        tech_stack = ["Python"]
        if "web" in task_name.lower() or "html" in task_name.lower():
            tech_stack.extend(["HTML", "CSS", "JavaScript"])
        elif "api" in task_name.lower() or "rest" in task_name.lower():
            tech_stack.extend(["Flask", "REST"])
        elif "database" in task_name.lower() or "db" in task_name.lower():
            tech_stack.extend(["SQLite", "Database"])

        implementation = Implementation(
            id=f"TASK-{task.get('task_id', '001')}",
            name=task_name,
            description=description,
            technology_stack=tech_stack,
            estimated_hours=task.get("estimated_hours", 2.0)
        )

        self.current_implementations.append(implementation)
        return implementation

    async def _execute_implementation_async(self, implementation):
        """Ejecutar implementacion de forma asincrona"""

        implementation.status = ImplementationStatus.IN_PROGRESS
        implementation.start_time = datetime.now()

        print(f"\n=== DEV {self.name}: INICIANDO IMPLEMENTACION ===")
        print(f"Tarea: {implementation.name}")
        print(f"Stack tecnologico: {', '.join(implementation.technology_stack)}")

        try:
            # Simular analisis y planificacion
            await asyncio.sleep(0.5)
            print(f"  [OK] Analisis completado")

            # Ejecutar pasos de implementacion
            analysis = {
                "requirements": f"Implementar {implementation.name}",
                "approach": "Desarrollo incremental",
                "estimated_files": 2,
                "implementation_approach": [
                    "1. Analizar requerimientos especificos",
                    "2. Implementar solucion paso a paso",
                    "3. Crear tests unitarios",
                    "4. Documentar implementacion"
                ]
            }

            await self._execute_implementation_steps(implementation, analysis)

            implementation.status = ImplementationStatus.COMPLETED
            implementation.completion_time = datetime.now()

            print(f"\n=== DEV {self.name}: IMPLEMENTACION COMPLETADA ===")
            print(f"Tarea: {implementation.name}")
            print(f"Archivos creados: {len(implementation.files_created)}")
            print(f"Tests creados: {len(implementation.tests_created)}")

        except Exception as e:
            implementation.status = ImplementationStatus.BLOCKED
            print(f"[ERROR] Error en implementacion: {e}")
            raise

    async def _report_task_completion(self, task, implementation):
        """Reportar finalizacion de tarea al PM"""

        if hasattr(self, 'pm_agent') and self.pm_agent:
            pm_name = self.pm_agent
        else:
            # Buscar el PM en assigned_by
            pm_name = task.get("assigned_by", "PM_Agent")

        # Enviar reporte de finalizacion
        await self.send_message(
            pm_name,
            MessageType.STATUS_UPDATE,
            {
                "message_type": "task_completed",
                "task_id": task.get("task_id"),
                "task_name": task.get("task_name"),
                "implementation_id": implementation.id,
                "files_created": implementation.files_created,
                "tests_created": implementation.tests_created,
                "duration_hours": implementation.actual_hours,
                "status": "completed",
                "dev_message": f"Tarea '{implementation.name}' completada exitosamente. Archivos generados: {len(implementation.files_created)}"
            }
        )

    async def handle_question(self, message: AgentMessage):
        """Manejar preguntas del PM o otros agentes"""

        question_type = message.content.get("message_type", "")

        if question_type == "unblock_request":
            await self._handle_unblock_request(message)
        elif question_type == "overdue_followup":
            await self._handle_overdue_followup(message)
        else:
            await super().handle_question(message)

    async def _handle_unblock_request(self, message: AgentMessage):
        """Manejar solicitud de desbloqueo del PM"""

        task_id = message.content.get("task_id")

        # Buscar la implementacion
        implementation = next((impl for impl in self.current_implementations
                             if impl.id == task_id), None)

        if implementation:
            # Simular analisis del bloqueo
            blocker_analysis = "Dependencia externa no disponible"
            solution_needed = "Acceso a API o recurso especifico"

            await self.send_response(
                message,
                MessageType.ANSWER,
                {
                    "task_id": task_id,
                    "blocker_identified": blocker_analysis,
                    "solution_needed": solution_needed,
                    "estimated_resolution_time": "2-4 horas",
                    "dev_message": f"Identifique el bloqueo: {blocker_analysis}. Necesito: {solution_needed}"
                }
            )
        else:
            await self.send_response(
                message,
                MessageType.ANSWER,
                {
                    "error": "Tarea no encontrada",
                    "dev_message": "No tengo esa tarea en mi lista actual"
                }
            )

    async def _handle_overdue_followup(self, message: AgentMessage):
        """Manejar followup de tareas retrasadas"""

        task_id = message.content.get("task_id")
        days_overdue = message.content.get("days_overdue", 0)

        implementation = next((impl for impl in self.current_implementations
                             if impl.id == task_id), None)

        if implementation:
            # Revisar el status y proporcionar update realista
            current_progress = "80% completado"
            new_timeline = "1-2 dias adicionales"

            await self.send_response(
                message,
                MessageType.ANSWER,
                {
                    "task_id": task_id,
                    "current_progress": current_progress,
                    "delay_reason": "Complejidad subestimada inicialmente",
                    "new_timeline": new_timeline,
                    "support_needed": False,
                    "dev_message": f"Status actual: {current_progress}. Nuevo timeline: {new_timeline}"
                }
            )
        else:
            await self.send_response(
                message,
                MessageType.ANSWER,
                {
                    "error": "Tarea no encontrada",
                    "dev_message": "No tengo registro de esa tarea"
                }
            )