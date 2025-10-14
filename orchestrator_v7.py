#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Orchestrator V7 - Claude Real Multi-Agente
==========================================

Discovery Motor V7 combina:
- Coordinación robusta de V5 ✅
- Inteligencia real de Claude (PM + Dev) 🧠
- Validación enterprise (Security + QA) 🔒
- Performance tracking integrado 📊

ARQUITECTURA:
- PM Agent: Claude via `claude --print` (razonamiento arquitectónico)
- Dev Agent: Claude via `claude --print` (generación código adaptativo)
- Security Agent: Python rules (OWASP + Bandit) - de V5
- QA Agent: Python rules (pytest + coverage) - de V5
- Orchestrator: Python coordina todo

WORKFLOW:
1. Usuario ingresa objetivo
2. ITERACIÓN 1:
   a. PM Agent (Claude) propone arquitectura
   b. Dev Agent (Claude) implementa código
   c. Security + QA validan
   d. Si scores < 9.5: feedback a Dev
3. ITERACIÓN 2+:
   a. Dev Agent (Claude) mejora basado en feedback
   b. Security + QA validan
   c. Si scores >= 9.5: CONVERGENCIA ✅
   d. Else: repeat
4. Safety: Max 10 iteraciones
5. Git commit + métricas

DIFERENCIAS CON V5:
- PM y Dev usan CLAUDE REAL (no templates)
- Código más adaptativo y específico al objetivo
- Convergencia más rápida (esperado: 3-5 iteraciones vs 5-8)

