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
Returns: follower_count, biography, is_private, is_business, category, external_url, full_name

## Rate limit behaviour
- `feedback_required / is_spam` → heavy rate limiting, wait 30–60 min
- HTML response on 200 → session flagged, need fresh cookies
- 429 → hard rate limit, wait 60s and retry
- Tag endpoint stays alive longer than enrich — can fetch tags when enrich is dead
- Pacing: 1.2s between pages, 1.5s between enriches, 2s between tags

## Female signal detection
```python
FEMALE_SIGNALS = [
    'she','her','woman','women','girl','lady','female','mum','mom','mama',
    'queen','sis','sister','wife','daughter','she/her','♀','👩','💁','🧘',
    '💃','🧖','👸','🤱','🌸','💅','🌺','💄','🦋','miss','mrs','bride',
    'doula','she/','/her','auntie','aunty','niece','goddess','🙋','🤰','👧',
]
```

## Company/brand filter
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
```
**Pitfall:** keyword filter is imperfect — solo PTs/coaches often get caught. Use manual KEEP list for borderlines.

## Known dead/thin tags (June 2026)
- melbournehormones, melbournewomenrunning, melbournepilateslover, melbourneactivewomen
- londonwomenwholift, londonwomenrunning, londonpilateslover, londonafrofit
- sydneyblackgirl, sydneyblackwomen, sydneywomenwholift, sydneywomenrunning
- londonmidlife, londonover40, londonover30 (0 candidates)
