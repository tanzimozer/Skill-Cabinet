---
name: cryptographic-system-audit
author: claude-code
description: >
  Comprehensive security audits for cryptographic systems (vaults, key derivation,
  encryption schemes, authentication protocols). Measures encryption/decryption latency,
  validates verification logic, tests collision resistance, audits access logging,
  and identifies performance bottlenecks and security gaps.
usage: >
  Use when auditing cryptographic credential stores, encryption implementations,
  or key management systems that need:
  - Encryption/decryption performance measurement (latency, throughput)
  - Verification protocol validation (MFA logic, 3/3 enforcement, etc.)
  - Obfuscation/hashing uniqueness testing (collision resistance, determinism)
  - Access audit trail validation and completeness assessment
  - Security gap identification (weak algorithms, missing controls, RAM exposure)
  - Compliance assessment (SOC2, HIPAA, PCI-DSS, GDPR)
  - Hardware binding and recovery mechanism analysis
tags: [security, cryptography, audit, performance-testing, compliance]
---

# Cryptographic System Audit

## Core Workflow

### Phase 1: System Discovery & Metadata (30 min)
- Locate vault/config files and document structure
- Identify cryptographic algorithms in use (encryption, KDF, hashing)
- Map all security-sensitive components (keys, credentials, logs, audit trails)
- Verify metadata integrity (version, timestamps, hardware binding)
- Document hardware/software dependencies (MAC address, UUID, OS)

### Phase 2: Encryption/Decryption Performance Measurement (45 min)
- Measure encryption latency across payload sizes (small, medium, large)
- Measure decryption latency with same payloads
- Calculate mean, median, std dev, min/max per category
- Measure key derivation overhead (if applicable)
- Test with clean/warm caches to separate initialization from per-op cost
- **Success criteria:** <100ms per operation for real-world payloads

**Measurement checklist:**
- [ ] Test at least 3 distinct payload sizes
- [ ] At least 10 iterations per size (for statistical significance)
- [ ] Record timing in milliseconds with 3+ decimal precision
- [ ] Calculate descriptive statistics (mean, median, std dev, min, max)
- [ ] Document any outliers or timing anomalies
- [ ] Estimate throughput (ops/sec) for single core
- [ ] Identify if bottleneck is cryptographic or architectural (key derivation, I/O, etc.)

### Phase 3: Verification Protocol Robustness (45 min)
- Document all security questions or challenge mechanisms
- Test answer verification logic (case sensitivity, whitespace handling, encoding)
- Validate answer encryption/decryption roundtrip correctness
- Confirm 3/3 enforcement (or whatever requirement exists)
- Test answer uniqueness (no duplicates, no weak patterns)
- Check for brute-force vulnerability (rate limiting, attempt limits)
- Identify MFA strength (Q&A weak, TOTP medium, WebAuthn strong)

**Verification test template:**
```python
# 1. Load verification questions
questions = load_questions()
assert len(questions) >= 3, "Need at least 3 questions"

# 2. Test case-insensitive matching
answer = "Real Madrid"
assert verify_answer("real madrid", answer), "Should match case-insensitive"

# 3. Test whitespace handling
assert verify_answer("  Real Madrid  ", answer), "Should strip whitespace"

# 4. Test answer uniqueness
answers = [q['answer'] for q in questions]
assert len(answers) == len(set(answers)), "All answers must be unique"

# 5. Test encryption roundtrip
encrypted = encrypt_answer("correct")
decrypted = decrypt_answer(encrypted)
assert decrypted == "correct", "Encryption/decryption must be lossless"

# 6. Test 3/3 requirement
correct_count = sum(1 for q in questions if verify(user_answer[i], q['answer']))
assert correct_count == 3, "All 3 must be correct to unlock"
```

### Phase 4: Obfuscation Uniqueness & Collision Testing (45 min)
- Generate obfuscated keys for 10+ distinct inputs
- Verify all outputs are unique (zero collisions in test set)
- Calculate theoretical collision probability from algorithm
- Test hardware/environment dependency (same input → same key on same hardware)
- Test determinism (key generation is reproducible)
- Verify enumeration resistance (attacker cannot guess obfuscated keys)
- Document collision space (e.g., "48-bit space for <1000 items")

**Collision resistance checklist:**
- [ ] Generate N keys from distinct service names (N ≥ 10)
- [ ] Verify all N are unique (set size == list size)
- [ ] Calculate theoretical collision space (e.g., 2^48 for 12 hex chars)
- [ ] Apply birthday paradox formula: P(collision) ≈ N²/2^k
- [ ] Document acceptable risk threshold (typically <2^-32 for <1000 items)
- [ ] Test with different hardware UUIDs to confirm environment binding
- [ ] Test same input multiple times to confirm determinism

