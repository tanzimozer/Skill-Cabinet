---
name: instagram_influencer_research
category: research
description: End-to-end workflow for finding, filtering, classifying, and delivering Instagram influencer lists by city. Used for TIMBR outreach campaigns targeting personal fitness/lifestyle accounts (500–3500 followers).
---

# Instagram Influencer Research

## What this is for
Building targeted lists of personal Instagram accounts in specific cities — female, 500–3500 followers, personal lifestyle/fitness/wellness, NOT company or brand accounts. Output: Google Sheet with rich classification columns.

## Full workflow

### 1. Validate session before scraping
Prefer **web-app** auth-required endpoints, not the mobile `/users/{uid}/info/` one:
```python
H = {"User-Agent": "Mozilla/5.0 ...", "X-IG-App-ID": "936619743392459", "X-CSRFToken": CSRF}
r = requests.post('https://www.instagram.com/api/v1/feed/timeline/', cookies=COOKIES, headers=H)
assert r.status_code == 200 and len(r.content) > 5000, "Session dead — need fresh cookies"
```
Never skip this. A dead session returns 200 with HTML, wastes the entire run.

**Pitfall — false negative from mobile endpoints.** The mobile `i.instagram.com/api/v1/users/{uid}/info/` and `accounts/current_user/` endpoints can return `{"user":{}}` or `status:fail` for a cookie that is actually LIVE — it's a device-signature/User-Agent quirk, not a dead session. Confirm with the web-app endpoints above (`feed/timeline/` ~190KB, `feed/reels_tray/` ~360KB of authenticated data = live). Don't declare a cookie dead on the mobile endpoint alone.

### 2. Get fresh cookies when needed
- Use Cookie-Editor by cgagnier (blue icon, Chrome store)
- URL: https://chrome.google.com/webstore/detail/cookie-editor/hlkenndednhfkekhgcdicdfddnkalmdm
- Open instagram.com → Cookie-Editor → Export → paste JSON
- Write immediately to vault: `update_vault('instagram', {session_id, csrf_token, datr, mid, ig_did, ds_user_id, last_updated})`
- hotcleaner.com exports are encrypted — reject and ask again

### 3. Scrape in background
- Run as background process with `notify_on_complete=True`
- Target: 2–3x more raw candidates than needed (filters cut 40–60%)
- Pacing: 1.2s/page, 1.5s/enrich, 2s/tag
- Save incrementally every hit — don't lose progress
- Run multiple cities in parallel (separate processes)

### 4. Filter criteria
```python
fc = u.get('follower_count', 0)
if not (500 <= fc <= 3500): continue
if u.get('is_private'): continue
if not is_female(u): continue
if not is_personal(u): continue  # see references/instagram_scraping.md
```

### 5. Classify with detail columns
For each passing profile, derive:
- **niche**: yoga / pilates / running / fitness / wellness / nutrition / mindfulness / beauty / motherhood / coaching / fashion / travel / food / content / other
- **account_type**: personal_influencer / personal_coach / personal_lifestyle
- **quality_score** (1–10): 8+ = city confirmed in bio + clear niche; 6–7 = niche OK but location inferred; <6 = vague
- **engagement_tier**: micro (500–1k) / mid_micro (1k–2k) / upper_micro (2k–3.5k)
- **location_confirmed**: city name appears explicitly in bio
- **red_flags**: list e.g. ["possibly_male", "brand_account", "location_unclear"]

### 6. Push to Google Sheets
- One tab per city, sorted by quality_score descending
- Master "Targets" tab with all cities combined
- Headers: City | Username | Instagram Link | Full Name | Followers | Engagement Tier | Niche | Account Type | Quality Score | Location Confirmed | Bio | Red Flags
- Freeze row 1, bold headers

## Known yield rates by city
| City | Tags available | Personal % after filter | Notes |
|---|---|---|---|
| London | High | ~40% | Best city for volume. Cultural tags add diversity. |
| Sydney | Medium | ~40% | Gets rate-limited faster |
| Melbourne | Low | ~30% | Hashtags run thin quickly |
| Tallinn | Very low | ~25% | Sparse fitness tags, mostly service businesses |

## Pitfall: company account leakage
Auto-filters miss borderline cases. PT/coaches with "coaching" in their name get flagged as companies.
**Do a manual KEEP pass on borderline accounts** — don't rely on the company filter alone.
When Tanzim says "these are companies not people", he means: gyms, studios, brands, products, run clubs, pageants.
A solo PT posting under their own name = personal account. A "Women's Gym" = not.

## Pitfall: Tanzim's key requirement
He wants **personal accounts** — real people posting as themselves, not brands.
Even if they're a fitness coach or nutritionist, if it's their personal name/handle = acceptable.
Remove: gym brands, studios, run clubs, beauty clinics, supplement brands, pageant orgs, photographers, male accounts.

## Google Sheet template
Sheet ID used for TIMBR outreach: `1ThRqyMct-3u2Fm7dgL3ap3QRxRTDBD4vE0NcxAeWMbU`

## See also
- `references/instagram_scraping.md` — API endpoints, rate limit behaviour, dead tags, full filter code
- `references/account_pool_management.md` — Turro read/write account separation, the "IG Creds" owned-handle ledger, cookie hygiene when a human hands you cookies
- vault_access skill — credential management for Instagram cookies
