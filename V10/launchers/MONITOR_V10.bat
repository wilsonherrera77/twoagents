@echo off
REM ============================================================
REM Discovery Motor V10 - Real-Time Monitor
REM ============================================================
REM Monitorea el sistema V10 en tiempo real:
REM - Message queue activity
REM - Procesos Python
REM - Logs recientes
REM ============================================================

cd /d "%~dp0"

:MONITOR_LOOP
cls
echo ============================================================
echo   DISCOVERY MOTOR V10 - MONITOR EN TIEMPO REAL
echo ============================================================
echo.
echo Timestamp: %DATE% %TIME%
echo.

REM 1. Estado de procesos Python
echo [1] PROCESOS PYTHON ACTIVOS:
echo ------------------------------------------------------------
tasklist /FI "IMAGENAME eq python.exe" /FO TABLE 2>nul | find /I "python.exe" || echo   (Ningun proceso Python activo)
echo.

REM 2. Message Queue - PM Inbox
echo [2] MESSAGE QUEUE - PM INBOX:
echo ------------------------------------------------------------
if exist .agents\pm\inbox\*.json (
    for %%F in (.agents\pm\inbox\*.json) do (
        echo   [PENDIENTE] %%~nxF - %%~zF bytes
    )
) else (
    echo   (Vacio - PM no tiene mensajes pendientes)
)
echo.

REM 3. Message Queue - Orchestrator Inbox
echo [3] MESSAGE QUEUE - ORCHESTRATOR INBOX:
echo ------------------------------------------------------------
if exist .agents\orchestrator\inbox\*.json (
    for %%F in (.agents\orchestrator\inbox\*.json) do (
        echo   [RECIBIDO] %%~nxF - %%~zF bytes
    )
) else (
    echo   (Vacio - Orchestrator no tiene respuestas)
)
echo.

REM 4. Proyectos generados recientemente
echo [4] PROYECTOS GENERADOS (ultimos 5):
echo ------------------------------------------------------------
if exist workspace\ (
    dir /B /O:-D workspace 2>nul | findstr /V /C:"test_project" | findstr /V /C:"audit_test" > temp_projects.txt
    set /a count=0
    for /F "tokens=*" %%D in (temp_projects.txt) do (
        set /a count+=1
        if !count! LEQ 5 (
            if exist "workspace\%%D\" (
                echo   [%%D]
                for /F %%S in ('dir /S /B "workspace\%%D\*.py" 2^>nul ^| find /C ".py"') do echo      - %%S archivos Python
            )
        )
    )
    del temp_projects.txt 2>nul
) else (
    echo   (No hay proyectos generados aun)
)
echo.

REM 5. Reportes recientes
echo [5] REPORTES GENERADOS (ultimo):
echo ------------------------------------------------------------
if exist reports\v10_async_*.json (
    for /F "delims=" %%F in ('dir /B /O:-D reports\v10_async_*.json 2^>nul') do (
        echo   [ULTIMO] %%F
        goto :FOUND_REPORT
    )
    :FOUND_REPORT
) else (
    echo   (No hay reportes generados)
)
echo.

REM 6. Logs mas recientes
echo [6] LOGS RECIENTES (ultimas 3 lineas):
echo ------------------------------------------------------------
if exist .logs\v10\ (
    for /F "delims=" %%L in ('dir /B /O:-D .logs\v10\*.log 2^>nul') do (
        echo   De: %%L
        for /F "skip=1 tokens=*" %%A in ('more +0 ".logs\v10\%%L" 2^>nul ^| findstr /N "^" ^| findstr /B ".*:.*" ^| more +-%^|-%') do echo     %%A
        goto :DONE_LOGS
    )
    :DONE_LOGS
) else (
    echo   (No hay logs aun)
)
echo.

echo ============================================================
echo Actualizando en 3 segundos... (Ctrl+C para salir)
echo ============================================================

timeout /t 3 /nobreak >nul
goto :MONITOR_LOOP
