"""File-based asynchronous message bus for V10 agents."""

from __future__ import annotations

import json
import time
import uuid
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Any

from V10.utils import create_logger, get_agent_runtime_dir, get_runtime_root


@dataclass
class Message:
    message_id: str
    conversation_id: str
    sender: str
    recipient: str
    payload: Dict[str, Any]
    created_at: str
    in_reply_to: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_file(cls, path: Path) -> "Message":
        with path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
        return cls(**data)


class FileMessageBus:
    """Minimal filesystem-backed message queue."""

    def __init__(self, base_dir: Optional[Path] = None):
        self.logger = create_logger("MESSAGE_BUS")
        if base_dir is None:
            base_dir = get_runtime_root() / "agents"
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def send(self, sender: str, recipient: str, payload: Dict[str, Any], conversation_id: Optional[str] = None, in_reply_to: Optional[str] = None) -> Message:
        conversation_id = conversation_id or uuid.uuid4().hex
        message_id = f"msg_{int(time.time()*1000)}_{uuid.uuid4().hex[:6]}"
        message = Message(
            message_id=message_id,
            conversation_id=conversation_id,
            sender=sender,
            recipient=recipient,
            payload=payload,
            created_at=datetime.utcnow().isoformat(),
            in_reply_to=in_reply_to,
        )
        inbox = self._inbox_dir(recipient)
        file_path = inbox / f"{message.message_id}.json"
        temp_path = file_path.with_suffix('.json.tmp')
        with temp_path.open('w', encoding='utf-8') as handle:
            json.dump(message.to_dict(), handle, indent=2)
            handle.flush()
        temp_path.replace(file_path)
        self.logger.info(f"Message {message.message_id} sent {sender}->{recipient}")
        return message

    def receive(self, agent_name: str, timeout: float = 0.0, poll_interval: float = 0.5) -> Optional[Message]:
        inbox = self._inbox_dir(agent_name)
        end_time = time.time() + timeout if timeout else None
        while True:
            files = sorted(inbox.glob("*.json"))
            if files:
                file_path = files[0]
                try:
                    message = Message.from_file(file_path)
                    file_path.unlink()
                    self.logger.info(f"Message {message.message_id} received by {agent_name}")
                    return message
                except Exception as exc:
                    self.logger.error(
                        f"Failed to read message {file_path.name}",
                        {"error": str(exc)}
                    )
                    file_path.unlink(missing_ok=True)
            if end_time is not None and time.time() >= end_time:
                return None
            time.sleep(poll_interval)

    def wait_for_reply(self, agent_name: str, in_reply_to: str, timeout: float = 60.0, poll_interval: float = 0.5) -> Optional[Message]:
        inbox = self._inbox_dir(agent_name)
        end_time = time.time() + timeout
        while time.time() < end_time:
            for file_path in sorted(inbox.glob("*.json")):
                try:
                    with file_path.open("r", encoding="utf-8") as handle:
                        data = json.load(handle)
                    if data.get("in_reply_to") == in_reply_to:
                        message = Message(**data)
                        file_path.unlink()
                        self.logger.success(f"Reply {message.message_id} received for {in_reply_to}")
                        return message
                except Exception as exc:
                    self.logger.error(
                        f"Failed to process reply {file_path.name}",
                        {"error": str(exc)}
                    )
                    file_path.unlink(missing_ok=True)
            time.sleep(poll_interval)
        self.logger.warn(f"Timeout waiting reply for {in_reply_to}")
        return None

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _inbox_dir(self, agent_name: str) -> Path:
        agent_dir = get_agent_runtime_dir(agent_name)
        inbox = agent_dir / "inbox"
        inbox.mkdir(parents=True, exist_ok=True)
        return inbox