DIFERENCIAS CON V6:
- SÍ usa claude --print (funciona, probado)
- NO usa subprocess interactivo (no funciona)
- Mantiene filesystem communication simple
"""

import sys
import subprocess
import json
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional, List

# Reutilizar de V5 (funcionan perfectamente)
from shared_utils import log, cleanup_stale_locks, cleanup_old_messages
from dialogue_logger import get_logger
from git_workflow import init_project_repo, commit_phase, create_phase_tag
from performance_tracker import tracked_operation, get_tracker

# Importar validation_utils_v4 si existe
try:
    from validation_utils_v4 import SecurityValidator, QAValidator
    VALIDATORS_AVAILABLE = True
except ImportError:
    VALIDATORS_AVAILABLE = False
    log("orchestrator", "validation_utils_v4 no encontrado, usando fallback", "WARN")


ROLE = "orchestrator_v7"
PROJECT_ROOT = Path(__file__).parent
WORKSPACE = PROJECT_ROOT / "workspace" / "v7_projects"
WORKSPACE.mkdir(parents=True, exist_ok=True)

# V7 Configuration
MAX_ITERATIONS = 10
MIN_SECURITY_SCORE = 9.5
MIN_QA_SCORE = 9.5
CLAUDE_TIMEOUT_PM = 180  # 3 minutos para PM
CLAUDE_TIMEOUT_DEV = 300  # 5 minutos para Dev

# Token estimation constants (rough heuristics)
TOKEN_LIMIT = 32000  # Claude's hard limit
TOKEN_SAFETY_MARGIN = 0.7  # Use only 70% of limit for safety
EFFECTIVE_TOKEN_LIMIT = int(TOKEN_LIMIT * TOKEN_SAFETY_MARGIN)  # 22,400 tokens

# Token estimation heuristics (tokens per item)
TOKENS_PER_CHAR = 0.25  # Rough: 1 token ~= 4 chars
TOKENS_PER_MODULE = 1200  # Average module generation
TOKENS_PER_TEST = 1500  # Average test file (complete)
TOKENS_PER_TEST_SKELETON = 200  # Skeleton test
TOKENS_README = 2000
TOKENS_DOCKER = 800
TOKENS_BASE_PROMPT = 5000
TOKENS_ARCHITECTURE_JSON = 3000


def estimate_tokens(text: str) -> int:
    """
    Estima tokens en un texto usando heurística simple.

    Aproximación: 1 token ~= 4 caracteres (para inglés/código)
    """
    return int(len(text) * TOKENS_PER_CHAR)


def estimate_batch_tokens(
    num_modules: int = 0,
    num_tests: int = 0,
    num_test_skeletons: int = 0,
    include_readme: bool = False,
    include_docker: bool = False,
    architecture_json: str = ""
) -> int:
    """
    Estima total de tokens para un batch.

    Returns:
        Estimación de tokens totales
    """
    total = TOKENS_BASE_PROMPT

    if architecture_json:
        total += estimate_tokens(architecture_json)
    else:
        total += TOKENS_ARCHITECTURE_JSON  # Default

    total += num_modules * TOKENS_PER_MODULE
    total += num_tests * TOKENS_PER_TEST
    total += num_test_skeletons * TOKENS_PER_TEST_SKELETON

    if include_readme:
        total += TOKENS_README

    if include_docker:
        total += TOKENS_DOCKER

    return total


def determine_batch_strategy(modules: List[str], architecture: Dict) -> str:
    """
    Determina estrategia de batching óptima basada en estimación de tokens.

    Returns:
        "single" | "3-batch" | "4-batch"
    """
    num_modules = len(modules)
    arch_json = json.dumps(architecture, indent=2)

    # Estimar tokens para generación completa en 1 batch
    single_batch_tokens = estimate_batch_tokens(
        num_modules=num_modules,
        num_tests=num_modules,
        include_readme=True,
        include_docker=True,
        architecture_json=arch_json
    )

    log(ROLE, f"Estimación single-batch: {single_batch_tokens} tokens", "INFO")

    # Si cabe en 1 batch con margen, usarlo
    if single_batch_tokens < EFFECTIVE_TOKEN_LIMIT:
        log(ROLE, f"Usando single-batch (dentro de {EFFECTIVE_TOKEN_LIMIT} tokens)", "SUCCESS")
        return "single"

    # Estimar 3-batch strategy
    batch1_tokens = estimate_batch_tokens(
        num_modules=min(4, num_modules),
        architecture_json=arch_json
    )

    batch2_tokens = estimate_batch_tokens(
        num_modules=max(0, num_modules - 4),
        include_readme=True
    )

    batch3_tokens = estimate_batch_tokens(
        num_tests=num_modules,
        include_docker=True,
        architecture_json=arch_json
    )

    max_3batch = max(batch1_tokens, batch2_tokens, batch3_tokens)
    log(ROLE, f"Estimación 3-batch max: {max_3batch} tokens", "INFO")

    if max_3batch < EFFECTIVE_TOKEN_LIMIT:
        log(ROLE, f"Usando 3-batch (max {max_3batch} < {EFFECTIVE_TOKEN_LIMIT})", "SUCCESS")
        return "3-batch"

    # Si 3-batch no cabe, usar 4-batch
    batch4_tokens = estimate_batch_tokens(
        num_tests=num_modules,
        architecture_json=arch_json
    )

    batch3_skel_tokens = estimate_batch_tokens(
        num_test_skeletons=num_modules,
        num_modules=max(0, num_modules - 6),
        include_docker=True
    )

    max_4batch = max(batch1_tokens, batch2_tokens, batch3_skel_tokens, batch4_tokens)
    log(ROLE, f"Estimación 4-batch max: {max_4batch} tokens", "INFO")

    if max_4batch < EFFECTIVE_TOKEN_LIMIT:
        log(ROLE, f"Usando 4-batch (max {max_4batch} < {EFFECTIVE_TOKEN_LIMIT})", "SUCCESS")
        return "4-batch"

    # Fallback: usar 4-batch y cruzar dedos
    log(ROLE, f"WARNING: Incluso 4-batch está cerca del límite ({max_4batch} tokens)", "WARN")
    log(ROLE, "Usando 4-batch como mejor opción disponible", "WARN")
    return "4-batch"


def display_header():
    """Display V7 header"""
    print()
    print("=" * 80)
    print("DISCOVERY MOTOR V7 - Claude Real Multi-Agente")
    print("=" * 80)
    print(f"Target: Security >= {MIN_SECURITY_SCORE}, QA >= {MIN_QA_SCORE}")
    print(f"Max iterations: {MAX_ITERATIONS}")
    print(f"Workspace: {WORKSPACE}")
    print("=" * 80)
    print()


def execute_claude_agent(role: str, prompt: str, timeout: int = 120) -> Dict:
    """
    Ejecutar Claude como agente via FILESYSTEM COMMUNICATION.

    MÉTODO QUE YA FUNCIONA (probado):
    1. Escribir prompt en .agents/{role}/inbox/prompt.txt
    2. Ejecutar: cat prompt.txt | claude --print --output-format json > response.json
    3. Leer .agents/{role}/outbox/response.json
    4. Parsear y retornar

    Args:
        role: "pm" o "dev" (para logging)
        prompt: Prompt especializado para el rol
        timeout: Segundos máximo de espera

    Returns:
        {
            "success": bool,
            "response": dict,  # JSON parseado de Claude
            "error": str,      # Si hubo error
            "duration_sec": float
        }
    """
    start_time = time.time()

    # Directorios de comunicación
    agent_dir = PROJECT_ROOT / ".agents" / role
    inbox_dir = agent_dir / "inbox"
    outbox_dir = agent_dir / "outbox"

    inbox_dir.mkdir(parents=True, exist_ok=True)
    outbox_dir.mkdir(parents=True, exist_ok=True)

    prompt_file = inbox_dir / "prompt.txt"
    response_file = outbox_dir / "response.json"

    # Limpiar respuesta anterior si existe
    if response_file.exists():
        try:
            response_file.unlink()
        except PermissionError:
            # Archivo en uso por otro proceso - intentar renombrar
            import random
            backup_name = f"response_backup_{random.randint(1000,9999)}.json"
            try:
                response_file.rename(response_file.parent / backup_name)
            except:
                pass  # Si falla, continuar de todos modos

    try:
        log(ROLE, f"Ejecutando Claude Agent ({role}) via filesystem...", "INFO")

        # 1. Escribir prompt
        prompt_file.write_text(prompt, encoding='utf-8')

        # 2. Ejecutar claude --print (usando stdin cross-platform)
        # FIX V7.10: Portabilidad Linux/macOS/Windows - No usar comando shell
        # FIX V7.10b: Windows necesita shell=True para encontrar .cmd en PATH
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
                    shell=True  # Necesario en Windows para encontrar .cmd en PATH
                )

        # 3. Esperar a que aparezca response.json
        wait_start = time.time()
        while not response_file.exists():
            if time.time() - wait_start > 10:  # Max 10s esperando el archivo
                return {
                    "success": False,
                    "error": "Response file not created",
                    "duration_sec": time.time() - start_time
                }
            time.sleep(0.5)

        # 4. Leer respuesta
        response_text = response_file.read_text(encoding='utf-8')

        if not response_text.strip():
            return {
                "success": False,
                "error": "Empty response from Claude",
                "duration_sec": time.time() - start_time
            }

        # 5. Parsear JSON
        try:
            data = json.loads(response_text)
        except json.JSONDecodeError as e:
            log(ROLE, f"JSON parse error: {e}", "ERROR")
            return {
                "success": False,
                "error": f"Invalid JSON: {e}",
                "duration_sec": time.time() - start_time
            }

        # 6. Extraer resultado
        if data.get("type") != "result":
            return {
                "success": False,
                "error": f"Unexpected type: {data.get('type')}",
                "duration_sec": time.time() - start_time
            }

        result_text = data.get("result", "")

        # Intentar extraer JSON del resultado - MÚLTIPLES ESTRATEGIAS

        # Estrategia 1: Bloque ```json
        if "```json" in result_text:
            try:
                json_str = result_text.split("```json")[1].split("```")[0].strip()
                parsed = json.loads(json_str)

                duration = time.time() - start_time
                log(ROLE, f"Claude Agent ({role}) respondió en {duration:.1f}s", "SUCCESS")

                return {
                    "success": True,
                    "response": parsed,
                    "raw": result_text,
                    "duration_sec": duration
                }
            except (IndexError, json.JSONDecodeError) as e:
                log(ROLE, f"Fallo extracción ```json: {e}", "WARN")
                # Continuar a estrategia 2

        # Estrategia 2: JSON puro (sin markdown)
        try:
            parsed = json.loads(result_text)

            duration = time.time() - start_time
            log(ROLE, f"Claude Agent ({role}) respondió con JSON puro en {duration:.1f}s", "SUCCESS")

            return {
                "success": True,
                "response": parsed,
                "raw": result_text,
                "duration_sec": duration
            }
        except json.JSONDecodeError as e:
            log(ROLE, f"No es JSON puro: {e}", "WARN")
            # Continuar a estrategia 3

        # Estrategia 3: Buscar primer objeto JSON en el texto
        try:
            # Buscar inicio de objeto JSON
            start_idx = result_text.find('{')
            if start_idx != -1:
                # Intentar parsear desde ese punto
                json_str = result_text[start_idx:]
                parsed = json.loads(json_str)

                duration = time.time() - start_time
                log(ROLE, f"Claude Agent ({role}) respondió con JSON embedded en {duration:.1f}s", "SUCCESS")

                return {
                    "success": True,
                    "response": parsed,
                    "raw": result_text,
                    "duration_sec": duration
                }
        except json.JSONDecodeError as e:
            log(ROLE, f"No se pudo extraer JSON embedded: {e}", "WARN")

        # Estrategia 4: FALLO - retornar error en lugar de success=True
        log(ROLE, "No se pudo parsear JSON de ninguna forma", "ERROR")
        return {
            "success": False,
            "error": "No valid JSON found in response",
            "raw": result_text,
            "duration_sec": time.time() - start_time
        }

    except subprocess.TimeoutExpired:
        duration = time.time() - start_time
        log(ROLE, f"Claude timeout after {timeout}s", "ERROR")
        return {
            "success": False,
            "error": f"Timeout after {timeout}s",
            "duration_sec": duration
        }

    except Exception as e:
        duration = time.time() - start_time
        log(ROLE, f"Error ejecutando Claude: {e}", "ERROR")
        return {
            "success": False,
            "error": str(e),
            "duration_sec": duration
        }


def request_pm_architecture(objective: str, iteration: int, tracker=None) -> Optional[Dict]:
    """
    PM Agent propone arquitectura usando Claude REAL.

    Este es uno de los dos cambios clave de V7:
    PM ahora usa inteligencia de Claude para razonar arquitectura,
    no templates predefinidos.
    """

    task_id = f"v7_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    prompt = f"""Eres PM Agent (Morgan), arquitecto de software senior.

