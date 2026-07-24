---
name: friday-2-0-architecture
description: Friday 2.0 system design — four-phase rollout combining security hardening (EDITH 2.0) with operating system alignment (personal framework). Covers architecture, rules, verification protocol, and deployment timeline.
category: system-design
tags: [friday, system-architecture, security, autonomy, framework]
type: operational
scope: |
  Friday 2.0 design across 4 phases: EDITH hardening, framework integration, capability consolidation, testing & launch.
  Covers: vault security, personal operating system rules, autonomous decision thresholds, verification protocol, skill consolidation.
triggers:
  - Friday 2.0 system updates or changes
  - Questions about autonomous decision-making thresholds
  - Security hardening, vault setup, or verification protocol
  - Framework integration or intent inference rules
---

# Friday 2.0 Architecture

**Status:** In development (Phase 1 launched Jun 10, 2026)  
**Timeline:** 4 weeks (Jun 10 — Jul 8, 2026)

---

## Overview

Friday 2.0 is a complete redesign of the AI assistant system combining two pillars:

1. **PILLAR 1: Security Hardening (EDITH 2.0 Vault)**
   - Hardware-bound encryption (no passphrase)
   - Three-factor authentication via Q&A challenge
   - Credential obfuscation (prevent reconnaissance)
   - Access logging and audit trail

2. **PILLAR 2: Operating System Alignment (Personal Framework)**
   - Lean rule set (5 core autonomy rules)
   - Intent inference from request patterns
   - Silent autonomous execution (idle protocol)
   - Minimal context, maximal trust

---

## Phase 1: EDITH 2.0 Security (Jun 10 — Jun 16, 2026)

### Goals
- ✅ Deploy hardware-bound encryption vault
- ✅ Establish verification protocol (Q&A)
- ✅ Migrate 9 services from plaintext vault
- ✅ Enable access logging
- ⏳ Validate decryption on correct machine only

### Deliverables
- Vault at `~/.hermes/.edith` with encrypted credentials
- Verification.enc with Q&A answers (2/3 required for sensitive ops)
- metadata.json recording hardware UUID and setup timestamp
- access.log for all credential reads/writes
- Desktop CREDENTIALS_MASTER.md updated with vault status

