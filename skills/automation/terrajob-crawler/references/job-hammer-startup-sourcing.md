# Job Hammer — Startup Job Sourcing Strategies

## Context
Job Hammer's primary JobSpy + BuiltInSeattle approach surfaces ~28 job openings across 60 days (mostly Coordinator roles). To access early-stage startup hiring, three complementary source patterns were developed June 2026.

## Pattern 1: Startup Job Board APIs
**Files:** `startup_jobs.py`

Sources crawled:
- **AngelList/Wellfound** — Series A/B companies, public API (`wellfound.com/api/jobs`)
- **startup.jobs** — dedicated early-stage board, public feed
- **CrunchBoard** — Crunchbase job aggregator (filters by funding stage)

**Implementation:**
```python
def fetch_wellfound(roles=['coordinator', 'specialist', 'analyst'], locations=['remote']):
    params = {'query': role, 'location': 'remote', 'type': 'fulltime'}
    r = requests.get('https://wellfound.com/api/jobs', params=params)
    # Yields ~10 jobs per role query (limit to 3 roles to avoid rate limits)
```

Rate limit: 0.5s between requests. No auth required.

**Output:** `output/startup_jobs.csv` (same format as main crawler)

**Gotchas:**
- AngelList API is gated; Wellfound endpoint works but rate-limits after ~50 requests/min
- startup.jobs and CrunchBoard have inconsistent API availability — both are fallback sources
- Expect ~30-50% API downtime across the three sources; treat as "best effort" supplements

## Pattern 2: VC-Backed Company ATS Crawling
**Files:** `crunchbase_vc_crawler.py`

**Strategy:** Instead of scraping job boards, directly hit Workday/Lever/Greenhouse instances of known VC-backed startups (Series A/B/C/D funded). This surfaces internal postings before they hit job boards.

**Company seed list (13 companies):**
| Company | Funding Stage | ATS Type | Coordinator Hiring Signal |
|---------|---------------|----------|--------------------------|
| Rippling | Series C | Lever | High (ops automation) |
| Mercury | Series C | Lever | High (fintech) |
| Notion | Series D | Lever | High (platform ops) |
| Airtable | Series D | Lever | High (platform ops) |
| Sigma Computing | Series D | Lever | Medium (data analyst) |
| Hex | Series B | Lever | Medium (data analyst) |
| Ro | Series D | Lever | High (healthcare ops) |
| Carbon Health | Series C | Greenhouse | High (healthcare ops) |
| Loom | Series D | Lever | Medium (general) |
| Figma | Series D | Lever | Low (design/eng focused) |
| Superhuman | Series B | Lever | Medium (operations) |
| Brex | Series D (IPO track) | Workday | High (finance ops) |
| Airbnb | Series ? (public) | Workday | Medium (competitive) |

**Implementation:**
```python
def fetch_lever_vc(url: str, company: str):
    api_url = f"{url.rstrip('/')}/jobs.json"
    r = requests.get(api_url)  # Returns full job list as JSON array
    for job in r.json():
        yield {
            'company': company,
            'title': job['text'],
            'url': job['hostedUrl'],
            'source': 'crunchbase_lever'
        }
```

Same pattern for Workday (regex parse HTML) and Greenhouse (regex + data-target filter).

**Output:** `output/crunchbase_vc_jobs.csv`

**Timing advantage:** Direct ATS pulls are 2–3 days faster than job board aggregators. Roles show up in Lever.json before they appear on LinkedIn job feed.

**Maintenance:** Every ~6 months, audit the seed list for bankruptcies/acquihires. Add new Series B/C startups in target verticals (fintech, operations, data, fitness, healthcare).

## Pattern 3: Accelerator Cohort Scraping
**Files:** `accelerator_crawler.py`

**Strategy:** Y Combinator, Techstars, 500 Global, and Plug and Play publish cohort lists (companies graduate every batch). For each company, directly crawl their ATS instances. Accelerator-grad companies have high hiring velocity and are early-stage enough to hire coordinators.