### Phase 5: Access Logging & Audit Trail Validation (45 min)
- Verify log file exists at expected location
- Check file permissions (should be 0o600 or similar)
- Test logging on successful access/authentication
- Test logging on failed attempts (wrong password, incorrect answer, etc.)
- Verify timestamp recording (created, last_accessed, per-operation)
- Assess log granularity:
  - ✅ Detailed: Individual operation records with service name, user, timestamp
  - ⚠️ Aggregated: Only counters (total accesses, failed attempts)
  - ❌ Missing: No audit trail at all
- Evaluate compliance against SOC2, HIPAA, PCI-DSS requirements

**Audit logging test:**
```python
# 1. Perform authenticated operation
vault.get_credential('service')

# 2. Verify log entry created
log = vault.get_access_log()
assert log['access_count'] > 0, "Access should be logged"

# 3. Verify failure tracking
vault.verify_challenge(['wrong', 'wrong', 'wrong'])
assert log['failed_attempts'] > 0, "Failed auth should be logged"

# 4. Check granularity
if 'operations' in log:
    print("✅ Detailed audit trail (individual records)")
else:
    print("⚠️ Aggregated statistics only (no per-operation detail)")
```

### Phase 6: Security Gap Analysis & Threat Modeling (60 min)
Systematically check for weaknesses:

**Algorithm Choices:**
- KDF: PBKDF2 (acceptable but GPU/ASIC vulnerable) vs. Argon2 (better) vs. bcrypt/scrypt
- Encryption: Fernet/AES-GCM (good), AES-CBC (requires auth layer), DES (broken)
- Hashing: SHA256 (good), SHA1 (weak), MD5 (broken)
- Authentication: Q&A (weak), TOTP (medium), WebAuthn (strong), MFA layering

**Key Management Vulnerabilities:**
- [ ] Hardware binding fragility (MAC address changes → vault locked)
- [ ] Key derivation overhead (blocking startup)
- [ ] Fixed salt (reduces entropy)
- [ ] Master key in memory (plaintext exposure)
- [ ] No key rotation/expiration mechanism

**Data Exposure Vulnerabilities:**
- [ ] Plaintext credentials in RAM (memory dump risk)
- [ ] Credentials decrypted all-at-once vs. on-demand (lazy decryption)
- [ ] No secure erasure (plaintext remains after use)
- [ ] Sensitive metadata plaintext (services.map reveals stored services)
- [ ] Log files unencrypted (audit trail readable by unauthorized users)

**Authentication & Authorization Gaps:**
- [ ] No rate limiting on verification attempts (brute-force)
- [ ] No account lockout after N failures
- [ ] No exponential backoff (makes brute-force easier)
- [ ] Weak MFA (Q&A susceptible to social engineering)
- [ ] No time-based component (TOTP) or hardware binding (WebAuthn)
- [ ] No multi-person approval for sensitive operations

**Operational & Recovery Issues:**
- [ ] No recovery mechanism for hardware UUID changes
- [ ] No backup encrypted vault
- [ ] No recovery codes or master recovery key
- [ ] No hardware UUID rotation capability
- [ ] Single point of failure (vault file loss = total credential loss)

**Compliance Gaps:**
- SOC2 Type II: Requires per-operation audit trail (user, timestamp, service, action)
- HIPAA: Requires user-level access logs for PHI + encryption
- PCI-DSS: Requires strong authentication (not just Q&A) + privilege tracking
- GDPR: Requires audit trail for data access + deletion verification

### Phase 7: Documentation & Remediation Planning (90 min)
Create multi-format output:

1. **Quick Reference** (one-page summary)
   - Key metrics (latency, collisions, audit granularity)
   - Critical issues (in 🔴/🟡 format)
   - Top 3-5 recommendations

2. **Executive Summary** (3-5 pages)
   - Findings by severity
   - Compliance assessment
   - Risk/effort matrix for fixes

3. **Technical Deep Dive** (10-20 pages)
   - Algorithm analysis with citations
   - Test results with code examples
   - Detailed threat model
   - Prioritized recommendations with implementation hints

4. **Completion Report** (comprehensive reference)
   - All findings documented
   - Test procedure details
   - Metrics and measurements
   - Performance analysis

5. **JSON Metrics** (machine-readable)
   - All measurements as structured data
   - All issues enumerated
   - Recommendations with priority

6. **Diagnostic Tool** (reusable)
   - Python script or module with all test cases
   - Can be re-run to verify fixes
   - Supports CI/CD integration

7. **Recovery & Remediation Guide**
   - Hardware UUID recovery procedures
   - Key rotation steps
   - Hardware binding migration
   - Incident response playbook

## Severity Levels

