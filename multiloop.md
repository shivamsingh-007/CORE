# Multi-Loop Coordination

## Priority Order
1. Project Builder (main dev loop)
2. CI Sweeper (if enabled)

## Collision Rules
- One agent per branch per hour
- Denylist: target/, .git/, node_modules/
- Shared state via state.md and tasks/

## Pause
- If STATE.md contains `loop-pause-all: true`, all loops pause