OBJETIVO DEL USUARIO:
{objective}

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

    log(ROLE, f"Iteración {iteration}: Solicitando arquitectura a PM Agent (Claude)...")

    if tracker:
        ctx = tracked_operation("pm.architecture_proposal", ROLE, task_id)
        ctx.__enter__()

    result = execute_claude_agent("pm", prompt, timeout=CLAUDE_TIMEOUT_PM)

    if tracker:
        ctx.__exit__(None, None, None)

    if not result["success"]:
        log(ROLE, f"PM Agent falló: {result['error']}", "ERROR")
        return None

    architecture = result.get("response", {})

    # Validar que tenga campos esperados
    if not architecture.get("proposed_modules"):
        log(ROLE, "PM no retornó proposed_modules", "WARN")
        return None

    modules_count = len(architecture.get("proposed_modules", []))
    log(ROLE, f"PM propuso {modules_count} módulos", "SUCCESS")

    return architecture


def request_dev_implementation(
    objective: str,
    architecture: Dict,
    iteration: int,
    feedback: Optional[Dict] = None,
    tracker=None,
    existing_project_dir: Optional[str] = None  # FIX: Pasar directorio existente
) -> Optional[Dict]:
    """
    Dev Agent implementa código usando Claude REAL con BATCH GENERATION.

    CAMBIO V7.3: Divide módulos en 4 batches para evitar token limit (32K).
    - Batch 1: Primeros 3 módulos + configs (~12K tokens)
    - Batch 2: Siguientes 3 módulos + README (~10K tokens)
    - Batch 3: Test skeletons + docker (~8K tokens)
    - Batch 4: Implement tests completos (~15K tokens)

    FIX V7.8: En iteraciones 2+, reutiliza proyecto de iteración 1.
    """

    task_id = f"v7_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    # FIX: En iteraciones 2+, usar directorio existente en lugar de crear uno nuevo
    if iteration > 1 and existing_project_dir:
        output_dir = Path(existing_project_dir)
        log(ROLE, f"Iteración {iteration}: Reutilizando proyecto {output_dir}", "INFO")
    else:
        output_dir = WORKSPACE / f"project_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        log(ROLE, f"Iteración {iteration}: Creando nuevo proyecto {output_dir}", "INFO")

    modules = architecture.get("proposed_modules", [])

    # BATCH GENERATION V7.4: Usar pre-flight token estimation
    if iteration == 1:
        batch_strategy = determine_batch_strategy(modules, architecture)
    else:
        batch_strategy = "single"  # Iteraciones 2+ usan single batch (mejoras)

    # 4-BATCH STRATEGY
    if batch_strategy == "4-batch" and iteration == 1:
        log(ROLE, f"Generando {len(modules)} módulos en 4 batches para evitar token limit", "INFO")

        batch1_modules = modules[:3]
        batch2_modules = modules[3:6]
        remaining_modules = modules[6:]

        # === BATCH 1: Primeros 3 módulos + configs ===
        prompt_batch1 = f"""Eres Dev Agent (Alex), desarrollador Python senior.

OBJETIVO:
{objective}

ARQUITECTURA APROBADA (PM Agent):
{json.dumps(architecture, indent=2)}

TU TAREA - BATCH 1/4:
Genera SOLO estos módulos CORE:
{json.dumps(batch1_modules, indent=2)}

Y TAMBIÉN:
- src/__init__.py (imports de módulos)
- requirements.txt (con TODAS las dependencias del proyecto completo)
- .env.example (variables necesarias)

Código 100% FUNCIONAL (NO TODOs, NO placeholders).

IMPORTANTE - NO INTENTES ESCRIBIR ARCHIVOS:
- NO uses Write tool, Bash tool, subprocess
- Retorna TODO el código como strings en JSON

RESPONDE JSON CON TODO EL CÓDIGO:
{{
  "role": "dev",
  "status": "batch1",
  "batch": 1,
  "output_dir": "{output_dir}",
  "files": [
    {{"path": "src/__init__.py", "content": "..."}},
    {{"path": "src/{batch1_modules[0] if batch1_modules else 'module.py'}", "content": "código completo..."}},
    {{"path": "requirements.txt", "content": "..."}},
    {{"path": ".env.example", "content": "..."}}
  ]
}}

Responde SOLO JSON."""

        log(ROLE, "Batch 1/4: Generando primeros 3 módulos + configs...", "INFO")
        result1 = execute_claude_agent("dev", prompt_batch1, timeout=CLAUDE_TIMEOUT_DEV)

        if not result1["success"]:
            log(ROLE, f"Batch 1 falló: {result1['error']}", "ERROR")
            return None

        batch1_files = result1.get("response", {}).get("files", [])
        log(ROLE, f"Batch 1: {len(batch1_files)} archivos generados", "SUCCESS")

        # === BATCH 2: Siguientes 3 módulos + README ===
        prompt_batch2 = f"""Eres Dev Agent (Alex), desarrollador Python senior.

OBJETIVO:
{objective}

ARQUITECTURA APROBADA (PM Agent):
{json.dumps(architecture, indent=2)}

TU TAREA - BATCH 2/4:
Genera SOLO estos módulos:
{json.dumps(batch2_modules, indent=2)}

Y TAMBIÉN:
- README.md (setup instructions, architecture, usage examples)
- alembic/versions/001_initial.py (si hay BD en arquitectura)

NO generes tests aún (van en Batch 3/4).

Código 100% FUNCIONAL (NO TODOs, NO placeholders).

IMPORTANTE - NO INTENTES ESCRIBIR ARCHIVOS:
- NO uses Write tool, Bash tool, subprocess
- Retorna TODO el código como strings en JSON

RESPONDE JSON CON TODO EL CÓDIGO:
{{
  "role": "dev",
  "status": "batch2",
  "batch": 2,
  "output_dir": "{output_dir}",
  "files": [
    {{"path": "src/{batch2_modules[0] if batch2_modules else 'module.py'}", "content": "código completo..."}},
    {{"path": "README.md", "content": "..."}},
    {{"path": "alembic/versions/001_initial.py", "content": "..."}}
  ]
}}

Responde SOLO JSON."""

        log(ROLE, "Batch 2/4: Generando módulos 4-6 + README...", "INFO")
        result2 = execute_claude_agent("dev", prompt_batch2, timeout=CLAUDE_TIMEOUT_DEV)

        if not result2["success"]:
            log(ROLE, f"Batch 2 falló: {result2['error']}", "ERROR")
            log(ROLE, "Guardando progreso parcial: Batch 1 completado", "WARN")
            # FIX V7.9: No perder Batch 1, continuar con progreso parcial
            batch2_files = []
            all_files = batch1_files
            # Skip Batches 3 y 4, ir directo a escribir archivos
        else:
            batch2_files = result2.get("response", {}).get("files", [])
            log(ROLE, f"Batch 2: {len(batch2_files)} archivos generados", "SUCCESS")

            # === BATCH 3: Módulos restantes + Test Skeletons + Docker ===
            # SOLO ejecutar si Batch 2 fue exitoso
            all_modules_list = json.dumps(modules, indent=2)
            prompt_batch3 = f"""Eres Dev Agent (Alex), desarrollador Python senior.

OBJETIVO:
{objective}

ARQUITECTURA APROBADA (PM Agent):
{json.dumps(architecture, indent=2)}

TU TAREA - BATCH 3/4:
Genera módulos restantes (si hay) + test skeletons + docker.

MÓDULOS RESTANTES:
{json.dumps(remaining_modules, indent=2)}

MÓDULOS YA GENERADOS (en batches 1 y 2):
{json.dumps(modules[:6], indent=2)}

GENERA:
1. Módulos restantes (si hay en lista MÓDULOS RESTANTES)
2. tests/__init__.py
3. test_*.py para CADA módulo (SOLO SKELETONS con TODOs):
   ```python
   import pytest

   def test_module_initialization():
       # TODO: Implement test
       pass

   def test_core_functionality():
       # TODO: Implement test
       pass
   ```
4. docker-compose.yml (servicios necesarios: app, DB, Redis, etc)
5. Dockerfile (si necesario para deployment)

Código 100% FUNCIONAL (NO TODOs en módulos, SÍ TODOs en tests).

IMPORTANTE - NO INTENTES ESCRIBIR ARCHIVOS:
- NO uses Write tool, Bash tool, subprocess
- Retorna TODO el código como strings en JSON

RESPONDE JSON CON TODO EL CÓDIGO:
{{
  "role": "dev",
  "status": "batch3",
  "batch": 3,
  "output_dir": "{output_dir}",
  "files": [
    {{"path": "tests/__init__.py", "content": "..."}},
    {{"path": "tests/test_module1.py", "content": "skeleton con TODOs..."}},
    {{"path": "docker-compose.yml", "content": "..."}},
    {{"path": "Dockerfile", "content": "..."}}
  ]
}}

Responde SOLO JSON."""

        log(ROLE, "Batch 3/4: Generando test skeletons + docker...", "INFO")
        result3 = execute_claude_agent("dev", prompt_batch3, timeout=CLAUDE_TIMEOUT_DEV)

        if not result3["success"]:
            log(ROLE, f"Batch 3 falló: {result3['error']}", "ERROR")
            log(ROLE, "Guardando progreso parcial: Batches 1+2 completados", "WARN")
            # No ejecutar Batch 4, continuar con lo que tenemos
            all_files = batch1_files + batch2_files
            # Skip Batch 4, ir directo a escribir archivos
        else:
            batch3_files = result3.get("response", {}).get("files", [])
            log(ROLE, f"Batch 3: {len(batch3_files)} archivos generados", "SUCCESS")

            # === BATCH 4: Implementar tests completos (solo si Batch 3 exitoso) ===
            prompt_batch4 = f"""Eres Dev Agent (Alex), desarrollador Python senior.

OBJETIVO:
{objective}

ARQUITECTURA APROBADA (PM Agent):
{json.dumps(architecture, indent=2)}

TU TAREA - BATCH 4/4:
Implementar tests completos para TODOS los módulos.

TODOS LOS MÓDULOS DEL PROYECTO:
{all_modules_list}

GENERA:
1. test_*.py para CADA módulo (tests unitarios COMPLETOS con >95% coverage)
2. tests/test_integration.py (tests de integración end-to-end)

Cada test debe incluir:
- Fixtures con pytest
- Tests unitarios completos
- Mocking apropiado
- Assertions robustas
- Edge cases

Tests 100% FUNCIONALES (NO TODOs, NO placeholders).

IMPORTANTE - NO INTENTES ESCRIBIR ARCHIVOS:
- NO uses Write tool, Bash tool, subprocess
- Retorna TODO el código como strings en JSON

RESPONDE JSON CON TODO EL CÓDIGO:
{{
  "role": "dev",
  "status": "batch4",
  "batch": 4,
  "output_dir": "{output_dir}",
  "files": [
    {{"path": "tests/test_auth_service.py", "content": "tests completos..."}},
    {{"path": "tests/test_task_service.py", "content": "tests completos..."}},
    {{"path": "tests/test_integration.py", "content": "tests integración..."}}
  ]
}}

Responde SOLO JSON."""

            log(ROLE, "Batch 4/4: Implementando tests completos...", "INFO")
            result4 = execute_claude_agent("dev", prompt_batch4, timeout=CLAUDE_TIMEOUT_DEV)

            if not result4["success"]:
                log(ROLE, f"Batch 4 falló: {result4['error']}", "ERROR")
                # Continuar con tests skeletons si Batch 4 falla
                log(ROLE, "Continuando con test skeletons de Batch 3", "WARN")
                all_files = batch1_files + batch2_files + batch3_files
            else:
                batch4_files = result4.get("response", {}).get("files", [])
                log(ROLE, f"Batch 4: {len(batch4_files)} archivos generados", "SUCCESS")
                all_files = batch1_files + batch2_files + batch3_files + batch4_files

    # 3-BATCH STRATEGY
    elif batch_strategy == "3-batch" and iteration == 1:
        log(ROLE, f"Generando {len(modules)} módulos en 3 batches para evitar token limit", "INFO")

        batch1_modules = modules[:4]
        batch2_modules = modules[4:] if len(modules) > 4 else []

        # === BATCH 1: Primeros 4 módulos + configs ===
        prompt_batch1 = f"""Eres Dev Agent (Alex), desarrollador Python senior.

OBJETIVO:
{objective}

ARQUITECTURA APROBADA (PM Agent):
{json.dumps(architecture, indent=2)}

TU TAREA - BATCH 1/3:
Genera SOLO estos módulos:
{json.dumps(batch1_modules, indent=2)}

Y TAMBIÉN:
- src/__init__.py (imports de módulos)
- requirements.txt (con TODAS las dependencias del proyecto completo)
- .env.example (variables necesarias)

Código 100% FUNCIONAL (NO TODOs, NO placeholders).

IMPORTANTE - NO INTENTES ESCRIBIR ARCHIVOS:
- NO uses Write tool, Bash tool, subprocess
- Retorna TODO el código como strings en JSON

RESPONDE JSON CON TODO EL CÓDIGO:
{{
  "role": "dev",
  "status": "batch1",
  "batch": 1,
  "output_dir": "{output_dir}",
  "files": [
    {{"path": "src/__init__.py", "content": "..."}},
    {{"path": "src/{batch1_modules[0]}", "content": "código completo..."}},
    {{"path": "requirements.txt", "content": "..."}},
    {{"path": ".env.example", "content": "..."}}
  ]
}}

Responde SOLO JSON."""

        log(ROLE, "Batch 1/3: Generando primeros 4 módulos + configs...", "INFO")
        result1 = execute_claude_agent("dev", prompt_batch1, timeout=CLAUDE_TIMEOUT_DEV)

        if not result1["success"]:
            log(ROLE, f"Batch 1 falló: {result1['error']}", "ERROR")
            return None

        batch1_files = result1.get("response", {}).get("files", [])
        log(ROLE, f"Batch 1: {len(batch1_files)} archivos generados", "SUCCESS")

        # === BATCH 2: Resto módulos + README (SIN TESTS) ===
        if batch2_modules:
            prompt_batch2 = f"""Eres Dev Agent (Alex), desarrollador Python senior.

OBJETIVO:
{objective}

ARQUITECTURA APROBADA (PM Agent):
{json.dumps(architecture, indent=2)}

TU TAREA - BATCH 2/3:
Genera SOLO estos módulos:
{json.dumps(batch2_modules, indent=2)}

Y TAMBIÉN:
- README.md (setup instructions, architecture, usage examples)
- alembic/versions/001_initial.py (si hay BD en arquitectura)

NO generes tests aún (van en Batch 3).

Código 100% FUNCIONAL (NO TODOs, NO placeholders).

IMPORTANTE - NO INTENTES ESCRIBIR ARCHIVOS:
- NO uses Write tool, Bash tool, subprocess
- Retorna TODO el código como strings en JSON

RESPONDE JSON CON TODO EL CÓDIGO:
{{
  "role": "dev",
  "status": "batch2",
  "batch": 2,
  "output_dir": "{output_dir}",
  "files": [
    {{"path": "src/{batch2_modules[0]}", "content": "código completo..."}},
    {{"path": "README.md", "content": "..."}},
    {{"path": "alembic/versions/001_initial.py", "content": "..."}}
  ]
}}

Responde SOLO JSON."""

            log(ROLE, "Batch 2/3: Generando módulos restantes + README...", "INFO")
            result2 = execute_claude_agent("dev", prompt_batch2, timeout=CLAUDE_TIMEOUT_DEV)

            if not result2["success"]:
                log(ROLE, f"Batch 2 falló: {result2['error']}", "ERROR")
                log(ROLE, "Guardando progreso parcial: Batch 1 completado", "WARN")
                batch2_files = []
                # Continuar con lo que tenemos
            else:
                batch2_files = result2.get("response", {}).get("files", [])
                log(ROLE, f"Batch 2: {len(batch2_files)} archivos generados", "SUCCESS")
        else:
            batch2_files = []

        # === BATCH 3: SOLO TESTS + DOCKER ===
        all_modules_list = json.dumps(modules, indent=2)
        prompt_batch3 = f"""Eres Dev Agent (Alex), desarrollador Python senior.

OBJETIVO:
{objective}

ARQUITECTURA APROBADA (PM Agent):
{json.dumps(architecture, indent=2)}

TU TAREA - BATCH 3/3:
Genera tests completos y deployment config.

MÓDULOS YA GENERADOS (en batches 1 y 2):
{all_modules_list}

GENERA:
1. tests/__init__.py
2. test_*.py para CADA módulo (tests unitarios completos)
3. tests/test_integration.py (tests de integración)
4. docker-compose.yml (servicios necesarios: app, DB, Redis, etc)
5. Dockerfile (si necesario para deployment)

Código 100% FUNCIONAL (NO TODOs, NO placeholders).
Tests con >95% coverage.

IMPORTANTE - NO INTENTES ESCRIBIR ARCHIVOS:
- NO uses Write tool, Bash tool, subprocess
- Retorna TODO el código como strings en JSON

RESPONDE JSON CON TODO EL CÓDIGO:
{{
  "role": "dev",
  "status": "batch3",
  "batch": 3,
  "output_dir": "{output_dir}",
  "files": [
    {{"path": "tests/__init__.py", "content": "..."}},
    {{"path": "tests/test_auth_service.py", "content": "código completo..."}},
    {{"path": "tests/test_integration.py", "content": "..."}},
    {{"path": "docker-compose.yml", "content": "..."}},
    {{"path": "Dockerfile", "content": "..."}}
  ]
}}

Responde SOLO JSON."""

        log(ROLE, "Batch 3/3: Generando tests + docker...", "INFO")
        result3 = execute_claude_agent("dev", prompt_batch3, timeout=CLAUDE_TIMEOUT_DEV)

        if not result3["success"]:
            log(ROLE, f"Batch 3 falló: {result3['error']}", "ERROR")
            log(ROLE, "Guardando progreso parcial: Batches 1+2 completados", "WARN")
            # Continuar con lo que tenemos (sin tests ni docker)
            all_files = batch1_files + batch2_files
        else:
            batch3_files = result3.get("response", {}).get("files", [])
            log(ROLE, f"Batch 3: {len(batch3_files)} archivos generados", "SUCCESS")
            # COMBINAR 3 BATCHES
            all_files = batch1_files + batch2_files + batch3_files

    # SINGLE-BATCH STRATEGY (pequeños proyectos o iteraciones 2+)
    else:
        if iteration == 1 and batch_strategy == "single":
            prompt = f"""Eres Dev Agent (Alex), desarrollador Python senior.

OBJETIVO:
{objective}

ARQUITECTURA APROBADA (PM Agent):
{json.dumps(architecture, indent=2)}

TU TAREA:
1. Genera TODOS los módulos propuestos por PM
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
    ...
  ]
}}

Responde SOLO JSON."""

            log(ROLE, "Iteración 1: Generación single-batch (proyecto pequeño)", "INFO")

        else:
            # Iteración 2+: mejorar basado en feedback
            log(ROLE, f"Iteración {iteration}: Mejorando código basado en feedback", "INFO")
            prompt = None  # Will be set below
            security_issues = feedback.get("security_issues", [])
            qa_issues = feedback.get("qa_issues", [])

            prompt = f"""Eres Dev Agent (Alex). MEJORA el código basado en feedback de validación.

OBJETIVO:
{objective}

FEEDBACK DE VALIDACIÓN (Iteración {iteration}):
- Security issues: {len(security_issues)}
- QA issues: {len(qa_issues)}

ISSUES CRÍTICOS:
{json.dumps(feedback.get('critical_issues', [])[:10], indent=2)}

HIGH PRIORITY:
{json.dumps(feedback.get('high_priority', [])[:10], indent=2)}

DIRECTORIO DEL PROYECTO:
{output_dir}

TU TAREA:
1. Analiza el código existente en {output_dir}
2. Genera versiones MEJORADAS de los archivos que necesitan cambios
3. FIX TODOS los issues críticos
4. FIX los high priority
5. Asegura tests pasan al 100%
6. ACTUALIZA README con cambios

IMPORTANTE - NO INTENTES ESCRIBIR ARCHIVOS:
- NO uses Write tool
- NO uses Bash tool
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

Responde SOLO JSON."""

        log(ROLE, f"Iteración {iteration}: Solicitando implementación a Dev Agent...")

        if tracker:
            ctx = tracked_operation("dev.implementation", ROLE, task_id)
            ctx.__enter__()

        result = execute_claude_agent("dev", prompt, timeout=CLAUDE_TIMEOUT_DEV)

        if tracker:
            ctx.__exit__(None, None, None)

        if not result["success"]:
            log(ROLE, f"Dev Agent falló: {result['error']}", "ERROR")
            return None

        all_files = result.get("response", {}).get("files", [])

    # ESCRIBIR ARCHIVOS (orchestrator, no Dev Agent)
    if not all_files:
        log(ROLE, "Dev no retornó archivos en JSON", "ERROR")
        return None

    output_path = Path(output_dir)

    try:
        output_path.mkdir(parents=True, exist_ok=True)

        files_written = 0
        for file_info in all_files:
            file_path = file_info.get("path")
            file_content = file_info.get("content")

            if not file_path or file_content is None:
                log(ROLE, f"Archivo inválido: {file_info.get('path', 'unknown')}", "WARN")
                continue

            full_path = output_path / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text(file_content, encoding='utf-8')
            files_written += 1

        log(ROLE, f"Escritos {files_written} archivos en {output_dir}", "SUCCESS")

    except Exception as e:
        log(ROLE, f"Error escribiendo archivos: {e}", "ERROR")
        return None

    return {
        "output_dir": str(output_dir),
        "files": all_files,
        "status": "implemented"
    }


