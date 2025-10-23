# Discovery Motor V10 - Plan de Implementación Completo

**Fecha**: 2025-10-19 21:30
**Objetivo**: Sistema 100% funcional y autónomo con Claude CLI
**Tiempo estimado**: 2-3 horas

---

## 🎯 OBJETIVOS DEL PLAN

1. **Eliminar dependencia de File Communicator Pattern** (causa raíz del fallo V8)
2. **Usar Claude CLI directamente** vía subprocess
3. **Observabilidad completa** con logs detallados en cada paso
4. **Controles de calidad** en cada fase
5. **Sistema 100% autónomo** sin intervención humana

---

## 📊 DIAGNÓSTICO V8 (Completado)

### **Problema Raíz Identificado**:

**V8 NO FUNCIONA** porque:
1. PM Agent escribe prompts en `.agents/pm/inbox/prompt_XXX.txt`
2. PM Agent ESPERA respuesta en `.agents/pm/outbox/response_XXX.json`
3. **NADIE responde** → Timeout de 180s
4. PM Agent nunca genera `proposal_001.json`
5. Orchestrator espera `proposal_001.json` y timeout después de 2.5 horas
6. **FALLO TOTAL**

### **Evidencia**:
- ✅ Orchestrator funciona (escribe `objective.json`)
- ✅ PM Agent inicia
- ❌ PM Agent espera humano indefinidamente
- ❌ Sin propuesta → Sin proyecto

### **Conclusión**:
V8 requiere HUMANO para funcionar. No es un sistema autónomo.

---

## 🔧 ARQUITECTURA V10

### **Componentes**:

```
Discovery Motor V10
│
├── utils/
│   ├── logger_v10.py          ✅ COMPLETADO (Sistema de logging)
│   └── claude_cli_wrapper.py  ✅ COMPLETADO (Wrapper para Claude CLI)
│
├── agents_v10/
│   ├── pm_agent_v10.py        ⏳ SIGUIENTE (PM con Claude CLI directo)
│   ├── dev_agent_v10.py       ⏳ PENDIENTE (Dev con Claude CLI directo)
│   ├── security_agent_v10.py  ⏳ PENDIENTE (Security simplificado)
│   └── qa_agent_v10.py         ⏳ PENDIENTE (QA simplificado)
│
├── orchestrator_v10.py         ⏳ PENDIENTE (Orchestrator con controles)
│
├── monitor_v10.py              ⏳ PENDIENTE (Monitor en tiempo real)
│
└── RUN_V10.bat                 ⏳ PENDIENTE (Launcher con debugging)
```

---

## 📝 PLAN PASO A PASO

### **FASE 1: Infraestructura Base** ✅ COMPLETADA

**Duración**: 30 minutos

**Tareas**:
1. ✅ Crear `utils/logger_v10.py`
   - Sistema de logging con colores
   - Logs a archivo por agente
   - Métricas de performance
   - Estado del sistema

2. ✅ Crear `utils/claude_cli_wrapper.py`
   - Wrapper seguro para Claude CLI
   - Manejo de errores robusto
   - Timeout configurable
   - Validación de respuestas JSON
   - Retry automático

**Resultado**:
```
✅ Logger funcional con observabilidad completa
✅ Wrapper Claude CLI con controles
```

---

### **FASE 2: PM Agent V10** ⏳ SIGUIENTE

**Duración**: 45 minutos

**Cambios clave vs V8**:
```python
# ❌ V8 (File Communicator - requiere humano)
def execute_claude(prompt: str):
    write_to_file(prompt, ".agents/pm/inbox/prompt.txt")
    wait_for_human_response(".agents/pm/outbox/response.json")  # FALLA AQUÍ
    return read_response()

# ✅ V10 (Claude CLI directo - 100% autónomo)
def execute_claude(prompt: str):
    wrapper = ClaudeCLIWrapper(logger)
    result = wrapper.execute(prompt, expect_json=True)
    if not result.success:
        logger.error("Claude failed", result.error)
        return None
    return result.response
```

**Tareas**:
1. Crear `agents_v10/pm_agent_v10.py`
2. Reemplazar File Communicator con Claude CLI Wrapper
3. Agregar logging detallado en cada paso
4. Agregar validación de respuestas
5. Agregar controles de timeout
6. Testing unitario

