#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Orchestrator V10 ASYNC - Sistema completo anti-deadlock
========================================================

INNOVACION PRINCIPAL:
Rompe el deadlock Claude→Claude usando Actor Model + Message Queue

ARQUITECTURA:
1. Orchestrator (Terminal 1 - Claude) coordina todo
2. PM Agent (Terminal 2 - Claude) analiza arquitectura
3. Dev Agent (Terminal 1 - Python puro) genera código
4. Security Agent (Terminal 1 - Python puro) analiza seguridad
5. QA Agent (Terminal 1 - Python puro) analiza calidad

COMUNICACION:
- T1 ← filesystem → T2 (async, no-bloqueante)
- PM Agent corre en T2 (otro Claude)
- Dev/Security/QA corren en T1 (Python puro, sin LLM)

FLUJO COMPLETO:
User da objetivo en T1
    ↓
T1 escribe en .agents/pm/inbox/
    ↓
T1 lanza T2 con claude_pm_agent.py (fire-and-forget)
    ↓
T2 (Claude) lee mensaje, analiza, escribe en .agents/orchestrator/inbox/
    ↓
T1 detecta respuesta via polling (no-bloqueante)
    ↓
T1 ejecuta Dev Agent (Python puro)
    ↓
T1 ejecuta Security Agent (Python puro)
    ↓
T1 ejecuta QA Agent (Python puro)
    ↓
T1 genera reporte final
    ↓
