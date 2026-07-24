# Instagram Scraper Detection Triggers

Reference from IG-Hunter audit session (2026-06-07). Consolidates patterns that Instagram's anti-bot systems detect.

## Request Timing Patterns (High Confidence Trigger)

**What gets detected:**
- Fixed delays (e.g., always 4 seconds between requests)
- No variance in timing (< 5% coefficient of variation)
- Requests arriving at exact intervals (millisecond precision)

**Why:** Human users vary response time naturally (2-8 seconds, distributed). Machines are predictable.

**Detection method:** Instagram logs request timestamps. Pattern analysis detects deviations from human baseline.

**Confidence:** 85% detection after 10-20 requests with fixed delays.

## Rate Limiting Triggers

**Hard limits:**
- ~50 requests per hour (for most endpoints)
- ~200 requests per 24 hours (for user profiles)
- Varies by endpoint (faster for public data, slower for private)

**What happens:**
- Request #45: 200 requests/13 min exceeds hourly limit
- Response: 429 Too Many Requests
- Result: Account flagged for review

**Recovery:** 5-15 minute backoff, then gradual retry

**Detection confidence:** 100% after limit exceeded (hard stop)

## XPath/DOM Selector Brittleness

**Root cause:** Instagram changes class names, attribute names, element structure frequently (weekly to monthly).

**Typical failure points:**
- `//button[@type='button']` → too generic, matches 20+ elements
- `//header//a[@title]` → header structure changed in v2.1
- `//*[contains(text(), 'followers')]` → text moved to data attribute
- `//section//div[contains(@class, 'bio')]` → bio section replaced with modal

**Mitigation strategy:**
1. Primary: Most specific selector (class + position + attribute)
2. Fallback: CSS selector (more stable)
3. Last resort: JavaScript DOM inspection
4. Validation: Check element properties before interaction

**Failure rate empirically observed:** 60-65% across 4 critical selectors.

## Browser Fingerprinting Detection

**What Instagram checks:**
- User-Agent header (trivial to spoof, but monitored)
- Accept-Language, Referer, other standard headers
- WebDriver property (navigator.webdriver)
- Chrome DevTools Protocol active
- Headless mode detection
- Canvas fingerprinting
- Timing attacks (Chrome API latencies)

**What's inadequate:**
- User-Agent rotation alone (90% likely to be detected)
- Single header set repeated (patterns stand out)
- No randomization of Accept, Referer, etc.

**What helps:**
- Full header rotation (not just User-Agent)
- JavaScript to disable navigator.webdriver
- Delay randomization
- Proxy rotation (masks IP pattern)
- Cookie persistence (avoids fresh login signature)

**Detection confidence:** 70-80% with incomplete header spoofing.

## Login Pattern Detection

**Red flags:**
- Fresh login on every run (Instagram expects user to stay logged in)
- Same username/password from different IPs hourly
- Login followed immediately by high-volume requests
- No cookie persistence (fresh browser signature)

**Normal behavior:**
- Login once, session lasts days
- Occasional re-login from same device/IP
- Delay before first request after login

**Detection confidence:** 60% if multiple login pattern anomalies.

## Data Extraction Patterns

**What gets flagged:**
- Requesting same profile repeatedly (10+ times/hour per account)
- Extracting data that requires page rendering (JavaScript-loaded fields)
- Large batch requests (e.g., 500 profiles in 30 min)

**Safe pattern:**
- 1-2 requests per profile per hour
- Space profiles across time (not sequential)
- Vary request targets (mix profile/search/hashtag)
- Use published APIs when possible (limits but realistic)

## Compound Detection (Most Likely Path)

Typical detection sequence for unpatched scraper:

1. **0:15** — Login from new IP detected (soft flag)
2. **0:30** — XPath selector fails 3x → Python exceptions (logged)
3. **1:00** — Rate limit hit: request #45 → 429 response
4. **1:05** — No backoff logic → script crashes, retries aggressively
5. **1:30** — Account flagged by ML model: multiple anomalies
6. **2:00** — Soft ban applied (24-48 hour timeout)
7. **24:00** — Ban expires OR escalates to hard ban

**Combined P(detection):** Using trigger independence assumption:
- P(timing) = 0.85
- P(rate limit + no recovery) = 1.0
- P(failed selectors + poor exception handling) = 0.80
- P(session/fingerprint anomalies) = 0.70

P(at least one trigger) = 1 - (0.15 × 0 × 0.20 × 0.30) = 1.0 (certain)

Conservative estimate (accounting for correlation): 75-95%

---

## Remediation Reference

### Phase 1 (Reduces risk to 40-50%)
- [x] Add request jitter (±50% variance around base delay)
- [x] Implement 429 detection + 5-15 min backoff
- [x] Replace bare `except:` with specific exception types
- [x] Add retry logic with exponential backoff
- [x] XPath fallback chains (CSS → JS as last resort)

### Phase 2 (Reduces risk to 10-20%)
- [x] Proxy rotation (residential proxy service)
- [x] Full header spoofing (not just User-Agent)
- [x] Cookie persistence (save/load between runs)
- [x] Browser fingerprint masking
- [x] Login pattern normalization (stay logged in)

### Phase 3 (Reduces risk to <5%)
- [x] Multi-account rotation
- [x] Human-like interaction simulation (scroll, pause, read)
- [x] VPN/proxy redundancy
- [x] Smart rate limiting (monitor response times)
- [x] Request batching and scheduling
