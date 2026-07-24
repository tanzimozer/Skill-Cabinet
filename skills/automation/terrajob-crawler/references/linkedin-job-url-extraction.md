# LinkedIn Job URL Extraction via curl

## Context
LinkedIn job listings don't have stable public search APIs. This technique
extracts confirmed job view URLs from LinkedIn's guest search pages using curl.

## Method

### 1. Search LinkedIn guest search
```bash
curl -s --max-time 20 -L \
  -A 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36' \
  -H 'Accept: text/html,application/xhtml+xml' \
  -H 'Accept-Language: en-US,en;q=0.9' \
  "https://www.linkedin.com/jobs/search/?keywords=JOB+TITLE+COMPANY&location=LOCATION"
```

Include company name in the keywords — it dramatically improves accuracy.

### 2. Extract job IDs from HTML
LinkedIn embeds job IDs as `jobPosting:XXXXXXXXXX` in the page HTML (JSON-LD / tracking data).

```python
import re
job_ids = re.findall(r'jobPosting:(\d+)', html)
# Also works: re.findall(r'"currentJobId":(\d+)', html)
```

The first ID in the list is the top result — usually the right one with company-included search.

### 3. Verify each ID
Fetch the job view page and check `og:title`:

```python
import subprocess, re

def verify_job(job_id, expected_company):
    cmd = ['curl', '-s', '--max-time', '12', '-L',
           '-A', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
           f'https://www.linkedin.com/jobs/view/{job_id}/']
    r = subprocess.run(cmd, capture_output=True, text=True)
    og = re.search(r'<meta property="og:title" content="([^"]+)"', r.stdout)
    title = og.group(1) if og else ""
    # Use len(w) > 2 to avoid false negatives on short names like SPS, WSP, EY
    company_words = [w.lower() for w in expected_company.replace('&','and').split() if len(w) > 2]
    return any(w in title.lower() for w in company_words), title
```

**Do not skip verification.** Search without company name returns unrelated top results frequently.

## Bulk workflow (200+ jobs, session-tested May 2026)

**Use `execute_code`, not subagents** — subagents time out on browser tools; execute_code with curl handles 200+ jobs reliably in one shot.

Two-pass approach:
1. **Pass 1 — bulk search**: search all jobs in batches of 10–20, collect first job ID per listing. Sleep 0.4–0.8s between requests.
2. **Pass 2 — verification sweep**: fetch og:title for every ID, flag mismatches. **~15% mismatch rate** is normal on a large bulk run.
3. **Pass 3 — fix mismatches**: re-search flagged rows with tighter keywords, verify, update sheet cells.

```python
import subprocess, re, time, urllib.parse

jobs = [("Title", "Company", "Location"), ...]
results = []

for title, company, location in jobs:
    kw_enc = urllib.parse.quote(f"{title} {company}")
    loc_enc = urllib.parse.quote(location)
    url = f"https://www.linkedin.com/jobs/search/?keywords={kw_enc}&location={loc_enc}"
    
    cmd = ['curl', '-s', '--max-time', '20', '-L',
           '-A', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
           url]
    r = subprocess.run(cmd, capture_output=True, text=True)
    ids = re.findall(r'jobPosting:(\d+)', r.stdout)
    
    results.append((title, company, location, ids[0] if ids else None))
    time.sleep(0.5)

# Verification sweep
for title, company, location, job_id in results:
    if not job_id:
        continue
    cmd = ['curl', '-s', '--max-time', '10', '-L', '-A', 'Mozilla/5.0',
           f'https://www.linkedin.com/jobs/view/{job_id}/']
    rv = subprocess.run(cmd, capture_output=True, text=True)
    og = re.search(r'<meta property="og:title" content="([^"]+)"', rv.stdout)
    actual = og.group(1) if og else "?"
    company_words = [w.lower() for w in company.replace('&','and').split() if len(w) > 2]
    if not any(w in actual.lower() for w in company_words):
        print(f"MISMATCH row: {company} | {title} | got: {actual[:60]}")
    time.sleep(0.25)
```

## Pitfalls

- **Google/Bing block curl** for `site:linkedin.com` searches — go direct to LinkedIn, not via search engines.
- **Without company in keywords**, the first ID is often a completely unrelated promoted job.
- **Multiple near-identical postings**: same title, same company, multiple Seattle listings with different IDs (e.g. SPS "Client Services Associate" had 4). Pick highest ID (most recent) unless a specific one was visible in screenshots.
- **`og:title` format**: `"COMPANY hiring JOB TITLE in LOCATION | LinkedIn"` — verify company present, not just title.
- **Short company names** (SPS, WSP, EY, MRO, DTN, UST) cause false-negative mismatch flags — use `len(w) > 2` filter on company words, not `len(w) > 3`.
- **Rate**: Sleep 0.3–0.8s between requests. Verification can go faster (0.25s) than search (0.5s).
- **~15% mismatch rate** is normal on bulk first-pass. Always do a verification sweep before writing to the sheet.
- **Mismatches that look correct**: some are just LinkedIn's HTML encoding (`&amp;amp;` in og:title for `&`) — these are real matches, not broken links.
- **Location filter sometimes causes no results** — if a targeted search returns nothing, drop the `&location=` param and search keywords-only.

## Notes
- LinkedIn guest search returns ~82KB HTML pages with embedded job data
- No authentication required for guest job search
- Works reliably as of May 2026; LinkedIn may change HTML structure over time
