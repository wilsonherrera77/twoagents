# Discovery Motor V10

V10 es una plataforma autónoma que genera prototipos de software usando un flujo de cuatro agentes (PM → Dev → Security → QA). La versión incluida en este repositorio elimina dependencias manuales, normaliza los protocolos de mensajería y ofrece un **pipeline reproducible de punta a punta** que puede ejecutarse con un único comando de Python.

---

## 🚀 Capacidades principales

- **Orquestación asíncrona real**: El orquestador se comunica con el Product Manager mediante un *message bus* basado en archivos. El PM se ejecuta en un hilo independiente y responde sin intervención humana.
- **Generación de proyectos reproducibles**: El Dev Agent crea estructuras completas (`src/`, `tests/`, `docs/`, `config/`) a partir de la arquitectura propuesta.
- **Auditorías estáticas automáticas**: Los agentes de Seguridad y QA puntúan el proyecto y generan reportes JSON persistidos en `runtime/reports/`.
- **Logs estructurados**: Todos los agentes comparten un logger consistente que escribe en consola y en `runtime/logs/`.

---

## 🧱 Arquitectura

```
┌────────────┐       send()        ┌────────────┐
│ Orchestrator│ ───────────────▶   │  PM Agent  │
│ (Python)    │ ◀───────────────   │ (worker)   │
└────┬───────┘       reply()       └────┬───────┘
     │                                  │
     │         Architecture              │
     ▼                                  ▼
┌────────────┐   ┌────────────┐   ┌────────────┐
│ Dev Agent  │ → │ Security    │ → │ QA Agent   │
│ (code gen) │   │ (checks)    │   │ (quality)  │
└────────────┘   └────────────┘   └────────────┘
```

- **FileMessageBus** (`core/message_bus.py`): implementa la cola de mensajes en `runtime/agents/<nombre>/inbox`. Soporta correlación de respuestas, timeouts y manejo de errores.
- **OrchestratorV10Async** (`core/orchestrator_v10_async.py`): coordina las etapas, aplica los *quality gates* y genera reportes.
- **PMAgentV10** (`agents/pm_agent_v10.py`): traduce objetivos de negocio a arquitecturas detalladas basadas en plantillas inteligentes.
- **Dev/Security/QA Agents** (`agents/*.py`): generan el proyecto, ejecutan heurísticas de seguridad y validan calidad.

---

## 📦 Estructura del repositorio

```
V10/
├── agents/                # Implementaciones de los agentes autónomos
│   ├── __init__.py
│   ├── dev_agent_v10.py
│   ├── pm_agent_v10.py
│   ├── qa_agent_v10.py
│   └── security_agent_v10.py
├── core/                  # Orquestador y message bus
│   ├── __init__.py
│   ├── message_bus.py
│   └── orchestrator_v10_async.py
├── protocols/             # Dataclasses compartidas
│   ├── __init__.py
│   └── messages.py
├── utils/                 # Logger y utilidades de runtime
│   ├── __init__.py
│   ├── logger.py
│   └── runtime.py
├── main.py                # Punto de entrada CLI (`python -m V10.main`)
├── QUICKSTART.md          # Guía rápida de ejecución
└── README.md              # Este documento
```

Durante la ejecución se generan directorios adicionales dentro de `V10/runtime/` (logs, reports, workspace, etc.).

---

## ▶️ Ejecución rápida

```bash
cd V10
python -m V10.main "Build a REST API for managing tasks"
```

Argumentos útiles:

- `--project-name my_app` para fijar el nombre del proyecto.
- `--workspace /ruta/custom` para cambiar la salida del código generado.
- `--pm-timeout 120` si deseas ampliar el tiempo de espera del PM Agent.

El comando devuelve un JSON con el resultado del pipeline. Los proyectos generados se ubican en `V10/runtime/workspace/` y los reportes en `V10/runtime/reports/`.

---

## ✅ Calidad y monitoreo

- **Logs**: revisa `V10/runtime/logs/<agente>/<fecha>.log`.
- **Reportes**: cada ejecución guarda un archivo `report_YYYYMMDD_HHMMSS.json`.
- **Re-ejecución**: los directorios `runtime/agents/<rol>/inbox` se limpian automáticamente después de cada mensaje.

---

## 🛠️ Requisitos y pruebas

- Python 3.10 o superior.
- No necesita dependencias externas.
- Para validar el correcto funcionamiento basta con ejecutar `python -m V10.main "Describe your project"`; se crearán módulos, pruebas y un reporte final.

---

## 🤝 Contribuciones

1. Ejecuta `python -m V10.main ...` y verifica que el pipeline finaliza con `status = "SUCCESS"` o `"PARTIAL_SUCCESS"`.
2. Adjunta el archivo de reporte generado en `runtime/reports/` como evidencia.
3. Sigue la estructura modular descrita arriba para agregar nuevas capacidades o agentes.

---

¿Dudas o mejoras? Crea un issue con el objetivo del proyecto y el resultado obtenido; así podremos ajustar la heurística de los agentes.
