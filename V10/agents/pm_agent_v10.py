#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PM Agent V10 - Product Manager con Claude CLI directo
======================================================

CAMBIO CLAVE vs V8:
- V8: File Communicator (espera humano) → BLOQUEADO POR SIEMPRE
- V10: Claude CLI directo via subprocess → 100% AUTONOMO

Características:
- Análisis de objetivos con Claude CLI
- Propuesta de arquitectura empresarial
- Validación de respuestas JSON
- Logging completo de cada operación
- Retry automático en fallos
"""

import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, List

# Imports de infraestructura V10
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils import create_logger, ClaudeCLIWrapper
from protocols_v10 import Architecture


class PMAgentV10:
    """
    Product Manager Agent V10 - 100% Autónomo con Claude CLI.

    Responsabilidades:
    1. Analizar objetivo del usuario
    2. Proponer arquitectura de módulos
    3. Definir esquema de base de datos
    4. Seleccionar tecnologías apropiadas
    5. Documentar razonamiento técnico
    """

    def __init__(self, timeout: int = 300):
        """
        Inicializa PM Agent V10.

        Args:
            timeout: Timeout para Claude CLI en segundos (default: 5 min)
        """
        self.logger = create_logger("PM_AGENT_V10")
        self.claude = ClaudeCLIWrapper(logger=self.logger, timeout=timeout)

        self.logger.set_state("INITIALIZED")
        self.logger.info("PM Agent V10 initialized")
        self.logger.info(f"Claude CLI timeout: {timeout}s")

    def propose_architecture(self, objective: str) -> Optional[Architecture]:
        """
        Propone arquitectura completa para el objetivo.

        Args:
            objective: Descripción del proyecto a crear

        Returns:
            Architecture object si exitoso, None si falla
        """
        self.logger.set_state("ANALYZING")
        self.logger.set_task(f"Analyzing objective: {objective[:50]}...")

        start_time = datetime.now()

        # Construir prompt empresarial
        prompt = self._build_architecture_prompt(objective)

        self.logger.info(
            "Requesting architecture from Claude",
            {"prompt_length": len(prompt), "objective_preview": objective[:100]}
        )

        # Ejecutar Claude CLI con retry
        result = self.claude.execute_with_retry(
            prompt=prompt,
            max_retries=3,
            expect_json=True
        )

        duration = self.logger.measure_time("Architecture generation", start_time)

        if not result.success:
            self.logger.error(
                "Failed to generate architecture",
                {"error": result.error, "duration": duration}
            )
            self.logger.set_state("FAILED")
            return None

        # Validar respuesta
        try:
            architecture = self._validate_and_parse_response(result.response)

            if architecture:
                self.logger.success(
                    "Architecture generated successfully",
                    {
                        "modules_count": len(architecture.proposed_modules),
                        "technologies": list(architecture.technologies.keys()),
                        "duration": duration
                    }
                )
                self.logger.set_state("SUCCESS")
                return architecture
            else:
                self.logger.error("Architecture validation failed")
                self.logger.set_state("FAILED")
                return None

        except Exception as e:
            self.logger.error(
                "Exception during architecture parsing",
                {"error": str(e), "type": type(e).__name__}
            )
            self.logger.set_state("FAILED")
            return None

    def _build_architecture_prompt(self, objective: str) -> str:
        """
        Construye prompt detallado para Claude.

        Este prompt incluye:
        - Objetivo del usuario
        - Requisitos empresariales estándar
        - Formato de respuesta JSON esperado
        - Ejemplos de buenas arquitecturas
        """
        prompt = f"""You are an expert Software Architect and Product Manager with 15+ years of experience designing enterprise-grade applications.

USER OBJECTIVE:
{objective}

YOUR TASK:
Analyze this objective and propose a complete, production-ready architecture.

REQUIREMENTS:
1. Propose 3-8 Python modules that implement the objective
2. Design a database schema (tables, fields, relationships)
3. Select appropriate technologies (framework, database, auth, etc.)
4. Provide technical analysis explaining your decisions
5. Include security, scalability, and maintainability considerations

