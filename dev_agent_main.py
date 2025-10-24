"""Standalone entry point for running the Dev agent in its own terminal."""

from __future__ import annotations

import argparse
import signal
import sys
from typing import Optional

from V10.agents.dev_agent_v10 import DevAgentV10
from V10.core.message_bus import FileMessageBus
from V10.core import message_types
from V10.protocols import Architecture
from V10.utils import create_logger


def _build_response(status: str, *, implementation: Optional[dict] = None, error: Optional[str] = None) -> dict:
    payload = {
        "type": message_types.IMPLEMENTATION_RESPONSE,
        "status": status,
    }
    if implementation is not None:
        payload["implementation"] = implementation
    if error is not None:
        payload["error"] = error
    return payload


def run_agent(poll_interval: float = 0.5, workspace: Optional[str] = None) -> None:
    bus = FileMessageBus()
    agent = DevAgentV10(workspace_dir=workspace or str(agent_default_workspace()))
    logger = create_logger("DEV_MAIN")
    logger.info("Dev agent main loop started")

    running = True

    def _handle_shutdown(signum, frame):  # pragma: no cover - signal handler
        nonlocal running
        logger.warning("Received shutdown signal", {"signal": signum})
        running = False

    for sig in (signal.SIGINT, signal.SIGTERM):
        signal.signal(sig, _handle_shutdown)

    while running:
        message = bus.receive("dev", timeout=poll_interval, poll_interval=poll_interval)
        if message is None:
            continue

        payload = message.payload or {}
        msg_type = payload.get("type")
        if msg_type == message_types.SHUTDOWN:
            logger.info("Shutdown command received")
            running = False
            bus.send(
                sender="dev",
                recipient=message.sender,
                payload={"type": message_types.IMPLEMENTATION_RESPONSE, "status": "SHUTDOWN_ACK"},
                conversation_id=message.conversation_id,
                in_reply_to=message.message_id,
            )
            continue

        if msg_type != message_types.REQUEST_IMPLEMENTATION:
            logger.error("Unsupported message type", {"type": msg_type})
            bus.send(
                sender="dev",
                recipient=message.sender,
                payload=_build_response("ERROR", error=f"Unsupported message type: {msg_type}"),
                conversation_id=message.conversation_id,
                in_reply_to=message.message_id,
            )
            continue

        arch_data = payload.get("architecture")
        project_name = payload.get("project_name")
        if not arch_data:
            bus.send(
                sender="dev",
                recipient=message.sender,
                payload=_build_response("ERROR", error="Missing architecture data"),
                conversation_id=message.conversation_id,
                in_reply_to=message.message_id,
            )
            continue

        architecture = Architecture(
            proposed_modules=arch_data.get("proposed_modules", []),
            database_schema=arch_data.get("database_schema", {}),
            technologies=arch_data.get("technologies", {}),
            analysis=arch_data.get("analysis", ""),
            reasoning=arch_data.get("reasoning", ""),
        )

        implementation = agent.generate_project(architecture, project_name=project_name)
        if implementation is None:
            response_payload = _build_response("ERROR", error="Failed to generate project")
        else:
            response_payload = _build_response("SUCCESS", implementation=implementation.to_dict())

        bus.send(
            sender="dev",
            recipient=message.sender,
            payload=response_payload,
            conversation_id=message.conversation_id,
            in_reply_to=message.message_id,
        )

    logger.info("Dev agent main loop stopped")


def agent_default_workspace():
    from V10.utils import get_runtime_root

    runtime_root = get_runtime_root()
    workspace = runtime_root / "workspace"
    workspace.mkdir(parents=True, exist_ok=True)
    return workspace


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the Dev agent in standalone mode")
    parser.add_argument("--poll-interval", type=float, default=0.5, help="Polling interval for the inbox in seconds")
    parser.add_argument("--workspace", help="Optional workspace directory")
    args = parser.parse_args()

    try:
        run_agent(poll_interval=args.poll_interval, workspace=args.workspace)
    except KeyboardInterrupt:  # pragma: no cover - interactive use
        print("\nDev agent interrupted", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