- **🔴 CRITICAL:** Vault inaccessible, credentials immediately lost, no recovery possible
  - Hardware UUID mismatch (can't decrypt)
  - Master key lost or corrupted
  - Decryption fails on valid vault

- **🔴 HIGH:** Credentials at immediate risk, attacker path clear, no defense
  - Plaintext credentials in RAM (memory dump)
  - No rate limiting on verification (brute-force 27 combinations possible)
  - Services map plaintext (attacker knows targets)
  - No encryption on plaintext credentials

- **🟡 MEDIUM:** Credentials at risk but with friction, some controls present
  - Weak MFA (Q&A only, not TOTP/WebAuthn)
  - Limited audit trail (aggregated stats, no per-operation records)
  - Hardware UUID stability issue (vault locked on NIC change)
  - No recovery mechanism

- **🟢 LOW:** Code quality or optimization issue, not security-critical
  - Key derivation overhead (7.8ms on startup)
  - JSON rewrite on every log (efficiency issue)
  - Full vault decryption on init (architectural, not algorithmic)

## Compliance Verdict Format

| Standard | Requirement | Current | Gap |
|----------|-------------|---------|-----|
| SOC2 Type II | Per-operation audit trail | Aggregated stats only | User tracking, operation timestamps, service-level detail |
| HIPAA | PHI access logging | No | User identification, detailed access logs, encryption of logs |
| PCI-DSS | Strong authentication | Q&A only | Multi-factor (TOTP/WebAuthn), privilege tracking |
| GDPR | Data access audit | Limited | Complete trail for data access + deletion verification |

**Recommendation language:**
- ✅ READY (meets standard)
- ⚠️ PARTIAL (meets some requirements, gaps present)
- ❌ NOT READY (significant gaps, does not meet standard)

## Common Pitfalls

1. **Skipping hardware-specific testing:** Testing obfuscation on the same hardware always passes. Must test with different UUIDs to verify hardware binding.

2. **Ignoring key derivation overhead:** PBKDF2 cost is O(1) per vault init, not per operation. Don't conflate key derivation latency with encryption latency.

3. **Treating Q&A as strong MFA:** Q&A answers are often guessable (public figures, sports teams) or socially engineered. Always flag as weak if no TOTP/WebAuthn backing.

4. **Missing cascade of failures:** Hardware UUID change doesn't just lock vault — it also prevents key rotation, recovery, and backup restore. Document the full impact chain.

5. **Underestimating memory exposure window:** Plaintext credentials in RAM are vulnerable for entire vault object lifetime. Document exposure duration and what garbage collection doesn't fix.

6. **Confusing compliance "ready" with "hardened":** A system can meet SOC2 audit requirements and still be weak. Always assess both compliance checklist AND threat model.

7. **Forgetting to measure with realistic payloads:** Testing with 100-byte payloads when real credentials are 5+ KB. Measure with actual vault contents.

8. **Missing rate limiting analysis:** Just because rate limiting isn't implemented doesn't mean attacker success is guaranteed. Calculate actual brute-force effort (27 combinations for 3 questions, ~seconds to minutes to guess).

## Output Quality Checklist

- [ ] Encryption/decryption latency measured across 3+ payload sizes
- [ ] Mean, median, std dev, min/max reported for each size
- [ ] Key derivation overhead documented separately
- [ ] Verification protocol test coverage (answer matching, uniqueness, 3/3 logic, encryption roundtrip)
- [ ] Obfuscation collision test: N ≥ 10 unique inputs, zero collisions, theoretical probability calculated
- [ ] Access logging granularity assessed (detailed vs. aggregated vs. missing)
- [ ] Hardware UUID binding tested with different UUIDs
- [ ] All 6 security gap categories checked (algorithms, key management, data exposure, auth, operational, compliance)
- [ ] Issues prioritized by severity (🔴 critical/high, 🟡 medium, 🟢 low)
- [ ] Compliance assessment for SOC2/HIPAA/PCI-DSS/GDPR
- [ ] Recovery/remediation recommendations with implementation hints
- [ ] Multi-format documentation (quick ref, summary, technical, metrics, tool)
- [ ] Risk/effort matrix for staged fixes
- [ ] All sensitive data (keys, credentials, codewords) scrubbed from output

## Success Indicators

✓ Stakeholders understand critical blockers (e.g., hardware UUID mismatch)
✓ Developers can prioritize fixes using severity + effort estimates
✓ Security team can validate threat model independently
✓ Compliance team knows what standards are met vs. failed
✓ Hardware vault recovery procedure documented if applicable
✓ Performance baseline established for regression testing

---

## Support Files

See linked files for:
- **`references/edith-2-0-vault-audit.md`** — Complete session record of EDITH 2.0 vault audit with detailed findings, metrics, critical issues, compliance assessment, and remediation roadmap. Reference for similar cryptographic audits.
- **`scripts/cryptographic-diagnostic-template.py`** — Reusable Python test suite template with classes for encryption latency testing, verification protocol validation, obfuscation collision testing, access logging assessment, and security gap analysis. Adapt to your cryptographic implementation.

---

See also: code-audit-with-risk-model (for general audit structure), security-audit (for Hermes infrastructure)
