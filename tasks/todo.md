# Tasks

## Step 1: Core Files Setup
- [x] Create .gitignore, AGENTS.md, context.md, loop-rules.md, LOOP.md, state.md, tasks/, multiloop.md

## Step 2: ADK Project Scaffold
- [x] `agents-cli scaffold create` with Agent Runtime + GitHub Actions
- [x] Merge scaffold into project directory
- [x] Install dependencies (`uv sync`)

## Step 3: Loop Agent Tools
- [x] Write `app/tools.py` with check_loop_compliance, init_loop_project, read_loop_state
- [x] Write `app/agent.py` with root_agent using those tools

## Step 4: Agent Config
- [x] Update AGENTS.md with ADK development phases
- [x] Verify all tools work with `uv run python -c`

## Step 5: Verify and Finalize
- [ ] Run `uv run pytest tests/unit`
- [ ] Run `loop-agent init` test in temp dir
- [ ] Final review and state update
