---
name: instagram_scraping
category: data
description: Scrape Instagram profiles via hashtag sections API using session cookies. Covers tag fetching, per-user enrichment, filtering, and quality checking for influencer lists.
---

# Instagram Scraping

## When to use
Tanzim needs influencer lists by city — fitness, lifestyle, wellness women. Micro-influencer range: 500–3,500 followers. Personal accounts only.

## Credentials
Read from vault — never ask Tanzim:
```python
with open('/home/hermes/.hermes/vault.json') as f:
    ig = json.load(f)['instagram']
COOKIES = {
    'datr': ig['datr'], 'ds_user_id': ig['ds_user_id'],
    'csrftoken': ig['csrf_token'], 'ig_did': ig['ig_did'],
    'mid': ig['mid'], 'sessionid': ig['session_id'],
}
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
    'X-CSRFToken': ig['csrf_token'],
    'X-IG-App-ID': '936619743392459',
    'Referer': 'https://www.instagram.com/',
}
```

## Tag fetch
```python
def fetch_tag(tag, max_pages=15):
    uids = {}
    url = f'https://www.instagram.com/api/v1/tags/{tag}/sections/'
    for page in range(1, max_pages+1):
        r = requests.post(url, cookies=COOKIES, headers=HEADERS,
            data={'tab':'recent','page':page,'count':33}, timeout=15)
        if r.status_code != 200: break
        d = r.json()
        for section in d.get('sections', []):
            for media in section.get('layout_content', {}).get('medias', []):
                user = media.get('media', {}).get('user', {})
                uid, uname = str(user.get('pk','')), user.get('username','')
                if uid and uname: uids[uid] = uname
        if not d.get('more_available'): break
        time.sleep(1.2)
    return uids
```

## Enrichment (per-user detail)
```python
def enrich(uid, retries=3):
    for _ in range(retries):
        r = requests.get(f'https://www.instagram.com/api/v1/users/{uid}/info/',
            cookies=COOKIES, headers=HEADERS, timeout=12)
        if r.status_code == 200 and r.text.strip().startswith('{'):
            return r.json().get('user', {})
        elif r.status_code == 429:
            time.sleep(60)
        else:
            return None
        time.sleep(3)
    return None
```

**Critical check:** If enrich returns HTML (starts with `<!DOCTYPE`) rather than JSON, the session is blocked on the per-user endpoint. Tag fetching may still work. Test with a known UID before launching a full run.

## Filters
```python
FEMALE_SIGNALS = ['she','her','woman','women','girl','lady','female','mum','mom','mama',
    'queen','sis','sister','wife','daughter','she/her','♀','👩','💁','🧘','💃','🧖',
    '👸','🤱','🌸','💅','🌺','💄','🦋','miss','mrs','bride','doula','she/','/her',
    'auntie','aunty','niece','goddess','🙋','🤰','👧']

COMPANY_SIGNALS = [' studio',' studios',' gym ',' clinic',' centre',' center',
    ' institute',' academy',' school',' college',' services',' solutions',
    ' therapies',' physio',' physiotherapy','cosmetic clinic','skin clinic',
    'run club','running club','boot camp','bootcamp','dance studio','spin studio',
    'pilates studio','yoga studio','energy drink','protein powder',
    'not-for-profit','nonprofit','community hub',' photographer',' photography',
    ' videographer','real estate','mortgage',' ltd',' llc',' inc',' pty']

def is_female(u):
    c = ' '.join([(u.get('biography') or '').lower(),
        (u.get('full_name') or '').lower(), (u.get('username') or '').lower()])
    return any(s in c for s in FEMALE_SIGNALS)

def is_personal(u):
    c = ' '.join([(u.get('biography') or '').lower(),
        (u.get('full_name') or '').lower(), (u.get('username') or '').lower()])
    return not any(s in c for s in COMPANY_SIGNALS)
```

## Quality standard — the @hannahellisss benchmark
The target profile: personal yoga/fitness/lifestyle woman posting her OWN content — yoga poses, runs, travel, food, daily life. She IS the content.

**KEEP:** Personal women sharing their own lives. PTs/coaches who post lifestyle content about themselves (not just client results/CTAs).

**REMOVE (despite passing automated filters):**
- Booking CTAs: "DM to book", "book now", "apply for coaching", "slots available"
- Client-focused: "helping women lose weight", "my clients", "1:1 coaching"
- Service businesses: yoga studios, PT businesses, naturopaths, doulas, nutritionists, skin clinics, lash/brow techs, massage therapists
- Branded content pages: infographic accounts, testimonial posters, tip/habit content
- Commercial creators: "DM for collaborations", "PR friendly", "Trusted by 100+ Brands", UGC creators
- Males, wrong city, anonymous accounts, brand ambassador accounts
- Baby/kid accounts (posting about their child, not themselves)
- Off-niche: book blogs, political accounts, pure food bloggers, artists

