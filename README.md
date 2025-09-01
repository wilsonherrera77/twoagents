# AI-Bridge: Herramienta Semi-Asistida de Desarrollo Colaborativo

Sistema de comunicación estructurada entre dos agentes IA para desarrollo colaborativo de software.

## Estructura del Proyecto

```
C:\ai-bridge\
├─ objective.txt            # Objetivo inicial definido por el usuario
├─ to_claude.txt            # Mensaje que viaja hacia Claude
├─ to_codex.txt             # Mensaje que viaja hacia Codex
├─ log_claude.md            # Bitácora de lo que vio Claude
├─ log_codex.md             # Bitácora de lo que vio Codex
├─ send-to-codex.ps1        # Script para enviar mensajes a Codex
├─ send-to-claude.ps1       # Script para enviar mensajes a Claude
├─ claude_mentor_prompt.md  # Plantilla de prompt para Claude (Mentor)
├─ codex_implementer_prompt.md # Plantilla de prompt para Codex (Implementador)
├─ claude_leader_startup.md # Prompt de arranque con Claude como líder
├─ codex_leader_startup.md  # Prompt de arranque con Codex como líder
└─ workspace\               # Carpeta compartida para código y archivos
```

## Protocolo de Mensajería

Cada mensaje utiliza este formato con timestamp ISO-8601 UTC:

```
[TIMESTAMP]: YYYY-MM-DDTHH:mm:ssZ
[FROM]: Claude|Codex
[TO]: Codex|Claude
[ROLE]: Mentor|Implementador|Colaborativo
[INTENT]: plan|design|code|review|test|refactor|ask|done
[LAST_SEEN]: <TIMESTAMP del último mensaje recibido de tu contraparte>
[SUMMARY]:
- punto1
- punto2
- punto3
[PAYLOAD]:
(contenido del mensaje, código con rutas especificadas)
```

## Uso Básico

### 1. Definir Objetivo
Edita `C:\ai-bridge\objective.txt` con una línea clara (1-3 frases):
```
Construir una API en FastAPI que reciba un CSV, calcule estadísticas por columna y devuelva JSON, con /health y tests.
```

### 2. Inicializar Agente Líder
Elige Claude o Codex como líder y usa el prompt correspondiente:
- **Claude (recomendado)**: `claude_leader_startup.md`
- **Codex**: `codex_leader_startup.md`

### 3. Intercambio de Mensajes
1. Copia la respuesta del agente líder al archivo correspondiente (`to_codex.txt` o `to_claude.txt`)
2. Ejecuta el script correspondiente:
   ```powershell
   # Primer turno
   .\send-to-codex.ps1 -LastSeen "none"
   # o
   .\send-to-claude.ps1 -LastSeen "none"
   
   # Turnos subsiguientes  
   .\send-to-codex.ps1 -LastSeen "2025-08-31T21:05:12Z"
   ```
3. Pega el contenido del portapapeles en el otro agente
4. Repite el proceso con la respuesta

### 4. Finalización
El proceso termina cuando algún agente emite `INTENT: done`.

## Comando Útil para Timestamp

```powershell
(Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
```

## Reglas de Oro

1. **Siempre actualiza [LAST_SEEN]** con el [TIMESTAMP] del último mensaje recibido
2. **Si hay mensajes cruzados**, usa el de TIMESTAMP más reciente
3. **Código completo con rutas**: cada archivo debe incluir ruta y contenido completo
4. **Máximo 3 bullets en [SUMMARY]** para lectura rápida
5. **Workspace compartido**: ambos agentes guardan/leen de `C:\ai-bridge\workspace\`
## Lanzamiento r�pido

- Iniciar solo frontend/API (8080):
  - start.bat
  - o python server.py

- Iniciar todo (8080, 8081 y watcher):
  - start_all.bat

## Notas
- Requiere Python 3.x en PATH.
- Los servicios se exponen en http://localhost:8080 y http://localhost:8081.
- El Watcher monitorea C:\ai-bridge\messages.
- Evita caracteres no ASCII si usas Invoke-RestMethod antiguo. El servidor ahora intenta decodificar UTF-8 con fallback.