ENTERPRISE STANDARDS TO FOLLOW:
- RESTful API design
- JWT authentication for protected endpoints
- Input validation and sanitization
- Proper error handling and logging
- Database transactions where needed
- Environment-based configuration (.env)
- Comprehensive testing strategy
- API documentation (OpenAPI/Swagger)

RESPONSE FORMAT (JSON):
{{
  "proposed_modules": [
    "auth_service.py",
    "user_management.py",
    "main_api.py",
    "database_models.py",
    "config.py"
  ],
  "database_schema": {{
    "users": {{
      "id": "INTEGER PRIMARY KEY",
      "email": "TEXT UNIQUE NOT NULL",
      "password_hash": "TEXT NOT NULL",
      "created_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
    }},
    "sessions": {{
      "id": "INTEGER PRIMARY KEY",
      "user_id": "INTEGER FOREIGN KEY REFERENCES users(id)",
      "token": "TEXT UNIQUE NOT NULL",
      "expires_at": "TIMESTAMP NOT NULL"
    }}
  }},
  "technologies": {{
    "framework": "FastAPI",
    "database": "SQLite (dev) / PostgreSQL (prod)",
    "auth": "JWT with PyJWT",
    "validation": "Pydantic",
    "testing": "pytest",
    "documentation": "OpenAPI (built-in FastAPI)"
  }},
  "analysis": "This objective requires a RESTful API with user authentication. FastAPI provides automatic validation, async support, and built-in documentation. SQLite for development simplifies setup, while PostgreSQL is recommended for production. JWT tokens provide stateless authentication suitable for microservices.",
  "reasoning": "The proposed modules follow separation of concerns: auth_service handles authentication logic, user_management handles CRUD operations, main_api coordinates endpoints, database_models defines ORM schemas, and config manages environment variables. This structure supports testing, scaling, and maintenance."
}}

IMPORTANT VALIDATION RULES:
- proposed_modules MUST be a list of strings (Python filenames)
- database_schema MUST be a dict of table definitions
- technologies MUST specify framework, database, auth, validation, testing
- analysis MUST explain WHY these choices (50-150 words)
- reasoning MUST explain HOW modules work together (50-150 words)

