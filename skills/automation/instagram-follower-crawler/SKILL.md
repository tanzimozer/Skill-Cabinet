---
name: instagram-follower-crawler
description: Build and operate a dumb Instagram follower-graph scroller triggered from a WhatsApp/group chat. Use when Tanzim wants to collect Instagram handles by scrolling follower lists, chain outward through the follower graph, or wire a chat-command trigger to a local crawler on his Mac. Covers the crawler script, the WhatsApp listener, GitHub deploy, and the trust/IP constraints.
---

# Instagram Follower Crawler (Instagrammer-lite)

A deliberately dumb two-file engine: a follower-list scroller + a chat trigger.
No intelligence, no filtering in-loop. One job: **scroll a followers list, grab
handles, chain outward, dump to CSV.** Filtering/enrichment/following are
separate later stages, never baked into this.

## SCOPE DISCIPLINE — the objective is the DUMB version; resist building the moat unasked (learned 2026-07-04)
The whole session arc was a warning: I built enrichment → scoring → three-way
classify → provider-gated self-propagating chaining — an elaborate "moat engine" —
and Tanzim then reset the objective to the bare minimum: **"simply what i want is,
i drop you screenshot, i get the list of user's followers on a google sheet.
that's all."** Everything sophisticated got gated off or stripped.
- **When he says the engine name is "instagrammer-LITE" / "dumb machine," believe it.**
  The value he wants first is the raw follower list on a sheet, formatted. NOT
  scored, NOT enriched, NOT filtered, NOT chained.
- **Don't pre-build downstream stages he hasn't asked to run.** Enrichment/scoring
  are real and documented below, but they are OPT-IN later stages — offer them,
  don't ship them into the default flow.
- **When he changes the objective, strip HARD and immediately.** He gated band-prune
  off (`PRUNE_BY_BAND=False`) the moment it made a crawl slow — a feature I'd just
  built. Read the room: a filter that costs a per-handle profile hit (4–9s each) is
  too heavy for "just give me the followers." Ship fast-and-dumb first; add
  intelligence only when he explicitly asks.
- **He rejects both "hand-pick a good seed" AND over-engineered auto-magic** as the
  answer to yield — he wants dynamic but SIMPLE. Match that instinct.

## BAND-FILTER IS SLOW — per-handle count = a profile hit each (gated off 2026-07-04)
Filtering a fresh crawl by follower band (e.g. 500–3,500) requires the follower
COUNT of every caught handle, and Instagram only gives counts one profile at a
time via `web_profile_info` — ~4–9s human-paced each. On a 200–500 handle catch
that's 15–40+ min AND blows past Meta's ~30–50 profile-call checkpoint, walling the
session. So band-pruning a raw catch is impractical at volume. Current state:
gated behind `PRUNE_BY_BAND` in `listener_sheet.py`, **default OFF** — crawl dumps
ALL followers to the tab, hyperlinked+formatted, fast. Turn it on only when the
count pass is made cheap (batched, or a lighter endpoint). Don't promise a live
band filter on a big catch without flagging the time+trust cost first.

## Core constraints (these shape everything)
1. **Must run on Tanzim's Mac, not a server.** Instagram blocks datacenter IPs on
   sight; it trusts his home connection + logged-in cookies. Never try to run the
   crawl remotely — the agent can *trigger* it but the crawl executes on the Mac.
2. **Instagram bans aggression.** Randomised pauses + cool-downs between accounts
   are built in. When Meta throttles (past a few thousand), the escape hatch is
   residential proxies + a small rotation of logged-in accounts — bolts on without
   touching the core script.
3. **Seed = the follower graph, NOT hashtags.** Hashtag pages are shadowbanned,
   throttled, full of dead accounts. Point the crawler at a *person* (Tanzim's own
   ~2,800 warm followers via `tanzim_ozer`, or a bigger fitness account with the
   target audience).

## SEED QUALITY DRIVES YIELD — a personal graph is PEOPLE, not PROVIDERS (learned 2026-07-04)
Provider yield off enrichment is roughly **1-in-20** for the wrong seed and that's
the SEED's fault, not the filter's. Two seeds proved it the same session:
- `hammerthehorrible` (not a fitness account) → 1 provider / 20.
- **Tanzim's OWN follower graph** (`tanzim.ozer`) → also 1 provider / 20. His
  followers are friends and personal accounts; ~14 of 20 scored 0 (private/no-signal).
