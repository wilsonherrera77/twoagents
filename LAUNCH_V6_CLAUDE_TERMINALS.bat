@echo off
REM ================================================================================
REM DISCOVERY MOTOR V6 - CLAUDE CODE MULTI-TERMINAL LAUNCHER
REM ================================================================================
REM
REM Lanza 6 terminales Claude Code colaborando con inteligencia REAL:
REM   1. Orchestrator (Alex) - Coordina proyecto
REM   2. PM Agent (Morgan) - Analisis de negocio y arquitectura
REM   3. Dev Agent (Jordan) - Desarrollo incremental
REM   4. Security Agent (Jorge) - Validacion OWASP Top 10
REM   5. QA Agent (Leidy) - Tests y coverage >95%
REM   6. UX/UI Agent - Diseno de interfaces (NUEVO)
REM
REM Principios:
REM   - SIN API keys (usa membresia Claude Code)
REM   - SIN templates (Claude razona en tiempo real)
REM   - Comunicacion filesystem (asyncrona)
REM   - Mejora incremental (1 proyecto)
REM   - Git tracking + rollback
REM ================================================================================

echo.
echo ================================================================================
echo DISCOVERY MOTOR V6 - CLAUDE CODE MULTI-TERMINAL
echo ================================================================================
echo.
echo Sistema de desarrollo autonomo con inteligencia REAL de Claude
echo.
echo ARQUITECTURA:
echo   - 6 terminales Claude Code independientes
echo   - Comunicacion via filesystem (.agents/)
echo   - Mejora incremental de 1 proyecto
echo   - Git tracking por iteracion
echo   - Rollback automatico si regresion
echo.
echo AGENTES:
echo   1. Orchestrator (Alex) - Coordinador estrategico
echo   2. PM Agent (Morgan) - Analista de negocio
echo   3. Dev Agent (Jordan) - Desarrollador pragmatico
echo   4. Security Agent (Jorge) - Experto en seguridad
echo   5. QA Agent (Leidy) - Quality assurance
echo   6. UX/UI Agent - Frontend/Diseno (INNOVACION)
echo.
echo PRINCIPIOS V6:
echo   - NO API keys (solo membresia Claude Code)
echo   - NO templates (inteligencia real)
echo   - SI colaboracion entre Claudes
echo   - SI convergencia garantizada
echo.
echo ================================================================================
echo.

REM Verificar archivos del sistema
if not exist "TERMINAL_1_ORCHESTRATOR_V6.md" (
    echo [ERROR] No se encuentran archivos TERMINAL_*.md
    echo Asegurate de estar en el directorio discovery_motor_final
    pause
    exit /b 1
)

echo [OK] Archivos del sistema encontrados
echo.

REM Limpiar inbox/outbox de agentes
echo Limpiando mensajes antiguos...
if exist ".agents" (
    for /d %%D in (.agents\*) do (
        if exist "%%D\inbox" del /q "%%D\inbox\*" 2>nul
        if exist "%%D\outbox" del /q "%%D\outbox\*" 2>nul
    )
)
echo [OK] Mensajes limpiados
echo.

REM Crear directorios necesarios
if not exist ".agents\orchestrator\inbox" mkdir .agents\orchestrator\inbox
if not exist ".agents\orchestrator\outbox" mkdir .agents\orchestrator\outbox
if not exist ".agents\pm\inbox" mkdir .agents\pm\inbox
if not exist ".agents\pm\outbox" mkdir .agents\pm\outbox
if not exist ".agents\dev\inbox" mkdir .agents\dev\inbox
if not exist ".agents\dev\outbox" mkdir .agents\dev\outbox
if not exist ".agents\security\inbox" mkdir .agents\security\inbox
if not exist ".agents\security\outbox" mkdir .agents\security\outbox
if not exist ".agents\qa\inbox" mkdir .agents\qa\inbox
if not exist ".agents\qa\outbox" mkdir .agents\qa\outbox
if not exist ".agents\ux\inbox" mkdir .agents\ux\inbox
if not exist ".agents\ux\outbox" mkdir .agents\ux\outbox

if not exist "workspace\current_project" mkdir workspace\current_project
if not exist "workspace\snapshots" mkdir workspace\snapshots
if not exist "workspace\archive" mkdir workspace\archive

echo [OK] Directorios de workspace listos
echo.

echo ================================================================================
echo LANZANDO 6 TERMINALES CLAUDE CODE...
echo ================================================================================
echo.
echo IMPORTANTE:
echo   - Cada terminal es Claude Code CLI con inteligencia REAL
echo   - NO son scripts automaticos (son sesiones Claude interactivas)
echo   - TU copiaras/pegaras el codigo de cada TERMINAL_*.md en su terminal
echo   - Los agentes se comunican via archivos JSON en .agents/
echo.
echo SE ABRIRAN 6 VENTANAS:
echo.

