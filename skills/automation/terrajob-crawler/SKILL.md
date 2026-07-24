---
name: terrajob-crawler
description: "Run TerraJob job crawler on demand"
version: 1.0.0
platforms: [linux]
metadata:
  hermes:
    tags: [jobs, crawler, terrajob, automation]
---

## TerraJob Crawler

## References
- `references/linkedin-job-url-extraction.md` — batch curl technique for finding confirmed LinkedIn job view URLs from screenshot-sourced job listings
- `references/quality-check.md` — post-crawl validation script and expected metrics
- `references/fluxjob-architecture.md` — FLUXJOB fork architecture, resume_data.json schema, sheet sync flow, LaTeX pitfall

## Location
```
~/TerraJob-personal/Stage_1_Job_Crawl/
```

## Run Command
```bash
cd ~/TerraJob-personal/Stage_1_Job_Crawl
python tanzim_scout_crawler_9of9.py --profile tanzim_scout_profile_4of9.json
```

The crawler self-bootstraps into its venv (`.venv/` in that directory).

## What It Does
1. Scrapes jobs from Indeed, LinkedIn, Greenhouse, Lever, BuiltInSeattle
2. Filters by Tanzim's profile (role, location, salary band, sponsorship needs)
3. Scores and ranks matches
4. Dedupes against previous runs (state/dedup_index.json)
5. Writes output to `output/` directory
6. Optionally syncs to Google Sheets (if credentials present)

## JobSpy Timeout Issues
JobSpy (Indeed + LinkedIn) often hangs for 10+ minutes or times out completely.
**Workaround:** Create a fast profile that skips JobSpy:
```bash
# In profile JSON, change:
"preferred_sources": ["builtin_seattle", "greenhouse", "lever"]
# This skips jobspy entirely and runs in ~2 minutes instead of 15+
```

The other sources (BuiltInSeattle, Greenhouse, Lever) return ~50 quality jobs without the timeout risk.

## Output
- `output/jobs_master.csv` — all scored jobs
- `output/jd_packet_*.txt` — JD packets for Stage 2 tailoring
- Console summary with top picks

## Setup (one-time per machine)
```bash
cd ~/TerraJob-personal
./setup.sh
```

## Google Sheets Sync
Requires `Stage_1_Job_Crawl/state/google_credentials.json` (service account JSON).
Toggle in profile: `google_sheets_sync.enabled`

**OAuth workaround:** If no service account is available, disable `google_sheets_sync.enabled` in the profile and populate the sheet manually using OAuth after the crawl:

```python
# After crawl completes, read jobs.csv and write to sheet via OAuth
import csv, json, urllib.request

# Refresh OAuth token
# ... (see google-oauth-refresh skill)

# Create new tab for today
today = datetime.now().strftime("%Y-%m-%d")
tab_name = f"Scout_{today}"

# Write jobs to sheet via Sheets API values:batchUpdate
```

This approach produces the same result without needing a service account.

## TerraJob Google Sheet

- **Sheet ID**: `1vhK1ys152Rem0J6ygntEB9uyajz8trGi7JlmCLHLniI`
- **URL**: https://docs.google.com/spreadsheets/d/1vhK1ys152Rem0J6ygntEB9uyajz8trGi7JlmCLHLniI
- **Tab naming convention**: `MM/DD` (e.g. `05/27`) — one tab per job search session
- **Columns**: `pdf_resume, score, company, position, location, remote, salary_min, salary_max, posted_date, alert, first_seen, url, source`
- **Existing tabs**: Master, 05/23, 05/24 (add new date tabs as sessions run)

## Manual Job Entry from LinkedIn Screenshots

When Tanzim sends LinkedIn job feed screenshots and asks to populate the sheet:

