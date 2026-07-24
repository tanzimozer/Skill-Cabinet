# Sheet-Triggered Playwright Crawler (Bulldozer architecture)

A more advanced variant of this pipeline, built July 2026 for Tanzim's "Bulldozer"
repo (github.com/tanzimozer/Bulldozer, Mac clone at ~/Desktop/Bulldozer). Use this
when the crawl must **trigger from chat/Hermes, not from a Claude relay**, and when
follower counts must be verified live rather than parsed from bio text.

## The trigger channel: a "Commands" tab, not a message bridge

Core insight (user demand, emphatic): **everything triggers from Hermes directly**,
never by asking Claude to run a command. The mechanism:

- Google Sheet "Bulldozer — Handles" has a `Commands` tab (8-col schema):
  `id | command | target | depth | status | result | requested_at | done_at`
- Friday writes a `pending` row directly via the live vault token
  (`~/.hermes/google_token.json`) — see the OAuth note below.
- `listener_sheet.py` runs on the always-on Mac, polls the Commands tab every 10s,
  executes any `pending` row, writes status back (`pending → running → done|error`).
- Commands supported: `crawl`, `enrich`, `kill`. Only `crawl` rows trigger a crawl;
  a `kill` row must be explicitly honoured by the listener (`kill_crawler()` sweeps
  `pgrep -f crawler.py` + SIGKILL). Early bug: sheet `kill` rows were ignored until
  the handler was built — before that, killing needed a Claude `pkill`.

Claude/relay is used ONLY for things touching the Mac's running process the listener
can't do itself (git pull, restart). Never for the trigger write.

## Why the vault token, not gspread.oauth()

Friday's own local Google OAuth client was deleted ("OAuth client was deleted"), so
every direct `gspread.oauth()` write silently failed. Fix: use the live authorized-user
token already in the vault:

```python
from google.oauth2.credentials import Credentials
import gspread
SCOPES=["https://www.googleapis.com/auth/spreadsheets","https://www.googleapis.com/auth/drive"]
creds=Credentials.from_authorized_user_file("/home/hermes/.hermes/google_token.json", SCOPES)
gc=gspread.authorize(creds)
sh=gc.open_by_key("1Nuroehse6WIvruHpb1tiyc8ZayIxuWVzzk0sfnYsGi0")
```

This opens the exact sheet directly, no new service account needed. Check the vault for
a live token BEFORE walking the user through creating a Google Cloud service account.

## Crawler: Playwright + cookies, not BeautifulSoup

`crawler.py` drives a headless Chromium with the live IG session cookies
(`secrets/ig_cookies.json`). Hard-won selector lessons:

- **`[role='link']` matched ZERO elements** — Instagram doesn't set `role` on `<a>`.
  A qualifier like `dialog.locator("a[href^='/'][role='link']")` silently returns
  nothing and masks as a "bad seed". Root-caused a whole session of false zeros.
  Drop it; use `a[href^='/']` inside the dialog.
- **Opening the followers modal:** the `a[href$='/followers/']` selector goes stale.
  Use multi-selector fallback (4 tries) including `a:has-text('followers')`. Add a
  dialog-open wait and surface rich DIAG into the result cell: URL, anchor count,
  login-wall flag, sample anchors.
- **We pull FOLLOWERS, not following** (`a[href$='/followers/']`).
- **Seeds must be PUBLIC** — a private account's follower modal won't open (returns 0).
  Screenshots don't always show the lock; verify.
- **Cookie sameSite normalisation:** `sameSite:null` must become `"None"` (mapping:
  strict→Strict, lax→Lax, no_restriction/none→None, unspecified→Lax). A naive re-pull
  can revert this patch — guard it.

## depth semantics (user-locked)

- `depth=0` = seed's followers only, stop. **This is the default.**
- `depth=1` = + each follower's followers (one hop out).
- `depth=2/3` = exponential. Chaining is opt-in; depth lives in the command row so
  Friday can toggle 0↔1 from Hermes with no code change.

## Live follower-count band-prune (the key technique)

Bio-parsed counts are unreliable. To filter a fresh crawl tab by follower band, hit
Instagram's **`web_profile_info` JSON endpoint** per handle with the live session:

```
GET https://www.instagram.com/api/v1/users/web_profile_info/?username=<h>
headers: x-ig-app-id=936619743392459, x-requested-with=XMLHttpRequest,
         referer=https://www.instagram.com/<h>/, accept=application/json
```

`data.user.edge_followed_by.count` = followers, `.is_private`, etc. This is a clean
JSON pull, far more reliable than DOM scraping. Cost: one profile hit per handle,
human-paced 4–9s, so a 200-handle catch = a few minutes, not seconds. That is the
unavoidable price of the band filter — flag it to the user up front.

`fetch_counts(handles)` in enrich.py returns `{handle: {followers, private, error}}`
and is reused by the listener's tab-writer to prune. **Band 500–3,500** (was 150–3,500
earlier — bands change per user; read the current spec). Out-of-band or unreadable →
row dropped.

## Output tab formatting (current spec)

New date-named tab per crawl (`%b %d`, same-day repeat → `Jul 03 (2)`, never
overwrites). Columns: `Handle | Followers | Crawled_at`. Handle written as a live
`=HYPERLINK("https://www.instagram.com/<h>/","<h>")` via `value_input_option="USER_ENTERED"`.
Format ALL cells centre + middle + WRAP; header bold; freeze row 1.

## Provider-gated chaining (optional moat engine — since descoped)

Built then set aside when the user simplified the objective. Pattern worth keeping:
instead of blind depth-chaining, let **each confirmed provider auto-queue a depth=0
crawl on itself** back to the Commands tab (`queue_provider_seeds()`), with a dedupe
guard (never re-queue a handle already used as a crawl target — prevents loops).
The graph walks itself toward density. Base rate learned: even a fitness account's
followers yield ~1 real "provider" per 20 enriched — providers are rare in ANY graph;
that's the demographic base rate, not a filter bug.

## Pitfalls logged this session

- Verify the handle spelling from the screenshot's own page anchors — `tanzim_ozer`
  (underscore) 404'd; the real handle `tanzim.ozer` (dot) was visible in the DIAG
  `sample=['/tanzim.ozer/']`. When a crawl returns 0 with a "no followers link" DIAG,
  read the anchor sample before blaming the account.
- A Claude relay may CLAIM success ("4,375 handles written to Jul 03") that didn't
  actually land — verify the tab's real row count via the token before trusting a
  relay's status message.
