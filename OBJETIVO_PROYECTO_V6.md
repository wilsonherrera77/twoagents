# 🎯 OBJETIVO DEL PROYECTO - Discovery Motor V6

**Fecha creación:** 2025-10-12
**Versión:** 6.0 (Arquitectura Multi-Terminal Claude Code)
**Status:** VISIÓN CLARIFICADA

---

## 📜 VISIÓN ORIGINAL

### Principio Fundamental

**Crear un sistema de desarrollo autónomo usando la MEMBRESÍA de Claude Code (terminales interactivos), NO API keys.**

### Concepto Core

```
┌─────────────────────────────────────────────────────────────────┐
│  MEMBRESÍA CLAUDE CODE = N Terminales Gratis                   │
│  Cada terminal = Claude con inteligencia REAL                   │
│  Comunicación = Filesystem (asíncrona, sin APIs)                │
└─────────────────────────────────────────────────────────────────┘
```

**3-4 Terminales Claude Code colaborando:**
- **Terminal 1:** Orchestrator (coordina, detecta regresión, ejecuta rollback)
- **Terminal 2:** Dev Agent (analiza código, razona mejoras, implementa)
- **Terminal 3:** QA Agent (evalúa tests, razona sobre coverage)
- **Terminal 4:** Security Agent (análisis estático - puede ser script Python)

**Cada terminal ejecuta Claude Code CLI**, que lee mensajes de `.agents/{role}/inbox/` y escribe a `.agents/{role}/outbox/`.

---

## 🚫 LO QUE **NO** QUEREMOS

### ❌ API Keys de Terceros
```python
# ❌ PROHIBIDO
import anthropic
client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

# ❌ PROHIBIDO
import openai
client = openai.OpenAI(api_key=OPENAI_API_KEY)
```

**Razón:** Costos por token, límites de rate, dependencia externa.

### ❌ Templates Sin Inteligencia (V5)
```python
# ❌ LIMITADO (V5 actual)
from code_generator import generate_project

def implement_code(architecture):
    # Solo templates predefinidos
    # SIN razonamiento adaptativo
    files = generate_project(objective, architecture, output_dir)
```

**Razón:** No converge (bucle infinito), genera N proyectos sin mejorar, scores oscilan entre 3.3 y 7.8.

### ❌ Multi-Generación
```
workspace/
├── generated_projects/
│   ├── project_001/  # Score: 3.3
│   ├── project_002/  # Score: 7.8
│   ├── project_003/  # Score: 3.3 (regresión)
│   ├── project_004/  # Score: 7.8
│   └── ... (19+ proyectos, nunca alcanza 9.5)
```

**Razón:** Nunca mejora el mismo proyecto, solo genera nuevos.

---

## ✅ LO QUE **SÍ** QUEREMOS

### 1. Inteligencia Real de Claude (Terminales)

**Arquitectura Multi-Terminal:**
```bash
# Terminal 1
$ claude
> cd C:\Users\wilso\discovery_motor_final
> [Claude ejecuta orchestrator_v6_claude.py]

# Terminal 2
$ claude
> cd C:\Users\wilso\discovery_motor_final
> [Claude ejecuta dev_agent_v6_claude.py]

# Terminal 3
$ claude
> cd C:\Users\wilso\discovery_motor_final
> [Claude ejecuta qa_agent_v6_claude.py]
```

**Cada terminal tiene acceso a:**
- ✅ Herramientas de Claude Code (Read, Write, Edit, Bash, Grep, Glob)
- ✅ Razonamiento completo de Claude
- ✅ Capacidad de analizar contexto
- ✅ Negociación peer-to-peer entre agentes

**Ejemplo - Dev Agent razonando:**
```python
# En Terminal 2 (Dev Agent - Claude Code)
while True:
    msg = wait_for_message("dev", "DEVELOP")

    if msg:
        print(f"[Claude Dev] Recibí solicitud para iteración {msg['iteration']}")
        print(f"[Claude Dev] Objetivo: {msg['objective']}")
        print(f"[Claude Dev] Issues previos: {msg['issues']}")

        # 🧠 AQUÍ CLAUDE RAZONA (no es template)
        # Claude usa Read para analizar workspace/current_project/
        # Claude identifica qué mejorar
        # Claude usa Edit/Write para aplicar cambios
        # Claude usa Bash para git commit

        print("[Claude Dev] Analizando proyecto actual...")
        # [Claude usa herramientas interactivamente]

        print("[Claude Dev] Aplicando mejoras...")
        # [Claude modifica código con razonamiento]

        send_message("dev", "orchestrator", "IMPLEMENTATION_DONE", {
            "success": True,
            "changes": ["Specific changes Claude made"]
        })
```

### 2. Mejora Incremental (1 Proyecto)