def validate_security(project_dir: str) -> Dict:
    """Validar seguridad del proyecto (reutiliza V5)"""

    if not VALIDATORS_AVAILABLE:
        log(ROLE, "!!! Validators no disponibles - usando mock CONSERVADOR !!!", "WARN")
        log(ROLE, "!!! Mock retorna FAILED para forzar validación real !!!", "WARN")
        return {
            "score": 5.0,  # Score bajo para evitar falsa convergencia
            "passed": False,  # NUNCA pasar con mock
            "violations": [
                "MOCK VALIDATOR: validation_utils_v4 no disponible",
                "MOCK VALIDATOR: Implementa SecurityValidator real para validación",
                "MOCK VALIDATOR: Score mock=5.0 (insuficiente para convergencia)"
            ],
            "is_mock": True  # Flag para identificar mock
        }

    try:
        validator = SecurityValidator()
        result = validator.validate(project_dir)
        result["is_mock"] = False  # Validación real
        return result
    except Exception as e:
        log(ROLE, f"Error en Security validation: {e}", "ERROR")
        return {
            "score": 0,
            "passed": False,
            "violations": [str(e)],
            "is_mock": False
        }


def validate_qa(project_dir: str) -> Dict:
    """Validar QA del proyecto (reutiliza V5)"""

    if not VALIDATORS_AVAILABLE:
        log(ROLE, "!!! Validators no disponibles - usando mock CONSERVADOR !!!", "WARN")
        log(ROLE, "!!! Mock retorna FAILED para forzar validación real !!!", "WARN")
        return {
            "score": 5.0,  # Score bajo para evitar falsa convergencia
            "passed": False,  # NUNCA pasar con mock
            "violations": [
                "MOCK VALIDATOR: validation_utils_v4 no disponible",
                "MOCK VALIDATOR: Implementa QAValidator real para validación",
                "MOCK VALIDATOR: Score mock=5.0 (insuficiente para convergencia)",
                "MOCK VALIDATOR: Coverage no verificado (0%)"
            ],
            "metrics": {"coverage": 0.0},  # Coverage real desconocido
            "is_mock": True  # Flag para identificar mock
        }

    try:
        validator = QAValidator()
        result = validator.validate(project_dir)
        result["is_mock"] = False  # Validación real
        return result
    except Exception as e:
        log(ROLE, f"Error en QA validation: {e}", "ERROR")
        return {
            "score": 0,
            "passed": False,
            "violations": [str(e)],
            "metrics": {},
            "is_mock": False
        }


