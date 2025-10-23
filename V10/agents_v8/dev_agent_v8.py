#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dev Agent V8 - Independent Process
===================================

Dev Agent (Alex) como proceso independiente que:
1. Lee propuestas de PM (.shared/pm/proposal_*.json)
2. Evalúa factibilidad técnica
3. Puede counter-proponer si detecta issues
4. O acepta y genera código
5. Mejora código basado en feedback de validación

Comunicación: Filesystem-based via .shared/
"""

import sys
import time
import json
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional, List

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from protocols.message_types import (
    ProposalMessage,
    EvaluationMessage,
    ImplementationMessage,
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
WORKSPACE = PROJECT_ROOT / "workspace" / "v8_projects"

POLL_INTERVAL = 5  # segundos
CLAUDE_TIMEOUT = 300  # 5 minutos
MAX_COUNTER_PROPOSALS = 3

WORKSPACE.mkdir(parents=True, exist_ok=True)


def log(message: str, level: str = "INFO"):
    """Log con timestamp"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] [Dev Agent] [{level}] {message}")


def execute_claude(prompt: str, timeout: int = CLAUDE_TIMEOUT) -> Optional[Dict]:
    """
    File Communicator Pattern - NO subprocess execution.

    Escribe prompt a archivo y espera respuesta del humano/Claude en otro terminal.
    """
    import uuid

    session_uuid = str(uuid.uuid4())[:8]

    # Usar .agents/dev/ para file communication
    agent_dir = PROJECT_ROOT / ".agents" / "dev"
    inbox_dir = agent_dir / "inbox"
    outbox_dir = agent_dir / "outbox"

    inbox_dir.mkdir(parents=True, exist_ok=True)
    outbox_dir.mkdir(parents=True, exist_ok=True)

    prompt_file = inbox_dir / f"prompt_{session_uuid}.txt"
    response_file = outbox_dir / f"response_{session_uuid}.json"

    try:
        log(f"📝 Escribiendo prompt para humano (session: {session_uuid})...")

        # Escribir prompt para humano
        prompt_file.write_text(prompt, encoding='utf-8')

        # Verify write
        written_size = prompt_file.stat().st_size
        log(f"✅ Prompt escrito: {prompt_file.name} ({written_size} bytes)", "SUCCESS")
        log(f"⏳ Esperando respuesta en: {response_file.name}", "INFO")
        log(f"", "INFO")  # Blank line
        log(f"🔔 ACCIÓN REQUERIDA:", "INFO")
        log(f"   Terminal Claude: Lee {prompt_file}", "INFO")
        log(f"   Terminal Claude: Escribe {response_file}", "INFO")
        log(f"", "INFO")  # Blank line

        # ESPERAR respuesta del humano (polling)
        wait_start = time.time()
        last_log_time = 0

        while not response_file.exists():
            elapsed = time.time() - wait_start

            if elapsed > timeout:
                log(f"⏱️ Timeout ({timeout}s) esperando respuesta humana", "ERROR")
                log(f"📁 Se esperaba: {response_file}", "ERROR")
                return None

            # Log cada 30 segundos
            if int(elapsed) - last_log_time >= 30:
                log(f"Aún esperando respuesta... ({int(elapsed)}s transcurridos)", "INFO")
                last_log_time = int(elapsed)

            time.sleep(2)  # Poll cada 2 segundos

        # Leer respuesta
        log(f"✅ Respuesta recibida! Leyendo...", "SUCCESS")
        response_text = response_file.read_text(encoding='utf-8')

        if not response_text.strip():
            log("❌ Response file vacía", "ERROR")
            return None

        # Parse JSON directo (no Claude CLI format)
        data = json.loads(response_text)

        log("✅ JSON parseado correctamente", "SUCCESS")
        return data

    except json.JSONDecodeError as e:
        log(f"❌ Error parseando JSON: {e}", "ERROR")
        log(f"Contenido del archivo: {response_text[:200]}...", "DEBUG")
        return None
    except Exception as e:
        log(f"❌ Error en file communicator: {e}", "ERROR")
        import traceback
        traceback.print_exc()
        return None


