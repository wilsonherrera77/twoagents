@echo off
REM ================================================================================
REM DISCOVERY MOTOR V8 - CLEANUP SCRIPT
REM ================================================================================
REM
REM Este script limpia el entorno V8 antes de un nuevo lanzamiento
REM
REM Acciones:
REM   1. Mata todos los procesos Python de agentes V8
REM   2. Limpia mensajes antiguos (.shared/)
REM   3. Opcional: Limpia workspace (pregunta al usuario)
REM ================================================================================

echo.
echo ================================================================================
echo DISCOVERY MOTOR V8 - CLEANUP
echo ================================================================================
echo.

cd /d "%~dp0"

echo [1/3] Cerrando procesos de agentes V8...
echo.

REM Cerrar ventanas de agentes V8 (graceful)
taskkill /FI "WINDOWTITLE eq *PM AGENT V8*" >nul 2>&1
taskkill /FI "WINDOWTITLE eq *DEV AGENT V8*" >nul 2>&1
taskkill /FI "WINDOWTITLE eq *SECURITY AGENT V8*" >nul 2>&1
taskkill /FI "WINDOWTITLE eq *QA AGENT V8*" >nul 2>&1
taskkill /FI "WINDOWTITLE eq *ORCHESTRATOR V8*" >nul 2>&1

REM Esperar 2 segundos
timeout /t 2 /nobreak >nul

REM Forzar cierre de procesos Python V8 si siguen activos
for /f "tokens=2" %%i in ('tasklist ^| findstr python.exe') do (
    wmic process where "ProcessId=%%i AND (CommandLine like '%%_v8.py%%' OR CommandLine like '%%orchestrator_v8%%')" delete >nul 2>&1
)

echo [OK] Procesos V8 cerrados
echo.

echo [2/3] Limpiando mensajes antiguos (.shared/)...
echo.

REM Limpiar todos los directorios de mensajes V8
if exist ".shared" (
    del /q ".shared\state\*.json" >nul 2>&1
    del /q ".shared\pm\*.json" >nul 2>&1
    del /q ".shared\dev\*.json" >nul 2>&1
    del /q ".shared\validation\*.json" >nul 2>&1
)

echo [OK] Mensajes limpiados
echo.

echo [3/3] Limpieza de workspace (OPCIONAL)
echo.
echo El workspace actual contiene proyectos generados:
echo   workspace\v8_projects\
echo.
choice /C SN /M "Quieres CONSERVAR (S) o LIMPIAR (N) el workspace"

if errorlevel 2 (
    echo.
    echo Limpiando workspace V8...
    if exist "workspace\v8_projects" (
        REM Backup rapido antes de borrar
        set timestamp=%date:~-4%%date:~3,2%%date:~0,2%_%time:~0,2%%time:~3,2%%time:~6,2%
        set timestamp=%timestamp: =0%

        if not exist "workspace\archive" mkdir workspace\archive

        echo Creando backup en workspace\archive\v8_backup_%timestamp%
        xcopy /E /I /Q "workspace\v8_projects" "workspace\archive\v8_backup_%timestamp%" >nul 2>&1

        REM Borrar contenido
        rmdir /s /q "workspace\v8_projects" >nul 2>&1

        echo [OK] Workspace limpiado (backup creado)
    ) else (
        echo [INFO] No hay workspace V8 para limpiar
    )
) else (
    echo [OK] Workspace conservado
)

echo.
echo ================================================================================
echo CLEANUP V8 COMPLETADO
echo ================================================================================
echo.
echo Sistema limpio y listo para nuevo lanzamiento V8.
echo.
echo Para lanzar Discovery Motor V8:
echo   LAUNCH_V8.bat
echo.
pause
