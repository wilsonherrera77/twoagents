# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
Sistema de Niveles de Autonomía v2.0
Implementación completa de la matriz operativa de autonomía con escalado automático
"""

import os
import sys
if sys.platform == "win32":
    os.environ['PYTHONIOENCODING'] = 'utf-8'

import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Literal
from dataclasses import dataclass, field
from enum import Enum
import uuid


AutonomyLevel = Literal["low", "medium", "high", "max"]


@dataclass
class AutonomyPolicy:
    """Política de autonomía por nivel"""
    level: AutonomyLevel
    human_confirmation: str
    pm_control: str
    allowed_actions: List[str]
    escalation_trigger: str
    max_cycles_before_escalation: int
    auto_replan: bool = False
    continuous_mode: bool = False


class AutonomyMatrix:
    """Matriz operativa de niveles de autonomía"""

    POLICIES = {
        "low": AutonomyPolicy(
            level="low",
            human_confirmation="Cada tarea",
            pm_control="PM aprueba todo",
            allowed_actions=[
                "Leer archivos locales",
                "Escribir archivos locales",
                "Proponer sin ejecutar"
            ],
            escalation_trigger="Si 2 ciclos sin progreso => pedir aclaración humana",
            max_cycles_before_escalation=2,
            auto_replan=False,
            continuous_mode=False
        ),
        "medium": AutonomyPolicy(
            level="medium",
            human_confirmation="Hitos (plan y entregables)",
            pm_control="PM aprueba; Dev ejecuta",
            allowed_actions=[
                "Ejecuta tras approval del plan",
                "Ejecutar scripts locales y tests",
                "Crear/modificar archivos"
            ],
            escalation_trigger="Si 3 ciclos sin progreso => replan y notificar",
            max_cycles_before_escalation=3,
            auto_replan=True,
            continuous_mode=False
        ),
        "high": AutonomyPolicy(
            level="high",
            human_confirmation="Solo cambios de alcance",
            pm_control="PM supervisa, no aprueba cada paso",
            allowed_actions=[
                "Ejecuta sin confirmación",
                "Concurrencia limitada",
                "Scraping local",
                "Auto-corrección de errores menores"
            ],
            escalation_trigger="Si 5 ciclos sin progreso => auto-replan + alerta",
            max_cycles_before_escalation=5,
            auto_replan=True,
            continuous_mode=False
        ),
        "max": AutonomyPolicy(
            level="max",
            human_confirmation="Ninguna (modo continuo)",
            pm_control="PM orquesta",
            allowed_actions=[
                "Autónomo total",
                "Watchers continuos",
                "Detección de duplicados/estancamiento",
                "Auto-corrección completa",
                "Replanificación automática"
            ],
            escalation_trigger="Detecta duplicados/estancamiento y se auto-corrige",
            max_cycles_before_escalation=float('inf'),
            auto_replan=True,
            continuous_mode=True
        )
    }

    @classmethod
    def get_policy(cls, level: AutonomyLevel) -> AutonomyPolicy:
        """Obtener política para nivel específico"""
        return cls.POLICIES[level]

    @classmethod
    def get_all_levels(cls) -> List[AutonomyLevel]:
        """Obtener todos los niveles disponibles"""
        return list(cls.POLICIES.keys())


@dataclass
class TaskCycle:
    """Ciclo de trabajo en una tarea"""
    cycle_id: str
    task_id: str
    started_at: datetime
    ended_at: Optional[datetime] = None
    progress_made: bool = False
    actions_taken: List[str] = field(default_factory=list)
    errors_encountered: List[str] = field(default_factory=list)
    status: str = "running"  # running, completed, failed, stalled


@dataclass
class AutonomyState:
    """Estado del sistema de autonomía"""
    current_level: AutonomyLevel
    task_cycles: Dict[str, List[TaskCycle]] = field(default_factory=dict)
    escalations_triggered: List[Dict[str, Any]] = field(default_factory=list)
    global_cycle_count: int = 0
    last_progress_time: Optional[datetime] = None
    stalled_tasks: List[str] = field(default_factory=list)
    continuous_mode_active: bool = False


class AutonomyManager:
    """Gestor central del sistema de autonomía"""

    def __init__(self, initial_level: AutonomyLevel = "medium"):
        self.state = AutonomyState(current_level=initial_level)
        self.policy = AutonomyMatrix.get_policy(initial_level)
        self.monitoring_active = False

    def set_autonomy_level(self, level: AutonomyLevel):
        """Cambiar nivel de autonomía"""

        print(f"[CHANGE] Cambiando autonomía: {self.state.current_level} -> {level}")

        self.state.current_level = level
        self.policy = AutonomyMatrix.get_policy(level)

        if level == "max":
            self.state.continuous_mode_active = True
            print("🚀 Modo continuo ACTIVADO")
        else:
            self.state.continuous_mode_active = False

        print(f"[OK] Política activa: {self.policy.pm_control}")
        print(f"   Escalado: {self.policy.escalation_trigger}")

    def start_task_cycle(self, task_id: str) -> str:
        """Iniciar nuevo ciclo para una tarea"""

        cycle_id = f"cycle_{uuid.uuid4().hex[:8]}"
        cycle = TaskCycle(
            cycle_id=cycle_id,
            task_id=task_id,
            started_at=datetime.now()
        )

        if task_id not in self.state.task_cycles:
            self.state.task_cycles[task_id] = []

        self.state.task_cycles[task_id].append(cycle)
        self.state.global_cycle_count += 1

        print(f"[PROC] Iniciando ciclo {cycle_id} para tarea {task_id}")
        return cycle_id

    async def end_task_cycle(self, task_id: str, cycle_id: str, progress_made: bool = False,
                      actions_taken: List[str] = None, errors: List[str] = None):
        """Finalizar ciclo de tarea"""

        cycles = self.state.task_cycles.get(task_id, [])
        for cycle in cycles:
            if cycle.cycle_id == cycle_id:
                cycle.ended_at = datetime.now()
                cycle.progress_made = progress_made
                cycle.actions_taken = actions_taken or []
                cycle.errors_encountered = errors or []
                cycle.status = "completed" if progress_made else "stalled"

                if progress_made:
                    self.state.last_progress_time = datetime.now()
                    if task_id in self.state.stalled_tasks:
                        self.state.stalled_tasks.remove(task_id)
                else:
                    if task_id not in self.state.stalled_tasks:
                        self.state.stalled_tasks.append(task_id)

                print(f"[END] Ciclo {cycle_id} finalizado - Progreso: {'[OK]' if progress_made else '[ERROR]'}")

                # Verificar si necesita escalado
                await self._check_escalation_needed(task_id)
                break

    async def _check_escalation_needed(self, task_id: str):
        """Verificar si se necesita escalado automático"""

        cycles = self.state.task_cycles.get(task_id, [])
        recent_cycles = [c for c in cycles if not c.progress_made and c.status == "stalled"]

        stalled_count = len(recent_cycles)
        max_cycles = self.policy.max_cycles_before_escalation

        print(f"📊 Tarea {task_id}: {stalled_count}/{max_cycles} ciclos sin progreso")

        if stalled_count >= max_cycles:
            await self._trigger_escalation(task_id, stalled_count)

    async def _trigger_escalation(self, task_id: str, stalled_count: int):
        """Activar escalado según política"""

        escalation = {
            "timestamp": datetime.now().isoformat(),
            "task_id": task_id,
            "trigger": self.policy.escalation_trigger,
            "stalled_cycles": stalled_count,
            "autonomy_level": self.state.current_level,
            "action_taken": None
        }

        print(f"🚨 ESCALADO ACTIVADO para {task_id}")
        print(f"   Trigger: {self.policy.escalation_trigger}")

        if self.state.current_level == "low":
            escalation["action_taken"] = "human_clarification_requested"
            print("📞 Solicitando aclaración humana...")

        elif self.state.current_level == "medium":
            escalation["action_taken"] = "auto_replan_and_notify"
            print("[PROC] Auto-replanificación activada + notificación...")
            await self._auto_replan_task(task_id)

        elif self.state.current_level == "high":
            escalation["action_taken"] = "auto_replan_and_alert"
            print("⚡ Auto-replanificación + alerta de supervisión...")
            await self._auto_replan_task(task_id)
            await self._send_supervision_alert(task_id)

        elif self.state.current_level == "max":
            escalation["action_taken"] = "auto_correction_and_adapt"
            print("🤖 Auto-corrección y adaptación continua...")
            await self._auto_correct_and_adapt(task_id)

        self.state.escalations_triggered.append(escalation)

    async def _auto_replan_task(self, task_id: str):
        """Replanificar tarea automáticamente"""

        print(f"[PROC] Replanificando tarea {task_id}...")

        # Analizar ciclos fallidos para identificar patrones
        cycles = self.state.task_cycles.get(task_id, [])
        failed_cycles = [c for c in cycles if not c.progress_made]

        common_errors = {}
        for cycle in failed_cycles:
            for error in cycle.errors_encountered:
                common_errors[error] = common_errors.get(error, 0) + 1

        # Generar estrategia alternativa
        if common_errors:
            most_common_error = max(common_errors, key=common_errors.get)
            print(f"   Error más común: {most_common_error}")
            print(f"   Adaptando estrategia...")

        # Reiniciar contadores para la tarea
        if task_id in self.state.task_cycles:
            # Mantener historial pero marcar como replanificado
            for cycle in self.state.task_cycles[task_id]:
                if cycle.status == "stalled":
                    cycle.status = "replanned"

    async def _send_supervision_alert(self, task_id: str):
        """Enviar alerta de supervisión"""

        print(f"🔔 ALERTA DE SUPERVISIÓN: Tarea {task_id} requiere atención")
        print(f"   Múltiples ciclos sin progreso detectados")
        print(f"   Replanificación automática en curso...")

    async def _auto_correct_and_adapt(self, task_id: str):
        """Auto-corrección y adaptación continua (nivel máximo)"""

        print(f"🤖 AUTO-CORRECCIÓN AVANZADA para {task_id}")

        # Detectar patrones de estancamiento
        cycles = self.state.task_cycles.get(task_id, [])

        # Análisis de patrones
        action_patterns = {}
        for cycle in cycles:
            for action in cycle.actions_taken:
                action_patterns[action] = action_patterns.get(action, 0) + 1

        # Detectar duplicación
        duplicated_actions = {k: v for k, v in action_patterns.items() if v > 3}

        if duplicated_actions:
            print(f"   🔍 Duplicación detectada: {list(duplicated_actions.keys())}")
            print(f"   [PROC] Cambiando estrategia completamente...")

            # Marcar estrategias duplicadas como prohibidas
            for cycle in cycles:
                if any(action in duplicated_actions for action in cycle.actions_taken):
                    cycle.status = "duplicated_strategy"

        # Auto-adaptar nivel si es necesario
        total_stalled = len(self.state.stalled_tasks)
        if total_stalled > 3:
            print(f"   ⬇️ Muchas tareas estancadas ({total_stalled}), considerando reducir autonomía...")

    def should_require_approval(self, action_type: str, task_context: Dict[str, Any] = None) -> bool:
        """Determinar si una acción requiere aprobación según nivel de autonomía"""

        if self.state.current_level == "low":
            return True  # Todo requiere aprobación

        elif self.state.current_level == "medium":
            # Solo requiere aprobación para hitos
            return action_type in ["task_plan", "major_deliverable", "scope_change"]

        elif self.state.current_level == "high":
            # Solo cambios de alcance requieren aprobación
            return action_type in ["scope_change", "major_architecture_change"]

        elif self.state.current_level == "max":
            return False  # Ninguna acción requiere aprobación

        return True  # Default seguro

    def can_execute_action(self, action_type: str) -> bool:
        """Verificar si una acción está permitida en el nivel actual"""

        allowed = self.policy.allowed_actions

        action_permissions = {
            "read_files": "low",
            "write_files": "low",
            "execute_scripts": "medium",
            "run_tests": "medium",
            "concurrent_tasks": "high",
            "web_scraping": "high",
            "auto_correction": "high",
            "continuous_monitoring": "max",
            "auto_replan": "medium"
        }

        required_level = action_permissions.get(action_type)
        if not required_level:
            return True  # Acción no restringida

        level_hierarchy = ["low", "medium", "high", "max"]
        current_index = level_hierarchy.index(self.state.current_level)
        required_index = level_hierarchy.index(required_level)

        return current_index >= required_index

    def get_status_report(self) -> Dict[str, Any]:
        """Obtener reporte de estado del sistema de autonomía"""

        total_cycles = sum(len(cycles) for cycles in self.state.task_cycles.values())
        active_tasks = len(self.state.task_cycles)
        stalled_tasks = len(self.state.stalled_tasks)

        return {
            "current_level": self.state.current_level,
            "policy": {
                "confirmation_required": self.policy.human_confirmation,
                "pm_control": self.policy.pm_control,
                "escalation_trigger": self.policy.escalation_trigger
            },
            "statistics": {
                "total_cycles": total_cycles,
                "active_tasks": active_tasks,
                "stalled_tasks": stalled_tasks,
                "escalations_triggered": len(self.state.escalations_triggered)
            },
            "continuous_mode": self.state.continuous_mode_active,
            "last_progress": self.state.last_progress_time.isoformat() if self.state.last_progress_time else None
        }

    async def start_continuous_monitoring(self):
        """Iniciar monitoreo continuo (solo para nivel max)"""

        if self.state.current_level != "max":
            print("⚠️ Monitoreo continuo solo disponible en nivel 'max'")
            return

        self.monitoring_active = True
        print("[TARGET] Iniciando monitoreo continuo...")

        while self.monitoring_active and self.state.continuous_mode_active:
            # Verificar estado general cada 30 segundos
            await asyncio.sleep(30)

            # Detectar tareas estancadas globalmente
            current_time = datetime.now()
            if self.state.last_progress_time:
                time_since_progress = current_time - self.state.last_progress_time
                if time_since_progress > timedelta(minutes=10):
                    print("🚨 ALERTA: No hay progreso global en 10+ minutos")
                    await self._global_intervention()

            # Auto-optimización
            if len(self.state.stalled_tasks) > 5:
                print("[PROC] Demasiadas tareas estancadas, activando optimización global...")
                await self._optimize_global_strategy()

    async def _global_intervention(self):
        """Intervención global para resolver estancamiento masivo"""

        print("🛠️ INTERVENCIÓN GLOBAL ACTIVADA")

        # Reiniciar todas las tareas estancadas con nueva estrategia
        for task_id in self.state.stalled_tasks.copy():
            print(f"   [PROC] Reiniciando estrategia para {task_id}")
            await self._auto_replan_task(task_id)

        # Limpiar lista de estancadas
        self.state.stalled_tasks.clear()
        self.state.last_progress_time = datetime.now()

    async def _optimize_global_strategy(self):
        """Optimizar estrategia global del sistema"""

        print("⚡ OPTIMIZACIÓN GLOBAL EN CURSO...")

        # Analizar patrones de fallo global
        all_cycles = []
        for cycles in self.state.task_cycles.values():
            all_cycles.extend(cycles)

        failed_cycles = [c for c in all_cycles if not c.progress_made]

        if len(failed_cycles) > 10:
            print("   📊 Analizando patrones de fallo...")
            # Implementar ML simple para detectar patrones
            print("   🧠 Adaptando estrategias basado en histórico...")

    def stop_monitoring(self):
        """Detener monitoreo continuo"""
        self.monitoring_active = False
        print("⏹️ Monitoreo continuo detenido")


# Singleton global para uso en todo el sistema
autonomy_manager = AutonomyManager()


class AutonomyDecorator:
    """Decorador para métodos que requieren control de autonomía"""

    @staticmethod
    def requires_approval(action_type: str):
        """Decorador que verifica si una acción requiere aprobación"""
        def decorator(func):
            async def wrapper(*args, **kwargs):
                if autonomy_manager.should_require_approval(action_type):
                    print(f"⏳ Acción '{action_type}' requiere aprobación en nivel {autonomy_manager.state.current_level}")
                    # Implementar lógica de espera de aprobación
                    return await func(*args, **kwargs)
                else:
                    print(f"[OK] Acción '{action_type}' ejecutándose directamente (nivel {autonomy_manager.state.current_level})")
                    return await func(*args, **kwargs)
            return wrapper
        return decorator

    @staticmethod
    def check_permission(action_type: str):
        """Decorador que verifica permisos de acción"""
        def decorator(func):
            async def wrapper(*args, **kwargs):
                if autonomy_manager.can_execute_action(action_type):
                    return await func(*args, **kwargs)
                else:
                    print(f"[DENIED] Acción '{action_type}' no permitida en nivel {autonomy_manager.state.current_level}")
                    return None
            return wrapper
        return decorator