# Instagram Scraping — API Patterns & Pitfalls

## Working endpoints (as of June 2026)
| Endpoint | Method | Status | Notes |
|---|---|---|---|
| `/api/v1/tags/{tag}/sections/` | POST | ✅ Reliable | Returns media + user stubs. Paginate with `page` param |
| `/api/v1/users/{uid}/info/` | GET | ⚠️ Rate-limited | Returns full profile. Breaks before tag endpoint |
| `/api/v1/users/web_profile_info/?username=X` | GET | ❌ 429s fast | Avoid |
| `/{username}/?__a=1&__d=dis` | GET | ❌ Returns HTML | Dead |

## Tag fetch pattern
```python
r = requests.post(
    f'https://www.instagram.com/api/v1/tags/{tag}/sections/',
    cookies=COOKIES, headers=HEADERS,
    data={'tab': 'recent', 'page': page, 'count': 33},
    timeout=15
)
data = r.json()
more = data.get('more_available')  # paginate while True
```
- Tag fetch returns minimal user data: pk, username, is_private, full_name — NO follower_count, NO biography
- Must enrich separately to get follower count and bio

## Enrich pattern
```python
r = requests.get(
    f'https://www.instagram.com/api/v1/users/{uid}/info/',
    cookies=COOKIES, headers=HEADERS, timeout=12
)
# CRITICAL: check it's actually JSON, not HTML
if r.status_code == 200 and r.text.strip().startswith('{'):
    user = r.json().get('user', {})
```
- Returns: follower_count, biography, is_private, is_business, category, external_url, full_name
- **Always check `r.text.strip().startswith('{')` — a blocked session returns 200 with HTML**

## Rate limit behaviour
- `feedback_required / is_spam` in JSON → heavy rate limiting, wait 30–60 min
- HTML response on 200 → session flagged, need fresh cookies
- 429 → hard rate limit, wait 60s and retry
- Tag endpoint stays alive longer than enrich — can still fetch tags when enrich is dead
- Pacing: 1.2s between page fetches, 1.5s between enrich calls, 2s between tags

## Female signal detection
```python
FEMALE_SIGNALS = [
    'she','her','woman','women','girl','lady','female','mum','mom','mama',
    'queen','sis','sister','wife','daughter','she/her','♀','👩','💁','🧘',
    '💃','🧖','👸','🤱','🌸','💅','🌺','💄','🦋','miss','mrs','bride',
    'doula','she/','/her','auntie','aunty','niece','goddess','🙋','🤰','👧',
]
def is_female(u):
    combined = ' '.join([
        (u.get('biography') or '').lower(),
        (u.get('full_name') or '').lower(),
        (u.get('username') or '').lower(),
    ])
    return any(s in combined for s in FEMALE_SIGNALS)
```

## Company/brand filter (personal accounts only)
```python
COMPANY_SIGNALS = [
    ' studio',' studios',' gym ',' clinic',' centre',' center',
    ' institute',' academy',' school',' college',' services',' solutions',
    ' therapies',' physio',' physiotherapy','cosmetic clinic','skin clinic',
    'run club','running club','boot camp','bootcamp','dance studio',
    'spin studio','pilates studio','yoga studio','energy drink',
    'protein powder','not-for-profit','nonprofit','community hub',
    ' photographer',' photography',' videographer','real estate',
    'mortgage',' ltd',' llc',' inc',' pty',
]
def is_personal(u):
    combined = (bio + name + username).lower()
    return not any(s in combined for s in COMPANY_SIGNALS)
```
**Pitfall:** keyword filter is imperfect. Personal PTs/coaches often get flagged as companies.
Do a manual KEEP list for borderline cases rather than auto-excluding.

## Classification columns for Google Sheets
Fields to collect per profile:
- city, username, full_name, followers, bio, uid
- is_business (from API), ig_category (from API), has_link (bool)
- niche, account_type, quality_score (1-10), engagement_tier, location_confirmed, red_flags

## Engagement tiers
- micro: 500–1000
- mid_micro: 1001–2000
- upper_micro: 2001–3500

## Quality score rubric
- 8–10: clear person, strong niche, city confirmed in bio
- 5–7: decent but vague or location inferred from tag only
- 1–4: weak bio, unclear if personal, or off-niche

