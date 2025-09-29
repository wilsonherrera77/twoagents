@echo off
REM Sistema de Agentes Autonomos - Lanzador Principal
echo ========================================
echo  SISTEMA DE AGENTES AUTONOMOS
echo ========================================
echo.

REM Cambiar al directorio correcto
cd /d "%~dp0"

REM Verificar Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python no encontrado. Instale Python primero.
    pause
    exit /b 1
)

echo Python detectado correctamente
echo.

REM Verificar e instalar dependencias
echo Verificando dependencias...
python -c "import flask, tkinter" 2>nul
if %errorlevel% neq 0 (
    echo Instalando Flask...
    pip install flask
)

echo.
echo ==========================================
echo OPCIONES DE LANZAMIENTO:
echo ==========================================
echo.
echo 1. INTERFAZ WEB (Recomendado)
echo    - Selector de carpeta en navegador
echo    - Monitoreo visual en tiempo real
echo    - Descarga de resultados
echo.
echo 2. LINEA DE COMANDOS
echo    - Control directo desde terminal
echo    - Selector de carpeta grafico
echo.
echo 3. TEST DE COMUNICACION
echo    - Verificar funcionamiento del sistema
echo.
echo Q. SALIR
echo.

choice /c 123Q /m "Seleccione [1]Web [2]CLI [3]Test [Q]Salir"

if %errorlevel%==1 goto web_interface
if %errorlevel%==2 goto cli_interface
if %errorlevel%==3 goto test_system
if %errorlevel%==4 goto end

:web_interface
echo.
echo ==========================================
echo LANZANDO INTERFAZ WEB
echo ==========================================
echo.
echo INICIANDO SERVIDOR WEB...
echo.
echo Abre tu navegador en: http://localhost:5000
echo Presiona Ctrl+C para detener
echo.
python web_interface.py
goto end

:cli_interface
echo.
echo ==========================================
echo INTERFAZ DE LINEA DE COMANDOS
echo ==========================================
echo.
set /p objective="Ingrese su objetivo: "
if "%objective%"=="" (
    echo Objetivo vacio. Cancelando.
    goto end
)
echo.
echo Ejecutando: %objective%
python autonomous_cli.py execute --objective "%objective%" --select-directory --export-report
goto end

:test_system
echo.
echo ==========================================
echo TEST DE COMUNICACION
echo ==========================================
echo.
echo Verificando comunicacion entre agentes...
python simple_autonomous_test.py
echo.
echo Presione cualquier tecla para continuar...
pause >nul
goto end

:end
echo.
echo Sistema finalizado.
echo Presione cualquier tecla para salir...
pause >nul