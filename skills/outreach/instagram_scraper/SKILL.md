---
name: instagram_scraper
category: outreach
description: Scrape Instagram hashtag feeds to build targeted influencer lists. Covers tag fetching, per-user enrichment, female signal detection, and cookie management.
---

# Instagram Influencer Scraper

## Architecture
Two-step pipeline:
1. **Tag fetch** — POST `/api/v1/tags/{tag}/sections/` → returns candidate UIDs + usernames
2. **Enrich** — GET `/api/v1/users/{uid}/info/` → follower count, bio, is_private

Tag fetch survives session limits longer than enrich. Test enrich separately before a full run.

## Standard headers
```python
COOKIES = {
    'datr': '...', 'ds_user_id': '...', 'csrftoken': '...',
    'ig_did': '...', 'mid': '...', 'sessionid': '...',
}
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
    'X-CSRFToken': '...',
    'X-IG-App-ID': '936619743392459',
    'Referer': 'https://www.instagram.com/',
}
```

## Enrich health check — always run this first
```python
r = requests.get(f'https://www.instagram.com/api/v1/users/{test_uid}/info/',
    cookies=COOKIES, headers=HEADERS, timeout=12)
if r.status_code == 200 and r.text.strip().startswith('{'):
    print("✅ Enrich working")
elif r.text.strip().startswith('<!DOCTYPE'):
    print("❌ HTML response — session dead, need fresh cookies")
elif 'feedback_required' in r.text:
    print("❌ Session flagged as spam — need fresh cookies")
elif r.status_code == 429:
    print("⏳ Rate limited — wait 45s")
```

## Female signal detection
```python
FEMALE_SIGNALS = [
    'she','her','woman','women','girl','lady','female','mum','mom','mama',
    'queen','sis','sister','wife','daughter','nainen','naine','she/her','♀',
    '👩','💁','🧘','💃','🧖','👸','🤱','🌸','💅','🌺','💄','🦋','miss','mrs',
    'bride','midwife','doula','she/','/her','auntie','aunty','niece','goddess',
    '🙋','🤰','👧',
]

def is_female(u):
    combined = ' '.join([
        (u.get('biography') or '').lower(),
        (u.get('full_name') or '').lower(),
        (u.get('username') or '').lower(),
    ])
    return any(s in combined for s in FEMALE_SIGNALS)
```

## Cookie management
Cookies expire. When enrich fails, ask Tanzim for fresh cookies.
- **Correct tool**: Cookie-Editor by cgagnier (Chrome, blue icon)
  https://chrome.google.com/webstore/detail/cookie-editor/hlkenndednhfkekhgcdicdfddnkalmdm
  Open instagram.com → Cookie-Editor → Export → plain JSON
- **Wrong tool**: hotcleaner.com Cookie Manager — exports encrypted blobs, unparseable
- After getting fresh cookies, save to vault: `update_vault('instagram', {...})`

## Timing / rate limiting
- Between tag pages: 1.2s sleep
- Between user enrichments: 1.5s sleep
- On 429: wait 45–60s
- Between tags: 2s sleep
- Max pages per tag: 8–12 depending on tag size

## Filter criteria (Tanzim's Jun 2026 campaign)
- Followers: 500–3500
- Public accounts only (`is_private == False`)
- Female signals present
- Non-fitness profiles acceptable — lifestyle, beauty, wellness all count

## Output format
```python
{
    'city': 'Melbourne',
    'username': 'handle',
    'full_name': 'Name',
    'followers': 1234,
    'bio': 'first 120 chars, newlines replaced with spaces',
    'uid': '12345678'
}
```
Save incrementally to `/tmp/ig_targets_vN.json` so progress survives interruption.

## Melbourne tags (tested)
`melbournefit`, `melbournefitness`, `melbournegym`, `melbourneyoga`, `melbournewellness`,
`melbournepilates`, `melbournerunning`, `melbourneactive`, `fitmelbourne`, `melbournebootcamp`,
`melbournelifting`, `gymmelbourne`, `yogamelbourne`, `pilatesmelbourne`, `melbournegirlswholift`,
`melbournewomen`, `melbournehealth`, `melbournedance`, `melbournespin`, `melbournecrossfit`,
`melbourneboxing`, `melbournehiit`, `melbournelifestyle`, `melbourneliving`, `melbournegirls`,
`melbournewoman`, `melbourneblogger`, `melbournepersonaltrainer`, `melbournecoach`,
`melbournemum`, `melbournemums`, `melbournemama`, `melbourne`

## Tallinn tags (tested)
`tallinnwomen`, `eestifitness`, `fitnesseesti`, `tallinnlife`, `estonialife`, `eestinaised`,
`tallinnlifestyle`, `estonianwomen`, `estonia`, `estonianlife`, `estonianwellness`,
`tallinnhealth`, `estonianlifestyle`, `tallinn`, `tallinnfit`, `tallinnfitness`,
`estoniafit`, `tallinnsport`

## Current results (Jun 3 2026)
35 Melbourne + 27 Tallinn = 62 total in `/tmp/ig_targets_v7.json`
Extended Melbourne run in progress → `/tmp/ig_targets_v8.json` (target: 100 Melbourne)
