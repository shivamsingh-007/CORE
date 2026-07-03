---
name: initializer
description: >-
  Set up a new project with harness scaffolding and loop files. Use when
  the user says "init", "setup", "start a project", "bootstrap", "first time
  setup", or whenever a project needs an initial interview to capture
  requirements, create feature lists, and scaffold the loop agent files
  (AGENTS.md, loop-rules.md, LOOP.md, context.md, state.md, tasks/).
  Also use when the user needs to define project scope, features, and
  development conventions before coding begins.
---

# Initializer Agent

Interviews the user to understand a project, then creates harness scaffolding and loop files so future agents can work autonomously.

## Workflow

1. Ask ONE question at a time (project name, stack, goal, features, target users, how to run)
2. Track what you know — don't repeat questions
3. When you understand the project, create all harness files

## Outputs

- `docs/PROJECT_BRIEF.md` — Project description and goal
- `docs/GOAL_CONTRACT.json` — Structured project metadata
- `feature_list.json` — JSON array of features with pasess check
- `init.sh` — Install deps and start dev server
- `AGENTS.md`, `loop-rules.md`, `LOOP.md`, `context.md`, `state.md` — Core loop files
- `tasks/todo.md`, `tasks/lessons.md` — Task tracking
- Git repo initialized with first commit

## Code Reference

Implementation: `app/agents/initializer/agent.py`

## Tools

- `ask_user` — Ask a question, wait for answer
- `create_artifact` — Write a file at path with content
- `create_feature_list` — Write a JSON feature list
- `create_init_script` — Write a shell init script
- `init_git` — Initialize git repo and commit
- `create_loop_files` — Scaffold AGENTS.md, loop-rules.md, LOOP.md, context.md, state.md, tasks/
- `finish` — Complete initialization
