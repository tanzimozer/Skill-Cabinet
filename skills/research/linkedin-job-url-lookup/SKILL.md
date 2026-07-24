---
name: linkedin-job-url-lookup
description: Finding verified LinkedIn job posting URLs for a list of job title + company pairs. Uses curl against LinkedIn's guest search, scrapes jobPosting IDs, and verifies via og:title.
category: research
tags: [linkedin, jobs, scraping, urls, terrjob]
---

# LinkedIn Job URL Lookup

## Use case
Given a list of (job title, company, location) tuples, find the correct `linkedin.com/jobs/view/{id}` URL for each. Used to populate TerraJob sheet.

## Method
Google/Bing block `site:linkedin.com/jobs` queries with CAPTCHAs. LinkedIn's own guest search returns job IDs in HTML as `jobPosting:(\d+)`.

### Step 1 — Search LinkedIn guest search
```python
import subprocess, re, urllib.parse, time

def search_linkedin(title, company, location=""):
    kw_enc = urllib.parse.quote(f"{title} {company}")
    loc_enc = urllib.parse.quote(location)
    url = f"https://www.linkedin.com/jobs/search/?keywords={kw_enc}&location={loc_enc}"
    cmd = ['curl', '-s', '--max-time', '15', '-L',
           '-A', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
           url]
    r = subprocess.run(cmd, capture_output=True, text=True)
    return re.findall(r'jobPosting:(\d+)', r.stdout)

# Rate limit: sleep 0.5–0.8s between requests
```

### Step 2 — Verify job ID matches company
```python
def verify_job(job_id, expected_company):
    cmd = ['curl', '-s', '--max-time', '10', '-L', '-A', 'Mozilla/5.0',
           f"https://www.linkedin.com/jobs/view/{job_id}/"]
    rv = subprocess.run(cmd, capture_output=True, text=True)
    og = re.search(r'<meta property="og:title" content="([^"]+)"', rv.stdout)
    actual = og.group(1) if og else ""
    company_words = [w.lower() for w in expected_company.replace('&', 'and').split() if len(w) > 2]
    return any(w in actual.lower() for w in company_words), actual
```

### Step 3 — Batch verify all IDs
Spot-check ~15 random rows first to gauge accuracy. Then do a full pass. Expect ~10–15% mismatch rate (wrong company in og:title). For mismatches, re-search with tighter keywords (add location, remove stopwords) and verify the next result.

## Batching strategy
- 100 jobs: ~2 min at 0.5s sleep
- 200 jobs: ~4 min
- Verification pass (200 jobs at 0.25s): ~3 min
- Use `execute_code` for large batches to avoid terminal timeout (60s limit)

## Common mismatch causes
- Short company names (SPS, WSP, EY, MRO) match unrelated companies — verify strictly
- Generic titles (Project Manager, Administrative Assistant) return wrong listings — include company in keywords
- Multiple identical job postings (same company, same title, different locations) — use highest job ID (most recent) or filter by location

## Mismatch fix recipe
```python
# Re-search without location filter, include company in title keywords
kw = urllib.parse.quote(f"{title} {company}")
url = f"https://www.linkedin.com/jobs/search/?keywords={kw}"
# Check first 3–5 results, pick first match where company appears in og:title
```

## URL format
```
https://www.linkedin.com/jobs/view/{job_id}
```
No trailing slash. No query params.

## Pitfalls
- `execute_code` has no 60s timeout (unlike terminal). Use it for batches > 50 jobs.
- Browser tool times out on LinkedIn — use curl only.
- Google/Bing `site:linkedin.com/jobs` searches return CAPTCHAs — don't use them.
- LE003 test showed ~10–15% false positives from short company names in verification logic. `len(w) > 2` filter helps but doesn't eliminate — always do a full verify pass.
