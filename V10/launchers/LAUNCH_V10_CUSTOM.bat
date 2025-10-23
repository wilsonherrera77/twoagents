@echo off
REM ============================================================
REM Discovery Motor V10 - Custom Objective Launcher
REM ============================================================
REM Uso: LAUNCH_V10_CUSTOM.bat
REM Permite ingresar tu propio objetivo de forma interactiva
REM ============================================================

REM Cambiar al directorio del script
cd /d "%~dp0"

echo.
echo ============================================================
echo   DISCOVERY MOTOR V10 - CUSTOM LAUNCHER
echo ============================================================
echo.
echo Directorio: %CD%
echo.

REM Limpiar procesos previos
echo [1/5] Limpiando procesos previos...
taskkill /F /IM python.exe /T >nul 2>&1
timeout /t 1 /nobreak >nul

REM Limpiar message queue
echo [2/5] Limpiando message queue...
if exist .agents\pm\inbox\*.json del /Q .agents\pm\inbox\*.json >nul 2>&1
if exist .agents\orchestrator\inbox\*.json del /Q .agents\orchestrator\inbox\*.json >nul 2>&1

REM Verificar directorios
echo [3/5] Verificando directorios...
if not exist .agents\pm\inbox mkdir .agents\pm\inbox
if not exist .agents\orchestrator\inbox mkdir .agents\orchestrator\inbox
if not exist workspace mkdir workspace
if not exist reports mkdir reports

echo.
echo ============================================================
echo   MODO INTERACTIVO - Ingresa tu objetivo
echo ============================================================
echo.
echo Ejemplos:
echo   - Create a REST API with GraphQL and PostgreSQL
echo   - Build a real-time chat application with WebSockets
echo   - Design a machine learning pipeline for image classification
echo   - Create a blockchain-based voting system
echo.
set /p "OBJETIVO=Tu objetivo (en ingles): "

if "%OBJETIVO%"=="" (
    echo.
    echo [ERROR] Debes ingresar un objetivo
    pause
    exit /b 1
)

echo.
set /p "NOMBRE=Nombre del proyecto (opcional, Enter para auto): "

echo.
echo [4/5] Lanzando Terminal 2 - Claude PM Agent (Auto-ejecutando)...
start "V10 T2 - Claude PM Agent" cmd /c "cd /d %CD% && python claude_pm_agent.py"
timeout /t 3 /nobreak >nul

echo [5/5] Lanzando Terminal 1 - Orchestrator...
echo.
echo Objetivo: %OBJETIVO%
if not "%NOMBRE%"=="" echo Nombre: %NOMBRE%
echo.

if "%NOMBRE%"=="" (
    start "V10 T1 - Orchestrator" cmd /c "cd /d %CD% && python orchestrator_v10_async.py \"%OBJETIVO%\" && pause"
) else (
    start "V10 T1 - Orchestrator" cmd /c "cd /d %CD% && python orchestrator_v10_async.py \"%OBJETIVO%\" --name %NOMBRE% && pause"
)

echo.
echo ============================================================
echo   SISTEMA LANZADO - 2 Terminales Claude Colaborando
echo ============================================================
echo.
echo Terminal 1: Orchestrator (coordinador maestro)
echo Terminal 2: Claude PM Agent (analisis de arquitectura)
echo.
echo Comunicacion: Async via filesystem (sin deadlock)
echo.
pause
