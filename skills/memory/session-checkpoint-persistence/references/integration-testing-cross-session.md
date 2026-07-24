# Session Checkpoint Persistence Integration Testing

**Tested:** June 11, 2026 (System diagnostics)

## Scenario: Cross-Session Memory Persistence

### Setup

1. **Session A (creation):**
   - User asks: "Check how to de-dupe memory"
   - Context loaded: Veronica audit results, credential management architecture
   - Memory grows: ~9,200 bytes of operational notes
   - Session ends at 12:24:43 UTC

2. **Session B (recovery):**
   - User asks: "Review conversation and update skills"
   - Expected: Memory from Session A is restored automatically
   - Actual: Memory starts at 0 bytes (fresh session)

### Issue & Lesson

**Observation:** Checkpoint manager works (can capture/restore manually) but **not integrated into session lifecycle**. No code currently calls:
- `capture_checkpoint()` at session end
- `load_checkpoint()` at session start

**Root cause:** Session lifecycle is external (handled by Hermes runtime, not visible to Claude inside the session). Agent cannot hook session boundaries directly.

**Workaround:** Explicit checkpoint calls by user or operator:
```bash
# At session end, user runs:
python ~/.hermes/checkpoint_manager.py --capture --session-id "session_12345"

# At session start, explicitly load:
python ~/.hermes/checkpoint_manager.py --load
```

Or: Wrap in a launcher script that handles lifecycle.

### Integration Checklist

- [ ] Session start hook: Load checkpoint before any prompts
- [ ] Session end hook: Capture checkpoint before exit
- [ ] Hourly cron: Prune old checkpoints (30-day retention)
- [ ] User command: `checkpoint restore <session-id>` to load specific checkpoint
- [ ] User command: `checkpoint list` to see recent snapshots
- [ ] Launcher script: `hermes-session-with-checkpoint.sh` that wraps session start/end

### Test Pass (Manual)

1. Start session, load checkpoint manually:
   ```python
   manager = CheckpointManager()
   result = manager.load_checkpoint()
   # → {"success": True, "restored_bytes": 0, "session_id": "...", "captured_at": "2026-06-11T12:24:43"}
   ```

2. Work in session (add notes to Memory)

3. End session, capture checkpoint:
   ```python
   manager = CheckpointManager()
   checkpoint = manager.capture_checkpoint("session_20260611_122443", context={"tokens_used": 150000})
   # → /home/hermes/.hermes/checkpoints/checkpoint_20260611_122443_00b6b24a.json
   ```

4. Start new session, verify load:
   ```python
   manager = CheckpointManager()
   result = manager.load_checkpoint()
   # → {"success": True, "restored_bytes": 9200, ...}
   ```

**Status:** ✓ Manual test pass, ✓ Needs lifecycle integration

## Next Steps

1. Create launcher script (`scripts/session-with-checkpoint.sh`) that:
   - Checks for most recent checkpoint
   - Loads it into Memory before spawning session
   - Captures checkpoint after session exits

2. Update integration points in session startup code (outside Claude's scope, requires Hermes runtime changes)

3. Schedule hourly pruning cron job

## Reference Dates

- Implemented: June 11, 2026
- Tested: June 11, 2026
- Integration: Pending (requires Hermes runtime hook)
