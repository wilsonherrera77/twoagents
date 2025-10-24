# Quickstart - Discovery Motor V10

> Tiempo estimado: 2 minutos · Requisitos: Python 3.10+

---

## 1. Preparar el entorno

```bash
python -m venv .venv        # opcional
source .venv/bin/activate    # en Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

---

## 2. Lanzar todo desde el Centro de Control

```bash
python control_center.py "Build a customer onboarding portal" --open-browser
```

Este comando:

1. Arranca el servicio web local de Claude.
2. Abre la interfaz web para responder prompts manualmente.
3. Inicia el orquestador y muestra en vivo los mensajes entre agentes en la misma terminal.

Parámetros útiles:

- `--project-name portal_onboarding` → fuerza el nombre del proyecto generado.
- `--workspace /tmp/v10` → cambia la carpeta base de proyectos y reportes.
- `--skip-service` → usa un servicio Claude que ya esté corriendo en otro terminal.
- `--iterations 5` → ajusta las vueltas máximas del feedback loop.

Durante la ejecución responde los prompts desde `http://localhost:5000` copiando/pegando las respuestas de tu cuenta de Claude.

---

## 3. Revisar resultados

- Código generado: `V10/runtime/projects/<session>/<slug>/`
- Reporte JSON: `V10/runtime/reports/report_YYYYMMDD_HHMMSS.json`
- Logs estructurados: `V10/runtime/logs/<agente>/<fecha>.log`

Al finalizar, el centro de control imprime el JSON completo con métricas, rutas y estado de cada etapa.

---

## 4. Modo avanzado

¿Necesitas integrar la plataforma en tus propias herramientas? Puedes importar `OrchestratorV10Async` o `FileMessageBus` desde `V10.core` y reutilizar la arquitectura multi-agente sin el centro de control.

---

¡Listo! Con un solo comando tienes a todos los agentes colaborando mientras observas cada interacción en tiempo real.
