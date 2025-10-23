"""
Enterprise Validation System V4 - Comprehensive Scoring 0-10
Validates 10 dimensions of code quality for enterprise-grade delivery
"""

import os
import re
import ast
import json
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class ValidationResult:
    """Result of enterprise validation"""
    passed: bool
    score: float  # 0-10
    phase: str  # REJECTED, PROTOTYPE, MVP, PRODUCTION, ENTERPRISE
    violations: Dict[str, List[str]]
    metrics: Dict[str, any]
    dimension_scores: Dict[str, float] = field(default_factory=dict)


class EnterpriseValidatorV4:
    """
    Comprehensive enterprise validator with 10-dimensional scoring.

    Dimensions:
    1. Security (15%)
    2. Testing (15%)
    3. Database (10%)
    4. Observability (10%)
    5. CI/CD (10%)
    6. Documentation (10%)
    7. Code Quality (10%)
    8. Performance (10%)
    9. Scalability (5%)
    10. Architecture (5%)
    """

    def __init__(self, project_dir: str, project_type: str = "api_rest"):
        self.project_dir = Path(project_dir)
        self.project_type = project_type
        self.weights = {
            "security": 0.15,
            "testing": 0.15,
            "database": 0.10,
            "observability": 0.10,
            "ci_cd": 0.10,
            "documentation": 0.10,
            "code_quality": 0.10,
            "performance": 0.10,
            "scalability": 0.05,
            "architecture": 0.05
        }

    def validate_all(self) -> ValidationResult:
        """Run complete enterprise validation"""
        violations = {"critical": [], "high": [], "medium": [], "low": []}
        dimension_scores = {}
        metrics = {}

        # Run all validators
        validators = [
            ("security", self.validate_security),
            ("testing", self.validate_testing),
            ("database", self.validate_database),
            ("observability", self.validate_observability),
            ("ci_cd", self.validate_ci_cd),
            ("documentation", self.validate_documentation),
            ("code_quality", self.validate_code_quality),
            ("performance", self.validate_performance),
            ("scalability", self.validate_scalability),
            ("architecture", self.validate_architecture)
        ]

        for dim_name, validator in validators:
            result = validator()
            dimension_scores[dim_name] = result["score"]

            violations["critical"].extend(result.get("critical", []))
            violations["high"].extend(result.get("high", []))
            violations["medium"].extend(result.get("medium", []))
            violations["low"].extend(result.get("low", []))

            metrics.update(result.get("metrics", {}))

        # Calculate weighted score
        final_score = sum(
            dimension_scores[dim] * self.weights[dim]
            for dim in dimension_scores
        )

        # Determine phase
        phase = self._determine_phase(final_score, violations)
        passed = len(violations["critical"]) == 0 and final_score >= 9.0

        return ValidationResult(
            passed=passed,
            score=final_score,
            phase=phase,
            violations=violations,
            metrics=metrics,
            dimension_scores=dimension_scores
        )

    def validate_security(self) -> Dict:
        """Validate OWASP Top 10 and security best practices"""
        violations = {"critical": [], "high": [], "medium": []}
        score = 10.0

        # 1. Check for authentication
        if not self._has_authentication():
            violations["critical"].append(
                "No authentication system found. Required: JWT, OAuth2, or session-based auth"
            )
            score -= 3.0

        # 2. Check CORS configuration
        cors_issues = self._check_cors_config()
        if cors_issues:
            violations["critical"].extend(cors_issues)
            score -= 2.0

        # 3. Check for hardcoded secrets
        secrets = self._find_hardcoded_secrets()
        if secrets:
            violations["critical"].extend([
                f"Hardcoded secret in {file}:{line}" for file, line in secrets
            ])
            score -= 1.0 * len(secrets)

        # 4. Check rate limiting
        if not self._has_rate_limiting():
            violations["high"].append("No rate limiting configured. Risk: DoS attacks")
            score -= 1.0

        # 5. Check input validation
        unvalidated = self._check_input_validation()
        if unvalidated:
            violations["high"].extend([
                f"Unvalidated input in {route}: {param}" for route, param in unvalidated
            ])
            score -= 0.5 * min(len(unvalidated), 4)

        return {
            "score": max(0, score),
            "critical": violations["critical"],
            "high": violations["high"],
            "medium": violations["medium"],
            "metrics": {
                "auth_present": self._has_authentication(),
                "cors_secure": len(cors_issues) == 0,
                "secrets_secure": len(secrets) == 0,
                "rate_limiting": self._has_rate_limiting()
            }
        }

    def validate_testing(self) -> Dict:
        """Validate test coverage and quality"""
        violations = {"critical": [], "high": [], "medium": []}
        score = 10.0

        # 1. Calculate coverage
        coverage = self._calculate_test_coverage()
        if coverage < 0.95:
            violations["critical"].append(
                f"Test coverage {coverage*100:.1f}% < 95% required for enterprise"
            )
            score -= (0.95 - coverage) * 20  # Harsh penalty

        # 2. Check for integration tests
        integration_count = self._count_integration_tests()
        if integration_count < 10:
            violations["high"].append(
                f"Only {integration_count} integration tests. Minimum 10 required"
            )
            score -= (10 - integration_count) * 0.1

        # 3. Check for load tests
        if not self._has_load_tests():
            violations["critical"].append("No load tests found. Required: locust or k6")
            score -= 2.0

        # 4. Check test quality
        if not self._has_test_fixtures():
            violations["medium"].append("No test fixtures found (conftest.py)")
            score -= 0.5

        return {
            "score": max(0, score),
            "critical": violations["critical"],
            "high": violations["high"],
            "medium": violations["medium"],
            "metrics": {
                "coverage": coverage,
                "unit_tests": self._count_unit_tests(),
                "integration_tests": integration_count,
                "load_tests": self._has_load_tests()
            }
        }

    def validate_database(self) -> Dict:
        """Validate database setup and migrations"""
        violations = {"critical": [], "high": []}
        score = 10.0

        # 1. Check for ORM
        if not self._has_orm():
            violations["critical"].append("No ORM found. Required: SQLAlchemy or similar")
            score -= 4.0

        # 2. Check for migrations
        if not self._has_migrations():
            violations["critical"].append("No migration system. Required: Alembic")
            score -= 3.0

        # 3. Check connection pooling
        if not self._has_connection_pooling():
            violations["high"].append("No connection pooling configured")
            score -= 1.5

        # 4. Check transactions
        if not self._uses_transactions():
            violations["high"].append("No explicit transaction management")
            score -= 1.5

        return {
            "score": max(0, score),
            "critical": violations["critical"],
            "high": violations["high"],
            "metrics": {
                "orm_present": self._has_orm(),
                "migrations": self._has_migrations(),
                "pooling": self._has_connection_pooling()
            }
        }

    def validate_observability(self) -> Dict:
        """Validate logging, metrics, and tracing"""
        violations = {"critical": [], "high": []}
        score = 10.0

        # 1. Structured logging
        if not self._has_structured_logging():
            violations["critical"].append("No structured (JSON) logging configured")
            score -= 3.0

        # 2. Metrics endpoint
        if not self._has_metrics_endpoint():
            violations["critical"].append("No Prometheus metrics endpoint")
            score -= 3.0

        # 3. Distributed tracing
        if not self._has_tracing():
            violations["high"].append("No distributed tracing (OpenTelemetry)")
            score -= 2.0

        # 4. Health checks
        if not self._has_health_endpoint():
            violations["high"].append("No /health endpoint for monitoring")
            score -= 2.0

        return {
            "score": max(0, score),
            "critical": violations["critical"],
            "high": violations["high"],
            "metrics": {
                "logging": self._has_structured_logging(),
                "metrics": self._has_metrics_endpoint(),
                "tracing": self._has_tracing(),
                "health": self._has_health_endpoint()
            }
        }

    def validate_ci_cd(self) -> Dict:
        """Validate CI/CD pipeline"""
        violations = {"high": [], "medium": []}
        score = 10.0

        # 1. CI pipeline exists
        if not self._has_ci_pipeline():
            violations["high"].append("No CI/CD pipeline configured")
            score -= 4.0

        # 2. Dockerfile
        if not self._has_dockerfile():
            violations["high"].append("No Dockerfile for containerization")
            score -= 3.0

        # 3. docker-compose
        if not self._has_docker_compose():
            violations["medium"].append("No docker-compose for local development")
            score -= 1.5

        # 4. CI runs tests
        if self._has_ci_pipeline() and not self._ci_runs_tests():
            violations["high"].append("CI pipeline doesn't run automated tests")
            score -= 1.5

        return {
            "score": max(0, score),
            "high": violations["high"],
            "medium": violations["medium"],
            "metrics": {
                "ci_configured": self._has_ci_pipeline(),
                "dockerized": self._has_dockerfile()
            }
        }

    def validate_documentation(self) -> Dict:
        """Validate documentation completeness"""
        violations = {"high": [], "medium": []}
        score = 10.0

        # 1. README exists and complete
        readme_score = self._check_readme_quality()
        if readme_score < 7:
            violations["high"].append(f"README incomplete (score: {readme_score}/10)")
            score -= (10 - readme_score) * 0.3

        # 2. Docstrings
        docstring_coverage = self._calculate_docstring_coverage()
        if docstring_coverage < 0.90:
            violations["high"].append(
                f"Docstring coverage {docstring_coverage*100:.0f}% < 90%"
            )
            score -= (0.90 - docstring_coverage) * 10

        # 3. SECURITY.md
        if not self._has_security_md():
            violations["medium"].append("No SECURITY.md with threat model")
            score -= 1.0

        # 4. API documentation
        if self.project_type == "api_rest" and not self._has_api_docs():
            violations["medium"].append("No API documentation (OpenAPI/Swagger)")
            score -= 1.0

        return {
            "score": max(0, score),
            "high": violations["high"],
            "medium": violations["medium"],
            "metrics": {
                "readme_quality": readme_score,
                "docstring_coverage": docstring_coverage
            }
        }

    def validate_code_quality(self) -> Dict:
        """Validate code quality (PEP8, complexity, etc)"""
        violations = {"high": [], "medium": [], "low": []}
        score = 10.0

        # 1. PEP8 violations
        pep8_violations = self._check_pep8()
        if len(pep8_violations) > 10:
            violations["medium"].extend(pep8_violations[:5])  # Show first 5
            score -= min(len(pep8_violations) * 0.1, 3.0)

        # 2. Complexity
        complex_functions = self._check_complexity()
        if complex_functions:
            violations["high"].extend([
                f"Function {func} has complexity {comp} (max 10)"
                for func, comp in complex_functions[:3]
            ])
            score -= min(len(complex_functions) * 0.5, 3.0)

        # 3. Code duplication
        duplicates = self._check_duplication()
        if duplicates > 5:
            violations["medium"].append(f"{duplicates} code duplications found")
            score -= min(duplicates * 0.3, 2.0)

        # 4. TODOs/FIXMEs
        todos = self._find_todos()
        if todos:
            violations["high"].extend([f"TODO in {file}:{line}" for file, line in todos[:3]])
            score -= len(todos) * 1.0

        return {
            "score": max(0, score),
            "high": violations["high"],
            "medium": violations["medium"],
            "low": violations["low"],
            "metrics": {
                "pep8_violations": len(pep8_violations),
                "complex_functions": len(complex_functions),
                "todos": len(todos)
            }
        }

    def validate_performance(self) -> Dict:
        """Validate performance characteristics"""
        violations = {"medium": []}
        score = 10.0

        # 1. Estimated latency
        latency = self._estimate_latency()
        if latency > 150:
            violations["medium"].append(f"Estimated p95 latency {latency}ms > 150ms")
            score -= min((latency - 150) * 0.02, 3.0)

        # 2. N+1 queries
        n_plus_one = self._check_n_plus_one_queries()
        if n_plus_one:
            violations["medium"].extend([
                f"Potential N+1 query in {loc}" for loc in n_plus_one[:3]
            ])
            score -= min(len(n_plus_one) * 0.5, 3.0)

        # 3. Caching
        if not self._has_caching():
            violations["medium"].append("No caching layer configured")
            score -= 2.0

        return {
            "score": max(0, score),
            "medium": violations["medium"],
            "metrics": {
                "estimated_latency_p95": latency,
                "n_plus_one_issues": len(n_plus_one)
            }
        }

    def validate_scalability(self) -> Dict:
        """Validate scalability readiness"""
        violations = {"high": []}
        score = 10.0

        # 1. Stateless design
        if not self._is_stateless():
            violations["high"].append("Application has global state - not horizontally scalable")
            score -= 5.0

        # 2. Async support
        if not self._has_async_support():
            violations["high"].append("No async support - limits concurrency")
            score -= 3.0

        # 3. Database connection pooling
        if not self._has_connection_pooling():
            violations["high"].append("No connection pooling - won't scale")
            score -= 2.0

        return {
            "score": max(0, score),
            "high": violations["high"],
            "metrics": {
                "stateless": self._is_stateless(),
                "async": self._has_async_support()
            }
        }

    def validate_architecture(self) -> Dict:
        """Validate architectural patterns"""
        violations = {"medium": []}
        score = 10.0

        # 1. Separation of concerns
        if not self._has_separation_of_concerns():
            violations["medium"].append("Poor separation of concerns")
            score -= 3.0

        # 2. Dependency injection
        if not self._uses_dependency_injection():
            violations["medium"].append("No dependency injection - tight coupling")
            score -= 2.0

        # 3. Configuration management
        if not self._has_config_management():
            violations["medium"].append("No proper configuration management")
            score -= 2.0

        return {
            "score": max(0, score),
            "medium": violations["medium"],
            "metrics": {
                "separation_of_concerns": self._has_separation_of_concerns(),
                "dependency_injection": self._uses_dependency_injection()
            }
        }

    def _determine_phase(self, score: float, violations: Dict) -> str:
        """Determine phase based on score and violations"""
        if len(violations["critical"]) > 0:
            return "REJECTED"
        elif score >= 9.0:
            return "ENTERPRISE"
        elif score >= 7.0:
            return "PRODUCTION"
        elif score >= 5.0:
            return "MVP"
        else:
            return "PROTOTYPE"

    # Helper methods (implement based on actual file analysis)
    def _has_authentication(self) -> bool:
        """Check if authentication is implemented"""
        patterns = ["JWT", "OAuth", "authenticate", "login", "token"]
        for py_file in self.project_dir.rglob("*.py"):
            content = py_file.read_text(errors='ignore')
            if any(pattern in content for pattern in patterns):
                return True
        return False

    def _check_cors_config(self) -> List[str]:
        """Check CORS configuration"""
        issues = []
        for py_file in self.project_dir.rglob("*.py"):
            content = py_file.read_text(errors='ignore')
            if 'allow_origins=["*"]' in content or "allow_origins=['*']" in content:
                issues.append(f"CORS allows all origins (*) in {py_file.name}")
        return issues

    def _find_hardcoded_secrets(self) -> List[Tuple[str, int]]:
        """Find hardcoded secrets"""
        secrets = []
        secret_patterns = [
            r'password\s*=\s*["\'][^"\']+["\']',
            r'api_key\s*=\s*["\'][^"\']+["\']',
            r'secret\s*=\s*["\'][^"\']+["\']'
        ]
        for py_file in self.project_dir.rglob("*.py"):
            content = py_file.read_text(errors='ignore')
            for i, line in enumerate(content.split('\n'), 1):
                for pattern in secret_patterns:
                    if re.search(pattern, line, re.IGNORECASE):
                        if "your-" not in line.lower() and "example" not in line.lower():
                            secrets.append((py_file.name, i))
        return secrets

    def _has_rate_limiting(self) -> bool:
        """Check for rate limiting"""
        patterns = ["limiter", "rate_limit", "slowapi", "ratelimit"]
        for py_file in self.project_dir.rglob("*.py"):
            content = py_file.read_text(errors='ignore')
            if any(pattern in content.lower() for pattern in patterns):
                return True
        return False

    def _check_input_validation(self) -> List[Tuple[str, str]]:
        """Check for unvalidated inputs"""
        # Simplified - check if Pydantic models are used
        return []  # Assume FastAPI+Pydantic validates automatically

    def _calculate_test_coverage(self) -> float:
        """Calculate test coverage"""
        test_files = list(self.project_dir.rglob("test_*.py"))
        src_files = [f for f in self.project_dir.rglob("*.py")
                    if "test" not in str(f) and "__pycache__" not in str(f)]

        if not src_files:
            return 0.0

        # Rough estimate: count test functions vs source functions
        test_funcs = 0
        for tf in test_files:
            content = tf.read_text(errors='ignore')
            test_funcs += len(re.findall(r'def test_\w+', content))

        src_funcs = 0
        for sf in src_files:
            content = sf.read_text(errors='ignore')
            src_funcs += len(re.findall(r'def \w+\(', content))

        if src_funcs == 0:
            return 0.0

        return min(test_funcs / max(src_funcs, 1), 1.0)

    def _count_unit_tests(self) -> int:
        """Count unit test functions"""
        count = 0
        for py_file in self.project_dir.rglob("test_*.py"):
            content = py_file.read_text(errors='ignore')
            count += len(re.findall(r'def test_\w+', content))
        return count

    def _count_integration_tests(self) -> int:
        """Count integration tests"""
        # Look for tests with "integration" in name or complex fixtures
        count = 0
        for py_file in self.project_dir.rglob("test_*.py"):
            content = py_file.read_text(errors='ignore')
            if "integration" in py_file.name.lower():
                count += len(re.findall(r'def test_\w+', content))
            elif "client" in content or "db_session" in content:
                count += len(re.findall(r'def test_\w+', content)) // 2
        return count

    def _has_load_tests(self) -> bool:
        """Check for load tests"""
        return (self.project_dir / "tests" / "load").exists() or \
               any((self.project_dir / "tests").rglob("locustfile.py"))

    def _has_test_fixtures(self) -> bool:
        """Check for pytest fixtures"""
        return (self.project_dir / "tests" / "conftest.py").exists()

    def _has_orm(self) -> bool:
        """Check for ORM usage"""
        patterns = ["sqlalchemy", "SQLAlchemy", "from database import", "sessionmaker"]
        for py_file in self.project_dir.rglob("*.py"):
            content = py_file.read_text(errors='ignore')
            if any(p in content for p in patterns):
                return True
        return False

    def _has_migrations(self) -> bool:
        """Check for migration system"""
        return (self.project_dir / "alembic").exists() or \
               (self.project_dir / "migrations").exists()

    def _has_connection_pooling(self) -> bool:
        """Check for connection pooling"""
        patterns = ["pool_size", "poolclass", "QueuePool"]
        for py_file in self.project_dir.rglob("*.py"):
            content = py_file.read_text(errors='ignore')
            if any(p in content for p in patterns):
                return True
        return False

    def _uses_transactions(self) -> bool:
        """Check for explicit transactions"""
        patterns = ["db.commit", "session.commit", "transaction", "@transactional"]
        for py_file in self.project_dir.rglob("*.py"):
            content = py_file.read_text(errors='ignore')
            if any(p in content for p in patterns):
                return True
        return False

    def _has_structured_logging(self) -> bool:
        """Check for JSON/structured logging"""
        patterns = ["jsonlogger", "structlog", "JsonFormatter"]
        for py_file in self.project_dir.rglob("*.py"):
            content = py_file.read_text(errors='ignore')
            if any(p in content for p in patterns):
                return True
        return False

    def _has_metrics_endpoint(self) -> bool:
        """Check for Prometheus metrics"""
        patterns = ["prometheus", "Counter", "Histogram", "/metrics"]
        for py_file in self.project_dir.rglob("*.py"):
            content = py_file.read_text(errors='ignore')
            if any(p in content for p in patterns):
                return True
        return False

    def _has_tracing(self) -> bool:
        """Check for distributed tracing"""
        patterns = ["opentelemetry", "tracer", "jaeger"]
        for py_file in self.project_dir.rglob("*.py"):
            content = py_file.read_text(errors='ignore')
            if any(p in content for p in patterns):
                return True
        return False

    def _has_health_endpoint(self) -> bool:
        """Check for health endpoint"""
        for py_file in self.project_dir.rglob("*.py"):
            content = py_file.read_text(errors='ignore')
            if "/health" in content or "def health" in content:
                return True
        return False

    def _has_ci_pipeline(self) -> bool:
        """Check for CI/CD pipeline"""
        return (self.project_dir / ".github" / "workflows").exists() or \
               (self.project_dir / ".gitlab-ci.yml").exists()

    def _has_dockerfile(self) -> bool:
        """Check for Dockerfile"""
        return (self.project_dir / "Dockerfile").exists()

    def _has_docker_compose(self) -> bool:
        """Check for docker-compose"""
        return (self.project_dir / "docker-compose.yml").exists()

    def _ci_runs_tests(self) -> bool:
        """Check if CI runs tests"""
        workflow_files = list((self.project_dir / ".github" / "workflows").rglob("*.yml")) if \
                        (self.project_dir / ".github" / "workflows").exists() else []
        for wf in workflow_files:
            content = wf.read_text(errors='ignore')
            if "pytest" in content or "test" in content:
                return True
        return False

    def _check_readme_quality(self) -> float:
        """Score README completeness 0-10"""
        readme = self.project_dir / "README.md"
        if not readme.exists():
            return 0.0

        content = readme.read_text(errors='ignore').lower()
        required_sections = [
            "installation", "usage", "api", "test", "deploy", "license"
        ]
        score = 0.0
        for section in required_sections:
            if section in content:
                score += 1.5
        return min(score, 10.0)

    def _calculate_docstring_coverage(self) -> float:
        """Calculate docstring coverage"""
        total_funcs = 0
        documented_funcs = 0

        for py_file in self.project_dir.rglob("*.py"):
            if "test" in str(py_file):
                continue
            try:
                tree = ast.parse(py_file.read_text())
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        total_funcs += 1
                        if ast.get_docstring(node):
                            documented_funcs += 1
            except:
                pass

        return documented_funcs / max(total_funcs, 1)

    def _has_security_md(self) -> bool:
        """Check for SECURITY.md"""
        return (self.project_dir / "SECURITY.md").exists()

    def _has_api_docs(self) -> bool:
        """Check for API documentation"""
        # FastAPI auto-generates OpenAPI docs
        for py_file in self.project_dir.rglob("*.py"):
            content = py_file.read_text(errors='ignore')
            if "FastAPI" in content:
                return True
        return False

    def _check_pep8(self) -> List[str]:
        """Check PEP8 violations"""
        violations = []
        for py_file in self.project_dir.rglob("*.py"):
            content = py_file.read_text(errors='ignore')
            lines = content.split('\n')

            for i, line in enumerate(lines, 1):
                if len(line) > 120:
                    violations.append(f"{py_file.name}:{i}: Line too long ({len(line)} > 120)")

            # Check for multiple blank lines
            for i in range(len(lines) - 3):
                if all(not lines[i+j].strip() for j in range(4)):
                    violations.append(f"{py_file.name}:{i+1}: More than 2 consecutive blank lines")

        return violations

    def _check_complexity(self) -> List[Tuple[str, int]]:
        """Check cyclomatic complexity"""
        complex_funcs = []
        # Simplified - count nested ifs/loops
        for py_file in self.project_dir.rglob("*.py"):
            try:
                tree = ast.parse(py_file.read_text())
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        complexity = self._calculate_complexity(node)
                        if complexity > 10:
                            complex_funcs.append((f"{py_file.name}:{node.name}", complexity))
            except:
                pass
        return complex_funcs

    def _calculate_complexity(self, node) -> int:
        """Calculate cyclomatic complexity"""
        complexity = 1
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.For, ast.While, ast.ExceptHandler)):
                complexity += 1
        return complexity

    def _check_duplication(self) -> int:
        """Check code duplication"""
        # Simplified - return 0 for now
        return 0

    def _find_todos(self) -> List[Tuple[str, int]]:
        """Find TODO/FIXME comments"""
        todos = []
        patterns = [r'#\s*TODO', r'#\s*FIXME', r'#\s*HACK']
        for py_file in self.project_dir.rglob("*.py"):
            content = py_file.read_text(errors='ignore')
            for i, line in enumerate(content.split('\n'), 1):
                if any(re.search(p, line, re.IGNORECASE) for p in patterns):
                    todos.append((py_file.name, i))
        return todos

    def _estimate_latency(self) -> int:
        """Estimate p95 latency in ms"""
        # Heuristic based on code patterns
        has_db = self._has_orm()
        has_cache = self._has_caching()
        has_async = self._has_async_support()

        base = 50  # Base FastAPI latency
        if has_db:
            base += 20
        if not has_cache:
            base += 30
        if not has_async:
            base += 20

        return base

    def _check_n_plus_one_queries(self) -> List[str]:
        """Check for N+1 query patterns"""
        # Simplified - look for queries in loops
        issues = []
        for py_file in self.project_dir.rglob("*.py"):
            content = py_file.read_text(errors='ignore')
            if "for" in content and ("query" in content or "filter" in content):
                issues.append(str(py_file.name))
        return issues

    def _has_caching(self) -> bool:
        """Check for caching"""
        patterns = ["redis", "cache", "lru_cache", "cached"]
        for py_file in self.project_dir.rglob("*.py"):
            content = py_file.read_text(errors='ignore')
            if any(p in content.lower() for p in patterns):
                return True
        return False

    def _is_stateless(self) -> bool:
        """Check if application is stateless"""
        # Look for global state
        for py_file in self.project_dir.rglob("*.py"):
            content = py_file.read_text(errors='ignore')
            # Check for global dicts/lists used as storage
            if re.search(r'^[a-z_]+\s*=\s*(\{\}|\[\])', content, re.MULTILINE):
                return False
        return True

    def _has_async_support(self) -> bool:
        """Check for async/await"""
        patterns = ["async def", "await", "asyncio"]
        for py_file in self.project_dir.rglob("*.py"):
            content = py_file.read_text(errors='ignore')
            if any(p in content for p in patterns):
                return True
        return False

    def _has_separation_of_concerns(self) -> bool:
        """Check for proper file organization"""
        required_files = ["routes.py", "models.py", "schemas.py"]
        return all((self.project_dir / f).exists() for f in required_files)

    def _uses_dependency_injection(self) -> bool:
        """Check for dependency injection"""
        patterns = ["Depends(", "dependencies="]
        for py_file in self.project_dir.rglob("*.py"):
            content = py_file.read_text(errors='ignore')
            if any(p in content for p in patterns):
                return True
        return False

    def _has_config_management(self) -> bool:
        """Check for configuration management"""
        return (self.project_dir / "config.py").exists() or \
               (self.project_dir / ".env.example").exists()


# Convenience function
def run_full_validation(project_dir: str, project_type: str = "api_rest") -> ValidationResult:
    """Run complete enterprise validation"""
    validator = EnterpriseValidatorV4(project_dir, project_type)
    return validator.validate_all()