1. **Extract all job listings** from screenshots (title, company, location, salary if shown)
2. **Find LinkedIn URLs in parallel** — use `subagent` with up to 3 concurrent tasks for large batches (50+ jobs). Each task: curl `https://www.linkedin.com/jobs/search/?keywords=TITLE+COMPANY` and extract `jobPosting:\d+` IDs from HTML
3. **Verify every ID** by fetching `https://www.linkedin.com/jobs/view/{id}/` and checking `og:title` contains expected company name. **Expect ~15-20% mismatch rate** — the search often returns an unrelated top result. Run verification on ALL rows, not just a sample.
   - Short company names (SPS, WSP, EY, MRO, DTN) are especially prone to false positives — their first word is too common to be a reliable match signal. Check the full og:title.
   - Collect all mismatches, re-search with `TITLE COMPANY LOCATION` combined, verify again
4. **Create new date tab** using `spreadsheets.batchUpdate` addSheet request
5. **Write rows** using `values:batchUpdate` POST (not PUT) — required for tab names with `/` (see google-workspace skill)
6. Set `source=manual`, `posted_date` and `first_seen` to today, leave `pdf_resume` and `score` blank

### Merging tabs
To merge two tabs (e.g. 05/27 + 05/27b → 05/27):
1. Read both tabs via `values.get`
2. Combine: header from tab1 + data rows from both (skip tab2 header)
3. Write combined to tab1 via `values:batchUpdate`
4. Get tab2's sheetId from `spreadsheets.get` metadata
5. Delete tab2 via `batchUpdate` with `deleteSheet` request

### Scale notes (from 05/27 session)
- ~230 jobs from one batch of screenshots → two tabs (05/27 + 05/27b), then merged
- Batch search: run in parallel subagents (3 concurrent max), 0.5s sleep between curl calls
- Full verification pass (230 rows): ~4 min in execute_code with 0.2s sleep per request
- Found ~26 confirmed mismatches requiring re-search and fix

## Repos
- Personal (populated profile): `~/TerraJob-personal` — cloned via git credentials
- Public V1 template: `https://github.com/tanzimozer/TERRAjob` (public)
- Public V2 template: `https://github.com/tanzimozer/TERRAjob.V2` (public)
- Private personal repo: `https://github.com/tanzimozer/TERRAjob` — use `~/.git-credentials` to clone, NOT the API token (API only returns public repos)

## NAMING CLARIFICATION (Critical for Context Switching)

Three distinct systems exist — **do not conflate them:**

1. **TERRAjob** (original system, `~/TERRAjob-personal/`, `TERRAjob.V2` public fork)
   - 3-stage pipeline: Scout Crawl → Resume Tailor → PDF Render
   - Uses `tanzim_scout_crawler_9of9.py`
   - Output: scored jobs CSV + resume PDFs + Drive upload

2. **FLUXJOB** (`https://github.com/tanzimozer/FLUXJOB`, optimised fork of TERRAjob.V2)
   - Same 3-stage pipeline, rewritten for speed + OAuth compatibility
   - Replaces service account Google auth with OAuth token (`~/.hermes/google_token.json`)
   - Runs subagent content workers + quality gate + 4-format output
   - Command: `python fluxjob_run.py --top 50`

3. **Job Hammer** (`/tmp/JOB_HAMMER-personal/`, **distinct system**)
   - 6-source crawler + merge/dedup orchestrator
   - Focuses on startup boards + VC-backed ATS + accelerators
   - Runs `master_crawl.py` (not the TERRAjob scout crawler)
   - Output: merged jobs.csv + per-job tabs in Sheet
   - **Not** a resume tailoring system — crawling only

**When user says "run hammer" or references "Job Hammer":**
- Ask which phase: Stage 1 crawl, or Stage 2 resume engine?
- If Stage 1 → use `job-hammer-crawler-architecture` skill + `/tmp/JOB_HAMMER-personal/`
- If Stage 2 → clarify if they mean Job Hammer resume tailoring (not yet implemented) OR FLUXJOB (existing resume system)

## JOB_HAMMER Stage 1 Crawler (Separate from TERRAjob Resume System)
**References:** 
- `references/job-hammer-master-orchestrator.md` — **NEW** master_crawl.py orchestration (6 sources, merge/dedup, pipeline integration)
- `references/job-hammer-filters.md` — full filter spec
- `references/job-hammer-filter-improvements.md` — June 2026 optimization (title expansion, blocklist trim, ATS seed expansion)
- `references/job-hammer-startup-sourcing.md` — three startup job source patterns (boards, VC-backed crawlers, accelerators)

