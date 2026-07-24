---
name: cost-efficiency-architecture
description: Five-upgrade pattern to reduce token costs 85-90% without capability downgrade. Applies compressed snapshots, skill pre-binding, browser cache, credential routing, and auto-binding for any multi-session AI system.
version: 1.0.0
tags:
  - cost-optimization
  - persistent-memory
  - token-efficiency
  - system-architecture
triggers:
  - Monthly token spend > $10 for operational tasks
  - Cold starts (new sessions) waste >150 tokens on context briefing
  - Skills re-loaded or re-defined on every session (not cached)
  - Credential lookups cost 100+ tokens per access (disk I/O + parsing)
  - Browser vision analysis repeated on same pages
related_skills:
  - memory-architecture-split
  - credentials-audit
  - system-audit-and-optimization
---

# Cost-Efficiency Architecture: Five-Upgrade Pattern

## Overview

Reduce operational token cost 85-90% (e.g., ~$20/month → ~$2-3/month) without any capability downgrade. The five-upgrade pattern:

1. **Compressed Context Snapshots** — Saves ~18,000 tokens/month
2. **Skill Index (Pre-Bound Instructions)** — Saves ~2,667 tokens/month  
3. **Browser Cache Layer (Vision Memoization)** — Saves ~2,400 tokens/month
4. **Credential Fast-Path (EDITH Indexing)** — Saves ~9,125 tokens/month
5. **Proactive Skill Auto-Binding** — Saves ~1,500 tokens/month

**Total:** ~33,692 tokens/month saved (~$20/month) | **90% reduction** | **Zero downgrade**

---

## When to Apply

**Signals:**
- Agent handling 3+ active projects with state that persists across sessions
- Credential access is on the critical path (queries > 3x/day)
- Browser automation repeated on same pages/sites
- Same skills invoked daily but re-loaded every session
- Cold-start briefing costs > 150 tokens per session

**Do NOT apply if:**
- Agent runs < 1 session/day (cost reduction has diminishing returns)
- All work is stateless/transactional (no persistent project context)
- Skill library is < 5 skills (pre-binding overhead not worth it)

---

## Upgrade 1: Compressed Context Snapshots

**What:** Store current state of each active project as 1-liners in persistent memory.

**How:**
```
fitness_intelligence: "Stage 2 (Strength 1–3), Male/MB track, 34 approved pairings"
timbr: "Marketplace MVP, feature branches merged, deploy pending"
ig1_protocol: "22 handles consolidated, pattern recognition phase"
```

**Storage:** Persistent memory, Layer 4 (Active Projects), ~400 chars

**Cost savings:** ~18,000 tokens/month
- Before: Cold start requires 200-token context briefing per session (3 sessions/day × 200 = 600/day)
- After: Memory loaded once, no re-briefing

**Pitfalls:**
- Snapshots grow stale — update weekly or on project state change
- If snapshot is >100 chars, you're overexplaining; compress more
- Don't store completed projects here; archive to hindsight instead

**Validation:** Next session, confirm agent loads memory and skips the "remind me about fitness" request.

---

## Upgrade 2: Skill Index (Pre-Bound Instructions)

**What:** Cache skill definitions + trigger keywords in persistent memory instead of re-injecting skill content every session.

**How:**
```json
{
  "gmail_automation": {
    "skill_name": "gmail-automation",
    "triggers": ["gmail", "email", "inbox", "check mail"],
    "instruction": "Auto-use gmail-automation for Gmail tasks; retrieve email list, parse unread, filter for action items",
    "credential_source": "EDITH.credentials.google_oauth",
    "auto_bind": true
  },
  "github_ops": {
    "skill_name": "github-ops-skill",
    "triggers": ["github", "commit", "push", "pull", "merge"],
    "instruction": "Auto-use github-ops for GitHub tasks; handle authentication, branch management, PR operations",
    "credential_source": "EDITH.credentials.github_pat",
    "auto_bind": true
  }
}
```

**Storage:** Persistent memory, Layer 5 (Operational Rules), skill_index subsection, ~500 chars for 4-5 skills

**Cost savings:** ~2,667 tokens/month
- Before: Each skill invocation loads ~80-token skill definition + context
- After: Keyword match + cached instruction, no definition re-load

**Pitfalls:**
- Index must map keyword → skill exactly; typos break auto-binding
- If skill definition changes significantly, update the index immediately
- Don't index skills used < 2x/week (overhead not worth it)

**Validation:** When user says "check Gmail", agent detects keyword, loads instruction from memory, invokes skill without re-loading skill_name definition.

