---
name: ig1-protocol
category: protocols
description: IG1 Protocol — Instagram influencer discovery and outreach crawler. Hashtag sweep across target cities, HTML follower scraping, female personal accounts 500–3,500 followers.
trigger: When Tanzim invokes "IG1" or "IG1 protocol" — run the full crawler pipeline.
---

# IG1 Protocol

## What it is
Instagram outreach intelligence sweep. Identifies personal female lifestyle/fitness accounts across target cities using hashtag scraping + HTML profile scraping for follower counts. Bypasses the blocked enrich API endpoint.

## Target profile standard
- **Gold standard**: @hannahellisss — personal yoga/fitness lifestyle, no service selling
- **Followers**: 500–3,500
- **Gender**: Female (bio/name/username signal detection)
- **Account type**: Personal only — no studios, gyms, coaches, brands
- **Visibility**: Public accounts only

## Cities on tab
Melbourne, Sydney, London, Tallinn, Brisbane, Anchorage, Edmonton, Dallas, Chicago, Salt Lake City, Portland, Warsaw, Kyiv, Moscow

## Method (current best architecture)
1. **Tag fetch**: POST to `/api/v1/tags/{tag}/sections/` — returns usernames from recent posts. Requires session cookies.
2. **Enrichment**: `GET /api/v1/users/web_profile_info/?username={username}` with mobile user agent — returns full JSON (follower count, bio, is_private, is_business, following count). More reliable than HTML scrape. Pace at 8–14s per call.
3. **Filter**: 500–3,500 followers, public, not a business. Female filter is SOFT — tag `likely_female` but don't hard-drop.
4. **Score**: `account_score` 0–100 based on following/follower ratio, bio signals, female signals. Sort by score descending.
5. **Save**: Incremental JSON to `~/.hermes/ig1/results/{city}.json`. Feedback loop updates scores after follow-back check.

## Two expansion strategies

**Strategy A — Tag → Enrich → Score**
Hashtag sections API → web_profile_info enrichment → filter → score by follow-back probability → feedback loop refines bio signal weights over time. Simple, runs anywhere, no warm account needed. Weakness: hashtag pools are shallow and noisy. Fitness tags produce zero — use lifestyle tags only.

**Strategy B — Seed Network Expansion (preferred)**
Use Instagram's suggested users / chaining endpoint on our 45 clean seeds: `GET /api/v1/discover/chaining/?target_id={uid}`. One good seed → 10–20 algorithmically similar accounts. 45 seeds × 15 suggestions = 675 high-signal candidates. Instagram's own algorithm does the targeting. **Requires desktop UA** — mobile UA returns 400 "useragent mismatch". Requires established follows (a few days old). Hybrid: B for quality, A for volume.

**Why B compounds:** Seeds → similar accounts → follow those → their network suggests more similar accounts. Each generation tightens the graph toward the target profile type.

## Feedback loop
`~/.hermes/ig1/ig1_feedback.py` — checks follow-back status via `/api/v1/friendships/show/{uid}/`, extracts bio patterns that correlate with follow-backs, updates `~/.hermes/ig1/feedback.json`. Crawl script loads this on startup and uses it to weight `account_score`.

## Output location (permanent)
- `~/.hermes/ig1/results/{city}.json` — verified targets per city
- `~/.hermes/ig1/feedback.json` — follow-back patterns and rates
- `~/.hermes/ig1/logs/{city}.log` — per-city crawl logs

## Cookies required
Fresh Instagram session cookies from vault (`~/.hermes/vault.json`). Test session with `/api/v1/users/{uid}/info/` before running. If rate-limited, load fresh cookies from Tanzim.

**CRITICAL — do not pass vault dict directly as cookies.** The vault instagram entry contains nested dicts (`cookies`, `note`, etc.) that break `requests` cookie handling with `TypeError: expected string or bytes-like object`. Always unpack explicitly:

```python
vault = json.load(open(Path.home() / '.hermes' / 'vault.json'))['instagram']
COOKIES = {
    'sessionid': vault['sessionid'],
    'csrftoken': vault['csrftoken'],
    'datr': vault['datr'],
    'mid': vault['mid'],
    'ig_did': vault['ig_did'],
    'ds_user_id': vault['ds_user_id'],
}
```

## Pacing
- Tag fetch: 1.5–3s between pages
- web_profile_info enrich: 8–14s per profile
- Between tags: 4–8s
- Follow actions (separate): 45–75s between follows

## Output files
- `/tmp/ig_veronica_v1.json` — verified targets with city, username, followers, bio, uid
- `/tmp/ig_final_v5.json` — previous clean seed list (45 accounts, already followed)
- `/tmp/ig_follows_log.json` — follow action log

## HTML scrape pattern (working as of June 2026)

The `/api/v1/users/{uid}/info/` enrich endpoint rate-limits aggressively after ~50–100 calls per session. Use HTML scraping instead:

```python
r = requests.get(f'https://www.instagram.com/{username}/',
    headers={'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 13_6) AppleWebKit/537.36'},
    cookies=COOKIES, timeout=12)
# Pattern 1 — JSON blob in page source
m = re.search(r'"edge_followed_by":\{"count":(\d+)\}', r.text)
# Pattern 2 — fallback text match
m2 = re.search(r'([\d,]+)\s*[Ff]ollowers', r.text)
```

Pattern 2 is the reliable fallback — confirmed working on public profiles June 2026.

## Followers list API — blocked for new follows

## Known pitfalls & lessons (June 2026)

### 1. Female filter — do NOT hard-filter during crawl
Instagram HTML does not reliably include bio text on authenticated requests. `<meta name="description">` is stripped. Running a hard female signal gate during the crawl produces zero results even when qualifying accounts exist — the filter starves itself.
**Fix**: Tag every account with `likely_female: true/false` but collect all 500–3,500 public accounts regardless. Apply gender filter as a soft QC pass after the crawl.

### 2. Follower count — strip commas
HTML renders follower counts as `2,188 Followers`. Always `.replace(',','')` before `int()`.

### 3. Enrich API rate-limit is silent
`/api/v1/users/{uid}/info/` returns a full HTML login page with status 200 when rate-limited — `r.json()` throws silently and the whole enrichment loop produces zero results. Use HTML scraping for bulk work; only use enrich for single-account tests.

### 4. Follower list API blocked for new follows
`/api/v1/friendships/{uid}/followers/` returns empty JSON — no error — for accounts followed within the last few days. Do not run seed crawl immediately after a follow batch. It will yield zero results across all seeds.

### 5. Fitness hashtags yield near-zero personal accounts — use lifestyle tags instead
City fitness hashtags (`#melbournefit`, `#londonfitness`, `#chicagoyoga`) are dominated by gyms, studios, coaches, brands. After full sweeps of 10 fitness tags per city, zero accounts cleared the filter across all 14 cities. **Always lead with lifestyle/personal tags:**
- `{city}life`, `{city}girl`, `{city}women`, `{city}lifestyle`, `{city}blogger`, `{city}foodie`, `{city}mum`, `{city}living`, `{city}local`
- Bare city tag (`#london`, `#melbourne`, `#dallas`) also surfaces personal accounts
- Fitness tags can supplement but must not be the primary source

### 6. Run parallel city agents, never sequential
Running 14 cities sequentially wastes hours. Launch one agent per city:
```bash
python3 -u /tmp/veronica_city.py "{city}" > "/tmp/ig_log_{city}.log" 2>&1 &
```
Each agent saves independently to `/tmp/ig_city_{city}.json`. 14 parallel agents complete in the same time as 1 sequential run.

## Reference files
- `references/scraping-lessons-june2026.md` — full debugging session: what worked, what failed, root causes, cookie notes

## After crawl
Push results to Google Sheet: `1ThRqyMct-3u2Fm7dgL3ap3QRxRTDBD4vE0NcxAeWMbU`
Run follow script with 45–75s pacing.
