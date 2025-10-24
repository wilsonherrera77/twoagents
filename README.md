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