✅ PROYECTO COMPLETO (sin deadlock!)
"""

import os
import sys
import json
import time
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any

sys.path.insert(0, str(Path(__file__).parent))

from utils import create_logger
from protocols_v10 import Architecture
from async_agent_system import AsyncMessageQueue, ClaudeTerminalLauncher
from agents_v10.dev_agent_v10 import DevAgentV10
from agents_v10.security_agent_v10 import SecurityAgentV10
from agents_v10.qa_agent_v10 import QAAgentV10


class OrchestratorV10Async:
    """
    Orchestrator V10 con comunicación asíncrona.

    INNOVACION: Usa múltiples Claude instances sin deadlock
    """

    def __init__(self, workspace_dir: str = "workspace"):
        self.logger = create_logger("ORCH_V10_ASYNC")
        self.logger.set_state("INITIALIZED")

        self.workspace = Path(workspace_dir)
        self.workspace.mkdir(exist_ok=True)

        # Async communication
        self.message_queue = AsyncMessageQueue()
        self.launcher = ClaudeTerminalLauncher()

        self.agent_name = "orchestrator"

        # Python-only agents (no LLM)
        self.dev_agent = DevAgentV10()
        self.security_agent = SecurityAgentV10()
        self.qa_agent = QAAgentV10()

        # Quality gates
        self.min_security_score = 7.0
        self.min_qa_score = 7.0

        self.logger.info("Orchestrator V10 Async initialized")

    def execute(
        self,
        objective: str,
        project_name: Optional[str] = None,
        use_claude_pm: bool = True
    ) -> Dict[str, Any]:
        """
        Ejecuta pipeline completo.

        Args:
            objective: Objetivo del proyecto
            project_name: Nombre del proyecto (opcional)
            use_claude_pm: Si True, usa Claude PM en terminal separada
                          Si False, usa template PM (sin LLM)
        """

        self.logger.set_state("EXECUTING")
        start_time = datetime.now()

        self.logger.info("="*60)
        self.logger.info("DISCOVERY MOTOR V10 ASYNC - PIPELINE START")
        self.logger.info("="*60)
        self.logger.info(f"Objective: {objective}")
        self.logger.info(f"Use Claude PM: {use_claude_pm}")

        result = {
            "objective": objective,
            "timestamp": start_time.isoformat(),
            "mode": "async_claude" if use_claude_pm else "template",
            "stages": {},
            "status": "running"
        }

        try:
            # STAGE 1: PM Agent
            self.logger.info("\n[STAGE 1] PM Agent - Architecture Design")

            if use_claude_pm:
                architecture = self._execute_claude_pm_agent(objective)
            else:
                architecture = self._execute_template_pm_agent(objective)

            if not architecture:
                raise Exception("PM Agent failed to generate architecture")

            result["stages"]["pm"] = {
                "status": "SUCCESS",
                "modules_count": len(architecture.proposed_modules),
                "technologies": architecture.technologies
            }

            self.logger.success(f"Architecture created: {len(architecture.proposed_modules)} modules")

            # STAGE 2: Dev Agent
            self.logger.info("\n[STAGE 2] Dev Agent - Code Generation")

            if not project_name:
                project_name = f"project_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

            implementation = self.dev_agent.generate_project(architecture, project_name)

            if not implementation:
                raise Exception("Dev Agent failed")

            result["stages"]["dev"] = {
                "status": "SUCCESS",
                "project_dir": implementation.project_dir,
                "files_count": implementation.files_count
            }

            self.logger.success(f"Project generated: {implementation.files_count} files")

            # STAGE 3: Security Agent
            self.logger.info("\n[STAGE 3] Security Agent - Security Analysis")

            security_result = self.security_agent.analyze(implementation.project_dir)

            result["stages"]["security"] = {
                "status": "PASS" if security_result.passed else "FAIL",
                "score": security_result.score,
                "critical_issues": len(security_result.critical_issues),
                "passed_gate": security_result.score >= self.min_security_score
            }

            if security_result.score >= self.min_security_score:
                self.logger.success(f"Security gate PASSED: {security_result.score}/10.0")
            else:
                self.logger.warn(f"Security gate FAILED: {security_result.score}/10.0")

            # STAGE 4: QA Agent
            self.logger.info("\n[STAGE 4] QA Agent - Quality Analysis")

            qa_result = self.qa_agent.analyze(implementation.project_dir)

            result["stages"]["qa"] = {
                "status": "PASS" if qa_result.passed else "FAIL",
                "score": qa_result.score,
                "issues": len(qa_result.issues),
                "passed_gate": qa_result.score >= self.min_qa_score
            }

            if qa_result.score >= self.min_qa_score:
                self.logger.success(f"QA gate PASSED: {qa_result.score}/10.0")
            else:
                self.logger.warn(f"QA gate FAILED: {qa_result.score}/10.0")

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
                self.logger.success(f"\n[APPROVED] Combined Score: {combined_score}/10.0")
            else:
                result["status"] = "PARTIAL_SUCCESS"
                result["decision"] = "NEEDS_IMPROVEMENT"
                self.logger.warn(f"\n[NEEDS_IMPROVEMENT] Combined Score: {combined_score}/10.0")

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

    def _execute_claude_pm_agent(self, objective: str) -> Optional[Architecture]:
        """
        Ejecuta PM Agent en terminal Claude separada (ASYNC).

        INNOVACION: Rompe deadlock usando fire-and-forget + polling
        """

        self.logger.info("Starting Claude PM Agent (async mode)...")

        # Enviar mensaje
        pm_message = self.message_queue.send_message(
            to_agent="pm",
            from_agent=self.agent_name,
            task_type="generate_architecture",
            payload={"objective": objective}
        )

        self.logger.info(f"Message sent: {pm_message.message_id}")

        # ✅ Lanzar Claude PM Agent (fire-and-forget)
        # NOTA: Esto requiere que el usuario ejecute manualmente:
        # python claude_pm_agent.py en Terminal 2

        self.logger.info("Waiting for PM Agent to process...")
        self.logger.info("[MANUAL] Run in Terminal 2: python claude_pm_agent.py")

        # Esperar respuesta via polling (no-bloqueante)
        pm_reply = self.message_queue.wait_for_reply(
            agent_name=self.agent_name,
            message_id=pm_message.message_id,
            timeout=120
        )

        if not pm_reply:
            self.logger.error("PM Agent timeout")
            return None

        # Parsear respuesta
        if pm_reply.payload.get("status") != "SUCCESS":
            self.logger.error("PM Agent failed")
            return None

        arch_data = pm_reply.payload.get("architecture")

        return Architecture(
            proposed_modules=arch_data["proposed_modules"],
            database_schema=arch_data.get("database_schema", {}),
            technologies=arch_data["technologies"],
            analysis=arch_data["analysis"],
            reasoning=arch_data["reasoning"]
        )

    def _execute_template_pm_agent(self, objective: str) -> Architecture:
        """
        Ejecuta PM Agent con templates (sin LLM, fallback).
        """
        from orchestrator_v10 import TemplateBasedPMAgent

        pm = TemplateBasedPMAgent()
        return pm.analyze_objective(objective)

    def _save_report(self, result: Dict[str, Any]) -> Path:
        """Guarda reporte."""
        report_dir = Path("reports")
        report_dir.mkdir(exist_ok=True)

        report_name = f"v10_async_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        report_path = report_dir / report_name

        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2)

        self.logger.info(f"Report saved: {report_path}")
        return report_path


def main():
    """CLI del Orchestrator V10 Async."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Discovery Motor V10 ASYNC - Anti-Deadlock System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Modo template (sin Claude PM, rápido)
  python orchestrator_v10_async.py "Create REST API" --no-claude-pm

  # Modo async Claude (requiere Terminal 2 corriendo claude_pm_agent.py)
  Terminal 1: python orchestrator_v10_async.py "Create REST API"
  Terminal 2: python claude_pm_agent.py
        """
    )

    parser.add_argument("objective", nargs="?", help="Project objective")
    parser.add_argument("--name", help="Project name")
    parser.add_argument("--workspace", default="workspace", help="Workspace directory")
    parser.add_argument("--no-claude-pm", action="store_true", help="Use template PM (faster, no LLM)")
    parser.add_argument("--interactive", action="store_true", help="Interactive mode")

    args = parser.parse_args()

    if args.interactive or not args.objective:
        print("\n" + "="*60)
        print("DISCOVERY MOTOR V10 ASYNC - INTERACTIVE MODE")
        print("="*60)
        print("\nProject objective:")
        objective = input("> ").strip()
        if not objective:
            print("[ERROR] Objective required")
            sys.exit(1)
    else:
        objective = args.objective

    print("\n" + "="*60)
    print("DISCOVERY MOTOR V10 ASYNC - STARTING")
    print("="*60 + "\n")

    orchestrator = OrchestratorV10Async(workspace_dir=args.workspace)

    result = orchestrator.execute(
        objective,
        project_name=args.name,
        use_claude_pm=not args.no_claude_pm
    )

    # Mostrar resultados
    print("\n" + "="*60)
    print("RESULTS")
    print("="*60)
    print(f"\nStatus: {result['status']}")
    print(f"Decision: {result.get('decision', 'N/A')}")

    if "combined_score" in result:
        print(f"Combined Score: {result['combined_score']}/10.0")

    if "stages" in result:
        print("\nStages:")
        for stage, data in result["stages"].items():
            status = data.get("status", "N/A")
            score = data.get("score", "N/A")
            print(f"  [{stage.upper()}] {status} - Score: {score}")

    if result["status"] == "SUCCESS":
        project_dir = result["stages"]["dev"]["project_dir"]
        print(f"\n[SUCCESS] Project: {project_dir}")
        print(f"Report: {result.get('report_path', 'N/A')}")
    elif result["status"] == "FAILED":
        print(f"\n[FAILED] {result.get('error', 'Unknown error')}")

    print("\n" + "="*60 + "\n")

    return 0 if result["status"] == "SUCCESS" else 1


if __name__ == "__main__":
    sys.exit(main())