## Hashtag strategy by city
- London: very high volume, productive. Cultural/community tags (londonhijabi, londonblackgirl, londonlatina) yield diverse results.
- Sydney: moderate volume. Gets rate-limited faster than London.
- Melbourne: thin volume. Hashtags run dry quickly; filters hit hard (65 personal from 100+ raw).
- Tallinn: very thin. Fitness hashtags sparse; most results are service businesses or non-Estonian.

## Post-scrape quality audit (essential — removes ~20–25%)
Keyword filters miss: males with male full_name, wrong-location profiles, businesses that slipped filters, bot accounts (random alphanumeric usernames). Always audit before pushing to sheet.

Subagent prompt for audit:
> Read /tmp/ig_classified.json. For each profile flag: (1) clearly male, (2) wrong location vs tagged city, (3) business/brand account, (4) bot signals (alphanumeric username, no bio), (5) off-niche entirely, (6) duplicates. Output: flagged list with REMOVE/REVIEW, write clean file to /tmp/ig_final_clean.json, print full report.

Plan for attrition: want 100 clean profiles → scrape 130+ raw.

## Diminishing returns — when hashtags run dry
Symptom: 3rd wave returns <35 profiles from 70+ tags.
Next strategy: location geotag scraping or follower-graph from known seed accounts — not more hashtag waves.
Per-city ceiling from hashtags alone: London ~200, Sydney ~130, Melbourne ~100, Tallinn ~15.

## Google Sheets — enriched influencer sheet columns
Standard header: City | Username | Instagram Link | Full Name | Followers | Engagement Tier | Niche | Account Type | Quality Score | Location Confirmed | Bio | Red Flags
Sort by quality_score DESC within each city tab.

## Gmail label management (JPMC pattern)
```python
# Create label
label = service.users().labels().create(userId='me', body={'name': 'JPMC'}).execute()
label_id = label['id']
# Move emails: apply label + remove INBOX
service.users().messages().modify(userId='me', id=mid, body={
    'addLabelIds': [label_id],
    'removeLabelIds': ['INBOX']
}).execute()
```
Search queries for JPMC: `from:jpmorgan OR from:jpmchase OR from:jpmorganchase OR subject:jpmorgan OR from:BIGreport.com OR Global Workforce Screening jpmorgan`

## Personal account benchmark — what to KEEP
The reference account is **@hannahellisss** (Hannah Jane Ellis, London). Keep accounts that match this pattern:
- Personal woman posting her OWN life: yoga poses, runs, travel, retreats, meals, daily moments
- She IS the content — not selling a service, not posting client results
- No pricelist, no booking CTA, no "DM to book", no before/after client transformations

**The key test:** Is this person sharing their own life, or selling a service to others?

### Remove even if they passed keyword filters:
- Solo PTs whose whole feed is client promos / programme CTAs ("Apply for coaching ⬇️")
- Yoga teachers with retreat bookings as primary CTA ("EMBODIED YIN YOGA IMMERSION — book now")
- Naturopaths, nutritionists, life coaches with "helping women" + booking links
- Doulas with booking CTAs (even if personal-sounding name)
- UGC creators who explicitly market to brands ("Trusted by 100+ Brands", "DM for Collaborations")
- Baby/child accounts that post about the child not themselves
- Anonymous accounts with no personal identity ("Explorer", "Adventures with a sketchbook")
- Accounts based outside the target city despite being found via city hashtag

### Keep even if they have professional credentials:
- Personal trainers who post their OWN workouts and lifestyle (not client results)
- Yoga practitioners who post their own practice (not selling classes as primary content)
- Runners documenting their own marathon training
- Mums sharing their own daily life (not a baby/product account)

### Beauty service removal pattern
Remove anyone whose bio/name contains: lash, brow, PMU, cosmetic tattoo, nail tech, spray tan, hair salon, skin clinic, aesthetician, injectable, filler, botox, dermaplaning, waxing, threading, tinting, lamination, extensions, lash lift, lash artist, brow artist, beauty therapist, beauty technician, beauty salon, medi spa, medspa, skin therapist.