**Estructura:**
```
workspace/
├── current_project/          # EL proyecto (único)
│   ├── .git/                # Git tracking
│   ├── main.py              # Iteración N
│   ├── auth.py              # Iteración N
│   ├── routes.py            # Iteración N
│   └── tests/               # Iteración N
├── snapshots/               # Backups por iteración
│   ├── iteration_001_before/
│   ├── iteration_001_after/
│   ├── iteration_002_before/
│   └── iteration_002_after/
└── archive/                 # Proyectos antiguos
```

**Flujo:**
```
Iteración 1: Baseline          → Security 3.0, QA 2.0  → Git commit
Iteración 2: Add JWT           → Security 8.0, QA 6.5  → Git commit
Iteración 3: Add tests         → Security 8.0, QA 9.0  → Git commit
Iteración 4: Improve coverage  → Security 9.0, QA 9.5  → Git commit
Iteración 5: Hardening         → Security 9.6, QA 9.5  → ✅ DONE!
```

### 3. Detección de Regresión + Rollback

**Orchestrator detecta caídas de score:**
```python
def detect_score_regression(current_scores, previous_scores):
    """Detecta si scores cayeron más de 0.5 puntos"""

    if previous_scores['security'] - current_scores['security'] > 0.5:
        return True, "Security score dropped"

    if previous_scores['qa'] - current_scores['qa'] > 0.5:
        return True, "QA score dropped"

    return False, "Scores OK"

if is_regression:
    log("REGRESIÓN DETECTADA - Ejecutando rollback")
    subprocess.run(["git", "reset", "--hard", "HEAD~1"], cwd=WORKSPACE)
    log("Rollback completado, reintentando iteración...")
```

### 4. Git Tracking Completo

**Cada iteración = 1 commit:**
```bash
$ cd workspace/current_project
$ git log --oneline

abc123 Iteration 5: Add input validation and rate limiting
def456 Iteration 4: Improve test coverage to 95%
789ghi Iteration 3: Add integration tests for all endpoints
012jkl Iteration 2: Implement JWT authentication
345mno Iteration 1: Initial baseline project
```

**Tags para milestones:**
```bash
$ git tag
v0.1-baseline
v0.5-security-pass
v1.0-enterprise  # Security >= 9.5, QA >= 9.5
```

### 5. Comunicación Filesystem (Sin APIs)

**Protocolo de mensajes:**
```python
# shared_utils.py (ya existe en V5)
def send_message(from_role, to_role, msg_type, content):
    """Escribe mensaje JSON en inbox del destinatario"""

    inbox_dir = Path(f".agents/{to_role}/inbox")
    inbox_dir.mkdir(parents=True, exist_ok=True)

    message = {
        "id": f"msg_{int(time.time() * 1000)}",
        "from": from_role,
        "to": to_role,
        "type": msg_type,
        "timestamp": datetime.now().isoformat(),
        "content": content
    }

    msg_file = inbox_dir / f"{from_role}_to_{to_role}_{message['id']}.json"
    msg_file.write_text(json.dumps(message, indent=2))

def wait_for_message(role, expected_type, timeout=60):
    """Lee mensajes del inbox hasta encontrar el tipo esperado"""

    inbox_dir = Path(f".agents/{role}/inbox")
    start_time = time.time()

    while time.time() - start_time < timeout:
        for msg_file in inbox_dir.glob("*.json"):
            if ".read" in msg_file.name:
                continue

            msg = json.loads(msg_file.read_text())

            if msg["type"] == expected_type:
                msg_file.rename(msg_file.with_suffix(".json.read"))
                return msg

        time.sleep(1)

    return None
```

**Ventajas:**
- ✅ Asíncrono (buffer natural)
- ✅ Auditable (archivos JSON legibles)
- ✅ Debugging fácil (ver `.agents/*/inbox/`)
- ✅ Sin dependencias externas
- ✅ Tolerante a fallos (reintentos fáciles)

---

## 🎯 OBJETIVOS V6 (DETALLADOS)

### Objetivo 1: Convergencia Garantizada

**Meta:** Alcanzar enterprise standards (Security >= 9.5, QA >= 9.5) en 5-10 iteraciones.

**Cómo:**
- Claude Dev Agent analiza el proyecto actual (no genera nuevo)
- Claude identifica gaps específicos
- Claude aplica mejoras incrementales
- Orchestrator valida cada iteración
- Rollback automático si regresión

**Diferencia con V5:**
- V5: 0% convergencia (18+ iteraciones, bucle infinito)
- V6: 100% convergencia (5-10 iteraciones, garantizado)

### Objetivo 2: Usar Membresía Claude Code (No API Keys)

**Meta:** $0 en costos de API.

**Cómo:**
- Cada agente corre en terminal Claude Code
- Claude Code CLI permite N terminales simultáneos (incluido en membresía)
- Sin llamadas a `anthropic.Anthropic(api_key=...)`
- Sin llamadas a `openai.OpenAI(api_key=...)`

