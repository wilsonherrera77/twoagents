# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
Interfaz Web Mejorada para Sistema de Agentes Autonomos
Incluye selector de carpeta de destino para los desarrollos
"""

import os
import sys
if sys.platform == "win32":
    os.environ['PYTHONIOENCODING'] = 'utf-8'

import asyncio
import json
import threading
import sys
import os
import shutil
from datetime import datetime
from pathlib import Path
from flask import Flask, render_template, request, jsonify, send_file
from werkzeug.serving import make_server

from autonomous_team_system import AutonomousTeamSystem

app = Flask(__name__)

# Estado global
current_execution = None
execution_results = []
execution_lock = threading.Lock()


@app.route('/')
def index():
    """Pagina principal con selector de carpeta"""
    return '''
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sistema de Agentes Autonomos - Version Mejorada</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        h1 {
            color: #333;
            text-align: center;
            margin-bottom: 30px;
        }
        .form-group {
            margin-bottom: 20px;
        }
        label {
            display: block;
            margin-bottom: 5px;
            font-weight: bold;
            color: #555;
        }
        textarea, input[type="text"] {
            width: 100%;
            padding: 12px;
            border: 2px solid #ddd;
            border-radius: 5px;
            font-size: 16px;
            resize: vertical;
        }
        .directory-selector {
            display: flex;
            gap: 10px;
            align-items: end;
        }
        .directory-input {
            flex: 1;
        }
        button {
            background-color: #007bff;
            color: white;
            padding: 12px 30px;
            border: none;
            border-radius: 5px;
            font-size: 16px;
            cursor: pointer;
            margin-right: 10px;
        }
        button:hover {
            background-color: #0056b3;
        }
        button:disabled {
            background-color: #ccc;
            cursor: not-allowed;
        }
        .browse-btn {
            background-color: #28a745;
            padding: 12px 20px;
            white-space: nowrap;
        }
        .browse-btn:hover {
            background-color: #218838;
        }
        .status {
            margin-top: 20px;
            padding: 15px;
            border-radius: 5px;
            display: none;
        }
        .status.info {
            background-color: #d1ecf1;
            color: #0c5460;
            border: 1px solid #bee5eb;
        }
        .status.success {
            background-color: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
        }
        .status.error {
            background-color: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
        }
        .progress {
            width: 100%;
            height: 20px;
            background-color: #e9ecef;
            border-radius: 10px;
            overflow: hidden;
            margin: 10px 0;
        }
        .progress-bar {
            height: 100%;
            background-color: #007bff;
            transition: width 0.3s ease;
        }
        .examples {
            margin-top: 30px;
            padding: 20px;
            background-color: #f8f9fa;
            border-radius: 5px;
        }
        .example-btn {
            background-color: #6c757d;
            margin: 5px;
            padding: 8px 15px;
            font-size: 14px;
        }
        .example-btn:hover {
            background-color: #545b62;
        }
        .results {
            margin-top: 20px;
        }
        .result-item {
            background-color: #f8f9fa;
            padding: 15px;
            margin: 10px 0;
            border-radius: 5px;
            border-left: 4px solid #007bff;
        }
        .directory-info {
            background-color: #e7f3ff;
            padding: 10px;
            border-radius: 5px;
            margin-top: 10px;
            font-size: 14px;
        }
        .file-list {
            max-height: 200px;
            overflow-y: auto;
            background-color: #f8f9fa;
            padding: 10px;
            border-radius: 5px;
            margin-top: 10px;
        }
        .file-item {
            padding: 2px 0;
            font-family: monospace;
            font-size: 12px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>[U1F916] Sistema de Agentes Autonomos - Version Mejorada</h1>

        <div class="form-group">
            <label for="objective">Objetivo para los agentes:</label>
            <textarea id="objective" rows="4" placeholder="Describe que quieres que los agentes hagan de forma autonoma...

Ejemplos:
- Crear una calculadora web con HTML, CSS y JavaScript
- Implementar una API REST para gestion de usuarios
- Desarrollar un sistema de inventario basico
- Crear un script de backup automatizado"></textarea>
        </div>

        <div class="form-group">
            <label for="outputDirectory">[DIR] Carpeta donde guardar los desarrollos:</label>
            <div class="directory-selector">
                <div class="directory-input">
                    <input type="text" id="outputDirectory"
                           placeholder="Selecciona carpeta o usa: C:/MisProyectos/NuevoDesarrollo"
                           value="">
                </div>
                <button type="button" class="browse-btn" onclick="selectDirectory()">[U1F4C2] Explorar</button>
            </div>
            <div class="directory-info">
                [U1F4A1] <strong>Tip:</strong> Si no seleccionas carpeta, se usara: <code>./autonomous_workspace</code><br>
                Los agentes crearan automaticamente una subcarpeta con el nombre del proyecto.
            </div>
        </div>

        <button onclick="executeObjective()" id="executeBtn">[START] Ejecutar Objetivo</button>
        <button onclick="checkStatus()" id="statusBtn">[CHART] Ver Status</button>
        <button onclick="clearResults()" id="clearBtn">[U1F5D1][UFE0F] Limpiar Resultados</button>

        <div id="status" class="status"></div>

        <div id="progress-container" style="display: none;">
            <div class="progress">
                <div id="progress-bar" class="progress-bar" style="width: 0%"></div>
            </div>
            <div id="progress-text">Preparando ejecucion...</div>
        </div>

        <div class="examples">
            <h3>[TARGET] Ejemplos rapidos:</h3>
            <button class="example-btn" onclick="setExample('Crear una calculadora simple que pueda sumar, restar, multiplicar y dividir')">[U1F522] Calculadora</button>
            <button class="example-btn" onclick="setExample('Implementar un sistema de gestion de tareas con CRUD basico')">[CLIPBOARD] Sistema de Tareas</button>
            <button class="example-btn" onclick="setExample('Crear una API REST para manejo de usuarios con autenticacion')">[WEB] API REST</button>
            <button class="example-btn" onclick="setExample('Desarrollar un script de backup automatizado para archivos')">[SAVE] Script Backup</button>
            <button class="example-btn" onclick="setExample('Crear una aplicacion web de notas con persistencia')">[EDIT] App de Notas</button>
        </div>

        <div id="results" class="results"></div>
    </div>

    <script>
        let currentExecutionId = null;
        let statusInterval = null;

        // Configurar directorio por defecto
        function setDefaultDirectory() {
            const defaultDir = 'C:/MisDesarrollosAgentes';
            document.getElementById('outputDirectory').value = defaultDir;
        }

        function setExample(text) {
            document.getElementById('objective').value = text;
        }

        function selectDirectory() {
            // Para navegadores modernos, usar File System Access API si esta disponible
            if ('showDirectoryPicker' in window) {
                selectDirectoryModern();
            } else {
                // Fallback: permitir al usuario escribir la ruta manualmente
                const currentPath = document.getElementById('outputDirectory').value;
                const newPath = prompt('Ingresa la ruta completa de la carpeta donde guardar los desarrollos:',
                                     currentPath || 'C:/MisDesarrollosAgentes');
                if (newPath) {
                    document.getElementById('outputDirectory').value = newPath;
                    validateDirectory(newPath);
                }
            }
        }

        async function selectDirectoryModern() {
            try {
                const dirHandle = await window.showDirectoryPicker();
                // Note: For security reasons, we can't get the full path in browsers
                // but we can use the directory name and let the user confirm
                const dirName = dirHandle.name;
                document.getElementById('outputDirectory').value = `Carpeta seleccionada: ${dirName}`;
                showStatus(`Carpeta seleccionada: ${dirName}`, 'success');
            } catch (err) {
                if (err.name !== 'AbortError') {
                    showStatus('Error seleccionando carpeta. Puedes escribir la ruta manualmente.', 'error');
                }
            }
        }

        function validateDirectory(path) {
            if (path && path.trim()) {
                showStatus(`Carpeta configurada: ${path}`, 'info');
            }
        }

        function showStatus(message, type = 'info') {
            const statusDiv = document.getElementById('status');
            statusDiv.textContent = message;
            statusDiv.className = `status ${type}`;
            statusDiv.style.display = 'block';
        }

        function hideStatus() {
            document.getElementById('status').style.display = 'none';
        }

        function updateProgress(progress, text) {
            const container = document.getElementById('progress-container');
            const bar = document.getElementById('progress-bar');
            const textDiv = document.getElementById('progress-text');

            container.style.display = 'block';
            bar.style.width = progress + '%';
            textDiv.textContent = text || `Progreso: ${progress}%`;
        }

        function hideProgress() {
            document.getElementById('progress-container').style.display = 'none';
        }

        async function executeObjective() {
            const objective = document.getElementById('objective').value.trim();
            const outputDirectory = document.getElementById('outputDirectory').value.trim();

            if (!objective) {
                showStatus('Por favor, ingresa un objetivo', 'error');
                return;
            }

            const executeBtn = document.getElementById('executeBtn');
            executeBtn.disabled = true;
            executeBtn.textContent = '[U2699][UFE0F] Ejecutando...';

            try {
                showStatus('Iniciando ejecucion autonoma...', 'info');
                updateProgress(0, 'Preparando sistema de agentes...');

                const response = await fetch('/api/execute', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        objective: objective,
                        output_directory: outputDirectory || null
                    })
                });

                const data = await response.json();

                if (response.ok) {
                    currentExecutionId = data.execution_id;
                    const dirInfo = data.output_directory ? ` -> ${data.output_directory}` : '';
                    showStatus(`[START] Ejecucion iniciada: ${data.execution_id}${dirInfo}`, 'success');

                    // Iniciar monitoreo
                    startStatusMonitoring();
                } else {
                    showStatus(`[ERROR] Error: ${data.error}`, 'error');
                    executeBtn.disabled = false;
                    executeBtn.textContent = '[START] Ejecutar Objetivo';
                    hideProgress();
                }

            } catch (error) {
                showStatus(`[ERROR] Error de conexion: ${error.message}`, 'error');
                executeBtn.disabled = false;
                executeBtn.textContent = '[START] Ejecutar Objetivo';
                hideProgress();
            }
        }

        function startStatusMonitoring() {
            if (statusInterval) {
                clearInterval(statusInterval);
            }

            statusInterval = setInterval(async () => {
                if (currentExecutionId) {
                    await checkExecutionStatus();
                }
            }, 2000);
        }

        async function checkExecutionStatus() {
            try {
                const response = await fetch(`/api/status/${currentExecutionId}`);
                const data = await response.json();

                if (response.ok) {
                    updateProgress(data.progress, data.status_text || 'Ejecutando...');

                    if (data.completed) {
                        clearInterval(statusInterval);
                        statusInterval = null;
                        currentExecutionId = null;

                        const executeBtn = document.getElementById('executeBtn');
                        executeBtn.disabled = false;
                        executeBtn.textContent = '[START] Ejecutar Objetivo';

                        if (data.status === 'completed' && data.result) {
                            showStatus('[OK] [U00A1]Ejecucion completada exitosamente!', 'success');
                            displayResult(data.result);
                            hideProgress();
                        } else if (data.status === 'error') {
                            showStatus(`[ERROR] Error durante ejecucion: ${data.error || 'Error desconocido'}`, 'error');
                            hideProgress();
                        }
                    } else {
                        showStatus(`[U2699][UFE0F] Estado: ${data.status}`, 'info');
                    }
                }
            } catch (error) {
                console.error('Error checking status:', error);
            }
        }

        async function checkStatus() {
            try {
                const response = await fetch('/api/status');
                const data = await response.json();

                if (data.current_execution) {
                    const exec = data.current_execution;
                    showStatus(`[U2699][UFE0F] Ejecucion actual: ${exec.status} (${exec.progress}%)`, 'info');
                    updateProgress(exec.progress, exec.status);
                } else {
                    showStatus('[U2139][UFE0F] No hay ejecuciones en progreso', 'info');
                    hideProgress();
                }

                if (data.history && data.history.length > 0) {
                    displayHistory(data.history);
                }

            } catch (error) {
                showStatus(`[ERROR] Error obteniendo status: ${error.message}`, 'error');
            }
        }

        function displayResult(result) {
            const resultsDiv = document.getElementById('results');

            // Mostrar archivos creados si estan disponibles
            let filesHtml = '';
            if (result.deliverables && result.deliverables.length > 0) {
                filesHtml = '<div class="file-list"><strong>[FILES] Archivos creados:</strong><br>';
                result.deliverables.forEach(deliverable => {
                    if (deliverable.files_created) {
                        deliverable.files_created.forEach(file => {
                            filesHtml += `<div class="file-item">[U1F4C4] ${file}</div>`;
                        });
                    }
                });
                filesHtml += '</div>';
            }

            const resultHtml = `
                <div class="result-item">
                    <h3>[OK] Resultado de Ejecucion</h3>
                    <p><strong>[TARGET] Objetivo:</strong> ${result.objective || 'N/A'}</p>
                    <p><strong>[OK] Exito:</strong> ${result.execution_summary?.success ? 'SI' : 'NO'}</p>
                    <p><strong>[U23F1][UFE0F] Duracion:</strong> ${result.execution_summary?.total_duration || 'N/A'}</p>
                    <p><strong>[PACK] Entregables:</strong> ${result.deliverables?.length || 0}</p>
                    <p><strong>[TALK] Mensajes intercambiados:</strong> ${result.communication_analysis?.total_messages || 0}</p>
                    <p><strong>[DIR] Ubicacion:</strong> ${result.final_output_directory || 'Workspace por defecto'}</p>

                    ${filesHtml}

                    <button onclick="downloadResult('${JSON.stringify(result).replace(/'/g, "\\'")}')">[U1F4E5] Descargar Reporte Completo</button>
                    <button onclick="openDirectory('${result.final_output_directory || ''}')">[U1F4C2] Abrir Carpeta</button>
                </div>
            `;

            resultsDiv.innerHTML = resultHtml + resultsDiv.innerHTML;
        }

        function openDirectory(path) {
            if (path) {
                showStatus(`[U1F4C2] Para abrir la carpeta, ve a: ${path}`, 'info');
                // En un entorno de escritorio real, esto podria abrir el explorador de archivos
                navigator.clipboard.writeText(path).then(() => {
                    showStatus(`[CLIPBOARD] Ruta copiada al portapapeles: ${path}`, 'success');
                });
            } else {
                showStatus('[ERROR] No se encontro la ruta de la carpeta', 'error');
            }
        }

        function displayHistory(history) {
            const resultsDiv = document.getElementById('results');

            let historyHtml = '<div class="result-item"><h3>[U1F4DA] Historial Reciente</h3>';

            history.slice(-3).reverse().forEach(exec => {
                const success = exec.result?.execution_summary?.success;
                historyHtml += `
                    <p>
                        <strong>${exec.objective.substring(0, 50)}...</strong> -
                        ${success ? '[OK] EXITO' : '[ERROR] ERROR'}
                        (${exec.result?.execution_summary?.total_duration || 'N/A'})
                    </p>
                `;
            });

            historyHtml += '</div>';
            resultsDiv.innerHTML = historyHtml;
        }

        function downloadResult(resultJson) {
            const result = JSON.parse(resultJson);
            const blob = new Blob([JSON.stringify(result, null, 2)], { type: 'application/json' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `autonomous_result_${new Date().toISOString().slice(0, 19).replace(/:/g, '-')}.json`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
        }

        function clearResults() {
            document.getElementById('results').innerHTML = '';
            hideStatus();
            hideProgress();
        }

        // Configurar directorio por defecto al cargar
        window.onload = function() {
            setDefaultDirectory();
            checkStatus();
        };
    </script>
</body>
</html>
    '''


@app.route('/api/execute', methods=['POST'])
def execute_objective():
    """Ejecutar objetivo con directorio personalizado"""
    global current_execution

    data = request.get_json()
    objective = data.get('objective', '').strip()
    output_directory = data.get('output_directory', '').strip()

    if not objective:
        return jsonify({'error': 'Objetivo requerido'}), 400

    with execution_lock:
        if current_execution and not current_execution['completed']:
            return jsonify({'error': 'Ya hay una ejecucion en progreso'}), 409

        # Configurar directorio de salida
        if output_directory and output_directory != '':
            # Limpiar y validar el directorio
            output_directory = output_directory.replace('Carpeta seleccionada: ', '')
            if not os.path.isabs(output_directory):
                # Si no es ruta absoluta, hacerla relativa al directorio actual
                output_directory = os.path.abspath(output_directory)
        else:
            output_directory = './autonomous_workspace'

        # Crear directorio si no existe
        try:
            os.makedirs(output_directory, exist_ok=True)
        except Exception as e:
            return jsonify({'error': f'No se puede crear el directorio: {str(e)}'}), 400

        # Iniciar nueva ejecucion
        execution_id = f"exec_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        current_execution = {
            'id': execution_id,
            'objective': objective,
            'output_directory': output_directory,
            'status': 'starting',
            'progress': 0,
            'messages': [],
            'completed': False,
            'result': None,
            'start_time': datetime.now().isoformat()
        }

    # Ejecutar en thread separado
    thread = threading.Thread(
        target=run_execution_async,
        args=(execution_id, objective, output_directory),
        daemon=True
    )
    thread.start()

    return jsonify({
        'execution_id': execution_id,
        'status': 'started',
        'message': 'Ejecucion iniciada',
        'output_directory': output_directory
    })


def run_execution_async(execution_id: str, objective: str, output_directory: str):
    """Ejecutar el objetivo en thread async con directorio personalizado"""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        result = loop.run_until_complete(
            execute_objective_internal(execution_id, objective, output_directory)
        )

        with execution_lock:
            if current_execution and current_execution['id'] == execution_id:
                current_execution['result'] = result
                current_execution['completed'] = True
                current_execution['status'] = 'completed'
                current_execution['progress'] = 100
                current_execution['end_time'] = datetime.now().isoformat()

                execution_results.append(current_execution.copy())

    except Exception as e:
        print(f"ERROR en ejecucion {execution_id}: {e}")
        with execution_lock:
            if current_execution and current_execution['id'] == execution_id:
                current_execution['status'] = 'error'
                current_execution['error'] = str(e)
                current_execution['completed'] = True
                current_execution['progress'] = 100


async def execute_objective_internal(execution_id: str, objective: str, output_directory: str):
    """Ejecutar objetivo con directorio personalizado"""

    def update_progress(progress: int, status_text: str):
        with execution_lock:
            if current_execution and current_execution['id'] == execution_id:
                current_execution['progress'] = progress
                current_execution['status'] = status_text

    try:
        update_progress(10, "Configurando directorio de salida...")

        # Crear un nombre de proyecto basado en el objetivo
        project_name = objective.lower()
        # Limpiar caracteres no validos para nombres de carpeta
        for char in ['<', '>', ':', '"', '|', '?', '*', '/', '\\']:
            project_name = project_name.replace(char, '_')
        project_name = project_name.replace(' ', '_')[:50]  # Limitar longitud

        # Crear carpeta especifica para este proyecto
        final_output_dir = Path(output_directory) / f"{project_name}_{execution_id[-8:]}"
        final_output_dir.mkdir(parents=True, exist_ok=True)

        update_progress(20, "Inicializando sistema de agentes...")

        # Usar el directorio personalizado como workspace
        async with AutonomousTeamSystem(str(final_output_dir)) as team_system:
            update_progress(30, "Agentes inicializados, negociando roles...")

            result = await team_system.execute_objective_autonomously(
                objective=objective,
                monitoring_interval=5,
                show_communication=False
            )

            update_progress(80, "Consolidando archivos en directorio final...")

            # Copiar archivos del dev_workspace al directorio final si es necesario
            dev_workspace = final_output_dir / "dev_workspace"
            if dev_workspace.exists():
                # Copiar archivos del dev_workspace al directorio principal
                for item in dev_workspace.iterdir():
                    if item.is_file():
                        shutil.copy2(item, final_output_dir)
                    elif item.is_dir():
                        shutil.copytree(item, final_output_dir / item.name, dirs_exist_ok=True)

            update_progress(90, "Actualizando informacion de resultados...")

            # Actualizar informacion en el resultado
            result['execution_id'] = execution_id
            result['final_output_directory'] = str(final_output_dir.absolute())
            result['project_name'] = project_name

            # Listar archivos creados en el directorio final
            created_files = []
            for item in final_output_dir.rglob('*'):
                if item.is_file() and not item.name.startswith('.'):
                    rel_path = item.relative_to(final_output_dir)
                    created_files.append(str(rel_path))

            # Actualizar entregables con la informacion de archivos
            if result.get('deliverables'):
                for deliverable in result['deliverables']:
                    if 'files_created' in deliverable:
                        # Actualizar rutas a las rutas finales
                        updated_files = []
                        for file_path in deliverable['files_created']:
                            file_name = Path(file_path).name
                            # Buscar el archivo en el directorio final
                            for created_file in created_files:
                                if Path(created_file).name == file_name:
                                    updated_files.append(str(final_output_dir / created_file))
                                    break
                            else:
                                updated_files.append(str(final_output_dir / file_name))
                        deliverable['files_created'] = updated_files

            # Agregar resumen de archivos creados
            result['files_summary'] = {
                'total_files': len(created_files),
                'file_list': created_files[:20],  # Primeros 20 archivos
                'output_directory': str(final_output_dir.absolute())
            }

            update_progress(100, "Completado exitosamente")

            return result

    except Exception as e:
        update_progress(100, f"Error: {str(e)}")
        raise


@app.route('/api/status')
@app.route('/api/status/<execution_id>')
def get_status(execution_id=None):
    """Obtener status de ejecucion"""
    with execution_lock:
        if execution_id:
            if current_execution and current_execution['id'] == execution_id:
                return jsonify(current_execution)
            else:
                for result in execution_results:
                    if result['id'] == execution_id:
                        return jsonify(result)
                return jsonify({'error': 'Ejecucion no encontrada'}), 404
        else:
            return jsonify({
                'current_execution': current_execution,
                'history': execution_results[-10:],
                'total_executions': len(execution_results)
            })


@app.route('/api/download/<execution_id>')
def download_result(execution_id):
    """Descargar resultado como JSON"""
    result_data = None

    with execution_lock:
        if current_execution and current_execution['id'] == execution_id:
            result_data = current_execution.get('result')
        else:
            for result in execution_results:
                if result['id'] == execution_id:
                    result_data = result.get('result')
                    break

    if not result_data:
        return jsonify({'error': 'Resultado no encontrado'}), 404

    temp_file = Path(f"./temp_result_{execution_id}.json")
    with open(temp_file, 'w', encoding='utf-8') as f:
        json.dump(result_data, f, indent=2, ensure_ascii=False, default=str)

    return send_file(
        temp_file,
        as_attachment=True,
        download_name=f"autonomous_result_{execution_id}.json",
        mimetype='application/json'
    )


def main():
    """Funcion principal mejorada"""
    print("=== SISTEMA DE AGENTES AUTONOMOS - VERSION MEJORADA ===")
    print("="*65)
    print("[NEW] Nuevas caracteristicas:")
    print("  - Selector de carpeta de destino para desarrollos")
    print("  - Explorador de archivos integrado")
    print("  - Copia automatica de archivos al directorio elegido")
    print("  - Organizacion automatica por proyecto")
    print()
    print("[WEB] Iniciando servidor web...")
    print()
    print("Una vez iniciado, abre tu navegador en:")
    print("  -> http://localhost:5000")
    print()
    print("Para acceso desde otros dispositivos en tu red:")
    print("  -> http://[tu-ip-local]:5000")
    print()
    print("[DIR] Los desarrollos se guardaran donde tu elijas")
    print("Presiona Ctrl+C para detener el servidor")
    print("="*65)

    try:
        app.run(
            host='0.0.0.0',
            port=5000,
            debug=False,
            threaded=True
        )
    except KeyboardInterrupt:
        print("\nServidor detenido por usuario")
    except Exception as e:
        print(f"Error iniciando servidor: {e}")


if __name__ == '__main__':
    main()