The lesson: a personal Instagram's followers are *people*, not *providers*. Don't
assume "warm graph = good yield" — warmth ≠ fitness density. When yield is low, look
at the SEED before touching the classifier. The dynamic fix Tanzim chose is
provider-gated chaining (see references/enrichment-stage.md), NOT hand-picking seeds
(he rejected "just run a Seattle gym" as "not dynamic enough").

## COPY-PASTE DELIVERY RULE (locked 2026-07-13)
When giving Tanzim commands or code blocks to run, **send each copyable item as its own isolated block** — never mix a command and surrounding explanation in the same paragraph or message. He copies directly from chat and does not want to filter noise.

- One command = one block
- If sending multiple commands, each gets its own separate block/message
- If the WhatsApp bridge is down, use inline code blocks with clear blank lines between — never embed a command inside prose on the same line
- This applies to terminal commands, code snippets, JSON, credentials — anything meant to be copied verbatim

## TURRO SETUP — 5-step sequence (state as of 2026-07-12, ALL COMPLETE)
1. Master account validation — tanzim_ozer cookie live ✓
2. Burner pool — 10 live accounts ✓
3. Provision master Google Sheet ✓ — Sheet ID `1ZmyV2nBq5uoql7WD9hxr7q6nM1ofT8nyJ8Q1C45Z4pc`, tabs: Crawl Output, Cookie Rotation, TANZIM, Cred
4. WhatsApp bridge re-auth ✓
5. Mac listener live at `http://10.217.135.195:5055` (`~/Desktop/Friday/TURRO/listener.py`), secret `turro-secret-2026` ✓

**TANZIM tab schema (confirmed live):** 1,501 rows (1 header + 1,500 data). Cols: FOLLOWERS | FOLLOWING | NON-FOLLOWERS. Col C = unfollow target list, ~1,080 active handles, skip `__deleted__` prefix. Used by the Unfollow Engine (see `references/turro-unfollow-engine.md`).

Cookie pool lives in `Team_Credentials` sheet `IG Creds` tab — authoritative source, not local files.

## COOKIE SOURCE — `IG Creds` tab is authoritative, local files go stale
`Team_Credentials` sheet (`1NVaI-jXqfS1z6aMLvNlwJCZoSzVMzP-17to24kKMcDA`), `IG Creds` tab, col D = live cookie JSON. Towsif refreshes here. Don't read from `~/.hermes/instagrammer/crawl_cookies/` — those copies age out. Parse col D: `json.loads(row[3])` gives the full cookie array.

## IP FINGERPRINT BLOCK — "too many redirects" ≠ dead cookie
Cookie valid in Brave on the Mac will `TooManyRedirects (30 redirects)` from a server IP. That's IG's login-wall redirect loop — non-home IP rejected, not the credential. Signs: `accounts/current_user/` → 30 redirects, no 200; same cookie in Brave → 200. Fix: ALL scroll execution must run Mac-side (home IP + real browser fingerprint). Friday triggers via sheet Commands row; Mac executes. Retrying with a different cookie won't help — the IP is the problem.

## HANDLE TYPO — read the DIAG anchors to self-correct (2026-07-04)
A crawl on `tanzim_ozer` (underscore) returned 0 with DIAG "no followers link" — but
the diagnostic's own `sample=[... '/tanzim.ozer/']` anchor list revealed the REAL
handle was `tanzim.ozer` (dot). When a crawl returns 0 on what should be a valid
account, scan the DIAG anchor sample for the correct handle spelling before assuming
private/broken. The self-reporting DIAG pays off here too.

## Architecture / flow
```
INPUT:  chat message  ->  crawl @targethandle depth=2
IN BETWEEN (all on the Mac):
  listener.py (always running, watches the chat)
    -> sees "crawl @handle" -> checks allow-listed sender -> fires
  crawler.py
    -> loads secrets/ig_cookies.json (live login)
    -> Playwright opens Chromium -> instagram.com/@target
    -> clicks Followers -> modal opens
    -> SCROLL loop: grab handles until no new ones load
    -> append to out/handles.csv
    -> CHAIN: each new handle becomes next target (until depth reached)
  listener.py replies into the chat when done
OUTPUT:
  A) out/handles.csv  (columns: handle, source, collected_at)
  B) chat reply: "Done, Boss. +740 new handles this run."
```
The only part that "thinks" is the scroll-grab loop. Everything else is plumbing.

