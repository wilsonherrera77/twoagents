#!/usr/bin/env python3
"""
Test Simple del Sistema de Equipo Autónomo
Prueba básica sin emojis para Windows
"""

import asyncio
import sys
from pathlib import Path

# Añadir paths para imports
sys.path.append(str(Path(__file__).parent))

from autonomous_team_system import AutonomousTeamSystem


async def test_basic_autonomous_collaboration():
    """Test básico de colaboración autónoma"""

    print("=== TEST: COLABORACION AUTONOMA BASICA ===")
    print("Objetivo: Crear un sistema simple de calculadora")

    try:
        async with AutonomousTeamSystem("./test_workspace") as team_system:

            # Test con objetivo simple
            objective = "Crear una calculadora simple que sume, reste, multiplique y divida"

            print(f"\nObjetivo: {objective}")
            print("Ejecutando colaboracion autonoma...")

            result = await team_system.execute_objective_autonomously(
                objective=objective,
                monitoring_interval=5  # Monitoreo más frecuente para test
            )

            # Verificar resultados
            success = result.get("execution_summary", {}).get("success", False)
            deliverables = result.get("deliverables", [])
            communication = result.get("communication_analysis", {})

            print(f"\nRESULTADOS DEL TEST:")
            print(f"   Exito: {'SI' if success else 'NO'}")
            print(f"   Entregables: {len(deliverables)}")
            print(f"   Mensajes: {communication.get('total_messages', 0)}")

            # Verificar que se generaron entregables
            if len(deliverables) > 0:
                print("   OK Entregables generados correctamente")
            else:
                print("   ERROR No se generaron entregables")

            # Verificar comunicación
            if communication.get("total_messages", 0) > 5:
                print("   OK Comunicacion efectiva entre agentes")
            else:
                print("   ERROR Comunicacion insuficiente")

            return success

    except Exception as e:
        print(f"ERROR en test: {e}")
        return False


async def test_communication_flow():
    """Test del flujo de comunicación entre agentes"""

    print("\n=== TEST: FLUJO DE COMUNICACION ===")

    try:
        # Test más simple para verificar solo comunicación
        from agent_communication import MessageBroker
        from project_manager_agent import ProjectManagerAgent
        from developer_agent import DeveloperAgent

        broker = MessageBroker()
        pm = ProjectManagerAgent("PM_Test", broker)
        dev = DeveloperAgent("Dev_Test", broker, "./test_comm_workspace")

        # Iniciar broker
        broker_task = asyncio.create_task(broker.start_routing())
        await asyncio.sleep(0.5)

        try:
            # Simular inicio de proyecto
            objective = "Crear calculadora simple"
            team_members = [dev.name]

            print(f"PM iniciando proyecto: {objective}")
            project_plan = await pm.start_project(objective, team_members)

            # Esperar un poco para que se procesen los mensajes
            await asyncio.sleep(2)

            # Verificar comunicación
            messages = broker.get_conversation_history()
            print(f"\nMensajes intercambiados: {len(messages)}")

            # Verificar tipos de mensajes
            message_types = {}
            for msg in messages:
                msg_type = msg.message_type.value
                message_types[msg_type] = message_types.get(msg_type, 0) + 1

            print("Tipos de mensajes:")
            for msg_type, count in message_types.items():
                print(f"   {msg_type}: {count}")

            # Verificar que hay comunicación bidireccional
            senders = set(msg.sender for msg in messages)
            receivers = set(msg.receiver for msg in messages)

            bidirectional = len(senders) > 1 and len(receivers) > 1
            print(f"\nComunicacion bidireccional: {'SI' if bidirectional else 'NO'}")

            return len(messages) > 0 and bidirectional

        finally:
            broker.stop_routing()
            await asyncio.sleep(0.5)
            if not broker_task.done():
                broker_task.cancel()

    except Exception as e:
        print(f"ERROR en test de comunicacion: {e}")
        return False


async def run_simple_tests():
    """Ejecutar tests simples del sistema"""

    print("SUITE DE TESTS - SISTEMA DE EQUIPO AUTONOMO")
    print("="*60)

    tests = [
        ("Colaboracion autonoma basica", test_basic_autonomous_collaboration),
        ("Flujo de comunicacion", test_communication_flow)
    ]

    results = []

    for test_name, test_func in tests:
        print(f"\nEjecutando: {test_name}")
        print("-" * 40)

        try:
            success = await test_func()
            results.append((test_name, success))
            status = "EXITOSO" if success else "FALLIDO"
            print(f"Resultado: {status}")

        except Exception as e:
            print(f"ERROR: {e}")
            results.append((test_name, False))

        # Pequeña pausa entre tests
        await asyncio.sleep(1)

    # Resumen final
    print("\n" + "="*60)
    print("RESUMEN DE TESTS")
    print("="*60)

    successful_tests = sum(1 for _, success in results if success)
    total_tests = len(results)

    print(f"Tests ejecutados: {total_tests}")
    print(f"Tests exitosos: {successful_tests}")
    print(f"Tests fallidos: {total_tests - successful_tests}")
    print(f"Tasa de exito: {successful_tests / total_tests * 100:.1f}%")

    print("\nDetalle por test:")
    for test_name, success in results:
        status = "OK" if success else "ERROR"
        print(f"   {status} {test_name}")

    if successful_tests == total_tests:
        print(f"\nTODOS LOS TESTS EXITOSOS!")
        print("El sistema de equipo autonomo esta funcionando correctamente.")
    else:
        print(f"\n{total_tests - successful_tests} tests fallaron.")
        print("Revisar la implementacion del sistema.")

    return successful_tests == total_tests


async def main():
    """Main de testing"""

    print("TESTING DEL SISTEMA DE EQUIPO AUTONOMO")
    print("Este sistema permite que los agentes trabajen juntos de forma completamente autonoma")
    print()

    success = await run_simple_tests()
    return success


if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\nTests interrumpidos por usuario")
        exit(130)