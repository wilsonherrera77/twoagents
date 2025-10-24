#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Security Agent V10 - Análisis de seguridad estático
====================================================

Análisis SIN LLM (rápido y gratis):
- Detección de secretos hardcodeados
- Patrones de SQL injection
- Validación de input
- Manejo de errores
- Score automático

NO requiere Claude CLI.
"""

import sys

import re
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

from V10.utils import create_logger
from V10.protocols import ValidationResult


class SecurityAgentV10:
    """
    Security Agent V10 - Análisis estático de seguridad.

    Checks:
    1. Secretos hardcodeados
    2. SQL injection patterns
    3. XSS vulnerabilities
    4. Insecure functions
    5. Missing input validation
    """

    def __init__(self):
        self.logger = create_logger("SECURITY_V10")
        self.logger.set_state("INITIALIZED")
        self.logger.info("Security Agent V10 initialized")

    def analyze(self, project_dir: str) -> ValidationResult:
        """
        Analiza proyecto para vulnerabilidades de seguridad.

        Args:
            project_dir: Directorio del proyecto

        Returns:
            ValidationResult con score y issues
        """
        self.logger.set_state("ANALYZING")
        start_time = datetime.now()

        project_path = Path(project_dir)
        self.logger.set_task(f"Analyzing: {project_path.name}")

        issues = []
        critical_issues = []
        warnings = []

        # Obtener todos los archivos Python
        py_files = list(project_path.rglob("*.py"))

        self.logger.info(f"Found {len(py_files)} Python files")

        for file_path in py_files:
            self.logger.debug(f"Checking: {file_path.name}")

            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()

                # Run security checks
                file_issues = self._check_file(file_path, content)

                for issue in file_issues:
                    if issue["severity"] == "critical":
                        critical_issues.append(issue["message"])
                    elif issue["severity"] == "warning":
                        warnings.append(issue["message"])
                    else:
                        issues.append(issue["message"])

            except Exception as e:
                self.logger.error(f"Error reading {file_path.name}: {e}")

        # Calcular score
        score = self._calculate_score(
            len(py_files),
            len(critical_issues),
            len(issues),
            len(warnings)
        )

        passed = score >= 7.0 and len(critical_issues) == 0

        duration = self.logger.measure_time("Security analysis", start_time)

        self.logger.success(
            f"Security analysis completed",
            {
                "score": score,
                "files": len(py_files),
                "critical": len(critical_issues),
                "issues": len(issues),
                "warnings": len(warnings),
                "duration": duration
            }
        )

        self.logger.set_state("COMPLETED")

        return ValidationResult(
            agent_type="security",
            score=score,
            issues=issues,
            critical_issues=critical_issues,
            warnings=warnings,
            passed=passed,
            timestamp=datetime.now().isoformat()
        )

    def _check_file(self, file_path: Path, content: str) -> List[Dict[str, Any]]:
        """Ejecuta checks de seguridad en un archivo."""
        issues = []

        # Check 1: Hardcoded secrets
        issues.extend(self._check_hardcoded_secrets(file_path, content))

        # Check 2: SQL injection
        issues.extend(self._check_sql_injection(file_path, content))

        # Check 3: XSS vulnerabilities
        issues.extend(self._check_xss(file_path, content))

        # Check 4: Insecure functions
        issues.extend(self._check_insecure_functions(file_path, content))

        # Check 5: Missing error handling
        issues.extend(self._check_error_handling(file_path, content))

        return issues

    def _check_hardcoded_secrets(self, file_path: Path, content: str) -> List[Dict]:
        """Detecta secretos hardcodeados."""
        issues = []

        # Patrones de secretos
        patterns = [
            (r'password\s*=\s*["\'](?!.*\{)(.{3,})["\']', "Hardcoded password"),
            (r'api[_-]?key\s*=\s*["\'](?!.*\{)(.{10,})["\']', "Hardcoded API key"),
            (r'secret[_-]?key\s*=\s*["\'](?!.*\{)(.{10,})["\']', "Hardcoded secret key"),
            (r'token\s*=\s*["\'](?!.*\{)(.{20,})["\']', "Hardcoded token"),
            (r'aws[_-]?secret\s*=\s*["\'](.{20,})["\']', "Hardcoded AWS secret"),
        ]

        for pattern, desc in patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                # Ignorar si es un placeholder o viene de env
                if not any(x in match.group(0).lower() for x in ["env", "getenv", "os.environ", "change-this", "your-", "example"]):
                    issues.append({
                        "severity": "critical",
                        "message": f"{file_path.name}: {desc} detected"
                    })

        return issues

    def _check_sql_injection(self, file_path: Path, content: str) -> List[Dict]:
        """Detecta posibles SQL injection."""
        issues = []

        # Patrones de SQL injection
        patterns = [
            r'execute\([^)]*%[^)]*\)',  # execute con string formatting
            r'cursor\.execute\([^)]*\+[^)]*\)',  # concatenación en execute
            r'SELECT.*FROM.*WHERE.*\+',  # concatenación en query
        ]

        for pattern in patterns:
            if re.search(pattern, content, re.IGNORECASE):
                issues.append({
                    "severity": "critical",
                    "message": f"{file_path.name}: Possible SQL injection (use parameterized queries)"
                })
                break  # Solo reportar una vez por archivo

        return issues

    def _check_xss(self, file_path: Path, content: str) -> List[Dict]:
        """Detecta posibles XSS."""
        issues = []

        # Patrones de XSS
        if "html" in content.lower() or "render" in content.lower():
            if not re.search(r'escape|sanitize|bleach', content, re.IGNORECASE):
                issues.append({
                    "severity": "warning",
                    "message": f"{file_path.name}: HTML rendering without sanitization"
                })

        return issues

    def _check_insecure_functions(self, file_path: Path, content: str) -> List[Dict]:
        """Detecta uso de funciones inseguras."""
        issues = []

        insecure = [
            (r'\beval\(', "Use of eval() is dangerous"),
            (r'\bexec\(', "Use of exec() is dangerous"),
            (r'\bpickle\.loads\(', "Pickle deserialization is unsafe"),
            (r'shell\s*=\s*True', "shell=True in subprocess is risky"),
        ]

        for pattern, desc in insecure:
            if re.search(pattern, content):
                issues.append({
                    "severity": "warning",
                    "message": f"{file_path.name}: {desc}"
                })

        return issues

    def _check_error_handling(self, file_path: Path, content: str) -> List[Dict]:
        """Verifica manejo de errores."""
        issues = []

        # Contar try/except
        try_count = len(re.findall(r'\btry\s*:', content))
        except_count = len(re.findall(r'\bexcept\s+', content))

        # Detectar except genéricos
        generic_except = len(re.findall(r'\bexcept\s*:', content))

        if generic_except > 0:
            issues.append({
                "severity": "info",
                "message": f"{file_path.name}: Generic except clause (should catch specific exceptions)"
            })

        # Si hay funciones pero no try/except
        function_count = len(re.findall(r'\bdef\s+\w+\(', content))
        if function_count > 3 and try_count == 0:
            issues.append({
                "severity": "warning",
                "message": f"{file_path.name}: No error handling found"
            })

        return issues

    def _calculate_score(self, files: int, critical: int, issues: int, warnings: int) -> float:
        """
        Calcula score de seguridad.

        Score base: 10.0
        - Critical issue: -2.0 cada uno
        - Issue: -0.5 cada uno
        - Warning: -0.2 cada uno
        """
        score = 10.0

        score -= critical * 2.0
        score -= issues * 0.5
        score -= warnings * 0.2

        # Bonus si no hay issues críticos
        if critical == 0 and files > 0:
            score += 0.5

        return max(0.0, min(10.0, round(score, 1)))

    def get_metrics(self) -> Dict[str, Any]:
        """Retorna métricas del agente."""
        return self.logger.get_metrics()


def main():
    """Test del Security Agent V10."""
    import argparse

    parser = argparse.ArgumentParser(description="Security Agent V10")
    parser.add_argument(
        "project_dir",
        nargs="?",
        default="workspace/test_project",
        help="Project directory to analyze"
    )

    args = parser.parse_args()

    agent = SecurityAgentV10()

    print(f"\n[ANALYZING] {args.project_dir}\n")

    result = agent.analyze(args.project_dir)

    print(f"\n[RESULTS]")
    print(f"Score: {result.score}/10.0")
    print(f"Passed: {'YES' if result.passed else 'NO'}")
    print(f"\nCritical Issues: {len(result.critical_issues)}")
    for issue in result.critical_issues:
        print(f"  [CRITICAL] {issue}")

    print(f"\nIssues: {len(result.issues)}")
    for issue in result.issues[:5]:  # Mostrar solo primeros 5
        print(f"  [ISSUE] {issue}")

    print(f"\nWarnings: {len(result.warnings)}")
    for warning in result.warnings[:5]:
        print(f"  [WARN] {warning}")

    agent.logger.print_summary()

    sys.exit(0 if result.passed else 1)


if __name__ == "__main__":
    main()
