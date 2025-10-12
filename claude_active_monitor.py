#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Claude Active Monitor - Para que Claude monitoree y desbloquee en tiempo real
===============================================================================

Este script muestra el estado del sistema de forma que Claude pueda:
1. Ver qué está pasando en tiempo real
2. Identificar bloqueos
3. Tomar acción para desbloquear
"""

import time
import json
from pathlib import Path
from datetime import datetime

AGENTS_DIR = Path(".agents")
WORKSPACE = Path("workspace/current_project")
DIALOGUE_LOGS = Path("dialogue_logs")

def get_latest_messages(role, limit=5):
    """Get latest messages for a role"""
    inbox = AGENTS_DIR / role / "inbox"
    if not inbox.exists():
        return []

    messages = []
    for msg_file in sorted(inbox.glob("*.json"), reverse=True)[:limit]:
        try:
            msg = json.loads(msg_file.read_text())
            messages.append({
                "file": msg_file.name,
                "from": msg.get("from", "?"),
                "type": msg.get("type", "?"),
                "time": msg.get("timestamp", "?")
            })
        except:
            pass

    return messages

def get_agent_status():
    """Check which agents are active"""
    status = {}

    for role in ["orchestrator", "dev", "pm", "qa", "security"]:
        inbox = AGENTS_DIR / role / "inbox"
        outbox = AGENTS_DIR / role / "outbox"

        inbox_count = len(list(inbox.glob("*.json"))) if inbox.exists() else 0
        outbox_count = len(list(outbox.glob("*.json"))) if outbox.exists() else 0

        status[role] = {
            "inbox": inbox_count,
            "outbox": outbox_count,
            "active": inbox_count > 0 or outbox_count > 0
        }

    return status

def get_workspace_status():
    """Check workspace state"""
    if not WORKSPACE.exists():
        return {"exists": False}

    files = list(WORKSPACE.glob("*.py"))

    return {
        "exists": True,
        "files": len(files),
        "file_names": [f.name for f in files[:10]]
    }

def get_latest_log():
    """Get latest dialogue log content"""
    if not DIALOGUE_LOGS.exists():
        return None

    logs = sorted(DIALOGUE_LOGS.glob("session_*.md"), reverse=True)
    if not logs:
        return None

    latest = logs[0]
    try:
        content = latest.read_text(encoding='utf-8')
        # Last 20 lines
        lines = content.split('\n')[-20:]
        return {
            "file": latest.name,
            "last_lines": '\n'.join(lines)
        }
    except:
        return {"file": latest.name, "error": "Could not read"}

def main():
    """Main monitoring loop"""
    print()
    print("=" * 80)
    print("CLAUDE ACTIVE MONITOR - Monitoring V6 System")
    print("=" * 80)
    print()
    print("Este monitor muestra el estado en tiempo real para que Claude pueda:")
    print("  1. Ver que esta pasando")
    print("  2. Identificar bloqueos")
    print("  3. Intervenir activamente")
    print()
    print("Presiona Ctrl+C para detener")
    print("=" * 80)
    print()

    iteration = 0

    try:
        while True:
            iteration += 1
            timestamp = datetime.now().strftime("%H:%M:%S")

            print(f"\n[{timestamp}] === Iteration #{iteration} ===\n")

            # Agent status
            agent_status = get_agent_status()
            print("AGENT STATUS:")
            for role, status in agent_status.items():
                active_marker = "[ACTIVE]" if status["active"] else "[idle]"
                print(f"  {role:15} {active_marker:10} inbox:{status['inbox']:2} outbox:{status['outbox']:2}")

            # Recent messages
            print("\nRECENT MESSAGES (Orchestrator inbox):")
            recent = get_latest_messages("orchestrator", limit=3)
            if recent:
                for msg in recent:
                    print(f"  - {msg['type']:30} from {msg['from']:12} [{msg['file']}]")
            else:
                print("  (no messages)")

            # Workspace status
            print("\nWORKSPACE STATUS:")
            ws_status = get_workspace_status()
            if ws_status["exists"]:
                print(f"  Files: {ws_status['files']}")
                if ws_status['file_names']:
                    print(f"  Files: {', '.join(ws_status['file_names'])}")
            else:
                print("  (empty)")

            # Latest log
            print("\nLATEST LOG:")
            log = get_latest_log()
            if log:
                print(f"  File: {log['file']}")
                if "last_lines" in log:
                    print("\n  Last activity:")
                    for line in log["last_lines"].split('\n')[-5:]:
                        if line.strip():
                            print(f"    {line[:70]}")
            else:
                print("  (no log yet)")

            print("\n" + "-" * 80)

            time.sleep(3)

    except KeyboardInterrupt:
        print("\n\nMonitor stopped by user")

if __name__ == "__main__":
    main()
