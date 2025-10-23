#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dialogue Logger - Detailed Conversation Tracking
=================================================

Logs all agent-to-agent communications with rich context:
- Message content
- Agent reasoning
- Code changes
- Validation results
- Decision points
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional


DIALOGUE_DIR = Path(__file__).parent / "dialogue_logs"
DIALOGUE_DIR.mkdir(exist_ok=True)


class DialogueLogger:
    """Logs conversations between agents"""

    def __init__(self, session_id: str = None):
        self.session_id = session_id or datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_file = DIALOGUE_DIR / f"session_{self.session_id}.md"
        self.message_count = 0

        # Initialize log file
        self._write_header()

    def _write_header(self):
        """Write session header"""
        with open(self.log_file, 'w', encoding='utf-8') as f:
            f.write(f"# Development Session - {self.session_id}\n\n")
            f.write(f"**Started**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write("---\n\n")

    def log_message(
        self,
        from_agent: str,
        to_agent: str,
        msg_type: str,
        content: Dict,
        reasoning: Optional[str] = None,
        metadata: Optional[Dict] = None
    ):
        """
        Log an agent-to-agent message.

        Args:
            from_agent: Sender (orchestrator/pm/dev)
            to_agent: Recipient
            msg_type: Message type (TASK_ASSIGNMENT, ARCHITECTURE_PROPOSAL, etc)
            content: Message content
            reasoning: Agent's reasoning for this message
            metadata: Additional context (phase, iteration, etc)
        """
        self.message_count += 1
        timestamp = datetime.now().strftime('%H:%M:%S')

        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(f"## Message #{self.message_count} - {timestamp}\n\n")
            f.write(f"**From**: `{from_agent.upper()}` → **To**: `{to_agent.upper()}`\n\n")
            f.write(f"**Type**: `{msg_type}`\n\n")

            if metadata:
                f.write("**Context**:\n")
                for key, value in metadata.items():
                    f.write(f"- {key}: `{value}`\n")
                f.write("\n")

            if reasoning:
                f.write("### 🧠 Agent Reasoning\n\n")
                f.write(f"> {reasoning}\n\n")

            f.write("### 📦 Message Content\n\n")
            f.write("```json\n")
            f.write(json.dumps(content, indent=2, ensure_ascii=False))
            f.write("\n```\n\n")

            f.write("---\n\n")

    def log_phase_start(self, phase_name: str, objectives: list):
        """Log start of a development phase"""
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(f"# 🚀 PHASE: {phase_name}\n\n")
            f.write(f"**Started**: {datetime.now().strftime('%H:%M:%S')}\n\n")
            f.write("**Objectives**:\n")
            for obj in objectives:
                f.write(f"- {obj}\n")
            f.write("\n---\n\n")

    def log_phase_complete(self, phase_name: str, outcome: Dict):
        """Log completion of a phase"""
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(f"## ✅ PHASE COMPLETE: {phase_name}\n\n")
            f.write(f"**Completed**: {datetime.now().strftime('%H:%M:%S')}\n\n")

            if outcome.get("passed"):
                f.write("**Status**: ✅ PASSED\n\n")
            else:
                f.write("**Status**: ⚠️ PARTIAL\n\n")

            f.write("**Validation Results**:\n")
            f.write("```json\n")
            f.write(json.dumps(outcome, indent=2))
            f.write("\n```\n\n")
            f.write("---\n\n")

    def log_validation(self, file_path: str, results: Dict):
        """Log code validation results"""
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(f"### 🔍 Code Validation: `{Path(file_path).name}`\n\n")

            if results.get("passed"):
                f.write("**Result**: ✅ PASSED\n\n")
            else:
                f.write("**Result**: ❌ FAILED\n\n")

                violations = results.get("violations", {})

                if violations.get("critical"):
                    f.write("**🚨 Critical Issues**:\n")
                    for v in violations["critical"]:
                        f.write(f"- {v}\n")
                    f.write("\n")

                if violations.get("high"):
                    f.write("**⚠️ High Priority**:\n")
                    for v in violations["high"]:
                        f.write(f"- {v}\n")
                    f.write("\n")

            f.write("---\n\n")

    def log_git_commit(self, commit_hash: str, message: str, files: list):
        """Log a Git commit"""
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(f"### 📝 Git Commit: `{commit_hash[:7]}`\n\n")
            f.write(f"**Message**: {message}\n\n")
            f.write("**Files changed**:\n")
            for file in files:
                f.write(f"- `{file}`\n")
            f.write("\n---\n\n")

    def log_agent_dialogue(self, agent1: str, agent2: str, topic: str, exchanges: list):
        """
        Log a back-and-forth dialogue between two agents.

        Args:
            agent1: First agent name
            agent2: Second agent name
            topic: Topic of discussion
            exchanges: List of {speaker, message} dicts
        """
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(f"### 💬 Agent Dialogue: {agent1} ↔ {agent2}\n\n")
            f.write(f"**Topic**: {topic}\n\n")

            for i, exchange in enumerate(exchanges, 1):
                speaker = exchange["speaker"]
                message = exchange["message"]
                f.write(f"**{speaker}**: {message}\n\n")

            f.write("---\n\n")

    def log_web_search(self, query: str, results: list):
        """Log web search results"""
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(f"### 🌐 Web Search\n\n")
            f.write(f"**Query**: `{query}`\n\n")
            f.write(f"**Results** ({len(results)} found):\n")
            for i, result in enumerate(results[:5], 1):
                f.write(f"{i}. [{result.get('title', 'N/A')}]({result.get('url', '#')})\n")
            f.write("\n---\n\n")

    def log_iteration_start(self, phase: str, iteration: int):
        """Log start of iteration"""
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(f"### Iteration #{iteration} - {phase}\n\n")
            f.write(f"**Started**: {datetime.now().strftime('%H:%M:%S')}\n\n")
            f.write("---\n\n")

    def log_iteration_loop(self, iteration: int, phase: str, status: str, next_action: str):
        """Log iteration in a feedback loop"""
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(f"### Iteration #{iteration} - {phase}\n\n")
            f.write(f"**Status**: {status}\n\n")
            f.write(f"**Next Action**: {next_action}\n\n")
            f.write("---\n\n")

    def log_session_start(self, params: Dict):
        """Log session start with parameters"""
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write("## Session Parameters\n\n")
            for key, value in params.items():
                f.write(f"- **{key}**: {value}\n")
            f.write("\n---\n\n")

    def log_session_complete(self, summary: Dict):
        """Alias for log_session_end"""
        self.log_session_end(summary)

    def log_session_end(self, summary: Dict):
        """Log end of session with summary"""
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write("\n\n# SESSION SUMMARY\n\n")
            f.write(f"**Ended**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

            f.write(f"**Total Messages**: {self.message_count}\n\n")

            if summary.get("final_phase"):
                f.write(f"**Final Phase**: {summary['final_phase']}\n\n")

            if summary.get("iterations"):
                f.write(f"**Total Iterations**: {summary['iterations']}\n\n")

            if summary.get("files_created"):
                f.write(f"**Files Created**: {len(summary['files_created'])}\n\n")

            f.write("**Full Summary**:\n")
            f.write("```json\n")
            f.write(json.dumps(summary, indent=2))
            f.write("\n```\n\n")

    def get_log_path(self) -> str:
        """Get path to log file"""
        return str(self.log_file)


# Singleton instance for current session
_current_logger: Optional[DialogueLogger] = None


def get_logger(session_id: str = None) -> DialogueLogger:
    """Get or create dialogue logger for current session"""
    global _current_logger

    if _current_logger is None or session_id:
        _current_logger = DialogueLogger(session_id)

    return _current_logger
