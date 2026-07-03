---
name: harness
description: >-
  Manage the project harness: plan work, review progress, and prepare releases.
  Use when the user says "plan", "scope", "review", "release", "check
  progress", "what's next", or whenever the project needs structured planning
  before implementation, review of completed work, or release preparation.
  Also use when the user needs to create specs, designs, or task breakdowns.
---

# Harness Agent

Provides structured project management: planning, review, and release.

## Modes

### Plan mode (`plan`)
- Read project state and feature list
- Scope the work and create specs + plans
- Update tasks/todo.md with step-by-step breakdown

### Review mode (`review`)
- Check completed work against specs
- Verify all acceptance criteria are met
- Flag incomplete or incorrect features

### Release mode (`release`)
- Verify everything is complete
- Tag the release
- Print release summary

## Usage

Invoke with: `loop-agent harness <mode> --project-dir <path> --goal "<goal>"`

## Code Reference

Implementation: `app/agents/harness/agent.py`
