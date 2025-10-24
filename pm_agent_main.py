"""Standalone entry point for running the PM agent in its own terminal."""

from __future__ import annotations

import argparse
import signal
import sys
from typing import Optional

from V10.agents.pm_agent_v10 import PMAgentV10
from V10.core.message_bus import FileMessageBus
from V10.core import message_types
from V10.protocols import Architecture
from V10.utils import create_logger


def _build_response(status: str, *, architecture: Optional[Architecture] = None, error: Optional[str] = None) -> dict:
    payload = {
        "type": message_types.ARCHITECTURE_RESPONSE,
        "status": status,
    }
    if architecture is not None:
        payload["architecture"] = architecture.to_dict()
    if error is not None:
        payload["error"] = error
    return payload


def run_agent(poll_interval: float = 0.5) -> None:
    bus = FileMessageBus()
    agent = PMAgentV10()
    logger = create_logger("PM_MAIN")
    logger.info("PM agent main loop started")
    agent.logger.set_state("WAITING")

    running = True

    def _handle_shutdown(signum, frame):  # pragma: no cover - signal handler
        nonlocal running
        logger.warning("Received shutdown signal", {"signal": signum})
        running = False

    for sig in (signal.SIGINT, signal.SIGTERM):
        signal.signal(sig, _handle_shutdown)

    while running:
        message = bus.receive("pm", timeout=poll_interval, poll_interval=poll_interval)
        if message is None:
            continue

        payload = message.payload or {}
        msg_type = payload.get("type")
        if msg_type == message_types.SHUTDOWN:
            logger.info("Shutdown command received")
            running = False
            bus.send(
                sender="pm",
                recipient=message.sender,
                payload={"type": message_types.ARCHITECTURE_RESPONSE, "status": "SHUTDOWN_ACK"},
                conversation_id=message.conversation_id,
                in_reply_to=message.message_id,
            )
            continue

        if msg_type != message_types.REQUEST_ARCHITECTURE:
            logger.error("Unsupported message type", {"type": msg_type})
            bus.send(
                sender="pm",
                recipient=message.sender,
                payload=_build_response("ERROR", error=f"Unsupported message type: {msg_type}"),
                conversation_id=message.conversation_id,
                in_reply_to=message.message_id,
            )
            continue

        objective = payload.get("objective", "")
        try:
            agent.logger.set_state("PROCESSING")
            architecture = agent.propose_architecture(objective)
            response_payload = _build_response("SUCCESS", architecture=architecture)
        except Exception as exc:  # pragma: no cover - safety
            agent.logger.error("PM generation failed", {"error": str(exc)})
            response_payload = _build_response("ERROR", error=str(exc))
        finally:
            agent.logger.set_state("WAITING")

        bus.send(
            sender="pm",
            recipient=message.sender,
            payload=response_payload,
            conversation_id=message.conversation_id,
            in_reply_to=message.message_id,
        )

    logger.info("PM agent main loop stopped")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the PM agent in standalone mode")
    parser.add_argument("--poll-interval", type=float, default=0.5, help="Polling interval for the inbox in seconds")
    args = parser.parse_args()

    try:
        run_agent(poll_interval=args.poll_interval)
    except KeyboardInterrupt:  # pragma: no cover - interactive use
        print("\nPM agent interrupted", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