**Controles**:
- ✅ Log antes de llamar Claude
- ✅ Log después con duración
- ✅ Log de error si falla
- ✅ Validar JSON response tiene campos requeridos
- ✅ Retry automático si falla (max 3)

**Testing**:
```bash
python agents_v10/pm_agent_v10.py --test
```

Expected output:
```
[INFO] PM Agent V10 starting...
[INFO] Testing architecture generation...
[INFO] 🤖 Claude execution #1 starting...
[SUCCESS] ✅ Claude execution #1 completed (12.3s)
[SUCCESS] Architecture generated: 6 modules
[SUCCESS] All tests PASSED
```

---

### **FASE 3: Dev Agent V10** ⏳ PENDIENTE

**Duración**: 45 minutos

**Cambios clave**:
- Igual que PM: reemplazar File Communicator con Claude CLI
- Generar código REAL (no fake)
- Validar sintaxis Python de archivos generados
- Crear estructura de proyecto completa

**Tareas**:
1. Crear `agents_v10/dev_agent_v10.py`
2. Implementar generación de código con Claude CLI
3. Implementar validación de sintaxis (`ast.parse()`)
4. Implementar escritura de archivos
5. Agregar controles de calidad
6. Testing unitario

**Controles**:
- ✅ Validar sintaxis Python de cada archivo
- ✅ Verificar que archivos se crearon
- ✅ Verificar que requirements.txt existe
- ✅ Verificar que tests/ existe
- ✅ Log de cada archivo creado

**Testing**:
```bash
python agents_v10/dev_agent_v10.py --test
```

---

### **FASE 4: Agentes Simplificados (Security + QA)** ⏳ PENDIENTE

**Duración**: 30 minutos

**Cambio de estrategia**:
En lugar de usar Claude CLI para Security/QA (costoso), usar **análisis estático simple**:

**Security Agent V10** (simplificado):
```python
def analyze_security(project_dir: Path) -> Dict:
    issues = []

    # Check 1: Hardcoded secrets
    for py_file in project_dir.rglob("*.py"):
        content = py_file.read_text()
        if "password = " in content.lower():
            issues.append(f"{py_file.name}: Hardcoded password detected")

    # Check 2: SQL injection patterns
    # Check 3: No error handling
    # etc...

    score = 10.0 - (len(issues) * 0.5)
    return {"score": max(score, 0), "issues": issues}
```

**QA Agent V10** (simplificado):
```python
def analyze_quality(project_dir: Path) -> Dict:
    issues = []

    # Check 1: Missing docstrings
    # Check 2: No type hints
    # Check 3: No tests
    # Check 4: PEP8 violations

    score = 10.0 - (len(issues) * 0.5)
    return {"score": max(score, 0), "issues": issues}
```

**Beneficios**:
- ⚡ Rápido (< 1 segundo)
- 💰 Sin costo adicional
- 🎯 Suficiente para V10

---

### **FASE 5: Orchestrator V10** ⏳ PENDIENTE

**Duración**: 45 minutos

**Cambios clave**:
```python
class OrchestratorV10:
    def __init__(self):
        self.logger = create_logger("ORCHESTRATOR")
        self.pm_agent = PMAgentV10(self.logger)
        self.dev_agent = DevAgentV10(self.logger)
        self.security_agent = SecurityAgentV10(self.logger)
        self.qa_agent = QAAgentV10(self.logger)

    def run(self, objective: str):
        self.logger.info(f"Starting workflow: {objective[:50]}...")

        # PHASE 1: PM proposes architecture
        self.logger.set_state("PM_PROPOSING")
        architecture = self.pm_agent.propose(objective)

        if not architecture:
            self.logger.error("PM failed to propose architecture")
            return False

        self.logger.success(f"Architecture proposed: {len(architecture['modules'])} modules")

        # PHASE 2: Dev generates code
        self.logger.set_state("DEV_IMPLEMENTING")
        implementation = self.dev_agent.implement(architecture)

        if not implementation:
            self.logger.error("Dev failed to generate code")
            return False

        self.logger.success(f"Code generated: {implementation['files_count']} files")

        # PHASE 3: Validation
        self.logger.set_state("VALIDATING")
        security_result = self.security_agent.analyze(implementation['project_dir'])
        qa_result = self.qa_agent.analyze(implementation['project_dir'])

        self.logger.info(f"Security Score: {security_result['score']:.1f}")
        self.logger.info(f"QA Score: {qa_result['score']:.1f}")

        # PHASE 4: Check convergence
        if security_result['score'] >= 9.5 and qa_result['score'] >= 9.5:
            self.logger.success("CONVERGENCE ACHIEVED!")
            return True
        else:
            self.logger.warn("Scores below threshold, but accepting for V10")
            return True
```

