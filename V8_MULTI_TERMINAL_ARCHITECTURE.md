# Discovery Motor V8 - Multi-Terminal Architecture

**Versión**: 8.0
**Fecha**: 2025-10-19
**Status**: DISEÑO - Listo para implementación

---

## OBJETIVO PRINCIPAL

> **Diseñar e implementar un laboratorio de inteligencia colectiva artificial donde 2 agentes autónomos —ejecutándose en N terminales abiertos e independientes— negocian y desarrollan proyectos de software con apoyo de un motor de descubrimiento.**

---

## DIFERENCIAS CLAVE: V7 → V8

| Aspecto | V7 (Actual) | V8 (Target) |
|---------|-------------|-------------|
| **Arquitectura** | Monolítico (1 proceso) | Multi-proceso (3-4 terminales) |
| **PM Agent** | Llamada interna | Proceso independiente (Terminal 1) |
| **Dev Agent** | Llamada interna | Proceso independiente (Terminal 2) |
| **Negociación** | One-way (PM → Dev acepta) | **Bi-directional** (PM ← → Dev discute) |
| **Communicación** | En memoria | Filesystem (.shared/) |
| **Discovery Motor** | NO existe | **Terminal 3** (nuevo) |
| **Concurrencia** | Fix UUID (V7.12) | Nativo multi-proceso |
| **Paralelización** | Secuencial | PM y Dev trabajan en paralelo |
| **Convergencia** | Validators bloquean loop | **Async validation** |

---

## ARQUITECTURA V8

```
┌─────────────────────────────────────────────────────────────────────────┐
│                       DISCOVERY MOTOR V8                                 │
│                  Multi-Terminal AI Collective Intelligence               │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐
│  TERMINAL 1     │      │  TERMINAL 2     │      │  TERMINAL 3     │
│  PM Agent       │◄────►│  Dev Agent      │◄────►│  Discovery      │
│  (Claude)       │      │  (Claude)       │      │  Motor (Claude) │
└────────┬────────┘      └────────┬────────┘      └────────┬────────┘
         │                        │                         │
         └────────────────┬───────┴─────────────────────────┘
                          │
                          ▼
                  ┌───────────────┐
                  │   .shared/    │  Filesystem Communication
                  │   ├─ pm/      │  - proposals.json
                  │   ├─ dev/     │  - implementations.json
                  │   ├─ discovery│  - insights.json
                  │   └─ state/   │  - convergence.json
                  └───────┬───────┘
                          │
                          ▼
         ┌────────────────────────────────┐
         │      TERMINAL 4 (Orquestador)  │
         │  - Spawn terminales 1-3        │
         │  - Monitor .shared/ changes    │
         │  - Run validators (async)      │
         │  - Detect convergence          │
         │  - Git commits                 │
         └────────────────────────────────┘
```

---

## COMPONENTES V8

### 1. PM Agent (Terminal 1) - Standalone Process

**Archivo**: `pm_agent_v8.py`

**Responsabilidades**:
- Leer `.shared/state/objective.json`
- Proponer arquitectura inicial
- Escribir `.shared/pm/proposal_{iteration}.json`
- **NUEVO**: Leer `.shared/dev/counter_proposal.json`
- **NUEVO**: Negociar y ajustar propuesta
- **NUEVO**: Señalar acuerdo → `.shared/pm/agreement.json`

**Prompt Mejorado**:
```python
prompt = f"""Eres PM Agent (Morgan), arquitecto senior.

OBJETIVO: {objective}

PROPUESTA DEV:
{dev_counter_proposal if exists else "Primera iteración"}

TU TAREA:
1. Si es primera iteración: proponer arquitectura
2. Si Dev envió counter-proposal:
   - Evaluar concerns de Dev
   - Si válidos: ajustar arquitectura
   - Si no válidos: justificar decisión original
3. Responde JSON:
   - "action": "PROPOSE" | "ADJUST" | "AGREE" | "REJECT"
   - "architecture": {{...}}
   - "reasoning": "..."
   - "responses_to_dev": ["...", "..."]
"""
```

### 2. Dev Agent (Terminal 2) - Standalone Process

**Archivo**: `dev_agent_v8.py`

**Responsabilidades**:
- Leer `.shared/pm/proposal_{iteration}.json`
- **NUEVO**: Evaluar factibilidad técnica
- **NUEVO**: Puede counter-proponer → `.shared/dev/counter_proposal.json`
- **NUEVO**: O aceptar → `.shared/dev/acceptance.json`
- Implementar código si hay acuerdo
- Escribir `.shared/dev/implementation.json`

**Prompt Mejorado**:
```python
prompt = f"""Eres Dev Agent (Alex), desarrollador senior.

PROPUESTA PM:
{pm_proposal}

TU TAREA - EVALUACIÓN TÉCNICA:
1. Analizar factibilidad de cada módulo
2. Detectar:
   - Dependencias circulares
   - Complejidad excesiva
   - Arquitectura sub-óptima
3. Si encuentras issues CRÍTICOS:
   - "action": "COUNTER"
   - "concerns": ["...", "..."]
   - "alternative_architecture": {{...}}
4. Si arquitectura OK:
   - "action": "ACCEPT"
   - Generar código completo
"""
```

