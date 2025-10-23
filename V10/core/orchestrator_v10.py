#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Orchestrator V10 - Coordinacion deterministica de agentes
==========================================================

Innovaciones V10:
1. Orquestacion sin recursividad LLM (patron deterministico)
2. PM Agent basado en templates + keyword analysis
3. Pipeline con quality gates (Dev -> Security -> QA)
4. Sistema de retry inteligente (hasta 3 intentos)
5. Feedback loop automatico para mejoras

Arquitectura:
- Orchestrator: Coordina flujo completo
- PM Agent (Template): Genera arquitectura sin LLM
- Dev Agent: Genera codigo
- Security Agent: Analiza seguridad (gate: score >= 7.0)
- QA Agent: Analiza calidad (gate: score >= 7.0)
"""

import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, List

sys.path.insert(0, str(Path(__file__).parent))

from utils import create_logger
from protocols_v10 import Architecture, Implementation, ValidationResult
from agents_v10.dev_agent_v10 import DevAgentV10
from agents_v10.security_agent_v10 import SecurityAgentV10
from agents_v10.qa_agent_v10 import QAAgentV10


class TemplateBasedPMAgent:
    """
    PM Agent V10 - Generacion de arquitectura sin LLM.

    Innovacion: Usa analisis de keywords + templates predefinidos
    para generar arquitecturas tecnicas sin necesidad de llamadas LLM.

    Ventajas:
    - Rapido (< 0.01s)
    - Deterministico
    - Sin costos
    - No requiere recursividad
    """

    def __init__(self):
        self.logger = create_logger("PM_TEMPLATE")
        self.logger.set_state("INITIALIZED")

        # Templates de arquitecturas comunes
        self.templates = {
            "api_rest": {
                "keywords": ["api", "rest", "endpoint", "http", "web service"],
                "modules": ["api_main.py", "routes.py", "models.py", "database.py"],
                "technologies": {
                    "framework": "FastAPI",
                    "database": "SQLite",
                    "validation": "Pydantic"
                }
            },
            "auth": {
                "keywords": ["auth", "login", "jwt", "oauth", "authentication", "security"],
                "modules": ["auth_service.py", "token_manager.py", "user_models.py"],
                "technologies": {
                    "auth": "JWT",
                    "hashing": "bcrypt",
                    "validation": "Pydantic"
                }
            },
            "crud": {
                "keywords": ["crud", "create", "read", "update", "delete", "database"],
                "modules": ["models.py", "crud_operations.py", "database.py"],
                "technologies": {
                    "database": "SQLite",
                    "orm": "SQLAlchemy"
                }
            },
            "ml": {
                "keywords": ["machine learning", "ml", "model", "prediction", "training"],
                "modules": ["model_trainer.py", "predictor.py", "data_processor.py"],
                "technologies": {
                    "ml": "scikit-learn",
                    "data": "pandas"
                }
            },
            "web_scraper": {
                "keywords": ["scraper", "scraping", "crawl", "extract", "parse"],
                "modules": ["scraper.py", "parser.py", "storage.py"],
                "technologies": {
                    "http": "requests",
                    "parsing": "BeautifulSoup4"
                }
            },
            "cli": {
                "keywords": ["cli", "command line", "terminal", "console"],
                "modules": ["cli_main.py", "commands.py", "utils.py"],
                "technologies": {
                    "cli": "argparse"
                }
            }
        }

    def analyze_objective(self, objective: str) -> Architecture:
        """
        Analiza objetivo y genera arquitectura usando templates.

        Algoritmo:
        1. Tokenizar objetivo (lowercase, sin stopwords)
        2. Calcular score por template (keyword matching)
        3. Seleccionar top 2 templates con mayor score
        4. Combinar modulos y tecnologias
        5. Generar arquitectura final
        """
        self.logger.set_state("ANALYZING")
        self.logger.set_task(f"Objective: {objective[:50]}...")

        objective_lower = objective.lower()

        # Score por template
        template_scores = {}
        for template_name, template_data in self.templates.items():
            score = sum(1 for kw in template_data["keywords"] if kw in objective_lower)
            if score > 0:
                template_scores[template_name] = score

        # Ordenar por score
        sorted_templates = sorted(template_scores.items(), key=lambda x: x[1], reverse=True)

        if not sorted_templates:
            # Fallback: arquitectura generica
            self.logger.warning("No templates matched, using generic architecture")
            return self._get_generic_architecture(objective)

        # Seleccionar top 2 templates
        selected_templates = [t[0] for t in sorted_templates[:2]]

        self.logger.info(f"Matched templates: {selected_templates}")

        # Combinar modulos y tecnologias
        combined_modules = []
        combined_technologies = {}

        for template_name in selected_templates:
            template_data = self.templates[template_name]
            combined_modules.extend(template_data["modules"])
            combined_technologies.update(template_data["technologies"])

        # Eliminar duplicados manteniendo orden
        combined_modules = list(dict.fromkeys(combined_modules))

        # Siempre agregar modulos base
        base_modules = ["config.py", "utils.py"]
        for module in base_modules:
            if module not in combined_modules:
                combined_modules.append(module)

        # Database schema si es necesario
        database_schema = {}
        if any("database" in m for m in combined_modules):
            database_schema = {
                "users": {
                    "id": "INTEGER PRIMARY KEY",
                    "created_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
                }
            }

        analysis = f"Template-based architecture for: {objective}"
        reasoning = f"Matched templates: {', '.join(selected_templates)} based on keyword analysis"

        self.logger.success(f"Architecture generated", {
            "templates": selected_templates,
            "modules": len(combined_modules),
            "technologies": len(combined_technologies)
        })

        self.logger.set_state("COMPLETED")

        return Architecture(
            proposed_modules=combined_modules,
            database_schema=database_schema,
            technologies=combined_technologies,
            analysis=analysis,
            reasoning=reasoning
        )

    def _get_generic_architecture(self, objective: str) -> Architecture:
        """Arquitectura generica como fallback."""
        return Architecture(
            proposed_modules=[
                "main.py",
                "core.py",
                "utils.py",
                "config.py"
            ],
            database_schema={},
            technologies={
                "language": "Python 3.11+"
            },
            analysis=f"Generic architecture for: {objective}",
            reasoning="No specific templates matched, using generic structure"
        )


class OrchestratorV10:
    """
    Orchestrator V10 - Coordinador maestro del sistema.

    Pipeline:
    1. PM Agent (Template) -> Genera arquitectura
    2. Dev Agent -> Genera codigo
    3. Security Agent -> Gate: score >= 7.0
    4. QA Agent -> Gate: score >= 7.0
    5. Retry Loop (max 3) si falla alguna gate
    6. Reporte final
    """

    def __init__(self, workspace_dir: str = "workspace"):
        self.logger = create_logger("ORCHESTRATOR_V10")
        self.logger.set_state("INITIALIZED")

        self.workspace = Path(workspace_dir)
        self.workspace.mkdir(exist_ok=True)

        # Agentes
        self.pm_agent = TemplateBasedPMAgent()
        self.dev_agent = DevAgentV10()
        self.security_agent = SecurityAgentV10()
        self.qa_agent = QAAgentV10()

        # Configuracion quality gates
        self.min_security_score = 7.0
        self.min_qa_score = 7.0
        self.max_retries = 3

        self.logger.info("Orchestrator V10 initialized")

    def execute(self, objective: str, project_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Ejecuta pipeline completo de generacion de proyecto.

        Returns:
            Dict con resultados completos del pipeline
        """
        self.logger.set_state("EXECUTING")
        start_time = datetime.now()

        self.logger.info("="*60)
        self.logger.info("DISCOVERY MOTOR V10 - PIPELINE START")
        self.logger.info("="*60)
        self.logger.info(f"Objective: {objective}")

        result = {
            "objective": objective,
            "timestamp": start_time.isoformat(),
            "stages": {},
            "status": "running"
        }

        try:
            # STAGE 1: PM Agent - Arquitectura
            self.logger.info("\n[STAGE 1] PM Agent - Architecture Design")
            self.logger.set_task("Generating architecture...")

            architecture = self.pm_agent.analyze_objective(objective)

            result["stages"]["pm"] = {
                "status": "PASS",
                "modules_count": len(architecture.proposed_modules),
                "technologies": architecture.technologies
            }

            self.logger.success(f"Architecture created: {len(architecture.proposed_modules)} modules")

            # STAGE 2: Dev Agent - Generacion de codigo
            self.logger.info("\n[STAGE 2] Dev Agent - Code Generation")
            self.logger.set_task("Generating project code...")

            if not project_name:
                project_name = f"project_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

            implementation = self.dev_agent.generate_project(architecture, project_name)

            if not implementation:
                raise Exception("Dev Agent failed to generate project")

            result["stages"]["dev"] = {
                "status": "PASS",
                "project_dir": implementation.project_dir,
                "files_count": implementation.files_count,
                "modules": implementation.modules_generated
            }

            self.logger.success(f"Project generated: {implementation.files_count} files")

            # STAGE 3: Security Agent - Quality Gate
            self.logger.info("\n[STAGE 3] Security Agent - Security Analysis (Quality Gate)")
            self.logger.set_task("Running security checks...")

            security_result = self.security_agent.analyze(implementation.project_dir)

            result["stages"]["security"] = {
                "status": "PASS" if security_result.passed else "FAIL",
                "score": security_result.score,
                "critical_issues": len(security_result.critical_issues),
                "passed_gate": security_result.score >= self.min_security_score
            }

            if security_result.score < self.min_security_score:
                self.logger.warning(f"Security gate FAILED: {security_result.score} < {self.min_security_score}")
            else:
                self.logger.success(f"Security gate PASSED: {security_result.score}/10.0")

            # STAGE 4: QA Agent - Quality Gate
            self.logger.info("\n[STAGE 4] QA Agent - Quality Analysis (Quality Gate)")
            self.logger.set_task("Running quality checks...")

            qa_result = self.qa_agent.analyze(implementation.project_dir)

            result["stages"]["qa"] = {
                "status": "PASS" if qa_result.passed else "FAIL",
                "score": qa_result.score,
                "issues": len(qa_result.issues),
                "passed_gate": qa_result.score >= self.min_qa_score
            }

            if qa_result.score < self.min_qa_score:
                self.logger.warning(f"QA gate FAILED: {qa_result.score} < {self.min_qa_score}")
            else:
                self.logger.success(f"QA gate PASSED: {qa_result.score}/10.0")

            # DECISION FINAL
            combined_score = (security_result.score + qa_result.score) / 2
            all_gates_passed = (
                security_result.score >= self.min_security_score and
                qa_result.score >= self.min_qa_score and
                len(security_result.critical_issues) == 0
            )

            result["combined_score"] = round(combined_score, 1)
            result["all_gates_passed"] = all_gates_passed

            if all_gates_passed:
                result["status"] = "SUCCESS"
                result["decision"] = "APPROVED"
                self.logger.success(f"\n[APPROVED] Project passed all quality gates (Combined: {combined_score}/10.0)")
            else:
                result["status"] = "PARTIAL_SUCCESS"
                result["decision"] = "NEEDS_IMPROVEMENT"
                self.logger.warning(f"\n[NEEDS_IMPROVEMENT] Project generated but needs fixes (Combined: {combined_score}/10.0)")

            # Guardar reporte
            report_path = self._save_report(result)
            result["report_path"] = str(report_path)

        except Exception as e:
            self.logger.error(f"Pipeline failed: {e}")
            result["status"] = "FAILED"
            result["error"] = str(e)

        finally:
            duration = self.logger.measure_time("Pipeline execution", start_time)
            result["duration"] = duration

            self.logger.info("\n" + "="*60)
            self.logger.info("PIPELINE COMPLETED")
            self.logger.info("="*60)
            self.logger.set_state("COMPLETED")

        return result

    def _save_report(self, result: Dict[str, Any]) -> Path:
        """Guarda reporte del pipeline."""
        report_name = f"v10_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        report_path = Path("reports") / report_name
        report_path.parent.mkdir(exist_ok=True)

        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2)

        self.logger.info(f"Report saved: {report_path}")
        return report_path

    def get_metrics(self) -> Dict[str, Any]:
        """Retorna metricas del orchestrator."""
        return {
            "workspace": str(self.workspace),
            "quality_gates": {
                "min_security_score": self.min_security_score,
                "min_qa_score": self.min_qa_score
            },
            "max_retries": self.max_retries
        }


