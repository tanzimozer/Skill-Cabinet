---
name: friday-2-0-system-integration
domain: system-architecture
category: architecture
description: |
  Pattern for deploying and integrating major Hermes/Friday system upgrades.
  
  Covers the full lifecycle: design → build → test orchestration → GitHub push → runtime integration → validation.
  Used for persistent memory systems, credential architecture changes, and core infrastructure updates.

date_created: 2026-06-11
version: 1.0
tags:
  - friday-2-0
  - system-upgrade
  - architecture
  - integration-pattern
  - deployment
---

## Overview

Friday 2.0 system upgrades are non-trivial changes to core infrastructure (memory, credentials, skill system, runtime). They require:

1. **Design & Prototyping** — Articulate the problem, evaluate options (e.g., Option A vs Option B), pick one
2. **Implementation & Local Testing** — Build the code, unit test in isolation
3. **Orchestrated Validation** — Use subagent deployment (Veronica-style) to validate in parallel
4. **Repository Documentation** — Push to GitHub with comprehensive integration guide
5. **Runtime Activation** — Load and wire into live agent session
6. **Verification & Diagnostics** — Small tests + full diagnostics, expect grade A

The entire workflow takes ~4–6 hours with orchestration (parallel tasks save ~2 hours vs sequential).

## The Friday 2.0 Upgrade Template

### Phase 1: Design & Decision (30 min)

**Input:** Problem statement (e.g., "memory is lost between sessions")

**Process:**
- Define the scope (what are we solving, what are we not solving?)
- Identify constraints (must be lightweight, no new dependencies, reversible, etc.)
- Evaluate 2–3 options (Option A, B, C)
- Present options to user with tradeoffs
- **User picks one**

**Output:** Accepted design, written up with rationale

**Example from Jun 11:** "Option A (lightweight checkpoint snapshots) vs Option B (full persistence store)." User picked A. → checkpoint_manager.py (6,887 bytes, zero dependencies)

### Phase 2: Build & Unit Test (1–2 hours)

**Input:** Accepted design

**Process:**
- Write core module(s) — checkpoint_manager.py, CheckpointIntegration wrapper, etc.
- Unit test each method individually (capture, load, list, prune)
- Verify data integrity (byte-for-byte restoration)
- Aim for 4/4 methods passing, zero external dependencies
- Commit to repo

**Output:** Production-ready code, tested locally

**Example from Jun 11:** CheckpointManager + tests passing 9/9 → push to Friday 2.0 repo

### Phase 3: Orchestrated Validation (1–2 hours)

**Key insight:** Parallel subagent validation is faster than sequential. Use 3 consolidated tasks.

**Task 1 — Code Integration & Testing**
- Pull code from repo
- Create integration wrapper if needed (CheckpointIntegration with lifecycle hooks)
- Build comprehensive test suite (capture/load cycle, error handling, edge cases)
- Run tests: expect 9/9 passing
- **Deliverable:** checkpoint_integration.py + test_checkpoint_integration.py

**Task 2 — Infrastructure & Credential Verification**
- Verify credential vault (all 7 services indexed at top level)
- Validate skill directory state (83 categories, 311 skills)
- Check system files (checkpoint_manager.py, vault.json, memory.md, etc.)
- Confirm cleanup completed (skill bloat removed, 4.4 MB freed)
- **Deliverable:** VAULT_VERIFICATION_REPORT.md

**Task 3 — Three-Layer Memory Integration Test**
- Test capture to Memory layer
- Test push to Hindsight layer
- Verify Vault isolation (zero credential leakage)
- Test Hindsight recall
- Test cross-session persistence (simulate 3 session boundaries)
- **Deliverable:** THREE_LAYER_MEMORY_INTEGRATION_TEST_REPORT.md + test passing 100%

**Why parallel?** Each task is independent. Running all 3 in parallel saves ~2 hours.

**How to invoke:**
```python
subagent(
    role='orchestrator',
    tasks=[
        {"goal": "Code integration + testing..."},
        {"goal": "Credential/infrastructure verification..."},
        {"goal": "Three-layer memory integration test..."},
    ]
)
```

**Expected result:** All 3 reports, all tests passing, zero blockers

### Phase 4: Repository Push & Documentation (30 min)

**Input:** Passing tests, verification reports

**Process:**
- Create INTEGRATION_COMPLETE.md with:
  - 10-item integration checklist (all passing)
  - Metrics (311 skills, 7 services, 609 bytes restored, etc.)
  - Status: A (5.0/5)
  - Next phase items
- Commit with clear message: "Friday 2.0 system upgrade — [name] integration complete (Jun 11, 2026)"
- Push to main branch

**Output:** Documentation live on GitHub

**Example from Jun 11:** INTEGRATION_COMPLETE.md + MAINTENANCE_LOG.md + CHECKPOINT_INTEGRATION_GUIDE.md

### Phase 5: Runtime Activation (30 min)

**Input:** Code + documentation in repo

**Process:**
1. Load the new module into sys.path
2. Create integration wrapper instance (e.g., CheckpointIntegration)
3. Call activation method (e.g., `on_session_start()`) to wire into session lifecycle
4. Verify metadata (expect specific outputs — 609 bytes restored, status operational, etc.)

**Output:** New system live in agent runtime