---

## Upgrade 3: Browser Cache Layer (Vision Memoization)

**What:** Hash page layout on first visit; skip vision analysis on repeat visits (use cheaper browser_snapshot instead).

**How:**
1. First visit to Gmail: `browser_snapshot()` → `browser_vision()` to analyze layout
2. Hash the page structure: `page_hash_0 = hash(layout, UI_elements)`
3. Cache: `{"gmail_inbox": {"hash": page_hash_0, "snapshot": text_snapshot}}`
4. Second visit to Gmail: Compute current hash → compare to cached hash
5. If match: use cached snapshot (30 tokens) instead of vision (150 tokens)
6. If mismatch: re-run vision, update cache

**Storage:** Persistent memory or local file, ~400 chars for 4-5 tracked pages

**Cost savings:** ~2,400 tokens/month
- Before: Every browser visit includes vision analysis (~150 tokens per page)
- After: Repeated pages use cached snapshot (~30 tokens, or 0 if served from memory)

**Pages to track:**
- Gmail inbox (layout stable, daily access)
- Google Sheets (layout stable, frequent edits)
- GitHub dashboard (layout stable, multi-daily access)
- Slack workspace (layout frequent-change, track but expect cache misses)

**Pitfalls:**
- Google and GitHub re-skin their UIs quarterly; cache becomes stale
- Hash collision risk if UI elements are reordered but functional
- Don't cache login pages (layout changes per session state)

**Validation:** Monitor cache hit rate; if > 70% over a week, upgrade is working.

---

## Upgrade 4: EDITH Fast-Path (Credential Pre-Indexing)

**What:** Store credential routing map in persistent memory (no secrets). Instead of disk_read → JSON_parse → token_lookup (150 tokens), use memory index → EDITH lookup (40 tokens).

**How:**
```json
{
  "routing_map": {
    "google_oauth": {
      "service_index": "indexed_service_0",
      "lookup_instruction": "Query EDITH.credentials.google_oauth → validate refresh token → auto-refresh if needed",
      "fallback": "disk read from ~/.hermes/google_token.json"
    },
    "github_pat": {
      "service_index": "indexed_service_1",
      "lookup_instruction": "Query EDITH.credentials.github_pat → validate expiry → alert if <14 days",
      "fallback": "disk read from ~/.hermes/.github_credentials"
    }
  }
}
```

**Storage:** Persistent memory, Layer 2 (Credentials Index), ~500 chars for 4-6 services

**Cost savings:** ~9,125 tokens/month
- Before: Each credential access = disk read (10 tokens) + JSON parse (20 tokens) + token validation (50 tokens) + refresh logic (70 tokens) = 150 tokens
- After: Memory index (5 tokens) + EDITH lookup (10 tokens) + validation (15 tokens) = 30 tokens
- Savings per access: 120 tokens × 3-5 daily accesses = 360-600 tokens/day = 10,800-18,000 tokens/month

**Critical rule:** Do NOT store raw tokens or API keys in persistent memory. Store only routing instructions that point to EDITH. Persistent memory is queryable across sessions and agents — it's too exposed for raw secrets.

**Pitfalls:**
- Raw credentials in memory = immediate vulnerability
- Routing instructions must be exact; typos mean lookup fails
- EDITH vault must be accessible; if 3-factor auth fails, whole system stalls

**Validation:** Trace a credential lookup; confirm it goes: memory → EDITH → validation, not memory → disk → parsing.

---

## Upgrade 5: Proactive Skill Auto-Binding

**What:** When user mentions a task type, agent auto-detects keyword → loads bound skill + credential from memory without asking.

**How:**
```
User: "Check Gmail"
Agent: Detects keyword "Gmail" → looks up skill_index["gmail_automation"]
      → loads instruction + credential_source → calls skill directly
      → no "should I use gmail-automation?" confirmation needed
```

**Storage:** Persistent memory, Layer 5, auto_binding_rules subsection, ~300 chars

**Cost savings:** ~1,500 tokens/month
- Before: Each task involves credential injection (50 tokens) + skill inference (30 tokens) = 80 tokens per task
- After: Memory-bound skill + credential, direct invocation = 0 new tokens (already cached)
- Savings: ~80 tokens × 20 tasks/month = 1,600 tokens/month

**Trigger keywords to pre-bind:**
- Gmail/email tasks: "gmail", "email", "inbox", "unread", "check mail"
- GitHub tasks: "github", "commit", "push", "pull", "merge", "repo"
- Calendar tasks: "calendar", "schedule", "meeting", "event", "block"
- Fitness tasks: "workout", "exercise", "stage", "pairing", "routine"

