#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Shared Utilities - Comunicacion y File Locking
=================================================

Modulo compartido por los 3 agentes con:
- Envio/recepcion de mensajes (filesystem)
- File locking para evitar race conditions
- Acceso a knowledge base
- Logging estructurado
"""

import os
import sys
import json
import time
import uuid
from pathlib import Path
from datetime import datetime
from contextlib import contextmanager
from typing import Dict, List, Optional, Any


PROJECT_ROOT = Path(__file__).parent
AGENTS_DIR = PROJECT_ROOT / ".agents"
SHARED_DIR = PROJECT_ROOT / ".shared"
KB_DIR = SHARED_DIR / "knowledge_base"
LOCKS_DIR = SHARED_DIR / "locks"
CONTEXT_DIR = SHARED_DIR / "context"
LOGS_DIR = PROJECT_ROOT / ".logs"


# ============================================================================
# LOGGING
# ============================================================================

def log(agent_role: str, message: str, level: str = "INFO"):
    """
    Log estructurado con timestamp y role.

    Args:
        agent_role: orchestrator, pm, dev
        message: Mensaje a loggear
        level: INFO, WARN, ERROR, SUCCESS
    """
    timestamp = datetime.now().strftime("%H:%M:%S")

    symbols = {
        "INFO": ">>",
        "WARN": "!!",
        "ERROR": "XX",
        "SUCCESS": "OK"
    }
    symbol = symbols.get(level, ">>")

    role_names = {
        "orchestrator": "Alex",
        "pm": "Morgan",
        "dev": "Jordan"
    }
    name = role_names.get(agent_role, agent_role)

    log_msg = f"[{timestamp}] [{name:8s}] {symbol} {message}"
    try:
        print(log_msg)
    except UnicodeEncodeError:
        # Fallback para Windows cmd con cp1252
        safe_msg = log_msg.encode('ascii', errors='replace').decode('ascii')
        print(safe_msg)

    # Guardar tambien en archivo
    log_file = LOGS_DIR / agent_role / f"{datetime.now().strftime('%Y%m%d')}.log"
    log_file.parent.mkdir(parents=True, exist_ok=True)

    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(log_msg + "\n")


# ============================================================================
# FILE LOCKING
# ============================================================================

@contextmanager
def acquire_lock(resource_name: str, timeout: int = 30):
    """
    Adquirir lock exclusivo sobre un recurso.

    Usa el patron de crear archivo .lock. Si el archivo existe,
    otro proceso tiene el lock.

    Args:
        resource_name: Nombre del recurso a lockear
        timeout: Segundos maximos a esperar

    Yields:
        True si lock adquirido

    Raises:
        TimeoutError si no se puede adquirir lock
    """
    LOCKS_DIR.mkdir(parents=True, exist_ok=True)
    lock_file = LOCKS_DIR / f"{resource_name}.lock"

    start_time = time.time()

    while (time.time() - start_time) < timeout:
        try:
            # Intentar crear archivo exclusivamente
            fd = os.open(
                str(lock_file),
                os.O_CREAT | os.O_EXCL | os.O_WRONLY
            )

            try:
                # Escribir info del lock
                lock_info = {
                    "resource": resource_name,
                    "acquired_at": datetime.now().isoformat(),
                    "pid": os.getpid()
                }
                os.write(fd, json.dumps(lock_info).encode())

                # Lock adquirido, yield control
                yield True

            finally:
                # Liberar lock
                os.close(fd)
                if lock_file.exists():
                    lock_file.unlink()

            return

        except FileExistsError:
            # Lock ocupado, esperar
            time.sleep(0.1)

    # Timeout
    raise TimeoutError(
        f"Could not acquire lock for '{resource_name}' after {timeout}s"
    )


def cleanup_stale_locks(max_age_seconds: int = 300):
    """
    Limpiar locks huerfanos (>5 min de antiguedad).

    Args:
        max_age_seconds: Edad maxima en segundos
    """
    if not LOCKS_DIR.exists():
        return

    now = time.time()

    for lock_file in LOCKS_DIR.glob("*.lock"):
        age = now - lock_file.stat().st_mtime

        if age > max_age_seconds:
            try:
                lock_file.unlink()
            except Exception:
                pass


# ============================================================================
# MESSAGING
# ============================================================================

def send_message(
    from_role: str,
    to_role: str,
    msg_type: str,
    content: Dict[str, Any],
    priority: str = "normal",
    requires_response: bool = True,
    conversation_id: Optional[str] = None
) -> str:
    """
    Enviar mensaje a otro agente.

    Args:
        from_role: orchestrator, pm, dev
        to_role: orchestrator, pm, dev
        msg_type: Tipo de mensaje (TASK_ASSIGNMENT, etc)
        content: Contenido del mensaje (dict)
        priority: low, normal, high, critical
        requires_response: Si espera respuesta
        conversation_id: ID de conversacion (o None para nuevo)

    Returns:
        message_id: ID del mensaje enviado
    """
    # Generar IDs
    msg_id = f"msg_{int(time.time() * 1000)}"
    conv_id = conversation_id or f"conv_{uuid.uuid4().hex[:8]}"

    # Construir mensaje
    message = {
        "id": msg_id,
        "from": from_role,
        "to": to_role,
        "type": msg_type,
        "priority": priority,
        "timestamp": datetime.now().isoformat(),
        "content": content,
        "conversation_id": conv_id,
        "requires_response": requires_response
    }

    # Guardar en inbox del destinatario
    inbox_dir = AGENTS_DIR / to_role / "inbox"
    inbox_dir.mkdir(parents=True, exist_ok=True)

    filename = f"{from_role}_to_{to_role}_{int(time.time() * 1000)}.json"
    filepath = inbox_dir / filename

    with acquire_lock(f"write_{filename}"):
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(message, f, indent=2, ensure_ascii=False)

    # Copiar a outbox del emisor (para tracking)
    outbox_dir = AGENTS_DIR / from_role / "outbox"
    outbox_dir.mkdir(parents=True, exist_ok=True)
    outbox_copy = outbox_dir / filename

    with open(outbox_copy, 'w', encoding='utf-8') as f:
        json.dump(message, f, indent=2, ensure_ascii=False)

    log(from_role, f"Sent {msg_type} to {to_role} (id: {msg_id})")

    return msg_id


def read_inbox(
    role: str,
    msg_type: Optional[str] = None,
    mark_as_read: bool = True
) -> Optional[Dict[str, Any]]:
    """
    Leer proximo mensaje del inbox.

    Args:
        role: orchestrator, pm, dev
        msg_type: Si especificado, solo leer mensajes de este tipo
        mark_as_read: Si True, marca archivo como leido (.json.read)

    Returns:
        message: Dict con mensaje, o None si inbox vacio
    """
    inbox_dir = AGENTS_DIR / role / "inbox"

    if not inbox_dir.exists():
        return None

    # Leer archivos .json (no .json.read)
    json_files = sorted(inbox_dir.glob("*.json"))

    # Filtrar solo archivos .json (excluir .json.read)
    json_files = [f for f in json_files if f.suffix == ".json"]

    for filepath in json_files:
        try:
            with acquire_lock(f"read_{filepath.name}", timeout=5):
                with open(filepath, 'r', encoding='utf-8') as f:
                    message = json.load(f)

                # Filtrar por tipo si especificado
                if msg_type and message.get("type") != msg_type:
                    continue

                # Marcar como leido
                if mark_as_read:
                    read_path = filepath.with_suffix('.json.read')
                    filepath.rename(read_path)

                log(role, f"Read {message['type']} from {message['from']}")

                return message

        except (json.JSONDecodeError, TimeoutError, Exception) as e:
            log(role, f"Error reading {filepath.name}: {e}", "WARN")
            continue

    return None


def wait_for_message(
    role: str,
    msg_type: str,
    from_role: Optional[str] = None,
    timeout: int = 120
) -> Optional[Dict[str, Any]]:
    """
    Esperar mensaje especifico (blocking).

    Args:
        role: orchestrator, pm, dev
        msg_type: Tipo de mensaje a esperar
        from_role: Si especificado, solo de este remitente
        timeout: Segundos maximos a esperar

    Returns:
        message: Dict con mensaje, o None si timeout
    """
    log(role, f"Waiting for {msg_type}" +
        (f" from {from_role}" if from_role else "") + "...")

    start_time = time.time()

    while (time.time() - start_time) < timeout:
        msg = read_inbox(role, msg_type=msg_type, mark_as_read=True)

        if msg:
            # Filtrar por remitente si especificado
            if from_role and msg.get("from") != from_role:
                continue

            return msg

        time.sleep(0.5)

    log(role, f"Timeout waiting for {msg_type}", "WARN")
    return None


def count_inbox_messages(role: str) -> int:
    """Contar mensajes pendientes en inbox"""
    inbox_dir = AGENTS_DIR / role / "inbox"

    if not inbox_dir.exists():
        return 0

    return len(list(inbox_dir.glob("*.json")))


# ============================================================================
# KNOWLEDGE BASE
# ============================================================================

def search_patterns(
    keywords: List[str],
    complexity: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Buscar patrones en knowledge base.

    Args:
        keywords: Lista de keywords a buscar
        complexity: SIMPLE, MEDIUM, COMPLEX, ENTERPRISE (opcional)

    Returns:
        patterns: Lista de patrones que coinciden
    """
    catalog_file = KB_DIR / "patterns/catalog.json"

    if not catalog_file.exists():
        return []

    with open(catalog_file, 'r', encoding='utf-8') as f:
        all_patterns = json.load(f)

    matches = []

    for pattern_id, pattern in all_patterns.items():
        # Filtrar por complejidad
        if complexity and pattern.get("complexity") != complexity:
            continue

        # Buscar keywords en nombre y descripcion
        text = (pattern.get("name", "") + " " +
                pattern.get("description", "")).lower()

        if any(kw.lower() in text for kw in keywords):
            matches.append({
                "id": pattern_id,
                **pattern
            })

    return matches


