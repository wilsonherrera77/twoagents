#!/usr/bin/env python3
"""
Sistema de Comunicación Entre Agentes
Permite que AgentA y AgentB se comuniquen, pregunten y aprueben acciones entre ellos.
"""

import asyncio
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass
from enum import Enum

try:
    from message_contracts_v2 import message_validator, message_factory, StandardMessageContract
    VALIDATION_V2_ENABLED = True
    print("[OK] Protocolo v2.0 habilitado")
except ImportError:
    VALIDATION_V2_ENABLED = False
    print("[WARN] message_contracts_v2 no disponible - usando protocolo legacy")


class MessageType(Enum):
    ACK = "ack"
    TASK_SPEC = "task_spec"
    APPROVAL_REQUEST = "approval_request"
    APPROVAL_RESPONSE = "approval_response"
    IMPLEMENTATION_PLAN = "implementation_plan"
    IMPLEMENTATION_STARTED = "implementation_started"
    IMPLEMENTATION_PROGRESS = "implementation_progress"
    IMPLEMENTATION_COMPLETED = "implementation_completed"
    DATA = "data"
    QUESTION = "question"
    ANSWER = "answer"
    BLOCKER = "blocker"
    STATUS_UPDATE = "status_update"
    ERROR = "error"
    FINISH = "finish"
    # Legacy support
    APPROVAL = "approval"
    SUGGESTION = "suggestion"
    NEGOTIATION = "negotiation"


@dataclass
class AgentMessage:
    """Estructura de mensaje entre agentes"""
    id: str
    sender: str
    receiver: str
    message_type: MessageType
    content: Dict[str, Any]
    requires_approval: bool = False
    timestamp: datetime = None
    response_to: Optional[str] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
        if self.id is None:
            self.id = str(uuid.uuid4())


def validate_message(msg: dict) -> tuple[bool, str]:
    """Validador de esquema para mensajes v1.0"""
    required = {"schema_version", "from", "to", "message_type", "correlation_id", "timestamp", "payload"}
    missing = required - msg.keys()
    if missing:
        return False, f"Missing keys: {missing}"

    # Validar schema_version
    if msg.get("schema_version") != "1.0":
        return False, f"Invalid schema_version: {msg.get('schema_version')}, expected '1.0'"

    # Validar message_type
    valid_types = [mt.value for mt in MessageType]
    if msg.get("message_type") not in valid_types:
        return False, f"Invalid message_type: {msg.get('message_type')}"

    return True, ""


class MessageBroker:
    """Broker central para manejar comunicación entre agentes"""

    def __init__(self):
        self.message_queue = asyncio.Queue()
        self.agents: Dict[str, 'BaseConversationalAgent'] = {}
        self.pending_responses: Dict[str, asyncio.Future] = {}
        self.message_history: List[AgentMessage] = []
        self.running = False

    def register_agent(self, agent: 'BaseConversationalAgent'):
        """Registrar un agente en el broker"""
        self.agents[agent.name] = agent
        print(f"Agente registrado: {agent.name}")

    async def send_message(self, message: AgentMessage) -> Optional[AgentMessage]:
        """Enviar mensaje a través del broker con validación v2.0"""

        # Validar mensaje con protocolo v2.0 si está habilitado
        if VALIDATION_V2_ENABLED:
            # Si el contenido ya está en formato v2.0, validar directamente
            if isinstance(message.content, dict) and "schema_version" in message.content:
                is_valid, error_msg = message_validator.validate_message(message.content)
                if not is_valid:
                    print(f"[REJECT] Mensaje v2.0 de {message.sender} rechazado: {error_msg}")
                    return None
                print(f"[OK] Mensaje v2.0 validado: {message.content.get('message_type', 'unknown')}")

        self.message_history.append(message)
        await self.message_queue.put(message)

        # Si requiere respuesta, esperar por ella
        if message.requires_approval or message.message_type in [MessageType.QUESTION, MessageType.APPROVAL_REQUEST]:
            future = asyncio.Future()
            self.pending_responses[message.id] = future
            try:
                response = await asyncio.wait_for(future, timeout=30.0)
                return response
            except asyncio.TimeoutError:
                print(f"Timeout esperando respuesta a mensaje {message.id}")
                return None

        return None

    async def send_response(self, response_message: AgentMessage):
        """Enviar respuesta a un mensaje pendiente"""
        if response_message.response_to and response_message.response_to in self.pending_responses:
            future = self.pending_responses.pop(response_message.response_to)
            if not future.done():
                future.set_result(response_message)

        self.message_history.append(response_message)

    async def start_routing(self):
        """Iniciar el routing de mensajes"""
        self.running = True
        print("MessageBroker iniciado - routing mensajes...")

        while self.running:
            try:
                message = await asyncio.wait_for(self.message_queue.get(), timeout=1.0)
                await self._route_message(message)
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                print(f"Error en routing: {e}")

    async def _route_message(self, message: AgentMessage):
        """Enrutar mensaje al agente destino"""
        if message.receiver in self.agents:
            agent = self.agents[message.receiver]
            print(f"{message.sender} -> {message.receiver}: {message.message_type.value}")
            await agent.receive_message(message)
        else:
            print(f"Agente destinatario no encontrado: {message.receiver}")

    def stop_routing(self):
        """Detener el routing de mensajes"""
        self.running = False
        print("MessageBroker detenido")

    def get_conversation_history(self, agent1: str = None, agent2: str = None) -> List[AgentMessage]:
        """Obtener historial de conversación"""
        if agent1 and agent2:
            return [msg for msg in self.message_history
                   if (msg.sender == agent1 and msg.receiver == agent2) or
                      (msg.sender == agent2 and msg.receiver == agent1)]
        return self.message_history


