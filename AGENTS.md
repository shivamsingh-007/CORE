# Loop Agent — Multi-Agent Autonomous Development Pipeline

## Purpose
An autonomous multi-agent system that takes a project goal and runs a full development loop — DISCOVERY → PLANNING → SCAFFOLDING → INITIALIZING → IMPLEMENTING → SELF_CHECK → VERIFYING → BUG_HUNT → REWORK → READY — with zero manual intervention.

## Architecture
- **Orchestrator**: Procedural state machine that routes between agents
- **5 Agents**: Initializer, Harness, Coding, Verifying, T3MP3ST (bug hunter)
- **Skills**: Each agent is documented as an anthropic-format SKILL.md under `skills/`
- **State**: `.loop-session.json` + on-disk markdown files (AGENTS.md, state.md, tasks/)
- **Auto-Sync**: Core files are synced after every phase change

## Agents

| Agent | State | Purpose |
|-------|-------|---------|
| Initializer | INITIALIZING / DISCOVERY | Interviews user, creates harness + loop files |
| Harness | PLANNING / SCAFFOLDING | Plans work, reviews, releases |
| Coding | IMPLEMENTING | One feature per session |
| Verifying | VERIFYING | Runs tests, checks quality |
| T3MP3ST | BUG_HUNT | Multi-engine bug hunter (RECON→SCAN→EXPLOIT→REVIEW→REPORT) |
| Orchestrator | all | Routes phases, syncs state, tracks goal |

## Skills
- `skills/initializer/SKILL.md`
- `skills/harness/SKILL.md`
- `skills/coding/SKILL.md`
- `skills/verifying/SKILL.md`
- `skills/t3mp3st/SKILL.md`
- `skills/loop/SKILL.md`

## Commands
- `uv sync` — install dependencies
- `uv run pytest tests -v` — run tests
- `loop-agent init --project-dir <path>` — interactive agent setup
- `loop-agent go --goal "<goal>" --project-dir <path>` — full autonomous loop
- `loop-agent loop --goal "<goal>" --max-loops <N>` — loop with safety limit
- `loop-agent hunt --project-dir <path>` — bug hunt only
- `loop-agent coding --project-dir <path> --task-id <id>` — single feature
- `loop-agent harness plan|review|release --project-dir <path>` — harness mode
- `skills-ref validate skills/*` — validate skill format

## Loop Rules
See `loop-rules.md`, `state.md`, `tasks/todo.md`.
