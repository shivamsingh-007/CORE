import os
from pathlib import Path

CORE_FILES = ["AGENTS.md", "loop-rules.md", "LOOP.md", "context.md", "state.md"]
TASK_FILES = ["tasks/todo.md", "tasks/lessons.md"]
ALL_REQUIRED = CORE_FILES + TASK_FILES

INIT_AGENTS = """# Loop Agent Instructions

## Purpose
This project uses the loop agent to enforce PLAN->IMPLEMENT->VERIFY cycles.

## Stack
- Agent: Google ADK with loop-rules.md
- State: Markdown files

## Commands
- `uv sync` - install dependencies
- `uv run pytest` - run tests

## Rules
- Follow loop-rules.md
- Never skip PLAN or VERIFY
- Docs-first when goal changes
"""

INIT_LOOP_RULES = """# Loop Rules

## Core Loop Shape
PLAN -> IMPLEMENT -> VERIFY -> PLAN ...

## Rules
1. Never skip PLAN or VERIFY
2. Docs-first when goal changes
3. Use state.md to track progress
4. Add lessons to tasks/lessons.md on failure
5. Autonomous execution once goal is set
"""

INIT_LOOP = """# LOOP.md

## Loop Shape
1. PLAN_NEXT_STEP
2. IMPLEMENT_STEP
3. VERIFY_STEP
4. DECIDE_RETRY_OR_ADVANCE
5. UPDATE_STATE
6. REPEAT

## State
- state.md - current loop state
- tasks/todo.md - task breakdown
- tasks/lessons.md - lessons learned
"""

INIT_CONTEXT = """# Project Context

## Description
<Describe your project here>

## Stack
<Languages, frameworks, tools>

## Key Files
- `AGENTS.md`
- `loop-rules.md`
- `LOOP.md`
- `state.md`

## Commands
- Build: <command>
- Test: <command>
"""

INIT_STATE = """# Project State

## Goal
<Current goal>

## Loop Status
- current_step:
- implementation_attempts: 0
- verification_attempts: 0
- last_result: pending
- last_error_summary:

## Completed Implementations
- [ ] Step 1:

## Log
"""


def check_loop_compliance(project_path: str) -> str:
    """Check if a project directory follows loop agent conventions.
    Reads required files (AGENTS.md, loop-rules.md, LOOP.md, context.md, state.md, tasks/todo.md, tasks/lessons.md)
    and reports which exist or are missing."""
    root = Path(project_path)
    if not root.is_dir():
        return f"Error: path does not exist or is not a directory: {project_path}"

    lines = [f"Loop Compliance Check for: {root.resolve()}", ""]
    passed = 0
    failed = 0

    for name in CORE_FILES:
        if (root / name).exists():
            lines.append(f"  PASS  {name}")
            passed += 1
        else:
            lines.append(f"  FAIL  {name}")
            failed += 1

    for name in TASK_FILES:
        if (root / name).exists():
            lines.append(f"  PASS  {name}")
            passed += 1
        else:
            lines.append(f"  FAIL  {name}")
            failed += 1

    lines.append("")
    lines.append(f"Result: {passed} passed, {failed} failed")
    if failed > 0:
        lines.append("Run `loop-agent init <path>` to scaffold missing files.")
    return "\n".join(lines)


def init_loop_project(project_path: str) -> str:
    """Scaffold loop agent files (AGENTS.md, loop-rules.md, LOOP.md, context.md, state.md, tasks/) into a project directory. Creates the directory if it doesn't exist."""
    root = Path(project_path)
    root.mkdir(parents=True, exist_ok=True)

    files = [
        ("AGENTS.md", INIT_AGENTS),
        ("loop-rules.md", INIT_LOOP_RULES),
        ("LOOP.md", INIT_LOOP),
        ("context.md", INIT_CONTEXT),
        ("state.md", INIT_STATE),
    ]

    created = []
    skipped = []

    for name, content in files:
        path = root / name
        if path.exists():
            skipped.append(name)
        else:
            path.write_text(content)
            created.append(name)

    tasks_dir = root / "tasks"
    tasks_dir.mkdir(exist_ok=True)

    task_files = {
        "todo.md": "# Tasks\n\n## Current\n- [ ] Define project goal\n",
        "lessons.md": "# Lessons\n\n## Format\n- Date: Context | Mistake | Rule\n",
    }

    for name, content in task_files.items():
        path = tasks_dir / name
        if path.exists():
            skipped.append(f"tasks/{name}")
        else:
            path.write_text(content)
            created.append(f"tasks/{name}")

    lines = ["Loop agent initialized."]
    if created:
        lines.append(f"  Created: {', '.join(created)}")
    if skipped:
        lines.append(f"  Skipped (already exist): {', '.join(skipped)}")
    return "\n".join(lines)


def read_loop_state(project_path: str) -> str:
    """Read and display the current loop state from state.md in the given project directory."""
    path = Path(project_path) / "state.md"
    if not path.exists():
        return f"state.md not found at {path}. Run `loop-agent init <path>` to create one."
    return path.read_text()