def get_tech_stack(domain: str) -> Optional[Dict[str, Any]]:
    """
    Obtener tech stack recomendado para un dominio.

    Args:
        domain: api, scraping, game, etc

    Returns:
        stack: Dict con stack recomendado, o None
    """
    stacks_file = KB_DIR / "stacks/catalog.json"

    if not stacks_file.exists():
        return None

    with open(stacks_file, 'r', encoding='utf-8') as f:
        stacks = json.load(f)

    # Buscar por dominio (fuzzy match)
    domain_lower = domain.lower()

    for stack_id, stack in stacks.items():
        stack_domain = stack.get("domain", "").lower()
        if domain_lower in stack_domain or stack_domain in domain_lower:
            return {"id": stack_id, **stack}

    return None


def get_security_rules() -> List[Dict[str, Any]]:
    """Obtener reglas de seguridad (OWASP Top 10)"""
    security_file = KB_DIR / "security/owasp_top10.json"

    if not security_file.exists():
        return []

    with open(security_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    return data.get("owasp_top5", [])


# ============================================================================
# SHARED CONTEXT
# ============================================================================

def save_current_objective(objective: str, complexity: str):
    """Guardar objetivo actual en contexto compartido"""
    CONTEXT_DIR.mkdir(parents=True, exist_ok=True)

    context = {
        "objective": objective,
        "complexity": complexity,
        "started_at": datetime.now().isoformat()
    }

    context_file = CONTEXT_DIR / "current_objective.json"

    with open(context_file, 'w', encoding='utf-8') as f:
        json.dump(context, f, indent=2, ensure_ascii=False)


def get_current_objective() -> Optional[Dict[str, Any]]:
    """Leer objetivo actual"""
    context_file = CONTEXT_DIR / "current_objective.json"

    if not context_file.exists():
        return None

    with open(context_file, 'r', encoding='utf-8') as f:
        return json.load(f)


# ============================================================================
# AGENT STATE
# ============================================================================

def save_agent_state(role: str, state: Dict[str, Any]):
    """Guardar estado del agente"""
    state_file = AGENTS_DIR / role / "state.json"

    with acquire_lock(f"state_{role}"):
        with open(state_file, 'w', encoding='utf-8') as f:
            json.dump(state, f, indent=2, ensure_ascii=False)


def load_agent_state(role: str) -> Dict[str, Any]:
    """Cargar estado del agente"""
    state_file = AGENTS_DIR / role / "state.json"

    if not state_file.exists():
        return {}

    with open(state_file, 'r', encoding='utf-8') as f:
        return json.load(f)


# ============================================================================
# UTILITIES
# ============================================================================

def classify_complexity(objective: str) -> str:
    """
    Clasificar complejidad de objetivo basado en keywords.

    Returns:
        SIMPLE, MEDIUM, COMPLEX, ENTERPRISE
    """
    obj_lower = objective.lower()

    # ENTERPRISE indicators
    enterprise_kw = [
        'multi-tenant', 'saas', 'microservicio', 'kubernetes',
        '100k usuarios', 'pci-dss', 'iso-27001', 'gdpr',
        'scalable', 'high availability', 'disaster recovery'
    ]

    if any(kw in obj_lower for kw in enterprise_kw):
        return "ENTERPRISE"

    # COMPLEX indicators
    complex_kw = [
        'real-time', 'websocket', 'streaming', 'machine learning',
        'ml', 'ia', 'ai', 'embedding', 'vector database',
        'distributed', 'event sourcing'
    ]

    if any(kw in obj_lower for kw in complex_kw):
        return "COMPLEX"

    # MEDIUM indicators
    medium_kw = [
        'api', 'rest', 'graphql', 'crud', 'autenticacion', 'jwt',
        'base de datos', 'postgresql', 'mysql', 'mongodb'
    ]

    if any(kw in obj_lower for kw in medium_kw):
        return "MEDIUM"

    # Default SIMPLE
    return "SIMPLE"


def cleanup_old_messages(role: str, days_old: int = 7):
    """Limpiar mensajes antiguos (>7 dias)"""
    inbox_dir = AGENTS_DIR / role / "inbox"
    outbox_dir = AGENTS_DIR / role / "outbox"

    cutoff = time.time() - (days_old * 86400)

    for directory in [inbox_dir, outbox_dir]:
        if not directory.exists():
            continue

        for filepath in directory.glob("*.json*"):
            if filepath.stat().st_mtime < cutoff:
                try:
                    filepath.unlink()
                except Exception:
                    pass
