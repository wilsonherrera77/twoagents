#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# -*- coding: utf-8 -*-
# -*- coding: utf-8 -*-
"""
Contratos de Mensaje y Esquemas de Validación
Sistema de validación centralizado para comunicación entre agentes
"""


import os
import sys
if sys.platform == "win32":
    os.environ["PYTHONIOENCODING"] = "utf-8"

from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass
from enum import Enum
import json
from datetime import datetime


class MessageContract:
    """Contrato base para validación de mensajes"""

    @staticmethod
    def validate_message(message_type: str, content: Dict[str, Any]) -> bool:
        """Validar contenido del mensaje según su tipo"""
        validators = {
            "task_assignment": TaskAssignmentContract.validate,
            "implementation_started": ImplementationStartedContract.validate,
            "implementation_progress": ImplementationProgressContract.validate,
            "implementation_completed": ImplementationCompletedContract.validate,
            "task_completed": TaskCompletedContract.validate,
            "project_plan": ProjectPlanContract.validate,
            "progress_update": ProgressUpdateContract.validate,
            "unblock_request": UnblockRequestContract.validate,
            "overdue_followup": OverdueFollowupContract.validate
        }

        validator = validators.get(message_type)
        if validator:
            return validator(content)
        return True  # Permitir mensajes no definidos por ahora

    @staticmethod
    def get_required_fields(message_type: str) -> List[str]:
        """Obtener campos requeridos para un tipo de mensaje"""
        required_fields = {
            "task_assignment": ["task_id", "task_name", "description", "priority"],
            "implementation_started": ["task_id", "task_name", "technology_stack"],
            "implementation_progress": ["task_id", "progress_percentage", "current_step"],
            "implementation_completed": ["task_id", "task_name", "completion_time", "deliverables"],
            "task_completed": ["task_id", "task_name", "status"],
            "project_plan": ["objective", "total_tasks", "estimated_duration"],
            "progress_update": ["project_completion", "team_status"],
            "unblock_request": ["task_id", "question"],
            "overdue_followup": ["task_id", "days_overdue", "question"]
        }
        return required_fields.get(message_type, [])


class TaskAssignmentContract:
    """Contrato para asignación de tareas del PM al Developer"""

    @staticmethod
    def validate(content: Dict[str, Any]) -> bool:
        required = ["task_id", "task_name", "description", "priority"]
        optional = ["estimated_hours", "deliverables", "dependencies", "pm_instructions"]

        # Verificar campos requeridos
        for field in required:
            if field not in content:
                return False

        # Validar tipos
        if not isinstance(content.get("task_id"), str):
            return False
        if not isinstance(content.get("task_name"), str):
            return False
        if not isinstance(content.get("description"), str):
            return False
        if content.get("priority") not in ["low", "medium", "high", "critical"]:
            return False

        return True

    @staticmethod
    def create_message(task_id: str, task_name: str, description: str,
                      priority: str = "medium", **kwargs) -> Dict[str, Any]:
        """Crear mensaje de asignación de tarea validado"""
        message = {
            "message_type": "task_assignment",
            "task_id": task_id,
            "task_name": task_name,
            "description": description,
            "priority": priority,
            "estimated_hours": kwargs.get("estimated_hours", 2.0),
            "deliverables": kwargs.get("deliverables", []),
            "dependencies": kwargs.get("dependencies", []),
            "pm_instructions": kwargs.get("pm_instructions", "Por favor confirma si puedes tomar esta tarea.")
        }
        return message


class ImplementationStartedContract:
    """Contrato para notificación de inicio de implementación"""

    @staticmethod
    def validate(content: Dict[str, Any]) -> bool:
        required = ["task_id", "task_name", "technology_stack"]

        for field in required:
            if field not in content:
                return False

        if not isinstance(content.get("technology_stack"), list):
            return False

        return True

    @staticmethod
    def create_message(task_id: str, task_name: str, technology_stack: List[str],
                      **kwargs) -> Dict[str, Any]:
        """Crear mensaje de inicio de implementación validado"""
        return {
            "message_type": "implementation_started",
            "task_id": task_id,
            "task_name": task_name,
            "technology_stack": technology_stack,
            "estimated_completion": kwargs.get("estimated_completion"),
            "dev_message": kwargs.get("dev_message", f"Comenzando implementación de '{task_name}'.")
        }


