# Hashtag Discovery via Selenium — Session Log (June 6, 2026)

## Problem Statement

HTML scraping works for **known public profiles** (celebrity accounts, verified influencers). But discovering **new profiles at scale** requires either:
1. Hardcoded username lists (unreliable — most are private/shadowbanned)
2. API hashtag endpoints (user excludes this)
3. Hashtag page scraping (requires JS rendering)

This session tested approaches 1 & 3 and found the path forward.

## Crawl Attempts

### Crawl #1–#2: Original 50 Celebrity Profiles ✅
- **Method:** Hardcoded list (emrata, gigi_hadid, kendalljenner, etc.)
- **Result:** 50/50 success (known public accounts)
- **Data:** Followers, following, bio via HTML
- **Dedup:** Both crawls = same 50 profiles (duplicates caught correctly)

### Crawl #3: Generic Wellness/Business Hashtags ❌
- **Method:** Hardcoded generic handles (womenceos, businessmindset, fitnessgal_, etc.)
- **Result:** 0/50 profiles scraped
- **Failure mode:** All returned "skipped or private"
- **Lesson:** Generic account names don't work. Instagram blocks or they're private/deleted.

### Crawl #4: Fitness/Lifestyle Discovery Names ❌
- **Method:** Similar generic handles (fitgirl_fit, fitfamily_, fitathlete_, etc.)
- **Result:** 0/48 profiles
- **Failure mode:** Same as Crawl #3
- **Lesson:** Reaffirmed — hardcoded generic lists are unreliable.

### Crawl #5: v4 "Verified Fresh Profiles" ❌
- **Method:** Curated list (fitnessmotivation_, gymgirlsonly, fashionmodel_, etc.)
- **Result:** 0/48 profiles
- **Auth issue:** Google OAuth token expired (401 on Sheets write) — refreshed
- **Lesson:** Even "verified" handles fail; auth hygiene matters

### Crawl #6: Hashtag Discovery via BeautifulSoup ❌
- **Method:** Scrape hashtag pages (fitnessgirl, fitnesswomen, fitnessmotivation, etc. — 16 total)
- **Result:** 0 usernames discovered across all hashtags
- **Root cause:** BeautifulSoup fetches static HTML skeleton; Instagram renders feed client-side (JavaScript). No profile links appear in raw HTML.
- **Solution identified:** Selenium + JavaScript rendering required

## Path Forward: Selenium + Hashtag Discovery

### Why Selenium Works Here

1. **Loads page fully** — JavaScript executes, feed renders
2. **Extracts profile links** — Post elements now contain username/profile links
3. **Parses real data** — `<a href="/username/">` links become accessible
4. **Uses existing session** — Cookies still authenticate the browser session

### Implementation Sketch

```python
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

# Load hashtag page with Selenium
driver = webdriver.Chrome()  # Or Firefox
driver.get(f"https://www.instagram.com/explore/tags/{hashtag}/")

# Wait for feed to render (JS completes)
WebDriverWait(driver, 10).until(
    EC.presence_of_all_elements_located((By.TAG_NAME, "article"))
)

# Extract profile links from post elements
links = driver.find_elements(By.CSS_SELECTOR, "a[href^='/']")
usernames = set()
for link in links:
    href = link.get_attribute("href")
    if href.startswith("/") and href.count("/") == 2:
        username = href.strip("/")
        if username and not any(x in username for x in ["explore", "p", "direct"]):
            usernames.add(username)

driver.quit()
return list(usernames)
```

### Workflow

1. **Phase 1 (Selenium):** Load 16 hashtag pages, extract ~50–100 unique usernames (3–5 min)
2. **Phase 2 (HTML scraper):** Batch scrape top 50 profiles for bios/followers (90 sec)
3. **Phase 3 (Dedupe + QC):** Remove existing, quality check, write to Sheets (30 sec)

**Total time:** ~5–6 minutes per run. Acceptable for discovery pipeline.

### Known Selenium Pitfalls

- **Browser setup:** Requires Chromium/Firefox binary. Hermes VM likely has one; if not: `apt-get install chromium` or use Geckodriver for Firefox.
- **Timing:** Don't just sleep — use WebDriverWait with explicit conditions (presence of elements, not just page load).
- **Memory:** Close driver after use (`driver.quit()`) or Selenium processes accumulate.
- **Cookies:** Pass the Instagram session cookies to Selenium so it stays authenticated.

### Comparison: BeautifulSoup vs Selenium vs API

| Approach | Speed | Reliability | Risk | Data Quality |
|----------|-------|-------------|------|--------------|
| BeautifulSoup (static) | Fast (1–2 sec/page) | Low (JS-rendered pages fail) | Low | Bio, pic URL |
| Selenium (JS rendering) | Slow (4–8 sec/page) | High (renders full page) | Low | Bio, pic URL, more |
| API (hashtag sections) | Fast (200ms/call) | High (designed for discovery) | Medium (rate-limited, throttles enrich) | Most complete |

**For this user:** Selenium = acceptable cost for HTML-only constraint. Next session would consider residential proxy if speed becomes critical.

## Session Decision Log

- **Jun 5:** Hardcoded lists → 0 results. Pivot to hashtag discovery.
- **Jun 6 (A):** BeautifulSoup hashtag scrape → 0 results. Root cause: JS rendering required.
- **Jun 6 (B):** User says "hold," checks Instagram notification. Waiting on direction.
- **Jun 6 (C):** Plan to implement Selenium + hashtag discovery v6.

## User Preference Note

User explicitly said **"Never just the api route, try again with html"** and later **"Never suggest option 2 again"** when I offered API as a fallback. This is locked in: HTML + Selenium for discovery only. If that fails completely, ask for direction rather than pivoting to API.
