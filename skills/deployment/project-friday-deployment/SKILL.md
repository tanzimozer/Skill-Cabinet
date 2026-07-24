---
name: project-friday-deployment
description: "Deployment framework for major Friday architecture updates — 4-phase build pattern with zero-cost capability stacking and quantified thresholds."
version: 1.0.0
tags: [friday, deployment, architecture, framework, zero-cost, build-pattern]
---

# Project Friday Deployment Pattern

Reusable framework for shipping major Friday upgrades. Used for Friday 2.0 (June 2026), extensible for future versions.

## Pattern Overview

**Structure:** 4 sequential phases (EDITH hardening → Framework integration → New capabilities → Go-live). Each phase is a standalone deliverable; phases can run tight but not parallel.

**Estimation:** Minimum realistic time only. No buffer padding. Quote in hours for work <1 week, days for 1-4 weeks, weeks for >4 weeks.

**Communication:** Bill of materials compiled first (full GitHub documentation), then single greenlight triggers all execution. No mid-project approval loops.

## The 4 Phases

### Phase 1: Security Hardening (EDITH Vault)
**Goal:** Centralize all credentials in encrypted, three-factor access control.

**Core deliverables:**
- Encrypted vault (AES-256-GCM at rest)
- Three-factor access: hardware UUID + passphrase (bcrypt-10) + time-window gating (±5 min, 5 min auto-purge)
- Verification questions hashed and stored separately
- Credential inventory (Google OAuth, GitHub PAT, Instagram cookies, iCloud, etc.)
- Token auto-refresh for expiring credentials
- Monthly rotation schedule

**Typical time:** 30 min to 2 hours (depending on how many credentials need migration)

**Definition of done:** 
- Vault loads on session start without user intervention
- All active credentials verified accessible
- Token refresh tested
- Secondary backup in Google Sheet for audit trail

### Phase 2: Personal Framework Integration
**Goal:** Codify decision-making principles into quantifiable operating system rules.

**Core deliverables:**
- 5 explicit rules (30-Day Rule, Minimal Context, Intent Inference, Silence Protocol, Execution-First)
- All thresholds quantified (confidence ≥0.75, pattern matches ≥3, idle >60 min, etc.)
- No hidden inference — all rules published in version-controlled repo
- Confidence scoring system (for Minimal Context rule)
- Pattern matching engine (for Intent Inference rule)
- Silence Protocol automation (60-min idle trigger for autonomous next steps)

**Typical time:** 45 min to 2 hours (depending on complexity of pattern matching logic)

**Definition of done:**
- All 5 rules published to GitHub with thresholds documented
- Confidence scorer operational (returns ≥0.75 for high-confidence inferences)
- Pattern matcher trained on session history (≥3 prior requests to infer intent)
- Silence Protocol active: 60+ min idle → auto-complete next logical step
- No rules remain undocumented or hidden

### Phase 3: New Software Capabilities
**Goal:** Deploy zero-cost tools to unlock new capabilities (browser automation, background jobs, database).

**Core deliverables:**
- **Playwright:** Live DOM inspection, screenshot, dynamic scraping, form filling
- **APScheduler:** Persistent job queue, cron-like scheduling, parallel execution, retry logic
- **SQLite database:** Sub-millisecond queries, ACID transactions, audit logging
- **Integration pipeline:** Trigger → APScheduler → work → SQLite → WhatsApp notification
- End-to-end test (e.g., IG-1 crawl scheduled, executed, stored, reported)

**Typical time:** 1.5 to 4 hours (depends on complexity of integration pipeline)

**Definition of done:**
- All tools installed and verified
- SQLite schema created and tested
- Job queue functional (can schedule, execute, retry, store results)
- WhatsApp notifications triggering on job completion/error
- One full end-to-end test completed successfully

### Phase 4: Testing & Go-Live
**Goal:** Clean up, verify, and ship Friday 2.0 to production.

**Core deliverables:**
- Skill audit (identify active, archived, deprecated; merge duplicates; remove orphans)
- Memory migration (narrative content → Hindsight semantic search; operational data → MEMORY.md)
- EDITH vault verification (fresh session startup: hardware UUID → passphrase → time-window)
- Framework rules live test (all 5 rules firing in real scenarios)
- Full capability stack test (Playwright, APScheduler, SQLite, WhatsApp integration)
- Silence Protocol verification (60-min idle → autonomous next step)

**Typical time:** 1 to 2 hours

**Definition of done:**
- Skills consolidated (27 → 12 active skills; naming standardized)
- Memory cleaned and optimized
- Vault loads without user prompts on session init
- All 5 framework rules verified in live scenarios
- IG-1 crawl runs, results stored in SQLite, completion notified via WhatsApp
- Autonomy active: no manual gates, idle >60 min triggers next step
- Go-live: Friday 2.0 operational

## Key Principles

### 1. Zero-Cost Stack
All tools are open-source, self-hosted, or already owned:
- **EDITH:** Open-source encryption, no SaaS
- **Personal Framework:** Version-controlled, GitHub private repos
- **Playwright:** MIT-licensed, self-hosted browser automation
- **APScheduler:** Apache 2.0, self-hosted job queue
- **SQLite:** Built-in, zero-config
- **Google OAuth / GitHub:** Already authenticated

**Cost:** $0 new infrastructure (Claude Max plan only, existing)

### 2. Quantified Thresholds (No Hidden Inference)
All decision rules must have measurable triggers and thresholds:
- Confidence score ≥0.75 (for Minimal Context)
- Pattern matches ≥3 prior requests (for Intent Inference)
- Idle time >60 minutes (for Silence Protocol)
- Task completion <30 days (for 30-Day Rule)
- MVP ≥60% core requirement (for Execution-First)

These are published, not hidden. Future audits can verify compliance.

### 3. Bill of Materials First, Then Execution
Don't start phases until:
1. Complete bill of materials (all 4 phases documented in GitHub)
2. Full cost breakdown and timeline estimated
3. Single approval/greenlight from user

Then execute without stopping for mid-project confirmation.

### 4. Time Estimation: Minimum Realistic, No Buffer
- Quote the tightest honest estimate, not a safety-padded version
- If 4 phases take 3.5 hours, say "3.5 hours" not "1 week"
- Only use larger time units if genuinely needed
- Assume tight sequencing, not loose project management

## Reuse Checklist

When deploying a major Friday update:
- [ ] Design all 4 phases (security, framework, capabilities, go-live)
- [ ] Document bill of materials in GitHub (Tanzim_Frameworks or relevant repo)
- [ ] Estimate minimum time per phase (hours, days, or weeks)
- [ ] Get single greenlight
- [ ] Execute all 4 phases without stopping
- [ ] Push all code to version-controlled repo
- [ ] Send completion notice via WhatsApp
- [ ] Store master plan in Hindsight for future reference

## Version History

- **1.0.0 (June 8, 2026):** Initial pattern from Friday 2.0 deployment
  - 4-phase structure (EDITH → Framework → Capabilities → Go-Live)
  - Zero-cost capability stack (Playwright, APScheduler, SQLite)
  - Quantified thresholds (confidence ≥0.75, pattern ≥3, idle >60 min)
  - Minimum time estimation (3.5 hours for full Friday 2.0)
  - GitHub documentation + single greenlight pattern

## Related Skills

- `tanzim-communication-style` — How to estimate and deliver to Tanzim (direct, realistic time, no padding)
- `tanzim-framework-schema` (future) — The Personal Framework rules in detail
- `edith-vault-operations` (future) — EDITH vault setup, credential management, rotation
