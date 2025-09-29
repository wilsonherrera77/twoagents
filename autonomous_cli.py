# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
CLI Mejorado para Sistema de Agentes Autonomos
Incluye selector de carpeta de destino para los desarrollos
"""

import os
import sys
if sys.platform == "win32":
    os.environ['PYTHONIOENCODING'] = 'utf-8'

import asyncio
import click
import json
import os
import shutil
from pathlib import Path
from datetime import datetime
import tkinter as tk
from tkinter import filedialog

from autonomous_team_system import AutonomousTeamSystem


def select_directory_gui(title="Seleccionar carpeta para guardar desarrollos"):
    """Abrir dialogo de seleccion de carpeta usando tkinter"""
    try:
        # Crear ventana root oculta
        root = tk.Tk()
        root.withdraw()  # Ocultar ventana principal
        root.attributes('-topmost', True)  # Mantener al frente

        # Abrir dialogo de seleccion de carpeta
        directory = filedialog.askdirectory(
            title=title,
            initialdir=os.path.expanduser("~"),  # Empezar en directorio home
        )

        root.destroy()  # Limpiar
        return directory if directory else None

    except Exception as e:
        print(f"Error abriendo selector de carpeta: {e}")
        return None


def prompt_for_directory():
    """Solicitar directorio al usuario con multiples opciones"""
    print("\n" + "="*60)
    print("[DIR] SELECCION DE CARPETA PARA DESARROLLOS")
    print("="*60)
    print()
    print("Opciones disponibles:")
    print("1. [FOLDER] Abrir explorador de archivos (recomendado)")
    print("2. [EDIT]  Escribir ruta manualmente")
    print("3. [COPY] Usar carpeta por defecto (./autonomous_workspace)")
    print()

    while True:
        choice = input("Selecciona opcion (1-3): ").strip()

        if choice == "1":
            print("\n[SEARCH] Abriendo explorador de archivos...")
            directory = select_directory_gui()
            if directory:
                print(f"[OK] Carpeta seleccionada: {directory}")
                return directory
            else:
                print("[ERROR] No se selecciono carpeta. Intentando otra opcion...")
                continue

        elif choice == "2":
            directory = input("\n[WRITE] Ingresa la ruta completa de la carpeta: ").strip()
            if directory:
                try:
                    # Validar que se pueda crear el directorio
                    Path(directory).mkdir(parents=True, exist_ok=True)
                    print(f"[OK] Carpeta configurada: {directory}")
                    return directory
                except Exception as e:
                    print(f"[ERROR] Error con la carpeta: {e}")
                    continue
            else:
                print("[ERROR] Ruta vacia. Intenta de nuevo.")
                continue

        elif choice == "3":
            default_dir = "./autonomous_workspace"
            print(f"[DIR] Usando carpeta por defecto: {os.path.abspath(default_dir)}")
            return default_dir

        else:
            print("[ERROR] Opcion invalida. Selecciona 1, 2 o 3.")


async def execute_with_custom_directory(objective, pm_agent, dev_agent,
                                      monitor_interval, export_report,
                                      show_communication, output_directory):
    """Ejecutar objetivo con directorio personalizado"""

    try:
        print("\n" + "="*60)
        print("[START] INICIANDO EJECUCION AUTONOMA")
        print("="*60)
        print(f"[TARGET] Objetivo: {objective}")
        print(f"[DIR] Directorio de salida: {output_directory}")
        print(f"[TIME]  Monitoreo cada: {monitor_interval}s")
        print()

        # Crear nombre de proyecto basado en el objetivo
        project_name = objective.lower()
        for char in ['<', '>', ':', '"', '|', '?', '*', '/', '\\']:
            project_name = project_name.replace(char, '_')
        project_name = project_name.replace(' ', '_')[:50]

        # Crear carpeta especifica para este proyecto
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        final_output_dir = Path(output_directory) / f"{project_name}_{timestamp}"
        final_output_dir.mkdir(parents=True, exist_ok=True)

        print(f"[FOLDER] Carpeta del proyecto: {final_output_dir.absolute()}")
        print()

        # Crear sistema de equipo autonomo usando el directorio personalizado
        async with AutonomousTeamSystem(str(final_output_dir)) as team_system:

            # Configurar nombres de agentes si se especifican
            agent_names = None
            user_roles = None

            if pm_agent or dev_agent:
                agent_names = [pm_agent or "PM_Agent", dev_agent or "Dev_Agent"]

                if pm_agent and dev_agent:
                    user_roles = {
                        pm_agent: "project_manager",
                        dev_agent: "developer"
                    }

            # Ejecutar objetivo autonomamente
            result = await team_system.execute_objective_autonomously(
                objective=objective,
                agent_names=agent_names,
                user_specified_roles=user_roles,
                monitoring_interval=monitor_interval,
                show_communication=show_communication
            )

            # Consolidar archivos en el directorio final
            print("\n[PACK] Consolidando archivos en directorio de destino...")

            dev_workspace = final_output_dir / "dev_workspace"
            if dev_workspace.exists():
                # Copiar archivos del dev_workspace al directorio principal
                for item in dev_workspace.iterdir():
                    if item.is_file():
                        shutil.copy2(item, final_output_dir)
                        print(f"  [FILE] Copiado: {item.name}")
                    elif item.is_dir() and item.name != "__pycache__":
                        dest_dir = final_output_dir / item.name
                        if dest_dir.exists():
                            shutil.rmtree(dest_dir)
                        shutil.copytree(item, dest_dir)
                        print(f"  [DIR] Copiado: {item.name}/")

            # Actualizar informacion del resultado
            result['final_output_directory'] = str(final_output_dir.absolute())
            result['project_name'] = project_name

            # Mostrar resultados
            print_execution_results(result, final_output_dir)

            # Exportar reporte si se solicita
            if export_report:
                report_path = final_output_dir / f"autonomous_report_{timestamp}.json"
                with open(report_path, 'w', encoding='utf-8') as f:
                    json.dump(result, f, indent=2, ensure_ascii=False, default=str)
                print(f"\n[REPORT] Reporte exportado: {report_path}")

            return result

    except Exception as e:
        print(f"\n[ERROR] ERROR durante ejecucion: {e}")
        sys.exit(1)


def print_execution_results(result, output_directory):
    """Mostrar resultados de ejecucion con informacion de archivos"""

    print("\n" + "="*60)
    print("[REPORT] RESULTADOS DE EJECUCION AUTONOMA")
    print("="*60)

    # Informacion basica
    execution_summary = result.get("execution_summary", {})
    success = execution_summary.get("success", False)
    duration = execution_summary.get("total_duration", "N/A")

    print(f"[OK] Exito: {'SI' if success else 'NO'}")
    print(f"[TIME]  Duracion: {duration}")
    print(f"[TARGET] Objetivo: {result.get('objective', 'N/A')}")
    print(f"[DIR] Ubicacion: {output_directory.absolute()}")

    # Performance del equipo
    team_performance = result.get("team_performance", {})
    role_assignments = team_performance.get("role_assignments", {})

    print(f"\n[TEAM] ASIGNACIONES DE ROLES")
    for agent, assignment in role_assignments.items():
        role = assignment.get("role", "unknown")
        confidence = assignment.get("confidence", 0)
        print(f"  [BOT] {agent}: {role} (confianza: {confidence:.2f})")

    # Entregables y archivos creados
    deliverables = result.get("deliverables", [])
    print(f"\n[PACK] ENTREGABLES GENERADOS ({len(deliverables)}):")

    # Listar archivos realmente creados en el directorio
    created_files = []
    for item in output_directory.rglob('*'):
        if item.is_file() and not item.name.startswith('.') and item.suffix not in ['.pyc']:
            rel_path = item.relative_to(output_directory)
            created_files.append(rel_path)

    if created_files:
        print(f"\n[FILE] ARCHIVOS CREADOS ({len(created_files)}):")
        for file in sorted(created_files):
            file_size = (output_directory / file).stat().st_size
            print(f"  [FILE] {file} ({file_size} bytes)")
    else:
        print("\n[WARN]  No se encontraron archivos en el directorio final")

    # Analisis de comunicacion
    comm_analysis = result.get("communication_analysis", {})
    total_messages = comm_analysis.get("total_messages", 0)
    effectiveness = comm_analysis.get("communication_effectiveness", "N/A")

    print(f"\n[TALK] COMUNICACION ENTRE AGENTES")
    print(f"  [MSG] Mensajes totales: {total_messages}")
    print(f"  [CHART] Efectividad: {effectiveness}")

    if comm_analysis.get("message_breakdown"):
        print("  [REPORT] Desglose de mensajes:")
        for msg_type, count in comm_analysis["message_breakdown"].items():
            print(f"    - {msg_type}: {count}")

    print(f"\n[DONE] [U00A1]Desarrollo completado!")
    print(f"[FOLDER] Abre la carpeta: {output_directory.absolute()}")


@click.group()
def cli():
    """Sistema de Equipo Autonomo Mejorado - Con selector de carpeta de destino"""
    pass


@cli.command()
@click.option('--objective', required=True, help='Objetivo que deben lograr los agentes autonomamente')
@click.option('--pm-agent', help='Nombre del agente que actuara como Project Manager')
@click.option('--dev-agent', help='Nombre del agente que actuara como Developer')
@click.option('--output-dir', help='Directorio donde guardar los desarrollos')
@click.option('--monitor-interval', default=10, help='Intervalo de monitoreo en segundos')
@click.option('--export-report', is_flag=True, help='Exportar reporte detallado al finalizar')
@click.option('--show-communication', is_flag=True, help='Mostrar comunicacion entre agentes en tiempo real')
@click.option('--select-directory', is_flag=True, help='Abrir selector de carpeta grafico')
def execute(objective, pm_agent, dev_agent, output_dir, monitor_interval,
           export_report, show_communication, select_directory):
    """
    Ejecutar objetivo de forma completamente autonoma con carpeta personalizada

    Los agentes negociaran roles, planificaran, implementaran y guardaran
    resultados en la carpeta que elijas.

    Ejemplos:
      autonomous_cli_enhanced.py execute --objective "Crear calculadora" --select-directory
      autonomous_cli_enhanced.py execute --objective "API REST" --output-dir "C:/MisProyectos"
    """

    # Determinar directorio de salida
    if select_directory or not output_dir:
        output_dir = prompt_for_directory()

    if not output_dir:
        output_dir = "./autonomous_workspace"

    # Validar que el directorio se pueda crear
    try:
        Path(output_dir).mkdir(parents=True, exist_ok=True)
    except Exception as e:
        print(f"[ERROR] Error creando directorio {output_dir}: {e}")
        sys.exit(1)

    # Ejecutar con directorio personalizado
    asyncio.run(execute_with_custom_directory(
        objective, pm_agent, dev_agent, monitor_interval,
        export_report, show_communication, output_dir
    ))


@cli.command()
@click.option('--workspace', default='./autonomous_workspace', help='Directorio de workspace a examinar')
def status(workspace):
    """Ver status del sistema y reportes anteriores"""

    workspace_path = Path(workspace)

    if not workspace_path.exists():
        print(f"[ERROR] Workspace no encontrado: {workspace}")
        return

    print(f"[DIR] Workspace: {workspace_path.absolute()}")
    print("="*60)

    # Buscar reportes
    reports = list(workspace_path.glob("**/autonomous_report_*.json"))
    print(f"[REPORT] Reportes encontrados: {len(reports)}")

    for report in reports[-5:]:  # Ultimos 5 reportes
        print(f"  [FILE] {report.name} - {report.parent.name}")

    # Buscar directorios de proyectos
    project_dirs = [d for d in workspace_path.iterdir() if d.is_dir() and '_exec_' in d.name]
    print(f"\n[FOLDER] Proyectos encontrados: {len(project_dirs)}")

    for project_dir in project_dirs[-5:]:  # Ultimos 5 proyectos
        files_count = len([f for f in project_dir.rglob('*') if f.is_file()])
        print(f"  [DIR] {project_dir.name} - {files_count} archivos")


@cli.command()
@click.option('--report-file', required=True, help='Archivo de reporte a analizar')
def analyze(report_file):
    """Analizar reporte especifico de ejecucion"""

    report_path = Path(report_file)

    if not report_path.exists():
        print(f"[ERROR] Reporte no encontrado: {report_file}")
        return

    try:
        with open(report_path, 'r', encoding='utf-8') as f:
            result = json.load(f)

        print(f"[REPORT] ANALISIS DE REPORTE: {report_path.name}")
        print("="*60)

        objective = result.get('objective', 'N/A')
        execution_summary = result.get('execution_summary', {})
        success = execution_summary.get('success', False)
        duration = execution_summary.get('total_duration', 'N/A')

        print(f"[TARGET] Objetivo: {objective}")
        print(f"[OK] Exito: {'SI' if success else 'NO'}")
        print(f"[TIME]  Duracion: {duration}")

        if execution_summary.get('start_time'):
            print(f"[TIME] Inicio: {execution_summary['start_time']}")
        if execution_summary.get('end_time'):
            print(f"[TIME] Fin: {execution_summary['end_time']}")

        # Mostrar ubicacion de archivos si esta disponible
        if result.get('final_output_directory'):
            output_dir = Path(result['final_output_directory'])
            if output_dir.exists():
                files_count = len([f for f in output_dir.rglob('*') if f.is_file()])
                print(f"[DIR] Ubicacion: {output_dir}")
                print(f"[FILE] Archivos: {files_count}")

        print_execution_results(result, report_path.parent)

    except Exception as e:
        print(f"[ERROR] Error analizando reporte: {e}")


@cli.command()
def demo():
    """Ejecutar demostracion del sistema autonomo con selector de carpeta"""

    print("[DEMO] DEMOSTRACION DEL SISTEMA AUTONOMO MEJORADO")
    print("="*60)
    print("[NEW] Esta version permite elegir donde guardar los desarrollos")
    print()
    print("Seleccione un objetivo de demostracion:")
    print()

    demo_objectives = [
        "Crear una calculadora simple con operaciones basicas",
        "Implementar un sistema de gestion de tareas",
        "Desarrollar una API REST para usuarios",
        "Crear un script de backup automatizado",
        "Implementar sistema de autenticacion basico"
    ]

    for i, objective in enumerate(demo_objectives, 1):
        print(f"  {i}. {objective}")

    print(f"  {len(demo_objectives) + 1}. Objetivo personalizado")
    print()

    try:
        choice = input("Seleccione opcion (1-6): ").strip()

        if choice.isdigit() and 1 <= int(choice) <= len(demo_objectives):
            selected_objective = demo_objectives[int(choice) - 1]
        elif choice == str(len(demo_objectives) + 1):
            selected_objective = input("Ingrese su objetivo personalizado: ").strip()
        else:
            print("[ERROR] Seleccion invalida")
            return

        if selected_objective:
            print(f"\n[TARGET] Ejecutando: {selected_objective}")
            print("-" * 50)

            # Solicitar directorio para demo
            output_dir = prompt_for_directory()

            # Ejecutar con configuracion de demo
            asyncio.run(execute_with_custom_directory(
                objective=selected_objective,
                pm_agent=None,
                dev_agent=None,
                monitor_interval=5,
                export_report=True,
                show_communication=True,
                output_directory=output_dir
            ))

    except KeyboardInterrupt:
        print("\n[STOP] Demo cancelado por usuario")


@cli.command()
@click.option('--workspace', default='./autonomous_workspace', help='Directorio de workspace a limpiar')
@click.option('--confirm', is_flag=True, help='Confirmar limpieza sin pregunta')
def cleanup(workspace, confirm):
    """Limpiar workspace de ejecuciones anteriores"""

    workspace_path = Path(workspace)

    if not workspace_path.exists():
        print(f"[ERROR] Workspace no encontrado: {workspace}")
        return

    if not confirm:
        response = input(f"[U00BF]Limpiar workspace '{workspace}'? (s/N): ").strip().lower()
        confirm = response in ['s', 'si', 'y', 'yes']

    if confirm:
        if len(list(workspace_path.iterdir())) == 0:
            print(f"[OK] Workspace ya esta limpio: {workspace}")
        else:
            try:
                shutil.rmtree(workspace_path)
                workspace_path.mkdir(exist_ok=True)
                print(f"[OK] Workspace limpiado: {workspace}")
            except Exception as e:
                print(f"[ERROR] Error limpiando workspace: {e}")
    else:
        print("[ERROR] Limpieza cancelada")


if __name__ == '__main__':
    cli()