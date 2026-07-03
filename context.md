# Project Context

## Description
A loop agent built on Google ADK that enforces disciplined PLAN→IMPLEMENT→VERIFY development cycles. The agent runs as an ADK agent (Gemini via Vertex AI) and provides tools for checking compliance, scaffolding projects, and reading state.

## Goals
1. Provide a Google ADK agent with loop enforcement tools
2. Deploy to Agent Runtime with CI/CD via GitHub Actions
3. The agent must be self-enforcing — it follows its own rules

## Key Files
- `AGENTS.md` — project instructions for OpenCode
- `loop-rules.md` — global loop constitution
- `LOOP.md` — this project's loop specifics
- `state.md` — current loop state
- `tasks/todo.md` — task breakdown
- `tasks/lessons.md` — self-improvement memory
- `app/agent.py` — ADK agent definition
- `app/tools.py` — loop enforcement tools
- `app/fast_api_app.py` — FastAPI server (ADK + A2A)
- `pyproject.toml` — Python project config
- `deployment/terraform/` — GCP infrastructure

## Commands
- `uv sync` — install dependencies
- `agents-cli playground` — interactive testing
- `agents-cli run "check compliance for ."` — smoke test
- `uv run pytest tests/unit tests/integration` — run tests
- `agents-cli deploy` — deploy to dev

## Constraints
- Python 3.11+, Google ADK, Gemini model
- Markdown files are the state format
- Must work on Windows and Linux
