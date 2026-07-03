# Project Context

## Description
Loop Agent — an autonomous multi-agent development pipeline. Takes a project goal and runs a full development loop (DISCOVERY→PLANNING→SCAFFOLDING→INITIALIZING→IMPLEMENTING→SELF_CHECK→VERIFYING→BUG_HUNT→REWORK→READY) with zero manual intervention. Features 5 specialized agents, a procedural orchestrator, anthropic-format skills, auto-sync of core files after every phase, and session persistence for resume support.

## Stack
- Python 3.11+
- Ollama / OpenRouter (OpenAI-compatible provider)
- Anthropic skill format (skills/)
- skills-ref for validation
- pytest for testing

## Key Files
- `AGENTS.md` — project instructions
- `loop-rules.md` — global loop constitution
- `LOOP.md` — loop specifics
- `state.md` — current loop state
- `tasks/todo.md` — task breakdown
- `tasks/lessons.md` — self-improvement memory
- `skills/` — anthropic-format SKILL.md per agent
- `app/agents/` — agent implementations
- `app/agents/loop/orchestrator.py` — procedural orchestrator
- `app/core_sync.py` — auto-sync utility
- `.loop-session.json` — session persistence

## Commands
- `uv sync` — install dependencies
- `uv run pytest tests -v` — run tests
- `loop-agent go --goal "<goal>" --project-dir <path>` — full autonomous loop
- `loop-agent init --project-dir <path>` — interactive setup
- `loop-agent hunt --project-dir <path>` — bug hunt
- `skills-ref validate skills/*` — validate skills

## Constraints
- Python 3.11+, OpenAI-compatible provider
- Markdown files + JSON for state
- Must work on Windows