## Agent-triggered = user-triggered
The listener watches the chat and doesn't care who typed the keyword. Tanzim
typing `crawl @handle` and Friday posting it into the same chat are **identical**
to the Mac. So once the listener runs, "trigger" is the agent's to pull.

## Expected outcome
A growing, deduped **CSV of raw Instagram handles** — the feedstock. Not filtered,
not enriched, not followed. One `crawl @bigaccount depth=2` yields a few hundred
to a few thousand handles.

## Support files
- `references/turro-listener-setup.md` — TURRO Mac listener build reference (port, secret, start command, check-alive)
- `references/enrichment-stage.md` — enrichment pipeline detail
- `references/scraper-zero-catch-debugging.md` — zero-catch debugging decision tree
- `references/turro-unfollow-engine.md` — Unfollow Engine design: Playwright/Chrome profile approach, TANZIM tab schema (col C = non-followers, 1,080 active handles), 3s pulse, file structure, modal handling pitfalls, Claude Code handoff pattern, copy-paste delivery rule
- `scripts/probe_google_creds.py` — probe candidate Google credential files
- `scripts/fire_crawl.py` — write trigger row to Commands tab from Friday's env

## Files (in this skill's `files/`)
- `crawler.py` — the dumb follower scroller (Playwright + real cookies).
- `listener.py` — WhatsApp keyword watcher that fires the crawler.
- `SETUP_FOR_CLAUDE.md` — self-contained runbook for Claude-on-the-Mac to deploy.
- `ig_cookies.template.json` — required cookie shape (sessionid, ds_user_id, csrftoken matter).
- `listener_config.template.json` — bridge_url/token, chat_id, sender allow-list.

## Deploy workflow
1. Build/refresh the two scripts + templates.
2. Push to a **private** GitHub repo (Tanzim's stored git creds under
   `~/.git-credentials`, user `tanzimozer`). Create via GitHub API
   `POST /user/repos` with `"private":true`, then `git push`.
3. Gitignore `secrets/*` (except the template), `out/`, `logs/`, `venv/`,
   `listener_config.json`. Force-allow the template with `!secrets/*.template.json`.
4. Hand Tanzim / Claude-on-Mac the one-line clone. Secrets get pasted locally.

## What the agent CANNOT do
- Reach the Mac directly (no listener running there yet = no hands on the machine).
- Run the crawl on its own IP (Meta blocks it).
- Fill the WhatsApp `bridge_url`/`bridge_token` — those come from the bridge the
  chat runs on; if unknown, test the crawler standalone and hold the listener.
- Reach the Mac directly to run the actual CRAWL (Meta blocks Friday's IP; the
  scroll must execute Mac-side with home IP + live cookies). Friday triggers; the
  Mac scrapes.

## TRIGGER FROM FRIDAY'S OWN ENVIRONMENT — the settled rule (locked 2026-07-04)
Tanzim's hard requirement: **"EVERYTHING HAS TO TRIGGER FROM HERE."** Do NOT relay
the trigger through Claude-on-the-Mac. Friday writes the `pending` row to the
Commands tab directly, from her own environment. Relaying through Claude when
Friday can do it herself is a workflow failure the user called out explicitly.

**Working credential (verified 2026-07-04):** `~/.hermes/google_token.json` is a
LIVE authorized-user token that opens the Bulldozer sheet directly. Also live:
`~/.hermes/instagrammer/mac/secrets/google_token.json`. DEAD ends: the
`friday_backup/google_token.json` refresh throws `deleted_client`, and
`GOOGLE_OAUTH_ACTIVE.json` is missing `refresh_token`. When a Google write appears
to fail, DON'T assume Friday "cannot write" and fall back to Claude — probe every
candidate credential file against the sheet KEY first. The runnable probe is
`scripts/probe_google_creds.py`; the direct-write trigger is
`scripts/fire_crawl.py`.

