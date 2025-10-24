"""Runtime path helpers used by the orchestrator and agents."""

from __future__ import annotations

from pathlib import Path
from typing import Optional


def get_project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def get_runtime_root() -> Path:
    root = get_project_root() / "runtime"
    root.mkdir(parents=True, exist_ok=True)
    return root


def get_agent_runtime_dir(agent_name: str) -> Path:
    base = get_runtime_root() / "agents" / agent_name
    base.mkdir(parents=True, exist_ok=True)
    for sub in ("inbox", "outbox"):
        (base / sub).mkdir(exist_ok=True)
    return base


def ensure_directory(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path
