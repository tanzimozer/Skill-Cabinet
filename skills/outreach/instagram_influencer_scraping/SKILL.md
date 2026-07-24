---
name: instagram_influencer_scraping
category: outreach
description: Scrape, filter, classify and publish Instagram influencer lists for Tanzim. Targets personal female micro-influencers (500–3500 followers) by city. Output goes to Google Sheets with rich classification columns.
---

# Instagram Influencer Scraping

## Tanzim's criteria (non-negotiable)
- **Followers:** 500–3500 (micro-influencer tier)
- **Gender:** Female signals in bio/name/username
- **Account type:** Personal only — real person posting as themselves
- **Public accounts only**
- **Cities so far:** Melbourne, Tallinn, London, Sydney

### What COUNTS as personal
- Personal trainer / coach posting under their own name
- Yoga/pilates teacher (personal account, not a studio page)
- Lifestyle, wellness, fitness, nutrition bloggers
- Mums/mamas, travel women, content creators

### What does NOT count (hard remove)
Gyms, studios, clinics, run clubs, brands, product companies, photographers (as a service), nonprofits, pageant orgs, supplement brands, nail/lash/brow businesses, real estate, cafes. Even if the bio says "women's gym" — remove it.

**Lesson:** Auto keyword filters over-remove personal coaches and over-include business accounts simultaneously. Always do a subagent Opus classification pass — never rely on keyword filtering alone for final output.

---

## Pipeline

### Step 1 — Credential check
Always read from vault first:
```python
with open('/home/hermes/.hermes/vault.json') as f:
    vault = json.load(f)
ig = vault['instagram']
COOKIES = {
    'datr': ig['datr'], 'ds_user_id': ig['ds_user_id'],
    'csrftoken': ig['csrf_token'], 'ig_did': ig['ig_did'],
    'mid': ig['mid'], 'sessionid': ig['session_id'],
}
```
If sessionid is None or enrichment returns HTML (not JSON), cookies are expired — ask Tanzim to re-export via Cookie-Editor (cgagnier extension, blue icon). Update vault immediately after. Never ask Tanzim for credentials already in the vault.

### Step 2 — Tag fetch
```
POST https://www.instagram.com/api/v1/tags/{tag}/sections/
data: tab=recent&page={n}&count=33
```
- Max 12–15 pages per tag
- Sleep 1.2s between pages
- Stop if `more_available` is false or status != 200

### Step 3 — Enrich
```
GET https://www.instagram.com/api/v1/users/{uid}/info/
```
- Returns JSON with `follower_count`, `biography`, `is_private`, `is_business`, `category`, `external_url`
- If response is HTML (starts with `<!DOCTYPE`): session flagged, need new cookies
- If 429: wait 60s, retry up to 3x
- If `feedback_required` / `is_spam`: session rate-limited — stop immediately, wait 30–60 min or use fresh cookies

### Step 4 — Filter
```python
def is_female(u): ...  # check FEMALE_SIGNALS in bio+name+username
def is_personal(u): ...  # check COMPANY_SIGNALS NOT in bio+name+username
# then: not private, 500 <= followers <= 3500, is_female, is_personal
```

### Step 5 — Classification (use Opus subagent)
Fields per profile:
- **niche**: fitness | yoga | pilates | running | wellness | nutrition | lifestyle | beauty | fashion | motherhood | travel | food | mindfulness | coaching | dance | martial_arts | other
- **account_type**: personal_influencer | personal_coach | personal_creator | personal_lifestyle
- **quality_score**: 1–10 (8–10 = clear person + strong niche + city confirmed in bio; 5–7 = decent; 1–4 = weak — remove ≤3)
- **engagement_tier**: micro (500–1000) | mid_micro (1001–2000) | upper_micro (2001–3500)
- **location_confirmed**: true if city name in bio, false if inferred from tag only
- **red_flags**: ["possibly_male", "brand_account", "location_unclear", "off_niche"]

### Step 6 — Google Sheets output
Sheet ID: `1ThRqyMct-3u2Fm7dgL3ap3QRxRTDBD4vE0NcxAeWMbU`
- One tab per city + master Targets tab
- Columns: City | Username | Instagram Link | Full Name | Followers | Engagement Tier | Niche | Account Type | Quality Score | Location Confirmed | Bio | Red Flags
- Sort each tab by Quality Score descending
- Bold + dark header, freeze row 1

---

## Execution pattern
- Run city scrapes **in parallel background jobs** — never sequentially
- Save incrementally to `/tmp/ig_{city}.json` — protects against crashes
- Skip already-collected usernames (load from existing files at job start)
- After scrape: classify with Opus subagent, then push to sheet
- Use 15 pages per tag for deeper coverage
- 60+ tags per city mixing fitness, lifestyle, wellness, beauty, mum, fashion, identity tags

## THE BENCHMARK — Tanzim's gold standard
**@hannahellisss** — personal lifestyle/fitness woman sharing her OWN life. Posts: yoga poses, running events, travel, beach moments, retreats she attends, daily life. She IS the content.

**KEEP:** Women documenting their own journey — yogis, runners, mums, lifestyle women, foodies, travellers who happen to be fit.

**REMOVE (the critical distinction):** Anyone whose PRIMARY purpose is selling a service/product — even solo operators. The question: *Is she sharing her own life, or selling something to others?*

