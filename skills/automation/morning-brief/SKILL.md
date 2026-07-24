---
name: morning-brief
description: Tanzim's 8:00 AM morning prep brief — scheduled cron delivery via WhatsApp
category: automation
tags: [cron, whatsapp, brief, gmail, crypto, fitness-tech, morning]
triggers:
  - morning brief
  - 8am brief
  - daily brief
  - morning prep
---

# Morning Brief

Tanzim's automated 8:00 AM daily briefing, delivered to his personal WhatsApp DM (`160799431606497@lid`).

## Delivery

Send via bridge direct API (not `send_message` tool — cron context requires raw HTTP).

**Use `execute_code` — `requests` and `subprocess` both work.** Confirmed July 2026: two patterns, both verified:

**Pattern A (subprocess grep — confirmed working 2026-07-22):**
```python
import subprocess, requests

result = subprocess.run(['grep', 'WHATSAPP_BRIDGE_TOKEN', '/home/hermes/.hermes/.env'], capture_output=True, text=True)
token = result.stdout.strip().split('=', 1)[1]  # split on first = only; value may contain special chars

TANZIM_JID = "160799431606497@lid"

resp = requests.post(
    'http://localhost:3000/send',
    json={"chatId": TANZIM_JID, "message": message},
    headers={"Authorization": f"Bearer {token}"},
    timeout=30
)
print(resp.status_code, resp.json())
```

**Pattern B (check_output — also works):**
```python
token = subprocess.check_output("grep WHATSAPP_BRIDGE_TOKEN ~/.hermes/.env | cut -d= -f2", shell=True).decode().strip()
```

> **Token source:** Read from `~/.hermes/.env`. `.env` is authoritative. Verified 2026-07-17 and 2026-07-22.

> **JID format:** `160799431606497@lid` (lid suffix, NOT `@s.whatsapp.net`). Confirmed working.

> **Pitfall:** The payload key is `chatId`, NOT `to`. Using `to` returns a 400 error.

> **Pitfall:** Token value in `.env` may appear truncated in debug output — always use `split('=', 1)[1].strip()` to get the full value. A partial token causes 401 Unauthorized.

> **Bridge auth:** `/health` is unauthenticated. All other endpoints require `Authorization: Bearer <token>`. A 401 means token not sent or wrong — check `.env` read path.
```

## Structure

Three sections, tight — scannable, no walls of text.

```
*MORNING BRIEF — [Day DD Mon, HH:MM AM]*

*GMAIL*
[1–4 lines. Real signals only. See triage rules below.]

*CRYPTO*
[1-line market tone, then 3 swing setups — ticker, price, reason]

*FITNESS TECH*
[1–2 lines. Relevant to Timbr. "Quiet." if nothing.]
```

Use WhatsApp bold (`*...*`) for section headers. No emojis. No preamble. Lead with content.

## Section 1: Gmail

Account: `tanzim.seattle@gmail.com`
Auth: see `gmail-automation` skill — use `execute_code` + `urllib.request` (Option A), it's faster in cron context.

**OAuth credential order:** Try `google_token.json` (client `313611152308-...`) first — confirmed working 2026-07-22 and 2026-07-23. `GOOGLE_OAUTH_ACTIVE.json` (client `990922176945-...`) is the backup if the primary refresh fails.

Query: `in:inbox is:unread after:{unix_timestamp}`, maxResults 20, fetch metadata (Subject, From, Date, snippet).

Use a 12-hour lookback window (overnight scope):
```python
from datetime import datetime, timezone, timedelta
after_time = int((datetime.now(timezone.utc) - timedelta(hours=12)).timestamp())
query = f'in:inbox is:unread after:{after_time}'
```

Fetch token via OAuth refresh (see `gmail-automation` skill) — use `urllib.request`, not `requests`.

### What to surface
- Real recruiter replies, interview scheduling, phone screen invites
- BrightHire notifications — these mean an interview is actually booked; always surface
- "Complete your profile" / "action required" from ATS systems (blocks future applications if ignored)
- Monster/LinkedIn/Indeed "you have a new message" notifications (actual humans messaging, not auto-acks)
- Anything with: schedule, interview, available, phone screen, offer, next steps
- **Rejections** (even auto-generated): surface as a brief one-liner — "Company X — rejected."
- **Role on hold:** surface separately from rejections — "Company X — role placed on hold, not a rejection." This matters; it's a keep-warm signal, not a close.
- **Incomplete applications with deadlines** — if deadline is TODAY, flag it explicitly

### What to skip (noise)
- "Thank you for applying" auto-acks with no next step and no deadline
- "We received your application" confirmations with no action
- "Application submitted" receipts
- Emails from: indeedapply@indeed.com, @applytojob.com, @hire.lever.co, @candidates.workablemail.com
- @adp.com "application received" relay emails (surface only if they contain rejection or next steps)
- `@myworkday.com` — ATS relay; check snippet. If rejection language ("decided to focus on other candidates", "we will not be moving forward", "wish you the best") → include as one-liner. If auto-ack → skip. **Do not skip `@myworkday.com` emails without inspecting the snippet — the same domain carries both auto-acks and rejections.**
- `@successfactors.eu`, `@greenhouse-mail.io`, similar ATS domains: rejection = surface; auto-ack = skip
- GDPR data-deletion notices — admin noise, skip unless active relationship
- Monster/Dice/LinkedIn *marketing* emails (salary surveys, "complete your profile", job alert digests)
- Job board welcome/onboarding emails (Qureos, etc.)

**BUT surface:** Monster "You have N new messages in your Monster inbox" — means actual recruiters have DMed.

If nothing clears the bar: one line saying so.

## Section 2: Crypto

Source: CoinGecko public API (no key needed). Use `execute_code` with `requests`.

```python
import requests

