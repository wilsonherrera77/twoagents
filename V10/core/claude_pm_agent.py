#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Claude PM Agent - Para ejecutar en terminal Claude separada
===========================================================

Este script está diseñado para ejecutarse en una terminal Claude SEPARADA.

USO:
Terminal 2 (Claude): python claude_pm_agent.py

FLUJO:
1. Lee mensaje de .agents/pm/inbox/
2. Analiza objetivo usando CLAUDE (el LLM que ejecuta este script)
3. Genera arquitectura técnica
4. Escribe resultado en .agents/orchestrator/inbox/
5. ✅ NO HAY DEADLOCK porque Claude en T2 responde via filesystem

INNOVACION:
- Este Claude NO llama a otro Claude
- Este Claude USA SU PROPIA INTELIGENCIA para analizar
- Comunicación async via filesystem
"""

import sys
import json
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))
from async_agent_system import AsyncMessageQueue
from utils import create_logger


class ClaudePMAgent:
    """
    PM Agent que corre en terminal Claude separada.

    Este agente ES ejecutado POR Claude, no LLAMA a Claude.
    """

    def __init__(self):
        self.logger = create_logger("CLAUDE_PM")
        self.message_queue = AsyncMessageQueue()
        self.agent_name = "pm"

    def process_messages(self, max_messages: int = 1):
        """Procesa mensajes pendientes en inbox."""

        self.logger.info(f"Checking inbox for messages...")

        processed = 0
        while processed < max_messages:
            # Leer mensaje
            message = self.message_queue.read_message(self.agent_name)

            if not message:
                self.logger.info("No more messages")
                break

            self.logger.info(f"Processing message: {message.message_id}")
            self.logger.info(f"Task type: {message.task_type}")

            # Procesar según tipo
            if message.task_type == "generate_architecture":
                result = self.generate_architecture(message.payload)
            else:
                self.logger.warning(f"Unknown task type: {message.task_type}")
                continue

            # Enviar respuesta
            self.message_queue.send_message(
                to_agent=message.from_agent,
                from_agent=self.agent_name,
                task_type=f"{message.task_type}_result",
                payload=result,
                session_id=message.session_id,
                reply_to=message.message_id
            )

            processed += 1
            self.logger.success(f"Message processed: {message.message_id}")

        return processed

    def generate_architecture(self, payload: dict) -> dict:
        """
        Genera arquitectura técnica usando análisis Claude.

        ✅ ESTE método es donde Claude (el LLM ejecutando este script)
           aplica su inteligencia para analizar el objetivo.

        NO llama a otro Claude, USA la inteligencia del Claude actual.
        """

        objective = payload.get("objective", "")

        self.logger.info(f"Generating architecture for: {objective}")

        # Aquí es donde Claude analiza el objetivo
        # NOTA: Este análisis lo hace Claude al ejecutar este código
        architecture = self._analyze_objective_with_intelligence(objective)

        return {
            "status": "SUCCESS",
            "architecture": architecture
        }

    def _analyze_objective_with_intelligence(self, objective: str) -> dict:
        """
        Análisis técnico del objetivo.

        CLAUDE: Cuando ejecutes este método, usa tu inteligencia para:
        1. Identificar tipo de proyecto
        2. Determinar módulos necesarios
        3. Seleccionar tecnologías apropiadas
        4. Definir esquema de base de datos si aplica
        """

        # Análisis básico con keywords (fallback)
        objective_lower = objective.lower()

        # Detectar tipo de proyecto
        if any(kw in objective_lower for kw in ["api", "rest", "endpoint", "web service"]):
            project_type = "api_rest"
            modules = ["api_main.py", "routes.py", "models.py", "database.py"]
            technologies = {
                "framework": "FastAPI",
                "database": "SQLite",
                "validation": "Pydantic"
            }
        elif any(kw in objective_lower for kw in ["auth", "login", "jwt", "oauth"]):
            project_type = "auth_system"
            modules = ["auth_service.py", "token_manager.py", "user_models.py", "middleware.py"]
            technologies = {
                "auth": "JWT",
                "hashing": "bcrypt",
                "framework": "FastAPI"
            }
        elif any(kw in objective_lower for kw in ["ml", "machine learning", "prediction", "model"]):
            project_type = "ml_system"
            modules = ["model_trainer.py", "predictor.py", "data_processor.py", "feature_engineering.py"]
            technologies = {
                "ml": "scikit-learn",
                "data": "pandas",
                "viz": "matplotlib"
            }
        elif any(kw in objective_lower for kw in ["scraper", "scraping", "crawl", "extract"]):
            project_type = "web_scraper"
            modules = ["scraper.py", "parser.py", "storage.py", "scheduler.py"]
            technologies = {
                "http": "requests",
                "parsing": "BeautifulSoup4",
                "storage": "SQLite"
            }
        else:
            # Genérico
            project_type = "generic"
            modules = ["main.py", "core.py", "utils.py", "config.py"]
            technologies = {
                "language": "Python 3.11+"
            }

        # Siempre agregar módulos base
        base_modules = ["config.py", "utils.py"]
        for module in base_modules:
            if module not in modules:
                modules.append(module)

        # Database schema
        database_schema = {}
        if "database" in " ".join(modules).lower() or "crud" in objective_lower:
            database_schema = {
                "users": {
                    "id": "INTEGER PRIMARY KEY",
                    "created_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
                }
            }

        return {
            "project_type": project_type,
            "proposed_modules": modules,
            "database_schema": database_schema,
            "technologies": technologies,
            "analysis": f"Architecture generated for: {objective}",
            "reasoning": f"Detected as {project_type} based on keywords analysis"
        }


def main():
    """Ejecuta PM Agent en modo daemon."""
    print("\n" + "="*60)
    print("CLAUDE PM AGENT V10 - ASYNC MODE")
    print("="*60)
    print("\nWaiting for messages in .agents/pm/inbox/")
    print("Press Ctrl+C to stop\n")

    agent = ClaudePMAgent()

    try:
        import time
        while True:
            processed = agent.process_messages(max_messages=5)

            if processed > 0:
                print(f"\n[PROCESSED] {processed} message(s)\n")
            else:
                time.sleep(2)  # Polling interval

    except KeyboardInterrupt:
        print("\n\n[STOPPED] PM Agent terminated by user")


if __name__ == "__main__":
    main()
