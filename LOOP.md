# LOOP.md — Loop Agent Project (ADK)

This project implements a **loop agent** built on Google ADK.

## Loop Rules
All loops must follow `loop-rules.md`.

## Loop Shape
1. PLAN_NEXT_STEP
2. IMPLEMENT_STEP
3. VERIFY_STEP (uv run pytest + agents-cli eval)
4. DECIDE_RETRY_OR_ADVANCE
5. UPDATE_STATE_AND_COMMIT
6. REPEAT until goal done

## Active Loop: Project Builder
- **Cadence**: per session
- **State**: state.md
- **Tasks**: tasks/todo.md
- **Lessons**: tasks/lessons.md
- **Verification**: `uv run pytest tests/unit tests/integration`
- **Smoke test**: `agents-cli run "check compliance for ."`
- **Playground**: `agents-cli playground`

## Steps
1. Core files setup (AGENTS.md, context.md, LOOP.md, loop-rules.md, state.md, tasks/)
2. ADK project scaffold via agents-cli
3. Loop agent tools (check_loop_compliance, init_loop_project, read_loop_state)
4. Agent config in app/agent.py
5. Verify and finalize

## Multi-loop
See `multiloop.md` for coordination rules.
