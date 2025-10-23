#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
QA Agent V8 - Independent Process
==================================

QA validator adaptado a arquitectura V8:
- Lee implementations de .shared/dev/
- Valida calidad de código
- Escribe reports a .shared/validation/
- Filesystem-based communication

Author: Discovery Motor Team
Version: 8.0.0
"""

import sys
import time
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List

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
    print(f"[{timestamp}] [QA Agent] [{level}] {message}")


class QAAgentV8:
    """QA Agent V8 - Code quality validation."""

    def __init__(self):
        self.last_processed_impl = None
        VALIDATION_DIR.mkdir(parents=True, exist_ok=True)

    def run(self):
        """Main loop."""
        log("QA Agent V8 started")
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

                        # Run QA validation
                        report = self.validate_quality(output_dir, iteration)

                        # Write report
                        report_file = VALIDATION_DIR / f"qa_report_{iteration:03d}.json"

                        report_file.write_text(
                            json.dumps(report, indent=2),
                            encoding='utf-8'
                        )

                        log(f"QA report written: score={report['qa_score']:.1f}")

                        self.last_processed_impl = latest_impl

                time.sleep(POLL_INTERVAL)

            except KeyboardInterrupt:
                log("Shutting down...", "WARN")
                break
            except Exception as e:
                log(f"Error: {e}", "ERROR")
                time.sleep(POLL_INTERVAL)

    def validate_quality(self, output_dir: str, iteration: int) -> Dict:
        """Run QA checks."""
        project_path = Path(output_dir)

        if not project_path.exists():
            log(f"Project directory not found: {output_dir}", "ERROR")
            return self._empty_report(iteration)

        issues = self.run_qa_checks(project_path)
        qa_score = self.calculate_score(issues)

        critical_count = len(issues.get("critical", []))

        log(f"QA check complete: {critical_count} critical issues")

        return {
            "type": "QA_REPORT",
            "role": "qa",
            "iteration": iteration,
            "timestamp": datetime.now().isoformat(),
            "qa_score": qa_score,
            "issues": issues,
            "critical_issues": issues.get("critical", []),
            "high_priority": issues.get("high", []),
            "recommendations": self.generate_recommendations(issues)
        }

    def run_qa_checks(self, project_path: Path) -> Dict[str, List[str]]:
        """Execute QA checks."""
        issues = {"critical": [], "high": [], "medium": []}

        # 1. Test coverage
        test_files = list(project_path.rglob("test_*.py"))
        src_files = [f for f in project_path.rglob("*.py") if "test" not in str(f)]

        if not test_files:
            issues["critical"].append("No test files found")
        elif len(test_files) < len(src_files) * 0.5:
            issues["high"].append(f"Low test coverage: {len(test_files)} tests for {len(src_files)} modules")

        # 2. Type hints
        if not self._check_type_hints(project_path):
            issues["high"].append("Missing type hints in code")

        # 3. Docstrings
        if not self._check_docstrings(project_path):
            issues["medium"].append("Insufficient docstrings")

        # 4. Error handling
        if not self._check_error_handling(project_path):
            issues["high"].append("Inadequate error handling")

        # 5. Logging
        if not self._check_logging(project_path):
            issues["medium"].append("Missing logging configuration")

        # 6. Dependencies
        if not (project_path / "requirements.txt").exists():
            issues["critical"].append("Missing requirements.txt")

        # 7. README
        if not (project_path / "README.md").exists():
            issues["medium"].append("Missing README.md")

        return issues

    def _check_type_hints(self, path: Path) -> bool:
        """Check for type hints."""
        patterns = [": str", ": int", ": Dict", ": List", "-> "]
        return self._search_patterns(path, patterns)

    def _check_docstrings(self, path: Path) -> bool:
        """Check for docstrings."""
        patterns = ['"""', "'''"]
        return self._search_patterns(path, patterns, min_matches=3)

    def _check_error_handling(self, path: Path) -> bool:
        """Check error handling."""
        patterns = ["try:", "except", "raise"]
        return self._search_patterns(path, patterns, min_matches=2)

    def _check_logging(self, path: Path) -> bool:
        """Check logging."""
        patterns = ["import logging", "logger =", "log("]
        return self._search_patterns(path, patterns)

    def _search_patterns(self, path: Path, patterns: List[str], min_matches: int = 1) -> bool:
        """Search for patterns."""
        matches = 0
        for py_file in path.rglob("*.py"):
            if "test" in str(py_file):
                continue
            try:
                content = py_file.read_text(encoding='utf-8', errors='ignore')
                if any(p in content for p in patterns):
                    matches += 1
                    if matches >= min_matches:
                        return True
            except:
                pass
        return False

    def calculate_score(self, issues: Dict[str, List]) -> float:
        """Calculate QA score 0-10."""
        score = 10.0
        score -= len(issues.get("critical", [])) * 2.0
        score -= len(issues.get("high", [])) * 0.5
        score -= len(issues.get("medium", [])) * 0.2
        return max(0.0, score)

    def generate_recommendations(self, issues: Dict[str, List]) -> List[str]:
        """Generate recommendations."""
        recs = []
        all_issues = issues.get("critical", []) + issues.get("high", [])

        for issue in all_issues[:10]:
            if "test" in issue.lower():
                recs.append("Add unit tests with pytest")
            elif "type hints" in issue.lower():
                recs.append("Add type hints to all functions")
            elif "error handling" in issue.lower():
                recs.append("Add try/except blocks for error handling")
            elif "requirements" in issue.lower():
                recs.append("Create requirements.txt file")
            else:
                recs.append(f"Fix: {issue}")

        return recs

    def _empty_report(self, iteration: int) -> Dict:
        """Empty report for errors."""
        return {
            "type": "QA_REPORT",
            "role": "qa",
            "iteration": iteration,
            "timestamp": datetime.now().isoformat(),
            "qa_score": 0.0,
            "issues": {"critical": ["Project directory not found"], "high": [], "medium": []},
            "critical_issues": ["Project directory not found"],
            "high_priority": [],
            "recommendations": []
        }


def main():
    agent = QAAgentV8()
    agent.run()


if __name__ == "__main__":
    main()