### Service keyword removal pattern (2+ hits = remove)
SERVICE_SIGNALS that indicate selling not sharing:
```
'dm to book','book now','booking','slots available','taking clients',
'apply for coaching','online programme','online program',
'1:1','1-1','join my','apply now','free consultation',
'certified pt','qualified pt','level 3','level 4',
'meal plans','macro coach','online coach','life coach',
'reiki master','reiki practitioner','sound healer','naturopath',
'kinesiologist','osteopath','acupuncturist','therapist',
'personal stylist','ugc creator','ugc portfolio',
```
Rule: 2+ hits AND no strong lifestyle counterbalance = remove. 3+ hits = always remove.

LIFESTYLE_SIGNALS (counterbalance):
```
'just a girl','documenting','sharing my','my journey','my life',
'living my','exploring','adventures','moments','diary',
'lover of','obsessed with','mum to','mom to','mama to',
'travel','foodie','coffee lover',
```

## Follower-graph scraping
**Better signal than hashtags** — followers of seed accounts are the exact target demographic.

### Endpoint
```python
r = requests.get(
    f'https://www.instagram.com/api/v1/friendships/{uid}/followers/',
    cookies=COOKIES, headers=HEADERS,
    params={'count': 50, 'max_id': next_max_id},  # paginate with next_max_id
    timeout=15
)
d = r.json()
users = d.get('users', [])  # list of user stubs
next_max_id = d.get('next_max_id')  # None when done
```

### Critical pitfall — must be following the seed account
Instagram only returns followers of accounts **you follow**. If not following, returns 0 results silently (no error).
**Sequence:** run follow job first → then run follower-graph scrape.

### Workflow
1. Build seed list from existing clean accounts (the 45 verified personal accounts)
2. Follow all seeds first (follow job must complete)
3. Scrape followers: 50 per page, paginate with next_max_id
4. Enrich + filter same as hashtag scrape
5. Expected yield: much cleaner than hashtags, ~10-30% pass rate vs ~5% for hashtags

## Instagram follow/like actions — rate limits & pacing
### Hard limits (approximate, enforced per hour)
- Follows: ~60/hour
- Likes: ~150/hour

### Safe pacing
- **Follow only:** 45–75 seconds between each follow → ~35 mins for 45 accounts
- **Follow + like (10 posts):** 25–35s between likes, 8–10 min between accounts → 6–7 hours for 45 accounts
- Every 10 accounts: add 5 min extra pause

### Critical pitfall — API 200 ≠ action succeeded
The follow endpoint returns 200 even when the action was blocked. Always verify with friendship_status:
```python
r = requests.post(f'https://www.instagram.com/api/v1/friendships/create/{uid}/', ...)
if r.status_code == 200:
    fs = r.json().get('friendship_status', {})
    # following=True means followed; outgoing_request=True means sent (private account)
    success = fs.get('following', False) or fs.get('outgoing_request', False)
```

### Rate limit detection
```python
if r.status_code == 429 or 'feedback_required' in r.text:
    time.sleep(600)  # 10 min pause
```

### Headers needed for write actions
```python
HEADERS = {
    ...
    'X-Instagram-AJAX': '1',
    'Origin': 'https://www.instagram.com',
}
```

### Getting user posts for liking
```python
r = requests.get(
    f'https://www.instagram.com/api/v1/feed/user/{uid}/?count=12',
    cookies=COOKIES, headers=HEADERS, timeout=12
)
post_ids = [item['pk'] for item in r.json().get('items', [])[:10]]
```

### Like endpoint
```python
r = requests.post(
    f'https://www.instagram.com/api/v1/media/{media_id}/like/',
    cookies=COOKIES, headers=HEADERS, timeout=12
)
```

### Sheet integration — mark followed in real time
```python
# Find username in sheet, write ✅ Followed to 'Followed' column
# Add 'Followed' column to header if not present
# Use chr(65 + col_idx) for column letter (A=0, B=1, etc.)
sheets.spreadsheets().values().update(
    spreadsheetId=SID, range=f'{tab}!{col_letter}{row_idx}',
    valueInputOption='RAW', body={'values': [['✅ Followed']]}
).execute()
```

## Known dead/empty tags (as of June 2026)
- melbournehormones, melbournewomenrunning, melbournepilateslover, melbourneactivewomen
- londonwomenwholift, londonwomenrunning, londonpilateslover, londonafrofit
- sydneyblackgirl, sydneyblackwomen, sydneywomenwholift, sydneywomenrunning