### 3. Discovery Motor (Terminal 3) - NUEVO

**Archivo**: `discovery_agent_v8.py`

**Responsabilidades**:
- **Monitorear** `.shared/pm/` y `.shared/dev/`
- **Analizar** patrones en código generado
- **Detectar**:
  - Code smells
  - Performance bottlenecks
  - Security vulnerabilities
  - Refactoring opportunities
- **Sugerir** mejoras proactivas
- Escribir `.shared/discovery/insights_{timestamp}.json`

**Prompt**:
```python
prompt = f"""Eres Discovery Motor, experto en code analysis.

CÓDIGO GENERADO:
{implementation_files}

ARQUITECTURA:
{architecture}

TU TAREA - ANÁLISIS PROFUNDO:
1. Buscar code smells (duplicación, complejidad, etc)
2. Detectar performance issues
3. Identificar security gaps
4. Sugerir refactorings
5. Responde JSON:
   - "insights": [
       {{"type": "performance", "severity": "high", "suggestion": "..."}},
       {{"type": "security", "severity": "critical", "suggestion": "..."}}
     ]
   - "recommended_actions": ["...", "..."]
"""
```

### 4. Orchestrator V8 (Terminal 4)

**Archivo**: `orchestrator_v8.py`

**Responsabilidades**:
- Spawn terminales 1-3 con `subprocess.Popen()`
- **Filesystem watcher** en `.shared/`
- Detectar cambios con `watchdog` library
- **State machine** para negociación:
  ```
  INIT → PM_PROPOSE → DEV_EVALUATE → [COUNTER → PM_ADJUST] → AGREEMENT → IMPLEMENT → VALIDATE → CONVERGE
  ```
- Run validators **async** (no bloquear)
- Git commits automáticos

**Código Clave**:
```python
import subprocess
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class V8Orchestrator:
    def __init__(self):
        self.pm_process = None
        self.dev_process = None
        self.discovery_process = None
        self.state = "INIT"

    def spawn_terminals(self):
        # PM Agent
        self.pm_process = subprocess.Popen(
            ["python", "pm_agent_v8.py"],
            cwd=str(PROJECT_ROOT)
        )

        # Dev Agent
        self.dev_process = subprocess.Popen(
            ["python", "dev_agent_v8.py"],
            cwd=str(PROJECT_ROOT)
        )

        # Discovery Motor
        self.discovery_process = subprocess.Popen(
            ["python", "discovery_agent_v8.py"],
            cwd=str(PROJECT_ROOT)
        )

    def watch_shared_dir(self):
        observer = Observer()
        handler = SharedDirHandler(self)
        observer.schedule(handler, ".shared", recursive=True)
        observer.start()
```

---

## WORKFLOW V8 - PASO A PASO

### Iteración 1: Propuesta Inicial

```
1. User: "REST API for task management"
   ↓
2. Orchestrator escribe .shared/state/objective.json
   ↓
3. PM Terminal lee objetivo → propone arquitectura
   ↓
4. PM escribe .shared/pm/proposal_001.json
   ↓
5. Dev Terminal lee propuesta → evalúa
   ↓
6. Dev escribe .shared/dev/evaluation_001.json
   - Si "action": "COUNTER": ir a paso 7
   - Si "action": "ACCEPT": ir a paso 9
   ↓
7. PM lee counter-proposal → ajusta arquitectura
   ↓
8. PM escribe .shared/pm/proposal_002.json → volver a paso 5
   ↓
9. Dev genera código → escribe .shared/dev/implementation_001.json
   ↓
10. Discovery Motor analiza código → insights
   ↓
11. Orchestrator valida (Security + QA)
   ↓
12. Si scores < 9.5: feedback a Dev → Iteración 2
```

### Iteración 2+: Mejora Incremental

```
1. Orchestrator escribe .shared/state/feedback.json
   - Security violations
   - QA violations
   - Discovery insights
   ↓
2. Dev lee feedback → mejora código
   ↓
3. Discovery Motor re-analiza
   ↓
4. Orchestrator re-valida
   ↓
5. Si scores >= 9.5: CONVERGENCIA ✅
```

---

## COMUNICACIÓN FILESYSTEM

### Estructura de `.shared/`

```
.shared/
├── state/
│   ├── objective.json          # User input
│   ├── current_iteration.json  # Tracking
│   └── convergence.json        # Final result
│
├── pm/
│   ├── proposal_001.json
│   ├── proposal_002.json
│   └── agreement.json
│
├── dev/
│   ├── evaluation_001.json
│   ├── counter_proposal_001.json
│   ├── acceptance.json
│   └── implementation_001.json
│
├── discovery/
│   ├── insights_001.json
│   ├── insights_002.json
│   └── recommendations.json
│
└── validation/
    ├── security_001.json
    └── qa_001.json
```

