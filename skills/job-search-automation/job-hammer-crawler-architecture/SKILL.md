---
name: job-hammer-crawler-architecture
description: Multi-source job crawl orchestration—six-phase architecture combining pre-crawl ATS seeds, startup boards, VC companies, accelerators, Indeed direct, and JobSpy aggregation with dedup-by-URL merge pipeline. Generalizes to any multi-source data aggregation task.
type: system-design
category: job-search-automation
triggers:
  - Multi-source job board aggregation
  - Pre-crawl seeding from direct ATS instances
  - Deduplication across job sources
  - CSV merge pipelines
  - Rate-limited API polling
---

# Job Hammer Crawler Architecture

## Overview

A **six-phase orchestrated job crawl system** that pulls from independent sources, merges outputs, deduplicates by URL, and feeds a unified pipeline. Built to maximize candidate supply while maintaining low latency and high dedup accuracy.

The pattern generalizes to any multi-source data aggregation task (not job-specific).

---

## Architecture (Six Phases)

### Phase 1: Pre-Crawl Sources (5 independent crawlers)

Run *before* the main aggregator to capture fresh postings at source.

1. **Seed Companies** (`seed_companies.py`)
   - Direct Workday/Lever/Greenhouse instances from known companies
   - Microsoft, UW, Fred Hutch, regional banks, fitness brands, startups
   - Captures internal postings before syndication
   - Output: `output/seed_companies.csv`

2. **Startup Job Boards** (`startup_jobs.py`)
   - AngelList/Wellfound, startup.jobs, CrunchBoard
   - Early-stage company focus (Series A/B/C)
   - Output: `output/startup_jobs.csv`

3. **Crunchbase VC-Backed Companies** (`crunchbase_vc_crawler.py`)
   - 13+ known VC-backed startups with proven ATS
   - Workday/Lever/Greenhouse direct crawls (Rippling, Mercury, Notion, Airtable, etc.)
   - Series A/B/C/D funded; fintech, ops, data, fitness, healthcare, SaaS verticals
   - Output: `output/crunchbase_vc_jobs.csv`

4. **Accelerator Networks** (`accelerator_crawler.py`)
   - Y Combinator (S24, S23, S13, W10, S09), Techstars, 500 Global, Plug and Play
   - Direct Workday/Lever/Greenhouse crawls of grad companies
   - Proven founders, immediate hiring velocity
   - Output: `output/accelerator_jobs.csv`

5. **Indeed Direct** (`indeed_scraper.py`)
   - Public HTML scrape of Indeed job search (no API key required)
   - Pre-filtered by role + location; 2 pages per search to avoid rate limits
   - Hits Indeed fresh *before* JobSpy crawl (no lag)
   - Output: `output/indeed_jobs.csv`

### Phase 2: Main Aggregator Crawl

6. **JobSpy** (`crawler.py`)
   - Aggregates Indeed + LinkedIn + Glassdoor + Google Jobs + ZipRecruiter
   - Runs *after* pre-crawl sources (avoids redundant polling)
   - Output: `jobs.csv` (replaces any existing file)

### Phase 3: Merge & Deduplicate

**Orchestrator:** `master_crawl.py`

- Reads all 6 source CSVs
- Deduplicates by URL (case-insensitive)
- Tracks dedup rate (% of duplicates removed)
- Outputs net-new unique jobs to `jobs.csv`

**Dedup strategy:**
- Iterate through sources in priority order (JobSpy first, then Phase 1 sources)
- For each row, check if URL already seen
- If seen, skip; if new, add to `seen_urls` set and append to output
- Retains first occurrence of each unique URL

### Phase 4: Filter Pipeline

Deduplicated `jobs.csv` feeds into scout_profile.json scoring:
- Hard exclude keywords (geographic, company blocklist, seniority, work auth)
- Soft boosts (title, company size, industry, experience level, salary band)
- Scores and ranks results
- Syncs to master_tab + individual job tabs via `sync_to_sheet.py`

---

## Filter Configuration (scout_profile.json)

**11 filter stages applied sequentially:**