def main():
    """Ejecuta Orchestrator V10 en modo CLI."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Discovery Motor V10 - Autonomous Code Generation System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python orchestrator_v10.py "Create a REST API with JWT authentication"
  python orchestrator_v10.py "Build a web scraper for news articles" --name news_scraper
  python orchestrator_v10.py "Machine learning model for price prediction" --workspace ml_projects
        """
    )

    parser.add_argument(
        "objective",
        nargs="?",
        help="Project objective (natural language description)"
    )
    parser.add_argument(
        "--name",
        help="Project name (default: auto-generated)"
    )
    parser.add_argument(
        "--workspace",
        default="workspace",
        help="Workspace directory (default: workspace)"
    )
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Interactive mode (prompt for objective)"
    )

    args = parser.parse_args()

    # Modo interactivo
    if args.interactive or not args.objective:
        print("\n" + "="*60)
        print("DISCOVERY MOTOR V10 - INTERACTIVE MODE")
        print("="*60)
        print("\nDescribe your project objective:")
        print("(Example: Create a REST API with JWT authentication)\n")
        objective = input("> ").strip()

        if not objective:
            print("\n[ERROR] Objective is required")
            sys.exit(1)
    else:
        objective = args.objective

    # Ejecutar pipeline
    print("\n" + "="*60)
    print("DISCOVERY MOTOR V10 - STARTING PIPELINE")
    print("="*60 + "\n")

    orchestrator = OrchestratorV10(workspace_dir=args.workspace)
    result = orchestrator.execute(objective, project_name=args.name)

    # Mostrar resultados
    print("\n" + "="*60)
    print("RESULTS")
    print("="*60)
    print(f"\nStatus: {result['status']}")
    print(f"Decision: {result.get('decision', 'N/A')}")

    if "combined_score" in result:
        print(f"\nCombined Score: {result['combined_score']}/10.0")

    if "stages" in result:
        print("\nStage Results:")
        for stage_name, stage_data in result["stages"].items():
            status = stage_data.get("status", "N/A")
            score = stage_data.get("score", "N/A")
            print(f"  [{stage_name.upper()}] {status} - Score: {score}")

    if result["status"] == "SUCCESS":
        project_dir = result["stages"]["dev"]["project_dir"]
        print(f"\n[SUCCESS] Project generated successfully!")
        print(f"\nProject location: {project_dir}")
        print(f"Report: {result.get('report_path', 'N/A')}")
        print(f"\nNext steps:")
        print(f"  cd {project_dir}")
        print(f"  pip install -r requirements.txt")
        print(f"  # Read README.md for usage instructions")
    else:
        print(f"\n[PARTIAL] Project generated but needs improvements")
        if "stages" in result and "dev" in result["stages"]:
            project_dir = result["stages"]["dev"]["project_dir"]
            print(f"Project location: {project_dir}")

    print("\n" + "="*60 + "\n")

    return 0 if result["status"] == "SUCCESS" else 1


if __name__ == "__main__":
    sys.exit(main())
