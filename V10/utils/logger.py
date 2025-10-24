"""Structured logging utilities used across the V10 platform."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional


@dataclass
class StructuredLogger:
    """Small structured logger with console and file support."""

    name: str
    base_dir: Optional[Path] = None
    level: str = "INFO"
    _state: Optional[str] = field(default=None, init=False)
    _task: Optional[str] = field(default=None, init=False)

    def __post_init__(self) -> None:
        if self.base_dir:
            self.base_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Public helpers
    # ------------------------------------------------------------------
    def set_state(self, state: str) -> None:
        self._state = state
        self.debug(f"state changed to {state}")

    def set_task(self, task: str) -> None:
        self._task = task
        self.debug(f"task set to {task}")

    def measure_time(self, label: str, start_time: datetime) -> float:
        duration = (datetime.now() - start_time).total_seconds()
        self.debug(f"{label} finished in {duration:.2f}s")
        return duration

    # ------------------------------------------------------------------
    # Logging API
    # ------------------------------------------------------------------
    def info(self, message: str, context: Optional[Dict[str, Any]] = None) -> None:
        self._log("INFO", message, context)

    def success(self, message: str, context: Optional[Dict[str, Any]] = None) -> None:
        self._log("SUCCESS", message, context)

    def warn(self, message: str, context: Optional[Dict[str, Any]] = None) -> None:
        self._log("WARN", message, context)

    def error(self, message: str, context: Optional[Dict[str, Any]] = None) -> None:
        self._log("ERROR", message, context)

    def debug(self, message: str, context: Optional[Dict[str, Any]] = None) -> None:
        if self.level == "DEBUG":
            self._log("DEBUG", message, context)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _log(self, level: str, message: str, context: Optional[Dict[str, Any]]) -> None:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        payload: Dict[str, Any] = {
            "time": timestamp,
            "level": level,
            "name": self.name,
            "message": message,
        }

        if self._state:
            payload["state"] = self._state
        if self._task:
            payload["task"] = self._task
        if context:
            payload["context"] = context

        text = self._format(payload)
        try:
            print(text)
        except UnicodeEncodeError:
            safe = text.encode("ascii", errors="ignore").decode("ascii")
            print(safe)

        if self.base_dir:
            log_file = self.base_dir / f"{datetime.now():%Y%m%d}.log"
            with log_file.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(payload, ensure_ascii=False) + "\n")

    @staticmethod
    def _format(payload: Dict[str, Any]) -> str:
        base = f"[{payload['time']}] [{payload['level']:^7}] {payload['name']}: {payload['message']}"
        extras = []
        if "state" in payload:
            extras.append(f"state={payload['state']}")
        if "task" in payload:
            extras.append(f"task={payload['task']}")
        if "context" in payload:
            extras.append(json.dumps(payload["context"], ensure_ascii=False))
        if extras:
            base = f"{base} :: {' | '.join(extras)}"
        return base


def create_logger(name: str, logs_dir: Optional[Path] = None) -> StructuredLogger:
    """Factory helper used across the project."""

    base_dir = logs_dir
    if logs_dir is None:
        root = Path(__file__).resolve().parents[1]
        base_dir = root / "runtime" / "logs" / name.lower()
    return StructuredLogger(name=name, base_dir=base_dir)