| Filter | Logic | Effect |
|--------|-------|--------|
| **F1 Location** | Seattle WA, Bellevue, Kirkland, Redmond, Remote | Hard include |
| **F2 Hard Exclude** | 76 companies (Big Tech, Big Finance, Big 4 consulting); keywords (clearance, PhD, on-site, cold-calling, commission) | Hard exclude (one match = drop job) |
| **F3 Seniority Exclude** | 7 regex patterns: intern, director, VP, C-suite, principal, staff, PM | Hard exclude |
| **F4 Title Boost** | Priority (+20): Project Coordinator, Implementation Specialist, Operations Specialist; Wide-net (+10): Support/Onboarding Specialist, Analyst variants | Soft boost (stacks) |
| **F5 Experience** | Early level (entry–2–3yr); max 5yr required | Hard exclude |
| **F6 Salary** | Floor $55k, ceiling $80k; target $70k±15% (+5 boost) | Hard exclude / soft boost |
| **F7 Work Auth** | US Citizen (no sponsorship) | Hard exclude |
| **F8 Company Size** | Startup + scaleup (<2k employees) preference; enforced via blocklist | Soft preference |
| **F9 Industry Boost** | +8 mobile banking/Microsoft/UW/Fred Hutch; +6 fitness/supplement; +5 fintech/wellness/sports/data | Soft boost |
| **F10 Work Model** | Remote-first + on-site OK (or override to fully_remote) | Hard exclude if override set |
| **F11 Recency** | 7-day scrape window, 21-day hard cap; <7d old (+boost) | Hard exclude / soft boost |

**Scoring:** Sort by SCORE descending. Dedup by URL (persistent dedup_index.json). Daily cap: top 50 net-new. Output: CSV → sync_to_sheet.py.

---

## Execution

```bash
cd Stage_1_Crawl
python3 master_crawl.py
```

**Output:**
- Phase 1 crawlers run in sequence (~1–2m total)
- Phase 2 (JobSpy) runs (~3–5m)
- Phase 3 merges + deduplicates
- Phase 4 ready for filter pipeline

**Timing:** ~5–7 minutes total.

**Error handling:** Graceful fallback if any single crawler fails; continues with others.

---

## Key Design Decisions

### Why Pre-Crawl Before JobSpy?

- **Latency:** Direct ATS crawls hit fresh postings before syndication lag
- **Coverage:** Internal postings never make it to job boards; seed crawlers capture them
- **Dedup:** URL-based dedup across all sources prevents double-counting

### Why Six Sources?

1. **Seed companies** → hidden vacancies at known good employers
2. **Startup boards** → earliest postings, lowest barrier to entry
3. **VC-backed** → funded companies with hiring velocity
4. **Accelerators** → proven founders, YC/Techstars signal
5. **Indeed direct** → largest US job board, fresh before JobSpy lag
6. **JobSpy** → fallback aggregator for everything else

### Why Dedup by URL?

- Prevents duplicate rows in master_tab (same job listed on multiple boards)
- Tracks dedup rate (signals source overlap; informs future source selection)
- Allows per-source tracking (each job row tagged with origin)

### Why Title Boosting Over Seniority?

- Market shows 96% of applicable roles are Coordinator + Specialist variants
- Broad title boost (6 priority, 14 wide-net) catches 57% of market
- Seniority exclude (7 patterns) filters out director/VP/C-suite noise
- Combination: wide title net + narrow seniority bounds = high precision

---

## Filter Tuning (2024 Seattle Market)

**Recent improvements:**

- Eased hard_exclude_keywords: removed 150+ geographic/intl entries (was over-filtering)
- Added 4 companies to blocklist: US Bank, Tesla, Pitchbook, Chase (user-specific preferences)
- Expanded title boosting: +3 priority roles, +6 wide-net roles (from 3+8 to 6+14)
- Trimmed company blocklist: 85 → 76 (removed irrelevant enterprises)

**Market signal (last 60 days):**
- 96% of crawled jobs are Coordinator roles
- 57% also have "Specialist" in title
- Project Coordinator is the hottest role (4 openings, trending)
- Data roles are secondary (10.7% of crawled)

