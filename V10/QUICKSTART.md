# Quickstart - Discovery Motor V10

> Tiempo estimado: 2 minutos · Requisitos: Python 3.10+

---

## 1. Preparar el entorno

```bash
cd V10
python -m venv .venv        # opcional
source .venv/bin/activate    # en Windows: .venv\\Scripts\\activate
```

No hay dependencias adicionales, el proyecto usa únicamente la librería estándar de Python.

---

## 2. Ejecutar el pipeline

```bash
python -m V10.main "Build a customer onboarding portal"
```

El comando lanza automáticamente el Product Manager en segundo plano, genera el proyecto y devuelve un JSON con los resultados del pipeline.

Parámetros útiles:

- `--project-name portal_onboarding` → fuerza el nombre del proyecto.
- `--workspace /tmp/v10` → cambia la carpeta donde se generan los archivos.
- `--pm-timeout 120` → amplía el tiempo máximo de espera del PM Agent.

---

## 3. Revisar resultados

- Código generado: `V10/runtime/workspace/<nombre-proyecto>/`
- Reporte JSON: `V10/runtime/reports/report_YYYYMMDD_HHMMSS.json`
- Logs estructurados: `V10/runtime/logs/<agente>/<fecha>.log`

Ejemplo de reporte parcial:

```json
{
  "status": "PARTIAL_SUCCESS",
  "decision": "REVIEW_REQUIRED",
  "combined_score": 7.5,
  "stages": {
    "pm": {"modules": 6, "status": "SUCCESS"},
    "dev": {"status": "SUCCESS", "files_count": 9},
    "security": {"status": "PASS", "score": 8.0},
    "qa": {"status": "FAIL", "score": 7.0}
  }
}
```

---

## 4. ¿Y si quiero depurar?

```bash
python -m V10.main "Test debug" --no-worker
```

Con `--no-worker` puedes lanzar el orquestador sin iniciar el PM automático. En ese modo podrías desarrollar tu propio consumidor de mensajes leyendo los archivos en `V10/runtime/agents/pm/inbox/`.

---

¡Listo! Ya cuentas con una herramienta autónoma para explorar arquitecturas y generar bases de código iniciales.
