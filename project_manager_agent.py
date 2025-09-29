#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Agente Project Manager (PM) - Especializado en gestion de proyectos autonoma
"""


import os
import sys
if sys.platform == "win32":
    os.environ["PYTHONIOENCODING"] = "utf-8"

import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum

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


class TaskStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class TaskPriority(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class ProjectTask:
    """Tarea individual del proyecto"""
    id: str
    name: str
    description: str
    assigned_to: Optional[str] = None
    priority: TaskPriority = TaskPriority.MEDIUM
    status: TaskStatus = TaskStatus.PENDING
    estimated_hours: float = 0.0
    actual_hours: float = 0.0
    dependencies: List[str] = field(default_factory=list)
    deliverables: List[str] = field(default_factory=list)
    start_date: Optional[datetime] = None
    due_date: Optional[datetime] = None
    completion_date: Optional[datetime] = None
    notes: List[str] = field(default_factory=list)


@dataclass
class ProjectPlan:
    """Plan completo del proyecto"""
    objective: str
    description: str
    tasks: List[ProjectTask]
    team_members: List[str]
    estimated_duration: str
    milestones: List[Dict[str, Any]]
    risks: List[str]
    success_criteria: List[str]
    created_at: datetime = field(default_factory=datetime.now)


class ProjectManagerAgent(RoleAwareAgent):
    """Agente especializado en gestion de proyectos"""

    def __init__(self, name: str, broker: MessageBroker):
        super().__init__(name, broker)
        self.current_project: Optional[ProjectPlan] = None
        self.team_members: List[str] = []
        self.project_history: List[ProjectPlan] = []
        self.active_communications: Dict[str, List[AgentMessage]] = {}

        # Override de capacidades para PM
        self.capabilities.preferred_roles = [RoleType.PROJECT_MANAGER, RoleType.ANALYST]
        self.capabilities.specializations = [
            "project_planning", "team_coordination", "risk_management",
            "quality_assurance", "stakeholder_communication"
        ]
        self.capabilities.self_assessment.update({
            "leadership": 9,
            "project_management": 9,
            "communication": 8,
            "planning": 9,
            "coordination": 8
        })

    async def start_project(self, objective: str, team_members: List[str]) -> ProjectPlan:
        """Iniciar un nuevo proyecto de forma autonoma"""

        print(f"\n=== PM {self.name}: INICIANDO PROYECTO ===")
        print(f"Objetivo: {objective}")
        print(f"Equipo: {team_members}")

        self.team_members = team_members

        # 1. Analizar el objetivo
        print(f"\n1. Analizando objetivo...")
        analysis = await self._analyze_objective(objective)

        # 2. Crear plan de proyecto
        print(f"\n2. Creando plan de proyecto...")
        project_plan = await self._create_project_plan(objective, analysis)

        # 3. Comunicar plan al equipo
        print(f"\n3. Comunicando plan al equipo...")
        await self._communicate_plan_to_team(project_plan)

        # 4. Asignar tareas iniciales
        print(f"\n4. Asignando tareas iniciales...")
        await self._assign_initial_tasks(project_plan)

        self.current_project = project_plan
        self.project_history.append(project_plan)

        print(f"\nPROYECTO INICIADO - {len(project_plan.tasks)} tareas creadas")
        return project_plan

    async def _analyze_objective(self, objective: str) -> Dict[str, Any]:
        """Analizar el objetivo para entender alcance y requerimientos"""

        objective_lower = objective.lower()

        # Determinar tipo de proyecto
        project_type = "development"
        if any(word in objective_lower for word in ["analizar", "estudiar", "investigar"]):
            project_type = "analysis"
        elif any(word in objective_lower for word in ["implementar", "desarrollar", "crear"]):
            project_type = "development"
        elif any(word in objective_lower for word in ["automatizar", "optimizar", "mejorar"]):
            project_type = "optimization"

        # Estimar complejidad
        complexity = "medium"
        complexity_indicators = len([word for word in ["sistema", "completo", "complejo", "integrar", "escalable"]
                                   if word in objective_lower])

        if complexity_indicators >= 3 or len(objective.split()) > 15:
            complexity = "high"
        elif complexity_indicators <= 1 and len(objective.split()) < 8:
            complexity = "low"

        # Identificar areas tecnicas
        technical_areas = []
        if any(word in objective_lower for word in ["frontend", "ui", "interfaz"]):
            technical_areas.append("frontend")
        if any(word in objective_lower for word in ["backend", "api", "servidor", "base"]):
            technical_areas.append("backend")
        if any(word in objective_lower for word in ["datos", "database", "almacen"]):
            technical_areas.append("database")
        if any(word in objective_lower for word in ["web", "http", "url"]):
            technical_areas.append("web")

        # Estimar duracion
        duration_days = 3  # Base
        if complexity == "high":
            duration_days = 7
        elif complexity == "low":
            duration_days = 1

        duration_days += len(technical_areas)  # +1 dia por area tecnica

        analysis = {
            "project_type": project_type,
            "complexity": complexity,
            "technical_areas": technical_areas,
            "estimated_duration_days": duration_days,
            "estimated_hours": duration_days * 6,  # 6 horas por dia
            "key_deliverables": self._identify_key_deliverables(objective),
            "potential_risks": self._identify_risks(objective, complexity),
            "success_criteria": self._define_success_criteria(objective)
        }

        print(f"  Analisis completado:")
        print(f"    Tipo: {project_type}")
        print(f"    Complejidad: {complexity}")
        print(f"    Duracion estimada: {duration_days} dias")
        print(f"    Areas tecnicas: {technical_areas}")

        return analysis

    def _identify_key_deliverables(self, objective: str) -> List[str]:
        """Identificar entregables clave basado en el objetivo"""

        deliverables = []
        objective_lower = objective.lower()

        # Entregables comunes
        if any(word in objective_lower for word in ["crear", "desarrollar", "implementar"]):
            deliverables.append("Codigo fuente implementado")
            deliverables.append("Documentacion tecnica")

        if any(word in objective_lower for word in ["sistema", "aplicacion", "app"]):
            deliverables.append("Sistema funcional")
            deliverables.append("Manual de usuario")

        if any(word in objective_lower for word in ["test", "prueba", "verificar"]):
            deliverables.append("Suite de pruebas")
            deliverables.append("Reporte de testing")

        if any(word in objective_lower for word in ["deploy", "produccion", "lanzar"]):
            deliverables.append("Sistema desplegado")
            deliverables.append("Guia de despliegue")

        # Entregables por defecto si no se identifican especificos
        if not deliverables:
            deliverables = ["Solucion implementada", "Documentacion", "Reporte de resultados"]

        return deliverables

    def _identify_risks(self, objective: str, complexity: str) -> List[str]:
        """Identificar riesgos potenciales del proyecto"""

        risks = []
        objective_lower = objective.lower()

        # Riesgos por complejidad
        if complexity == "high":
            risks.extend([
                "Subestimacion del tiempo requerido",
                "Complejidad tecnica no anticipada",
                "Necesidad de refactoring durante desarrollo"
            ])

        # Riesgos por tipo de objetivo
        if any(word in objective_lower for word in ["integrar", "conectar", "combinar"]):
            risks.append("Problemas de compatibilidad entre sistemas")

        if any(word in objective_lower for word in ["nuevo", "innovador", "experimental"]):
            risks.append("Tecnologias no probadas")

        if any(word in objective_lower for word in ["performance", "optimizar", "escalable"]):
            risks.append("Requisitos de rendimiento no alcanzables")

        # Riesgos generales
        risks.extend([
            "Cambios en requerimientos",
            "Dependencias externas no disponibles"
        ])

        return risks

    def _define_success_criteria(self, objective: str) -> List[str]:
        """Definir criterios de exito del proyecto"""

        criteria = []
        objective_lower = objective.lower()

        # Criterios basicos
        criteria.append("Objetivo cumplido segun especificacion")
        criteria.append("Entregables completados y documentados")
        criteria.append("Calidad del codigo verificada")

        # Criterios especificos
        if any(word in objective_lower for word in ["funcional", "trabajar", "operar"]):
            criteria.append("Sistema operativo sin errores criticos")

        if any(word in objective_lower for word in ["usuario", "interfaz", "ui"]):
            criteria.append("Interfaz usable y accesible")

        if any(word in objective_lower for word in ["performance", "rapido", "eficiente"]):
            criteria.append("Metricas de rendimiento cumplidas")

        return criteria

    async def _create_project_plan(self, objective: str, analysis: Dict[str, Any]) -> ProjectPlan:
        """Crear plan detallado del proyecto"""

        tasks = []
        task_counter = 1

        # Fase 1: Planificacion y analisis
        tasks.append(ProjectTask(
            id=f"TASK-{task_counter:03d}",
            name="Analisis detallado de requerimientos",
            description="Analizar y documentar todos los requerimientos del proyecto",
            priority=TaskPriority.HIGH,
            estimated_hours=2.0,
            deliverables=["Documento de requerimientos", "Especificaciones tecnicas"]
        ))
        task_counter += 1

        # Fase 2: Diseno
        if analysis["project_type"] == "development":
            tasks.append(ProjectTask(
                id=f"TASK-{task_counter:03d}",
                name="Diseno de arquitectura",
                description="Disenar la arquitectura del sistema",
                priority=TaskPriority.HIGH,
                estimated_hours=3.0,
                dependencies=[tasks[-1].id],
                deliverables=["Diagrama de arquitectura", "Especificaciones de diseno"]
            ))
            task_counter += 1

        # Fase 3: Implementacion (tareas especificas por area tecnica)
        for area in analysis["technical_areas"]:
            tasks.append(ProjectTask(
                id=f"TASK-{task_counter:03d}",
                name=f"Implementar componente {area}",
                description=f"Desarrollar e implementar la funcionalidad de {area}",
                priority=TaskPriority.MEDIUM,
                estimated_hours=4.0,
                dependencies=[t.id for t in tasks if t.name.startswith("Diseno")],
                deliverables=[f"Codigo {area}", f"Tests {area}"]
            ))
            task_counter += 1

        # Si no hay areas especificas, crear tarea de implementacion general
        if not analysis["technical_areas"]:
            tasks.append(ProjectTask(
                id=f"TASK-{task_counter:03d}",
                name="Implementacion principal",
                description="Implementar la funcionalidad principal del sistema",
                priority=TaskPriority.MEDIUM,
                estimated_hours=6.0,
                dependencies=[t.id for t in tasks],
                deliverables=["Codigo implementado", "Tests unitarios"]
            ))
            task_counter += 1

        # Fase 4: Testing y validacion
        tasks.append(ProjectTask(
            id=f"TASK-{task_counter:03d}",
            name="Testing y validacion",
            description="Ejecutar pruebas y validar funcionalidad",
            priority=TaskPriority.HIGH,
            estimated_hours=2.0,
            dependencies=[t.id for t in tasks if "Implementar" in t.name or "Implementacion" in t.name],
            deliverables=["Reporte de testing", "Sistema validado"]
        ))
        task_counter += 1

        # Fase 5: Documentacion y entrega
        tasks.append(ProjectTask(
            id=f"TASK-{task_counter:03d}",
            name="Documentacion y entrega final",
            description="Documentar solucion y preparar entrega",
            priority=TaskPriority.MEDIUM,
            estimated_hours=1.0,
            dependencies=[tasks[-1].id],
            deliverables=["Documentacion completa", "Guia de usuario"]
        ))

        # Crear milestones
        milestones = [
            {
                "name": "Analisis completado",
                "tasks": [t.id for t in tasks if "Analisis" in t.name],
                "percentage": 20
            },
            {
                "name": "Diseno completado",
                "tasks": [t.id for t in tasks if "Diseno" in t.name],
                "percentage": 40
            },
            {
                "name": "Implementacion completada",
                "tasks": [t.id for t in tasks if "Implementar" in t.name or "Implementacion" in t.name],
                "percentage": 80
            },
            {
                "name": "Proyecto completado",
                "tasks": [tasks[-1].id],
                "percentage": 100
            }
        ]

        return ProjectPlan(
            objective=objective,
            description=f"Proyecto para: {objective}",
            tasks=tasks,
            team_members=self.team_members,
            estimated_duration=f"{analysis['estimated_duration_days']} dias",
            milestones=milestones,
            risks=analysis["potential_risks"],
            success_criteria=analysis["success_criteria"]
        )

    async def _communicate_plan_to_team(self, project_plan: ProjectPlan):
        """Comunicar el plan del proyecto al equipo"""

        for member in self.team_members:
            if member in self.broker.agents:
                print(f"  Comunicando plan a {member}...")

                await self.send_message(
                    receiver=member,
                    message_type=MessageType.DATA,
                    content={
                        "message_type": "project_plan",
                        "objective": project_plan.objective,
                        "total_tasks": len(project_plan.tasks),
                        "estimated_duration": project_plan.estimated_duration,
                        "your_role": "developer",  # Por ahora asumimos dev
                        "milestones": project_plan.milestones,
                        "success_criteria": project_plan.success_criteria,
                        "pm_message": f"Hola {member}, como PM te comparto el plan del proyecto. Te mantendre informado del progreso."
                    }
                )

    async def _assign_initial_tasks(self, project_plan: ProjectPlan):
        """Asignar tareas iniciales al equipo"""

        available_devs = [member for member in self.team_members if member != self.name]

        if not available_devs:
            print("  ADVERTENCIA: No hay desarrolladores disponibles para asignar tareas")
            return

        # Asignar las primeras tareas que no tienen dependencias
        initial_tasks = [task for task in project_plan.tasks if not task.dependencies]

        for i, task in enumerate(initial_tasks):
            if i < len(available_devs):
                dev = available_devs[i]
                await self._assign_task_to_developer(task, dev)

    async def _assign_task_to_developer(self, task: ProjectTask, developer: str):
        """Asignar una tarea especifica a un desarrollador usando protocolo v2.0"""

        task.assigned_to = developer
        task.status = TaskStatus.PENDING
        task.start_date = datetime.now()

        print(f"  Asignando tarea '{task.name}' a {developer} [PROTOCOLO v2.0]")

        if developer in self.broker.agents:
            if VALIDATION_V2_ENABLED:
                # Usar protocolo v2.0 estricto
                v2_message = message_factory.create_task_spec(
                    task_id=task.id,
                    task_name=task.name,
                    description=task.description,
                    priority=task.priority.value,
                    estimated_hours=task.estimated_hours,
                    deliverables=task.deliverables,
                    dependencies=task.dependencies,
                    acceptance_criteria=[
                        "Codigo implementado y funcional",
                        "Tests unitarios pasando",
                        "Documentacion actualizada"
                    ]
                )

                print(f"[SEND] PM: Enviando task_spec para {task.id}")
                await self.send_v2_message(developer, v2_message)
            else:
                # Fallback a protocolo legacy
                await self.send_message(
                    receiver=developer,
                    message_type=MessageType.APPROVAL_REQUEST,
                    content={
                        "message_type": "task_assignment",
                        "task_id": task.id,
                        "task_name": task.name,
                        "description": task.description,
                        "priority": task.priority.value,
                        "estimated_hours": task.estimated_hours,
                        "deliverables": task.deliverables,
                        "dependencies": task.dependencies,
                        "pm_instructions": "Por favor confirma si puedes tomar esta tarea."
                    },
                    requires_approval=True
                )

    async def monitor_project_progress(self) -> Dict[str, Any]:
        """Monitorear progreso del proyecto de forma autonoma"""

        if not self.current_project:
            return {"error": "No hay proyecto activo"}

        print(f"\n=== PM {self.name}: MONITOREANDO PROGRESO ===")

        # Verificar estado de tareas
        progress_report = await self._check_task_progress()

        # Comunicar con el equipo sobre el progreso
        await self._communicate_progress_updates(progress_report)

        # Tomar acciones correctivas si es necesario
        await self._take_corrective_actions(progress_report)

        return progress_report

    async def _check_task_progress(self) -> Dict[str, Any]:
        """Verificar progreso de todas las tareas"""

        if not self.current_project:
            return {}

        task_status_count = {status.value: 0 for status in TaskStatus}
        tasks_by_member = {}
        blocked_tasks = []
        overdue_tasks = []

        for task in self.current_project.tasks:
            task_status_count[task.status.value] += 1

            if task.assigned_to:
                if task.assigned_to not in tasks_by_member:
                    tasks_by_member[task.assigned_to] = []
                tasks_by_member[task.assigned_to].append(task)

            if task.status == TaskStatus.BLOCKED:
                blocked_tasks.append(task)

            if task.due_date and task.due_date < datetime.now() and task.status != TaskStatus.COMPLETED:
                overdue_tasks.append(task)

        # Calcular porcentaje completado
        total_tasks = len(self.current_project.tasks)
        completed_tasks = task_status_count[TaskStatus.COMPLETED.value]
        completion_percentage = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0

        progress_report = {
            "completion_percentage": completion_percentage,
            "task_status_count": task_status_count,
            "tasks_by_member": {member: len(tasks) for member, tasks in tasks_by_member.items()},
            "blocked_tasks": len(blocked_tasks),
            "overdue_tasks": len(overdue_tasks),
            "next_milestone": self._get_next_milestone(),
            "risks_identified": self._identify_current_risks()
        }

        print(f"  Progreso: {completion_percentage:.1f}% completado")
        print(f"  Tareas: {task_status_count}")
        if blocked_tasks:
            print(f"  ALERTA: {len(blocked_tasks)} tareas bloqueadas")
        if overdue_tasks:
            print(f"  ALERTA: {len(overdue_tasks)} tareas retrasadas")

        return progress_report

    def _get_next_milestone(self) -> Optional[Dict[str, Any]]:
        """Obtener el proximo milestone pendiente"""

        if not self.current_project:
            return None

        for milestone in self.current_project.milestones:
            milestone_tasks = milestone["tasks"]
            completed_milestone_tasks = [
                task for task in self.current_project.tasks
                if task.id in milestone_tasks and task.status == TaskStatus.COMPLETED
            ]

            if len(completed_milestone_tasks) < len(milestone_tasks):
                return {
                    "name": milestone["name"],
                    "progress": len(completed_milestone_tasks) / len(milestone_tasks) * 100,
                    "remaining_tasks": len(milestone_tasks) - len(completed_milestone_tasks)
                }

        return None

    def _identify_current_risks(self) -> List[str]:
        """Identificar riesgos actuales basado en el estado del proyecto"""

        risks = []

        if not self.current_project:
            return risks

        # Verificar tareas bloqueadas
        blocked_count = sum(1 for task in self.current_project.tasks if task.status == TaskStatus.BLOCKED)
        if blocked_count > 0:
            risks.append(f"{blocked_count} tareas bloqueadas afectando el cronograma")

        # Verificar tareas retrasadas
        overdue_count = sum(1 for task in self.current_project.tasks
                           if task.due_date and task.due_date < datetime.now()
                           and task.status != TaskStatus.COMPLETED)
        if overdue_count > 0:
            risks.append(f"{overdue_count} tareas retrasadas")

        # Verificar carga de trabajo desbalanceada
        tasks_by_member = {}
        for task in self.current_project.tasks:
            if task.assigned_to and task.status in [TaskStatus.PENDING, TaskStatus.IN_PROGRESS]:
                tasks_by_member[task.assigned_to] = tasks_by_member.get(task.assigned_to, 0) + 1

        if tasks_by_member:
            max_tasks = max(tasks_by_member.values())
            min_tasks = min(tasks_by_member.values())
            if max_tasks - min_tasks > 2:
                risks.append("Carga de trabajo desbalanceada en el equipo")

        return risks

    async def _communicate_progress_updates(self, progress_report: Dict[str, Any]):
        """Comunicar updates de progreso al equipo"""

        for member in self.team_members:
            if member != self.name and member in self.broker.agents:
                await self.send_message(
                    receiver=member,
                    message_type=MessageType.STATUS_UPDATE,
                    content={
                        "message_type": "progress_update",
                        "project_completion": progress_report["completion_percentage"],
                        "your_tasks": progress_report["tasks_by_member"].get(member, 0),
                        "next_milestone": progress_report["next_milestone"],
                        "team_status": "On track" if progress_report["blocked_tasks"] == 0 else "Issues detected",
                        "pm_message": f"Update del proyecto: {progress_report['completion_percentage']:.1f}% completado."
                    }
                )

    async def _take_corrective_actions(self, progress_report: Dict[str, Any]):
        """Tomar acciones correctivas basadas en el progreso"""

        # Si hay tareas bloqueadas, investigar
        if progress_report["blocked_tasks"] > 0:
            await self._address_blocked_tasks()

        # Si hay retrasos, redistribuir tareas
        if progress_report["overdue_tasks"] > 0:
            await self._address_overdue_tasks()

        # Si el progreso es muy lento, escalate
        if progress_report["completion_percentage"] < 10 and len(self.current_project.tasks) > 0:
            print(f"  ACCION: Progreso lento detectado, revisando asignaciones...")

    async def _address_blocked_tasks(self):
        """Abordar tareas bloqueadas"""

        if not self.current_project:
            return

        blocked_tasks = [task for task in self.current_project.tasks if task.status == TaskStatus.BLOCKED]

        for task in blocked_tasks:
            if task.assigned_to and task.assigned_to in self.broker.agents:
                print(f"  Investigando tarea bloqueada: {task.name}")

                await self.send_message(
                    receiver=task.assigned_to,
                    message_type=MessageType.QUESTION,
                    content={
                        "message_type": "unblock_request",
                        "task_id": task.id,
                        "task_name": task.name,
                        "question": "[U00BF]Que necesitas para desbloquear esta tarea? [U00BF]Como puedo ayudarte como PM?",
                        "pm_support": "Estoy aqui para remover cualquier bloqueador."
                    },
                    requires_approval=True
                )

    async def _address_overdue_tasks(self):
        """Abordar tareas retrasadas"""

        if not self.current_project:
            return

        overdue_tasks = [task for task in self.current_project.tasks
                        if task.due_date and task.due_date < datetime.now()
                        and task.status != TaskStatus.COMPLETED]

        for task in overdue_tasks:
            if task.assigned_to and task.assigned_to in self.broker.agents:
                print(f"  Siguiendo up tarea retrasada: {task.name}")

                await self.send_message(
                    receiver=task.assigned_to,
                    message_type=MessageType.QUESTION,
                    content={
                        "message_type": "overdue_followup",
                        "task_id": task.id,
                        "task_name": task.name,
                        "days_overdue": (datetime.now() - task.due_date).days,
                        "question": "Esta tarea esta retrasada. [U00BF]Cual es el status actual y nuevo timeline estimado?",
                        "pm_support": "[U00BF]Necesitas que reasigne parte del trabajo o recursos adicionales?"
                    },
                    requires_approval=True
                )

    async def complete_project(self) -> Dict[str, Any]:
        """Completar el proyecto y generar reporte final"""

        if not self.current_project:
            return {"error": "No hay proyecto activo"}

        print(f"\n=== PM {self.name}: COMPLETANDO PROYECTO ===")

        # Verificar que todas las tareas esten completadas
        incomplete_tasks = [task for task in self.current_project.tasks
                           if task.status != TaskStatus.COMPLETED]

        if incomplete_tasks:
            print(f"ADVERTENCIA: {len(incomplete_tasks)} tareas aun pendientes")
            for task in incomplete_tasks:
                print(f"  - {task.name} ({task.status.value})")

        # Generar reporte final
        final_report = await self._generate_final_report()

        # Comunicar finalizacion al equipo
        await self._communicate_project_completion(final_report)

        return final_report

    async def _generate_final_report(self) -> Dict[str, Any]:
        """Generar reporte final del proyecto"""

        if not self.current_project:
            return {}

        completed_tasks = [task for task in self.current_project.tasks
                          if task.status == TaskStatus.COMPLETED]

        total_hours = sum(task.actual_hours or task.estimated_hours for task in self.current_project.tasks)

        report = {
            "project_objective": self.current_project.objective,
            "completion_date": datetime.now().isoformat(),
            "duration_days": (datetime.now() - self.current_project.created_at).days,
            "tasks_completed": len(completed_tasks),
            "tasks_total": len(self.current_project.tasks),
            "completion_rate": len(completed_tasks) / len(self.current_project.tasks) * 100,
            "total_hours_spent": total_hours,
            "deliverables": [],
            "team_performance": {},
            "lessons_learned": [],
            "success_criteria_met": self._evaluate_success_criteria()
        }

        # Recopilar entregables
        for task in completed_tasks:
            report["deliverables"].extend(task.deliverables)

        # Evaluar performance del equipo
        for member in self.team_members:
            member_tasks = [task for task in self.current_project.tasks if task.assigned_to == member]
            completed_member_tasks = [task for task in member_tasks if task.status == TaskStatus.COMPLETED]

            if member_tasks:
                report["team_performance"][member] = {
                    "tasks_assigned": len(member_tasks),
                    "tasks_completed": len(completed_member_tasks),
                    "completion_rate": len(completed_member_tasks) / len(member_tasks) * 100
                }

        return report

    def _evaluate_success_criteria(self) -> List[Dict[str, Any]]:
        """Evaluar si se cumplieron los criterios de exito"""

        if not self.current_project:
            return []

        evaluations = []

        for criterion in self.current_project.success_criteria:
            # Evaluacion simple basada en completitud de tareas
            completion_rate = len([task for task in self.current_project.tasks
                                 if task.status == TaskStatus.COMPLETED]) / len(self.current_project.tasks)

            met = completion_rate >= 0.9  # 90% de tareas completadas

            evaluations.append({
                "criterion": criterion,
                "met": met,
                "evidence": f"Completitud de tareas: {completion_rate * 100:.1f}%"
            })

        return evaluations

    async def _communicate_project_completion(self, final_report: Dict[str, Any]):
        """Comunicar finalizacion del proyecto al equipo"""

        for member in self.team_members:
            if member != self.name and member in self.broker.agents:
                await self.send_message(
                    receiver=member,
                    message_type=MessageType.DATA,
                    content={
                        "message_type": "project_completion",
                        "completion_rate": final_report["completion_rate"],
                        "your_performance": final_report["team_performance"].get(member, {}),
                        "deliverables": final_report["deliverables"],
                        "pm_message": f"[U00A1]Proyecto completado! Gracias por tu excelente trabajo. Tasa de completitud: {final_report['completion_rate']:.1f}%"
                    }
                )

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
            print(f"[MSG] PM: Recibido {message_type} v1.0 [PROTOCOLO ESTRICTO] de {v2_content.get('from')}")
            await self._handle_v1_message(v2_content, payload)
            return

        print(f"[MSG] PM: Recibido {message_type} v2.0 de {v2_content.get('from')}")

        handlers = {
            "ack": self._handle_v2_ack,
            "implementation_plan": self._handle_v2_implementation_plan,
            "implementation_started": self._handle_v2_implementation_started,
            "implementation_progress": self._handle_v2_implementation_progress,
            "implementation_completed": self._handle_v2_implementation_completed
        }

        handler = handlers.get(message_type)
        if handler:
            await handler(v2_content, payload)
        else:
            print(f"[WARN] PM: Tipo de mensaje v2.0 no manejado: {message_type}")

    async def _handle_v1_message(self, v1_content: Dict[str, Any], payload: Dict[str, Any]):
        """Manejar mensajes del protocolo estricto v1.0"""

        message_type = v1_content.get("message_type")
        correlation_id = v1_content.get("correlation_id")

        # Validar mensaje segun contrato v1.0
        is_valid, error_msg = GlobalSystemPrompt.validate_global_message(v1_content)
        if not is_valid:
            print(f"[ERROR] PM: Mensaje v1.0 invalido: {error_msg}")
            return

        handlers_v1 = {
            "answer": self._handle_v1_answer,           # Bootstrap response del Dev
            "ack": self._handle_v1_ack,                 # ACK del Dev
            "implementation_plan": self._handle_v1_implementation_plan,  # Plan del Dev
            "implementation_started": self._handle_v1_implementation_started,
            "implementation_progress": self._handle_v1_implementation_progress,
            "implementation_completed": self._handle_v1_implementation_completed,
            "error": self._handle_v1_error,
            "blocker": self._handle_v1_blocker
        }

        handler = handlers_v1.get(message_type)
        if handler:
            await handler(v1_content, payload, correlation_id)
        else:
            print(f"[WARN] PM: Tipo de mensaje v1.0 no manejado: {message_type}")

    async def _handle_v1_answer(self, v1_content: Dict[str, Any], payload: Dict[str, Any], correlation_id: str):
        """Manejar respuesta bootstrap del Dev"""

        if correlation_id == "BOOTSTRAP":
            print("[OK] PM: Bootstrap response recibido")
            ready = payload.get("ready", False)
            capabilities = payload.get("capabilities", [])
            contract_version = payload.get("contract_version")

            if ready and contract_version == "1.0":
                print(f"   Dev capabilities: {capabilities}")
                print(f"   Contract version: {contract_version}")
                print("   [START] Dev esta listo para el protocolo v1.0")
            else:
                print("   [ERROR] Dev no esta listo o version de contrato incorrecta")

    async def _handle_v1_ack(self, v1_content: Dict[str, Any], payload: Dict[str, Any], correlation_id: str):
        """Manejar ACK del Dev en protocolo v1.0"""

        received = payload.get("received", False)
        if received:
            print(f"[OK] PM: ACK confirmado para {correlation_id}")
        else:
            print(f"[ERROR] PM: ACK negativo para {correlation_id}")

    async def _handle_v1_implementation_plan(self, v1_content: Dict[str, Any], payload: Dict[str, Any], correlation_id: str):
        """Manejar plan de implementacion v1.0"""

        implementation_approach = payload.get("implementation_approach", [])
        steps = payload.get("steps", [])
        eta_hours = payload.get("eta_hours", 0)

        print(f"[CLIPBOARD] PM: Plan de implementacion recibido [{correlation_id}]")
        print(f"   Enfoque: {len(implementation_approach)} pasos")
        print(f"   Steps: {len(steps)} etapas")
        print(f"   ETA: {eta_hours} horas")

        # En protocolo estricto, PM aprueba automaticamente si es valido
        if implementation_approach and steps:
            print(f"[OK] PM: Plan aprobado automaticamente [{correlation_id}]")
        else:
            print(f"[ERROR] PM: Plan rechazado - informacion incompleta [{correlation_id}]")

    async def _handle_v1_implementation_started(self, v1_content: Dict[str, Any], payload: Dict[str, Any], correlation_id: str):
        """Manejar inicio de implementacion v1.0"""

        started_step = payload.get("started_step", "Unknown")
        print(f"[START] PM: Implementacion iniciada [{correlation_id}] - Step: {started_step}")

    async def _handle_v1_implementation_progress(self, v1_content: Dict[str, Any], payload: Dict[str, Any], correlation_id: str):
        """Manejar progreso de implementacion v1.0"""

        percent = payload.get("percent", 0)
        current_step = payload.get("current_step", "Unknown")
        artifacts = payload.get("artefacts", [])

        print(f"[CHART] PM: Progreso {percent}% [{correlation_id}] - {current_step}")
        if artifacts:
            print(f"   Artefactos: {artifacts}")

    async def _handle_v1_implementation_completed(self, v1_content: Dict[str, Any], payload: Dict[str, Any], correlation_id: str):
        """Manejar implementacion completada v1.0"""

        files = payload.get("files", [])
        tests_summary = payload.get("tests_summary", {})

        print(f"[DONE] PM: Implementacion completada [{correlation_id}]")
        print(f"   Archivos: {len(files)} creados")
        print(f"   Tests: {tests_summary}")

        # Listar archivos creados con hashes
        for file_info in files:
            path = file_info.get("path", "unknown")
            sha256 = file_info.get("sha256", "no-hash")[:8]  # Primeros 8 caracteres
            print(f"     [FILE] {path} ({sha256}...)")

    async def _handle_v1_error(self, v1_content: Dict[str, Any], payload: Dict[str, Any], correlation_id: str):
        """Manejar error v1.0"""

        details = payload.get("details", "Error sin detalles")
        requires_clarification = payload.get("requires_clarification", False)

        print(f"[ERROR] PM: Error recibido [{correlation_id}]")
        print(f"   Detalles: {details}")

        if requires_clarification:
            print(f"   [WARN] Requiere aclaracion del PM")

    async def _handle_v1_blocker(self, v1_content: Dict[str, Any], payload: Dict[str, Any], correlation_id: str):
        """Manejar bloqueo v1.0"""

        missing_info = payload.get("missing_info", "Informacion faltante")
        proposed_unblock = payload.get("proposed_unblock", "Sin propuesta")

        print(f"[BLOCK] PM: Bloqueo reportado [{correlation_id}]")
        print(f"   Informacion faltante: {missing_info}")
        print(f"   Propuesta de desbloqueo: {proposed_unblock}")

    async def _handle_v2_ack(self, v2_message: Dict[str, Any], payload: Dict[str, Any]):
        """Manejar ACK v2.0"""

        task_id = payload.get("task_id")
        task_name = payload.get("task_name", "Unknown")

        print(f"[OK] PM: ACK recibido para {task_id} - {task_name}")

        # Actualizar estado de tarea
        if self.current_project:
            for task in self.current_project.tasks:
                if task.id == task_id:
                    task.notes.append(f"ACK v2.0 recibido de {v2_message.get('from')}")
                    break

    async def _handle_v2_implementation_plan(self, v2_message: Dict[str, Any], payload: Dict[str, Any]):
        """Manejar implementation_plan v2.0 - enviar approval_response"""

        task_id = payload.get("task_id")
        task_name = payload.get("task_name", "Unknown")
        technology_stack = payload.get("technology_stack", [])
        implementation_approach = payload.get("implementation_approach", [])
        revised_estimate = payload.get("revised_estimate", 0)

        print(f"[CLIPBOARD] PM: Evaluando implementation_plan para {task_id}")
        print(f"   Stack: {', '.join(technology_stack)}")
        print(f"   Estimacion: {revised_estimate}h")
        print(f"   Pasos: {len(implementation_approach)}")

        # Evaluar plan automaticamente (criterios simples)
        approved = True
        feedback = "Plan aprobado"

        if revised_estimate > 8:
            feedback = "Plan aprobado con observacion: estimacion alta"
        if not technology_stack:
            approved = False
            feedback = "Plan rechazado: stack tecnologico no especificado"

        # Enviar approval_response v2.0
        approval_message = message_factory.create_approval_response(
            task_id=task_id,
            approved=approved,
            feedback=feedback,
            conditions=["Reportar progreso cada hora"] if revised_estimate > 6 else [],
            revised_priority=None
        )

        print(f"[SEND] PM: Enviando approval_response ({'[OK] APROBADO' if approved else '[ERROR] RECHAZADO'})")
        await self.send_v2_message(v2_message.get("from"), approval_message)

        # Actualizar tarea si se aprueba
        if approved and self.current_project:
            for task in self.current_project.tasks:
                if task.id == task_id:
                    task.estimated_hours = revised_estimate
                    task.status = TaskStatus.IN_PROGRESS
                    print(f"PM: [OK] Tarea {task.name} aprobada y en progreso")
                    break

    async def _handle_v2_implementation_started(self, v2_message: Dict[str, Any], payload: Dict[str, Any]):
        """Manejar implementation_started v2.0"""

        task_id = payload.get("task_id")
        task_name = payload.get("task_name", "Unknown")

        print(f"[START] PM: Implementacion iniciada - {task_id}: {task_name}")

        # Actualizar tarea
        if self.current_project:
            for task in self.current_project.tasks:
                if task.id == task_id:
                    task.status = TaskStatus.IN_PROGRESS
                    task.start_date = datetime.now()
                    task.notes.append(f"Iniciado por {v2_message.get('from')}")
                    break

    async def _handle_v2_implementation_progress(self, v2_message: Dict[str, Any], payload: Dict[str, Any]):
        """Manejar implementation_progress v2.0"""

        task_id = payload.get("task_id")
        progress = payload.get("progress_percentage", 0)
        current_step = payload.get("current_step", "")

        print(f"[CHART] PM: Progreso {task_id}: {progress:.1f}% - {current_step}")

    async def _handle_v2_implementation_completed(self, v2_message: Dict[str, Any], payload: Dict[str, Any]):
        """Manejar implementation_completed v2.0"""

        task_id = payload.get("task_id")
        task_name = payload.get("task_name", "Unknown")
        deliverables = payload.get("deliverables", {})

        print(f"[DONE] PM: Implementacion COMPLETADA - {task_id}: {task_name}")
        print(f"   Archivos: {deliverables.get('total_files', 0)}")

        # Actualizar tarea
        if self.current_project:
            for task in self.current_project.tasks:
                if task.id == task_id:
                    task.status = TaskStatus.COMPLETED
                    task.completion_date = datetime.now()
                    task.actual_hours = payload.get("actual_hours", task.estimated_hours)
                    task.notes.append(f"Completado por {v2_message.get('from')}")

                    print(f"PM: [OK] Tarea {task.name} marcada como COMPLETADA")

                    # Asignar tareas dependientes
                    await self._assign_next_dependent_tasks(task)
                    break

    async def handle_approval_request(self, message: AgentMessage):
        """Manejar solicitudes de aprobacion del Developer"""

        message_type = message.content.get("message_type", "")

        if message_type == "implementation_proposal":
            await self._handle_implementation_proposal(message)
        else:
            # Usar handler por defecto para otros tipos
            await super().handle_approval_request(message)

    async def _handle_implementation_proposal(self, message: AgentMessage):
        """Evaluar y aprobar/rechazar propuesta de implementacion del Developer"""

        task_id = message.content.get("task_id")
        task_name = message.content.get("task_name", "Unknown")
        technology_stack = message.content.get("technology_stack", [])
        revised_estimate = message.content.get("revised_estimate", 0)
        implementation_approach = message.content.get("implementation_approach", [])
        potential_challenges = message.content.get("potential_challenges", [])

        print(f"\n[CLIPBOARD] PM: Evaluando propuesta para tarea {task_id}")
        print(f"   [EDIT] Tarea: {task_name}")
        print(f"   [FAST] Stack: {', '.join(technology_stack)}")
        print(f"   [U23F1][UFE0F]  Estimacion: {revised_estimate}h")
        print(f"   [TARGET] Enfoque: {len(implementation_approach)} pasos")

        # Evaluar la propuesta automaticamente
        approval_decision = await self._evaluate_proposal(
            task_id, technology_stack, revised_estimate, implementation_approach, potential_challenges
        )

        # Crear respuesta de aprobacion/rechazo
        if VALIDATION_ENABLED:
            response_content = MessageValidator.create_safe_message(
                "proposal_response",
                task_id=task_id,
                approved=approval_decision["approved"],
                pm_feedback=approval_decision["feedback"],
                conditions=approval_decision.get("conditions", []),
                pm_message=f"{'[OK] Propuesta aprobada' if approval_decision['approved'] else '[ERROR] Propuesta rechazada'}: {approval_decision['feedback']}"
            )
        else:
            response_content = {
                "message_type": "proposal_response",
                "task_id": task_id,
                "approved": approval_decision["approved"],
                "pm_feedback": approval_decision["feedback"],
                "conditions": approval_decision.get("conditions", []),
                "pm_message": f"{'[OK] Propuesta aprobada' if approval_decision['approved'] else '[ERROR] Propuesta rechazada'}: {approval_decision['feedback']}"
            }

        await self.send_response(message, MessageType.APPROVAL, response_content)

        # Actualizar estado de la tarea si se aprueba
        if approval_decision["approved"]:
            await self._update_task_on_approval(task_id, revised_estimate)

    async def _evaluate_proposal(self, task_id: str, technology_stack: List[str],
                                revised_estimate: float, implementation_approach: List[str],
                                potential_challenges: List[str]) -> Dict[str, Any]:
        """Evaluar automaticamente una propuesta de implementacion"""

        # Criterios de evaluacion automatica
        approved = True
        feedback_points = []
        conditions = []

        # 1. Verificar estimacion de tiempo razonable
        if revised_estimate > 8:
            feedback_points.append("[WARN] Estimacion alta, considerar dividir la tarea")
            conditions.append("Reportar progreso cada 2 horas")
        elif revised_estimate < 1:
            feedback_points.append("[WARN] Estimacion muy baja, verificar completitud")

        # 2. Verificar stack tecnologico apropiado
        if not technology_stack:
            approved = False
            feedback_points.append("[ERROR] Stack tecnologico no especificado")
        elif len(technology_stack) > 5:
            feedback_points.append("[WARN] Muchas tecnologias, asegurar coherencia")

        # 3. Verificar enfoque de implementacion
        if len(implementation_approach) < 2:
            feedback_points.append("[WARN] Enfoque muy simplificado, agregar mas detalle")
        elif len(implementation_approach) > 8:
            feedback_points.append("[WARN] Enfoque muy complejo, considerar simplificar")

        # 4. Evaluar desafios identificados
        if len(potential_challenges) > 3:
            feedback_points.append("[WARN] Muchos desafios identificados, riesgo alto")
            conditions.append("Solicitar apoyo si se bloquea")

        # Generar feedback final
        if approved:
            if feedback_points:
                feedback = "Aprobado con observaciones: " + "; ".join(feedback_points)
            else:
                feedback = "Propuesta excelente, adelante con la implementacion"
        else:
            feedback = "Rechazado: " + "; ".join(feedback_points)

        return {
            "approved": approved,
            "feedback": feedback,
            "conditions": conditions
        }

    async def _update_task_on_approval(self, task_id: str, revised_estimate: float):
        """Actualizar tarea cuando la propuesta es aprobada"""

        if not self.current_project:
            return

        for task in self.current_project.tasks:
            if task.id == task_id:
                task.estimated_hours = revised_estimate
                task.status = TaskStatus.IN_PROGRESS
                task.start_date = datetime.now()
                print(f"PM: [OK] Tarea {task.name} aprobada y en progreso")
                break

    async def handle_status_update(self, message: AgentMessage):
        """Procesar actualizaciones de status del Developer y otros agentes"""

        message_type = message.content.get("message_type", "")

        if message_type == "implementation_completed":
            await self._handle_implementation_completed(message)
        elif message_type == "implementation_progress":
            await self._handle_implementation_progress(message)
        elif message_type == "task_completed":
            await self._handle_task_completed(message)
        elif message_type == "task_acknowledgment":
            await self._handle_task_acknowledgment(message)
        else:
            # Usar handler por defecto para otros tipos
            await super().handle_status_update(message)

    async def _handle_task_acknowledgment(self, message: AgentMessage):
        """Manejar confirmacion de recepcion de tarea"""

        task_id = message.content.get("task_id")
        task_name = message.content.get("task_name", "Unknown")

        print(f"PM: [MSG] ACK recibido para tarea {task_id} - {task_name}")

        # Actualizar estado de la tarea
        if self.current_project:
            for task in self.current_project.tasks:
                if task.id == task_id:
                    task.notes.append(f"ACK recibido de {message.sender}")
                    break

    async def _handle_implementation_completed(self, message: AgentMessage):
        """Manejar notificacion de implementacion completada"""

        if not self.current_project:
            return

        task_id = message.content.get("task_id")
        task_name = message.content.get("task_name", "Unknown")

        # Encontrar y actualizar la tarea
        for task in self.current_project.tasks:
            if task.id == task_id:
                task.status = TaskStatus.COMPLETED
                task.completion_date = datetime.now()
                task.actual_hours = message.content.get("actual_hours", task.estimated_hours)
                task.notes.append(f"Completado por {message.sender}")

                print(f"PM: [OK] Tarea completada - {task_name}")
                break

    async def _handle_implementation_progress(self, message: AgentMessage):
        """Manejar progreso de implementacion"""

        task_id = message.content.get("task_id")
        progress = message.content.get("progress_percentage", 0)
        current_step = message.content.get("current_step", "")

        print(f"PM: [CHART] Progreso tarea {task_id}: {progress:.1f}% - {current_step}")

    async def _handle_task_completed(self, message: AgentMessage):
        """Manejar finalizacion de tarea especifica"""

        if not self.current_project:
            return

        task_id = message.content.get("task_id")

        # Buscar y actualizar la tarea
        for task in self.current_project.tasks:
            if task.id == task_id:
                task.status = TaskStatus.COMPLETED
                task.completion_date = datetime.now()
                task.notes.append(f"Completado por {message.sender}")

                print(f"PM: [OK] Tarea {task.name} marcada como completada")

                # Asignar siguiente tarea si hay dependientes
                await self._assign_next_dependent_tasks(task)
                break

    async def _assign_next_dependent_tasks(self, completed_task: ProjectTask):
        """Asignar tareas que dependian de la tarea completada"""

        if not self.current_project:
            return

        # Buscar tareas que dependian de esta
        dependent_tasks = [
            task for task in self.current_project.tasks
            if completed_task.id in task.dependencies and task.status == TaskStatus.PENDING
        ]

        for task in dependent_tasks:
            # Verificar si todas las dependencias estan completadas
            all_deps_completed = all(
                any(t.id == dep_id and t.status == TaskStatus.COMPLETED
                    for t in self.current_project.tasks)
                for dep_id in task.dependencies
            )

            if all_deps_completed:
                # Asignar la tarea a un desarrollador disponible
                available_devs = [member for member in self.team_members if member != self.name]
                if available_devs:
                    await self._assign_task_to_developer(task, available_devs[0])

    def get_project_status(self) -> Dict[str, Any]:
        """Obtener status actual del proyecto"""

        if not self.current_project:
            return {"status": "No active project"}

        return {
            "objective": self.current_project.objective,
            "created_at": self.current_project.created_at.isoformat(),
            "team_size": len(self.team_members),
            "total_tasks": len(self.current_project.tasks),
            "completed_tasks": len([task for task in self.current_project.tasks
                                  if task.status == TaskStatus.COMPLETED]),
            "current_milestone": self._get_next_milestone()
        }