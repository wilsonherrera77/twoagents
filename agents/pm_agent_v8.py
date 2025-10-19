#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PM Agent V8 - Independent Process
==================================

PM Agent (Morgan) como proceso independiente que:
1. Lee objetivos de .shared/state/objective.json
2. Propone arquitecturas
3. Negocia con Dev Agent (lee counter-proposals)
4. Ajusta arquitectura basado en feedback
5. Señala acuerdo cuando negociación completa

Comunicación: Filesystem-based via .shared/
"""

import sys
import time
import json
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional

# Add parent directory to path para imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from protocols.message_types import (
    ProposalMessage,
    EvaluationMessage,
    write_message,
    read_message,
    AgentAction
)

# Configuración
PROJECT_ROOT = Path(__file__).parent.parent
SHARED_DIR = PROJECT_ROOT / ".shared"
STATE_DIR = SHARED_DIR / "state"
PM_DIR = SHARED_DIR / "pm"
DEV_DIR = SHARED_DIR / "dev"

POLL_INTERVAL = 5  # segundos
CLAUDE_TIMEOUT = 180  # 3 minutos
MAX_NEGOTIATION_ROUNDS = 5

# Enterprise requirements para todos los proyectos
ENTERPRISE_REQUIREMENTS = """
REQUISITOS ENTERPRISE OBLIGATORIOS:
- JWT authentication (si aplica web/API)
- SQLAlchemy ORM + Alembic migrations (si necesita BD)
- Tests unitarios + integración con >95% coverage
- Prometheus metrics para observabilidad
- Docker + docker-compose para deployment
- Rate limiting y seguridad (OWASP compliance)
- Structured logging (JSON format)
- README.md con setup instructions
- requirements.txt completo
"""


def log(message: str, level: str = "INFO"):
    """Log con timestamp"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] [PM Agent] [{level}] {message}")


def execute_claude(prompt: str, timeout: int = CLAUDE_TIMEOUT) -> Optional[Dict]:
    """
    Ejecuta Claude via CLI para razonamiento arquitectónico.

    Reutiliza método probado de V7 con mejoras.
    """
    import uuid

    session_uuid = str(uuid.uuid4())[:8]

    # Usar .agents/pm/ para compatibilidad con V7
    agent_dir = PROJECT_ROOT / ".agents" / "pm"
    inbox_dir = agent_dir / "inbox"
    outbox_dir = agent_dir / "outbox"

    inbox_dir.mkdir(parents=True, exist_ok=True)
    outbox_dir.mkdir(parents=True, exist_ok=True)

    prompt_file = inbox_dir / f"prompt_{session_uuid}.txt"
    response_file = outbox_dir / f"response_{session_uuid}.json"

    try:
        log(f"Ejecutando Claude (session: {session_uuid})...")

        # Escribir prompt
        prompt_file.write_text(prompt, encoding='utf-8')

        # Ejecutar Claude
        with open(prompt_file, 'r', encoding='utf-8') as stdin_file:
            with open(response_file, 'w', encoding='utf-8') as stdout_file:
                result = subprocess.run(
                    ['claude', '--print', '--output-format', 'json'],
                    stdin=stdin_file,
                    stdout=stdout_file,
                    stderr=subprocess.PIPE,
                    text=True,
                    timeout=timeout,
                    cwd=str(agent_dir),
                    shell=True  # Windows compatibility
                )

        # Esperar respuesta
        wait_start = time.time()
        while not response_file.exists():
            if time.time() - wait_start > 10:
                log("Response file not created", "ERROR")
                return None
            time.sleep(0.5)

        # Leer y parsear respuesta
        response_text = response_file.read_text(encoding='utf-8')

        if not response_text.strip():
            log("Empty response from Claude", "ERROR")
            return None

        # Parse JSON response
        data = json.loads(response_text)

        if data.get("type") != "result":
            log(f"Unexpected response type: {data.get('type')}", "ERROR")
            return None

        result_text = data.get("result", "")

        # Extract JSON from response (multiple strategies)
        # Strategy 1: ```json block
        if "```json" in result_text:
            try:
                json_str = result_text.split("```json")[1].split("```")[0].strip()
                parsed = json.loads(json_str)
                log("Claude responded successfully", "SUCCESS")
                return parsed
            except (IndexError, json.JSONDecodeError):
                pass

        # Strategy 2: Pure JSON
        try:
            parsed = json.loads(result_text)
            log("Claude responded with pure JSON", "SUCCESS")
            return parsed
        except json.JSONDecodeError:
            pass

        # Strategy 3: Find first JSON object
        try:
            start_idx = result_text.find('{')
            if start_idx != -1:
                parsed = json.loads(result_text[start_idx:])
                log("Claude responded with embedded JSON", "SUCCESS")
                return parsed
        except json.JSONDecodeError:
            pass

        log("Could not parse JSON from Claude response", "ERROR")
        return None

    except subprocess.TimeoutExpired:
        log(f"Claude timeout after {timeout}s", "ERROR")
        return None
    except Exception as e:
        log(f"Error executing Claude: {e}", "ERROR")
        return None