**Commands-tab schema is 8 columns, order matters:**
`id | command | target | depth | status | result | requested_at | done_at`.
Earlier blind `append_row(['crawl','handle','1','pending'])` (4 values) mangled the
column alignment — another reason the trigger "didn't work." Always write all 8:
`[uuid8, 'crawl', target, '1', 'pending', '', iso_now, '']`. Bind by KEY
`1Nuroehse6WIvruHpb1tiyc8ZayIxuWVzzk0sfnYsGi0`, never by name.

## Read the screenshot for the PRIVATE lock before firing
A crawl on a private account returns 0 handles — the followers modal won't open.
`zoiemastin` (private) and any locked account waste a run. Before firing, check the
profile screenshot for the "This account is private" state / absent stats. Flag it
and ask for a public seed rather than burning a crawl. NOTE: a *public* account
returning 0 (e.g. `emccoyy`, `ava.pappas` on 2026-07-04) is a CRAWLER bug —
stale Playwright selectors, resolved by the fixes in
`references/scraper-zero-catch-debugging.md`. Do NOT swap to another seed; the
self-reporting DIAG line in the sheet cell tells you the real cause without
needing eyes on the Mac browser.
**A PUBLIC account returning 0 is a SCRAPER bug — stop swapping seeds.** Three
public seeds returned zero on 2026-07-04 (`emccoyy`, `ava.pappas`, plus private
`zoiemastin`); the cause was stale Playwright selectors, not the seeds. After ONE
public zero, go to the code, not another screenshot. Full decision tree, the two
selector bugs (dead `role='link']` qualifier; stale followers-link selector), and
the self-reporting-DIAG pattern: `references/scraper-zero-catch-debugging.md`.

When a relayed command "didn't work," do NOT send another blind command. That
burned six turns here. Every diagnostic one-liner relayed to Claude-on-the-Mac
MUST print its own evidence and the user MUST paste it back before the next move:
- Make the probe self-reporting: `print('HEADER:', ...); ...; print('WROTE OK')`
  and wrap so a traceback surfaces rather than a silent no-op.
- One probe that reveals tabs + header + write-result at once beats three
  sequential guesses.
- "It didn't work" with no error text is not actionable — ask for the output,
  don't theorise. Confirm the sheet KEY (not the name — same-named copies are the
  classic trap) with `sh.url` early.
- Before assuming the Mac is broken, verify Friday's OWN side can even reach the
  resource (see dead-OAuth note above). The failure was mine, not the Mac's.

## Trigger reference
```
crawl @tanzim_ozer                        # depth=0 default: THIS account's followers only, clean stop
crawl @somebigfitnessaccount depth=2      # opt-in graph-walk: chain outward 2 hops
```

## DEPTH SEMANTICS — depth=0 is now the committed default (locked 2026-07-04)
- **depth=0** — crawl the target's followers, stop. One list. THE DEFAULT for a
  single "crawl @handle". Set as default in both `crawler.py` (`--depth default=0`)
  and `listener_sheet.py` (`int(r.get("depth") or 0)`), committed to the repo.
- **depth=1** — crawl the target's followers, THEN crawl each of those followers'
  followers too (one hop outward — the spidering). This is what made a single test
  run 8+ minutes and climb past 2,492 handles: not a hang, just chaining.
- **depth=2+** — another hop; grows exponentially.
- **Rule:** chaining is opt-in. A single-handle crawl must NOT chain by default —
  Tanzim called this out explicitly. If a crawl runs unexpectedly long, suspect
  chaining (check depth) before suspecting a stall.

## KILL-SWITCH GAP — stopping a running crawl (open issue, flagged 2026-07-04)
The listener only acts on `crawl` rows; it has **no kill command**. A crawl that's
already running is a live process on the Mac that NOTHING in the sheet reaches
mid-run. Writing a `kill` row does nothing — don't pretend it will. To stop a
running crawl right now, the ONLY path is Claude-on-the-Mac: `pkill -f crawler.py`.
- **Cost of pkill mid-run:** it can cut the process off BEFORE the dated-tab write
  step, so the catch is stranded in `out/handles.csv` and no "Jul 03" tab appears.
  (Happened 2026-07-04: a killed depth=1 ava.pappas run left 4,375 handles in the
  CSV with no tab.) After ANY pkill, verify the tab actually dropped; if not,
  recover the CSV into a tab (see below).