class BaseConversationalAgent:
    """Clase base para agentes conversacionales"""

    def __init__(self, name: str, role: str, broker: MessageBroker):
        self.name = name
        self.role = role
        self.broker = broker
        self.message_handlers: Dict[MessageType, Callable] = {}
        self.conversation_context: Dict[str, Any] = {}

        # Registrar handlers por defecto
        self._register_default_handlers()

        # Registrar en broker
        broker.register_agent(self)

    def _register_default_handlers(self):
        """Registrar handlers por defecto para tipos de mensaje"""
        self.message_handlers[MessageType.QUESTION] = self.handle_question
        self.message_handlers[MessageType.APPROVAL_REQUEST] = self.handle_approval_request
        self.message_handlers[MessageType.SUGGESTION] = self.handle_suggestion
        self.message_handlers[MessageType.ERROR] = self.handle_error
        self.message_handlers[MessageType.STATUS_UPDATE] = self.handle_status_update
        self.message_handlers[MessageType.DATA] = self.handle_data
        self.message_handlers[MessageType.ANSWER] = self.handle_answer
        self.message_handlers[MessageType.APPROVAL] = self.handle_approval
        self.message_handlers[MessageType.NEGOTIATION] = self.handle_negotiation

    async def receive_message(self, message: AgentMessage):
        """Recibir y procesar mensaje"""
        try:
            # Actualizar contexto
            self.conversation_context[f"last_message_from_{message.sender}"] = message

            # Buscar handler apropiado
            if message.message_type in self.message_handlers:
                await self.message_handlers[message.message_type](message)
            else:
                await self.handle_unknown_message(message)

        except Exception as e:
            print(f"Error procesando mensaje en {self.name}: {e}")
            await self.send_error_response(message, str(e))

    async def send_message(self, receiver: str, message_type: MessageType,
                          content: Dict[str, Any], requires_approval: bool = False,
                          response_to: str = None) -> Optional[AgentMessage]:
        """Enviar mensaje a otro agente"""
        message = AgentMessage(
            id=str(uuid.uuid4()),
            sender=self.name,
            receiver=receiver,
            message_type=message_type,
            content=content,
            requires_approval=requires_approval,
            response_to=response_to
        )

        return await self.broker.send_message(message)

    async def send_v2_message(self, receiver_agent: str, v2_message: Dict[str, Any]) -> Optional[AgentMessage]:
        """Enviar mensaje usando protocolo v2.0"""

        if not VALIDATION_V2_ENABLED:
            print("⚠️ Protocolo v2.0 no disponible, usando mensaje legacy")
            return None

        # Crear AgentMessage wrapper para el mensaje v2.0
        legacy_message = AgentMessage(
            id=v2_message.get("correlation_id", str(uuid.uuid4())),
            sender=self.name,
            receiver=receiver_agent,
            message_type=MessageType.DATA,  # Usar DATA como wrapper
            content=v2_message,  # El mensaje v2.0 completo va en content
            requires_approval=v2_message.get("message_type") in ["task_spec", "implementation_plan"],
            response_to=None
        )

        return await self.broker.send_message(legacy_message)

    async def send_response(self, original_message: AgentMessage, message_type: MessageType,
                           content: Dict[str, Any]):
        """Enviar respuesta a un mensaje"""
        response = AgentMessage(
            id=str(uuid.uuid4()),
            sender=self.name,
            receiver=original_message.sender,
            message_type=message_type,
            content=content,
            response_to=original_message.id
        )

        await self.broker.send_response(response)

    async def send_error_response(self, original_message: AgentMessage, error_description: str):
        """Enviar respuesta de error"""
        await self.send_response(
            original_message,
            MessageType.ERROR,
            {"error": error_description, "original_message_id": original_message.id}
        )

    # Handlers por defecto (pueden ser sobrescritos)
    async def handle_question(self, message: AgentMessage):
        """Handler por defecto para preguntas"""
        await self.send_response(
            message,
            MessageType.ANSWER,
            {"answer": f"No tengo respuesta específica para: {message.content}"}
        )

    async def handle_approval_request(self, message: AgentMessage):
        """Handler por defecto para requests de aprobación"""
        await self.send_response(
            message,
            MessageType.APPROVAL,
            {"approved": True, "comments": "Aprobado automáticamente"}
        )

    async def handle_suggestion(self, message: AgentMessage):
        """Handler por defecto para sugerencias"""
        print(f"Sugerencia de {message.sender}: {message.content}")

    async def handle_error(self, message: AgentMessage):
        """Handler por defecto para errores"""
        print(f"Error reportado por {message.sender}: {message.content}")

    async def handle_status_update(self, message: AgentMessage):
        """Handler por defecto para updates de status"""
        print(f"Status de {message.sender}: {message.content}")

    async def handle_data(self, message: AgentMessage):
        """Handler por defecto para mensajes de datos"""
        print(f"Datos recibidos de {message.sender}: {message.content.get('message_type', 'data')}")

    async def handle_answer(self, message: AgentMessage):
        """Handler por defecto para respuestas"""
        print(f"Respuesta de {message.sender}: {message.content}")

    async def handle_approval(self, message: AgentMessage):
        """Handler por defecto para aprobaciones"""
        approved = message.content.get('approved', True)
        print(f"Aprobación de {message.sender}: {'[OK] Aprobado' if approved else '[ERROR] Rechazado'}")

    async def handle_negotiation(self, message: AgentMessage):
        """Handler por defecto para negociaciones"""
        print(f"Negociación de {message.sender}: {message.content}")

    async def handle_unknown_message(self, message: AgentMessage):
        """Handler para mensajes desconocidos"""
        print(f"Mensaje desconocido de {message.sender}: {message.message_type}")


