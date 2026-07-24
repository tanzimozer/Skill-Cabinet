---
name: selenium-scraper-detection-evasion
category: data
description: Build Selenium-based web scrapers that evade detection through behavioral mimicry, dynamic rate-limiting, and robust DOM handling
tags: [selenium, web-scraping, detection-evasion, anti-bot, rate-limiting, headless-browser]
version: 1.0.0
created: 2026-06-06
---

# Selenium Scraper Detection Evasion

Build Selenium-based web scrapers that survive anti-bot detection by mimicking human behavior, managing rate limits dynamically, and handling brittle DOM selectors gracefully.

## When to Use

- Target requires headless browser (JavaScript rendering, interactive elements)
- Session/cookie management essential (login required, state persistence)
- XPath/CSS selectors likely to break (dynamic DOM, vendor updates)
- Rate-limiting is the constraint (more pages to scrape than allowed in time window)
- IP/device fingerprinting possible (residential IP available locally, not datacenter)

## When NOT to Use

- Simple static HTML scraping (use requests + BeautifulSoup)
- API endpoints available (use direct HTTP with session cookies)
- Tor/proxy rotation primary defense (use instagrapi, scrapy-splash, or headless services)
- Time not critical (can use slower, less risky approach)

## Detection Mechanisms Your Scraper Faces

### 1. **Request Pattern Detection**
- **Velocity:** Too many requests in short time (e.g., Instagram flags at ~45+ requests/5min)
- **Timing:** Consistent fixed delays are bot signatures; humans have variable pauses
- **Distribution:** Requests clustered at predictable intervals

**Mitigation:**
```python
def jittered_delay(base=4):
    """Add random jitter to avoid timing patterns."""
    jitter = base + random.uniform(-1, 2)  # 3-6s range
    time.sleep(max(2, jitter))
```

**Rate-limit detection:**
```python
class RateLimitTracker:
    def __init__(self, window_seconds=300, max_requests=40):
        self.window = window_seconds  # 5-min rolling window
        self.max_requests = max_requests  # Instagram: ~45 before 429
        self.requests = []
    
    def should_backoff(self):
        """Detect approaching rate limit; back off before hitting it."""
        return len(self.requests) >= self.max_requests
    
    def add_request(self):
        """Track request timestamp."""
        now = time.time()
        self.requests = [r for r in self.requests if now - r < self.window]
        self.requests.append(now)
```

When `should_backoff()` returns True, wait 120s–180s (with jitter) before continuing.

### 2. **Session Behavior Detection**
- **New browser:** Fresh profile with no history
- **Unvarying user agent:** Same UA across all requests
- **Missing headers:** Missing Accept-Language, Referer, etc.
- **No cookies:** Session cookies reset each request
- **Impossible navigation:** Jumping to profiles without visiting feed first

**Mitigation:**
```python
# Chrome profile persistence (caches cookies, history, cache)
chrome_options.add_argument("--user-data-dir=/tmp/ig-hunter-profile")

# Realistic user agent
chrome_options.add_argument(
    "user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)

# Auto-include headers (Selenium does this if you use normal navigation)
# Referer, Accept-Language set automatically by Chrome
```

### 3. **Device Fingerprinting**
- **Headless detection:** `navigator.webdriver` set to true in headless mode
- **Window size:** Unusual resolutions (e.g., 1920x1080 is suspicious in headless)
- **Plugin absence:** Headless has no Flash, PDF plugin, etc.
- **Timing anomalies:** JS execution too fast (no human think-time)

**Mitigation:**
```python
# Disable webdriver flag
chrome_options.add_argument("--disable-blink-features=AutomationControlled")

# Realistic window size
chrome_options.add_argument("--window-size=1920,1080")

# Add human-like delays between actions
time.sleep(random.uniform(1, 3))  # Think time before clicking
```

### 4. **IP Reputation**
- **Datacenter IP:** Flagged immediately (AWS, GCP, Azure ranges known)
- **Proxy IP:** Same IP across many accounts = bot signature
- **Residential IP:** Trusted by default, but repeated requests can still trigger rate-limits

**Mitigation:**
- Run scraper on your personal Mac (residential ISP IP)
- If using cloud VM, source is flagged regardless of other measures
- For scale (100+ accounts), Phase 2 requires residential proxy rotation

## Core Implementation Pattern

### 1. Initialize Driver (Real Browser, Not Headless Tests)

