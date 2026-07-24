# Protocol Distinction: Veronica vs. IG-1

## Critical Confusion Point (Jun 6, 2026)

User established **Protocol Veronica** as a general deployment standard. This was incorrectly conflated in hindsight with **IG-1 Protocol**, which is an Instagram-specific crawler. They are entirely separate.

## Protocol Veronica

**Type:** Deployment standard (generic, reusable)  
**Purpose:** Template for running complex/high-stakes tasks with maximum capability and quality assurance  
**Components:**
1. Claude Opus model (primary task execution)
2. 2–3 subagents in parallel (if needed for scale/isolation)
3. Two-level quality check (review layer 1, then review layer 2)

**Invocation:** User says "deploy veronica"  
**Execution:** Immediate, no preamble. Full protocol as stated.  
**Use case:** Task complexity warrants model upgrade, work parallelization, or high confidence threshold needed.

### Hindsight Storage (Correct)
```
Protocol Veronica — DISTINCT FROM IG-1 Protocol

Deployment standard for complex/high-stakes tasks:
1. Deploy latest Claude Opus model for primary task execution
2. Deploy 2–3 subagents in parallel if needed to scale work or isolate concerns
3. Two-level quality check at task end by default (review layer 1, then review layer 2)

Use case: task complexity warrants model upgrade, work parallelization, or high confidence threshold needed.

Execution: When user says "deploy veronica", execute immediately without preamble, confirmation menu, or options. Full protocol runs as stated above.

DO NOT CONFUSE with IG-1 Protocol (Instagram crawler) — they are separate operational protocols.
```

Tags: `["protocol-veronica-ONLY", "opus-subagent-qc", "not-ig1", "distinct-protocol", "execution-immediate"]`

## IG-1 Protocol

**Type:** Crawler specification (domain-specific)  
**Purpose:** Large-scale Instagram scraping for account discovery  
**Components:**
- HTML profile scraping (2–4 seconds per profile)
- City-by-city sequential sweep (Melbourne, Sydney, London, Tallinn, Seattle, LA, Dallas, etc.)
- Follower count filtering (500–3,500 range)
- Female-identifying account detection

**Invocation:** Not a "deploy" protocol — specific task with parameters  
**Execution:** Background crawler with auto-save and completion notification  
**Repository:** `tanzimozer/ig-1-protocol` on GitHub

### Hindsight Storage (Correct)
```
IG-1 Protocol — DISTINCT FROM Protocol Veronica

Large-scale Instagram scraping deployment across multiple cities (Melbourne, Sydney, London, Tallinn, etc.) targeting female fitness accounts with 500–3,500 followers using HTML profile scraping, hashtag sweeps, and parallel crawlers.

GitHub repo: tanzimozer/ig-1-protocol
Deployment: Sequential city-by-city sweep with HTML scraping (no subagents in the crawler itself).

DO NOT CONFUSE with Protocol Veronica (Opus + subagent QC standard) — they are separate operational protocols.
```

Tags: `["ig1-protocol-ONLY", "instagram-crawler", "not-veronica", "distinct-protocol", "html-scrape"]`

## Why The Mix-Up Happened

1. Both were named "Veronica" initially (IG-1 was formerly "Protocol Veronica")
2. IG-1 was renamed on Jun 5, 2026 to avoid confusion
3. Protocol Veronica (the general deployment standard) was created Jun 6, 2026
4. Hindsight still had tangled entries from the IG-1 scraper work that mentioned "Veronica"
5. When asked "Did you understand Protocol Veronica?", I claimed yes without searching hindsight — a direct violation of the verification rule

## The Fix

Both protocols are now stored in hindsight with:
- Explicit "DISTINCT FROM" language in the body
- "NOT-[other]" tags to prevent search bleed
- Separate context tags (one for deployment standard, one for crawler)
- Explicit reference in the body to prevent future confusion

**Never search for "Protocol Veronica" and assume the first result is the general deployment standard.** Always check the tags and context.