pause

REM ================================================================================
REM LANZAR TERMINALES CLAUDE CODE
REM ================================================================================

echo [1/6] Abriendo Terminal 1 - ORCHESTRATOR (Alex)...
echo        Archivo: TERMINAL_1_ORCHESTRATOR_V6.md
start "ORCHESTRATOR V6 (Alex)" cmd /k "type TERMINAL_1_ORCHESTRATOR_V6.md && echo. && echo ============================================================== && echo COPIA EL CODIGO ARRIBA Y PEGALO EN CLAUDE CODE && echo =============================================================="
timeout /t 3 /nobreak >nul

echo [2/6] Abriendo Terminal 2 - PM AGENT (Morgan)...
echo        Archivo: TERMINAL_2_PM_V6.md
start "PM AGENT V6 (Morgan)" cmd /k "type TERMINAL_2_PM_V6.md && echo. && echo ============================================================== && echo COPIA EL CODIGO ARRIBA Y PEGALO EN CLAUDE CODE && echo =============================================================="
timeout /t 3 /nobreak >nul

echo [3/6] Abriendo Terminal 3 - DEV AGENT (Jordan)...
echo        Archivo: TERMINAL_3_DEV_V6.md
start "DEV AGENT V6 (Jordan)" cmd /k "type TERMINAL_3_DEV_V6.md && echo. && echo ============================================================== && echo COPIA EL CODIGO ARRIBA Y PEGALO EN CLAUDE CODE && echo =============================================================="
timeout /t 3 /nobreak >nul

echo [4/6] Abriendo Terminal 4 - SECURITY AGENT (Jorge)...
echo        Archivo: TERMINAL_4_SECURITY_V6.md
start "SECURITY AGENT V6 (Jorge)" cmd /k "type TERMINAL_4_SECURITY_V6.md && echo. && echo ============================================================== && echo COPIA EL CODIGO ARRIBA Y PEGALO EN CLAUDE CODE && echo =============================================================="
timeout /t 3 /nobreak >nul

echo [5/6] Abriendo Terminal 5 - QA AGENT (Leidy)...
echo        Archivo: TERMINAL_5_QA_V6.md
start "QA AGENT V6 (Leidy)" cmd /k "type TERMINAL_5_QA_V6.md && echo. && echo ============================================================== && echo COPIA EL CODIGO ARRIBA Y PEGALO EN CLAUDE CODE && echo =============================================================="
timeout /t 3 /nobreak >nul

echo [6/6] Abriendo Terminal 6 - UX/UI AGENT...
echo        Archivo: TERMINAL_6_UX_V6.md
start "UX/UI AGENT V6" cmd /k "type TERMINAL_6_UX_V6.md && echo. && echo ============================================================== && echo COPIA EL CODIGO ARRIBA Y PEGALO EN CLAUDE CODE && echo =============================================================="
timeout /t 3 /nobreak >nul

echo.
echo ================================================================================
echo 6 TERMINALES ABIERTAS
echo ================================================================================
echo.
echo PROXIMO PASO:
echo.
echo 1. En CADA ventana, abre Claude Code CLI:
echo      $ claude
echo.
echo 2. COPIA el codigo Python que se muestra en cada ventana
echo.
echo 3. PEGALO en la sesion Claude Code correspondiente
echo.
echo 4. Claude ejecutara el codigo con su inteligencia REAL
echo.
echo 5. El Terminal 1 (Orchestrator) te pedira el objetivo del proyecto
echo.
echo 6. Los 6 Claudes colaboraran automaticamente via filesystem
echo.
echo 7. Veras la conversacion en tiempo real en cada terminal
echo.
echo ================================================================================
echo.
echo EJEMPLO DE OBJETIVO:
echo   "Create a task management app with real-time sync, JWT auth, and admin dashboard"
echo.
echo RESULTADO ESPERADO:
echo   - Iteraciones: 5-10
echo   - Tiempo: 20-30 minutos
echo   - Convergencia: 100%% (Security >= 9.5, QA >= 9.5, UX >= 9.0)
echo   - Proyecto: workspace/current_project/ (fullstack completo)
echo.
echo ================================================================================
echo.
echo TIP: Yo (este Claude en la terminal donde corriste el .bat) puedo MONITOREAR
echo      en tiempo real y hacer AJUSTES sin parar el proceso si ves bloqueos.
echo.
echo      Para monitorizacion activa, usame para:
echo        - Ver logs: dialogue_logs/
echo        - Ver mensajes: .agents/*/inbox/
echo        - Ver commits: cd workspace/current_project && git log
echo        - Inyectar mensajes de correccion si algo falla
echo        - Modificar codigo en caliente
echo.
echo ================================================================================
echo.

pause

echo.
echo Sistema listo. Los 6 Claudes estan esperando tus instrucciones.
echo.
echo Buena suerte! :)
echo.
