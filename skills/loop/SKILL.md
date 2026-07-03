---
name: loop
description: >-
  Autonomous loop orchestrator that runs the full development pipeline from
  goal to completion. Use when the user says "run the loop", "go", "autonomous
  mode", "full cycle", "run until done", "execute the project", or whenever
  they want to start or resume an autonomous development session. Routes
  through DISCOVERY→PLANNING→SCAFFOLDING→INITIALIZING→IMPLEMENTING→
  SELF_CHECK→VERIFYING→BUG_HUNT→REWORK|READY. Syncs core files after
  every phase. Only stops on READY or FAILED.
---

# Loop Orchestrator

Procedural orchestrator that routes between agents based on state machine transitions.

## States

| State | What happens |
|-------|-------------|
| DISCOVERY | Initializer interviews user, gathers requirements |
| PLANNING | Harness plans the work, writes specs |
| SCAFFOLDING | Harness creates project structure |
| INITIALIZING | Initializer scaffolds harness + loop files |
| IMPLEMENTING | Coding implements one feature |
| SELF_CHECK | Verifies feature_list.json completeness |
| VERIFYING | Runs tests, checks quality |
| BUG_HUNT | T3MP3ST scans for bugs |
| REWORK | Fix issues, re-implement |
| READY | All done, release |
| FAILED | Unrecoverable error |

## Key Features

- **Auto-sync**: After every phase, AGENTS.md, context.md, state.md, tasks/ are updated
- **Resume**: Reads `.loop-session.json` to skip completed phases
- **Goal tracking**: Goal string propagates through all phases
- **Unlimited loop**: Runs until READY or FAILED (max_loops as safety limit)

## Usage

`loop-agent go --goal "<goal>" --project-dir <path>`
`loop-agent loop --goal "<goal>" --project-dir <path> --max-loops <N>`

## Code Reference

Implementation: `app/agents/loop/orchestrator.py`
