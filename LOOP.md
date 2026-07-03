# LOOP.md — Autonomous Multi-Agent Loop

## Loop States
```
DISCOVERY → PLANNING → SCAFFOLDING → INITIALIZING → IMPLEMENTING → SELF_CHECK → VERIFYING → BUG_HUNT → REWORK → READY
                                                                                              ↓         ↑
                                                                                           FAILED
```

| State | Agent | What happens |
|-------|-------|-------------|
| DISCOVERY | Initializer | Interview user, gather requirements |
| PLANNING | Harness | Scope project, create specs |
| SCAFFOLDING | Harness | Create project structure |
| INITIALIZING | Initializer | Scaffold harness + loop files |
| IMPLEMENTING | Coding | One feature per session |
| SELF_CHECK | Orchestrator | Check feature_list.json |
| VERIFYING | Verifying | Run tests, check quality |
| BUG_HUNT | T3MP3ST | Multi-engine bug scan |
| REWORK | Coding | Fix issues, re-implement |
| READY | Harness | Release |
| FAILED | — | Manual intervention needed |

## Auto-Sync
After every phase change, the orchestrator calls `sync_core_files()` to update:
- `AGENTS.md` — agent run log
- `context.md` — project description + goal
- `state.md` — current state, loops, features
- `tasks/todo.md` — feature tracking
- `tasks/lessons.md` — lessons learned

## State
- `state.md` — current loop state
- `tasks/todo.md` — task breakdown
- `tasks/lessons.md` — lessons learned
- `.loop-session.json` — session persistence (resume support)

## Verification
- `uv run pytest tests -v`
- `skills-ref validate skills/*`