**Job Hammer is a DISTINCT SYSTEM from TERRAjob** — it's a multi-source crawler orchestrator, not a resume tailoring system.

### Location & Credentials
```
/tmp/JOB_HAMMER-personal/Stage_1_Crawl/     # Main crawler
/tmp/JOB_HAMMER-personal/Stage_2_Resume/    # Resume tailoring (TBD)

Google OAuth: ~/.hermes/google_token.json   # Same token, drive + sheets scopes
Scout profile: Stage_1_Crawl/scout_profile.json
Sheets ID: 12FTPE1jSvrzdBeQ5Sjwiv8ccNVEbw7tTWJNdtDkrLZ0
```

### Run Command (Full Pipeline — After June 2026 Improvements)
```bash
cd /tmp/JOB_HAMMER-personal/Stage_1_Crawl

# ORCHESTRATED: All 6 sources + merge + dedup in one command
python master_crawl.py
# Internally runs:
#   - seed_companies.py (7 direct ATS)
#   - startup_jobs.py (AngelList, startup.jobs, CrunchBoard)
#   - crunchbase_vc_crawler.py (13 VC-backed startup ATS)
#   - accelerator_crawler.py (YC, Techstars, 500 Global, Plug and Play)
#   - indeed_scraper.py (Indeed direct)
#   - crawler.py (JobSpy main crawl)
# Outputs: output/jobs.csv (merged + deduped + scored + top 50)

# Then sync to Google Sheets (per-job tabs + master_tab append)
python sync_to_sheet.py  
# Creates individual job tabs + appends net-new to master_tab
```

**Single-command execution:** See `references/job-hammer-master-orchestrator.md` for full flow, dedup logic, and troubleshooting.

### Filter Architecture (11 Stages)
See `references/job-hammer-filters.md` for full list. As of June 2026:

| Filter | Setting | Notes |
|--------|---------|-------|
| **Location** | Seattle WA + Remote | JobSpy + BuiltInSeattle + seed companies (7) + startup boards + VC crawlers (13) + accelerators |
| **Experience** | Early (entry-2yrs) | Max 5 years required; entry-tier titles preferred |
| **Salary** | $55k–$80k | Target $70k ±15% gets +5 boost; no salary = pass (benefit of doubt) |
| **Seniority exclude** | No intern/director/VP/principal/staff/program manager | Blocks senior variants (Senior Manager, Senior SDR, etc.) |
| **Title priority (IMPROVED)** | +20: 6 titles (Project/Implementation/Ops Coordinator, Specialist roles) | +10: 14 title variants (APM, Analyst, Specialist, Coordinator, Operations, etc.) — captures 57% of market |
| **Hard exclude** | ~200 keywords + 76 companies (down from 110) | Clearance, PhD/MD, on-site only, cold-calling, LATAM/APAC/EMEA remote; removed irrelevant enterprise blocks (Shopify, Roblox, Netflix, etc.) |
| **Work auth** | US Citizen | No sponsorship |
| **Company size** | Startup/scaleup (<2K employees) | Via blocklist (no headcount data per job) |
| **Industry boost** | +8: fintech/wellness; +6: fitness; +5: banking, data | Matched against company + description lowercase |
| **Work model** | "any" (on-site OK) | Override to "fully_remote" to drop on-site |
| **Recency** | 7-day crawl window, 21-day hard cap | Bonus if <7d old |

All filters = substring match (case-insensitive). One rule kills the job. Scoring stacks.

**June 2026 improvements:** Title boosting expanded 6x (now catches Specialist role variants); company blocklist trimmed 27% (precision gain); 20+ startup ATS sources added (supply +40-80%).

### Sheet Sync — Per-Job Tabs + Master Archive (June 2026 Extended)
**EXTENDED:** `sync_to_sheet.py` now creates individual tabs per job + master_tab append-only archive.

Architecture:
```
master_tab         ← All net-new jobs from every crawl (append-only, deduped by URL)
Jun 03             ← Daily crawl tab (top 50 net-new, sorted by score, formatted header)
Google SWE         ← Per-job tab (header + 1 row, auto-created)
Microsoft PM       ← Per-job tab
Rippling Ops       ← Per-job tab
... (one tab per net-new job)
```