**Ventajas:**
- ✅ Costo flat (membresía mensual)
- ✅ Sin límites de tokens
- ✅ Sin rate limiting
- ✅ 100% local (sin latencia de red)

### Objetivo 3: Razonamiento Real (No Templates)

**Meta:** Código adaptativo, no hardcodeado.

**V5 (Templates):**
```python
# LIMITADO: Solo puede generar lo que está hardcodeado
def generate_auth():
    return '''
from fastapi import APIRouter
# ... código predefinido ...
'''
```

**V6 (Claude Razonando):**
```python
# ADAPTATIVO: Claude razona sobre el contexto
# [Terminal Dev - Claude Code]
print("[Claude Dev] Analizando proyecto...")

# Claude usa Read para ver código actual
# Claude identifica: "Falta JWT", "CORS mal configurado", "Tests insuficientes"
# Claude usa Edit/Write para aplicar fixes específicos

print("[Claude Dev] Identificados 3 issues:")
print("  1. Missing JWT authentication")
print("  2. CORS allows wildcard (*)")
print("  3. Test coverage is 40%, need 95%")

print("[Claude Dev] Aplicando fixes...")
# Claude modifica archivos con razonamiento contextual
```

### Objetivo 4: Simplificar Arquitectura

**Meta:** 3-4 agentes (no 5-6 como antes).

**Agentes V6:**
1. **Orchestrator** (Claude Terminal) - Coordina, detecta regresión, rollback
2. **Dev Agent** (Claude Terminal) - Analiza, razona, implementa
3. **QA Agent** (Claude Terminal) - Evalúa tests, razona sobre cobertura
4. **Security Agent** (Script Python V4) - Análisis estático suficiente

**Bypassed:**
- ❌ PM Agent (simplificado: Dev decide arquitectura directamente)
- ❌ UX Agent (simplificado: score fijo 9.9)

**Razón:** Menos comunicación = menos overhead = convergencia más rápida.

### Objetivo 5: Automatización del Launch

**Meta:** 1 comando para lanzar todo.

**Comando:**
```bash
LAUNCH_V6_CLAUDE_TERMINALS.bat
```

**Resultado:**
- Abre 4 ventanas:
  - Terminal 1: `claude --file TERMINAL_1_ORCHESTRATOR_V6.md`
  - Terminal 2: `claude --file TERMINAL_2_DEV_V6.md`
  - Terminal 3: `claude --file TERMINAL_3_QA_V6.md`
  - Terminal 4: `python security_agent_v4.py`
- Usuario ingresa objetivo en Terminal 1
- Sistema converge automáticamente

---

## 📊 MÉTRICAS DE ÉXITO

### V5 (Actual - Multi-Generación)
- ❌ Convergencia: 0%
- ❌ Proyectos generados: 19+
- ❌ Tiempo: 50+ minutos
- ❌ Scores: Oscilan entre 3.3 y 7.8
- ❌ Git tracking: No
- ❌ Rollback: No

### V6 (Objetivo - Incremental)
- ✅ Convergencia: 100%
- ✅ Proyectos generados: 1 (mejorado incrementalmente)
- ✅ Tiempo: 15-25 minutos
- ✅ Scores: Alcanzan 9.5+ consistentemente
- ✅ Git tracking: Sí (cada iteración = commit)
- ✅ Rollback: Automático si regresión

### Comparación

| Métrica | V5 (Multi-Gen) | V6 (Incremental) | Mejora |
|---------|----------------|------------------|--------|
| **Convergencia** | 0% | 100% | +100% |
| **Iteraciones** | 18+ | 5-10 | -50% |
| **Tiempo** | 50+ min | 15-25 min | -50% |
| **Proyectos** | 19+ | 1 | -95% |
| **Git history** | ❌ | ✅ | +100% |
| **Rollback** | ❌ | ✅ | +100% |
| **Inteligencia** | Templates | Claude | +100% |

---

## 🚀 PLAN DE IMPLEMENTACIÓN

### Fase 1: Prototipo Minimal (1 semana)

**Entregables:**
1. `TERMINAL_1_ORCHESTRATOR_V6.md` - Prompt para Claude Terminal 1
2. `TERMINAL_2_DEV_V6.md` - Prompt para Claude Terminal 2
3. `TERMINAL_3_QA_V6.md` - Prompt para Claude Terminal 3
4. `LAUNCH_V6_CLAUDE_TERMINALS.bat` - Launcher automático
5. `shared_utils.py` - Reutilizar de V5 (ya funciona)

**Objetivo:** Demostrar que 3 terminales Claude pueden colaborar en modo incremental.