def evaluate_architecture(proposal: Dict, iteration: int) -> Optional[EvaluationMessage]:
    """
    Evalúa arquitectura propuesta por PM y decide si counter-proponer.
    """
    prompt = f"""Eres Dev Agent (Alex), desarrollador Python senior con 15 años de experiencia.

PROPUESTA DE ARQUITECTURA DEL PM:
{json.dumps(proposal, indent=2)}

TU TAREA - EVALUACIÓN TÉCNICA:
1. Analiza la factibilidad técnica de cada módulo
2. Detecta problemas potenciales:
   - Dependencias circulares
   - Complejidad excesiva
   - Arquitectura sub-óptima
   - Missing componentes críticos
   - Performance bottlenecks
3. Decide si aceptar o counter-proponer

CRITERIOS PARA COUNTER-PROPOSAL:
- Issues CRÍTICOS que impedirían implementación
- Dependencias circulares
- Arquitectura claramente deficiente
- Missing componentes esenciales

RESPONDE EN FORMATO JSON:

{{
  "role": "dev",
  "action": "ACCEPT" | "COUNTER",
  "concerns": [
    "Concern 1: detailed description",
    "Concern 2: detailed description"
  ],
  "alternative_architecture": {{
    "proposed_modules": [...],
    "reasoning": "why this is better"
  }},
  "reasoning": "why accepting or counter-proposing"
}}

IMPORTANTE:
- Si arquitectura es viable: "action": "ACCEPT" (incluso si tiene minor issues)
- Solo "COUNTER" si hay issues CRÍTICOS
- Sé específico en concerns
- Responde SOLO JSON
"""

    log(f"Iteration {iteration}: Evaluating PM architecture...")

    result = execute_claude(prompt)

    if not result:
        log("Failed to evaluate architecture", "ERROR")
        return None

    action = result.get("action", "ACCEPT")
    concerns = result.get("concerns", [])

    evaluation = EvaluationMessage(
        action=action,
        concerns=concerns,
        iteration=iteration,
        alternative_architecture=result.get("alternative_architecture"),
        reasoning=result.get("reasoning", "")
    )

    log(f"Evaluation: {action} ({len(concerns)} concerns)", "SUCCESS")

    return evaluation


def generate_code(
    objective: str,
    architecture: Dict,
    iteration: int
) -> Optional[ImplementationMessage]:
    """
    Genera código completo basado en arquitectura aprobada.

    Reutiliza estrategia de V7 con single-batch para simplificar POC.
    """
    output_dir = WORKSPACE / f"project_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    modules = architecture.get("proposed_modules", [])

    prompt = f"""Eres Dev Agent (Alex), desarrollador Python senior.

OBJETIVO:
{objective}

ARQUITECTURA APROBADA (acordada con PM):
{json.dumps(architecture, indent=2)}

TU TAREA:
1. Genera TODOS los módulos propuestos
2. Código 100% FUNCIONAL (NO TODOs, NO placeholders)
3. Cada módulo: docstrings, type hints, error handling, logging
4. Tests unitarios para CADA módulo
5. requirements.txt, README.md, docker-compose.yml
6. Si BD: alembic migrations

IMPORTANTE - NO INTENTES ESCRIBIR ARCHIVOS:
- Retorna TODO el código como strings en JSON

RESPONDE JSON CON TODO EL CÓDIGO:

{{
  "role": "dev",
  "status": "implemented",
  "output_dir": "{output_dir}",
  "files": [
    {{"path": "src/__init__.py", "content": "..."}},
    {{"path": "src/module1.py", "content": "..."}},
    {{"path": "tests/test_module1.py", "content": "..."}},
    {{"path": "requirements.txt", "content": "..."}},
    {{"path": "README.md", "content": "..."}}
  ]
}}

Responde SOLO JSON.
"""

    log(f"Iteration {iteration}: Generating code for {len(modules)} modules...")

    result = execute_claude(prompt, timeout=CLAUDE_TIMEOUT)

    if not result:
        log("Failed to generate code", "ERROR")
        return None

    files = result.get("files", [])

    if not files:
        log("No files generated", "ERROR")
        return None

    # Write files to disk
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    files_written = 0
    for file_info in files:
        file_path = file_info.get("path")
        file_content = file_info.get("content")

        if not file_path or file_content is None:
            continue

        full_path = output_path / file_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(file_content, encoding='utf-8')
        files_written += 1

    log(f"Written {files_written} files to {output_dir}", "SUCCESS")

    implementation = ImplementationMessage(
        status="implemented",
        output_dir=str(output_dir),
        files=files,
        iteration=iteration
    )

    return implementation


