---
name: instagram-data-consolidation-pattern-analysis
title: Instagram Data Consolidation & Pattern Analysis at Scale
description: >
  Consolidate Instagram handles from multiple sources into a unified dataset,
  then analyze for demographic and behavioral patterns. Handles quota limits,
  batch operations, demo validation, and real data analysis workflows.
triggers:
  - Consolidating Instagram data from multiple sheets
  - Building pattern analysis frameworks for Instagram accounts
  - Analyzing demographic signals at scale (handles >500)
  - Designing crawl prioritization based on account patterns
---

## Overview

This skill governs **data consolidation + analysis workflows** for Instagram datasets. The workflow has three phases:

1. **Consolidation** — Deduplicate handles from N sources into a single source-of-truth sheet
2. **Pattern Framework** — Define metrics and expected patterns that predict good outcomes
3. **Analysis** — Populate metrics for all handles, then prioritize based on patterns

The class includes quota management (Instagram API rate-limiting), Google Sheets batch operations, and a **demo-validation pattern** to test the framework before committing to full analysis.

---

## Phase 1: Consolidation

### Input
- Multiple existing Instagram sheets (location data, follower lists, target lists, chat extractions, etc.)
- Goal: deduplicate and create a master "Consolidated Handles" tab

### Process

1. **Identify all Instagram sheets** in the user's Google Drive (use `gspread.oauth()` to list)
   - Look for sheets with "Instagram", "IG", "followers", "targets", "handles" in the name
   - Scan actual sheet tabs for Instagram-relevant columns (handle, username, etc.)

2. **Extract handles with deduplication**
   - Regex to match Instagram handles: `^[a-zA-Z0-9._-]+$` (alphanumeric, dots, underscores, hyphens only)
   - Case-insensitive dedup (Instagram handles are case-insensitive)
   - Track source sheet for each handle (useful for provenance later)

3. **Create "Consolidated Handles" tab**
   - Columns: `Handle` (primary), `Source_Sheets` (comma-separated), `Crawl_Status` (pending/enriched/crawled)
   - Load all deduplicated handles
   - Sort alphabetically for readability

### Gotchas
- **Google Sheets quota**: Reading multiple sheets in a single session can hit rate limits. Batch reads are safer than individual `worksheet.get_all_values()` calls.
- **Dedup logic**: Instagram allows handles with dots, underscores, hyphens. Don't over-sanitize.
- **Source tracking**: Include which original sheets each handle came from — useful for comparing results across sources later.

---

## Phase 2: Pattern Framework

### Input
- Consolidated Handles tab with N handles
- A hypothesis about what account characteristics predict good outcomes (e.g., "micro accounts with strong female signals convert better")

### Process

1. **Define 6–8 metrics** that proxy for your hypothesis
   - Each metric should be measurable from a public Instagram profile
   - Examples: `Followers_Estimate` (micro/mid/macro), `Follower_Velocity` (growth speed), `Account_Age_Estimate` (maturity), `Bio_Signal_Strength` (authenticity), `Business_Likelihood`, `Female_Score_Predicted`

2. **Create "Pattern Recognition" tab** in the same sheet
   - Top section: **Metric Definitions**
     - What it measures
     - Range of values
     - Strategic objective (why this metric matters)
     - Pattern insight (what combinations work)
     - Priority rating (★ scale)
   - Middle section: **Expected High-Performing Patterns** (6–10 combinations you predict will convert well)
     - Example: "PATTERN 1 (GOLD): micro + fast_growth + female_score≥3 + bio≥5 → 65-75% conversion"
     - Describe each pattern's characteristics, expected ROI, and the reasoning
   - Bottom section: **Analysis Checkpoint** (status tracker for when analysis runs)

3. **Document the scoring logic**
   - If female_score is weighted (pronouns 3pts, gender nouns 2pts, etc.), write it clearly
   - If business-likelihood uses heuristics (specific keywords, account type), document them
   - Future sessions need to understand the scoring to interpret results

---

## Phase 3: Analysis (With Rate-Limit Awareness)

