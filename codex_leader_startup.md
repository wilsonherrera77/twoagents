# Prompt de ARRANQUE - Agente Líder = Codex (alternativo)

Si prefieres que Codex haga el bootstrap (plan + primer código), usa esto en Codex:

## Prompt para Codex:

```
Contexto:
- Objetivo (pegaré aquí): <<<OBJECTIVE>>>
- Workspace: C:\ai-bridge\workspace\
- Comunicación con Claude con encabezados y timestamps.

Tarea (modo líder):
1) Emite AHORA el PRIMER MENSAJE hacia Claude con:
   - un plan mínimo + 2 decisiones de diseño justificadas en 2 bullets
   - propuesta de estructura de proyecto (lista de rutas)
   - petición de revisión y 1 test inicial por parte de Claude
   - INTENT=design
2) A continuación, entrega 1 archivo inicial (p. ej. "ruta: workspace\src\app.py") con el esqueleto listo.
3) Entrega "INSTRUCCIONES PARA EL USUARIO" (como arriba) para el pegado y seguimiento.

Usa el formato con [TIMESTAMP],[FROM],[TO],[ROLE],[INTENT],[LAST_SEEN],[SUMMARY],[PAYLOAD] y timestamps ISO-8601 UTC.
```