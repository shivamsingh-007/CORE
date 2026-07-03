from pathlib import Path
from app.session.schema import SessionState


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

TEMPLATES = {
    "AGENTS.md": INIT_AGENTS,
    "loop-rules.md": INIT_LOOP_RULES,
    "LOOP.md": INIT_LOOP,
    "context.md": INIT_CONTEXT,
    "state.md": INIT_STATE,
}


def _write(path: Path, content: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)


def scaffold_loop_files(project_dir: str):
    """Write all loop files that don't already exist."""
    root = Path(project_dir)
    created = []
    for name, content in TEMPLATES.items():
        p = root / name
        if not p.exists():
            _write(p, content)
            created.append(name)
    tasks_dir = root / "tasks"
    tasks_dir.mkdir(exist_ok=True)
    for name, content in {"todo.md": "# Tasks\n\n## Current\n- [ ] Define project goal\n", "lessons.md": "# Lessons\n\n## Format\n- Date: Context | Mistake | Rule\n"}.items():
        p = tasks_dir / name
        if not p.exists():
            _write(p, content)
            created.append(f"tasks/{name}")
    return created


def sync_core_files(s: SessionState):
    """Sync in-memory session state to the on-disk loop files (AGENTS.md, context.md, state.md, tasks/)."""
    root = Path(s.project_dir) if s.project_dir else Path(".")
    goal = getattr(s, "goal", "") or ""

    # AGENTS.md — keep initial content, append agent run log
    agents_path = root / "AGENTS.md"
    if agents_path.exists():
        agents_content = agents_path.read_text()
    else:
        agents_content = INIT_AGENTS
    run_log = "\n".join(
        f"- {r.state}: {r.result} — {r.detail[:80]}"
        for r in s.runs[-20:]
    )
    if run_log:
        agents_content = agents_content.split("\n## Recent Runs")[0]
        agents_content += f"\n## Recent Runs\n{run_log}\n"
    _write(agents_path, agents_content)

    # context.md — update description with current goal
    ctx_path = root / "context.md"
    if ctx_path.exists():
        ctx = ctx_path.read_text()
    else:
        ctx = INIT_CONTEXT
    if goal and "<Describe your project here>" in ctx:
        ctx = ctx.replace("<Describe your project here>", goal)
    _write(ctx_path, ctx)

    # state.md — rewrite with current session state
    features_done = getattr(s, "features_done", [])
    features_total = getattr(s, "features_total", 0)
    last_error = s.last_error or ""
    done_list = "\n".join(f"- [x] {f}" for f in features_done) if features_done else "- [ ] No features completed yet"
    log_entries = "\n".join(
        f"- {r.state}: {r.result}" for r in s.runs[-10:]
    )
    state_content = f"""# Project State

## Goal
{goal or "<Current goal>"}

## Loop Status
- current_step: {s.current_state}
- loops_completed: {s.loops_completed}
- features_done: {len(features_done)}/{features_total}
- last_result: {s.runs[-1].result if s.runs else "pending"}
- last_error_summary: {last_error[:200] if last_error else "none"}

## Completed Implementations
{done_list}

## Log
{log_entries}
"""
    _write(root / "state.md", state_content)

    # tasks/todo.md — update with current features
    todo_path = root / "tasks/todo.md"
    if todo_path.exists():
        todo_content = todo_path.read_text()
    else:
        tasks_dir = root / "tasks"
        tasks_dir.mkdir(exist_ok=True)
        todo_content = "# Tasks\n\n## Current\n- [ ] Define project goal\n"
    features = getattr(s, "features_done", [])
    if features:
        task_lines = "\n".join(f"- [x] {f}" for f in features)
        todo_content += f"\n## Features\n{task_lines}\n"
    _write(todo_path, todo_content)
