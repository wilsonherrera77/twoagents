# AI-Bridge: Herramienta Semi-Asistida de Desarrollo Colaborativo

Sistema de comunicaciÃ³n estructurada entre dos agentes IA para desarrollo colaborativo de software.

## Estructura del Proyecto

```
C:\ai-bridge\
â”œâ”€ objective.txt            # Objetivo inicial definido por el usuario
â”œâ”€ to_claude.txt            # Mensaje que viaja hacia Claude
â”œâ”€ to_codex.txt             # Mensaje que viaja hacia Codex
â”œâ”€ log_claude.md            # BitÃ¡cora de lo que vio Claude
â”œâ”€ log_codex.md             # BitÃ¡cora de lo que vio Codex
â”œâ”€ send-to-codex.ps1        # Script para enviar mensajes a Codex
â”œâ”€ send-to-claude.ps1       # Script para enviar mensajes a Claude
â”œâ”€ claude_mentor_prompt.md  # Plantilla de prompt para Claude (Mentor)
â”œâ”€ codex_implementer_prompt.md # Plantilla de prompt para Codex (Implementador)
â”œâ”€ claude_leader_startup.md # Prompt de arranque con Claude como lÃ­der
â”œâ”€ codex_leader_startup.md  # Prompt de arranque con Codex como lÃ­der
â””â”€ workspace\               # Carpeta compartida para cÃ³digo y archivos
```

## Protocolo de MensajerÃ­a

Cada mensaje utiliza este formato con timestamp ISO-8601 UTC:

```
[TIMESTAMP]: YYYY-MM-DDTHH:mm:ssZ
[FROM]: Claude|Codex
[TO]: Codex|Claude
[ROLE]: Mentor|Implementador|Colaborativo
[INTENT]: plan|design|code|review|test|refactor|ask|done
[LAST_SEEN]: <TIMESTAMP del Ãºltimo mensaje recibido de tu contraparte>
[SUMMARY]:
- punto1
- punto2
- punto3
[PAYLOAD]:
(contenido del mensaje, cÃ³digo con rutas especificadas)
```

## Uso BÃ¡sico

### 1. Definir Objetivo
Edita `C:\ai-bridge\objective.txt` con una lÃ­nea clara (1-3 frases):
```
Construir una API en FastAPI que reciba un CSV, calcule estadÃ­sticas por columna y devuelva JSON, con /health y tests.
```

### 2. Inicializar Agente LÃ­der
Elige Claude o Codex como lÃ­der y usa el prompt correspondiente:
- **Claude (recomendado)**: `claude_leader_startup.md`
- **Codex**: `codex_leader_startup.md`

### 3. Intercambio de Mensajes
1. Copia la respuesta del agente lÃ­der al archivo correspondiente (`to_codex.txt` o `to_claude.txt`)
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


### Ejecucion con `start_all.bat`

En Windows, abre una consola en la carpeta del proyecto y ejecuta:

```bat
start_all.bat
```

Se abriran tres ventanas (API, Claude-B y watcher). El watcher esta en modo productivo cuando su consola muestra mensajes como:

- `Starting Simple File Watcher for AI-Bridge...`
- `Monitoring directory: C:\ai-bridge\messages`
- `Watching for: to_claude-b.txt, from_claude-b.txt, and to_claude-a.txt`

Si la ventana del watcher se cierra automaticamente, revisa que `workspace/` contenga al menos un archivo; el watcher se detiene tras dos iteraciones si el directorio sigue vacio.

### 4. FinalizaciÃ³n
El proceso termina cuando algÃºn agente emite `INTENT: done`.

## Comando Ãštil para Timestamp

```powershell
(Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
```

## Reglas de Oro

1. **Siempre actualiza [LAST_SEEN]** con el [TIMESTAMP] del Ãºltimo mensaje recibido
2. **Si hay mensajes cruzados**, usa el de TIMESTAMP mÃ¡s reciente
3. **CÃ³digo completo con rutas**: cada archivo debe incluir ruta y contenido completo
4. **MÃ¡ximo 3 bullets en [SUMMARY]** para lectura rÃ¡pida
5. **Workspace compartido**: ambos agentes guardan/leen de `C:\ai-bridge\workspace\`
## Lanzamiento rápido

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
