# Prompt de ARRANQUE - Agente Líder = Claude (recomendado)

Copia el contenido de `objective.txt` y sustitúyelo donde dice `<<<OBJECTIVE>>>`.

## Prompt para Claude:

```
Contexto:
- Objetivo del usuario (pegaré aquí): <<<OBJECTIVE>>>
- Carpeta de trabajo compartida: C:\ai-bridge\workspace\
- Comunicación con otro agente (Codex) por mensajes con encabezado y timestamps.
- Ambos verán y comentarán el código en la carpeta compartida.

Tarea (modo líder):
1) Produce AHORA el PRIMER MENSAJE hacia Codex con:
   - Plan en bullets, interfaces y criterios de éxito
   - 3 casos borde
   - Petición de EXACTAMENTE 2 archivos iniciales (rutas dentro de C:\ai-bridge\workspace\)
   - INTENT=plan
2) Luego, genera un segundo bloque (separado) titulado "INSTRUCCIONES PARA EL USUARIO" explicando:
   - Dónde pegar el mensaje (to_codex.txt)
   - El valor de [LAST_SEEN] que debe colocar (usa "none" para el primer turno)
   - Cómo verificar y continuar el intercambio.

Formato del mensaje a Codex: usa el contrato con [TIMESTAMP],[FROM],[TO],[ROLE],[INTENT],[LAST_SEEN],[SUMMARY],[PAYLOAD].
Recuerda usar ISO-8601 UTC para TIMESTAMP (ejemplo: 2025-08-31T21:07:00Z).
```