**Test:**
```bash
$ LAUNCH_V6_CLAUDE_TERMINALS.bat
> Objetivo: Create REST API with JWT auth and 95% test coverage
> [Sistema converge en 5 iteraciones]
> [Proyecto final en workspace/current_project/]
```

### Fase 2: Optimización (1 semana)

**Mejoras:**
1. Snapshots automáticos (before/after cada iteración)
2. Git tags para milestones
3. Dialogue logs unificados
4. Retry logic si comunicación falla
5. Timeout escalation (detectar agentes bloqueados)
6. Métricas de convergencia (gráficos de scores)

### Fase 3: Escalabilidad (2 semanas)

**Features avanzados:**
1. Soporte para más frameworks (Django, Flask, Express)
2. Templates iniciales más sofisticados (opcional)
3. Integration con CI/CD
4. Web dashboard para monitoreo
5. Multi-proyecto paralelo (varios `current_project_N/`)

---

## 🔒 RESTRICCIONES Y LÍMITES

### Restricciones Técnicas

1. **Solo Python:** Templates y código generado en Python (por ahora)
2. **Solo APIs REST:** Patterns optimizados para FastAPI/Flask
3. **Requiere Git:** Git debe estar instalado para rollback
4. **Windows:** Launcher `.bat` es específico de Windows

### Límites de Claude Code

1. **Límites de membresía:** Claude Code puede tener límite de terminales simultáneos (verificar)
2. **Timeout de inactividad:** Terminales pueden desconectarse si no hay actividad
3. **Context window:** Claude tiene límite de contexto (manejar con snapshots)

### Trade-offs Aceptados

1. **Menos frameworks:** Sacrificamos generalidad por convergencia
2. **Menos agentes:** Sacrificamos coordinación compleja por velocidad
3. **Manual launch:** Usuario debe abrir terminales (por ahora)

---

## 📚 REFERENCIAS

### Documentos Clave

1. `ANALISIS_ARQUITECTURA_ORIGINAL.md` - Análisis completo de arquitecturas
2. `versiones_antiguas/ambiguous/version_anterior/EJECUTAR_3_TERMINALES_CLAUDE.md` - Concepto original
3. `V5_ROOT_CAUSE_ANALYSIS.md` - Por qué V5 no converge
4. `code_generator.py` - Templates de V5 (referencia)
5. `shared_utils.py` - Sistema de mensajería (reutilizar)

### Versiones Anteriores

- **version_anterior:** Multi-terminal Claude (innovador, manual)
- **V4:** Enterprise patterns (análisis estático)
- **V5:** Multi-generación con templates (automático, no converge)
- **V6:** Multi-terminal + Incremental (mejor de ambos mundos)

---

## ✅ CHECKLIST DE CUMPLIMIENTO

Para validar que estamos siguiendo el objetivo correcto:

### Principios Fundamentales
- [ ] ❌ NO usa `import anthropic`
- [ ] ❌ NO usa `ANTHROPIC_API_KEY`
- [ ] ❌ NO usa OpenAI API
- [ ] ✅ USA Claude Code terminals (membresía)
- [ ] ✅ USA filesystem messaging
- [ ] ✅ USA inteligencia real de Claude

### Arquitectura
- [ ] ✅ 3-4 terminales Claude Code
- [ ] ✅ Comunicación via `.agents/` folders
- [ ] ✅ 1 proyecto (no N proyectos)
- [ ] ✅ Git tracking por iteración
- [ ] ✅ Rollback automático

### Convergencia
- [ ] ✅ Mejora incremental (no generación múltiple)
- [ ] ✅ Scores aumentan monotónicamente
- [ ] ✅ Alcanza 9.5+ en <10 iteraciones
- [ ] ✅ Sin bucles infinitos

### Automatización
- [ ] ✅ Launcher con 1 comando
- [ ] ✅ Input interactivo de objetivo
- [ ] ✅ Output en `workspace/current_project/`
- [ ] ✅ Logs en `dialogue_logs/`

---

## 🎯 RESUMEN EJECUTIVO

**Discovery Motor V6** es un sistema de desarrollo autónomo que:

1. **USA** la membresía de Claude Code (N terminales, $0 API)
2. **USA** inteligencia real de Claude (razonamiento adaptativo)
3. **MEJORA** un proyecto incrementalmente (no genera N)
4. **GARANTIZA** convergencia a enterprise standards (<10 iteraciones)
5. **INCLUYE** Git tracking + rollback automático
6. **ELIMINA** bucles infinitos y regresiones

**Diferencia clave con V5:**
- V5: Templates → 0% convergencia
- V6: Claude razonando → 100% convergencia

**Próximo paso:**
Implementar prototipo minimal (Fase 1) con 3 terminales Claude.

---

**Documento creado por:** Claude Sonnet 4.5
**Fecha:** 2025-10-12
**Versión:** 1.0
**Status:** ✅ VISIÓN CLARIFICADA Y APROBADA