Specific remove signals:
- Booking CTAs: "DM to book", "book now", "slots available", "link in bio to book"
- Client results: before/afters, transformation photos of OTHER people
- Programme selling: "join my", "apply for coaching", "online programme", "apply now"
- Service card bios: credentials + services + booking info (reads like a business card)
- Lash/brow/nail/PMU/beauty service: even solo operators with pricelist content
- Yoga/PT with studio page, class schedule, retreat business

This filter removes roughly 60–70% of profiles that pass keyword filters — that's expected, not a bug.

## Follow/like actions — rate limits
Instagram caps write actions heavily per session:
- **Follow cap:** ~60 follows/hour — hits after ~11 accounts at normal pace
- **Like cap:** ~150 likes/hour
- **Safe pacing:** 25–35s between likes, **8–10 min between accounts**
- On 429 or `feedback_required`: pause 20 min, continue
- Always check `friendship_status` before following to avoid double-follows
- Run as **overnight scheduled cron job** — never a fast synchronous loop
- API endpoints: `POST /api/v1/friendships/create/{uid}/` and `POST /api/v1/media/{media_id}/like/`
- Get feed: `GET /api/v1/feed/user/{uid}/?count=12`
- "✅ Followed" 200 response can be a false positive — verify with friendship_status check

## Enrich endpoint — 429 vs checkpointed (critical distinction)

Two failure modes look similar but need different fixes:

| Symptom | Meaning | Fix |
|---|---|---|
| `200 + HTML` (starts `<!DOCTYPE`) | Session/device checkpointed | Fresh cookies from different browser |
| `429` | Rate limited — too many requests this session | Wait 30–60 min, retry — **do not ask for new cookies** |
| `feedback_required` in JSON | Hard rate limit / spam flag | Stop immediately, wait 60 min or new cookies |

**Tag sections vs enrich**: tag sections API (`/api/v1/tags/{tag}/sections/`) survives longer under rate pressure than enrich. Can still collect UIDs when enrich is dead. **However, tag sections returns bio but NOT follower count** — enrich is mandatory, there is no workaround.

**web_profile_info** (`/api/v1/users/web_profile_info/?username=`) is the web alternative to mobile enrich — returns bio + follower count via `edge_followed_by.count`. Rate-limits at the same threshold as mobile enrich. Not a bypass; just a fallback when mobile enrich 401s.

**datr cookie re-use**: if same `datr` appears in new cookies as a previously-flagged session, Instagram still recognises the device. HTML-on-200 persists. Ask for cookies from a different browser (Firefox, Edge) or incognito from a different network.

**Zero hits despite valid tag candidates**: If tag fetch returns candidates (non-zero `len(raw)`) but final list is 0, the enrich step is silently failing. Root cause in confirmed session: enrich endpoint returns `200 + HTML` (Instagram login/challenge page) — `r.json()` throws, except block catches it, returns `None`, every user is dropped. The tag fetch → filter pipeline appears to run but produces nothing. **Fix: add explicit HTML detection before `r.json()`:**
```python
if r.status_code == 200 and r.text.strip().startswith('<!DOCTYPE'):
    print("Session checkpointed — cookies expired, need fresh from different browser")
    return None
```

## Known pitfalls
- Melbourne/Sydney hashtags dominated by businesses — expect ~50% removal rate
- London yields cleaner personal accounts
- Tallinn tags thin — skew toward Russian-language service accounts
- `easyteaching.melb` appears in Sydney tags — dedupe across cities
- Personal coaches with "coaching" in bio get incorrectly flagged as companies by keyword filter — Opus pass fixes this
- **Quality audit removes ~20–25%** of profiles that passed filters — always run audit before final sheet push. Audit catches: males with male full_name, wrong-location bios, businesses that slipped keyword filter, alphanumeric bot usernames
- **Hashtag diminishing returns**: after 3 waves, yield drops to <35 per 70 tags. Per-city hashtag ceiling: London ~200 raw, Sydney ~130, Melbourne ~100, Tallinn ~15. Switch to location geotag or follower-graph scraping when this hits.
- **datr cookie fingerprint**: if the same `datr` value appears in new cookies as in a previously-flagged session, Instagram still recognises the device. Symptom: enrich returns HTML on a 200. Ask for cookies from a different browser (Firefox/Edge) or wait for device block to expire (~2–3 hrs).
- **Don't mistake rate-limit for expired cookies**: `feedback_required/is_spam` = rate limit (wait); HTML on 200 = device/session blocked (need fresh cookies from different browser).
- Subagent quality audit catches male accounts reliably by checking full_name — keyword filter misses these entirely.

## Rate limit behaviour
- Enrich endpoint trips before tag fetch endpoint
- After ~300–400 enrich calls in a session: expect 429s
- Safe pacing: 1.5s between enrichments, 2s between tags
- `feedback_required` response = stop immediately, fresh cookies needed
- Tag fetch survives longer — can still collect UIDs even when enrich is dead

## Hashtag ceiling by city (from 4+ run sessions)
| City | Raw ceiling | Post-audit clean | Notes |
|---|---|---|---|
| London | ~200 | ~130–160 | Cultural/identity tags productive (hijabi, blackgirl, latina) |
| Sydney | ~130 | ~100 | Gets rate-limited faster |
| Melbourne | ~100 | ~65–80 | Thin hashtag pool; many tags empty |
| Tallinn | ~15 | ~8–10 | Mostly service accounts; not worth large investment |

## Reference files
- `references/signal_lists.md` — full FEMALE_SIGNALS and COMPANY_SIGNALS arrays
- `references/city_tags.md` — tag lists per city used across all runs