### The Rate-Limiting Reality
Instagram's public API is rate-limited. Fetching real data for >500 handles will hit quota walls:
- **Timeout**: Instagram returns 429 (rate limit) after ~100–200 requests
- **Quota reset**: typically 1 hour, but varies
- **Safe batch size**: 10–50 handles per batch, with 3–5 sec delays between requests, 30 sec between batches

### Option A: Demo Mode (Fast, For Validation)
Use **synthetic/realistic data** to populate the first 50 handles:
- Immediately shows the analysis framework works end-to-end
- Validates that metrics flow into sheets correctly
- Allows crawl prioritization testing without waiting 2+ hours
- **When to choose**: User is time-constrained, or wants to validate the pattern framework first

**Implementation**:
- Create `run_pattern_analysis_demo.py` that generates realistic (not random) synthetic data
- Cycle through the expected patterns (PATTERN 1, PATTERN 2, etc.) so distribution is realistic
- Update the Consolidated Handles sheet with demo data for first 50 handles
- Print summary of pattern distribution

### Option B: Full Analysis (Slow, For Real Data)
Fetch actual Instagram profile data for all handles:
- Takes ~2 hours for 1,975 handles
- Requires quota management (batch + delays)
- More accurate for final prioritization
- **When to choose**: Ready to commit to real data, or only a subset of handles

**Implementation**:
- Create `run_pattern_analysis.py` with quota-safe batching
- Fetch each handle's profile via Instagram's public HTML (no API key needed)
- Parse bio, follower count, recent post count, posting frequency for the metrics
- Update sheet in batches (Google Sheets batch_update API, not individual updates)
- Log progress (handles processed, batches completed, errors)

### Critical: Google Sheets Batch Operations
**DO NOT use individual `ws.update()` calls** — they are slow and fail with validation errors.

**DO use `batch_update()`** with a list of dicts:
```python
updates = []
for i, handle in enumerate(sample_handles):
    row_num = i + 2
    updates.append({
        'range': f'D{row_num}:I{row_num}',
        'values': [[val1, val2, val3, val4, val5, val6]]
    })
ws.batch_update(updates)
```

This is 10–50x faster and avoids 400 validation errors.

---

## Workflow Decision Tree

**User asks to analyze consolidated handles:**

1. **How many handles?**
   - <100: Use Option A (demo), then Option B if needed
   - 100–500: Offer both; default to Option A unless user specifically requests real data
   - >500: Offer both; warn that Option B takes 1–2+ hours

2. **Is the pattern framework already defined?**
   - No: Create the Pattern Recognition tab first (metrics + expected patterns)
   - Yes: Jump to analysis

3. **User says "analyze" without specifying A or B?**
   - Ask: "Option A (demo, ~5 min, synthetic data) or Option B (full analysis, ~2 hours, real Instagram data)?"
   - If user says B: warn about rate-limiting and total time
   - If user then says "stop" or "do A instead": kill the process immediately, run demo

4. **After analysis completes:**
   - Show pattern distribution (how many handles match PATTERN 1, PATTERN 2, etc.)
   - Identify which handles are highest-priority for crawling
   - Suggest next action (run crawler on top N handles, measure conversion, compare to expected rates)

---

## Implementation Checklist

- [ ] Consolidate handles from all source sheets (deduplicate, track sources)
- [ ] Create "Consolidated Handles" tab with Handle, Source_Sheets, Crawl_Status columns
- [ ] Create "Pattern Recognition" tab with metric definitions and expected patterns
- [ ] Decide: Option A (demo) or Option B (full analysis)?
- [ ] If Option A: Create `run_pattern_analysis_demo.py`, populate 50 handles with synthetic data
- [ ] If Option B: Create `run_pattern_analysis.py` with quota-safe batching, run in background
- [ ] Use `batch_update()` for Google Sheets, NOT individual `update()` calls
- [ ] Commit to GitHub with version bump and clear description
- [ ] Show pattern distribution and next action to user

---

## References
- See `references/google-sheets-batch-operations.md` for batch_update patterns and common errors
- See `references/instagram-rate-limiting.md` for quota limits, safe batch sizes, and workarounds
- See `templates/pattern-analysis-framework.md` for a boilerplate Pattern Recognition tab structure

