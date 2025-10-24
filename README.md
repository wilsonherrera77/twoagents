# Discovery Motor

Este repositorio aloja la versión V10 del motor autónomo de generación de software. Todas las implementaciones antiguas fueron retiradas para dejar un único stack mantenible basado en agentes Python.

## 📂 Contenido

- `V10/` – Código completo del sistema (agentes, orquestador, protocolos y utilidades).
- `V10/runtime/` – Se crea en tiempo de ejecución y almacena logs, reportes y proyectos generados.

## 🚀 Ejecución rápida

```bash
cd V10
python -m V10.main "Create a booking management API"
```

El comando lanza el Product Manager asíncrono, genera la estructura del proyecto y evalúa seguridad y calidad. El resultado se imprime en JSON y se guarda en `V10/runtime/reports/`.

Consulta `V10/README.md` y `V10/QUICKSTART.md` para más detalles, opciones avanzadas y guía de contribución.

## 🧵 Modo multi-terminal (Fase 1)

El plan Discovery Motor V10 ahora incluye *entry points* independientes para ejecutar cada agente en su propia terminal usando únicamente el `FileMessageBus`. Esta configuración habilita la comunicación asíncrona basada en archivos JSON sin hilos internos.

```
# Terminal 1: Orquestador principal
python orchestrator_main.py "Create a hybrid acquisition engine"

# Terminal 2: Product Manager
python pm_agent_main.py

# Terminal 3: Developer
python dev_agent_main.py

# Terminal 4: QA
python qa_agent_main.py

# Terminal 5: Seguridad
python security_agent_main.py
```

Todos los procesos comparten el mismo runtime en `runtime/agents/<rol>/` y pueden detenerse con `Ctrl+C` o enviando un mensaje `SHUTDOWN`. Esta arquitectura será la base para las fases siguientes (PM inteligente, generación de código adaptativa, QA/Sec avanzados, tooling DevOps, etc.).
