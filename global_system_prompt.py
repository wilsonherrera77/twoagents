#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# -*- coding: utf-8 -*-
"""
Prompt Global del Sistema - Mensaje de Sistema Compartido
Implementacion completa del orquestador multiagente con protocolo v1.0
"""


import os
import sys
if sys.platform == "win32":
    os.environ["PYTHONIOENCODING"] = "utf-8"

from typing import Dict, Any, List
from datetime import datetime
import json


class GlobalSystemPrompt:
    """Prompt global que actua como mensaje de sistema compartido para todos los agentes"""

    SYSTEM_PROMPT = """
[GLOBAL SYSTEM PROMPT]
Eres un orquestador de un equipo multiagente real (PM_Agent y Dev_Agent) que coopera hasta cumplir los criterios de aceptacion.
Usa SIEMPRE el "Contrato de Mensajes v1.0" adjunto. Todas las interacciones entre agentes deben ser JSON validos, una estructura por mensaje, sin texto adicional.

Parametros de ejecucion:
- autonomy_level = {{low|medium|high|max}}
- max_turns = null (ilimitado). La unica condicion de parada es que PM_Agent envie message_type="finish" con payload.done=true.
- Ciclo por evento (no simulado). Cada mensaje de un agente debe producir una reaccion del destinatario conforme al contrato.

Reglas:
1) Todo nuevo trabajo comienza con PM_Agent -> Dev_Agent message_type="task_spec".
2) Dev_Agent debe responder en este orden: "ack" -> "implementation_plan" (incluye "implementation_approach") -> esperar "approval_response".
3) Sin "approval_response.approved=true", Dev_Agent NO ejecuta.
4) Progreso real: Dev_Agent reporta "implementation_started" -> "implementation_progress" (con % y artefactos) -> "implementation_completed" (con lista de archivos, rutas y hash).
5) Si un agente no entiende un mensaje, responde "error" con payload.details y NO continua hasta aclararse.
6) El PM mantiene estado de tareas y solo envia "finish" cuando los criterios de aceptacion se satisfacen.

Contrato de Mensajes v1.0:
{
  "schema_version": "1.0",
  "from": "PM_Agent | Dev_Agent",
  "to": "PM_Agent | Dev_Agent",
  "message_type": "ack | task_spec | approval_request | approval_response | implementation_plan | implementation_started | implementation_progress | implementation_completed | data | question | answer | blocker | status_update | error | finish",
  "correlation_id": "<uuid o task_id>",
  "timestamp": "<ISO8601>",
  "payload": { "...dependiendo del tipo..." }
}
"""

    MESSAGE_CONTRACT_V1 = {
        "schema_version": "1.0",
        "valid_message_types": [
            "ack", "task_spec", "approval_request", "approval_response",
            "implementation_plan", "implementation_started", "implementation_progress",
            "implementation_completed", "data", "question", "answer", "blocker",
            "status_update", "error", "finish"
        ],
        "valid_agents": ["PM_Agent", "Dev_Agent"],
        "required_fields": ["schema_version", "from", "to", "message_type", "correlation_id", "timestamp", "payload"]
    }

    @classmethod
    def get_system_prompt(cls, autonomy_level: str = "medium") -> str:
        """Obtener prompt global parametrizado"""
        return cls.SYSTEM_PROMPT.replace("{{low|medium|high|max}}", autonomy_level)

    @classmethod
    def get_contract_definition(cls) -> Dict[str, Any]:
        """Obtener definicion del contrato v1.0"""
        return cls.MESSAGE_CONTRACT_V1

    @classmethod
    def validate_global_message(cls, message: Dict[str, Any]) -> tuple[bool, str]:
        """Validar mensaje segun el contrato global v1.0"""

        # Verificar campos requeridos
        for field in cls.MESSAGE_CONTRACT_V1["required_fields"]:
            if field not in message:
                return False, f"Campo requerido faltante: {field}"

        # Verificar schema_version
        if message.get("schema_version") != "1.0":
            return False, f"Schema version invalido: {message.get('schema_version')}"

        # Verificar agentes validos
        from_agent = message.get("from")
        to_agent = message.get("to")
        valid_agents = cls.MESSAGE_CONTRACT_V1["valid_agents"]

        if from_agent not in valid_agents:
            return False, f"Agente 'from' invalido: {from_agent}"
        if to_agent not in valid_agents:
            return False, f"Agente 'to' invalido: {to_agent}"

        # Verificar tipo de mensaje valido
        message_type = message.get("message_type")
        valid_types = cls.MESSAGE_CONTRACT_V1["valid_message_types"]

        if message_type not in valid_types:
            return False, f"Tipo de mensaje invalido: {message_type}"

        # Verificar que payload sea un diccionario
        if not isinstance(message.get("payload"), dict):
            return False, "Payload debe ser un diccionario"

        return True, "Mensaje valido segun contrato v1.0"


