from pathlib import Path

from app.core_sync import scaffold_loop_files, TEMPLATES

CORE_FILES = list(TEMPLATES.keys())
TASK_FILES = ["tasks/todo.md", "tasks/lessons.md"]


def check_loop_compliance(project_path: str) -> str:
    """Check if a project directory follows loop conventions by verifying required files exist."""
    try:
        root = Path(project_path)
    except Exception as e:
        return f"Error: {e}"
    if not root.is_dir():
        return f"Error: path does not exist or is not a directory: {project_path}"
    lines = [f"Loop Compliance Check for: {root.resolve()}", ""]
    passed = 0
    failed = 0
    for name in CORE_FILES:
        p = root / name
        if p.exists():
            lines.append(f"  PASS  {name}"); passed += 1
        else:
            lines.append(f"  FAIL  {name}"); failed += 1
    for name in TASK_FILES:
        p = root / name
        if p.exists():
            lines.append(f"  PASS  {name}"); passed += 1
        else:
            lines.append(f"  FAIL  {name}"); failed += 1
    lines.append("")
    lines.append(f"Result: {passed} passed, {failed} failed")
    if failed > 0:
        lines.append("Run init_loop_project to scaffold missing files.")
    return "\n".join(lines)


def init_loop_project(project_path: str) -> str:
    """Scaffold loop agent files (AGENTS.md, loop-rules.md, LOOP.md, context.md, state.md, tasks/) into a project directory."""
    try:
        created = scaffold_loop_files(project_path)
        lines = ["Loop agent initialized."]
        if created:
            lines.append(f"  Created: {', '.join(created)}")
        return "\n".join(lines)
    except OSError as e:
        return f"Failed to init project: {e}"


def read_loop_state(project_path: str) -> str:
    """Read and display the current loop state from state.md."""
    try:
        p = Path(project_path) / "state.md"
        if not p.exists():
            return f"state.md not found at {p}. Run init_loop_project to create one."
        return p.read_text()
    except OSError as e:
        return f"Failed to read state: {e}"


def plan_next_step(project_path: str, goal: str) -> str:
    """Analyze state.md and todo.md to determine the next step to work on."""
    try:
        root = Path(project_path)
        state_file = root / "state.md"
        todo_file = root / "tasks/todo.md"
        if not state_file.exists():
            return "No state.md found. Init the project first."
        state = state_file.read_text()
        todo = todo_file.read_text() if todo_file.exists() else "No tasks defined."
        return f"## Current State\n{state}\n\n## Tasks\n{todo}\n\n## Instruction\nBased on the state and tasks above, determine the next concrete step to implement and explain why."
    except OSError as e:
        return f"Failed to plan next step: {e}"


def add_lesson(project_path: str, context: str, mistake: str, rule: str) -> str:
    """Record a lesson learned to prevent repeating mistakes."""
    try:
        p = Path(project_path) / "tasks/lessons.md"
        if not p.exists():
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text("# Lessons\n\n## Format\n- Date: Context | Mistake | Rule\n")
        entry = f"\n- {context} | {mistake} | {rule}"
        p.write_text(p.read_text() + entry)
        return f"Lesson recorded: {mistake}"
    except OSError as e:
        return f"Failed to record lesson: {e}"


def update_loop_state(project_path: str, step: str = "", status: str = "", attempts: int = 0) -> str:
    """Update the loop state in state.md with current step progress."""
    try:
        p = Path(project_path) / "state.md"
        if not p.exists():
            return "state.md not found."
        content = p.read_text()
        if step:
            content = content.replace("current_step:", f"current_step: {step}")
        if status:
            content = content.replace("last_result:", f"last_result: {status}")
        if attempts:
            import re
            m = re.search(r"implementation_attempts: (\d+)", content)
            if m:
                old = int(m.group(1))
                content = content.replace(f"implementation_attempts: {old}", f"implementation_attempts: {old + attempts}")
        p.write_text(content)
        return f"State updated: step={step}, status={status}"
    except OSError as e:
        return f"Failed to update state: {e}"