def improve_code(
    output_dir: str,
    feedback: Dict,
    iteration: int
) -> Optional[ImplementationMessage]:
    """
    Mejora código basado en feedback de validación.
    """
    security_issues = feedback.get("security_issues", [])
    qa_issues = feedback.get("qa_issues", [])

    prompt = f"""Eres Dev Agent (Alex). MEJORA el código basado en feedback de validación.

DIRECTORIO DEL PROYECTO:
{output_dir}

FEEDBACK DE VALIDACIÓN (Iteración {iteration}):
- Security issues: {len(security_issues)}
- QA issues: {len(qa_issues)}

ISSUES CRÍTICOS:
{json.dumps(feedback.get('critical_issues', [])[:10], indent=2)}

HIGH PRIORITY:
{json.dumps(feedback.get('high_priority', [])[:10], indent=2)}

TU TAREA:
1. Analiza el código existente en {output_dir}
2. Genera versiones MEJORADAS de los archivos que necesitan cambios
3. FIX TODOS los issues críticos
4. FIX los high priority
5. Asegura tests pasan al 100%

IMPORTANTE - NO INTENTES ESCRIBIR ARCHIVOS:
- Retorna archivos modificados como strings en JSON

RESPONDE JSON CON ARCHIVOS MEJORADOS:

{{
  "role": "dev",
  "status": "improved",
  "output_dir": "{output_dir}",
  "files": [
    {{
      "path": "src/module_modificado.py",
      "content": "# código mejorado completo..."
    }}
  ],
  "fixes_applied": ["fix1", "fix2", ...],
  "notes": "resumen de mejoras"
}}

Responde SOLO JSON.
"""

    log(f"Iteration {iteration}: Improving code based on validation feedback...")

    result = execute_claude(prompt, timeout=CLAUDE_TIMEOUT)

    if not result:
        log("Failed to improve code", "ERROR")
        return None

    files = result.get("files", [])

    # Write improved files
    output_path = Path(output_dir)

    files_written = 0
    for file_info in files:
        file_path = file_info.get("path")
        file_content = file_info.get("content")

        if not file_path or file_content is None:
            continue

        full_path = output_path / file_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(file_content, encoding='utf-8')
        files_written += 1

    log(f"Improved {files_written} files in {output_dir}", "SUCCESS")

    implementation = ImplementationMessage(
        status="improved",
        output_dir=output_dir,
        files=files,
        iteration=iteration,
        fixes_applied=result.get("fixes_applied", []),
        notes=result.get("notes", "")
    )

    return implementation


