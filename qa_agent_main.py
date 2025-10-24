"""Standalone entry point for running the QA agent in its own terminal."""

from __future__ import annotations

import argparse
import signal
import sys

from V10.agents.qa_agent_v10 import QAAgentV10
from V10.core.message_bus import FileMessageBus
from V10.core import message_types
from V10.utils import create_logger


def _build_response(status: str, *, report: dict | None = None, error: str | None = None) -> dict:
    payload = {
        "type": message_types.QA_REVIEW_RESPONSE,
        "status": status,
    }
    if report is not None:
        payload["qa_report"] = report
    if error is not None:
        payload["error"] = error
    return payload


def run_agent(poll_interval: float = 0.5) -> None:
    bus = FileMessageBus()
    agent = QAAgentV10()
    logger = create_logger("QA_MAIN")
    logger.info("QA agent main loop started")

    running = True

    def _handle_shutdown(signum, frame):  # pragma: no cover - signal handler
        nonlocal running
        logger.warning("Received shutdown signal", {"signal": signum})
        running = False

    for sig in (signal.SIGINT, signal.SIGTERM):
        signal.signal(sig, _handle_shutdown)

    while running:
        message = bus.receive("qa", timeout=poll_interval, poll_interval=poll_interval)
        if message is None:
            continue

        payload = message.payload or {}
        msg_type = payload.get("type")
        if msg_type == message_types.SHUTDOWN:
            logger.info("Shutdown command received")
            running = False
            bus.send(
                sender="qa",
                recipient=message.sender,
                payload={"type": message_types.QA_REVIEW_RESPONSE, "status": "SHUTDOWN_ACK"},
                conversation_id=message.conversation_id,
                in_reply_to=message.message_id,
            )
            continue

        if msg_type != message_types.REQUEST_QA_REVIEW:
            logger.error("Unsupported message type", {"type": msg_type})
            bus.send(
                sender="qa",
                recipient=message.sender,
                payload=_build_response("ERROR", error=f"Unsupported message type: {msg_type}"),
                conversation_id=message.conversation_id,
                in_reply_to=message.message_id,
            )
            continue

        project_dir = payload.get("project_dir")
        if not project_dir:
            bus.send(
                sender="qa",
                recipient=message.sender,
                payload=_build_response("ERROR", error="Missing project_dir"),
                conversation_id=message.conversation_id,
                in_reply_to=message.message_id,
            )
            continue

        result = agent.analyze(project_dir)
        response_payload = _build_response("SUCCESS", report=result.to_dict())

        bus.send(
            sender="qa",
            recipient=message.sender,
            payload=response_payload,
            conversation_id=message.conversation_id,
            in_reply_to=message.message_id,
        )

    logger.info("QA agent main loop stopped")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the QA agent in standalone mode")
    parser.add_argument("--poll-interval", type=float, default=0.5, help="Polling interval for the inbox in seconds")
    args = parser.parse_args()

    try:
        run_agent(poll_interval=args.poll_interval)
    except KeyboardInterrupt:  # pragma: no cover - interactive use
        print("\nQA agent interrupted", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
