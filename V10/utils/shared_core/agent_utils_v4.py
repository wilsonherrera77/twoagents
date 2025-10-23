"""
Utility functions for V4 agents
Compatible wrappers around shared_utils for V4 agent requirements
"""

import os
import uuid
from datetime import datetime
from shared_utils import (
    log as shared_log,
    send_message as shared_send_message,
    read_inbox as shared_read_inbox,
    wait_for_message as shared_wait_for_message,
    cleanup_old_messages as shared_cleanup_old_messages
)


def log_agent_action(agent_name: str, message: str, level: str = "INFO"):
    """
    Log agent action with consistent format

    Args:
        agent_name: Name of the agent (e.g., "Alex", "Taylor")
        message: Message to log
        level: Log level (INFO, SUCCESS, WARN, ERROR)
    """
    # Map to shared_utils log levels
    level_map = {
        "INFO": "INFO",
        "SUCCESS": "SUCCESS",
        "WARN": "WARN",
        "ERROR": "ERROR"
    }

    mapped_level = level_map.get(level, "INFO")

    # Use shared_utils log with agent role
    # For V4 agents, we'll use their names directly
    shared_log(agent_name, message, mapped_level)


def mark_as_processed(role: str, msg: dict):
    """
    Mark message as processed

    In V2 system, this is handled by mark_as_read parameter in read_inbox()
    For V4, we can implement if needed, or just use read_inbox with mark_as_read=True

    Args:
        role: Agent role
        msg: Message dict
    """
    # V2 system uses mark_as_read=True in read_inbox()
    # This function is a no-op for compatibility
    pass


def clear_screen():
    """Clear terminal screen"""
    os.system('cls' if os.name == 'nt' else 'clear')


def get_conversation_id() -> str:
    """
    Generate or retrieve conversation ID

    Returns:
        Unique conversation ID
    """
    # Generate timestamp-based conversation ID
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_id = str(uuid.uuid4())[:8]
    return f"conv_{timestamp}_{unique_id}"


# Wrapper functions for compatibility with UX Agent V4

def log(role: str, message: str, level: str = "INFO"):
    """
    Wrapper for shared_log to match UX agent's expected signature

    Args:
        role: Agent role (e.g., "ux", "security", "qa")
        message: Message to log
        level: Log level (INFO, SUCCESS, WARN, ERROR)
    """
    shared_log(role, message, level)


def send_message(from_role: str, to_role: str, msg_type: str, content: dict, priority: str = "normal"):
    """
    Wrapper for shared_send_message

    Args:
        from_role: Sender role
        to_role: Recipient role
        msg_type: Message type
        content: Message content dict
        priority: Message priority
    """
    shared_send_message(from_role, to_role, msg_type, content, priority)


def read_inbox(role: str, mark_as_read: bool = True):
    """
    Wrapper for shared_read_inbox

    Args:
        role: Agent role
        mark_as_read: Whether to mark message as processed

    Returns:
        Message dict or None
    """
    return shared_read_inbox(role, mark_as_read)


def wait_for_message(role: str, expected_type: str = None, timeout: int = 60):
    """
    Wrapper for shared_wait_for_message

    Args:
        role: Agent role
        expected_type: Expected message type (optional)
        timeout: Timeout in seconds

    Returns:
        Message dict or None
    """
    return shared_wait_for_message(role, expected_type, timeout)


def cleanup_old_messages(role: str):
    """
    Wrapper for shared_cleanup_old_messages

    Args:
        role: Agent role
    """
    shared_cleanup_old_messages(role)
