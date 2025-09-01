@echo off
setlocal ENABLEDELAYEDEXPANSION
title AI-Bridge Launcher
echo ========================================
echo AI-Bridge: Lanzando servicios
echo - Frontend/API:    http://localhost:8080
echo - Claude-B Server: http://localhost:8081
echo - Watcher:         simple-watcher.ps1
echo ========================================
echo [POLITICA] Los agentes estan AUTORIZADOS para usar los recursos locales de la PC sin restricciones para alcanzar el objetivo (sin solicitar aprobaciones intermedias).
echo.

cd /d "%~dp0"

REM Lanzar Frontend/API (8080)
start "AI-Bridge Frontend (8080)" cmd /k python server.py

REM Lanzar Claude-B (8081)
start "Claude-B Server (8081)" cmd /k python claude-b-server.py

REM Lanzar Watcher
start "AI-Bridge Watcher" powershell -ExecutionPolicy Bypass -NoLogo -NoProfile -File "%CD%\simple-watcher.ps1"

echo Servicios lanzados. Presiona una tecla para salir de este lanzador...
pause >nul