def run_v7_loop(objective: str, dialogue_log) -> Dict:
    """
    Loop principal V7 con Claude real para PM/Dev.

    Retorna:
        {
            "success": bool,
            "iterations": int,
            "output_dir": str,
            "security_score": float,
            "qa_score": float,
            "reason": str (si falló)
        }
    """

    tracker = get_tracker()
    iteration = 0
    architecture = None
    output_dir = None
    first_iteration_output_dir = None  # FIX: Guardar proyecto de Iteración 1
    security_score = 0.0
    qa_score = 0.0
    security_result = {}  # Inicializar aquí para evitar UnboundLocalError
    qa_result = {}         # Inicializar aquí para evitar UnboundLocalError

    dialogue_log.log_phase_start("V7_ENTERPRISE", [
        f"Objective: {objective}",
        f"Target: Security >= {MIN_SECURITY_SCORE}, QA >= {MIN_QA_SCORE}",
        f"Max iterations: {MAX_ITERATIONS}",
        "PM/Dev: Claude real intelligence"
    ])

    while iteration < MAX_ITERATIONS:
        iteration += 1

        log(ROLE, f"=== ITERACIÓN {iteration}/{MAX_ITERATIONS} ===", "INFO")
        print()

        dialogue_log.log_iteration_loop(
            iteration,
            "V7_ENTERPRISE",
            "running",
            f"Iteración {iteration}: {'PM→Dev' if iteration == 1 else 'Dev mejora'} → Validation"
        )

        # ITERACIÓN 1: PM propone arquitectura
        if iteration == 1:
            architecture = request_pm_architecture(objective, iteration, tracker)

            if not architecture:
                return {
                    "success": False,
                    "iterations": iteration,
                    "reason": "PM Agent failed to propose architecture"
                }

            dialogue_log.log_message(
                from_agent="pm",
                to_agent=ROLE,
                msg_type="ARCHITECTURE_PROPOSAL",
                content=architecture,
                reasoning="PM Agent (Claude) proposed architecture"
            )

        # DEV implementa o mejora
        if iteration == 1:
            feedback = None
        else:
            # Preparar feedback de iteración anterior
            feedback = {
                "security_issues": security_result.get("violations", []),
                "qa_issues": qa_result.get("violations", []),
                "critical_issues": security_result.get("critical", []),
                "high_priority": security_result.get("high", [])
            }

        # FIX: Pasar directorio existente en iteraciones 2+
        implementation = request_dev_implementation(
            objective,
            architecture,
            iteration,
            feedback,
            tracker,
            existing_project_dir=first_iteration_output_dir if iteration > 1 else None
        )

        if not implementation:
            return {
                "success": False,
                "iterations": iteration,
                "reason": "Dev Agent failed to implement"
            }

        output_dir = implementation.get("output_dir")

        # FIX: Guardar output_dir de primera iteración para reutilizar en iteraciones 2+
        if iteration == 1:
            first_iteration_output_dir = output_dir

        if not output_dir or not Path(output_dir).exists():
            log(ROLE, "Dev no generó output_dir válido, continuando...", "WARN")
            continue

        dialogue_log.log_message(
            from_agent="dev",
            to_agent=ROLE,
            msg_type="IMPLEMENTATION_DONE",
            content={"output_dir": output_dir},
            reasoning=f"Dev Agent (Claude) {'implemented' if iteration == 1 else 'improved'}"
        )

        # VALIDACIÓN Security + QA
        log(ROLE, "Validando Security...", "INFO")
        security_result = validate_security(output_dir)
        security_score = security_result.get("score", 0)
        security_passed = security_result.get("passed", False)

        log(ROLE, f"Security score: {security_score:.1f}/10",
            "SUCCESS" if security_passed else "WARN")

        log(ROLE, "Validando QA...", "INFO")
        qa_result = validate_qa(output_dir)
        qa_score = qa_result.get("score", 0)
        qa_passed = qa_result.get("passed", False)

        coverage = qa_result.get("metrics", {}).get("coverage", 0) * 100

        log(ROLE, f"QA score: {qa_score:.1f}/10 (coverage: {coverage:.1f}%)",
            "SUCCESS" if qa_passed else "WARN")

        print()

        # ¿CONVERGENCIA?
        if (security_score >= MIN_SECURITY_SCORE and
            qa_score >= MIN_QA_SCORE and
            security_passed and
            qa_passed):

            log(ROLE, f"🎉 CONVERGENCIA ALCANZADA! (iteración {iteration})", "SUCCESS")
            print()
            print("=" * 80)
            print(f"  ✓ Security Score: {security_score:.1f}/10 (>= {MIN_SECURITY_SCORE})")
            print(f"  ✓ QA Score: {qa_score:.1f}/10 (>= {MIN_QA_SCORE})")
            print(f"  ✓ Iteraciones: {iteration}")
            print(f"  ✓ Output: {output_dir}")
            print("=" * 80)
            print()

            dialogue_log.log_validation(output_dir, {
                "passed": True,
                "security_score": security_score,
                "qa_score": qa_score,
                "iteration": iteration
            })

            # Git commit
            try:
                init_project_repo(output_dir)
                success, commit_hash = commit_phase(
                    output_dir,
                    "V7_ENTERPRISE",
                    f"V7 convergencia en {iteration} iteraciones - "
                    f"Security: {security_score:.1f}, QA: {qa_score:.1f}"
                )
                if success:
                    log(ROLE, f"Git commit: {commit_hash[:7]}", "SUCCESS")
            except Exception as e:
                log(ROLE, f"Git commit falló: {e}", "WARN")

            # Flush metrics
            tracker.flush()

            return {
                "success": True,
                "iterations": iteration,
                "output_dir": output_dir,
                "security_score": security_score,
                "qa_score": qa_score
            }

        else:
            # No convergió
            log(ROLE, f"No convergió (Security: {security_score:.1f}, QA: {qa_score:.1f})", "WARN")
            print()

            # Preparar feedback para siguiente iteración
            # (ya está en security_result y qa_result para próxima iteración)

    # Max iterations alcanzadas
    log(ROLE, f"Max iteraciones ({MAX_ITERATIONS}) alcanzadas sin convergencia", "ERROR")

    return {
        "success": False,
        "iterations": MAX_ITERATIONS,
        "output_dir": output_dir,
        "security_score": security_score,
        "qa_score": qa_score,
        "reason": "Max iterations reached without convergence"
    }


