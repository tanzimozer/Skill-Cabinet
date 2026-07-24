---
name: instagram-scraper
category: instagram
description: Notes and pitfalls for Instagram hashtag scraping + user enrichment
support_files:
  - templates/html_scraper_batch.py (production-ready HTML scraper for batch crawls)
  - references/html-scraper-implementation-20260605.md (discovery, setup, and decision framework)
  - references/hashtag-discovery-selenium-pivot-june6.md (Selenium + hashtag discovery workflow; why BeautifulSoup fails on JS-rendered pages; user API constraint)
---

## Diagnosis before action

When Instagram crawler reports issues, **always run diagnostics first** — never assume rate-limit from API response alone:

1. **Check libraries installed** — `instagrapi`, `selenium`, `beautifulsoup4`, `requests` in active venv.
2. **Check cookies file** — Path: `~/.hermes/.ig_cookies.json` — must contain: `datr`, `ds_user_id`, `csrftoken`, `ig_did`, `mid`, `sessionid`.
3. **Validate session** — Hit `/api/v1/users/web_profile_info/?username=instagram` with cookies → 200 = session live, 429 = throttled (not expired), 401 = stale.
4. **Test HTML parser separately** — Even if API is 429, HTML scraper (BeautifulSoup + direct profile page fetch) often works — parse `og:description` for bio.

### HTML scraper fallback (low-risk when API is throttled)

When API returns 429, switch to HTML scraping:
- **Endpoint:** Direct profile page: `https://www.instagram.com/{username}/`
- **Parser:** BeautifulSoup to extract meta tags (`og:description` for bio, `og:image` for profile pic)
- **Rate limit risk:** Low — Instagram detects bots less aggressively on HTML parsing
- **Speed:** 1–2 seconds per profile (slower than API, but safer)
- **Setup:** `pip install beautifulsoup4` in venv

**Example:**
```python
from bs4 import BeautifulSoup
import requests

response = requests.get(f"https://www.instagram.com/{username}/", 
                       cookies=cookies, headers=headers, timeout=8)
if response.status_code == 200:
    soup = BeautifulSoup(response.text, 'html.parser')
    og_desc = soup.find("meta", property="og:description")
    bio = og_desc.get("content") if og_desc else ""
```

See `templates/html_scraper_batch.py` for a full production-ready batch crawler (load cookies, stagger requests, save results).

### Rate-limit decision framework

When Instagram blocks with 429:

| Situation | Safe to retry now | Workaround |
|-----------|-------------------|-----------|
| API 429, HTML 200 | No (force = hard lock) | Switch to HTML scraper |
| Session 401 | No (stale) | Re-paste cookies from browser |
| Tag sections work, enrich fails | Yes, stagger (1–2 req/min) | Use tag sections data directly, skip enrich |
| All endpoints 429 | No | Wait 1–2 hours OR use residential proxy |

**Never force requests during 429** — Instagram's anti-bot system will escalate to account lock (24–72 hours).

## Known pitfalls

### Enrich endpoint silent failure
`/api/v1/users/{uid}/info/` returns HTML (200 + login/challenge page) when session is rate-limited or cookies are stale. `r.json()` throws silently → every user drops out before follower/gender check.

**Fix:** Always check `'application/json' in r.headers.get('content-type', '')` before parsing. If HTML, treat as rate-limited and back off 30–60s.

### Avoid separate enrich when possible
Tag sections response (`/api/v1/tags/{tag}/sections/`) includes `user.pk`, `user.username`, and sometimes follower_count inline. Use that data first — skip the enrich call entirely when the fields you need are already present.

### Rate limit pattern
- Tag sections API: works even on limited sessions
- `web_profile_info`: rate limits first (~30–60 min recovery)
- `/api/v1/users/{uid}/info/`: rate limits hardest — returns HTML 200, not 429

### Session freshness
Cookies expire. If tag fetch returns candidates but enrich returns 0, session is likely stale. Re-paste cookies from browser → vault.

## Hashtag Discovery & Profile Extraction (June 6 2026 learnings)

### Hardcoded username lists don't work reliably

When scraping a static list of usernames (e.g., fitness influencers) via HTML:
- **Celebrity/verified accounts** (kendalljenner, emrata, gigi_hadid) → **200 OK**, bio extracted ✅
- **Generic handles** (fitnessgirl_, beautyinfluencer_, gymgirlsonly) → **skip/private**, 0 results ❌

**Why:** Generic account handles are often private, shadowbanned, deleted, or blocking HTML requests. High-follower public accounts have reliable HTML surface area.

**Lesson:** Don't build discovery on hardcoded lists. Use real hashtag mining instead.

### Hashtag discovery requires Selenium (not BeautifulSoup)

**Problem:** Instagram renders hashtag pages client-side (JavaScript). BeautifulSoup fetches static HTML skeleton with no usernames.

**Solution:** Use Selenium + your cookies to:
1. Load hashtag page dynamically (JS renders the feed)
2. Wait for post elements to populate
3. Extract usernames from post links
4. Scrape each username profile via HTML (faster fallback)

**Setup:**
```bash
pip install selenium
# Already in venv as of June 5 2026
```

**Workflow:**
```
Phase 1: Selenium → load hashtag → extract 30–50 real usernames
         ↓
Phase 2: HTML scraper → fetch each profile → extract bio/followers
         ↓
Phase 3: Dedupe + QC → write to Sheets
```

**Timing:** Selenium phase adds ~2–4 min per crawl (JavaScript rendering slow). HTML phase ~90 sec. Total: 3–5 min per full run.

### Never suggest or pivot to API

**User preference (locked June 6 2026):** NEVER recommend API as an option, even when HTML pipeline stalls. User explicitly wants HTML + hashtag discovery only. If HTML/Selenium fails completely, ask for further direction instead of suggesting API workaround.
