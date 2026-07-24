---
name: linkedin-job-scraping
category: research
description: Finding and verifying specific LinkedIn job posting URLs by scraping LinkedIn's guest search HTML via curl.
---

# LinkedIn Job Scraping

## When to use
Tanzim shares screenshots of LinkedIn job listings and wants direct URLs for specific postings — or any task requiring programmatic retrieval of linkedin.com/jobs/view/ links without a logged-in session.

## Key insight
LinkedIn's **guest job search page** (`linkedin.com/jobs/search/?keywords=...&location=...`) returns full HTML — including embedded JSON with `jobPosting:XXXXXXXXXX` URNs — without requiring authentication or a browser. curl with a standard browser User-Agent works reliably.

The **browser tool often times out entirely** on this class of task (VM networking issue). Use `execute_code` with `subprocess` + `curl` instead — it's faster and more reliable.

## Workflow

### Step 1 — Search with title + company keywords
```python
import subprocess, re, time, urllib.parse

keywords = urllib.parse.quote("Job Title CompanyName")
location = urllib.parse.quote("Seattle, WA")
url = f"https://www.linkedin.com/jobs/search/?keywords={keywords}&location={location}"

cmd = [
    'curl', '-s', '--max-time', '20', '-L',
    '-A', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    url
]
html = subprocess.run(cmd, capture_output=True, text=True).stdout
job_ids = re.findall(r'jobPosting:(\d+)', html)
```

**Include company name in the keywords** — it dramatically narrows results and avoids false positives from similarly-titled roles at different companies.

### Step 2 — Verify each candidate ID
```python
def verify_job(job_id):
    cmd = ['curl', '-s', '--max-time', '12', '-L',
           '-A', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
           f"https://www.linkedin.com/jobs/view/{job_id}/"]
    html = subprocess.run(cmd, capture_output=True, text=True).stdout
    og = re.search(r'<meta property="og:title" content="([^"]+)"', html)
    return og.group(1) if og else ""
```

The `og:title` format is: `"CompanyName hiring Job Title in Location | LinkedIn"` — check that both company name and job title appear.

### Step 3 — Handle multiple listings for same role
Some companies (e.g. SPS, KPMG) post the same role across multiple locations with distinct job IDs. Pick the one matching the location from the screenshot.

### Step 4 — Batch parallel approach for 30+ jobs
Run searches in a loop with `time.sleep(0.8)` between requests. Then batch-verify all candidate IDs in a second loop with `time.sleep(0.3)`. Two-pass approach keeps it clean and avoids rate limiting.

## Pitfalls

- **`jobPosting:` URNs are the most reliable ID source** in guest HTML. `currentJobId` and `data-job-id` also work but are less consistent.
- **Search returns the top result, not necessarily the right one.** Always verify the ID against the actual page's og:title before presenting the URL.
- **Google/Bing `site:` searches are unreliable from the VM** — both returned no LinkedIn results in testing (CAPTCHA or bot detection). Go directly to LinkedIn guest search instead.
- **Browser tool may time out entirely** on LinkedIn searches when the VM has network issues. Fall back to curl immediately rather than retrying the browser.
- **SPS has many near-identical Client Services Associate postings** — grab the most recent (highest ID) for the target location.
- **"Confirmed" ≠ verified** — the og:title check must actually contain the company name, not just any keyword from the expected title. Tighten the match logic to avoid false positives.

## Output format
Present as a numbered list grouped loosely by type (consulting, coordinator, analyst, etc.) or just sequentially. Each line:
```
N. **Job Title** – Company
   https://www.linkedin.com/jobs/view/XXXXXXXXXX/
```

## References
- `references/session-2025-bulk-seattle.md` — first large run: 36 jobs from Tanzim's LinkedIn feed screenshots, confirmed IDs included.
