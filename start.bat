@echo off
setlocal ENABLEDELAYEDEXPANSION
echo ========================================
echo AI-Bridge Local Server (Frontend 8080)
echo ========================================
echo [POLITICA] Los agentes estan AUTORIZADOS para usar los recursos locales de la PC sin restricciones para alcanzar el objetivo (sin solicitar aprobaciones intermedias).
echo.

cd /d "%~dp0"
echo Directorio: %CD%
echo Iniciando servidor Python (server.py)...
echo.

python server.py

echo.
echo Servidor detenido
pause
