---
name: job-board-scraping
description: "Scrape job boards (Indeed, LinkedIn, Greenhouse, Lever, BuiltInSeattle) with scoring, filtering, and CSV/Google Sheets output."
tags: [jobs, scraping, indeed, linkedin, jobspy, greenhouse, lever, builtinseattle, csv, career]
---

# Job Board Scraping

## When to Use
- User wants to pull job listings from Indeed, LinkedIn, Greenhouse, Lever, or BuiltInSeattle
- Building or running a weekly job tracker pipeline
- Need to filter, score, and output structured job data to CSV or Excel
- Running a job search for a **new candidate** (not Tanzim) — parse their resume, build a profile, then spin up a candidate-specific scraper

## Per-Candidate Scraper Pattern

When running for a new candidate (not Tanzim):

1. **Parse resume** — use python-docx or pymupdf to extract text from uploaded .docx/.pdf
2. **Build profile** — identify: current role, years of experience, top skills/tools, education, salary floor, location preference
3. **Create a candidate-specific script** at `/home/hermes/jobs/<name>_scraper.py`:
   - Override `PRIORITY_TITLES`, `WIDE_NET_TITLES`, `INDUSTRY_BOOST` to match their background
   - Set a fixed `SALARY_FLOOR` constant (no location-based logic if floor is uniform)
   - Add hybrid detection if relevant: `is_hybrid(title, desc)` checks `"hybrid"` in title/desc, score +6
   - Output to `/home/hermes/jobs/<name>_jobs.csv`
4. Run with the Hermes venv, background process, drop CSV in chat when done

**Example — Zara Mondale (CS/Research/Ops, $70k floor):**
- Script: `/home/hermes/jobs/zara_scraper.py`
- Output: `/home/hermes/jobs/zara_jobs.csv`
- Profile: Customer Success Specialist + Research Coordinator, 6+ yrs, Joylux, BA Psychology UMBC
- Industry boost: health tech (Joylux, Oura, Whoop), SaaS tools she uses (Airtable, Notion, Asana), fintech
- Run yielded: 2,661 raw → 140 filtered (Seattle/remote/hybrid, $70k+)

## Critical Bug Fixed (2026-05-05)
`run()` was only calling `scrape_jobspy()` — `scrape_builtinseattle()` and `scrape_greenhouse()` were never invoked. The fixed `run()` calls all four sources in sequence: JobSpy → BIS → Greenhouse → Lever.



## Sources Summary (as of 2026-05-05)

| Source | Type | Coverage |
|---|---|---|
| Indeed | JobSpy | Seattle, 12 search terms |
| LinkedIn | JobSpy | Seattle, 12 search terms |
| BuiltInSeattle | Playwright | Seattle, 8 search terms |
| Greenhouse | Direct API | 31 company boards |
| Lever | Direct API | 4 company boards |
| We Work Remotely | RSS | 3 categories (customer-support, management-finance, sales-marketing) |

Total: 5 broad sources + 35 company boards.

**RemoteOK removed (2026-05-06):** Jobs linked to paywalled apply pages — not useful. Removed from scraper entirely.

## Remote Sources (added 2026-05-05)

### RemoteOK
```python
url = f"https://remoteok.com/api?tag={tag}"
# Headers required: User-Agent + Accept: application/json
# Index 0 is a legal notice — filter with: [j for j in data if isinstance(j, dict) and j.get("company")]
# Fields: id, epoch, company, position, description (HTML), tags, url, salary_min, salary_max
# Salary is already annual; 0 means not listed
# Date: epoch seconds → datetime.fromtimestamp(int(epoch))
```
Tags that yield ops-relevant results: `coordinator` (~27), `operations` (~95). Tags like `customer-success`, `project-management` return 0.

### We Work Remotely RSS
```python
url = f"https://weworkremotely.com/categories/{category}.rss"
# Title format: "Company: Job Title" — split on ': ' to get both
# Region field: filter to "Anywhere in the World", "USA Only", "United States", "North America"
# Skip other regions (Europe, Canada-only, etc.)
# No salary data in RSS
```
Useful categories: `remote-customer-support-jobs` (59 items), `remote-management-and-finance-jobs` (17), `remote-sales-and-marketing-jobs` (62). Category `remote-business-exec-and-management-jobs` returns 301 redirect — skip it.

### Himalayas — DO NOT USE
API returns irrelevant results regardless of query/category params. Tested and confirmed broken as of 2026-05-05.

- **Script location:** `/home/hermes/jobs/scraper.py`
- **Dedupe script:** `/home/hermes/jobs/dedupe.py`
- **Output:** `/home/hermes/jobs/jobs.csv` (raw filtered) → `/home/hermes/jobs/jobs_final.csv` (deduped, final)
- **Python:** use the Hermes venv (`/home/hermes/.hermes/hermes-agent/venv/bin/python3`)
- **BeautifulSoup** must be installed in the venv:
  ```bash
  /home/hermes/.hermes/hermes-agent/venv/bin/pip3 install beautifulsoup4
  ```

## Library Situation (Critical)

### JobSpy (working — use this)
- Package: `python-jobspy` (NOT `jobspy`) — installs as `jobspy` module
- Has built-in TLS fingerprint spoofing for Indeed — much higher yield (~565 raw vs ~20 with direct requests)
- **numpy==1.26.3 conflict is resolved** — install numpy + pandas first, then jobspy, in the Hermes venv:
  ```bash
  /home/hermes/.hermes/hermes-agent/venv/bin/pip3 install numpy pandas -q
  /home/hermes/.hermes/hermes-agent/venv/bin/pip3 install python-jobspy -q
  ```
- Verify: `/home/hermes/.hermes/hermes-agent/venv/bin/python3 -c "from jobspy import scrape_jobs; print('JobSpy ready')"`
- Use: `scrape_jobs(site_name=["indeed", "linkedin"], search_term=..., location="Seattle, WA", results_wanted=30, hours_old=168, country_indeed="USA", linkedin_fetch_description=False)`
- **DO NOT** install via system pip (`pip install --break-system-packages`) — numpy version conflicts will block pandas import

