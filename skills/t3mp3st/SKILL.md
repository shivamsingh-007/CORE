---
name: t3mp3st
description: >-
  Multi-engine bug hunter that scans code for security flaws, logic errors,
  and quality issues. Use when the user says "hunt", "bug hunt", "scan for
  bugs", "security scan", "audit code", "find bugs", "code review", or
  whenever code needs adversarial testing before release. Runs static
  analysis, dynamic testing, and code review in sequence. Also use
  automatically after verification passes in the autonomous loop.
---

# T3MP3ST — Multi-Engine Bug Hunter

## Pipeline

1. **RECON** — Map the codebase: files, imports, entry points, exports
2. **SCAN** — Static analysis: regex patterns for common bug classes (race conditions, path traversal, injection, error handling gaps)
3. **EXPLOIT** — Dynamic probing: invoke modules with edge-case inputs, check for crashes
4. **REVIEW** — LLM-driven code review: focus on suspicious patterns from SCAN
5. **REPORT** — Deduplicate, classify by severity, produce structured report

## Severity Levels

- `CRITICAL` — Security vulnerability, data loss
- `HIGH` — Logic error causing wrong behavior
- `MEDIUM` — Error handling gap, edge case
- `LOW` — Code style, maintainability
- `INFO` — Observation, suggestion

## Code Reference

Implementation: `app/agents/t3mp3st/` (multi-file agent)
