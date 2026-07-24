---
name: multi-stage-infrastructure-fixes
type: infrastructure
summary: Sequence and deliver multi-stage infrastructure fixes (3+ tasks) one task at a time.
description: >
  How to handle multi-stage infrastructure fixes (3+ tasks, mixed priorities).
  Tanzim works in ops mode under pressure. Deliver each task to completion
  sequentially, not as a batch. Each task has explicit subtasks with code,
  test, and verification. Stop after each task and ask before moving to the
  next one.
---

## Context
Tanzim works under pressure in ops mode. When infrastructure has multiple
blockers (e.g., EDITH UUID mismatch + JARVIS calibration + Framework fixes),
the fix list must be prioritized and delivered **one task at a time** — not as
a batch list followed by "pick one and we'll start". Each task runs to
completion (code, test, verification) before the next begins.

## Delivery Pattern

**PHASE 1: Diagnostic Summary (upfront, once)**
- List all tasks with: priority, hours, status, blocker/dependency info
- Format: compact table (5 tasks = 1 screen max)
- Save to file for reference
- State: "Here are the 5 tasks. Ready to start TASK 1?"

**PHASE 2: Execute One Task at a Time**
- Pick the first critical blocker
- Break it into 1–4 subtasks (1.1, 1.2, 1.3, 1.4)
- Each subtask: code change → test → verify
- Walk Tanzim through step-by-step (show changes, run tests)
- When subtask fails: debug in-session, fix, re-test
- When task completes: summary + "Ready for TASK 2?" — **stop there**
- Do NOT jump to TASK 2 without explicit confirmation

**PHASE 3: Next Task (on confirmation)**
- Same pattern: subtasks, code, test, verify, summary, ask

## Pitfall: Batch Delivery
Do NOT:
- Give task list, then immediately start Task 1 code without confirming
- Give all 5 tasks as a list, then ask "which do you want?"
- Present Task 1 at 100% done, then launch into Task 2 without stopping

User correction signal: "give me 1 task at a time" or "do one thing at a time"
→ Embedded here. Next session: deliver tasks sequentially with pauses.

## Subtask Pattern for Code Fixes
Each subtask has explicit name + deliverable:

```
TASK N.M: [Clear descriptive name]
───────────────────────────────
PROBLEM: [What's broken, why]
SOLUTION: [What we're doing]
RESULT: [What we check to know it worked]

[Code changes / execution]

✓ DONE → [Brief verification output]
```

Example (from TASK 1 EDITH recovery):
```
TASK 1.1: Create recovery.json
───────────────────────────────
PROBLEM: Vault has no recovery metadata
SOLUTION: Write recovery.json with original UUID + migration status
RESULT: File exists, contains correct data, permissions 0o600

[Execute code to create file]

✓ DONE → recovery.json created at ~/.hermes/.edith/recovery.json
```

## When to Stop and Wait
After each task's final subtask (the test/verify step):
- Print a completion summary (what changed, what was added)
- Print current status (blockers resolved? what's next?)
- Explicitly ask: "Ready for TASK 2?" or "Want to test the migration first?"
- **Do not assume**. Wait for user response.

## File Tracking
For multi-stage infrastructure work, save a completion marker after each task:
- `~/TASK_N_COMPLETE.txt` — summary of what was done
- Include: subtasks finished, files modified, verification results
- Use as checklist for next session if interrupted

## Apply When
- 3+ related fixes needed (priority blocker + secondary blockers)
- User explicitly says "1 task at a time" or "give me one step"
- Infrastructure work under time pressure (ops mode, "deploy veronica")
- Any multi-stage fix where intermediate testing is critical

## Related Skills
- `subagent-orchestration` — when to use Veronica for diagnostics vs. inline execution
- `error-debugging` — how to handle failures mid-task
- `infrastructure-diagnostics` — how to scope and report infrastructure issues