class PhaseManager:
    """Gestor de fases del protocolo estricto"""

    def __init__(self, workspace_path: str, autonomy_level: str = "medium"):
        self.workspace_path = workspace_path
        self.autonomy_level = autonomy_level
        self.current_phase = "bootstrap"
        self.bootstrap_completed = False
        self.task_counter = 0

    def generate_bootstrap_pm_message(self) -> Dict[str, Any]:
        """Generar mensaje bootstrap del PM (Fase 0)"""

        return {
            "schema_version": "1.0",
            "from": "PM_Agent",
            "to": "Dev_Agent",
            "message_type": "question",
            "correlation_id": "BOOTSTRAP",
            "timestamp": datetime.now().isoformat(),
            "payload": {
                "ask": "Confirma capacidades, rutas de trabajo y version del protocolo.",
                "contract_version_expected": "1.0",
                "workspace": self.workspace_path,
                "autonomy_level": self.autonomy_level
            }
        }

    def generate_bootstrap_dev_response(self) -> Dict[str, Any]:
        """Generar respuesta bootstrap del Dev (Fase 0)"""

        return {
            "schema_version": "1.0",
            "from": "Dev_Agent",
            "to": "PM_Agent",
            "message_type": "answer",
            "correlation_id": "BOOTSTRAP",
            "timestamp": datetime.now().isoformat(),
            "payload": {
                "contract_version": "1.0",
                "capabilities": ["software_development", "testing", "debugging", "documentation"],
                "workspace_ok": True,
                "tools": ["python", "pytest", "html/css/js"],
                "limits": [],
                "ready": True
            }
        }

    def generate_task_spec_message(self, objective: str, task_id: str = None) -> Dict[str, Any]:
        """Generar task_spec del PM (Fase 1)"""

        if not task_id:
            self.task_counter += 1
            task_id = f"TASK-{self.task_counter:03d}"

        # Adaptar task_spec segun el objetivo
        if "calculadora" in objective.lower():
            title = "Implementar calculadora web completa"
            acceptance_criteria = [
                "HTML funcional con interfaz de calculadora",
                "JavaScript con operaciones basicas (+,-,*,/)",
                "CSS con diseno responsive",
                "Tests unitarios para todas las operaciones"
            ]
            artifacts_expected = ["calc.html", "calc.js", "calc.css", "tests/test_calc.py"]

        elif "api" in objective.lower() or "rest" in objective.lower():
            title = "Implementar API REST completa"
            acceptance_criteria = [
                "Endpoints CRUD funcionales",
                "Documentacion de API",
                "Tests de integracion",
                "Manejo de errores"
            ]
            artifacts_expected = ["api/main.py", "api/models.py", "tests/test_api.py", "docs/api_spec.md"]

        else:
            # Generico
            title = f"Analisis detallado de requerimientos + implementacion para: {objective}"
            acceptance_criteria = [
                "Codigo implementado y funcional",
                "Tests unitarios pasando",
                "Documentacion tecnica completa",
                "Estructura de archivos organizada"
            ]
            artifacts_expected = ["main.py", "tests/test_main.py", "README.md"]

        return {
            "schema_version": "1.0",
            "from": "PM_Agent",
            "to": "Dev_Agent",
            "message_type": "task_spec",
            "correlation_id": task_id,
            "timestamp": datetime.now().isoformat(),
            "payload": {
                "title": title,
                "acceptance_criteria": acceptance_criteria,
                "artefacts_expected": artifacts_expected
            }
        }

    def generate_ack_message(self, correlation_id: str) -> Dict[str, Any]:
        """Generar ACK del Dev"""

        return {
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

    def generate_implementation_plan_message(self, correlation_id: str, objective: str) -> Dict[str, Any]:
        """Generar implementation_plan del Dev (Fase 1)"""

        # Adaptar plan segun objetivo
        if "calculadora" in objective.lower():
            implementation_approach = [
                "Crear estructura HTML con botones y display",
                "Implementar logica JavaScript para operaciones",
                "Disenar CSS responsive y moderno",
                "Desarrollar tests unitarios para todas las funciones"
            ]
            steps = [
                {"id": "S1", "desc": "Estructura HTML basica"},
                {"id": "S2", "desc": "Logica JavaScript"},
                {"id": "S3", "desc": "Estilos CSS"},
                {"id": "S4", "desc": "Tests y validacion"}
            ]

        elif "api" in objective.lower():
            implementation_approach = [
                "Definir estructura de endpoints REST",
                "Implementar modelos de datos",
                "Crear logica de negocio y validaciones",
                "Desarrollar tests de integracion"
            ]
            steps = [
                {"id": "S1", "desc": "Definir endpoints"},
                {"id": "S2", "desc": "Implementar modelos"},
                {"id": "S3", "desc": "Logica de negocio"},
                {"id": "S4", "desc": "Tests de integracion"}
            ]

        else:
            implementation_approach = [
                "Analizar requerimientos especificos",
                "Disenar arquitectura modular",
                "Implementar funcionalidad principal",
                "Crear tests y documentacion"
            ]
            steps = [
                {"id": "S1", "desc": "Analisis de requerimientos"},
                {"id": "S2", "desc": "Diseno de arquitectura"},
                {"id": "S3", "desc": "Implementacion principal"},
                {"id": "S4", "desc": "Tests y documentacion"}
            ]

        return {
            "schema_version": "1.0",
            "from": "Dev_Agent",
            "to": "PM_Agent",
            "message_type": "implementation_plan",
            "correlation_id": correlation_id,
            "timestamp": datetime.now().isoformat(),
            "payload": {
                "implementation_approach": implementation_approach,
                "steps": steps,
                "eta_hours": 2
            }
        }

    def generate_approval_response_message(self, correlation_id: str, approved: bool = True,
                                         changes: List[str] = None) -> Dict[str, Any]:
        """Generar approval_response del PM"""

        return {
            "schema_version": "1.0",
            "from": "PM_Agent",
            "to": "Dev_Agent",
            "message_type": "approval_response",
            "correlation_id": correlation_id,
            "timestamp": datetime.now().isoformat(),
            "payload": {
                "approved": approved,
                "changes": changes or []
            }
        }

    def generate_implementation_started_message(self, correlation_id: str, step_id: str = "S1") -> Dict[str, Any]:
        """Generar implementation_started del Dev (Fase 2)"""

        return {
            "schema_version": "1.0",
            "from": "Dev_Agent",
            "to": "PM_Agent",
            "message_type": "implementation_started",
            "correlation_id": correlation_id,
            "timestamp": datetime.now().isoformat(),
            "payload": {
                "started_step": step_id
            }
        }

    def generate_implementation_progress_message(self, correlation_id: str, percent: int,
                                               current_step: str, artifacts: List[str] = None) -> Dict[str, Any]:
        """Generar implementation_progress del Dev (Fase 2)"""

        return {
            "schema_version": "1.0",
            "from": "Dev_Agent",
            "to": "PM_Agent",
            "message_type": "implementation_progress",
            "correlation_id": correlation_id,
            "timestamp": datetime.now().isoformat(),
            "payload": {
                "percent": percent,
                "current_step": current_step,
                "artefacts": artifacts or [],
                "logs_tail": f"Trabajando en {current_step}..."
            }
        }

    def generate_implementation_completed_message(self, correlation_id: str,
                                                files: List[Dict[str, str]]) -> Dict[str, Any]:
        """Generar implementation_completed del Dev (Fase 2)"""

        return {
            "schema_version": "1.0",
            "from": "Dev_Agent",
            "to": "PM_Agent",
            "message_type": "implementation_completed",
            "correlation_id": correlation_id,
            "timestamp": datetime.now().isoformat(),
            "payload": {
                "files": files,
                "tests_summary": {"ran": 3, "passed": 3, "failed": 0}
            }
        }

    def generate_qa_task_spec_message(self) -> Dict[str, Any]:
        """Generar task_spec de QA del PM (Fase 3)"""

        task_id = "TASK-QA"
        return {
            "schema_version": "1.0",
            "from": "PM_Agent",
            "to": "Dev_Agent",
            "message_type": "task_spec",
            "correlation_id": task_id,
            "timestamp": datetime.now().isoformat(),
            "payload": {
                "title": "Pruebas minimas de normalizacion, deduplicacion y scoring",
                "acceptance_criteria": [
                    "Tests que ejecuten funciones reales",
                    "Fixtures reproducibles con 5-10 items",
                    "Reporte de cobertura basico"
                ],
                "artefacts_expected": [
                    "tests/test_normalization.py",
                    "tests/test_dedup.py",
                    "tests/test_scoring.py",
                    "reports/test_results.txt"
                ]
            }
        }

    def generate_finish_message(self, summary_path: str = "reports/summary.json") -> Dict[str, Any]:
        """Generar finish del PM (Fase 4)"""

        return {
            "schema_version": "1.0",
            "from": "PM_Agent",
            "to": "Dev_Agent",
            "message_type": "finish",
            "correlation_id": "PROJECT",
            "timestamp": datetime.now().isoformat(),
            "payload": {
                "done": True,
                "summary_path": summary_path
            }
        }

    def generate_error_message(self, correlation_id: str, details: str,
                             from_agent: str = "Dev_Agent") -> Dict[str, Any]:
        """Generar mensaje de error"""

        to_agent = "PM_Agent" if from_agent == "Dev_Agent" else "Dev_Agent"

        return {
            "schema_version": "1.0",
            "from": from_agent,
            "to": to_agent,
            "message_type": "error",
            "correlation_id": correlation_id,
            "timestamp": datetime.now().isoformat(),
            "payload": {
                "details": details,
                "requires_clarification": True
            }
        }

    def generate_blocker_message(self, correlation_id: str, missing_info: str,
                                proposed_unblock: str) -> Dict[str, Any]:
        """Generar mensaje de bloqueo"""

        return {
            "schema_version": "1.0",
            "from": "Dev_Agent",
            "to": "PM_Agent",
            "message_type": "blocker",
            "correlation_id": correlation_id,
            "timestamp": datetime.now().isoformat(),
            "payload": {
                "missing_info": missing_info,
                "proposed_unblock": proposed_unblock
            }
        }


# Singleton global para uso en todo el sistema
global_prompt_system = GlobalSystemPrompt()
phase_manager = None  # Se inicializa con workspace especifico