---
name: verifying
description: >-
  Run tests and verify that implemented features work correctly. Use when
  the user says "verify", "test", "check", "run tests", "validate", "make
  sure it works", or whenever code has been implemented and needs to be
  checked for correctness. Runs project tests, checks feature_list.json
  passes, and reports pass/fail results. Always use after implementing
  before declaring anything done.
---

# Verifying Agent

Runs tests and validates that features pass.

## Workflow

1. Run the project's test command (from context.md or init.sh)
2. Collect test output and parse pass/fail counts
3. Check feature_list.json for feature completeness
4. Report results: passed_all, passed count, failed count

## Return Value

```json
{"passed_all": true/false, "passed": N, "failed": N, "output": "..."}
```

## Code Reference

Implementation: `app/agents/verifying/agent.py`