def propose_architecture(objective: str, iteration: int) -> Optional[ProposalMessage]:
    """
    Proponer arquitectura inicial usando Claude.
    """
    prompt = f"""Eres PM Agent (Morgan), arquitecto de software senior.

OBJETIVO DEL USUARIO:
{objective}

{ENTERPRISE_REQUIREMENTS}

TU TAREA COMO PM:
1. Analiza el objetivo en profundidad
2. Identifica componentes clave necesarios
3. Propón arquitectura modular (5-8 módulos Python específicos)
4. Define estructura de base de datos si aplica
5. Especifica stack tecnológico apropiado

RESPONDE EN FORMATO JSON ESTRICTO (sin texto adicional):

{{
  "role": "pm",
  "analysis": "análisis breve del objetivo (2-3 oraciones)",
  "proposed_modules": [
    "module1.py",
    "module2.py",
    "module3.py"
  ],
  "database_schema": {{
    "tables": ["tabla1", "tabla2"],
    "relationships": "descripción de relaciones clave"
  }},
  "technologies": {{
    "framework": "FastAPI",
    "database": "PostgreSQL",
    "cache": "Redis",
    "auth": "JWT + bcrypt",
    "testing": "pytest"
  }},
  "reasoning": "por qué esta arquitectura es apropiada (3-4 oraciones)"
}}

IMPORTANTE:
- Sé ESPECÍFICO al objetivo (no genérico)
- Propón módulos CONCRETOS (no "module1.py", sino "user_auth.py")
- Responde SOLO JSON (sin explicaciones antes/después)
"""

    log(f"Iteration {iteration}: Proposing architecture...")

    result = execute_claude(prompt)

    if not result:
        log("Failed to get architecture from Claude", "ERROR")
        return None

    # Validate response
    if not result.get("proposed_modules"):
        log("Claude response missing proposed_modules", "ERROR")
        return None

    # Create ProposalMessage
    proposal = ProposalMessage(
        architecture={
            "proposed_modules": result.get("proposed_modules", []),
            "database_schema": result.get("database_schema", {}),
            "technologies": result.get("technologies", {}),
            "analysis": result.get("analysis", "")
        },
        reasoning=result.get("reasoning", ""),
        iteration=iteration,
        action=AgentAction.PROPOSE.value
    )

    log(f"Proposed {len(result.get('proposed_modules', []))} modules", "SUCCESS")

    return proposal


def adjust_architecture(
    original_proposal: Dict,
    dev_feedback: EvaluationMessage,
    iteration: int
) -> Optional[ProposalMessage]:
    """
    Ajustar arquitectura basado en counter-proposal de Dev.
    """
    prompt = f"""Eres PM Agent (Morgan), arquitecto de software senior.

PROPUESTA ORIGINAL:
{json.dumps(original_proposal, indent=2)}

FEEDBACK DEL DEV AGENT:
Acción: {dev_feedback.action}
Concerns: {json.dumps(dev_feedback.concerns, indent=2)}

ARQUITECTURA ALTERNATIVA SUGERIDA POR DEV:
{json.dumps(dev_feedback.alternative_architecture, indent=2) if dev_feedback.alternative_architecture else "Ninguna"}

TU TAREA:
1. Analiza los concerns de Dev
2. Evalúa si son válidos técnicamente
3. Si son válidos: ajusta arquitectura incorporando sugerencias
4. Si no son válidos: justifica decisión original
5. Propón arquitectura ajustada

RESPONDE EN FORMATO JSON:

{{
  "role": "pm",
  "action": "ADJUST" | "AGREE" | "REJECT",
  "architecture": {{
    "proposed_modules": [...],
    "database_schema": {{...}},
    "technologies": {{...}}
  }},
  "reasoning": "por qué aceptas/rechazas feedback de Dev",
  "response_to_dev": [
    "Addressed concern X by...",
    "Modified module Y to..."
  ]
}}

IMPORTANTE:
- Si Dev tiene razón: "action": "ADJUST" y modifica arquitectura
- Si arquitectura está bien: "action": "AGREE" (sin cambios)
- Responde SOLO JSON
"""

    log(f"Iteration {iteration}: Adjusting architecture based on Dev feedback...")

    result = execute_claude(prompt)

    if not result:
        log("Failed to adjust architecture", "ERROR")
        return None

    action = result.get("action", "ADJUST")

    # Create adjusted ProposalMessage
    proposal = ProposalMessage(
        architecture=result.get("architecture", original_proposal),
        reasoning=result.get("reasoning", ""),
        iteration=iteration,
        action=action,
        response_to_dev=result.get("response_to_dev", [])
    )

    log(f"Action: {action}", "SUCCESS")

    return proposal


