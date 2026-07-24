# Friday 2.0 Infrastructure Fixes — Example Sequence

**Context:** Multi-stage fix for Friday 2.0 after diagnostics identified 3 critical + 2 high-priority issues across 3 infrastructure layers (EDITH vault, Personal Framework, JARVIS personality).

## Task Prioritization (Pattern)

| Task | Title | Hours | Priority | Blocker | Status |
|------|-------|-------|----------|---------|--------|
| 1 | EDITH UUID Recovery | 2 | 🔴 CRITICAL | Vault inaccessible | In Progress |
| 2 | JARVIS Accuracy Calibration | 10 | 🔴 CRITICAL | Personality checker broken | Blocked on Task 1 |
| 3 | Framework Minor Fixes | 0.5 | 🟡 HIGH | Missing metric + float boundary | Ready |
| 4 | EDITH Security Hardening | 3 | 🟡 HIGH | Rate limiting, plaintext map | Ready |
| 5 | Memory Safety | 2 | 🟠 MEDIUM | Lazy decryption, context mgr | Ready |

**Delivery order:** 1 → 2 → 3 → 4 → 5 (critical blockers first, then high-priority, then best-practices).

## TASK 1 Subtask Breakdown (EDITH UUID Recovery)

### TASK 1.1: Create recovery.json
- **What:** Create metadata file tracking original UUID vs. current system UUID
- **File:** `~/.hermes/.edith/recovery.json`
- **Contains:** original_uuid, current_uuid, recovery_methods, migration_status
- **Permissions:** 0o600
- **Verification:** File exists, readable, contains both UUIDs

### TASK 1.2: Add UUID override parameter
- **What:** Allow vault to decrypt with original UUID (recovery mode)
- **File:** `~/friday-2.0/edith.py` (EDITHVault.__init__)
- **Change:** Add `override_uuid: str = None` parameter
- **Logic:** If override_uuid provided, use it for encryption/obfuscation engines
- **Logging:** Log recovery attempt to access.log
- **Verification:** Parameter accepted, logged, doesn't break normal init

### TASK 1.3: Implement migration functions
- **What:** Move vault from old hardware UUID to new hardware UUID
- **Methods to add:**
  - `migrate_to_hardware_uuid(target_uuid=None)`: decrypt all → re-encrypt → save
  - `_save_metadata()`: persist updated metadata.json
  - `_update_recovery_status(status, uuid)`: track migration in recovery.json
- **Process:**
  1. Create new EncryptionEngine with target UUID
  2. Decrypt all credentials with original UUID
  3. Re-encrypt with new UUID
  4. Update metadata (migration timestamp, old→new UUID)
  5. Persist vault.enc + metadata.json
  6. Update recovery.json
  7. Reinitialize vault with new UUID
- **Verification:** All steps succeed, no data loss, audit trail in access.log

### TASK 1.4: Test recovery components
- **What:** Verify recovery.json, UUID override, and migration function exist
- **Tests:**
  1. recovery.json readable + contains correct UUIDs
  2. Vault accepts override_uuid parameter
  3. migrate_to_hardware_uuid() method callable
  4. Vault decrypts (may fail due to UUID mismatch — expected)
- **Expected outcome:** All structural tests pass; vault inaccessible (as expected) because vault.enc was encrypted with 244019394735095 but system is on 238817333662082

## Key Implementation Details

**UUID Mismatch Problem:**
- Vault created on: 244019394735095
- Current system UUID: 238817333662082
- EncryptionEngine uses hardware UUID to derive Fernet key
- Cannot decrypt without original UUID

**Recovery Solution:**
1. Store original UUID in recovery.json (created at 1.1)
2. Allow override_uuid parameter to use original UUID (added at 1.2)
3. Migrate function re-encrypts all creds with new UUID (added at 1.3)
4. User runs: `vault = EDITHVault(override_uuid='244019394735095'); vault.migrate_to_hardware_uuid()`

**Testing Limitations:**
- Cannot fully test migration without actually triggering UUID mismatch and running migration
- Structural tests (file exists, method callable) pass
- Functional test (actual decryption) will fail until migration is explicitly triggered by user

## Files Modified

| File | Changes | Lines |
|------|---------|-------|
| `~/.hermes/.edith/recovery.json` | NEW | Full file |
| `~/friday-2.0/edith.py` | `__init__`: added override_uuid parameter | 281 |
| `~/friday-2.0/edith.py` | `migrate_to_hardware_uuid()` + helpers | 592–684 |

## Timing
- Total: 2 hours (estimated 2 hours, actual 2 hours)
- Breakdown: 1.1 (20 min) → 1.2 (30 min) → 1.3 (50 min) → 1.4 (20 min)

## Next Task (TASK 2)
- **Name:** JARVIS Personality Checker Accuracy Calibration
- **Hours:** 10
- **Blocker:** Personality detection at 14.2/100 accuracy (96.9% misclassified as "Poor")
- **Root cause:** Keyword-only detection misses implicit patterns
- **Solution:** Semantic pattern library + scoring recalibration
