@echo off
REM ============================================================
REM Discovery Motor V10 - Dual Claude Terminal Launcher
REM ============================================================
REM
REM Este script lanza dos terminales Claude que colaboran:
REM - Terminal 1: Orchestrator V10 Async
REM - Terminal 2: Claude PM Agent
REM
REM Innovacion: Sin deadlock gracias a async message queue
REM ============================================================

REM Cambiar al directorio del script
cd /d "%~dp0"

echo.
echo ============================================================
echo   DISCOVERY MOTOR V10 - DUAL CLAUDE LAUNCHER
echo ============================================================
echo.
echo Directorio de trabajo: %CD%
echo.

REM Paso 1: Limpiar procesos previos de Python que puedan estar corriendo
echo [PASO 1] Limpiando procesos Python previos...
taskkill /F /IM python.exe /T >nul 2>&1
timeout /t 2 /nobreak >nul
echo [OK] Procesos Python cerrados

REM Paso 2: Limpiar mensajes antiguos del filesystem message queue
echo.
echo [PASO 2] Limpiando message queue...
if exist .agents\pm\inbox\*.json del /Q .agents\pm\inbox\*.json >nul 2>&1
if exist .agents\orchestrator\inbox\*.json del /Q .agents\orchestrator\inbox\*.json >nul 2>&1
echo [OK] Message queue limpiado

REM Paso 3: Crear directorios necesarios
echo.
echo [PASO 3] Verificando directorios...
if not exist .agents\pm\inbox mkdir .agents\pm\inbox
if not exist .agents\pm\outbox mkdir .agents\pm\outbox
if not exist .agents\orchestrator\inbox mkdir .agents\orchestrator\inbox
if not exist .agents\orchestrator\outbox mkdir .agents\orchestrator\outbox
if not exist workspace mkdir workspace
if not exist reports mkdir reports
echo [OK] Directorios verificados

REM Paso 4: Lanzar Terminal 2 (Claude PM Agent) primero
echo.
echo [PASO 4] Lanzando Terminal 2 - Claude PM Agent (Auto-ejecutando)...
echo.
start "V10 - TERMINAL 2 - Claude PM Agent" cmd /c "cd /d %CD% && python claude_pm_agent.py"
timeout /t 3 /nobreak >nul
echo [OK] Terminal 2 lanzada

REM Paso 5: Lanzar Terminal 1 (Orchestrator) con objetivo
echo.
echo [PASO 5] Lanzando Terminal 1 - Orchestrator V10...
echo.

REM Aqui puedes cambiar el objetivo del proyecto
set "OBJETIVO=Create a distributed microservices architecture with message queue pattern, API gateway, service discovery, and monitoring dashboard"

echo Objetivo: %OBJETIVO%
echo.

REM Lanzar orchestrator SIN --no-claude-pm para usar Claude PM real
start "V10 - TERMINAL 1 - Orchestrator" cmd /c "cd /d %CD% && python orchestrator_v10_async.py \"%OBJETIVO%\" --name microservices_demo && pause"

echo [OK] Terminal 1 lanzada
echo.
echo ============================================================
echo   SISTEMA V10 LANZADO EXITOSAMENTE
echo ============================================================
echo.
echo Ahora tienes DOS terminales Claude colaborando:
echo.
echo   Terminal 1 (Orchestrator):
echo   - Coordina el pipeline completo
echo   - Envia mensajes via filesystem
echo   - Espera respuestas sin bloqueo
echo.
echo   Terminal 2 (Claude PM Agent):
echo   - Lee mensajes del filesystem
echo   - Analiza objetivo con inteligencia Claude
echo   - Escribe respuesta asincrona
echo.
echo Innovacion V10: Sin deadlock gracias a async message queue
echo.
echo Presiona cualquier tecla para cerrar este launcher...
pause >nul
