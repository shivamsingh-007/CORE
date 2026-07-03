# Loop Rules — Global Loop Constitution for All Agents

Non-negotiable rules for every AI agent in this project. Treat as a system-level contract.

## 0. Core Loop Shape
Every non-trivial task runs: **PLAN → IMPLEMENT → VERIFY → PLAN again → ...** until done or stopped.
Never skip PLAN or VERIFY. Never reorder.

## 1. Spec-Me at Start
First run: discover project purpose, stack, structure, commands. Read AGENTS.md, context.md, LOOP.md, loop-rules.md, state.md, tasks/. Write/refresh spec in context.md before coding.

## 2. Docs-First When Goal Changes
Goal changes → update context.md, tasks/todo.md, state.md first. Then code.

## 3. PLAN Phase
Read all state files. Produce a step plan (step_id, description, target files, success criteria, verification method). Write to tasks/todo.md and state.md.

## 4. IMPLEMENT Phase
Only modify files in the current plan. No broad refactors. After impl: update state.md (increment attempts, log).

## 5. VERIFY Phase (Maker vs Checker)
Always use a separate checker. Internal checks (build, test) + external verifier review. Treat your own reasoning as insufficient.

## 6. Loop Memory
Disk + git = canonical memory. Re-read state files on context reset. Never assume prior context is loaded.

## 7. Self-Improvement
Every correction or failed verification → add lesson to tasks/lessons.md. Read lessons before PLAN.

## 8. Autonomy
Once goal is set, run the loop autonomously. Don't wait for micro-instructions.

## 9. Stop Conditions
All tasks done & verified, or hard limit reached (max attempts/time/budget), or loop-pause-all flag set.

## 10. Enforcement
If you skip PLAN/VERIFY, fail to update docs, ignore lessons, or declare done without verification → treat as violation, add lesson, re-run affected step.