def main_loop():
    """
    Loop principal del PM Agent.

    Estados:
    1. WAITING_OBJECTIVE: Esperando objetivo del orchestrator
    2. PROPOSING: Generando propuesta arquitectónica
    3. NEGOTIATING: Esperando evaluación de Dev
    4. AGREED: Negociación completa
    """
    log("PM Agent V8 started")
    log(f"Watching: {STATE_DIR}")
    log(f"Output to: {PM_DIR}")

    state = "WAITING_OBJECTIVE"
    current_iteration = 0
    current_objective = None
    current_proposal = None
    negotiation_rounds = 0

    while True:
        try:
            # STATE: WAITING_OBJECTIVE
            if state == "WAITING_OBJECTIVE":
                objective_file = STATE_DIR / "objective.json"

                if objective_file.exists():
                    obj_data = read_message(objective_file)

                    if obj_data:
                        current_objective = obj_data.get("objective")
                        current_iteration = obj_data.get("iteration", 1)

                        log(f"New objective received: {current_objective[:50]}...")
                        state = "PROPOSING"
                        negotiation_rounds = 0

            # STATE: PROPOSING
            elif state == "PROPOSING":
                proposal = propose_architecture(current_objective, current_iteration)

                if proposal:
                    # Write proposal to .shared/pm/
                    proposal_file = PM_DIR / f"proposal_{current_iteration:03d}.json"
                    write_message(proposal, proposal_file)

                    current_proposal = proposal.architecture
                    log(f"Proposal written to {proposal_file.name}")

                    state = "NEGOTIATING"
                else:
                    log("Failed to generate proposal, retrying...", "ERROR")
                    time.sleep(POLL_INTERVAL)

            # STATE: NEGOTIATING
            elif state == "NEGOTIATING":
                eval_file = DEV_DIR / f"evaluation_{current_iteration:03d}.json"

                if eval_file.exists():
                    eval_data = read_message(eval_file)

                    if eval_data:
                        action = eval_data.get("action")

                        if action == "ACCEPT":
                            log("Dev accepted proposal!", "SUCCESS")

                            # Write agreement signal
                            agreement_file = PM_DIR / "agreement.json"
                            write_message(ProposalMessage(
                                architecture=current_proposal,
                                reasoning="Dev accepted proposal",
                                iteration=current_iteration,
                                action=AgentAction.AGREE.value
                            ), agreement_file)

                            state = "AGREED"

                        elif action == "COUNTER":
                            log("Dev counter-proposed, adjusting...")
                            negotiation_rounds += 1

                            if negotiation_rounds >= MAX_NEGOTIATION_ROUNDS:
                                log(f"Max negotiation rounds ({MAX_NEGOTIATION_ROUNDS}) reached, forcing agreement", "WARN")
                                state = "AGREED"
                            else:
                                # Adjust architecture
                                dev_feedback = EvaluationMessage.from_dict(eval_data)
                                adjusted = adjust_architecture(
                                    current_proposal,
                                    dev_feedback,
                                    current_iteration
                                )

                                if adjusted:
                                    # Write adjusted proposal
                                    current_iteration += 1
                                    proposal_file = PM_DIR / f"proposal_{current_iteration:03d}.json"
                                    write_message(adjusted, proposal_file)

                                    current_proposal = adjusted.architecture
                                    log(f"Adjusted proposal written to {proposal_file.name}")

                                    # Stay in NEGOTIATING state
                                else:
                                    log("Failed to adjust proposal", "ERROR")

            # STATE: AGREED
            elif state == "AGREED":
                log("Waiting for next objective...")
                state = "WAITING_OBJECTIVE"
                current_objective = None
                current_proposal = None
                negotiation_rounds = 0

            # Poll interval
            time.sleep(POLL_INTERVAL)

        except KeyboardInterrupt:
            log("Shutting down...", "WARN")
            break
        except Exception as e:
            log(f"Error in main loop: {e}", "ERROR")
            import traceback
            traceback.print_exc()
            time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    # Ensure directories exist
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    PM_DIR.mkdir(parents=True, exist_ok=True)
    DEV_DIR.mkdir(parents=True, exist_ok=True)

    main_loop()
