"""CLI entry point for running the V10 orchestrator."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import List, Optional

from V10.core.orchestrator_v10_async import OrchestratorSettings, OrchestratorV10Async
from V10.utils import get_runtime_root


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the autonomous V10 orchestrator")
    parser.add_argument("objective", help="Project objective to be analysed")
    parser.add_argument("--project-name", help="Optional project name")
    parser.add_argument(
        "--workspace",
        help="Workspace directory where generated projects will live",
        default=None,
    )
    parser.add_argument(
        "--pm-timeout",
        type=int,
        default=60,
        help="Timeout in seconds for PM responses",
    )
    parser.add_argument(
        "--no-worker",
        action="store_true",
        help="Disable the embedded PM worker (useful for debugging)",
    )
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.workspace:
        workspace = Path(args.workspace).expanduser().resolve()
    else:
        workspace = get_runtime_root() / "workspace"
    workspace.mkdir(parents=True, exist_ok=True)

    settings = OrchestratorSettings(
        workspace_dir=workspace,
        use_pm_worker=not args.no_worker,
        pm_timeout=args.pm_timeout,
    )
    orchestrator = OrchestratorV10Async(settings=settings)
    result = orchestrator.execute(args.objective, project_name=args.project_name)
    print(json.dumps(result, indent=2))
    return 0 if result.get("status") == "SUCCESS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