# Top 20 coins with 30d + 7d price change for swing candidates
data = requests.get(
    'https://api.coingecko.com/api/v3/coins/markets',
    params={
        'vs_currency': 'usd',
        'order': 'market_cap_desc',
        'per_page': 20,
        'page': 1,
        'sparkline': 'false',
        'price_change_percentage': '7d,30d'
    }
).json()
```

### Swing candidate filter (buy-low setups)

**Use 30d change as the primary signal** — sustained weakness vs. one-day dips. Scan top 100 by market cap (not just top 20) to find viable candidates outside the mega-caps.

```python
import requests

# Top 100 with 30d + 7d for swing candidates
resp = requests.get(
    'https://api.coingecko.com/api/v3/coins/markets',
    params={
        'vs_currency': 'usd',
        'order': 'market_cap_desc',
        'per_page': 100,
        'page': 1,
        'price_change_percentage': '24h,7d,30d',
        'sparkline': False
    },
    timeout=15
)
coins = resp.json()
```

**Market tone (separate call):**
```python
market = requests.get('https://api.coingecko.com/api/v3/global', timeout=10).json()['data']
total_cap = market['total_market_cap']['usd']
change_24h = market['market_cap_change_percentage_24h_usd']
btc_dom = market['market_cap_percentage']['btc']
# e.g. "$2.33T cap, -1.1% overnight, BTC dominance 56.6%"
```

**Filter logic (confirmed working 2026-07-22):**
```python
stables = {'USDT', 'USDC', 'BUSD', 'DAI', 'TUSD', 'FRAX', 'LUSD', 'USDP', 'GUSD', 'USDS'}

candidates = []
for c in coins:
    if c['symbol'].upper() in stables:
        continue
    p30 = c.get('price_change_percentage_30d_in_currency') or 0
    p7  = c.get('price_change_percentage_7d_in_currency') or 0
    p24 = c.get('price_change_percentage_24h') or 0
    ath_change = c.get('ath_change_percentage') or 0

    # Down 10%+ on 30d AND 7d trend better than 30d (stabilising)
    if p30 < -10 and p7 > p30:
        candidates.append({
            'symbol': c['symbol'].upper(),
            'price': c['current_price'],
            'p30': p30, 'p7': p7, 'p24': p24,
            'rank': c['market_cap_rank'],
            'ath_change': ath_change
        })