RETURN ONLY THE JSON OBJECT. NO MARKDOWN. NO EXPLANATIONS OUTSIDE JSON.
"""
        return prompt

    def _validate_and_parse_response(self, response: Dict[str, Any]) -> Optional[Architecture]:
        """
        Valida que la respuesta de Claude tenga el formato correcto.

        Args:
            response: Respuesta JSON de Claude

        Returns:
            Architecture object si válido, None si inválido
        """
        required_keys = [
            "proposed_modules",
            "database_schema",
            "technologies",
            "analysis",
            "reasoning"
        ]

        # Verificar que todas las keys existan
        missing = [k for k in required_keys if k not in response]

        if missing:
            self.logger.error(
                "Response missing required keys",
                {"missing_keys": missing, "received_keys": list(response.keys())}
            )
            return None

        # Validar tipos
        if not isinstance(response["proposed_modules"], list):
            self.logger.error("proposed_modules must be a list")
            return None

        if not isinstance(response["database_schema"], dict):
            self.logger.error("database_schema must be a dict")
            return None

        if not isinstance(response["technologies"], dict):
            self.logger.error("technologies must be a dict")
            return None

        # Validar que proposed_modules no esté vacío
        if len(response["proposed_modules"]) < 3:
            self.logger.error(
                "Too few modules proposed",
                {"count": len(response["proposed_modules"]), "minimum": 3}
            )
            return None

        # Validar que technologies tenga keys importantes
        required_techs = ["framework", "database"]
        missing_techs = [k for k in required_techs if k not in response["technologies"]]

        if missing_techs:
            self.logger.warn(
                "Technologies missing recommended keys",
                {"missing": missing_techs}
            )

        # Crear Architecture object
        try:
            architecture = Architecture(
                proposed_modules=response["proposed_modules"],
                database_schema=response["database_schema"],
                technologies=response["technologies"],
                analysis=response["analysis"],
                reasoning=response["reasoning"]
            )

            self.logger.success("Architecture validation passed")
            return architecture

        except Exception as e:
            self.logger.error(
                "Failed to create Architecture object",
                {"error": str(e)}
            )
            return None

    def save_architecture(self, architecture: Architecture, output_dir: Path) -> bool:
        """
        Guarda arquitectura en archivo JSON.

        Args:
            architecture: Architecture object
            output_dir: Directorio donde guardar

        Returns:
            True si exitoso, False si falla
        """
        try:
            output_dir.mkdir(parents=True, exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = output_dir / f"architecture_{timestamp}.json"

            with open(filename, "w", encoding="utf-8") as f:
                json.dump(architecture.to_dict(), f, indent=2)

            self.logger.success(
                "Architecture saved",
                {"file": str(filename)}
            )

            return True

        except Exception as e:
            self.logger.error(
                "Failed to save architecture",
                {"error": str(e)}
            )
            return False

    def get_metrics(self) -> Dict[str, Any]:
        """Retorna métricas combinadas del agente y Claude."""
        return {
            "pm_agent": self.logger.get_metrics(),
            "claude_cli": self.claude.get_metrics()
        }


def main():
    """Test del PM Agent V10."""
    import argparse

    parser = argparse.ArgumentParser(description="PM Agent V10 - Architecture Proposal")
    parser.add_argument(
        "--test",
        action="store_true",
        help="Run test with simple objective"
    )
    parser.add_argument(
        "--objective",
        type=str,
        help="Project objective to analyze"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=".shared/pm_v10",
        help="Output directory for architecture"
    )

    args = parser.parse_args()

    # Determinar objetivo
    if args.test:
        objective = "Create a simple REST API for task management with JWT authentication. Users should be able to create, read, update, and delete tasks. Each task has a title, description, status, and due date."
        print("\n[TEST MODE] Using test objective:")
        print(f"  {objective}\n")
    elif args.objective:
        objective = args.objective
    else:
        print("[ERROR] Please provide --test or --objective")
        sys.exit(1)

    # Crear agente
    print("[INIT] Creating PM Agent V10...")
    agent = PMAgentV10(timeout=300)

    # Proponer arquitectura
    print(f"\n[ANALYZING] Objective: {objective[:80]}...\n")
    architecture = agent.propose_architecture(objective)

    if architecture:
        print("\n[SUCCESS] Architecture generated!\n")
        print(f"Modules ({len(architecture.proposed_modules)}):")
        for module in architecture.proposed_modules:
            print(f"  - {module}")

        print(f"\nTechnologies:")
        for tech, value in architecture.technologies.items():
            print(f"  - {tech}: {value}")

        print(f"\nDatabase Tables: {len(architecture.database_schema)}")
        for table in architecture.database_schema.keys():
            print(f"  - {table}")

        # Guardar
        output_dir = Path(args.output)
        if agent.save_architecture(architecture, output_dir):
            print(f"\n[SAVED] Architecture saved to {output_dir}")

        # Métricas
        metrics = agent.get_metrics()
        print(f"\n[METRICS]")
        print(f"  Claude executions: {metrics['claude_cli']['total_executions']}")
        print(f"  Total duration: {metrics['claude_cli']['total_duration_seconds']}s")
        print(f"  Agent events: {sum(metrics['pm_agent']['event_counts'].values())}")

        # Summary
        agent.logger.print_summary()

        print("\n[OK] PM Agent V10 test completed successfully!")
        sys.exit(0)
    else:
        print("\n[FAILED] Architecture generation failed")

        # Summary
        agent.logger.print_summary()

        print("\n[ERROR] PM Agent V10 test failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