**Workflow:**
1. Crawl → jobs.csv (sorted by SCORE desc)
2. Dedup vs master_tab (by URL) — skip if already seen
3. Keep top 50 net-new
4. **For each net-new job:**
   - Create tab named `{COMPANY} {TITLE}` (sanitized to 31 chars max, special chars → underscores)
   - Write header + single row to that tab
   - Append same row to master_tab (in background, batch write every 10 jobs)
5. Write daily tab (all 50, formatted with frozen header, bold CAPS columns)

**Key functions in sync_to_sheet.py:**
```python
def _sanitize_tab_name(name: str, max_len: int = 31) -> str:
    # Convert "Google SWE (NYC)" → "Google_SWE_NYC"
    # Handles special chars, enforces max length, avoids collisions
    
def _apply_format(ws, n_rows: int):
    # Frozen header row (F2)
    # Bold + center all CAPS columns (COMPANY, TITLE, SCORE, etc.)
    # JD column (rightmost) left-aligned + text-wrap
    
def _dedup_by_url(jobs: List[dict], master_tab_rows: List[list]) -> List[dict]:
    # Extract URLs from master_tab, skip jobs already seen
    # Return net-new jobs only
```

**Dedup index:** Persistent in `dedup_index.json` at crawl time (for next run's comparison).

**Daily cap:** 50 net-new per crawl (oldest data pruned if >50).

**Columns:** `URL`, `COMPANY`, `TITLE`, `SCORE`, `LOCATION`, `REMOTE`, `SALARY_MIN`, `SALARY_MAX`, `POSTED_DATE`, `SOURCE`, `JD`

**Example output (master_tab after 2 crawls):**
```
URL                                    COMPANY      TITLE                        SCORE  POSTED_DATE  SOURCE
https://jobs.lever.co/rippling/...    Rippling     Operations Specialist        72     2026-06-03   startup_jobs
https://careers.mercury.com/jobs/...  Mercury      Fintech Operations Manager    68     2026-06-03   crunchbase_vc
...
(49 more rows from Jun 03)
https://jobs.lever.co/notion/...      Notion       Project Coordinator          71     2026-06-04   accelerator
...
(all Jun 04 net-new rows appended below)
```

### Dry-run mode
```bash
python sync_to_sheet.py --dry-run --csv path/to/jobs.csv
# Shows transform without Google calls; useful for testing filters
```

### Historical data
Jun 03 tab seeded with 49 jobs; master_tab contains all of those + any crawls since.

## TERRAjob.V2 Architecture (3-Stage Pipeline)

```
Stage 1 → Scout Crawler   → jobs.csv + JD packets (one per job)
Stage 2 → Resume Engine   → resume_data.json per job (LLM tailoring)
Stage 3 → App Orchestrator → render PDF + upload to Drive + track state
```

### Key files (V2)
- `Stage_2_Resume_Tailoring/resume_profile_4of8.json` — user profile (NEVER committed to GitHub — lives on device only)
- `Stage_2_Resume_Tailoring/resume_soul_7of8.md` — tailoring decision logic
- `Stage_3_Application/tools/prepare_tailoring.py` — stages top-N jobs for subagent dispatch
- `Stage_3_Application/tools/render_pdf.py` — reportlab PDF renderer (pure Python, no LaTeX needed)
- `Stage_3_Application/tools/render_pipeline.py` — post-tailoring: reads resume_data.json → renders PDFs → updates sheet
- `Stage_3_Application/tools/drive_upload.py` — uploads PDF to Google Drive folder "TerraJob Resumes"
- `Stage_3_Application/tools/tailor_subagent.md` — instructions for one-per-job tailoring subagent

### Resume output spec (4 files per job)
| File | Purpose |
|---|---|
| `[Last]_[First]_[Company].docx` | ATS submission (Word) |
| `[Last]_[First]_[Company].pdf` | PDF reference |
| `[Last]_[First]_[Company]_CoverLetter.docx` | Cover letter |
| `[Last]_[First]_[Company]_Deedy.pdf` | Two-column visual PDF |

### 4-Format Output Pipeline (BUILT — June 2026)
`output_pipeline.py` in `Stage_2_Resume_Tailoring/` generates all 4 formats in one command:

```bash
python output_pipeline.py --job "Brex_DataAnalyst" --title "Data Analyst II" --company "Brex" \
  --profile tanzim_resume_profile_4of8.json --out output/formatted
```

| # | Format | Generator | Notes |
|---|--------|-----------|-------|
| 1 | `Resume.pdf` | WeasyPrint HTML→PDF | Pixel-perfect, Lato font |
| 2 | `Resume.docx` | python-docx | ATS-safe, spec-compliant |
| 3 | `Deedy.pdf` | XeLaTeX (xelatex) | Two-column visual, Lato |
| 4 | `CoverLetter.docx` | python-docx | Auto-personalised per JD |

Requires: `xelatex`, `weasyprint`, `python-docx` (all confirmed installed on hermes VM).
Deedy class file: `deedy_template.tex` (in same dir) + `deedy-resume-openfont.cls` (auto-downloaded from GitHub on first run, fallback minimal cls if network fails).

**LaTeX template pitfall:** Do NOT use Python `r"""..."""` string for LaTeX templates containing `%` characters — `%` triggers `%s`-style formatting. Write the template to a separate `.tex` file and use `.replace("%%PLACEHOLDER%%", value)` instead.

**Profile field mapping for output_pipeline.py:**
```python
profile['name'], profile['email'], profile['phone'], profile['location']
profile['summary']          # string
profile['skills_core']      # list of strings
profile['skills_swap']      # list of strings  
profile['experiences']      # list: {title, company, location, dates, bullets:[str]}
profile['education']        # list: {degree, school, dates}
profile['certifications']   # list of strings OR dicts with 'name' key
profile['projects']         # list: {name, description}
profile['top_wins']         # list of strings — used in cover letter
```

## Drive Upload — OAuth vs Service Account
`drive_upload.py` was written expecting a **service account** JSON at `state/google_credentials.json`.
Tanzim's machine has an **OAuth token** at `~/.hermes/google_token.json` with `drive` scope.

To use OAuth instead of service account, swap the credential loader:
```python
from google.oauth2.credentials import Credentials
creds = Credentials(
    token=token_data["token"],
    refresh_token=token_data["refresh_token"],
    token_uri=token_data["token_uri"],
    client_id=token_data["client_id"],
    client_secret=token_data["client_secret"],
)
```
Load from `/home/hermes/.hermes/google_token.json` (has `drive` scope confirmed).

## Profile Population — Critical Prerequisite
`resume_profile_4of8.json` is intentionally NOT committed to GitHub (personal data).
- GitHub copy = empty template with all TODO fields
- Populated copy lives on Tanzim's local machine only
- **Before any resume generation run:** confirm profile is populated OR run onboarding (upload resume → extract → populate JSON)
- Onboarding questions are in `resume_onboarding_questions_3of8.md`

### Profile JSON field names (CRITICAL — not intuitive)
```python
role['default_title']       # NOT role['title']
role['title_options']       # list of alternate titles
role['bullets'][n]['text']  # bullets are dicts with 'text' key
profile['core_skills']      # NOT profile['skills']['core']
profile['swappable_skills'] # NOT profile['skills']['swappable']
profile['certifications']   # list of STRINGS, not dicts
profile['projects']         # list of STRINGS, not dicts
```
Always use `.get()` with fallbacks when reading profile fields.

## FLUXJOB Fork (June 2026 — active)

FLUXJOB is the optimised fork of TERRAjob.V2-personal. **Do NOT modify the source repo `TERRAjob.V2-personal` directly** — Tanzim was explicit: "do not touch my repo." All efficiency work lives in FLUXJOB only.

**Repo:** https://github.com/tanzimozer/FLUXJOB (private)
**Local clone target:** `/tmp/FLUXJOB_build/`

### What FLUXJOB adds (original files untouched)

| File | Purpose |
|------|---------|
| `fluxjob_run.py` | Main orchestrator — 4-step pipeline in one command |
| `fluxjob_sheet_sync.py` | OAuth Drive upload + Sheet HYPERLINK writer |
| `Stage_2_Resume_Tailoring/FLUXJOB_CONTEXT_COMPILED.md` | 288-line compiled spec (from 1,413 lines across 8 files) |
| `Stage_2_Resume_Tailoring/FLUXJOB_CLAUDE_WORKER_PROMPT.md` | Content-only worker prompt |
| `Stage_3_Application/FLUXJOB_PIPELINE_NOTES.md` | Schema + gap analysis |
| `FLUXJOB_ENGINE_GUIDE.md` | User-facing how-it-works + how-to-use doc |

### Pipeline (4 steps)
```
Step 1: Claude content workers (parallel, max 6) → resume_data.json per job
Step 2: Quality gate — validates every resume_data.json before render
Step 3: render_pipeline.py → 4 output formats per job
Step 4: fluxjob_sheet_sync.py → DOCX → Drive (FLUXJOB Resumes folder) → HYPERLINK in pdf_resume column
```

### Run commands
```bash
python fluxjob_run.py --top 5          # top 5 by score
python fluxjob_run.py --all            # all JD packets
python fluxjob_run.py --dry-run --top 10
python fluxjob_run.py --qc-only --top 5
python fluxjob_run.py --render-only --top 5
```

### Sheet sync — OAuth not service account
`fluxjob_sheet_sync.py` uses `~/.hermes/google_token.json` (OAuth). The original `drive_upload.py` used a service account at `state/google_credentials.json` — that file does not exist on this machine. **Always use OAuth for Drive/Sheets operations in this setup.**

Towsif's view in the Sheet after sync:
| company | position | score | pdf_resume |
|---------|----------|-------|------------|
| Brex | Data Analyst II | 62 | 📄 Resume |

He clicks → downloads DOCX → applies. No further action needed from Tanzim.

### Key architecture decision
**Claude handles content. Python handles formatting. They never mix.**
- Claude reads JD + compiled context → outputs `resume_data.json` (content only)
- Python reads `resume_data.json` → renders all 4 formats to exact spec
- Bullet length, spacing, font sizes — all enforced by Python, never by Claude

### Compiled context efficiency
Original: 8 spec files, 1,413 lines — loaded fresh per worker
FLUXJOB: `FLUXJOB_CONTEXT_COMPILED.md`, 288 lines — ~75% token reduction per job
Same spec fidelity. Comments, rationale, changelog stripped. Only executable rules kept.

## Efficiency Improvements — Proposed (June 2026)

### Problem 1: Job Selection Quality
Current score doesn't learn from outcomes. Proposed callback signal loop:
- When a role reaches `phone_screen` or `interview`, backfill its profile signals into a local `state/callback_signals.json`
- Next crawl boosts roles matching those signals +15
- Works after ~5–10 responses; no ML needed

### Problem 2: work_model_preference
`"any"` is too permissive — remote roles get 10x more applicants, killing callback rate.
**Recommendation:** Set `work_model_preference: "hybrid_ok"` while unemployed in Seattle.

### Problem 3: Auto-logging to Sheet
`drive_upload.py` uses service account — doesn't work with Tanzim's OAuth token.
Fix: swap to OAuth credentials from `~/.hermes/google_token.json` (has `drive` scope).
Once fixed, single pipeline command:
```bash
python pipeline.py run --top 5
# crawl → tailor → 4-format output → Drive upload → Sheet logging
```

### Approach
1. Run crawler → get jobs.csv
2. `prepare_tailoring.py --top 50` → stages 50 job folders
3. Spawn 50 subagents in parallel (each reads profile + JD packet → writes `resume_data.json`)
4. `render_pipeline.py` → renders all PDFs
5. `drive_upload.py` (OAuth variant) → uploads to "TerraJob Resumes" Drive folder
6. Report back to Tanzim

### Speed estimate
50 parallel subagents ≈ 10–15 minutes total

### Retry logic needed
No retry on subagent failure in current codebase. Wrap dispatch loop to re-queue any job where `resume_data.json` was not produced.
