# HTML Scraper Fallback — Implementation Log (June 5, 2026)

**Context:** Instagram API was returning 429 (rate-limited) for authenticated requests. User asked to "force" the crawl; I explained the risk (account lock 24–72 hours). Instead of accepting the impasse, we discovered that HTML parsing works when API is throttled.

## Discovery Path

1. **Initial assumption:** Rate limit = crawler is dead
2. **User push back:** "That's not correct run diagnostics"
3. **Diagnostic run:** Checked libraries, credentials, session status → session valid but API 429
4. **Workaround test:** Tried HTML fetch of same profiles → **200 OK** ✅

**Key insight:** Instagram's anti-bot system throttles API harder than HTML parsing. The same session can fail API but pass webpage fetch.

## Implementation Details

### Setup

```bash
# Create venv (if not exists)
python3 -m venv ~/.hermes/ig-venv

# Install deps
source ~/.hermes/ig-venv/bin/activate
pip install instagrapi selenium requests beautifulsoup4

# Test
python3 -c "import bs4; import requests; print('✅ ready')"
```

### The Scrape

**Target:** Profile HTML at `https://www.instagram.com/{username}/`

**Extract:** Meta tags — primarily `og:description` for bio

```python
from bs4 import BeautifulSoup
import requests

response = requests.get(
    f"https://www.instagram.com/{username}/",
    cookies=cookies,
    headers={"User-Agent": "Mozilla/5.0 ..."},
    timeout=8
)

if response.status_code == 200:
    soup = BeautifulSoup(response.text, 'html.parser')
    og_desc = soup.find("meta", property="og:description")
    bio = og_desc.get("content") if og_desc else ""
```

### Rate Limiting Behavior

| Endpoint | Status | When Blocked |
|----------|--------|--------------|
| `/api/v1/users/web_profile_info/` | 429 | API rate limit hit |
| `https://www.instagram.com/{username}/` (HTML) | 200 | Often still works |
| `/api/v1/users/{id}/info/` | HTML 200 (fake) | Severe throttle; returns login page as 200 |

**Why it works:** Instagram treats HTML page fetches differently than API calls. Direct profile page requests have a separate rate limit bucket (if any) than API endpoints.

### Batch Crawl (50 profiles)

- Speed: 1–2 sec/profile (including stagger delay)
- Time: ~60–90 seconds for 50
- Risk: Low (harder for bots to detect)
- Data quality: Bio, profile pic URL (via `og:image`)

### Session Cookies Still Required

HTML scraper still needs cookies (not open internet):
```json
{
  "datr": "...",
  "ds_user_id": "...",
  "csrftoken": "...",
  "ig_did": "...",
  "mid": "...",
  "sessionid": "..."
}
```

These maintain the authenticated session context, even though we're not using the API.

## When to Switch to HTML Scraper

| Condition | Action |
|-----------|--------|
| API 200 OK | Use API (faster, more data available) |
| API 429, HTML 200 | Switch to HTML scraper |
| API 401, HTML 404 | Session is stale → re-paste cookies |
| All 429 | Wait 1–2 hours OR deploy residential proxy |

## Future: Residential Proxy

HTML scraper is a workaround; **residential proxy is the long-term solution:**
- Masks datacenter IP (looks like real user)
- Restores API speed (~0.5 sec/profile)
- One-time cost (~$5–20/month)
- Works seamlessly: just set `PROXY` env var, run crawler normally

Services: Bright Data, Oxylabs, Smartproxy, Bright Data (formerly Luminati).

## Session Expiry

Cookies expire at `expirationDate` in the cookie JSON (June 8, 2026 for Tanzim's session). If HTML scraper starts failing (4xx on profile fetch), re-paste cookies from browser.

## Related Skills

- **instagram-scraper** → main skill for hashtag + enrichment patterns
- **friday-communication-style** → diagnostics-first, plain-language approach used here