class ImplementationProgressContract:
    """Contrato para actualizaciones de progreso de implementación"""

    @staticmethod
    def validate(content: Dict[str, Any]) -> bool:
        required = ["task_id", "progress_percentage", "current_step"]

        for field in required:
            if field not in content:
                return False

        progress = content.get("progress_percentage")
        if not isinstance(progress, (int, float)) or not (0 <= progress <= 100):
            return False

        return True

    @staticmethod
    def create_message(task_id: str, progress_percentage: float, current_step: str,
                      **kwargs) -> Dict[str, Any]:
        """Crear mensaje de progreso validado"""
        return {
            "message_type": "implementation_progress",
            "task_id": task_id,
            "task_name": kwargs.get("task_name", ""),
            "progress_percentage": progress_percentage,
            "current_step": current_step,
            "steps_completed": kwargs.get("steps_completed", 0),
            "total_steps": kwargs.get("total_steps", 0),
            "dev_message": kwargs.get("dev_message", f"Progreso: {progress_percentage:.1f}% - {current_step}")
        }


class ImplementationCompletedContract:
    """Contrato para notificación de implementación completada"""

    @staticmethod
    def validate(content: Dict[str, Any]) -> bool:
        required = ["task_id", "task_name", "completion_time", "deliverables"]

        for field in required:
            if field not in content:
                return False

        deliverables = content.get("deliverables")
        if not isinstance(deliverables, dict):
            return False

        return True

    @staticmethod
    def create_message(task_id: str, task_name: str, deliverables: Dict[str, Any],
                      **kwargs) -> Dict[str, Any]:
        """Crear mensaje de implementación completada validado"""
        return {
            "message_type": "implementation_completed",
            "task_id": task_id,
            "task_name": task_name,
            "completion_time": kwargs.get("completion_time", datetime.now().isoformat()),
            "actual_hours": kwargs.get("actual_hours", 0.0),
            "deliverables": deliverables,
            "status": kwargs.get("status", "completed"),
            "quality_metrics": kwargs.get("quality_metrics", {}),
            "dev_message": kwargs.get("dev_message", f"[OK] '{task_name}' completada exitosamente.")
        }


class TaskCompletedContract:
    """Contrato para notificación de tarea completada"""

    @staticmethod
    def validate(content: Dict[str, Any]) -> bool:
        required = ["task_id", "task_name", "status"]

        for field in required:
            if field not in content:
                return False

        if content.get("status") not in ["completed", "failed", "cancelled"]:
            return False

        return True

    @staticmethod
    def create_message(task_id: str, task_name: str, status: str = "completed",
                      **kwargs) -> Dict[str, Any]:
        """Crear mensaje de tarea completada validado"""
        return {
            "message_type": "task_completed",
            "task_id": task_id,
            "task_name": task_name,
            "implementation_id": kwargs.get("implementation_id"),
            "files_created": kwargs.get("files_created", []),
            "tests_created": kwargs.get("tests_created", []),
            "duration_hours": kwargs.get("duration_hours", 0.0),
            "status": status,
            "dev_message": kwargs.get("dev_message", f"Tarea '{task_name}' completada.")
        }


class ProjectPlanContract:
    """Contrato para comunicación de plan de proyecto"""

    @staticmethod
    def validate(content: Dict[str, Any]) -> bool:
        required = ["objective", "total_tasks", "estimated_duration"]

        for field in required:
            if field not in content:
                return False

        if not isinstance(content.get("total_tasks"), int) or content.get("total_tasks") < 0:
            return False

        return True

    @staticmethod
    def create_message(objective: str, total_tasks: int, estimated_duration: str,
                      **kwargs) -> Dict[str, Any]:
        """Crear mensaje de plan de proyecto validado"""
        return {
            "message_type": "project_plan",
            "objective": objective,
            "total_tasks": total_tasks,
            "estimated_duration": estimated_duration,
            "your_role": kwargs.get("your_role", "developer"),
            "milestones": kwargs.get("milestones", []),
            "success_criteria": kwargs.get("success_criteria", []),
            "pm_message": kwargs.get("pm_message", f"Hola, te comparto el plan del proyecto.")
        }


