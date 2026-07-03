---
name: coding
description: >-
  Implement one feature at a time following the project's feature list and
  existing conventions. Use when the user says "implement", "code", "build
  feature", "develop", "write code", "add functionality", or whenever
  a feature from feature_list.json needs to be implemented. Works on one
  feature per session, no broad refactors. Also use for bug fixes within
  the current feature scope.
---

# Coding Agent

Implements one feature from the feature list per session.

## Workflow

1. Read feature_list.json to find an unfinished feature (`passes: false`)
2. Read AGENTS.md, loop-rules.md, context.md, state.md for context
3. Run init.sh to verify the app still works
4. Implement the feature — one at a time, no broad refactors
5. Update feature_list.json — flip `passes` to `true`
6. Record progress in CLAUDE-PROGRESS.txt and state.md

## Rules

- Only modify files in the current feature's plan
- No broad refactors outside scope
- Update state.md after implementation (increment attempts, log)

## Code Reference

Implementation: `app/agents/coding/agent.py`