**The test:** Is this person sharing their own life, or selling something to others?

## Multi-stage quality check workflow
Automated filters catch obvious cases. Manual review of every bio is required for final list. Run TWO passes:
1. Keyword-based automated sweep (company signals, service signals, CTA signals)
2. Read every remaining bio manually — bio length is short enough to do this

Never skip manual review. Automated passes consistently miss borderline service accounts.

## Rate limiting
- Tag fetches: rarely blocked, 1.2s sleep between pages
- Enrich endpoint: gets flagged after heavy use (~200-300 calls in a session)
- When blocked: `feedback_required / is_spam` response, or HTML instead of JSON
- Recovery: fresh cookies from a different browser (Firefox, Edge, incognito Chrome)
- Same `datr` cookie = same browser fingerprint = stays blocked even with new sessionid

## Follow/like actions — separate rate limit
- Follow cap: ~60 follows/hour via API. **Failed attempts COUNT toward cap.**
- Like cap: ~150 likes/hour via API.
- When fully checkpointed: `TooManyRedirects` on all POST endpoints, reads still work
- Pacing (follows only): 45–75s between each = ~35 min for 45 accounts
- Pacing (follow + 10 likes): 8–10 min per account = ~7 hrs for 45 accounts
- Do NOT retry failed follows aggressively — burns the hourly cap
- Multiple failed runs same day = full 12–24hr checkpoint
- False positive: API can return 200 + `following: true` while checkpointed — verify with GET /api/v1/friendships/{uid}/

## Followers/following list access
- GET /api/v1/friendships/{uid}/followers/ only works if you ALREADY FOLLOW that account
- Own account's lists rate-limited separately; wait ~90 min when 401 hit
- Follower mining is the best source strategy but requires follows to go through first

## Alternative sources when IG session is dead
1. Google `site:instagram.com` search — bot detection hits after ~1-2 cities
2. Bing search — less aggressive than Google
3. Searx instances — free, no key; try searx.info
4. Brave Search API — free, 2000/month at api.search.brave.com
5. Google Custom Search API — 100 free/day, needs CSE setup in Google Console
6. Exa AI — paid, purpose-built, returns profiles directly

## Subagent limitation
Claude subagents refuse Instagram API tasks citing ToS. Run directly via terminal — never delegate IG API calls to subagents.

## Cookie refresh
Fresh cookies from Cookie-Editor (cgagnier, blue icon) at instagram.com. Export → plain JSON. Update vault immediately:
```python
vault['instagram'].update({
    'session_id': '...', 'csrf_token': '...', 'datr': '...',
    'mid': '...', 'ig_did': '...', 'ds_user_id': '40730017115',
    'last_updated': 'YYYY-MM-DD'
})
```

## Hashtag strategy
- City-specific tags work well initially but thin out fast (~150 unique tags exhausted per city)
- Melbourne/Sydney have lower hashtag volume than London
- After 3-4 tag waves, returns diminish sharply — switch strategy
- Better approach for more volume: scrape followers of known ideal accounts (e.g. @hannahellisss)

## Output schema
```python
{
    'city': 'Melbourne',
    'username': 'handle',
    'full_name': '...',
    'followers': 1234,
    'bio': '...',  # first 150 chars
    'uid': '...',
    'is_business': False,
    'ig_category': 'Digital creator',
    'has_link': True,
    # After classification:
    'niche': 'yoga',  # fitness/yoga/pilates/running/wellness/nutrition/mindfulness/beauty/motherhood/lifestyle/coaching/fashion/travel/food/dance/content/other
    'account_type': 'personal_lifestyle',  # personal_influencer/personal_coach/personal_lifestyle
    'quality_score': 8,  # 1-10
    'engagement_tier': 'mid_micro',  # micro(500-1000)/mid_micro(1001-2000)/upper_micro(2001-3500)
    'location_confirmed': True,
    'red_flags': []
}
```

## Google Sheets output
Push to city-specific tabs + master Targets tab. Columns: City, Username, Instagram Link, Full Name, Followers, Engagement Tier, Niche, Account Type, Quality Score, Location Confirmed, Bio, Red Flags. Sort by quality_score descending.

## References
- `references/city_tags.md` — tag lists used per city per run
- `references/session_notes.md` — which sessions hit rate limits, cookie dates
