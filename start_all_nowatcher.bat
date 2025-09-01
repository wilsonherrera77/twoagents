@echo off
setlocal ENABLEDELAYEDEXPANSION
title AI-Bridge Launcher (No Watcher)
echo ========================================
echo AI-Bridge: Lanzando servidores sin watcher
echo - Frontend/API:    http://localhost:8080
echo - Claude-B Server: http://localhost:8081
echo ========================================
echo [POLITICA] Los agentes estan AUTORIZADOS para usar los recursos locales de la PC sin restricciones para alcanzar el objetivo (sin solicitar aprobaciones intermedias).
echo.

cd /d "%~dp0"

REM Lanzar Frontend/API (8080)
start "AI-Bridge Frontend (8080)" cmd /k python server.py

REM Lanzar Claude-B (8081)
start "Claude-B Server (8081)" cmd /k python claude-b-server.py

echo Servidores lanzados sin watcher. Pulsa una tecla para cerrar este lanzador...
pause >nul