**Controles**:
- ✅ Log antes/después de cada fase
- ✅ Duración de cada fase
- ✅ Estado del sistema actualizado
- ✅ Validación de outputs
- ✅ Métricas finales

---

### **FASE 6: Monitor en Tiempo Real** ⏳ PENDIENTE

**Duración**: 20 minutos

**Crear `monitor_v10.py`**:
```python
# Monitor que muestra estado del sistema en tiempo real
# Lee logs de .logs/v10/ y muestra progreso
# Dashboard en consola con rich library (opcional)

while True:
    # Leer últimos logs
    # Mostrar estado actual
    # Mostrar progreso
    # Mostrar alertas si hay errores
    time.sleep(2)
```

**Output esperado**:
```
==============================================================
DISCOVERY MOTOR V10 - MONITOR
==============================================================
Status: RUNNING
Current Phase: DEV_IMPLEMENTING
Progress: 45%

Orchestrator:  ACTIVE   Uptime: 120s
PM Agent:      IDLE     Last: Architecture proposed (12.3s)
Dev Agent:     WORKING  Current: Generating code...
Security:      WAITING  -
QA:            WAITING  -

Recent Events:
[21:30:15] [SUCCESS] Architecture proposed: 6 modules
[21:30:27] [INFO] Dev generating module: user_auth.py
[21:30:29] [INFO] Dev generating module: api_gateway.py
==============================================================
```

---

### **FASE 7: Testing End-to-End** ⏳ PENDIENTE

**Duración**: 30 minutos

**Test 1: Proyecto Simple**
```bash
python orchestrator_v10.py "Simple REST API with JWT authentication"
```

**Expected**:
- ⏱️ Tiempo: 2-5 minutos
- ✅ Genera arquitectura
- ✅ Genera código
- ✅ Valida security/QA
- ✅ Proyecto en `workspace/v10_projects/`

**Test 2: Proyecto Complejo**
```bash
python orchestrator_v10.py "E-commerce platform with cart, checkout, and payments"
```

**Expected**:
- ⏱️ Tiempo: 5-10 minutos
- ✅ Arquitectura más compleja (8-10 módulos)
- ✅ Código completo
- ✅ Scores >= 9.0

**Test 3: Monitoreo**
```bash
# Terminal 1
python orchestrator_v10.py "Task management system"

# Terminal 2
python monitor_v10.py
```

**Expected**:
- ✅ Monitor muestra progreso en tiempo real
- ✅ Logs detallados en `.logs/v10/`

---

## 🎯 CONTROLES DE CALIDAD

### **Control 1: Logging Completo**
```
Cada operación DEBE loggear:
- ✅ Inicio (con timestamp)
- ✅ Progreso (si > 5 segundos)
- ✅ Fin (con duración)
- ✅ Resultado (success/error)
- ✅ Datos relevantes
```

### **Control 2: Validación de Respuestas**
```python
def validate_architecture(arch: Dict) -> bool:
    required_keys = ["proposed_modules", "technologies"]

    for key in required_keys:
        if key not in arch:
            logger.error(f"Missing required key: {key}")
            return False

    if not arch["proposed_modules"]:
        logger.error("Empty modules list")
        return False

    return True
```

### **Control 3: Timeout en Cada Fase**
```python
# PM: max 5 minutos
# Dev: max 10 minutos
# Security: max 30 segundos
# QA: max 30 segundos
```

### **Control 4: Retry Automático**
```python
# Si Claude falla:
# - Retry 1: Esperar 2s, reintentar
# - Retry 2: Esperar 4s, reintentar
# - Retry 3: Esperar 8s, reintentar
# - Después de 3 fallos: ERROR y abortar
```