class ProgressUpdateContract:
    """Contrato para actualizaciones de progreso del proyecto"""

    @staticmethod
    def validate(content: Dict[str, Any]) -> bool:
        required = ["project_completion", "team_status"]

        for field in required:
            if field not in content:
                return False

        completion = content.get("project_completion")
        if not isinstance(completion, (int, float)) or not (0 <= completion <= 100):
            return False

        return True

    @staticmethod
    def create_message(project_completion: float, team_status: str, **kwargs) -> Dict[str, Any]:
        """Crear mensaje de actualización de progreso validado"""
        return {
            "message_type": "progress_update",
            "project_completion": project_completion,
            "your_tasks": kwargs.get("your_tasks", 0),
            "next_milestone": kwargs.get("next_milestone"),
            "team_status": team_status,
            "pm_message": kwargs.get("pm_message", f"Update del proyecto: {project_completion:.1f}% completado.")
        }


class UnblockRequestContract:
    """Contrato para solicitudes de desbloqueo"""

    @staticmethod
    def validate(content: Dict[str, Any]) -> bool:
        required = ["task_id", "question"]

        for field in required:
            if field not in content:
                return False

        return True

    @staticmethod
    def create_message(task_id: str, task_name: str, question: str, **kwargs) -> Dict[str, Any]:
        """Crear mensaje de solicitud de desbloqueo validado"""
        return {
            "message_type": "unblock_request",
            "task_id": task_id,
            "task_name": task_name,
            "question": question,
            "pm_support": kwargs.get("pm_support", "Estoy aquí para remover cualquier bloqueador.")
        }


class OverdueFollowupContract:
    """Contrato para seguimiento de tareas retrasadas"""

    @staticmethod
    def validate(content: Dict[str, Any]) -> bool:
        required = ["task_id", "days_overdue", "question"]

        for field in required:
            if field not in content:
                return False

        if not isinstance(content.get("days_overdue"), int) or content.get("days_overdue") < 0:
            return False

        return True

    @staticmethod
    def create_message(task_id: str, task_name: str, days_overdue: int,
                      question: str, **kwargs) -> Dict[str, Any]:
        """Crear mensaje de seguimiento de retraso validado"""
        return {
            "message_type": "overdue_followup",
            "task_id": task_id,
            "task_name": task_name,
            "days_overdue": days_overdue,
            "question": question,
            "pm_support": kwargs.get("pm_support", "¿Necesitas que reasigne parte del trabajo?")
        }


class MessageValidator:
    """Validador centralizado de mensajes"""

    @staticmethod
    def validate_and_log(message_type: str, content: Dict[str, Any],
                        sender: str = "unknown") -> bool:
        """Validar mensaje y loggear errores"""

        try:
            is_valid = MessageContract.validate_message(message_type, content)

            if not is_valid:
                required_fields = MessageContract.get_required_fields(message_type)
                missing_fields = [field for field in required_fields if field not in content]

                print(f"[ERROR] MENSAJE INVÁLIDO de {sender}:")
                print(f"   Tipo: {message_type}")
                print(f"   Campos faltantes: {missing_fields}")
                print(f"   Contenido: {content}")

            return is_valid

        except Exception as e:
            print(f"[ERROR] ERROR validando mensaje de {sender}: {e}")
            return False

    @staticmethod
    def create_safe_message(message_type: str, **kwargs) -> Dict[str, Any]:
        """Crear mensaje seguro usando los contratos"""

        creators = {
            "task_assignment": TaskAssignmentContract.create_message,
            "implementation_started": ImplementationStartedContract.create_message,
            "implementation_progress": ImplementationProgressContract.create_message,
            "implementation_completed": ImplementationCompletedContract.create_message,
            "task_completed": TaskCompletedContract.create_message,
            "project_plan": ProjectPlanContract.create_message,
            "progress_update": ProgressUpdateContract.create_message,
            "unblock_request": UnblockRequestContract.create_message,
            "overdue_followup": OverdueFollowupContract.create_message
        }

        creator = creators.get(message_type)
        if creator:
            return creator(**kwargs)
        else:
            # Mensaje genérico para tipos no definidos
            return {
                "message_type": message_type,
                **kwargs
            }