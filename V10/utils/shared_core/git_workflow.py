#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Git Workflow Manager - Phase-based Git Operations
==================================================

Manages Git workflow for phased development:
- Initialize repo
- Create branches per phase
- Commit with structured messages
- Track progress
"""

import subprocess
from pathlib import Path
from typing import List, Optional, Tuple, Dict


def run_git_command(command: List[str], cwd: str) -> Tuple[bool, str]:
    """
    Run a git command.

    Returns:
        (success, output)
    """
    try:
        result = subprocess.run(
            ["git"] + command,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=30
        )

        output = result.stdout + result.stderr

        return (result.returncode == 0, output.strip())

    except subprocess.TimeoutExpired:
        return (False, "Git command timed out")
    except Exception as e:
        return (False, f"Error: {e}")


def init_project_repo(project_dir: str) -> bool:
    """
    Initialize git repo in project directory.

    Returns:
        success: bool
    """
    project_path = Path(project_dir)

    if not project_path.exists():
        return False

    # Check if already a repo
    if (project_path / ".git").exists():
        return True

    # Init repo
    success, output = run_git_command(["init"], str(project_path))

    if not success:
        return False

    # Initial commit
    success, _ = run_git_command(["add", ".gitignore"], str(project_path))

    # Create .gitignore if needed
    gitignore = project_path / ".gitignore"
    if not gitignore.exists():
        gitignore.write_text(
            "__pycache__/\n*.pyc\n.env\n.venv/\nnode_modules/\n.DS_Store\n"
        )

    run_git_command(["add", ".gitignore"], str(project_path))
    run_git_command(
        ["commit", "-m", "[INIT] Initialize repository"],
        str(project_path)
    )

    return True


def create_phase_branch(project_dir: str, phase: str) -> bool:
    """
    Create and checkout a branch for a phase.

    Args:
        project_dir: Project directory
        phase: Phase name (MVP, PRODUCTION, ENTERPRISE)

    Returns:
        success: bool
    """
    branch_map = {
        "MVP": "feat/mvp",
        "PRODUCTION": "feat/production-ready",
        "ENTERPRISE": "main"
    }

    branch_name = branch_map.get(phase, f"feat/{phase.lower()}")

    # Create branch
    success, output = run_git_command(
        ["checkout", "-b", branch_name],
        project_dir
    )

    if not success:
        # Branch might exist, try to checkout
        success, output = run_git_command(
            ["checkout", branch_name],
            project_dir
        )

    return success


def commit_phase(
    project_dir: str,
    phase: str,
    description: str,
    files: Optional[List[str]] = None
) -> Tuple[bool, str]:
    """
    Commit changes for a phase.

    Args:
        project_dir: Project directory
        phase: Phase name
        description: Commit description
        files: Specific files to commit (None = all)

    Returns:
        (success, commit_hash)
    """
    # Add files
    if files:
        for file in files:
            run_git_command(["add", file], project_dir)
    else:
        run_git_command(["add", "."], project_dir)

    # Commit message format: [PHASE] description
    commit_msg = f"[{phase}] {description}"

    success, output = run_git_command(
        ["commit", "-m", commit_msg],
        project_dir
    )

    if not success:
        return (False, "")

    # Get commit hash
    success, commit_hash = run_git_command(
        ["rev-parse", "HEAD"],
        project_dir
    )

    return (True, commit_hash.strip() if success else "")


def get_commit_history(project_dir: str, limit: int = 10) -> List[Dict]:
    """
    Get recent commit history.

    Returns:
        List of {hash, message, author, date}
    """
    success, output = run_git_command(
        ["log", f"--max-count={limit}", "--pretty=format:%H|%s|%an|%ad", "--date=short"],
        project_dir
    )

    if not success:
        return []

    commits = []
    for line in output.split('\n'):
        if '|' in line:
            parts = line.split('|')
            if len(parts) == 4:
                commits.append({
                    "hash": parts[0],
                    "message": parts[1],
                    "author": parts[2],
                    "date": parts[3]
                })

    return commits


def get_changed_files(project_dir: str) -> List[str]:
    """
    Get list of changed files (staged + unstaged).

    Returns:
        List of file paths
    """
    success, output = run_git_command(
        ["status", "--porcelain"],
        project_dir
    )

    if not success:
        return []

    files = []
    for line in output.split('\n'):
        if line.strip():
            # Format: "XY filename"
            parts = line.strip().split(maxsplit=1)
            if len(parts) == 2:
                files.append(parts[1])

    return files


def create_phase_tag(project_dir: str, phase: str, version: str = "1.0") -> bool:
    """
    Create a tag for a completed phase.

    Args:
        project_dir: Project directory
        phase: Phase name
        version: Version number

    Returns:
        success: bool
    """
    tag_name = f"{phase.lower()}-v{version}"

    success, output = run_git_command(
        ["tag", "-a", tag_name, "-m", f"Completed {phase} phase"],
        project_dir
    )

    return success


def merge_phase_to_main(project_dir: str, phase_branch: str) -> bool:
    """
    Merge a phase branch to main.

    Args:
        project_dir: Project directory
        phase_branch: Branch to merge (e.g., feat/mvp)

    Returns:
        success: bool
    """
    # Checkout main
    success, _ = run_git_command(["checkout", "main"], project_dir)

    if not success:
        # Create main if it doesn't exist
        success, _ = run_git_command(["checkout", "-b", "main"], project_dir)

    if not success:
        return False

    # Merge
    success, output = run_git_command(
        ["merge", "--no-ff", phase_branch, "-m", f"Merge {phase_branch} into main"],
        project_dir
    )

    return success