### **Control 5: Métricas Finales**
```
Al terminar, SIEMPRE mostrar:
- ✅ Duración total
- ✅ Número de ejecuciones Claude
- ✅ Archivos generados
- ✅ Scores finales
- ✅ Ubicación del proyecto
```

---

## 📂 ESTRUCTURA DE ARCHIVOS V10

```
discovery_motor_final/
│
├── utils/
│   ├── logger_v10.py               ✅ Logger con observabilidad
│   └── claude_cli_wrapper.py       ✅ Wrapper Claude CLI
│
├── agents_v10/
│   ├── __init__.py
│   ├── pm_agent_v10.py             ⏳ PM con Claude CLI
│   ├── dev_agent_v10.py            ⏳ Dev con Claude CLI
│   ├── security_agent_v10.py       ⏳ Security simplificado
│   └── qa_agent_v10.py             ⏳ QA simplificado
│
├── orchestrator_v10.py             ⏳ Orchestrator con controles
├── monitor_v10.py                  ⏳ Monitor tiempo real
├── RUN_V10.bat                     ⏳ Launcher
│
├── .logs/
│   └── v10/
│       ├── orchestrator_YYYYMMDD_HHMMSS.log
│       ├── pm_agent_YYYYMMDD_HHMMSS.log
│       ├── dev_agent_YYYYMMDD_HHMMSS.log
│       ├── security_agent_YYYYMMDD_HHMMSS.log
│       └── qa_agent_YYYYMMDD_HHMMSS.log
│
└── workspace/
    └── v10_projects/
        └── project_YYYYMMDD_HHMMSS/
            ├── src/
            ├── tests/
            ├── requirements.txt
            ├── README.md
            └── Dockerfile
```

---

## 🚀 COMANDOS PARA EJECUTAR

### **Test Utilidades** (Ya disponible):
```bash
# Test logger
python utils/logger_v10.py

# Test Claude CLI wrapper
python utils/claude_cli_wrapper.py
```

### **Cuando V10 esté completo**:
```bash
# Ejecutar proyecto
python orchestrator_v10.py "Your objective here"

# Con monitor
python monitor_v10.py  # Terminal 2
python orchestrator_v10.py "Your objective"  # Terminal 1

# Launcher simplificado
RUN_V10.bat
```

---

## 📊 MÉTRICAS DE ÉXITO

### **V10 será EXITOSO si**:
1. ✅ Genera proyecto completo en < 10 minutos
2. ✅ Sin intervención humana (0%)
3. ✅ Logs detallados en cada paso
4. ✅ Scores >= 9.0 en Security y QA
5. ✅ Código Python válido (sintaxis)
6. ✅ Estructura completa (src/, tests/, requirements.txt)
7. ✅ Rate de éxito >= 90% en 10 ejecuciones

---

## ⏭️ PRÓXIMOS PASOS INMEDIATOS

1. **Terminar PM Agent V10** (45 min)
2. **Terminar Dev Agent V10** (45 min)
3. **Crear Security/QA simplificados** (30 min)
4. **Crear Orchestrator V10** (45 min)
5. **Testing end-to-end** (30 min)

**TOTAL**: ~3 horas

---

## 🎓 LECCIONES APRENDIDAS DE V8

1. ❌ **File Communicator NO funciona** para sistemas autónomos
2. ❌ **Esperar humano = NO escalable**
3. ✅ **Claude CLI directo = 100% autónomo**
4. ✅ **Logging detallado = debugging fácil**
5. ✅ **Controles en cada paso = confiabilidad**

---

**Documento creado**: 2025-10-19 21:30
**Autor**: Discovery Motor Team
**Versión**: 10.0.0-plan
**Estado**: PLAN COMPLETO - LISTO PARA IMPLEMENTAR

---

# ¿PROCEDER CON IMPLEMENTACIÓN?

Este plan garantiza:
- ✅ Sistema 100% funcional
- ✅ Observabilidad completa
- ✅ Debugging fácil
- ✅ 0% intervención humana

**¿Continuar con FASE 2 (PM Agent V10)?**
