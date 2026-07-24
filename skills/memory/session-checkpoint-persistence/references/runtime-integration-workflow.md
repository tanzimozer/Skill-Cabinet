# Runtime Integration Workflow — Session Checkpoint Persistence

**Date:** June 11, 2026  
**Agent:** Hermes (Friday 2.0)  
**Status:** Deployed and operational

## The Five-Step Integration Pattern

This is the tested workflow for deploying checkpoint persistence from repository code into a live agent runtime.

### Step 1: Build & Unit Test
- Create `checkpoint_manager.py` with four core methods: `capture_checkpoint()`, `load_checkpoint()`, `list_checkpoints()`, `prune_old_checkpoints()`
- Test each method in isolation with synthetic Memory state (capture/load cycle)
- Verify data integrity — byte-for-byte restoration
- **Target:** 4/4 methods passing, zero dependencies outside stdlib
- **Time:** ~30 min

### Step 2: Validate with Orchestration (Subagent Pattern)
Deploy 3 parallel subagents with consolidated tasks. This is faster than sequential validation:

**Task 1 — Code Extraction & Integration**
- Pull checkpoint_manager.py from repository
- Create CheckpointIntegration wrapper with lifecycle hooks (on_session_start, on_session_end, on_hourly_maintenance)
- Create test suite (capture/load cycle, error handling, edge cases)
- Run tests: expect 9/9 passing
- **Deliverable:** checkpoint_integration.py (tested, ready to load)

**Task 2 — Credential & Infrastructure Verification**
- Verify vault.json has `google_token_file`, `github_token`, `github_account` indexed at top level
- Check all 7 credential services (Google, GitHub, iCloud, Instagram, Webflow, Wix, Canva)
- Validate skill directory state: 83 categories, 311 skills, ~11 MB (after cleanup)
- Verify directory pruning: 6 empty categories removed, 4.4 MB freed
- **Deliverable:** VAULT_VERIFICATION_REPORT.md + confirmed O(1) credential access

**Task 3 — Three-Layer Memory Integration Test**
- Phase 1: Write test data to Memory layer (4 entries + 3 user profile entries)
- Phase 2: Verify Hindsight indexing (3/3 entries searchable)
- Phase 3: Confirm Vault isolation (zero credential leakage)
- Phase 4: Hindsight recall across session boundary (100% accuracy)
- Phase 5: Cross-session persistence (simulate 3 session boundaries, 100% survival)
- **Deliverable:** THREE_LAYER_MEMORY_INTEGRATION_TEST_REPORT.md + 9 test files passing 100%

**Parallel execution saves ~2 hours vs sequential validation.**

### Step 3: Push to Repository
- Create `INTEGRATION_COMPLETE.md` documenting:
  - All 10 checklist items (CheckpointManager, CheckpointIntegration, lifecycle hooks, credentials, memory, skills, runtime)
  - Metrics (311 skills, 7 services, 609 bytes restored, etc.)
  - Next phase items (cron jobs, Hindsight prefetch, etc.)
- Commit with clear message: "Friday 2.0 runtime integration complete (Jun 11, 2026)"
- Push to main branch
- **Verification:** INTEGRATION_COMPLETE.md now live on GitHub

### Step 4: Activate Lifecycle Hooks
- Load CheckpointManager into sys.path
- Create CheckpointIntegration instance
- Call `on_session_start()` — should restore prior Memory (expect 600+ bytes if prior session exists)
- Verify `get_status()` returns `{"status": "operational", ...}`
- Wire into session initialization so next chat auto-restores Memory
- **Expected result:** Memory restored, context carries forward, 0 user action required

### Step 5: Small Test + Recheck
Run quick validation suite (5 tests):
1. Session checkpoint restore — expect 609 bytes or "fresh start" if first session
2. Credential vault access — expect 3/3 critical tokens present (github_token, github_account, google_token_file)
3. Skill directory loading — expect 311 skills, 83 categories
4. Memory file integrity — expect Memory.md exists with session data
5. Hindsight database — expect database exists and is queryable

Then run full diagnostics:
- Infrastructure status (7 files/dirs checked)
- Credential coverage (7/7 services)
- Memory system (3 checkpoints saved)
- Skill performance (83 categories, 311 skills, 10.9 MB)
- Runtime state (session ID, memory loaded, checkpoints accessible, credentials accessible, skills ready)
- Quality metrics (100% efficiency, 100% credential coverage, -4.4 MB bloat removed)
- Integration checklist (10/10 items complete)
- **Expected final grade: A (5.0/5)**

## Lifecycle Hook Implementation

### on_session_start()
```python
def on_session_start(self, session_id=None):
    """Load checkpoint at session start"""
    result = self.manager.load_checkpoint(session_id)
    if result['success']:
        # Memory was restored from prior session
        return result
    else:
        # No prior checkpoint — fresh start
        return result
```

**When:** Call this at the very beginning of a new chat session, BEFORE any tasks execute.

**Effect:** Restores the Memory.md from the end of the previous session. User context, active projects, team info, and interview schedules carry forward automatically.

**Failure mode:** If no checkpoint exists, load_checkpoint() returns `{"success": False, "reason": "No checkpoint available"}` — this is normal for the first session.