# Sort by steepest 30d drop; pick top 3
candidates.sort(key=lambda x: x['p30'])
top3 = candidates[:3]
```

**Prefer candidates where 7d is also turning positive** — early reversal signal, strongest swing case.

**Brief one-liner per coin:** `- TICKER $price — down X% in 30d, [7d context / why it's a swing candidate].`

> **Pitfall:** `price_change_percentage_30d_in_currency` can be `None` — always `or 0` before any comparison or format call.

## Section 3: Fitness Tech

Relevance lens: trainer/client apps, wearables, AI fitness coaching, connected equipment, funding rounds, competitor moves, regulatory signals — anything relevant to Timbr's space.

Sources that work (no CAPTCHA / bot blocks):
- **Bing News RSS (best all-rounder, confirmed 2026-07-20):** `https://www.bing.com/news/search?q=fitness+technology+wearables+AI+trainer+app&format=RSS` — returns recent headlines, parseable via regex, no auth needed
- `https://athletechnews.com/` — best source, fitness industry focused, loads cleanly
- **TechCrunch daily page** `https://techcrunch.com/YYYY/MM/DD/` — today's full tech firehose; keyword-scan for fitness/health/wearable. Confirmed loading cleanly 2026-07-23 when tag page had nothing current.
- `https://www.mobihealthnews.com/` — health tech, broader but relevant; confirmed working 2026-07-16 (Cloudflare-blocked 2026-07-23 — may be intermittent)
- `https://www.prnewswire.com/news-releases/news-releases-list/` — broad press releases, funding rounds, major product announcements; filter by Lifestyle & Health or search keyword
- `https://techcrunch.com/category/biotech-health/` — occasional fitness tech

**Bing RSS parse pattern (fastest path):**
```python
import requests, re
resp = requests.get(
    'https://www.bing.com/news/search?q=fitness+technology+AI+trainer+wearables&format=RSS',
    headers={'User-Agent': 'Mozilla/5.0'},
    timeout=8
)
items = re.findall(r'<item>(.*?)</item>', resp.text[:15000], re.DOTALL)
for item in items[:6]:
    title = re.findall(r'<title>(.*?)</title>', item)
    pub   = re.findall(r'<pubDate>(.*?)</pubDate>', item)
    desc  = re.findall(r'<description>(.*?)</description>', item)
    if title:
        clean_title = re.sub(r'<[^>]+>', '', title[0])
        clean_desc  = re.sub(r'<[^>]+>', '', desc[0])[:200] if desc else ''
        pub_date = pub[0][:30] if pub else ''
        print(clean_title, '|', pub_date)
        print(clean_desc)
```

Filter results for items < 48h old and relevant to Timbr's space.

**HN Algolia (`hn.algolia.com`) for fitness tech: usually returns zero results** — not worth trying first for this topic. Bing RSS is more reliable.

**Confirmed blocked (skip entirely):**
- Google search / `news.google.com` — CAPTCHA/bot blocked in headless cron context
- `wareable.com` — Cloudflare challenge, unresolvable
- `fiercehealthcare.com` — Cloudflare block
- `digitaltrends.com/fitness/` — 404 (page removed)

Scan the homepage for articles from the last 24–48h. If nothing notable: `"Quiet."`

One to two lines max. Name the company/product and what matters about it for Timbr.

## Format rules

- WhatsApp bold for headers only: `*GMAIL*`, `*CRYPTO*`, `*FITNESS TECH*`
- One idea per line
- No paragraph walls
- No emojis
- No preamble ("Good morning Boss, here's your brief") — start with `*MORNING BRIEF*`
- Date header: `*MORNING BRIEF — Sun 13 Jul, 8:00 AM*`

## References
- `references/swing-trade-filter.md` — detailed notes on the buy-low swing candidate logic
- `references/sample-brief.md` — example output
- `references/session-2026-07-22.md` — worked example: full email signal/noise breakdown, confirmed delivery pattern, crypto filter that produced good results
- `references/session-2026-07-23.md` — 2026-07-23 signal/noise breakdown; OAuth credential note; crypto filter regression (ATH% shortcut used instead of p30+p7 — avoid); fitness tech source reliability map

## Pitfalls
- Google News search (`news.google.com`) is blocked with bot detection — use site-direct URLs
- Google search is CAPTCHA-blocked in headless browser — go direct to source sites
- CoinGecko free API is rate-limited; one global + one markets call is fine, don't hammer it
- `send_message` tool may behave differently in cron context — use bridge direct HTTP to be safe
