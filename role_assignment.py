#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# -*- coding: utf-8 -*-
"""
Sistema de Asignación Dinámica de Roles
Permite que los agentes negocien automáticamente quién será PM y quién Dev
"""


import os
import sys
if sys.platform == "win32":
    os.environ["PYTHONIOENCODING"] = "utf-8"

import asyncio
from typing import Dict, Any, List, Optional, Tuple
from enum import Enum
from dataclasses import dataclass
from agent_communication import BaseConversationalAgent, MessageBroker, MessageType, AgentMessage


class RoleType(Enum):
    PROJECT_MANAGER = "project_manager"
    DEVELOPER = "developer"
    ANALYST = "analyst"
    RESEARCHER = "researcher"
    UNASSIGNED = "unassigned"


@dataclass
class AgentCapability:
    """Capacidades declaradas de un agente"""
    agent_name: str
    preferred_roles: List[RoleType]
    experience_level: int  # 1-10
    specializations: List[str]
    availability: float  # 0-1
    self_assessment: Dict[str, int]  # skill -> rating


@dataclass
class RoleAssignment:
    """Resultado de asignación de roles"""
    agent_name: str
    assigned_role: RoleType
    confidence: float  # 0-1
    reasoning: str
    backup_roles: List[RoleType]


class RoleNegotiationSystem:
    """Sistema que maneja la negociación automática de roles"""

    def __init__(self, broker: MessageBroker):
        self.broker = broker
        self.agent_capabilities: Dict[str, AgentCapability] = {}
        self.negotiation_history: List[Dict[str, Any]] = []

    async def register_agent_capabilities(self, agent_name: str, capabilities: AgentCapability):
        """Registrar capacidades de un agente"""
        self.agent_capabilities[agent_name] = capabilities
        print(f"Capacidades registradas para {agent_name}")

    async def negotiate_roles_for_objective(
        self,
        objective: str,
        available_agents: List[str],
        user_specified_roles: Optional[Dict[str, RoleType]] = None
    ) -> Dict[str, RoleAssignment]:
        """
        Negociar roles automáticamente basado en el objetivo
        """
        print(f"\nIniciando negociacion de roles para: '{objective}'")
        print(f"Agentes disponibles: {available_agents}")

        # Si el usuario especificó roles, usar esos
        if user_specified_roles:
            print("Usuario especifico roles:")
            for agent, role in user_specified_roles.items():
                print(f"  {agent} -> {role.value}")
            return self._create_assignments_from_user_specification(user_specified_roles)

        # Analizar el objetivo para determinar roles necesarios
        required_roles = self._analyze_objective_for_roles(objective)
        print(f"Roles necesarios identificados: {[r.value for r in required_roles]}")

        # Recopilar auto-evaluaciones de los agentes
        agent_evaluations = await self._collect_agent_evaluations(available_agents, objective, required_roles)

        # Negociar asignaciones
        role_assignments = await self._negotiate_assignments(
            objective, required_roles, agent_evaluations
        )

        # Documentar la negociación
        self.negotiation_history.append({
            "objective": objective,
            "agents": available_agents,
            "required_roles": [r.value for r in required_roles],
            "assignments": {name: assignment.assigned_role.value for name, assignment in role_assignments.items()},
            "reasoning": {name: assignment.reasoning for name, assignment in role_assignments.items()}
        })

        return role_assignments

    def _analyze_objective_for_roles(self, objective: str) -> List[RoleType]:
        """Analizar objetivo para determinar qué roles se necesitan"""
        objective_lower = objective.lower()

        required_roles = []

        # Siempre necesitamos PM para coordinación
        required_roles.append(RoleType.PROJECT_MANAGER)

        # Determinar roles adicionales basado en palabras clave
        if any(word in objective_lower for word in ["implementar", "desarrollar", "crear", "construir", "programar", "codificar"]):
            required_roles.append(RoleType.DEVELOPER)

        if any(word in objective_lower for word in ["analizar", "analisis", "estudiar", "evaluar", "examinar"]):
            required_roles.append(RoleType.ANALYST)

        if any(word in objective_lower for word in ["investigar", "investigacion", "buscar", "explorar", "descubrir"]):
            required_roles.append(RoleType.RESEARCHER)

        # Si solo tenemos PM, agregar Developer como rol general
        if len(required_roles) == 1:
            required_roles.append(RoleType.DEVELOPER)

        return required_roles

    async def _collect_agent_evaluations(
        self,
        agents: List[str],
        objective: str,
        required_roles: List[RoleType]
    ) -> Dict[str, Dict[str, Any]]:
        """Recopilar auto-evaluaciones de cada agente para los roles requeridos"""

        evaluations = {}

        for agent in agents:
            if agent not in self.broker.agents:
                continue

            print(f"\nSolicitando evaluacion a {agent}...")

            # Solicitar auto-evaluación
            response = await self.broker.agents[agent].send_message(
                receiver=agent,  # Auto-evaluación
                message_type=MessageType.QUESTION,
                content={
                    "question": "role_self_evaluation",
                    "objective": objective,
                    "required_roles": [r.value for r in required_roles],
                    "context": "Sistema de asignacion automatica de roles"
                },
                requires_approval=True
            )

            if response and response.message_type == MessageType.ANSWER:
                evaluations[agent] = response.content
                print(f"  Evaluacion recibida de {agent}")
            else:
                # Evaluación por defecto si no responde
                evaluations[agent] = self._default_evaluation(agent, required_roles)
                print(f"  Usando evaluacion por defecto para {agent}")

        return evaluations

    def _default_evaluation(self, agent_name: str, required_roles: List[RoleType]) -> Dict[str, Any]:
        """Evaluación por defecto cuando un agente no responde"""

        # Evaluación básica basada en el nombre del agente
        evaluation = {
            "preferred_role": RoleType.DEVELOPER.value,
            "experience_level": 5,
            "confidence_scores": {},
            "specializations": [],
            "reasoning": "Evaluacion por defecto del sistema"
        }

        # Asignar confianza basada en el nombre/tipo de agente
        for role in required_roles:
            if "backend" in agent_name.lower() or "dev" in agent_name.lower():
                evaluation["confidence_scores"][role.value] = 0.8 if role == RoleType.DEVELOPER else 0.3
            elif "frontend" in agent_name.lower() or "pm" in agent_name.lower():
                evaluation["confidence_scores"][role.value] = 0.8 if role == RoleType.PROJECT_MANAGER else 0.4
            else:
                evaluation["confidence_scores"][role.value] = 0.5

        return evaluation

    async def _negotiate_assignments(
        self,
        objective: str,
        required_roles: List[RoleType],
        evaluations: Dict[str, Dict[str, Any]]
    ) -> Dict[str, RoleAssignment]:
        """Negociar asignaciones finales basado en evaluaciones"""

        print(f"\nNegociando asignaciones finales...")

        assignments = {}
        used_roles = set()

        # Ordenar agentes por confianza general (promedio de todos los roles)
        agent_confidence = {}
        for agent, eval_data in evaluations.items():
            confidence_scores = eval_data.get("confidence_scores", {})
            if confidence_scores:
                avg_confidence = sum(confidence_scores.values()) / len(confidence_scores)
            else:
                avg_confidence = 0.5
            agent_confidence[agent] = avg_confidence

        sorted_agents = sorted(agent_confidence.keys(), key=lambda x: agent_confidence[x], reverse=True)

        # Asignar roles empezando por el agente con mayor confianza
        for agent in sorted_agents:
            eval_data = evaluations[agent]
            confidence_scores = eval_data.get("confidence_scores", {})

            # Encontrar el mejor rol disponible para este agente
            best_role = None
            best_score = 0

            for role in required_roles:
                if role not in used_roles:
                    score = confidence_scores.get(role.value, 0.5)
                    if score > best_score:
                        best_score = score
                        best_role = role

            if best_role:
                used_roles.add(best_role)

                # Crear asignación
                assignment = RoleAssignment(
                    agent_name=agent,
                    assigned_role=best_role,
                    confidence=best_score,
                    reasoning=f"Mejor puntuacion ({best_score:.2f}) para {best_role.value}. {eval_data.get('reasoning', '')}",
                    backup_roles=[r for r in required_roles if r != best_role]
                )

                assignments[agent] = assignment
                print(f"  {agent} -> {best_role.value} (confianza: {best_score:.2f})")

        # Si hay roles sin asignar y agentes disponibles, asignar los restantes
        unassigned_roles = [r for r in required_roles if r not in used_roles]
        unassigned_agents = [a for a in sorted_agents if a not in assignments]

        for i, role in enumerate(unassigned_roles):
            if i < len(unassigned_agents):
                agent = unassigned_agents[i]
                assignment = RoleAssignment(
                    agent_name=agent,
                    assigned_role=role,
                    confidence=0.5,
                    reasoning=f"Asignacion por necesidad del proyecto - rol {role.value} requerido",
                    backup_roles=[]
                )
                assignments[agent] = assignment
                print(f"  {agent} -> {role.value} (asignacion por necesidad)")

        return assignments

    def _create_assignments_from_user_specification(
        self,
        user_roles: Dict[str, RoleType]
    ) -> Dict[str, RoleAssignment]:
        """Crear asignaciones basadas en especificación del usuario"""

        assignments = {}

        for agent_name, role in user_roles.items():
            assignment = RoleAssignment(
                agent_name=agent_name,
                assigned_role=role,
                confidence=1.0,
                reasoning="Asignado explicitamente por el usuario",
                backup_roles=[]
            )
            assignments[agent_name] = assignment

        return assignments

    def get_negotiation_summary(self) -> Dict[str, Any]:
        """Obtener resumen de todas las negociaciones"""
        return {
            "total_negotiations": len(self.negotiation_history),
            "registered_agents": len(self.agent_capabilities),
            "recent_negotiations": self.negotiation_history[-5:] if self.negotiation_history else []
        }