- **Worth building:** a `kill` command the listener honours (write a pending
  `kill` row → listener pkills the crawler AND flushes whatever's in the run CSV
  to a dated tab before exiting). Until then, killing needs Claude and risks a
  stranded catch. Tanzim asked for this; it's the next real improvement.

## Recover a stranded catch (CSV → dated tab)
If handles landed in `out/handles.csv` but no tab wrote (killed mid-run), push the
CSV into a fresh dated tab. Runs Mac-side (its OAuth writes the sheet):
```
python3 -c "import gspread, csv; from datetime import datetime; sh=gspread.oauth().open_by_key('1Nuroehse6WIvruHpb1tiyc8ZayIxuWVzzk0sfnYsGi0'); rows=list(csv.reader(open('out/handles.csv'))); t=datetime.now().strftime('%b %d'); ws=sh.add_worksheet(title=t, rows=len(rows)+5, cols=6); ws.update('A1', rows); ws.format('A1:C1', {'textFormat':{'bold':True},'horizontalAlignment':'CENTER'}); ws.freeze(rows=1); print('WROTE tab', t, len(rows)-1)"
```
Friday can also do this directly via her live token if the CSV is reachable, but
the CSV lives on the Mac — so this is one of the few genuinely Claude-side jobs.

## The gid trap — Commands tab is NOT where catches land
When Tanzim shares a sheet URL with `#gid=NNNN`, that gid points at a SPECIFIC
tab. On 2026-07-04 he linked `gid=1381046192` expecting the catch there — but that
gid is the **Commands** (trigger) tab. Catches never land in Commands; each crawl
spawns its OWN new dated tab. Check the gid against `w.id` for each worksheet
before assuming — don't write a catch into the Commands tab. Confirm which tab a
shared gid actually is (`[(w.title, w.id) for w in sh.worksheets()]`).

## VERIFIED END-TO-END 2026-07-04 (the loop works)
`@hammerthehorrible` depth=0 → 219 handles → "Jul 03" tab, bold/frozen, <1 min,
fired entirely from Friday's side (no Claude). Screenshot in → tab out. This is
the proof the whole pipeline works as designed; if a future run breaks, this is
the known-good baseline to diff against.

## Database schema (the actual product / moat)
The value isn't the handles — it's a clean, enriched, dispatch-ready provider
table. Filter in LAYERS, never destructively; every pass adds a column, drops
nothing. Rejected rows are tagged + parked (Rejected tab), never deleted, so raw
catch is re-cuttable against a new city/band without re-scraping. See
`files/SCHEMA.md` for the full 24-column spec. Key points:
- **Band: 150–3,500** (moved from 500–3,500 on 2026-07-03). Floor is a rate-limit
  valve, NOT a quality lever — judge quality on `fitness_score`, never size.
  ±10% edge → tagged `maybe`, not rejected.
- **fitness_score (0–100):** bio/name keyword hits + external link + IG category
  + engagement proxy. Cheap, sortable, transparent. Never eyeball the raw list —
  only ever the score-ranked, city-flagged view. Top slice runs ~45–60% signal.
- **Seattle flag = filter IN, never OUT.** yes/maybe/blank. Blank stays in pool,
  unranked, never dropped. Evidence: bio (Seattle, 206, Ballard, Capitol Hill,
  SLU, Fremont…), tagged locations, tz/lang. Built as a city dictionary
  (`files/cities.json`) — swap one config line to run Austin, etc. Test Seattle;
  if top-slice signal ≥ 30%, flood to more cities.