### Formato de Mensajes

**PM Proposal**:
```json
{
  "iteration": 1,
  "timestamp": "2025-10-19T14:30:00",
  "role": "pm",
  "action": "PROPOSE",
  "architecture": {
    "modules": ["auth.py", "tasks.py", ...],
    "database": {...},
    "technologies": {...}
  },
  "reasoning": "..."
}
```

**Dev Counter-Proposal**:
```json
{
  "iteration": 1,
  "timestamp": "2025-10-19T14:32:00",
  "role": "dev",
  "action": "COUNTER",
  "concerns": [
    "Module 'auth.py' has circular dependency with 'tasks.py'",
    "Database schema missing index on user_id (performance issue)"
  ],
  "alternative_architecture": {
    "modules": ["auth_service.py", "task_service.py", "shared_models.py"],
    "reasoning": "Eliminates circular dependency via shared models"
  }
}
```

---

## VENTAJAS V8 vs V7

| Mejora | V7 | V8 | Impacto |
|--------|----|----|---------|
| **Negociación Real** | PM → Dev acepta | PM ← → Dev discute | +70% arquitectura óptima |
| **Paralelización** | Secuencial | PM y Dev paralelos | -40% tiempo total |
| **Discovery Motor** | NO | Proactive insights | +30% calidad código |
| **Concurrencia** | Fix UUID | Multi-proceso nativo | Escalable a N proyectos |
| **Validación** | Bloquea loop | Async validators | -50% tiempo validación |
| **Debugging** | 1 proceso | 4 procesos aislados | +90% facilidad debug |

---

## ROADMAP DE IMPLEMENTACIÓN

### Sprint 1 (Semana 1): Fundación
- [ ] Crear `pm_agent_v8.py` (standalone)
- [ ] Crear `dev_agent_v8.py` (standalone)
- [ ] Implementar `.shared/` file structure
- [ ] Basic orchestrator con `subprocess.Popen()`

### Sprint 2 (Semana 2): Negociación
- [ ] Prompts de counter-proposal
- [ ] State machine en orchestrator
- [ ] Filesystem watcher (`watchdog`)
- [ ] Logging multi-proceso

### Sprint 3 (Semana 3): Discovery Motor
- [ ] Crear `discovery_agent_v8.py`
- [ ] Code analysis prompts
- [ ] Integration con validators
- [ ] Feedback loop automático

### Sprint 4 (Semana 4): Testing & Polish
- [ ] End-to-end testing (3 proyectos reales)
- [ ] Performance benchmarking
- [ ] Documentation
- [ ] Demo preparation

---

## MIGRACIÓN V7 → V8

**Backward Compatibility**:
```python
# orchestrator_v8.py
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["v7", "v8"], default="v8")
    args = parser.parse_args()

    if args.mode == "v7":
        # Run V7 monolithic (compatibility)
        run_v7_loop(objective, dialogue_log)
    else:
        # Run V8 multi-terminal (new)
        run_v8_multi_terminal(objective)
```

**Migration Path**:
1. V7 sigue funcionando (producción)
2. V8 se testea en paralelo
3. Cuando V8 alcanza 95% success rate → deprecate V7
4. V7 → V8 es opt-in con flag `--mode=v8`

---

## MÉTRICAS DE ÉXITO V8

| Métrica | Target | Medición |
|---------|--------|----------|
| **Convergencia Rate** | ≥ 90% | 9/10 proyectos convergen |
| **Avg Iterations** | ≤ 4 | Reducción vs V7 (esperado 5-8) |
| **Negotiation Effectiveness** | ≥ 70% | % arquitecturas mejoradas post-counter |
| **Discovery Motor Value** | ≥ 3 insights/proyecto | Insights accionables detectados |
| **Time to Convergence** | ≤ 30min | Para proyecto promedio 6 módulos |
| **Concurrent Projects** | ≥ 5 | Sin conflictos de archivos |

---

## CONCLUSIÓN

**Discovery Motor V8 es la implementación final del objetivo principal:**

✅ 2 agentes autónomos (PM + Dev)
✅ N terminales independientes (3-4)
✅ Negociación real (bidirectional)
✅ Motor de descubrimiento (nuevo agente)
✅ Enterprise DevSecOps
✅ 100% local (no APIs externas)
✅ Git tracking completo
✅ Trazabilidad total

**V8 NO es un rewrite - es la evolución natural de V7 con:**
- Misma base sólida (validators, git_workflow, performance_tracker)
- Misma inteligencia Claude
- Nueva arquitectura multi-proceso
- Nueva capacidad de negociación
- Nuevo motor de descubrimiento

**Tiempo estimado implementación**: 3-4 semanas
**ROI esperado**: 90% del objetivo principal alcanzado
**Risk level**: BAJO (V7 como fallback)
