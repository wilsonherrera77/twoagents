#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Security Agent V8 - Independent Process
========================================

Security validator adaptado a arquitectura V8:
- Lee implementations de .shared/dev/
- Valida OWASP Top 10
- Escribe reports a .shared/validation/
- Filesystem-based communication

Author: Discovery Motor Team
Version: 8.0.0
"""

import sys
import time
import json
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from protocols.message_types import write_message, read_message

# Configuration
PROJECT_ROOT = Path(__file__).parent.parent
SHARED_DIR = PROJECT_ROOT / ".shared"
DEV_DIR = SHARED_DIR / "dev"
VALIDATION_DIR = SHARED_DIR / "validation"

POLL_INTERVAL = 5

def log(message: str, level: str = "INFO"):
    """Log con timestamp."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] [Security Agent] [{level}] {message}")


class SecurityAgentV8:
    """Security Agent V8 - OWASP validation."""

    def __init__(self):
        self.last_processed_impl = None
        VALIDATION_DIR.mkdir(parents=True, exist_ok=True)

    def run(self):
        """Main loop."""
        log("Security Agent V8 started")
        log(f"Watching: {DEV_DIR}")
        log(f"Output to: {VALIDATION_DIR}")

        while True:
            try:
                # Look for latest implementation
                impl_files = sorted(DEV_DIR.glob("implementation_*.json"))

                if impl_files:
                    latest_impl = impl_files[-1]

                    # Skip if already processed
                    if latest_impl == self.last_processed_impl:
                        time.sleep(POLL_INTERVAL)
                        continue

                    impl_data = read_message(latest_impl)

                    if impl_data:
                        output_dir = impl_data.get("output_dir", "")
                        iteration = impl_data.get("iteration", 1)

                        log(f"New implementation detected: {output_dir}")

                        # Run security validation
                        report = self.validate_security(output_dir, iteration)

                        # Write report
                        report_file = VALIDATION_DIR / f"security_report_{iteration:03d}.json"

                        report_file.write_text(
                            json.dumps(report, indent=2),
                            encoding='utf-8'
                        )

                        log(f"Security report written: score={report['security_score']:.1f}")

                        self.last_processed_impl = latest_impl

                time.sleep(POLL_INTERVAL)

            except KeyboardInterrupt:
                log("Shutting down...", "WARN")
                break
            except Exception as e:
                log(f"Error: {e}", "ERROR")
                time.sleep(POLL_INTERVAL)

    def validate_security(self, output_dir: str, iteration: int) -> Dict:
        """Run OWASP security checks."""
        project_path = Path(output_dir)

        if not project_path.exists():
            log(f"Project directory not found: {output_dir}", "ERROR")
            return self._empty_report(iteration)

        violations = self.run_security_checks(project_path)
        security_score = self.calculate_score(violations)

        critical_count = len(violations.get("critical", []))

        log(f"Security check complete: {critical_count} critical issues")

        return {
            "type": "SECURITY_REPORT",
            "role": "security",
            "iteration": iteration,
            "timestamp": datetime.now().isoformat(),
            "security_score": security_score,
            "violations": violations,
            "critical_issues": violations.get("critical", []),
            "high_priority": violations.get("high", []),
            "recommendations": self.generate_recommendations(violations)
        }

    def run_security_checks(self, project_path: Path) -> Dict[str, List[str]]:
        """Execute OWASP Top 10 checks."""
        violations = {"critical": [], "high": [], "medium": []}

        # 1. Authentication
        if not self._check_authentication(project_path):
            violations["critical"].append(
                "Missing authentication system (JWT/OAuth2 required)"
            )

        # 2. CORS
        cors_issues = self._check_cors(project_path)
        violations["critical"].extend(cors_issues)

        # 3. Hardcoded secrets
        secrets = self._find_hardcoded_secrets(project_path)
        if secrets:
            violations["critical"].extend([
                f"Hardcoded secret in {file}:{line}" for file, line in secrets[:5]
            ])

        # 4. Rate limiting
        if not self._check_rate_limiting(project_path):
            violations["high"].append(
                "No rate limiting configured (DoS risk)"
            )

        # 5. Input validation
        if not self._check_input_validation(project_path):
            violations["high"].append(
                "Input validation incomplete (injection risk)"
            )

        # 6. Password hashing
        if not self._check_password_hashing(project_path):
            violations["critical"].append(
                "Insecure password hashing (use bcrypt/argon2)"
            )

        return violations

    def _check_authentication(self, path: Path) -> bool:
        """Check auth implementation."""
        patterns = ["JWT", "OAuth", "authenticate", "login", "token"]
        return self._search_patterns(path, patterns)

    def _check_cors(self, path: Path) -> List[str]:
        """Check CORS config."""
        issues = []
        for py_file in path.rglob("*.py"):
            try:
                content = py_file.read_text(encoding='utf-8', errors='ignore')
                if ('allow_origins=["*"]' in content or
                    "allow_origins=['*']" in content):
                    issues.append(
                        f"CORS allows all origins in {py_file.name}"
                    )
            except:
                pass
        return issues

    def _find_hardcoded_secrets(self, path: Path) -> List[Tuple[str, int]]:
        """Find hardcoded secrets."""
        secrets = []
        patterns = [
            (r'password\s*=\s*["\'][^"\']{8,}["\']', "password"),
            (r'api_key\s*=\s*["\'][^"\']{20,}["\']', "api_key"),
            (r'secret\s*=\s*["\'][^"\']{20,}["\']', "secret"),
        ]

        for py_file in path.rglob("*.py"):
            if "test" in str(py_file):
                continue
            try:
                content = py_file.read_text(encoding='utf-8', errors='ignore')
                lines = content.split('\n')

                for i, line in enumerate(lines, 1):
                    for pattern, _ in patterns:
                        if re.search(pattern, line, re.IGNORECASE):
                            if any(w in line.lower() for w in ["example", "test", "fake", "your-"]):
                                continue
                            secrets.append((py_file.name, i))
                            break
            except:
                pass

        return secrets

    def _check_rate_limiting(self, path: Path) -> bool:
        """Check rate limiting."""
        patterns = ["limiter", "rate_limit", "@limiter.limit"]
        return self._search_patterns(path, patterns)

    def _check_input_validation(self, path: Path) -> bool:
        """Check input validation."""
        patterns = ["BaseModel", "Field(", "validator"]
        return self._search_patterns(path, patterns)

    def _check_password_hashing(self, path: Path) -> bool:
        """Check password hashing."""
        patterns = ["bcrypt", "argon2", "CryptContext", "pwd_context"]
        return self._search_patterns(path, patterns)

    def _search_patterns(self, path: Path, patterns: List[str]) -> bool:
        """Search for patterns in Python files."""
        for py_file in path.rglob("*.py"):
            if "test" in str(py_file):
                continue
            try:
                content = py_file.read_text(encoding='utf-8', errors='ignore')
                if any(p in content for p in patterns):
                    return True
            except:
                pass
        return False

    def calculate_score(self, violations: Dict[str, List]) -> float:
        """Calculate security score 0-10."""
        score = 10.0
        score -= len(violations.get("critical", [])) * 2.0
        score -= len(violations.get("high", [])) * 0.5
        score -= len(violations.get("medium", [])) * 0.2
        return max(0.0, score)

    def generate_recommendations(self, violations: Dict[str, List]) -> List[str]:
        """Generate recommendations."""
        recs = []
        all_issues = violations.get("critical", []) + violations.get("high", [])

        for issue in all_issues[:10]:
            if "authentication" in issue.lower():
                recs.append("Implement JWT authentication")
            elif "cors" in issue.lower():
                recs.append("Restrict CORS to known domains")
            elif "rate limiting" in issue.lower():
                recs.append("Add rate limiting middleware")
            elif "password" in issue.lower():
                recs.append("Use bcrypt for password hashing")
            elif "secret" in issue.lower():
                recs.append("Move secrets to environment variables")
            else:
                recs.append(f"Fix: {issue}")

        return recs

    def _empty_report(self, iteration: int) -> Dict:
        """Empty report for errors."""
        return {
            "type": "SECURITY_REPORT",
            "role": "security",
            "iteration": iteration,
            "timestamp": datetime.now().isoformat(),
            "security_score": 0.0,
            "violations": {"critical": ["Project directory not found"], "high": [], "medium": []},
            "critical_issues": ["Project directory not found"],
            "high_priority": [],
            "recommendations": []
        }


def main():
    agent = SecurityAgentV8()
    agent.run()


if __name__ == "__main__":
    main()