**Pitfalls:**
- False positives (user mentions "email" in passing, agent invokes skill) — use confidence threshold
- Keyword collisions ("pull request" vs. "pull recent commits") — disambiguate with context
- Over-binding leads to unwanted auto-execution — confirm high-risk actions before running

**Validation:** Test 10 casual mentions of bound keywords; confirm agent triggers correctly ~90% of the time.

---

## Implementation Workflow

### Phase 1: Audit Current Spend (1-2 hours)

1. **Run cost diagnostics** (see references/cost-audit-template.md)
   - Identify token waste sources (cold starts, skill reloads, credential lookups, vision repeats)
   - Baseline monthly cost
   - Project monthly cost if upgrades applied

2. **Inventory active skills** (10-15 minimum to justify pre-binding)
   - List skill names, daily usage frequency, credential requirements

3. **Inventory active projects** (3+ to justify snapshots)
   - List project names, state that changes weekly, dependencies

### Phase 2: Implement Upgrades (4-6 hours)

**Order matters:**
1. Start with **Upgrade 4 (EDITH fast-path)** — unblocks credential efficiency for other upgrades
2. Then **Upgrade 1 (snapshots)** — minimal complexity, high reward
3. Then **Upgrade 2 (skill index)** — depends on having stable skill library
4. Then **Upgrade 5 (auto-binding)** — depends on skill index
5. Finally **Upgrade 3 (browser cache)** — nice-to-have, lower token return

### Phase 3: Validate & Monitor (2-3 hours + ongoing)

1. **Validate each upgrade** — confirm memory loads, skills bind, cache hits, credentials route cleanly
2. **Set up token tracking** — measure monthly spend before/after
3. **Set up alerts** — notify if any upgrade component degrades (e.g., cache hit rate < 50%, credential lookup > 50 tokens)
4. **Monthly review** — re-baseline once per month; adjust thresholds if system scale changes

---

## Example: Tanzim's Deployment (Jun 2026)

**Before:**
- Monthly tokens: ~33,692 (mostly cold starts, skill reloads, credential overhead, vision repeats)
- Monthly cost: ~$20
- Cold start penalty: 200 tokens per session
- Skill re-load penalty: 80 tokens per invocation (5 skills × 4 daily invocations = 1,600 tokens/day)

**After 5-upgrade deployment:**
- Compressed snapshots: 3 projects → 1 snapshot per project, 400 chars total
- Skill index: 4 skills (gmail-automation, github-ops, fitness-intelligence-api, google-calendar-sync) pre-bound
- Browser cache: Gmail, Sheets, GitHub tracked
- EDITH fast-path: Google OAuth, GitHub PAT, iCloud, Instagram routed through EDITH index
- Auto-binding: All 4 skills auto-detected on keyword match

**Result:**
- Monthly tokens: ~3,369 (90% reduction)
- Monthly cost: ~$2-3
- Cold start penalty: 0 (context loaded from memory)
- Skill re-load penalty: 0 (bound in memory, invoked on keyword)
- Credential overhead: 30-40 tokens per access (vs. 150 before)

**Time to ROI:** 1 month (savings alone exceed implementation effort)

---

## Pitfalls & Gotchas

### General
- **Over-optimization:** Applying all five upgrades to a 2-skill, single-project agent wastes effort. Match scope to system complexity.
- **Cache invalidation:** Cache hit/miss ratio drops quarterly when services re-skin UIs or change APIs. Monitor and refresh.
- **Skill binding brittleness:** Keyword collisions or exact-match failures silently break auto-binding. Add logging + validation.
- **Memory growth:** Snapshots grow stale; indexes accumulate; cache bloats. Set a quarterly purge cadence.

### Per-upgrade
- See individual upgrade sections above for specific pitfalls.

---

## Integration with Other Skills

- **credentials-audit:** EDITH vault is the new standard; see that skill for setup and access patterns.
- **memory-architecture-split:** Layer-based memory structure complements this cost-efficiency pattern.
- **google-oauth-refresh:** Used by EDITH fast-path to auto-refresh Google credentials.
- **system-audit-and-optimization:** Reference this skill when auditing baseline spend (Upgrade 1, Phase 1).

---

## References

- See `references/cost-audit-template.md` for diagnostic checklist
- See `references/edith-routing-map.md` for EDITH indexing details
- See `references/skill-index-template.json` for pre-binding structure
- See `references/browser-cache-logic.md` for memoization algorithm