**Cohort coverage:**
| Accelerator | Cohorts | # Companies | ATS Types |
|-------------|---------|------------|-----------|
| Y Combinator | S24 (recent), S23, S13, W10, S09 | 7 | Workday, Lever |
| Techstars | Recent ('24) | 2 | Greenhouse, Lever |
| 500 Global | Backlog | 2 | Lever |
| Plug and Play | Backlog | 1 | Workday |

**Key companies in current seed:**
- **Y Combinator S24 (hot):** Ramp, Catch, Pivot Tables, tinybird, Paradime
- **Y Combinator S23 (warm):** Idle, Brex, Airbnb
- **Techstars '24:** Moment, Joist

**Implementation:**
Same as Pattern 2 — crawl Workday/Lever/Greenhouse instances for each company. Cohort tag added to source column for tracking.

**Output:** `output/accelerator_jobs.csv`

**Timing advantage:** Techstars/YC companies often hire for ops/coordinator roles in their first 12 months post-graduation. Catch these roles early by monitoring cohort pages monthly.

**Maintenance:** Update cohort list quarterly with new cohort announcements. Remove companies that acquired/IPO'd (they shift to enterprise hiring, less coordinator-focused).

## Integration with Main Crawler
All three sources feed into a single pool before the filter pipeline runs:

```
seed_companies.py          → output/seed_companies.csv
startup_jobs.py            → output/startup_jobs.csv
crunchbase_vc_crawler.py   → output/crunchbase_vc_jobs.csv
accelerator_crawler.py     → output/accelerator_jobs.csv
JobSpy (main)              → output/jobs.csv
BuiltInSeattle (main)      → merged into output/jobs.csv
                ↓
           merge all CSVs
                ↓
         apply scout_profile.json filters
         (title boost, salary band, experience level, etc.)
                ↓
         dedup by URL (dedup_index.json)
                ↓
         top 50 by SCORE
                ↓
      sync_to_sheet.py: create per-job tabs + master_tab

```

**Execution order (important for freshness):**
1. Run seed_companies.py first (direct company pages, freshest)
2. Run startup_jobs.py (boards, ~1-day lag)
3. Run crunchbase_vc_crawler.py (VC ATS, ~1-day lag)
4. Run accelerator_crawler.py (cohort ATS, ~1-day lag)
5. Run main crawler (JobSpy + BuiltInSeattle, ~2-3 day lag)
6. Merge, filter, score, sync

## Performance Baseline
As of June 2026:

**Market read (28 jobs, 60-day lookback):**
- 96% Coordinator roles (Project, Account, Operations, Implementation)
- 57% also have "Specialist" in title
- 10.7% are Data roles (emerging signal)
- Coordinator hiring velocity: steady, 0.5 roles/day average

**With expanded startup sources:**
- Expected +20-30% supply increase (AngelList + Crunchbase + accelerators)
- Faster time-to-first-response (direct ATS = 2-3d earlier than job boards)
- Higher signal-to-noise on early-stage companies (Series A/B less likely to ghost)

## Cost
- No API keys required (all public endpoints)
- Rate limits: respect 0.5-1.5s between requests per source
- Estimated runtime: ~3 min for all four startup sources, ~2 min for main crawler = ~5 min total

## Known Issues & Workarounds

### Issue: Lever API endpoint changes
Lever.co sometimes renames the `/jobs.json` endpoint. If a company's Lever page returns 404:
```python
# Fallback: scrape the HTML page directly
r = requests.get(url)
for match in re.finditer(r'<a[^>]*href="([^"]*)"[^>]*>([^<]+)</a>', r.text):
    # Extract job link + title from HTML
```

### Issue: Workday rate limiting (403 Forbidden after 20 requests)
Workday enforces per-IP rate limits. Workaround:
```python
# Add exponential backoff
if status_code == 403:
    wait = 2 ** attempt  # 2, 4, 8, 16s
    time.sleep(wait)
    retry()
```

### Issue: Greenhouse jobs.json doesn't exist for all companies
Some Greenhouse instances use a different API path. Fallback to HTML scrape (works 95% of the time).

## Next Steps (Future Sessions)

### Automation
Wire all four startup crawlers into a cron job that runs daily at 6am (before main crawler). Append all startup-source jobs to a dedicated Google Sheet tab ("Startup Sources") for visibility on what's feeding the filter pipeline.

### Feedback loop
Track which startup-source jobs yield phone screens. Use signals to boost their industry/company signals in next run (+10 boost for "fintech + Lever" if a fintech Lever job got a callback).

### Cohort expansion
Add more accelerators (Techstars global, Y Combinator APAC, Plug and Play cohorts) quarterly as they graduate companies.