---

## Support Files

- `references/filter-tuning.md` — detailed F1–F11 filter configuration with market data
- `references/startup-company-list.md` — curated 13+ VC-backed startups + ATS URLs
- `references/accelerator-cohorts.md` — YC/Techstars/500G/P&P company lists + cohort tracking
- `scripts/master_crawl.py` — orchestrator that runs all 6 phases
- `templates/scout_profile.json.template` — filter config template (copy + modify)
- `references/tracing-interview-to-source-row.md` — READ/LOOKUP side: map a live interview back to its sheet tab+row. Live sheet is `JOB_HAMMER` (`12FTPE1...`), NOT the stale `TERRAjob` sheet; covers recruiter-vs-employer aliasing, bloated-JD-cell gotcha, and Gmail/Calendar/sheet triangulation.

---

## Pitfalls & Lessons

### Pitfall: Slow Network Crawls Block Pipeline

**Lesson:** Rate-limit between requests (1–2s spacing). Set crawler timeouts (10–15s per request). Use parallel job execution for independent sources if needed.

**Workaround (network timeout mid-session):** If JobSpy or Indeed scraper hangs during `master_crawl.py`:
1. Stop the crawl (Ctrl+C after 60s timeout)
2. Load the last successful `output/jobs.csv` (from prior run)
3. Manually run only Phase 1 crawlers (`seed_companies.py`, `startup_jobs.py` — these are fast, <1s each)
4. Merge fresh Phase 1 output with prior jobs.csv via pandas:
   ```python
   import pandas as pd
   prior = pd.read_csv("output/jobs.csv")
   fresh_seed = pd.read_csv("output/seed_companies.csv")
   fresh_startup = pd.read_csv("output/startup_jobs.csv")
   merged = pd.concat([prior, fresh_seed, fresh_startup], ignore_index=True)
   dedup = merged.drop_duplicates(subset=['url'], keep='first')
   dedup.to_csv("output/jobs.csv", index=False)
   ```
5. This preserves all prior jobs + adds any new postings from seed/startup boards without waiting for the slow aggregator. Typical result: 40–50 jobs in <5 seconds.

### Pitfall: DNS Failures in Network-Isolated Environments

**Lesson:** Graceful error handling in each crawler; continue with remaining sources if one fails. Log errors but do not halt pipeline.

### Pitfall: Duplicate URLs Across Multiple Sources

**Lesson:** Dedup by URL, track origin (SOURCE column), calculate dedup rate. This reveals source overlap and informs future crawler selection.

### Pitfall: Title Variation Across Job Boards

**Lesson:** Regex-based title matching is brittle. Boost multiple variants (Project Coordinator, Implementation Specialist, Operations Specialist) rather than relying on exact match. Allow soft matching.

### Pitfall: Outdated Company Blocklist

**Lesson:** Review blocklist quarterly. Remove irrelevant companies (large enterprises unlikely to hire for entry-level roles). Keep only meaningful blocks (Big Tech, Big Finance, consulting firms, HR software giants).

---

## Generalization (Beyond Job Hammer)

This architecture generalizes to **any multi-source data aggregation task:**

- **Real estate listings:** MLS + Zillow + direct agent websites + new construction boards
- **Product research:** Product Hunt + G2 + direct company landing pages + announcement feeds
- **Talent scouting:** LinkedIn + GitHub + direct company career pages + startup boards
- **News aggregation:** RSS feeds + API sources + direct publisher scrapes + newsletter archives

**Template:**
1. Define N independent sources (Phase 1+)
2. Define one aggregator (Phase 2)
3. Merge + dedup by key field (URL, ID, etc.)
4. Apply filter pipeline to deduplicated output
5. Sync to downstream (sheet, DB, API, etc.)

---

## Session Context

Built during June 2024 optimization of Job Hammer for Seattle market. Incorporates feedback on filter tuning, startup company access, and Indeed board coverage.

**Related skills:** `data-aggregation`, `web-scraping`, `csv-pipeline`