class RoleAwareAgent(BaseConversationalAgent):
    """Agente con capacidad de auto-evaluación para roles"""

    def __init__(self, name: str, broker: MessageBroker, capabilities: Optional[AgentCapability] = None):
        super().__init__(name, "role_aware_agent", broker)
        self.capabilities = capabilities or self._default_capabilities()
        self.current_role = RoleType.UNASSIGNED
        self.role_performance_history = []

    def _default_capabilities(self) -> AgentCapability:
        """Capacidades por defecto basadas en el nombre del agente"""

        # Inferir capacidades del nombre
        if "backend" in self.name.lower() or "dev" in self.name.lower():
            preferred = [RoleType.DEVELOPER, RoleType.PROJECT_MANAGER]
            specializations = ["backend_development", "api_design", "database_management"]
        elif "frontend" in self.name.lower():
            preferred = [RoleType.PROJECT_MANAGER, RoleType.DEVELOPER]
            specializations = ["project_management", "user_interface", "coordination"]
        else:
            preferred = [RoleType.DEVELOPER, RoleType.PROJECT_MANAGER]
            specializations = ["general_development", "problem_solving"]

        return AgentCapability(
            agent_name=self.name,
            preferred_roles=preferred,
            experience_level=7,
            specializations=specializations,
            availability=1.0,
            self_assessment={
                "technical_skills": 8,
                "communication": 7,
                "leadership": 6,
                "problem_solving": 8,
                "project_management": 5
            }
        )

    async def handle_question(self, message: AgentMessage):
        """Manejar preguntas incluyendo auto-evaluación de roles"""

        question = message.content.get("question", "")

        if question == "role_self_evaluation":
            await self._handle_role_evaluation(message)
        else:
            await super().handle_question(message)

    async def _handle_role_evaluation(self, message: AgentMessage):
        """Manejar solicitud de auto-evaluación para roles"""

        objective = message.content.get("objective", "")
        required_roles = message.content.get("required_roles", [])

        print(f"  {self.name}: Evaluando mi idoneidad para roles: {required_roles}")

        # Calcular puntuaciones de confianza para cada rol
        confidence_scores = {}

        for role_str in required_roles:
            try:
                role = RoleType(role_str)
                confidence = self._calculate_role_confidence(role, objective)
                confidence_scores[role_str] = confidence
            except ValueError:
                confidence_scores[role_str] = 0.5  # Rol desconocido

        # Determinar rol preferido
        preferred_role = max(confidence_scores.keys(), key=lambda r: confidence_scores[r])

        # Generar razonamiento
        reasoning = f"Prefiero {preferred_role} con confianza {confidence_scores[preferred_role]:.2f}. "
        reasoning += f"Especializado en: {', '.join(self.capabilities.specializations)}"

        response_content = {
            "agent_name": self.name,
            "preferred_role": preferred_role,
            "confidence_scores": confidence_scores,
            "experience_level": self.capabilities.experience_level,
            "specializations": self.capabilities.specializations,
            "reasoning": reasoning,
            "objective_analysis": self._analyze_objective(objective)
        }

        await self.send_response(message, MessageType.ANSWER, response_content)

    def _calculate_role_confidence(self, role: RoleType, objective: str) -> float:
        """Calcular confianza para un rol específico"""

        base_confidence = 0.5

        # Ajustar basado en roles preferidos
        if role in self.capabilities.preferred_roles:
            base_confidence += 0.3

        # Ajustar basado en especialización
        objective_lower = objective.lower()

        if role == RoleType.PROJECT_MANAGER:
            if any(spec in ["project_management", "coordination", "leadership"]
                   for spec in self.capabilities.specializations):
                base_confidence += 0.2
            if self.capabilities.self_assessment.get("leadership", 5) > 6:
                base_confidence += 0.1

        elif role == RoleType.DEVELOPER:
            if any(spec in ["development", "programming", "technical"]
                   for spec in self.capabilities.specializations):
                base_confidence += 0.2
            if self.capabilities.self_assessment.get("technical_skills", 5) > 6:
                base_confidence += 0.1

        elif role == RoleType.ANALYST:
            if "analiz" in objective_lower:
                base_confidence += 0.2
            if self.capabilities.self_assessment.get("problem_solving", 5) > 7:
                base_confidence += 0.1

        # Ajustar por experiencia general
        experience_factor = self.capabilities.experience_level / 10
        base_confidence = base_confidence * (0.7 + 0.3 * experience_factor)

        return min(1.0, max(0.1, base_confidence))

    def _analyze_objective(self, objective: str) -> Dict[str, Any]:
        """Analizar el objetivo desde la perspectiva del agente"""

        objective_lower = objective.lower()

        complexity = "medium"
        if len(objective.split()) > 10:
            complexity = "high"
        elif len(objective.split()) < 5:
            complexity = "low"

        technical_focus = any(word in objective_lower
                            for word in ["implementar", "desarrollar", "programar", "codigo"])

        management_focus = any(word in objective_lower
                             for word in ["gestionar", "coordinar", "planificar", "organizar"])

        return {
            "complexity": complexity,
            "technical_focus": technical_focus,
            "management_focus": management_focus,
            "estimated_duration": "2-5 días" if complexity == "high" else "1-2 días"
        }

    def assign_role(self, role: RoleType, confidence: float, reasoning: str):
        """Asignar rol al agente"""
        self.current_role = role
        print(f"{self.name} asignado como {role.value} (confianza: {confidence:.2f})")
        print(f"  Razonamiento: {reasoning}")

    def get_current_role(self) -> RoleType:
        """Obtener rol actual"""
        return self.current_role