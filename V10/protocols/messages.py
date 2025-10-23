#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Message Protocols V10 - Estructuras de mensajes simplificadas
============================================================

Mensajes para comunicación entre componentes V10.
Versión simplificada sin File Communicator.
"""

from dataclasses import dataclass, asdict, field
from typing import Dict, List, Optional, Any
from datetime import datetime


@dataclass
class Architecture:
    """Arquitectura propuesta por PM."""
    proposed_modules: List[str]
    database_schema: Dict[str, Any]
    technologies: Dict[str, str]
    analysis: str
    reasoning: str

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class Implementation:
    """Implementación generada por Dev."""
    project_dir: str
    files_created: List[str]
    files_count: int
    technologies: Dict[str, str]
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class ValidationResult:
    """Resultado de validación (Security o QA)."""
    agent_type: str  # "security" o "qa"
    score: float
    issues: List[str]
    critical_issues: List[str]
    warnings: List[str]
    passed: bool
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class ProjectResult:
    """Resultado final del proyecto."""
    success: bool
    project_dir: str
    architecture: Architecture
    implementation: Implementation
    security_result: ValidationResult
    qa_result: ValidationResult
    total_duration: float
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict:
        return {
            "success": self.success,
            "project_dir": self.project_dir,
            "architecture": self.architecture.to_dict(),
            "implementation": self.implementation.to_dict(),
            "security_result": self.security_result.to_dict(),
            "qa_result": self.qa_result.to_dict(),
            "total_duration": self.total_duration,
            "timestamp": self.timestamp
        }