```python
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service

def init_driver(headless=True):
    chrome_options = Options()
    
    if headless:
        chrome_options.add_argument("--headless")
    
    # Avoid headless detection
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    
    # Realistic window
    chrome_options.add_argument("--window-size=1920,1080")
    
    # Sandbox + dev-shm for stability
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    # Real user agent
    chrome_options.add_argument(
        "user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
    
    # **KEY:** Persist cookies/history across runs
    chrome_options.add_argument("--user-data-dir=/tmp/browser-profile")
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.set_page_load_timeout(20)
    
    return driver
```

### 2. Robust XPath Selectors (Multiple Fallbacks)

Instagram's DOM changes frequently. Never rely on a single XPath.

```python
def extract_handle_robust(driver):
    """Extract handle with 3+ fallback strategies."""
    strategies = [
        ("//header//a[@title]", "title"),
        ("//header//a[contains(@href, '/')]", "href"),
        ("//a[contains(@href, '/p/')]/ancestor::article//a[@title]", "title"),
    ]
    
    for xpath, attr in strategies:
        try:
            elem = driver.find_element(By.XPATH, xpath)
            if attr == "title":
                handle = elem.get_attribute("title")
            else:
                href = elem.get_attribute("href")
                handle = href.strip('/').split('/')[-1]
            
            if handle and len(handle) > 2:
                return handle
        except:
            continue
    
    return None

def extract_followers_robust(driver):
    """Extract follower count with multiple strategies."""
    strategies = [
        lambda: int(driver.find_element(
            By.XPATH, "//*[contains(text(), 'followers')]"
        ).text.split()[0].replace(',', '')),
        
        lambda: int(driver.find_element(
            By.XPATH, "//header//*[contains(., ' followers')]"
        ).text.split()[0].replace(',', '')),
    ]
    
    for strategy in strategies:
        try:
            return strategy()
        except:
            continue
    
    return None
```

**Pitfall:** If one selector breaks (vendor update), entire scraper fails silently. Always provide 3+ fallbacks, in order of specificity.

### 3. Retry Logic with Exponential Backoff

```python
def extract_profile_data(driver, handle, max_retries=3):
    """Extract profile with automatic retry on transient failures."""
    for attempt in range(max_retries):
        try:
            profile_url = f"https://www.instagram.com/{handle}/"
            driver.get(profile_url)
            
            followers = extract_followers_robust(driver)
            if followers is None:
                return None  # Skip if extraction failed
            
            bio = extract_bio_robust(driver)
            
            return {
                "handle": handle,
                "followers": followers,
                "bio": bio,
                "url": profile_url
            }
            
        except Exception as e:
            logger.debug(f"Attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                time.sleep(3 * (2 ** attempt))  # 3s, 6s, 12s
            else:
                logger.error(f"Failed to extract {handle} after {max_retries} attempts")
                return None
```

### 4. Dynamic Rate-Limit Management

```python
class RateLimitTracker:
    def __init__(self, window_seconds=300, max_requests=40):
        self.window = window_seconds
        self.max_requests = max_requests
        self.requests = []
    
    def add_request(self):
        now = time.time()
        self.requests = [r for r in self.requests if now - r < self.window]
        self.requests.append(now)
    
    def should_backoff(self):
        return len(self.requests) >= self.max_requests
    
    def count(self):
        return len(self.requests)

# In main loop
rate_limiter = RateLimitTracker(window_seconds=300, max_requests=40)

for item in items:
    if rate_limiter.should_backoff():
        backoff_time = 120 + random.uniform(0, 60)
        logger.warning(f"Rate limit detected. Backing off {backoff_time:.0f}s")
        time.sleep(backoff_time)
        rate_limiter.requests = []  # Reset counter
    
    # Do work
    driver.get(url)
    rate_limiter.add_request()
    jittered_delay()
```

## Risk Progression & Remediation Phases

This pattern reflects reality: evasion is a multi-phase effort.

### Phase 1: Request Behavior (4–6 hours)
**P(Ban) reduction: 75-95% → 40-50%**

- Jittered delays (3–6s range, not fixed)
- Rate-limit detection (track requests, back off at threshold)
- Retry logic (exponential backoff on transient failures)
- XPath robustness (3+ fallbacks per selector)

**Output:** Scraper runs without immediate detection, survives minor DOM changes.

### Phase 2: Session & Headers (12–18 hours)
**P(Ban) reduction: 40-50% → 10-20%**

- Chrome profile persistence (caches cookies, browsing history)
- Full header spoofing (Accept-Language, Referer, Sec-CH-* headers)
- Cookie jar management (proper session lifecycle)
- Per-proxy header variation (if using proxy rotation)