### on_session_end()
```python
def on_session_end(self, session_id=None, context=None):
    """Capture checkpoint at session end"""
    result = self.manager.capture_checkpoint(session_id, context)
    # Checkpoint is now saved to ~/.hermes/checkpoints/checkpoint_<timestamp>.json
    return result
```

**When:** Call this at the END of a session, after all user tasks are complete but before the session terminates.

**Effect:** Snapshots the current Memory.md to a timestamped JSON checkpoint file. The checkpoint includes session metadata (tokens used, duration, etc.).

**Critical:** If you don't call this, the session's Memory is lost when the session ends.

### on_hourly_maintenance()
```python
def on_hourly_maintenance(self):
    """Run hourly maintenance"""
    return self.manager.prune_old_checkpoints()
```

**When:** Schedule this as a cron job, e.g., daily at 00:00 or 06:00 AM.

**Effect:** Deletes checkpoints older than 30 days, keeps index.json up to date, frees disk space.

**No user interaction needed** — runs automatically.

## Expected Metrics After Integration

| Metric | Value | Notes |
|--------|-------|-------|
| Memory restored on session start | 600–5000 bytes | Depends on prior session activity |
| Skill categories active | 83 | Down from 89 (6 empty removed) |
| Total skills | 311 | No change |
| Credential services | 7/7 | All accessible O(1) |
| Checkpoint files saved | 1+ | New one per session |
| Directory pruning | 4.4 MB freed | One-time, already done |
| Integration checklist | 10/10 | All items passing |
| Final system grade | A (5.0/5) | Across 5 categories |

## Pitfalls & Fixes

### Pitfall 1: Memory Starts Blank
**Problem:** After integration, next session doesn't have prior context.

**Cause:** `on_session_start()` not called, or checkpoint restore failed.

**Fix:**
- Verify `~/.hermes/checkpoints/index.json` exists and has entries
- Check that `on_session_start()` is being called before any user tasks
- Test manually: `python -c "from checkpoint_manager import CheckpointManager; m = CheckpointManager(); print(m.load_checkpoint())"`

### Pitfall 2: Checkpoint Restore Returns 0 Bytes
**Problem:** Integration says "restored" but Memory is actually empty.

**Cause:** Prior checkpoint was captured with empty Memory (e.g., first session after cleanup).

**Fix:**
- This is normal. Check `index.json` to see if prior checkpoints have non-zero `memory_snapshot` fields.
- If all checkpoints have zero-byte snapshots, Memory was genuinely empty in all prior sessions.

### Pitfall 3: Vault Lookup Fails
**Problem:** Credentials return `None` instead of token value.

**Cause:** vault.json missing top-level keys like `google_token_file`, `github_token`, `github_account`.

**Fix:**
- Open vault.json and verify these keys exist at the root level (not nested)
- If missing, run: `python -c "import json; v=json.load(open(Path.home()/'/.hermes/vault.json')); v['google_token_file']='/...'; json.dump(v, open(..., 'w'))"`

### Pitfall 4: Skill Loading Slow
**Problem:** Skill directory scan takes >1 second.

**Cause:** Empty skill categories still present (not pruned).

**Fix:**
- Verify skill directory only has 83 categories: `ls ~/.hermes/skills | wc -l`
- If more than 83, prune: `rm -rf ~/.hermes/skills/{.git,.hub,gifs,diagramming,domain,inference-sh,yuanbao}`

### Pitfall 5: CheckpointIntegration Module Not Found
**Problem:** `from checkpoint_integration import CheckpointIntegration` fails.

**Cause:** checkpoint_integration.py not on disk or not in sys.path.

**Fix:**
- Check if file exists: `ls -la ~/.hermes/checkpoint_integration.py`
- If missing, create it from the integration wrapper in the repository
- Ensure `sys.path.insert(0, str(Path.home() / '.hermes'))` is called before import

## Testing Checklist

Before declaring integration complete, verify:

- [ ] Small test #1: Checkpoint restore loads 600+ bytes (or "fresh start" msg)
- [ ] Small test #2: Vault access returns github_token, github_account, google_token_file
- [ ] Small test #3: Skills load — 311 skills across 83 categories
- [ ] Small test #4: Memory file exists with session data
- [ ] Small test #5: Hindsight database exists (may be 0 MB initially)
- [ ] Full diagnostics: All 7 infrastructure files present
- [ ] Full diagnostics: 7/7 credential services accessible
- [ ] Full diagnostics: 3+ checkpoints saved
- [ ] Full diagnostics: 83 categories, 311 skills, 10.9 MB
- [ ] Full diagnostics: 10/10 integration checklist items passing
- [ ] Full diagnostics: System grade A (5.0/5)

If all pass, **integration is complete and ready for production.**

## Post-Integration Steps (June 12+)

- [ ] Set up hourly cron job for `on_hourly_maintenance()` (de-dupe + pruning)
- [ ] Implement Hindsight prefetch on session start (Veronica recommendation, Phase 2)
- [ ] Add ElevenLabs speech-to-speech integration (Tanzim requested)
- [ ] Configure Slack bot token (missing from vault)

---

**Deployed by:** Hermes Agent  
**For:** Tanzim Ozer  
**Session:** June 11, 2026  
**Status:** ✓ Operational