def main():
    """Entry point V7"""
    display_header()

    cleanup_stale_locks()
    cleanup_old_messages(ROLE)

    # Dialogue logger
    session_id = f"v7_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    dialogue_log = get_logger(session_id)

    log(ROLE, f"Dialogue log: {dialogue_log.get_log_path()}")
    print()

    try:
        # 1. Get objective from user
        print("What should we build?")
        print()
        print("Examples:")
        print("  - REST API for task management with JWT auth")
        print("  - CLI tool for file processing with progress bars")
        print("  - ETL pipeline with data validation")
        print("  - Web scraper with anti-detection")
        print()
        print("IMPORTANT: Be specific about what you want")
        print()

        objective = input("Objective: ").strip()

        if not objective:
            log(ROLE, "No objective provided", "ERROR")
            return 1

        print()
        print("-" * 80)
        print()

        # 2. Run V7 loop
        result = run_v7_loop(objective, dialogue_log)

        print()
        print("=" * 80)
        print("V7 FINAL RESULT")
        print("=" * 80)

        if result["success"]:
            print("✅ SUCCESS - CONVERGENCIA ALCANZADA")
            print()
            print(f"  Iterations: {result['iterations']}")
            print(f"  Security Score: {result['security_score']:.1f}/10")
            print(f"  QA Score: {result['qa_score']:.1f}/10")
            print(f"  Output: {result['output_dir']}")
        else:
            print(f"❌ FAILED: {result.get('reason', 'Unknown')}")
            print()
            print(f"  Iterations: {result['iterations']}")
            print(f"  Security Score: {result.get('security_score', 0):.1f}/10")
            print(f"  QA Score: {result.get('qa_score', 0):.1f}/10")
            if result.get('output_dir'):
                print(f"  Partial output: {result['output_dir']}")

        print()
        print(f"  Dialogue log: {dialogue_log.get_log_path()}")
        print(f"  Metrics: .metrics/performance_summary.json")
        print()
        print("=" * 80)

        # Log session end
        dialogue_log.log_session_end({
            "success": result["success"],
            "iterations": result["iterations"],
            "security_score": result.get("security_score"),
            "qa_score": result.get("qa_score"),
            "output_dir": result.get("output_dir")
        })

        return 0 if result["success"] else 1

    except KeyboardInterrupt:
        log(ROLE, "Interrupted by user", "WARN")
        return 0

    except Exception as e:
        log(ROLE, f"Error: {e}", "ERROR")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