def main_loop():
    """
    Loop principal del Dev Agent.

    Estados:
    1. WAITING_PROPOSAL: Esperando propuesta de PM
    2. EVALUATING: Evaluando arquitectura
    3. IMPLEMENTING: Generando código
    4. WAITING_FEEDBACK: Esperando feedback de validación
    5. IMPROVING: Mejorando código
    """
    log("Dev Agent V8 started")
    log(f"Watching: {PM_DIR}")
    log(f"Output to: {DEV_DIR}")

    state = "WAITING_PROPOSAL"
    current_iteration = 0
    current_objective = None
    current_proposal = None
    current_output_dir = None
    counter_proposals_count = 0
    last_processed_proposal = None

    while True:
        try:
            # STATE: WAITING_PROPOSAL
            if state == "WAITING_PROPOSAL":
                # Look for latest proposal
                proposal_files = sorted(PM_DIR.glob("proposal_*.json"))

                if proposal_files:
                    latest_proposal = proposal_files[-1]

                    # Skip if already processed
                    if latest_proposal == last_processed_proposal:
                        time.sleep(POLL_INTERVAL)
                        continue

                    proposal_data = read_message(latest_proposal)

                    if proposal_data:
                        current_proposal = proposal_data.get("architecture", {})
                        current_iteration = proposal_data.get("iteration", 1)
                        action = proposal_data.get("action", "PROPOSE")

                        log(f"New proposal received: iteration {current_iteration}, action={action}")

                        # Read objective
                        objective_file = STATE_DIR / "objective.json"
                        if objective_file.exists():
                            obj_data = read_message(objective_file)
                            current_objective = obj_data.get("objective", "")

                        last_processed_proposal = latest_proposal
                        state = "EVALUATING"

            # STATE: EVALUATING
            elif state == "EVALUATING":
                evaluation = evaluate_architecture(current_proposal, current_iteration)

                if evaluation:
                    # Write evaluation
                    eval_file = DEV_DIR / f"evaluation_{current_iteration:03d}.json"
                    write_message(evaluation, eval_file)

                    log(f"Evaluation written to {eval_file.name}")

                    if evaluation.action == "ACCEPT":
                        state = "IMPLEMENTING"
                    elif evaluation.action == "COUNTER":
                        counter_proposals_count += 1

                        if counter_proposals_count >= MAX_COUNTER_PROPOSALS:
                            log(f"Max counter-proposals ({MAX_COUNTER_PROPOSALS}) reached, accepting", "WARN")
                            state = "IMPLEMENTING"
                        else:
                            # Wait for PM adjustment
                            state = "WAITING_PROPOSAL"
                else:
                    log("Failed to evaluate, retrying...", "ERROR")
                    time.sleep(POLL_INTERVAL)

            # STATE: IMPLEMENTING
            elif state == "IMPLEMENTING":
                implementation = generate_code(
                    current_objective,
                    current_proposal,
                    current_iteration
                )

                if implementation:
                    # Write implementation
                    impl_file = DEV_DIR / f"implementation_{current_iteration:03d}.json"
                    write_message(implementation, impl_file)

                    current_output_dir = implementation.output_dir
                    log(f"Implementation written to {impl_file.name}")
                    log(f"Code generated in: {current_output_dir}")

                    state = "WAITING_FEEDBACK"
                else:
                    log("Failed to generate code, retrying...", "ERROR")
                    time.sleep(POLL_INTERVAL)

            # STATE: WAITING_FEEDBACK
            elif state == "WAITING_FEEDBACK":
                feedback_file = STATE_DIR / "validation_feedback.json"

                if feedback_file.exists():
                    feedback_data = read_message(feedback_file)

                    if feedback_data:
                        security_score = feedback_data.get("security_score", 0)
                        qa_score = feedback_data.get("qa_score", 0)

                        log(f"Validation feedback: Security={security_score:.1f}, QA={qa_score:.1f}")

                        if security_score >= 9.5 and qa_score >= 9.5:
                            log("Validation passed! Waiting for next objective...", "SUCCESS")
                            state = "WAITING_PROPOSAL"
                            current_objective = None
                            current_proposal = None
                            current_output_dir = None
                            counter_proposals_count = 0
                        else:
                            log("Validation failed, improving code...")
                            state = "IMPROVING"

            # STATE: IMPROVING
            elif state == "IMPROVING":
                feedback_file = STATE_DIR / "validation_feedback.json"
                feedback_data = read_message(feedback_file)

                if feedback_data and current_output_dir:
                    current_iteration += 1

                    improved = improve_code(
                        current_output_dir,
                        feedback_data,
                        current_iteration
                    )

                    if improved:
                        # Write improved implementation
                        impl_file = DEV_DIR / f"implementation_{current_iteration:03d}.json"
                        write_message(improved, impl_file)

                        log(f"Improved code written to {impl_file.name}")

                        # Delete feedback file to signal processing done
                        feedback_file.unlink()

                        state = "WAITING_FEEDBACK"
                    else:
                        log("Failed to improve code, retrying...", "ERROR")
                        time.sleep(POLL_INTERVAL)

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
    WORKSPACE.mkdir(parents=True, exist_ok=True)

    main_loop()
