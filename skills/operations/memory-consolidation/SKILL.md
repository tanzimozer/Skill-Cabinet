---
name: memory-consolidation
description: "Workflow for deduplicating and consolidating large, noisy memory systems (Hindsight) into clean, semantic tiers without data loss."
version: 1.0.0
tags: [memory, consolidation, dedup, hindsight, optimization]
---

# Memory Consolidation

Workflow for reducing memory bloat in Hindsight (append-only, unlimited storage) while preserving all unique facts and maintaining operational continuity.

## When to Consolidate

- Hindsight entry count > 50 with suspected 60%+ duplication rate
- Memory lookups becoming slow (~6,000 tokens per recall)
- Multiple near-identical entries on the same topic (e.g., 5 variations of \"X rule\")
- User requests organization before archival or version control

## Pre-Consolidation Audit

1. **Sample recall** — run a test query and count returned entries
2. **Estimate noise** — scan for duplicate patterns:
   - Identical entries verbatim
   - Near-duplicates with slight wording differences (same fact, restated 3+ times)
   - Stale entries (resolved blockers, one-time events marked as historical)
   - Process logs, status updates, dated announcements
3. **Identify clusters** — group entries by topic/semantic area:
   - Security issues (codeword leaks, vulnerability patches)
   - System architecture (three-tier structure, capacity)
   - Project status (current + archived)
   - Team/process rules (collaboration, communication style)
   - Optimization history (cost changes, config updates)
4. **Verify critical facts** — spot-check that all unique, irreplaceable facts are captured and will survive

## Consolidation Steps

### Step 1: Semantic Grouping
Organize all entries by topic. Each cluster should collapse to **one authoritative entry** containing:
- The richest version of the fact (most detail, latest update)
- All unique sub-facts from the cluster merged into it
- Dates and version history if relevant
- Any caveats or context from the original entries

**Example cluster:**
- Entry A: "THETA codeword was leaked in Hindsight on May 30, 2026."
- Entry B: "THETA was changed to DELTA 08:47:51 UTC, entries flagged as compromised."
- Entry C: "3am gardener job monitors flagged entries. SOUL.md already contains DELTA."

Consolidates to:
- "THETA codeword was leaked in ~50+ Hindsight entries on May 30, 2026. Changed to DELTA 08:47:51 UTC. Entries flagged as compromised/stale (append-only DB, cannot delete); 3am gardener job monitors. SOUL.md already contains DELTA. Core memory never stored old codeword."

### Step 2: Size Estimate

Count consolidated entries and estimate total character size:
- Typical consolidated entry: 250–450 chars
- Expect 60–80% reduction from original if pre-consolidation noise is 70%+

Example:
- Before: 57 entries, ~14,159 chars, 70% estimated noise
- After: 11 entries, ~3,853 chars (73% reduction)

### Step 3: Re-seeding into Hindsight

Use `hindsight_retain()` for each consolidated entry with:
- **content** — the consolidated fact
- **context** — semantic topic (e.g., "Security — Codeword Management")
- **tags** — list of keywords for recall (e.g., `["security", "codeword", "theta", "delta"]`)

Do NOT delete old entries (append-only constraint). New consolidated entries will rank higher in recall because they are richer and more recent.

### Step 4: Verification

After re-seeding:
1. Run a test recall on a key topic to confirm consolidated entries appear first
2. Spot-check 3–5 specific facts to ensure they survived intact
3. Document final count and size reduction

## Output Format

Create a consolidated memory document (e.g., `memory.md`) with:
1. Header with dates, entry counts before/after, % reduction
2. Each consolidated topic as a numbered section with title and content
3. Summary table (original vs. final, metrics)
4. Readiness statement (e.g., \"Ready for GitHub push\")

Example structure:
```markdown
# Friday Memory (Consolidated) — June 5, 2026

**Consolidation complete:** 57 entries → 11 consolidated topics. Total size: **3,853 characters** (72.8% reduction).

## 1. Topic Name
[content]

## 2. Topic Name
[content]

...

| Metric | Before | After | Change |
|--------|--------|-------|--------|
| Hindsight entries | 57 | 11 | -80% |
| Total size | 14,159 chars | 3,853 chars | -72.8% |
| Unique facts preserved | ~40 | 40 | 100% |
```

## Pitfalls to Avoid

- **Don't delete old entries.** Hindsight is append-only; deletion violates the contract. Flag stale entries; rely on new consolidated entries to rank higher in recall.
- **Don't merge contradictory facts.** If two entries disagree on a date or value, keep both versions in the consolidated entry with a note (e.g., "Originally stated as X on [date], updated to Y on [date]").
- **Don't lose context.** If an entry includes a job ID, file path, or specific config, preserve it in the consolidated version.
- **Don't assume 100% dedup rate.** Some noise may be intentional (e.g., multiple descriptions of the same rule for different contexts). Only consolidate genuinely redundant entries.
- **Don't skip the size estimate.** Estimate BEFORE re-seeding so you can report the reduction to the user.

## Session Reference

**June 5, 2026:** First full consolidation pass on Tanzim's memory. Consolidated 57 Hindsight entries + 14.1k MEMORY.md into 11 consolidated topics + 3.9k markdown output. Preserved 40+ unique facts, removed 70% noise. See `references/consolidation-jun5-2026.md` for the actual output.
