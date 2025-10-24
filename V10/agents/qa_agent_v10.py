#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
QA Agent V10 - Análisis de calidad estático
============================================

Análisis SIN LLM:
- Docstrings
- Type hints
- Tests existence
- Code structure
- Score automático
"""

import sys

import re
import ast
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

from V10.utils import create_logger
from V10.protocols import ValidationResult


class QAAgentV10:
    """QA Agent V10 - Análisis estático de calidad."""

    def __init__(self):
        self.logger = create_logger("QA_V10")
        self.logger.set_state("INITIALIZED")
        self.logger.info("QA Agent V10 initialized")

    def analyze(self, project_dir: str) -> ValidationResult:
        """Analiza calidad del código."""
        self.logger.set_state("ANALYZING")
        start_time = datetime.now()

        project_path = Path(project_dir)
        self.logger.set_task(f"Analyzing: {project_path.name}")

        issues = []
        warnings = []

        py_files = list(project_path.rglob("*.py"))
        self.logger.info(f"Found {len(py_files)} Python files")

        total_functions = 0
        functions_with_docstrings = 0
        functions_with_types = 0

        for file_path in py_files:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()

                tree = ast.parse(content)

                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        total_functions += 1

                        if ast.get_docstring(node):
                            functions_with_docstrings += 1
                        else:
                            warnings.append(f"{file_path.name}:{node.lineno} - Function '{node.name}' missing docstring")

                        if node.returns or any(arg.annotation for arg in node.args.args):
                            functions_with_types += 1
                        else:
                            issues.append(f"{file_path.name}:{node.lineno} - Function '{node.name}' missing type hints")

            except Exception as e:
                self.logger.error(f"Error parsing {file_path.name}: {e}")

        # Check tests
        has_tests = any("test" in str(f).lower() for f in py_files)
        if not has_tests:
            issues.append("No test files found")

        # Calculate score
        score = self._calculate_score(
            total_functions,
            functions_with_docstrings,
            functions_with_types,
            has_tests,
            len(issues),
            len(warnings)
        )

        passed = score >= 7.0

        duration = self.logger.measure_time("QA analysis", start_time)

        self.logger.success(
            f"QA analysis completed",
            {
                "score": score,
                "functions": total_functions,
                "with_docstrings": functions_with_docstrings,
                "with_types": functions_with_types,
                "has_tests": has_tests,
                "duration": duration
            }
        )

        self.logger.set_state("COMPLETED")

        return ValidationResult(
            agent_type="qa",
            score=score,
            issues=issues,
            critical_issues=[],
            warnings=warnings,
            passed=passed,
            timestamp=datetime.now().isoformat()
        )

    def _calculate_score(self, total_funcs, with_docs, with_types, has_tests, issues_count, warnings_count):
        """Calcula score de calidad."""
        if total_funcs == 0:
            return 8.0  # Proyecto muy pequeño

        doc_ratio = with_docs / total_funcs if total_funcs > 0 else 0
        type_ratio = with_types / total_funcs if total_funcs > 0 else 0

        score = 10.0
        score -= (1 - doc_ratio) * 3.0  # Docstrings importantes
        score -= (1 - type_ratio) * 2.0  # Type hints importantes
        score -= 1.0 if not has_tests else 0
        score -= issues_count * 0.2
        score -= warnings_count * 0.1

        return max(0.0, min(10.0, round(score, 1)))


def main():
    """Test del QA Agent V10."""
    import argparse

    parser = argparse.ArgumentParser(description="QA Agent V10")
    parser.add_argument(
        "project_dir",
        nargs="?",
        default="workspace/test_project",
        help="Project directory"
    )

    args = parser.parse_args()

    agent = QAAgentV10()
    print(f"\n[ANALYZING] {args.project_dir}\n")

    result = agent.analyze(args.project_dir)

    print(f"\n[RESULTS]")
    print(f"Score: {result.score}/10.0")
    print(f"Passed: {'YES' if result.passed else 'NO'}")
    print(f"\nIssues: {len(result.issues)}")
    for issue in result.issues[:10]:
        print(f"  {issue}")
    print(f"\nWarnings: {len(result.warnings)}")
    for warning in result.warnings[:10]:
        print(f"  {warning}")

    agent.logger.print_summary()
    sys.exit(0 if result.passed else 1)


if __name__ == "__main__":
    main()