**Example from Jun 11:**
```python
from checkpoint_manager import CheckpointManager
from checkpoint_integration import CheckpointIntegration

integration = CheckpointIntegration()
result = integration.on_session_start()
# Expected: restored 609 bytes, status operational
```

### Phase 6: Verification & Diagnostics (30 min)

**Input:** Running system

**Process:**
1. **Small tests** (5 quick checks):
   - Checkpoint restore
   - Credential vault access
   - Skill loading
   - Memory file integrity
   - Hindsight database
2. **Full diagnostics** (8 categories):
   - Infrastructure status
   - Credential coverage
   - Memory system
   - Skill performance
   - Runtime state
   - Quality metrics
   - Integration checklist (10/10)
   - System grade

**Expected result:** All 5 small tests pass, all 8 diagnostic categories green, integration checklist 10/10, grade A (5.0/5)

**Output:** Diagnostics report confirming production readiness

## Workflow Diagram

```
Design → Build & Test → Orchestrated Validation → Push to Repo → Activate → Verify
(30min)   (1-2h)         (1-2h, parallel)         (30min)         (30min)   (30min)
         ✓ 4/4 tests    ✓ 9/9 tests              ✓ INTEGRATION_   ✓ on_session ✓ Grade A
                         ✓ All 3 reports          COMPLETE.md      _start()    ✓ 10/10
                         ✓ Parallel saves 2h                       called      checklist
```

**Total time: 4–6 hours (with parallelization)**

## Integration Patterns

### Lifecycle Hook Pattern
Most Friday 2.0 upgrades expose 3 lifecycle hooks:

```python
class Integration:
    def on_session_start(self):
        """Load/restore at session start"""
        pass
    
    def on_session_end(self, context=None):
        """Capture/save at session end"""
        pass
    
    def on_hourly_maintenance(self):
        """Scheduled cleanup/optimization"""
        pass
```

Wire them into session init/cleanup code.

### Checklist-Based Validation
Post-integration validation should be **checklist-driven**, not narrative. After activation, verify:

- [ ] Module loaded without errors
- [ ] on_session_start() callable and returns expected metadata
- [ ] on_session_end() callable and creates timestamped artifact
- [ ] on_hourly_maintenance() callable and completes without errors
- [ ] Credential vault still accessible (no breakage)
- [ ] Skill directory still scannable (no bloat regression)
- [ ] Memory layer responds (no I/O errors)
- [ ] Hindsight database queryable (no corruption)
- [ ] Vault isolation maintained (no credential leakage)
- [ ] Runtime state reflects new system (e.g., "3 checkpoints saved")

If all 10 pass → **integration complete, production ready**.

## Success Metrics

An upgrade is successful if:

1. **Code quality** — All unit tests pass (9/9 or better)
2. **Integration fidelity** — All orchestrated validation tasks pass (3/3 reports)
3. **Documentation** — INTEGRATION_COMPLETE.md with 10-item checklist, all passing
4. **Runtime activation** — Module loads, lifecycle hooks callable, session_start restores context
5. **Diagnostics** — Final grade A (5.0/5) across all 5 categories

**Anything less than A warrants troubleshooting before calling it "done".**

## Common Pitfalls

### Pitfall 1: Sequential Validation Instead of Parallel
**Problem:** Running validation tasks one at a time → takes 4 hours instead of 2

**Fix:** Use subagent orchestrator with 3 consolidated tasks (code integration, credential verification, memory integration). Save 2 hours.

### Pitfall 2: Skipping Repository Documentation
**Problem:** Code is integrated but README/checklist is missing → future agent doesn't know what was done

**Fix:** Always push INTEGRATION_COMPLETE.md with metrics and checklist before calling integration "done".

### Pitfall 3: Not Wiring Lifecycle Hooks into Session Code
**Problem:** on_session_start() and on_session_end() exist but aren't called → upgrade doesn't actually activate

**Fix:** Add explicit calls to session init/cleanup. Verify they run with `print()` or logging.

### Pitfall 4: Diagnostics Return < Grade A
**Problem:** After activation, diagnostics show B+ or B → there's still a blocker

**Fix:** Don't declare integration complete. Run small tests to isolate failure, fix it, re-run diagnostics. Loop until A.

### Pitfall 5: Environment-Dependent Failures
**Problem:** Capture all transient errors ("apt-get install failed", "network timeout") as persistent blockers

**Fix:** Distinguish:
- **Transient** (env setup, network hiccup, missing binary) → fix and retry, don't encode as skill
- **Durable** (design flaw, API mismatch, data corruption) → encode as pitfall + fix in skill

## Files & Support Materials

- `references/runtime-integration-workflow.md` — Detailed integration checklist and lifecycle hooks
- `scripts/verify-integration.py` — Runnable diagnostic script (small tests + full diagnostics)
- `templates/INTEGRATION_COMPLETE.md` — Template for post-integration documentation

## Status

✓ Templated June 11, 2026 (based on checkpoint persistence upgrade)
✓ Successfully deployed once (checkpoint persistence integration)
✓ Ready for reuse on future Friday 2.0 upgrades

## References & Related Skills

- `session-checkpoint-persistence` — First real-world deployment of this pattern (Jun 11, 2026)
- `credential-management-tanzim` — Architecture that integrates via this pattern
- `friday-2-0-architecture` (future) — High-level Friday 2.0 design and roadmap