### Phase 3: Account & Behavioral (24+ hours)
**P(Ban) reduction: 10-20% → <5%**

- Account rotation (multiple IG accounts, not just cookies)
- Human-like behavior (random scrolls, random delays, occasional backtracks)
- VPN/residential proxy rotation (if running at scale)
- Device fingerprint rotation (different window sizes, User-Agent families)

## Configuration Pattern

Separate config from code:

```python
# config.py
REQUEST_DELAY = 4  # Base delay (jitter applied ±1 to +2s)
HEADLESS = True
WINDOW_SIZE = (1920, 1080)

# Rate limiting
RATE_LIMIT_WINDOW = 300  # seconds
RATE_LIMIT_MAX = 40  # requests before backoff
RATE_LIMIT_BACKOFF = 120  # cooldown duration

# Target
TARGET_COUNT = 100
FOLLOWER_MIN = 500
FOLLOWER_MAX = 3500

# Search strategy
SEARCH_HASHTAGS = ["fitnessgirl", "girlsworkout", ...]
```

Then tweak without touching code:
```python
# Hitting rate limits? Increase RATE_LIMIT_WINDOW or decrease RATE_LIMIT_MAX
# Getting blocked? Increase REQUEST_DELAY and RATE_LIMIT_BACKOFF
```

## Logging & Monitoring

Always log actionable events:

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scraper.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Log every decision point
logger.info(f"Searching #{hashtag} (requests this window: {rate_limiter.count()})")
logger.warning(f"Rate limit detected. Backing off for {backoff_time:.0f}s")
logger.error(f"Profile extraction failed for @{handle}: {e}")
```

This lets you:
- Monitor when rate limits were hit (post-mortem analysis)
- Detect if selectors broke (error spikes)
- Tune parameters (adjust delays based on when blocking started)

## Testing (Before Full Run)

1. **Test login:** Verify credentials work, 2FA handling if needed
2. **Test extraction:** Run on 1 known profile, verify all selectors hit
3. **Test rate-limit detection:** Manually trigger backoff by reducing `RATE_LIMIT_MAX` to 5
4. **Test error paths:** Try a deleted/private account, verify graceful skip

Never skip testing. A silent failure (no exception, but `followers = None`) will silently add wrong data to your output.

## Common Pitfalls

### 1. **XPath Selector Brittle**
- **Problem:** Vendor updates DOM, selector returns 0 results, script crashes silently
- **Fix:** Always 3+ fallbacks. Test monthly. Set up monitoring for selector failures

### 2. **Fixed Delays = Bot Signature**
- **Problem:** 4.0 second delays every time are instantly recognizable
- **Fix:** Jitter: `delay = 4 + random.uniform(-1, 2)` → 3-6 second range

### 3. **No Rate-Limit Detection**
- **Problem:** Hit 429, get checkpointed, keep retrying, make it worse
- **Fix:** Track request timestamps in rolling window. Back off BEFORE hitting limit

### 4. **Silent Failures**
- **Problem:** Selector fails, returns None, script silently adds incomplete record
- **Fix:** Check return values. Log every skip. Review logs post-run

### 5. **Headless Detected**
- **Problem:** `--headless` mode flagged by `navigator.webdriver` check
- **Fix:** Add `--disable-blink-features=AutomationControlled`. Consider not headless if running locally

### 6. **Wrong Window Size**
- **Problem:** 1920x1080 in headless mode is suspicious (no one runs that small)
- **Fix:** Use realistic size (1440x900, 1280x720), or don't run headless

## Target Behavior

A successful Selenium scraper:

✅ Respects rate limits (backs off before hitting 429)  
✅ Survives DOM changes (3+ XPath fallbacks)  
✅ Persists session state (Chrome profile dir)  
✅ Logs all decisions (easy to debug post-run)  
✅ Runs on residential IP (not datacenter)  
✅ Variable request timing (not fixed delays)  
✅ Handles edge cases (deleted accounts, private profiles, null fields)  

## References

- `references/ig-hunter-session-2026-06-06.md` — IG-Hunter scraper audit + Phase 1 implementation
- `templates/selenium-scraper-scaffold.py` — Boilerplate ready to adapt (RateLimitTracker, retry logic, multiple XPath fallbacks)

## Quick Start

1. Copy `templates/selenium-scraper-scaffold.py` and adapt `scrape_item()` method
2. Create `config.py` with your parameters (see template in `references/ig-hunter-session-2026-06-06.md`)
3. Create `.env` with credentials if needed
4. `pip install selenium webdriver-manager`
5. Run and monitor logs