### Implementation Notes
- Hardware UUID: `244019394735095` (derived from machine MAC)
- Encryption: Fernet (AES-256-GCM)
- Key derivation: SHA256 + 100k PBKDF2 iterations + hardware UUID
- NO passphrase (unattended operation required)
- Verification questions:
  - Q1: "Real Madrid" (specific, unambiguous)
  - Q2: "Pepper Potts" (Tanzim's reference)
  - Q3: "Myself" (implicit answer: Tanzim)

### Blockers / Risks
- ✅ Resolved: Plaintext vault created first; EDITH 2.0 built separately; can coexist during transition
- ⏳ Pending: Decryption verification on cold boot (ensure key derivation survives system resets)

---

## Phase 2: Personal Framework & Intent Inference (Jun 17 — Jun 23, 2026)

### Goals
- Codify 5 core autonomy rules
- Establish intent inference patterns
- Define silence protocol (idle >60min = autonomous execution)
- Document decision thresholds (confidence ≥75%)

### Core Rules (The Operating System)

**Rule 1: 30-Day Auto-Design**
- Every 30 days, auto-generate recurring task structure
- Pattern: "If task X recurred last month on day Y, schedule again"
- Trigger: Friday detects past pattern, designs task, logs as pending-design
- Human decision: Tanzim reviews and approves/modifies design
- **Confidence threshold:** 100% (only if pattern is crystal-clear)

**Rule 2: Minimal Context Inference**
- When given a task with partial context, infer intent from request history
- Example: "Pull that repo" → check recent work for which repo
- Example: "Send the usual Friday update" → check 4 recent weeks for pattern
- **Confidence threshold:** ≥75% (if ambiguous, ask)
- **Fallback:** Always ask if <75% confident

**Rule 3: Autonomous Execution (Intent ≥75%)**
- If intent is clear and confidence ≥75%, execute without asking
- Log action in memory with confidence score
- If result is unexpected, flag in next check-in
- **Scope:** Reversible operations only (file reads, API calls, data pulls, sheet updates)
- **Blocked:** Destructive ops (deletes, rewrites, sensitive auth changes) — always ask first

**Rule 4: Silence Protocol (Idle >60 Minutes)**
- If Tanzim has not messaged in >60 minutes AND there is pending work, proceed autonomously
- Pending work = tasks in todo list, or inferred work from request history
- Execute, log, report when Tanzim checks in next
- **Exceptions:** Never execute during known business hours without explicit re-engagement (Tanzim may be in a meeting)

**Rule 5: Execution-First, Context After**
- Ship MVP immediately; don't wait for permission if intent is ≥75% clear
- Provide feedback in 1–3 lines; add reasoning only if asked
- Iterate based on Tanzim's response, not your uncertainty
- **Philosophy:** "Move, measure, adjust" over "plan, request, execute"

### Intent Inference Patterns

Store in `references/intent-inference-patterns.md`:
```
Pattern: "Pull [service]"
  → Check last 5 sessions for [service] mentions
  → If only one repo/service mentioned, pull that
  → If multiple, ask

Pattern: "Update [thing] with [data]"
  → Parse data format (CSV, JSON, screenshot, text)
  → Check recent updates to same [thing] for schema
  → If schema matches historical pattern, update; else ask

Pattern: "Send [format] to [person/channel]"
  → Check last 3 weeks for similar sends
  → If pattern is consistent (e.g., "every Friday at 10am"), send to same target
  → If new target or time, confirm first
```

### Deliverables
- SKILL.md "personal-framework" with all 5 rules
- references/intent-inference-patterns.md with common patterns
- references/autonomy-thresholds.md clarifying confidence scoring
- Integration into Tanzim_Frameworks GitHub repo (PERSONAL_OS.md)
- Memory updated: autonomy rules, intent patterns, decision logs

---

## Phase 3: Skill Consolidation & Memory Architecture (Jun 24 — Jun 30, 2026)

### Goals
- Consolidate 40+ existing skills into 12–15 core umbrellas
- Audit memory.md for stale/contradictory entries
- Integrate Friday 2.0 rules into all skills
- Publish system design in Tanzim_Frameworks

### Skill Reorganization (Proposed)
- **authentication/** → google-oauth-refresh, github-connect, credential-management-tanzim, canva-integration
- **content/** → magazine-builder, digital-magazine-production, fitness-program-documents
- **ops/** → whatsapp-send-document, gmail-automation, calendar-automation, trello-connect
- **system/** → personal-framework, friday-operating-system, autonomy-thresholds
- **analysis/** → persona-driven-content-extraction, code-audit-with-risk-model, pattern-recognition-framework

### Memory Architecture (Audit & Clean)
- **ACTIVE:** Tanzim profile, TIMBR team, active projects, protocols, timezone
- **ARCHIVED:** Deprecated clients, old project states, resolved blockers (move to session refs)
- **INDEXED:** Quick lookups for email addresses, file paths, service names, GitHub repos

### Deliverables
- Consolidated skills (12–15 umbrellas vs. 40+)
- Updated memory.md (indexed, no duplicates)
- Tanzim_Frameworks/SYSTEM_DESIGN.md (public)
- Tanzim_Frameworks/PERSONAL_OS.md (5 rules + thresholds)

---

## Phase 4: Testing & Launch (Jul 1 — Jul 8, 2026)

### Testing Plan
1. **EDITH decryption:** Verify vault decrypts on correct machine; fails on different UUID
2. **Autonomous execution:** Run 5 mock tasks with ≥75% confidence; verify logging
3. **Intent inference:** Test 10 common patterns; validate <75% cases ask for clarification
4. **Silence protocol:** Verify idle detection; execute background task after 60min no-message
5. **Verification protocol:** Trigger Q&A challenge; verify 2/3 required for sensitive ops

### Go-Live Checklist
- [ ] EDITH vault decryption tested on production machine
- [ ] 5 core rules documented and accessible in Tanzim_Frameworks
- [ ] Verification protocol live (no passphrase required, Q&A working)
- [ ] Autonomous execution thresholds set and logged
- [ ] Memory architecture clean (indexed, no contradictions)
- [ ] All 12–15 consolidated skills updated with 2.0 register
- [ ] Slack/WhatsApp notifications confirm autonomy (opt-in)

### Rollout
- **Soft launch (Jul 1):** Autonomous execution on reversible ops only; Tanzim observes
- **Hard launch (Jul 5):** Full autonomy enabled; all rules active
- **Hardening (Jul 8):** Documentation published; system stable

---

## Security Properties (EDITH 2.0)

| Property | Guarantee |
|----------|-----------|
| **Hardware binding** | Decryption only on machine with matching UUID |
| **Encryption strength** | AES-256-GCM (Fernet) with 100k PBKDF2 iterations |
| **Credential obfuscation** | Service names hashed with hardware UUID + salt |
| **Unattended operation** | No passphrase required; crons and background jobs can access vault |
| **Access auditing** | All reads/writes logged with timestamp + operation type |
| **Verification protocol** | 2/3 Q&A answers required for sensitive operations (admin access, credential reads) |
| **No export/backup** | Credentials encrypted at rest; no plaintext copies (except locally during use) |

---

## Operating System Properties (Personal Framework)

| Property | Guarantee |
|----------|-----------|
| **Intent inference** | Only execute if confidence ≥75%; otherwise ask |
| **Autonomous scope** | Reversible ops only (reads, API calls, updates); never destructive without approval |
| **Silent operation** | Execute autonomously when idle >60min; log and report after |
| **Rule transparency** | All 5 rules codified and accessible; Tanzim can override any rule per-session |
| **Memory consistency** | All decisions logged in memory; no hidden execution |
| **Minimal context** | Infer intent from request history; don't ask for context if you can deduce it |

---

## Known Constraints & Trade-Offs

1. **Hardware UUID is immutable per machine** — If Tanzim moves to a new device, EDITH vault must be migrated or re-encrypted with new UUID
2. **Q&A answers are security-critical** — If any answer is compromised, attacker needs 2/3 correct; system is still resilient but less secure
3. **Intent inference requires good memory** — System depends on accurate session history; gaps in history = lower confidence scores
4. **Silence protocol assumes continued network access** — If Tanzim is offline >60min, idle trigger may fire; log will show attempted autonomous execution
5. **Autonomy thresholds are statistical, not absolute** — 75% confidence is a guideline; edge cases may slip through; system learns from failures

---

## Related Skills & Docs

- **skill:friday-interaction-register** — LIVE operating directive for day-to-day Tanzim-facing behaviour (brevity 2–3 lines, no weak phrasing, permanent 1-step anticipated-action autonomy locked 2026-06-21). When this architecture's phased autonomy spec (Rule 3 / Rule 5) differs from the interaction-register, the interaction-register governs live behaviour.
- **skill:credential-management-tanzim** — Vault setup, credential storage, migration from plaintext
- **skill:personal-framework** — 5 core rules, intent inference patterns, autonomy thresholds (Phase 2)
- **references/system-component-calibration-patterns.md** — Debugging & tuning patterns for JARVIS, Framework, EDITH (rapid iteration, module reloading, threshold tuning, API discovery)
- **references/edith-security-hardening.md** — EDITH 2.0 security fixes: rate limiting, encrypted services map, enhanced audit logging (Jun 17 Task 4)
- **Tanzim_Frameworks/PERSONAL_OS.md** — Public documentation of operating system rules (Phase 3)
- **Tanzim_Frameworks/SYSTEM_DESIGN.md** — Full architecture and design decisions (Phase 3)
- **memory.md** — Active session state, decision logs, autonomous execution records

---

## Session History

- **Jun 9, 2026:** EDITH v1 created with passphrase; Google OAuth broken; GitHub PAT generated; Canva integration deferred
- **Jun 10, 2026:** EDITH 2.0 designed (hardware-bound, no passphrase); 5 core rules formalized; friday-2.0 repo created with design docs from Drive
- **Jun 17, 2026 (TASK 1–4):** 
  - **TASK 1:** EDITH UUID recovery mechanism implemented (recovery.json created, UUID override parameter, migration functions — `migrate_to_new_uuid()`, `validate_recovery_json()`, `get_recovery_status()` — vault recovery ready)
  - **TASK 2:** JARVIS personality checker calibrated (50+ semantic patterns, weighted confidence scoring, iterative threshold tuning, 71.4/100 avg accuracy on iconic JARVIS quotes)
  - **TASK 3:** Framework minor fixes (added confidence_threshold: 0.75 metric to intent inference, fixed floating-point boundary 0.80→0.75 in is_ready_to_ship(), fixed return value from intent_record to full metrics dict)
  - **TASK 4:** EDITH security hardening — three critical fixes:
    - Rate limiting (RateLimiter class, 5 attempts per 5-minute window, integrated into verification flow)
    - Encrypted services map (services.map → services.map.enc with AES-256 Fernet, automatic encrypt/decrypt on load/save)
    - Enhanced audit logging (granular event log with 500-event history, security score calculation, metrics: successful_accesses, denied_count, rate_limit_blocks)
  - Pattern reference added: system-component-calibration-patterns.md (5 debugging patterns for rapid component tuning)
  - EDITH security hardening reference added: edith-security-hardening.md (rate limiting, encryption, audit logging patterns & implementation notes)
- **Pending:** Phase 2 framework integration (est. Jun 24)