### Requests + BeautifulSoup (fallback)
- Works but Indeed blocks after ~1-2 pages per session with 403s
- Yields ~10-20 jobs vs. 200+ with JobSpy
- Use only as a fallback or for Greenhouse (which doesn't block)

### Direct scraping 403 pattern
- Indeed and BuiltInSeattle both aggressively block direct requests after page 1
- Adding delays helps marginally — the real fix is JobSpy's TLS spoofing
- Do NOT waste time retrying raw requests against Indeed — fix JobSpy instead

## Tanzim's Filter Criteria

### Priority titles (+20 score bonus)
- project coordinator, program coordinator
- assistant/associate/junior project manager
- assistant manager
- implementation coordinator, operations coordinator
- onboarding specialist

### Wide net titles (+10 score)
- project manager, implementation manager/specialist/consultant
- operations manager/analyst, business operations, tech ops, revenue ops, customer ops
- customer success specialist/associate/manager
- solutions consultant, business analyst
- workflow, automation, ai implementation, ai operations

### Hard exclude in title (drop the row)
- Seniority: senior, sr., staff, principal, director, head of, VP, vice president, chief, lead
- Levels: II, III, IV
- Modifiers: enterprise, expert, advanced, experienced
- Engineering roles: engineering manager, engineering program manager, engineering lead, people manager, tech lead

### Sales language exclude (drop the row)
- quota, SDR, BDR, account executive, sales executive, commission-based, book of business, cold calling, outbound sales, new business development

### Location
- Accept: Seattle metro (Seattle P1, Bellevue/Redmond P2, Kirkland/Renton/Tukwila/SeaTac/Issaquah/Bothell/Lynnwood/Mercer Island)
- Accept: Remote (US-based) — strict definition: title/location contains "remote"/"anywhere"/"telecommute" OR description contains "fully remote"/"100% remote"/"remote-first"/"this position is remote"/"work from anywhere"
- Drop: onsite outside Seattle metro

### Salary
- Floor $60k if Seattle metro or remote; $70k if outside metro
- Converted at 2,080 hrs/yr for hourly
- Only filter when salary IS posted and top of range is below floor
- Most postings don't publish salary — those pass through

COMPANY_BLOCKLIST = ["us bank", "pitchbook", "24 hour fitness", "stripe", "figma", "amazon"]

### Degree filter
- Drop if description has strict "bachelor's degree required" / "requires a bachelor's degree" / "must have a bachelor's degree"
- Keep if "preferred" or "or equivalent" softens it

## Scoring Engine

```python
score = 0
# Priority title match:    +20
# Wide net title match:    +10
# Industry boost:          +8 to +10
# Remote:                  +15  (higher than Seattle — remote is first priority)
# Seattle location:        +8
# Freshness: full +15 up to 3 days old, linear decay to 0 at 21 days
#   days_old <= 3:  +15
#   days_old 4-21:  +max(0, 15 * (1 - (days_old - 3) / 18))
#   days_old > 21:  +0
# (Old curve: max +25 decaying at 4pts/day → zero at 7 days. Too aggressive.)
# Company velocity boost (applied AFTER dedupe):
#   company has 2 relevant open roles: +10
#   company has 3+ relevant open roles: +20
```

### Company Velocity Grouping
After deduplication, count relevant open roles per company. Boost scores and write a hot companies summary.

```python
# Count open roles per company
company_counts = {}
for j in deduped:
    c = str(j.get("company", "")).strip().lower()
    company_counts[c] = company_counts.get(c, 0) + 1

# Boost
for j in deduped:
    count = company_counts.get(str(j.get("company", "")).lower(), 0)
    if count >= 3:
        j["_score"] += 20
    elif count == 2:
        j["_score"] += 10

# Hot companies JSON output → /home/hermes/jobs/hot_companies.json
# Fields: company, open_roles, remote_roles, top_score, roles[]
# Sorted by: remote_roles desc, then top_score desc
# Only includes companies with 2+ roles AND at least 1 remote role
```

This file tells you which companies are hiring the most for your target roles with remote work — sorted by remote role count.

### Industry boost companies (+10 each unless noted)
- Fitness tech: Whoop, Strava, Tonal, Hydrow, Oura, Peloton
- Workflow/automation: Zapier, n8n, Airtable, Retool (Make: +5)
- Fintech: Mercury, Ramp, Brex, Chime, BECU
- Seattle mid-market: Rec Room, Remitly, Smartsheet

## Output CSV Columns
```
Score | Title | Company | Location | Remote | Salary | Posted | URL | Source | Snippet
```
- Status dropdown (New/Interested/Applied/Phone/Interview/Rejected/Offer) — add for Excel output
- Archive sheet: old tracked rows that drop out of fresh scrape

## Search Terms to Use (Indeed)
```python
SEARCH_TERMS = [
    "project coordinator", "program coordinator",
    "assistant project manager", "operations coordinator",
    "onboarding specialist", "implementation coordinator",
    "customer success associate", "business analyst",
    "implementation specialist", "operations analyst",
    "customer success manager",
]
```
Run each term, dedupe by job ID/URL, then filter + score combined results.

## Running the Scraper
```bash
cd /home/hermes/jobs
/home/hermes/.hermes/hermes-agent/venv/bin/python3 scraper.py
```
Output goes to `/home/hermes/jobs/jobs.csv`. Run `clean_csv.py` after for cleaned output.

## BuiltInSeattle via Playwright (WORKING)

BuiltInSeattle is JS-rendered — no static HTML job data, and direct curl requests time out. Use Playwright headless Chromium instead.

**Setup:**
```bash
/home/hermes/.hermes/hermes-agent/venv/bin/pip3 install playwright -q
/home/hermes/.hermes/hermes-agent/venv/bin/playwright install chromium
```

**How it works:**
- Load `https://www.builtinseattle.com/jobs?search=TERM` with `wait_until="domcontentloaded"` + `time.sleep(4)`
- Job URLs extracted via regex: `href="(/job/[^"/]+/(\d+))"` — pattern `/job/title-slug/id`
- Titles + descriptions extracted from JSON-LD `@graph` block (NOT bare `@type: ItemList` — it's nested under `@graph`):
  ```python
  data = json.loads(block)
  if isinstance(data, dict) and "@graph" in data:
      items_to_check = data["@graph"]
  for item in items_to_check:
      if item.get("@type") == "ItemList":
          for el in item.get("itemListElement", []):
              # el has: name, url, description
  ```
- BIS listing pages can yield company names from `JobPosting` JSON-LD blocks on the listing page itself (not just individual job page fetch). Parse `@type == "JobPosting"` items in the same `@graph` block → `hiringOrganization.name`. Map by job ID to the structured dict.
- BIS jobs should be treated as Seattle location by default in the location filter

**BIS search terms that yield results:**
```python
BIS_SEARCH_TERMS = [
    "project coordinator", "program coordinator",
    "operations coordinator", "onboarding specialist",
    "customer success", "business analyst",
    "assistant project manager",
]
```
Note: "implementation coordinator" returns 0 on BIS.

**Yield:** ~103 raw unique per full run. After filters typically 10-30 survive (BIS skews tech companies, many exceed seniority filters).

## Pitfalls
- **Wrong python:** `python3` on this system resolves to the Hermes venv. Always use the full venv path to confirm which interpreter you're using.
- **numpy conflict:** `python-jobspy` pins `numpy==1.26.3`. Installing in system pip collides with other packages. Use the venv.
- **bs4 not in venv:** must install separately — `pip3 install beautifulsoup4` in the venv, not system pip.
- **Company + location merged in raw HTML:** Indeed's scraped HTML often concatenates company name and location into one string. Use regex to split on city names.
- **403 on page 2+:** Direct requests to Indeed will block. JobSpy is the only reliable solution for volume.
- **BuiltInSeattle JSON-LD structure:** BIS wraps ItemList inside `@graph`, not at the root. If you parse `data.get("@type") == "ItemList"` directly you'll get nothing — always unwrap `@graph` first.
- **BIS location filter:** BIS jobs return empty/generic location strings. Treat any job sourced from `builtinseattle` as Seattle in the location filter, else they all get dropped by the location check.
- **no_title_match kills BIS jobs:** If JSON-LD parsing fails, titles come in empty → all get dropped. Validate the `@graph` parser is working if BIS yield drops to zero.

## Lever Boards (WORKING — added 2026-05-05)

Free public API, no auth needed.

```python
url = f"https://api.lever.co/v0/postings/{slug}?mode=json"
```

Response: JSON array of postings. Each has: `text` (title), `hostedUrl`, `categories.location`, `createdAt` (epoch ms), `lists` (description blocks).

**Confirmed working slugs:**
| Company | Slug | Jobs |
|---|---|---|
| Outreach | outreach | 32 |
| Aircall | aircall | 101 |
| Highspot | highspot | 6 |
| Clari | clari | 4 |

**Slugs tested and NOT on Lever (404):** intercom, mixpanel, amplitude, webflow, miro, gong, samsara, brex, plaid, chime, zapier, stripe, affirm, okta, datadog, sentry — most use Greenhouse or Workday instead.

**Date parsing:** `createdAt` is epoch milliseconds — `datetime.fromtimestamp(int(created) / 1000)`

**Location:** in `categories.location` or `categories.allLocations[0]`

**Description:** concatenate `lists[].content` fields (these are the job requirement sections)



Public JSON API — no blocking, no auth needed.

```python
url = f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs?content=true"
```

Response: `{ "jobs": [ { "title", "absolute_url", "offices": [{"name"}], "updated_at", "content" } ] }`

**Live slugs (confirmed working as of 2026-04):**
| Company | Slug | ~Jobs |
|---|---|---|
| Smartsheet | smartsheet | 147 |
| Airtable | airtable | 34 |
| Brex | brex | 227 |
| Mercury | mercury | 59 |
| Chime | chime | 71 |
| Peloton | peloton | 52 |
| Oura | oura | 107 |
| Ramp | rampnetwork | 2 |
| Asana | asana | 129 |
| Lattice | lattice | 11 |
| Gusto | gusto | 78 |
| Klaviyo | klaviyo | 235 |
| Notion | notion | - |
| Loom | loom | - |
| Rippling | rippling | - |
| Deel | deel | - |
| Intercom | intercom | 174 |
| Mixpanel | mixpanel | 51 |
| Amplitude | amplitude | 60 |
| Webflow | webflow | - |
| Miro | miro | - |
| Pendo | pendo | 18 |
| Fullstory | fullstory | - |
| Calendly | calendly | - |
| Productboard | productboard | - |
| Coda | coda | - |
| Heap | heap | ❌ 404 |
| Samsara | samsara | 362 |
| Linear | linear | ❌ 404 |
| Rec Room | recroom | - |
| Remitly | remitly | - |

**Not on Greenhouse:** Zapier, Strava, Retool, Whoop, BECU

**Greenhouse location filter:** Greenhouse jobs have explicit office location strings (e.g. "San Francisco, CA"). Filter is_seattle() normally. For jobs with no location, treat as pass-through (they may be remote). Do NOT auto-tag as Seattle.

**Greenhouse score tip:** These companies are in the INDUSTRY_BOOST list — they'll score higher just from the company name match even without salary data.

**Yield:** ~714 raw per full run. After seniority/location/title filters, typically 10-20 survive (Greenhouse boards are senior-heavy).

## Current Status
- Indeed + LinkedIn via JobSpy: ✅ working (~759 raw per run with 14 search terms)
- BuiltInSeattle via Playwright: ✅ working (~99 raw per run)
- Greenhouse boards: ✅ working (~1,803 raw per run, 14 live boards)
- **Total pipeline yield: ~140 filtered jobs per run (2,661 raw → 140 after all filters)**
- Biggest filter killers: exclude_title (1,180), location (659), no_title_match (277), salary (275), sales (108)

## Job Tracker Sheet Management (Google Sheets)

When the user has an existing job tracker spreadsheet and wants to clean, score, or reorder it:

### Structure Notes (Tanzim's tracker)
- Sheet ID: `1v6CY46PBfGyrde8uuMzPv1cETZrOiflUj_HY34SJC_Q`
- Active tabs follow naming like `2026-04-29 23-29` (date + time of scrape run)
- Row 1 = scrape metadata, Row 2 = header (`Company, Title, Location, Resume, Description, Applied`)
- Data starts at Row 3
- Second tracker (BuiltInSeattle jobs): `1nFbZSjT3iP5V5zGOju7BBLhIEAySq_ayQ_m3n3ROQ1Q` — Sheet1, header at Row 1 (`#, JOB TITLE, COMPANY, RESUME, JOB LINK`), no location column (all Seattle by default)

### Scoring Model (100-point scale)
Used when user wants priority ordering for callback rate. Three factors — resume match and JD fit are handled by Tanzim's Claude engine, excluded here.

1. **Title fit (40pts max)**
   - 40: exact priority match (project/program/ops coordinator, onboarding specialist, asst PM, implementation coordinator/specialist, saas onboarding, customer onboarding, campaign/content/travel ops coordinator, AP project coordinator)
   - 25: good match (any coordinator, project manager, client/customer success manager, business analyst, ops manager, enablement)
   - 5: bad signal (senior, lead, sr., director, VP, principal, engineer, developer, scientist, sales rep/associate)
   - 10: everything else

2. **Company size/type (35pts max)**
   - 10: staffing agencies (Collabera, Aston Carter, Robert Half, Randstad, etc.) — low callback
   - 15: mega corp (Amazon, Microsoft, Google, Meta, Boeing, Deloitte, Accenture, etc.)
   - 25: known enterprise (universities, government, Stripe, Fortinet, nonprofits)
   - 35: unknown/mid-size startup (default — sweet spot for callback rate)

3. **Location (25pts max)**
   - 25: Seattle metro (Seattle, Bellevue, Kirkland, Redmond, Tacoma, Renton, Bothell)
   - 20: WA state or remote+WA
   - 15: fully remote (US)
   - 5: out of state

**Target threshold:** 80+/100 = high priority. Use 80 as the filter cutoff for Top 50 lists.

**Note:** BuiltInSeattle jobs have no location column — treat all as Seattle (25pts location).

### Industry Exclusion Filter
Always strip these before scoring or building priority lists:
- **Construction/trades:** construction, civil, structural, electrical, contractor, handling systems, electric (company), builder, hvac, mechanical, engineering firms (KPFF, HDR, etc.)
- **In-store food/retail:** restaurant, fast food, panda, grocery store, in-store (role, not industry)
- Check both title AND company name for exclusion keywords

### Workflow: Score + Reorder a Tab
```python
# Read all rows from target tab (skip row 1 metadata if present)
result = sheets.values().get(spreadsheetId=SHEET_ID, range=f"'{tab}'!A2:G200").execute()
rows = result.get('values', [])
header = rows[0]
data = rows[1:]

# Score each row, sort descending
scored = sorted([(score(row), row) for row in data], key=lambda x: x[0], reverse=True)

# Add Priority Score column to header
new_header = header + ['Priority Score']
new_rows = [new_header] + [[*row, str(total)] for total, row in scored]

# Clear and rewrite
sheets.values().clear(spreadsheetId=SHEET_ID, range=f"'{tab}'!A2:H200").execute()
sheets.values().update(spreadsheetId=SHEET_ID, range=f"'{tab}'!A2", valueInputOption='RAW', body={'values': new_rows}).execute()
```

**Pitfall:** Always delete bottom-to-top when removing multiple rows from the same tab — row indices shift after each deletion. Use `batchUpdate` with `deleteDimension` requests ordered from highest to lowest row index.

### Workflow: Remove Irrelevant Listings
- Identify rows by keyword scan (food, construction, retail, etc.)
- Use `batchUpdate` with `deleteDimension` requests
- Sort delete requests highest row index first within each tab to avoid index drift
- Scan all tabs, not just the latest — duplicates often appear across runs

### Workflow: Build a Top 50 Priority Tab (cross-sheet)
When user wants the best 50 jobs ranked across multiple sheets/tabs:

```python
# Pull from all relevant tabs/sheets
all_jobs = []
for each source (Job_Tracker tabs, BuiltInSeattle sheet):
    read rows, skip header
    filter is_excluded(title, company)  # construction, in-store food, etc.
    score each row (title + company + location, max 100)
    append to all_jobs

# Filter threshold + sort + take top 50
top50 = sorted([j for j in all_jobs if j['score'] >= 80], key=lambda x: x['score'], reverse=True)[:50]

# Create new tab in target sheet
sheets.batchUpdate(spreadsheetId=SHEET_ID, body={"requests": [{"addSheet": {"properties": {"title": "Top 50 Priority"}}}]}).execute()

# Write with header
header = [['#', 'Score', 'Title', 'Company', 'Location', 'Link', 'Source']]
data = [[i+1, j['score'], j['title'], j['company'], j['location'], j['link'], j['source']] for i, j in enumerate(top50)]
sheets.values().update(spreadsheetId=SHEET_ID, range="'Top 50 Priority'!A1", valueInputOption='RAW', body={'values': header + data}).execute()
```

**Pitfall:** Job_Tracker tabs don't store source URLs — the scraper captures job details but not links. Only ~84 URLs survive in the CSV. For missing links, either re-scrape or do targeted web searches per company+title.

### Adding a Custom Column (e.g. "Call Received")
```python
# Add header in column G row 2 (or wherever next empty col is)
sheets.values().update(spreadsheetId=SHEET_ID, range=f"'{tab}'!G2", valueInputOption='RAW', body={'values': [['Call Received']]}).execute()
# Mark specific row
sheets.values().update(spreadsheetId=SHEET_ID, range=f"'{tab}'!G24", valueInputOption='RAW', body={'values': [['Yes']]}).execute()
```

## Workflow: Merge Multiple Tabs Into One Named Tab

When multiple scraper output tabs accumulate (e.g. several runs from the same day), merge them:

1. Read all tabs after the target boundary tab (e.g. everything after "May")
2. Use Job URL (col index 5 in standard schema) as the dedupe key
3. Detect and skip stray headers — if `row[0]` matches the known header's first value, it's a header row
4. Watch for cross-schema rows — some tabs use a different column order (`Status | Company | Title | Location | Score | Source | Posted | Job URL | Notes`). Detect by checking if `row[0]` is a status value like "Not Applied" or if the header row has "Status" as col 0. Remap those rows to the standard schema before merging.
5. Create the new named tab, write merged data, delete the old tabs

```python
# Standard schema: Company(0), Title(1), Location(2), Resume(3), Description(4), Job URL(5), Salary(6), Posted(7), Source(8), Score(9)
# Alt schema:      Status(0), Company(1), Title(2), Location(3), Score(4), Source(5), Posted(6), Job URL(7), Notes(8)

def normalize_row(row, detected_schema):
    if detected_schema == 'alt':
        # remap alt → standard
        return [row[1], row[2], row[3], '', '', row[7] if len(row) > 7 else '', 'Not listed', row[6] if len(row) > 6 else '', row[5] if len(row) > 5 else '', row[4] if len(row) > 4 else '']
    return row

def detect_schema(header_row):
    if header_row and header_row[0].lower() == 'status':
        return 'alt'
    return 'standard'
```

**Pitfall:** A stray header row with alt schema will be treated as a data row unless you explicitly detect it. Check first row of each tab — if it looks like a header (contains "Company", "Title", "Status"), skip it.

**Pitfall:** After merge, always verify last N rows of the new tab — stray alt-schema rows that slipped through will show up with "Not Applied" in the Company column.

**Typical yield:** 7 tabs with ~515 raw rows → ~154 unique after URL dedupe (~360 dupes removed across repeat runs).

## Auto-Push to Google Sheets (BUILT)

After each scrape run, `push_to_sheets.py` automatically writes jobs to a new dated tab in the Job_Tracker sheet — including the Job URL column.

**Script:** `/home/hermes/jobs/push_to_sheets.py`
**Triggered by:** scraper.py at the end of every run (auto-imported)
**Tab naming (FIXED 2026-05-05):** Now uses `%-m/%-d` format (e.g. `5/5`, `5/6`) — one tab per day, overwrites if run again same day. Old behavior created a new `YYYY-MM-DD HH:MM` timestamped tab on every run, causing tab explosion. If tab already exists, it's cleared and rewritten.
**Columns written:** Company | Title | Location | Resume | Description | Job URL | Salary | Posted | Source | Score

The scraper's `run()` tail calls it:
```python
try:
    import push_to_sheets
    pushed = push_to_sheets.push_jobs()
except Exception as e:
    print(f"Sheets push skipped: {e}")
```

**Pitfall — URL backfill is not possible retroactively.** The CSV only holds ~84 URLs per run (those scraped in that specific run). Jobs from older tabs/runs don't have stored URLs. If links are missing in older tabs:
- Only 3/32 can be recovered from CSV for a given tab
- For the rest, use targeted web searches (company + title + "job Seattle" on Indeed/LinkedIn)
- Search URLs (not direct postings) are acceptable as fallback — they route to the right company/title search
- Going forward, every new scrape run will capture URLs cleanly via `push_to_sheets.py`

## On-Demand Named Tab Run (custom date window)

When user requests a scrape for a specific date range (e.g. "last 3 days") and wants a named tab (e.g. "MAY 3rd") instead of the auto-timestamp tab:

1. Write a temp runner script that patches `hours_old` and `results_wanted` inline (read scraper.py, str-replace, write to `scraper_<name>_temp.py`)
2. Run the temp script — it will auto-push to a timestamped tab via `push_to_sheets.py`
3. After the run, separately push `jobs.csv` to the custom-named tab using the Sheets API directly
4. Cleanup the temp script after

**hours_old values:**
- Last 3 days → 72
- Last week → 168 (default)
- Last 2 weeks → 336

**Pitfall:** The auto-push inside scraper.py always uses a timestamp tab name. To get a custom name, always do a second push after the run with the named tab explicitly.

## BuiltInSeattle Company Name Backfill

BIS listing pages don't include company names — they come in blank. To backfill:

1. Identify rows where `Source == 'builtinseattle'` and `Company` is empty
2. Use Playwright headless Chromium to visit each job URL individually
3. Extract company from JSON-LD `JobPosting` block → `hiringOrganization.name`
4. Filter out generic values: `'built in seattle'`, `'builtinseattle'`, `'built in'`
5. Write back to CSV and batch-update the Sheets tab

**Extraction order (JSON-LD is most reliable):**
```python
blocks = re.findall(r'<script[^>]+type="application/ld\+json"[^>]*>(.*?)</script>', content, re.DOTALL)
for block in blocks:
    data = json.loads(block)
    items = data['@graph'] if '@graph' in data else [data]
    for item in items:
        if item.get('@type') == 'JobPosting':
            return item.get('hiringOrganization', {}).get('name', '')
```

**Pitfall:** BIS job pages are slow — add `time.sleep(2)` after `domcontentloaded` and `time.sleep(0.5)` between requests to avoid rate limits. Expect ~54 missing out of ~103 BIS jobs per run.

**Sheet batch update for backfill:**
```python
updates = []
for sheet_row_idx, sheet_row in enumerate(sheet_rows[1:], start=2):
    if source == 'builtinseattle' and not company_val:
        # match by title to CSV row, get filled company
        updates.append({'range': f"'{TAB}'!A{sheet_row_idx}", 'values': [[company]]})
sheets.values().batchUpdate(spreadsheetId=SHEET_ID, body={'valueInputOption': 'RAW', 'data': updates}).execute()
```

## Master Tracker Tab (BUILT — 2026-05-03)

`push_to_sheets.py` now upserts every scrape run into a persistent **Master Tracker** tab in addition to creating the dated raw tab. This is the canonical running list of all jobs seen.

**Tab name:** `Master Tracker` (index 0, always first tab)
**Columns:** Status | Company | Title | Location | Salary | Score | Source | Posted | Date Added | Job URL | Notes
**Status default:** `Not Applied` (change to Applied / Interviewing / Rejected / Offer manually)
**Dedupe key:** Job URL — jobs already in Master Tracker are skipped on subsequent runs

**How it works in push_to_sheets.py:**
1. Creates dated raw tab as before (existing behavior preserved)
2. Reads all existing URLs from Master Tracker column J
3. Appends only new jobs not already present
4. Prints `Added N new jobs to Master Tracker (M duplicates skipped)`

If Master Tracker tab doesn't exist yet, it's created automatically with the correct header.

**Pitfall:** Master Tracker must be created before running push_to_sheets.py for the first time — or let push_to_sheets.py create it on first run. Do NOT manually rename or delete the tab or dedupe will break.

## Automation Pipeline (BUILT — 2026-05-05)

Three files form the full pipeline:

1. `scraper.py` — collect + filter + score + write CSV + write alert_jobs.json + write hot_companies.json
2. `push_to_sheets.py` — daily tab + Master Tracker upsert + Hot Companies tab + formatting
3. `notify_jobs.py` — WhatsApp alert for score 40+ jobs + top 5 hot companies

**Cron schedule:** Monday + Thursday 7AM (`0 7 * * 1,4`) — job ID `e57503e01968` (was daily, updated 2026-05-06)

Run manually:
```bash
cd /home/hermes/jobs
python3 scraper.py && python3 push_to_sheets.py && python3 notify_jobs.py
```

**Applied Job Deduplication (UPDATED — 2026-05-06)**

`push_to_sheets.py` reads Master Tracker **before** writing the daily tab. Any job URL already present in Master Tracker (regardless of status) is excluded from the daily tab. This keeps the daily tab clean — only genuinely new jobs appear each run.

The sent_jobs.txt file (`/home/hermes/jobs/sent_jobs.txt`) tracks URLs already WhatsApp-alerted so the same job is never re-notified.

## Hot Companies Tab (BUILT — 2026-05-05)

`push_to_sheets.py` writes a **Hot Companies** tab after each run from `hot_companies.json`.

**Columns:** Company | Open Roles | Remote Roles | Top Score | Roles
**Sorted by:** remote_roles desc, then top_score desc
**Only includes:** companies with 2+ relevant roles AND at least 1 remote role

This is the primary answer to "which US companies are hiring the most remote ops/coordinator roles."

## Master Tracker Formatting (BUILT — 2026-05-05)

After each upsert, `push_to_sheets.py` applies:
- Sort by Score column (col F) descending, skipping header
- Green highlight: Score >= 40
- Yellow highlight: Score 25-39
- Frozen header row + bold header

**Pitfall:** `sortRange` requires all columns in the range to be specified. If a new column is added to Master Tracker, update `endColumnIndex` in the sort request.

## Output Files

| File | Contents |
|---|---|
| `/home/hermes/jobs/jobs.csv` | All filtered+scored jobs from latest run |
| `/home/hermes/jobs/alert_jobs.json` | Jobs scoring 40+ (not yet sent) |
| `/home/hermes/jobs/hot_companies.json` | Companies with 2+ remote roles, ranked |
| `/home/hermes/jobs/sent_jobs.txt` | URLs already WhatsApp-alerted |

## International Location Filter (ADDED 2026-05-06)

Jobs with international locations must be blocked even if the title says "remote". Added `is_international_only(location)` check in `apply_filters()` before seniority/title checks:

```python
INTERNATIONAL_PATTERNS = [
    r"\bcanada\b", r"\buk\b", r"\bunited kingdom\b", r"\bengland\b", r"\bindia\b",
    r"\baustralia\b", r"\beurope\b", r"\bgermany\b", r"\bfrance\b", r"\bspain\b",
    r"\bmexico\b", r"\bbrazil\b", r"\blatam\b", r"\bemea\b", r"\bapac\b",
    r"\bsingapore\b", r"\btoronto\b", r"\bvancouver\b", r"\blondon\b",
    r"\bberlin\b", r"\bamsterdam\b", r"\bparis\b", r"\bdublin\b", r"\bsydney\b",
    r"\bmelbourne\b", r"\bsao paulo\b", r"\bmexico city\b", r"\bnew zealand\b",
]

def is_international_only(location):
    return matches_any(str(location).lower(), INTERNATIONAL_PATTERNS)
```

Applied in `apply_filters()` right after the company blocklist check, and also in the post-LinkedIn-description re-filter pass.

## Senior-Level Description Filter (ADDED 2026-05-06)

Title-level seniority exclusions do not catch jobs that are senior in practice but have generic titles. Added `seniority_ok(description)` that rejects any job requiring 5+ years experience:

```python
SENIOR_YEARS_PATTERNS = [
    r"\b[5-9]\+\s*years?\s+(?:of\s+)?(?:experience|exp)\b",
    r"\b[5-9]\s+or\s+more\s+years?\b",
    r"\bminimum\s+(?:of\s+)?[5-9]\s+years?\b",
    r"\bat\s+least\s+[5-9]\s+years?\b",
    r"\b1[0-9]\+?\s*years?\s+(?:of\s+)?(?:experience|exp)\b",
    r"\b[5-9]\s+to\s+\d+\s+years?\s+(?:of\s+)?(?:experience|exp)\b",
]
```

Also patched `\bsr\.` (with period) into `HARD_EXCLUDE_TITLE` — the old `\bsr\b` missed "Sr. Project Manager".

Applied in both `apply_filters()` and the post-description re-filter pass.

## Claude Project Reference Doc (BUILT — 2026-05-08)

A standalone `.md` file exists for uploading into a Claude Project or Claude Cowork session so Claude can operate the scraper without needing Hermes context.

**File:** `/home/hermes/jobs/scraper_cowork.md`

**Contents:** All 5 sources with endpoints + logic, full filter pipeline (9 steps in order), scoring breakdown with exact point values, output files, how to run/modify/debug, and a "Common Tasks for Claude" section covering: add a company, debug missing jobs, run the scraper, update blocklist.

**When to regenerate:** If scraper logic changes significantly (new sources, filter changes, scoring adjustments), re-read `scraper.py` end-to-end and rewrite the file. Deliver via MEDIA: attachment so user can re-upload to their Claude project.

**Pattern (reusable):** When a complex script lives on Hermes and the user wants to operate it via a separate Claude Project (not Hermes), produce a self-contained `.md` reference that covers: what it does, how it works, all configurable params, output files, common tasks with exact commands, and known issues. Format it as prose + tables + code blocks — no Hermes-specific context, no credential values.

## Source Toggle (UPDATED 2026-05-08)

Greenhouse, Lever, and WWR are **disabled** in the current scraper. Only LinkedIn, Indeed (via JobSpy), and BuiltInSeattle are active. To re-enable, restore the `run()` function calls for those sources.

In `run()`, the disabled sources are stubbed out:
```python
# Greenhouse, Lever, and WWR disabled — LinkedIn/Indeed/BuiltInSeattle only
gh_jobs, lever_jobs, wwr_jobs = [], [], []
```

**Why disabled:** Tanzim's preference is quality over volume — Greenhouse/Lever boards skew senior-heavy, WWR is low signal for his target titles. Re-enable if coverage drops below 80 filtered jobs per run.

## Daily Tab = Full Snapshot (FIXED 2026-05-08)

The daily tab (e.g. `5/8`) should contain **all filtered jobs from that run**, not just ones new to Master Tracker. The bug was filtering daily tab rows by `existing_urls` — this caused the daily tab to show only 23 of 101 jobs.

**Fixed in push_to_sheets.py:** `data_rows` no longer filters by `existing_urls`. Master Tracker still deduplicates — only truly new jobs get appended there. Daily tab = full snapshot always.

```python
# CORRECT — daily tab is full snapshot
data_rows = [[...] for r in rows]  # all rows, no URL filter

# WRONG — was filtering by Master Tracker existing URLs
data_rows = [[...] for r in rows if r.get('URL', '').strip() not in existing_urls]
```

## Priority Titles — Junior/Entry/Associate Variants (ADDED 2026-05-08)

Expanded `PRIORITY_TITLES` to catch entry-level and associate-level roles more aggressively:

```python
PRIORITY_TITLES = [
    # original
    "project coordinator", "program coordinator",
    "assistant project manager", "associate project manager", "junior project manager",
    "assistant manager",
    "implementation coordinator", "operations coordinator",
    "onboarding specialist",
    # added 2026-05-08
    "junior coordinator", "junior analyst", "junior specialist",
    "entry level", "entry-level",
    "associate coordinator", "associate analyst", "associate specialist",
    "associate program", "associate operations",
]
```

`results_wanted` also bumped from 30 → 50 per JobSpy search term to hit ~100 filtered jobs per run.

## Target: 100 Filtered Jobs Per Run

Current design finds 100+ filtered jobs per run but only pushes "new" ones to the daily tab (fixed above). The scraper does NOT iterate until 100 new-to-sheet jobs are found — it runs once and pushes what it finds. The 100 target refers to filtered output, not net-new to the sheet.

If you need 100 truly new jobs each run, the pipeline would need to: check new count post-dedup, expand `hours_old` or add more search terms, and re-run until threshold is met. Not yet built.

## Wide-Window Re-Run Pattern (when net-new count is too low)

When a normal scrape run yields fewer than 50 net-new jobs to Master Tracker, run a wider variant without modifying the main scraper:

```bash
sed 's/hours_old=168/hours_old=336/g; s/results_wanted=50/results_wanted=75/g' scraper.py > scraper_wide.py
/home/hermes/.hermes/hermes-agent/venv/bin/python3 scraper_wide.py
```

- `hours_old=336` = 14-day window (vs default 7)
- `results_wanted=75` = 75 per search term (vs default 50)
- Output still goes to `jobs.csv` and pushes to sheets normally
- Clean up: `rm scraper_wide.py` after run

**Trigger:** net-new count < 50 after a normal run. Check the push_to_sheets output line: `Added N new jobs to Master Tracker (M dupes skipped)` — if N < 50, run wide variant.

## Next Steps (not yet built)
- Iterating scraper: loop until 100 net-new jobs reach the sheet (expand hours_old → add terms → re-run)
- Entry-level signal boost: +10 for "0-2 years", "1-3 years", "entry level", "no prior experience" in description
- Bump JobSpy `hours_old` from 168 to 336 (14 days) for better coverage
- Greenhouse/Lever remote detection: check description for remote signals before dropping on location mismatch

## Industry/Role Exclusion Filter (ADDED 2026-05-08)

Beyond company blocklist and title seniority, a broad `INDUSTRY_EXCLUDE_PATTERNS` list blocks irrelevant role types that slip through title filters. Applied in `apply_filters()` right after company blocklist and empty-company checks.

Patterns cover: social worker, social service, supportive housing, homeless, mental health, substance abuse, foster care, case manager, case management, behavioral health, domestic violence, refugee, low income housing, veterans affairs, department of veterans, clinical nurse, nurse coordinator, oncology, chiropractic, patient care coordinator, school district, preparatory school, volleyball, athletic coordinator, agriculture, agrilytics, fertility valuation, bilingual, bilingue.

Also added empty company check: if `company.strip()` is empty, drop the row (LinkedIn scrape gaps produce blank-company rows that are useless).

**Pattern:** These exclusions should also be applied when cleaning an existing sheet tab — scan `title + company` combined string against all patterns and remove matching rows.

## Sheet Cleaning Workflow (ADDED 2026-05-08)

When a tab has bad rows (bilingual roles, social services, healthcare, no company name), clean it in Python:
1. Pull tab rows via Sheets API
2. For each row: skip if no company, skip if title+company matches any BAD_PATTERN
3. Overwrite tab with keep rows only (clear then update)
4. Re-apply formatting after cleaning

Typical yield: ~37 removed from 101 rows.

## Import External XLSX to Job Tracker (ADDED 2026-05-13)

When user provides an xlsx file (from Claude Cowork, manual export, etc.) and wants it pushed to a new tab:

**Workflow:**
1. Load xlsx with `openpyxl` — install via `pip3 install openpyxl` if needed
2. Extract all rows as string values
3. Create new tab via Sheets API `addSheet` request
4. Write data via `values().update()`
5. Convert URL column to clickable hyperlinks via `batchUpdate` with `updateCells` + `textFormat.link`
6. Apply standard formatting (wrap, middle align, center)

**Hyperlink conversion code:**
```python
import openpyxl
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

# Load xlsx
wb = openpyxl.load_workbook('/path/to/file.xlsx')
ws = wb.active
rows_data = [[str(cell.value) if cell.value else "" for cell in row] for row in ws.iter_rows()]

# Connect + create tab
creds = Credentials.from_authorized_user_file('/home/hermes/.hermes/google_token.json')
sheets = build('sheets', 'v4', credentials=creds).spreadsheets()

sheets.batchUpdate(spreadsheetId=SHEET_ID, body={
    "requests": [{"addSheet": {"properties": {"title": TAB_NAME}}}]
}).execute()

# Get tab ID
meta = sheets.get(spreadsheetId=SHEET_ID).execute()
tab_id = next(s['properties']['sheetId'] for s in meta['sheets'] if s['properties']['title'] == TAB_NAME)

# Write data
sheets.values().update(spreadsheetId=SHEET_ID, range=f"'{TAB_NAME}'!A1",
    valueInputOption='RAW', body={'values': rows_data}).execute()

# Find URL column and convert to hyperlinks
header = rows_data[0]
url_col_idx = header.index('URL') if 'URL' in header else -1

if url_col_idx >= 0:
    requests = []
    for row_idx, row in enumerate(rows_data[1:], start=2):
        if url_col_idx < len(row) and row[url_col_idx].startswith('http'):
            requests.append({
                "updateCells": {
                    "range": {"sheetId": tab_id, "startRowIndex": row_idx - 1, "endRowIndex": row_idx,
                              "startColumnIndex": url_col_idx, "endColumnIndex": url_col_idx + 1},
                    "rows": [{"values": [{"userEnteredFormat": {"textFormat": {"link": {"uri": row[url_col_idx]}}}}]}],
                    "fields": "userEnteredFormat.textFormat.link"
                }
            })
    for i in range(0, len(requests), 100):  # batch in chunks
        sheets.batchUpdate(spreadsheetId=SHEET_ID, body={"requests": requests[i:i+100]}).execute()
```

**Pitfall:** openpyxl may store hyperlinks separately from cell values. Check `cell.hyperlink.target` if URLs appear as display text only. If URLs are plain text in cells, the code above handles it.

**Pitfall:** Tab names with `/` (e.g. `05/13`) work fine — just quote the tab name in range strings.

## Email Rejection Pattern Analysis (ADDED 2026-05-16)

Periodically scan Gmail inbox + trash for job application emails to identify failure patterns and refine scraper filters.

**When to run:** Every 2-4 weeks, or when callback rate drops

**Workflow:**
1. Search Gmail for job emails: `job OR application OR interview OR recruiter OR hiring`
2. Also search trash: `in:trash job OR application OR interview OR recruiter`
3. Categorize results into: positive movement (callbacks, offers), rejections, auto-confirms
4. Identify patterns in rejections by: company type, role seniority, title keywords, industries

**Typical failure patterns to watch for:**
- **Senior/Strategic roles:** "Strategic CSM", "Technical PM", "Program Manager Commerce" → instant rejects from big tech
- **Big tech companies:** PostHog, Anduril, Valve, Figma, ŌURA → fast rejections, resume mismatch
- **Industry mismatch:** Engineering/construction firms (KPFF, Beck Group) rejecting for "Coordinator"
- **Language requirements:** "French Speaking", "Bilingual" roles → wrong fit

**What to update based on findings:**
- `COMPANY_BLOCKLIST`: Add companies with consistent fast-reject pattern
- `HARD_EXCLUDE_TITLE`: Add title keywords that correlate with rejections (e.g. "strategic")
- `INDUSTRY_EXCLUDE_PATTERNS`: Add language/specialty requirements
- `INDUSTRY_BOOST`: Remove companies that moved to blocklist

**Example update (2026-05-16):**
- Added to blocklist: PostHog, Anduril, Valve, Gusto, ŌURA, Kalepa, SOLV Energy, Yoodli, Thrive Market, Beck Group, Klaviyo, KPFF, WSP
- Added to title exclude: `\bstrategic\b`, `technical program manager`, `program manager.?commerce`
- Added to industry exclude: French/Spanish/German/Mandarin/Japanese speaking patterns
- Removed ŌURA from INDUSTRY_BOOST (moved to blocklist)

## Email Rejection Pattern Analysis (ADDED 2026-05-16)

Periodically scan Gmail inbox + trash for job application emails to identify failure patterns and refine scraper filters.

**When to run:** Every 2-4 weeks, or when callback rate drops

**Workflow:**
1. Search Gmail for job emails: `job OR application OR interview OR recruiter OR hiring`
2. Also search trash: `in:trash job OR application OR interview OR recruiter`
3. Categorize results into: positive movement (callbacks, offers), rejections, auto-confirms
4. Identify patterns in rejections by: company type, role seniority, title keywords, industries

**Typical failure patterns to watch for:**
- **Senior/Strategic roles:** "Strategic CSM", "Technical PM", "Program Manager Commerce" → instant rejects from big tech
- **Big tech companies:** PostHog, Anduril, Valve, Figma, ŌURA → fast rejections, resume mismatch
- **Industry mismatch:** Engineering/construction firms (KPFF, Beck Group) rejecting for "Coordinator"
- **Language requirements:** "French Speaking", "Bilingual" roles → wrong fit

**What to update based on findings:**
- `COMPANY_BLOCKLIST`: Add companies with consistent fast-reject pattern
- `HARD_EXCLUDE_TITLE`: Add title keywords that correlate with rejections (e.g. "strategic")
- `INDUSTRY_EXCLUDE_PATTERNS`: Add language/specialty requirements
- `INDUSTRY_BOOST`: Remove companies that moved to blocklist

**Example update (2026-05-16):**
- Added to blocklist: PostHog, Anduril, Valve, Gusto, ŌURA, Kalepa, SOLV Energy, Yoodli, Thrive Market, Beck Group, Klaviyo, KPFF, WSP
- Added to title exclude: `\bstrategic\b`, `technical program manager`, `program manager.?commerce`
- Added to industry exclude: French/Spanish/German/Mandarin/Japanese speaking patterns
- Removed ŌURA from INDUSTRY_BOOST (moved to blocklist)

## Email Triage for Interview Opportunities (ADDED 2026-05-17)

Scan inbox for actionable job search signals — interview invites, assessment requests, recruiter outreach — and distinguish from rejections and auto-confirms.

**When to run:** On-demand ("scan my email"), or weekly alongside scraper runs

**Gmail search query (broad net):**
```bash
$GAPI gmail search "newer_than:14d" --max 30
```

Then manually filter results for job-related signals. Avoid over-filtering in the query — recruiter emails often don't contain obvious keywords.

**Signal categories:**

| Category | Action | Examples |
|----------|--------|----------|
| Interview invite | Schedule/complete ASAP | "Let's talk", "phone screen", "video interview", AI recruiter invite |
| Assessment request | Complete within deadline | IBM competency assessment, HireVue, Codility, work sample |
| Recruiter outreach | Respond same day | "Reviewed your background", "would like to connect", candidate portal invite |
| Onboarding/offer | Background check, paperwork | "Welcome to", "Begin your onboarding", FINRA screening |
| Rejection | Archive | "Unfortunately", "other candidates", "position has been filled" |
| Auto-confirm | Ignore | "Thank you for applying", "application received" |

**Triage output format (for user):**

```
**Action needed:**
1. **Company — Role** — what to do, deadline if any
2. ...

**Progressing (no action):**
- Company — status update

**Rejections:**
- Company, Company, Company
```

**Pitfalls:**
- AI recruiter invites (ITC Avery, Paradox Olivia) are real interviews — don't dismiss as spam
- Candidate portal invites often precede interview scheduling — set them up promptly
- Assessment deadlines are usually 7 days — check original email date
- Reminder emails (2nd, 3rd) indicate urgency — user may have missed the first
- Some recruiters use generic "Thank you for applying" subject but body contains interview request — always read full body for ambiguous ones

**Integration with Interviews sheet:**
After triage, update the Interviews tab in Job Tracker with new actionable items:
- Sheet ID: `1v6CY46PBfGyrde8uuMzPv1cETZrOiflUj_HY34SJC_Q`
- Tab: `Interviews` (gid 1499246630)
- Columns: Company | Role | Stage | Next Step | Date Added | Notes

## Default Cell Formatting (ADDED 2026-05-08)

All tabs (daily + Master Tracker) get wrap + middle align + center align applied by default after every write. Baked into `push_to_sheets.py` via `apply_cell_formatting()`. Call after `clear_and_write()` for both daily tab and Master Tracker.

```python
def apply_cell_formatting(sheets, sheet_id, num_rows):
    sheets.batchUpdate(spreadsheetId=SHEET_ID, body={"requests": [{
        "repeatCell": {
            "range": {"sheetId": sheet_id, "startRowIndex": 0,
                      "endRowIndex": num_rows + 1, "startColumnIndex": 0, "endColumnIndex": 11},
            "cell": {"userEnteredFormat": {
                "wrapStrategy": "WRAP",
                "verticalAlignment": "MIDDLE",
                "horizontalAlignment": "CENTER",
            }},
            "fields": "userEnteredFormat(wrapStrategy,verticalAlignment,horizontalAlignment)"
        }
    }]}).execute()
```