- **Time-series is the moat:** first_seen / last_seen / seen_count per handle. A
  snapshot is data; the change (who's growing, who added a coaching link) is the
  asset. Store wide now — no second free profile visit.
- **Enrich only survivors, not everything** — crawl handles first, filter cheap,
  then visit profiles. Enrichment is the slow, trust-burning step.

## Analyst data harvested per profile visit (store wide)
followers/following/posts, follow_ratio, bio, external_link + parsed domain,
ig_category, account_type, verified, is_private, last_post_date, engagement proxy
(avg likes last 3 posts ÷ followers), profile pic, full name, source/graph
provenance.

## ENRICHMENT (Stage 4) — profile extraction NOW WIRED (2026-07-04)
`enrich.py` no longer stubs extraction. Built and committed:
- **Extraction via JSON endpoint, NOT DOM scraping.** Hit
  `https://www.instagram.com/api/v1/users/web_profile_info/?username=<h>` with the
  live session (Playwright `ctx.request.get`) and header `x-ig-app-id: 936619743392459`
  + a `referer` of the profile URL. Returns clean JSON: `data.user.edge_followed_by.count`
  (followers), `edge_follow.count` (following), `edge_owner_to_timeline_media.count`
  (posts) + `.edges` (recent posts for eng proxy + last_post date), `biography`,
  `external_url`, `category_name`, `is_verified`, `is_private`, `is_business_account`.
  Far more robust than scrolling DOM — no stale-selector fragility like the crawler had.
- **eng_proxy** = avg likes over recent ≤12 posts ÷ followers, from the edges.
- **Fire from Friday's side** via a new `enrich` listener command:
  row `command=enrich | target=<TabName> | depth=<batch_limit> | status=pending`.
  Here `target` = the dated tab to read (e.g. "Jul 03"), `depth` = batch size (default 20).
  Listener runs `enrich.py --tab <Tab> --limit <N>`, writes **Providers** + **Rejected** + **Review** tabs.
- **Small batches (default 20), human-paced 4–9s** between profiles — protects cookie trust.
- **Scoring/city/band logic was already complete + offline-testable** — verify it with a
  synthetic profile dict through `score_row()` BEFORE any live run (a Seattle coach test
  profile should score 100 / seattle=yes / band=yes). Do this to prove logic independent
  of the network call.
- **CLASSIFY GATES ON FITNESS SCORE FIRST — band is a rate valve, not a promoter (fixed 2026-07-04).**
  The first version sorted on band alone and got it exactly backwards: unreadable private
  score-0 accounts became "Providers" (in-band) while real fitness businesses got rejected
  (out-of-band). Correct three-way `classify(p)`: `provider` = fitness_score≥24 AND (in-band
  OR seattle); `review` = error OR score==0 (private/no-signal, NEVER auto-promoted);
  `rejected` = has signal but fails band+city. Three tabs out: Providers / Rejected / Review.
  Verify `classify()` offline against the observed batch before re-firing.
Full build detail, the JSON field map, and the enrich-command wiring:
`references/enrichment-stage.md`.

## PROVIDER-GATED CHAINING — the self-propagating engine (built 2026-07-04)
Every confirmed provider auto-queues a depth=0 crawl on itself back to Commands, so
the Providers tab fills itself: enrich finds a provider → queues a crawl on them →
their (fitness-dense) followers get caught → enrich them → new providers seed the
next round. `queue_provider_seeds()` in enrich.py, called after write unless
`--no-chain`, with a dedupe guard (never re-queue a handle ever seeded) that breaks
the loop. This is the answer to "how does yield improve" — NOT hand-picking seeds
(Tanzim rejected that) and NOT depth chaining (walks everyone blindly). Deliberately
one-hop/human-paced, not runaway — the new tab still needs a Friday-fired `enrich`.
Full detail: `references/enrichment-stage.md`.

## CI/CD — the "deploy from just a phone" mechanism
The repo IS the control surface. Tanzim carries only his phone; compute lives on
the always-on Mac (VM fine). Flow: he WhatsApps a change → Friday commits → GitHub
Action (`files/ci.yml`) gates it → `watcher.py` on the Mac sees the green SHA,
`git pull`s, restarts the listener via launchd. He never touches the machine.
- `files/watcher.py` — polls repo, deploys only CI-green SHAs, launchd kickstart.
- **Token scope gotcha:** the stored PAT lacks `workflow` scope, so `ci.yml`
  can't be pushed into `.github/workflows/` over the API. Park it as
  `ci_pending/ci.yml` and activate via web UI or a Mac token with `workflow`
  scope. See `ci_pending/README.md` in the repo.

## Sheet formatting (locked)
Header row: bold, centred (h+v), frozen. Data cells: left-aligned, wrap ON, top
vertical align. Numeric columns as numbers. fitness_score conditional colour
scale. seattle=yes row highlight.

## OPERATING DOCTRINE (locked 2026-07-03 — the settled spec)

**Target:** 250–500 handles/day, zero-detection priority (Meta is dynamic — assume no safe margin).

**What Meta tracks:** the scroller (you), not the scrolled. Risk = request volume + velocity from one session. Reads safer than follows; follows are the real ban trigger.

**Safe unit:** 1 account → 1 light followers-skim (~150 handles) → rest. Never two accounts on the same handle (wasted, double exposure). Spread *handles* across the pool, not accounts across one handle.

**Chosen model — cold rotation:**
- Each account works once per rotation, then rests days. Looks dormant, no rhythm to detect.
- ~3 active accounts/day × 150 = ~450/day.
- **Pool of 15** → each account works 1-in-5 days.
- Colder on demand: **30** → 1-in-10. Lever = add accounts, not activity.

**Why cold beats light-daily:** same yield, but each account touches Meta once every 5+ days instead of daily — no recurring pattern. Accounts are free to create (one-time task), so spend accounts to buy coldness.

**Hub-and-spoke dispatcher:** hub parcels the handle queue in small batches; spokes (accounts) each do one light skim then rest. Health-check quarantines dead/challenged sessions and reroutes — system never fully stops.

**Default:** pool 15–20, one 150-handle skim per account per rotation, 4–9 day rest. Auth via session cookies (not passwords). Escape hatch at scale: residential proxies, bolt-on.

## Trigger via Google Sheet (the bridge — no WhatsApp token needed)
The clean way to close the "trigger from chat" loop WITHOUT a WhatsApp bridge
token: the Mac already has working Google OAuth (it writes the handles), so make
the **Sheet itself the command channel**.
- `listener_sheet.py` polls a 'Commands' tab on the Bulldozer sheet every 10s.
  Columns: id | command | target | depth | status | result | requested_at | done_at.
  status flow pending→running→done|error; only acts on `pending` rows.
- Friday writes a `pending` row DIRECTLY from her own environment (using the live
  `~/.hermes/google_token.json`, via `scripts/fire_crawl.py`) → Mac executes →
  writes status back → Friday reads (`fire_crawl.py --status`) and reports.
- This beats chasing a bridge token when Sheets OAuth is already live. General
  lesson: if two systems already share one authorised channel, route control
  through it rather than standing up a second integration.
- **The live sheet KEY is `1Nuroehse6WIvruHpb1tiyc8ZayIxuWVzzk0sfnYsGi0`**
  ("Bulldozer — Handles"). Always bind by KEY, never by name — `gspread.open()` on
  the name can hit a different same-named copy, which was a suspected cause of
  "the write didn't land."  Commands-tab row format:
  `command=crawl | target=<public_handle> | depth=0 | status=pending` (depth=0 =
  followers-only, the default; set depth>=1 only to chain outward).

## Dated per-crawl output tabs
Tanzim's locked I/O spec: always the SAME spreadsheet, but EVERY crawl spawns a
NEW tab named the crawl date in `datetime.strftime("%b %d")` → "Jul 03". Same-day
repeat → "Jul 03 (2)" (increment suffix; check existing worksheet titles first,
never overwrite). Header row: bold, centred (h+v), frozen (`ws.freeze(rows=1)`).
- crawler.py needs a `--run-out <csv>` flag emitting THIS run's found handles
  (pre global-dedup) so the dated tab shows the full haul even when handles are
  already in the master out/handles.csv. Global dedup stays for the master file;
  the per-run file is the tab's source.

### The CRAWL CAP is a self-imposed `--max`, NOT an Instagram limit (2026-07-04)
Per-run handle count is capped by the `--max` value in the listener's crawl call
(`crawler.py <target> --depth N --max 500 ...`), started at 200, raised to 500 on
request. It's a one-number change in `run_crawl()`. When Tanzim asks "why capped at
N?" the honest answer is "I set it, to keep runs short / protect trust" — not that
IG forbids more. The REAL ceiling on a big account isn't `--max`, it's any per-handle
profile pass (band filter) hitting Meta's checkpoint. Raise `--max` freely; only
flag the profile-hit ceiling.

### Simplified output tab schema (the LITE default, 2026-07-04)
When band-prune is off (the default), the dated tab is 3 columns:
`Handle | Followers | Crawled_at`. Handle = live `=HYPERLINK(...)` (USER_ENTERED),
Followers left blank (no count pass in fast mode), Crawled_at = `%Y-%m-%d`.
Formatting locked: every cell centre + middle + wrap; header bold; header frozen.

## Account pool + dispatcher (distributed load = ban avoidance)
- **1 account per handle, not many** — two accounts on the same followers list is
  wasted, double exposure. Rotation spreads *handles across the pool*, not
  accounts across one handle.
- **Pool = 10 crawl accounts** (Tanzim owns 10; he floated 20–25, real count is
  10) + **1 dedicated follow account** kept clean from crawl traffic.
- **Dispatcher (hub-and-spoke):** parcels the handle queue out in small batches —
  each account scrolls only a few handles/day, human pace, then rests. Little per
  account = under the radar; pool gives scale.
- **20 follows/day cap** per account on the follow side (vs 200 on one).
- **Health-based rotation:** health-check per run detects dead/challenged
  sessions, quarantines + reroutes to other spokes, alerts Tanzim which account
  needs a cookie refresh. System never fully stops. (Tested: 7/10 dead, 3
  survivors finished the run.)
- **Auth via session cookies, not passwords** — avoids login checkpoints/2FA.
  Cookies live in the Instagrammer Sheet 'IG Creds' tab; Towsif refreshes via
  60s Cookie-Editor when challenged.
- Escape hatch at scale: residential proxies bolt on without touching core.

## Hyperlink handles in dated tabs (locked 2026-07-04)
Tanzim wants every extracted handle clickable → its IG profile. In `write_run_tab`,
write column A as `=HYPERLINK("https://www.instagram.com/<handle>/","<handle>")` and
push with `value_input_option="USER_ENTERED"` (else the formula lands as literal
text, not a link). To RETROFIT an existing plain-text tab, rewrite column A in place
with the same formula + USER_ENTERED — Friday can do this directly via her live token
(the tab is in the sheet, no Mac needed). Tabs written before this change stay plain
until retrofitted.

## TWO-WRITER GIT DIVERGENCE — Friday AND Claude both push to Bulldozer (2026-07-04)
Both Friday (her env) and Claude (the Mac) commit to the same repo, often the SAME
file (`listener_sheet.py`, `crawler.py`). A Friday push gets rejected with
"Updates were rejected / need to pull before pushing" when Claude pushed first.
- Resolve with `git pull --no-rebase --no-edit` (the repo has no default reconcile
  set, so a bare `git pull` errors "Need to specify how to reconcile divergent
  branches" — always pass `--no-rebase`). It auto-merges cleanly when the two sides
  touched different regions (e.g. Friday added hyperlinks, Claude added the
  kill-switch — merged with zero conflicts).
- **After ANY auto-merge, RE-READ the merged file** to confirm YOUR change survived
  and you can see the OTHER side's addition. Don't trust "Merge made by ort" blindly
  — verify both edits are present before moving on.

## Reference repo
Live repo is **github.com/tanzimozer/Bulldozer** (private, "dumb machine that
ploughs the follower graph"), cloned at `~/Desktop/Bulldozer` on the Mac. Renamed
from the earlier `instagrammer-lite`.
**Patch-clobber gotcha:** the Mac's local `crawler.py` carries two hand-patches —
the null-`sameSite` fix (sessionid/csrftoken have `sameSite: null` in the cookies;
without the fix cookies won't load and the crawler dies on launch) and a login
check. A Friday-side `git pull` reverted them twice. Fix committed to the repo so
pulls stop clobbering; if a crawl dies on launch, re-check with
`grep -n "sameSite\|login" crawler.py` and `git stash pop` / re-apply + push.
The older 7-stage engine is github.com/tanzimozer/Instagrammer (crawl -> filter ->
store -> enrich -> output -> follow -> schedule). This lite version deliberately
strips to crawl-only.