# Utilidades para logging y debugging
class ConversationLogger:
    """Logger para conversaciones entre agentes"""

    def __init__(self, broker: MessageBroker):
        self.broker = broker

    def print_conversation(self, agent1: str = None, agent2: str = None):
        """Imprimir conversación en formato legible"""
        history = self.broker.get_conversation_history(agent1, agent2)

        print("\n" + "="*50)
        print("HISTORIAL DE CONVERSACION")
        print("="*50)

        for msg in history:
            timestamp = msg.timestamp.strftime("%H:%M:%S")
            print(f"[{timestamp}] {msg.sender} -> {msg.receiver}")
            print(f"    Tipo: {msg.message_type.value}")
            print(f"    Contenido: {msg.content}")
            if msg.response_to:
                print(f"    Respuesta a: {msg.response_to}")
            print()

    def export_conversation(self, filename: str = "conversation_log.json"):
        """Exportar conversación a archivo JSON"""
        import json

        history_data = []
        for msg in self.broker.message_history:
            history_data.append({
                "id": msg.id,
                "sender": msg.sender,
                "receiver": msg.receiver,
                "message_type": msg.message_type.value,
                "content": msg.content,
                "requires_approval": msg.requires_approval,
                "timestamp": msg.timestamp.isoformat(),
                "response_to": msg.response_to
            })

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(history_data, f, indent=2, ensure_ascii=False)

        print(f"Conversacion exportada a: {filename}")