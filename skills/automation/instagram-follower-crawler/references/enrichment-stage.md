# Enrichment Stage (Stage 4) — build notes

Built and committed 2026-07-04. Turns the raw handle list (a dated tab) into the
scored, dispatch-ready provider database. This is where the actual product value is.

## Why the JSON endpoint over DOM scraping
The crawler's bug this session was stale Playwright selectors (see
`scraper-zero-catch-debugging.md`). Enrichment deliberately AVOIDS that fragility by
hitting Instagram's internal JSON API instead of parsing rendered HTML:

    GET https://www.instagram.com/api/v1/users/web_profile_info/?username=<handle>

Headers required (the session cookies alone aren't enough — IG returns 403/empty
without the app id):
    x-ig-app-id: 936619743392459        # standard IG web app id
    x-requested-with: XMLHttpRequest
    referer: https://www.instagram.com/<handle>/
    accept: application/json

Called via Playwright's request context so it rides the same authenticated session:
    ctx = browser.new_context(user_agent=..., )
    ctx.add_cookies(cookies)
    resp = ctx.request.get(URL, headers={...}, timeout=20000)
    data = resp.json()

## JSON field map (data.user.*)
- edge_followed_by.count        → followers
- edge_follow.count             → following
- edge_owner_to_timeline_media.count   → posts
- edge_owner_to_timeline_media.edges   → recent posts:
    node.edge_liked_by.count (or edge_media_preview_like.count) → likes (eng proxy)
    node.taken_at_timestamp → last_post_date (first edge = most recent)
- biography                     → bio
- external_url                  → external_link
- category_name                 → ig_category
- is_verified / is_private      → verified / is_private
- is_business_account / is_professional_account → account_type (business/creator/personal)

eng_proxy = avg(likes over first ≤12 edges) / followers, rounded 4dp.
Missing `data.user` in the payload = the profile couldn't be read (private,
rate-limited, or gone) → tag row status with the error, don't crash the batch.

## Scoring (was already complete — verify offline first)
`score_row(p, city, lo, hi, source)` runs the three layers, all pure/offline:
- fitness_score(0–100): bio+name keyword hits (×12, cap 60) + external link (+15)
  + fitness-y ig_category (+15) + eng_proxy>0.03 (+10).
- city_flag: cities.json strong/weak lists → yes/maybe/blank. Seattle = filter IN.
- band(150–3500): yes / maybe (±10% edge) / no.
BEFORE any live run, push a synthetic Seattle-coach dict through score_row and assert
score>0, seattle=='yes', band=='yes'. Proves the logic independent of the network.

## Classification — GATE ON FITNESS FIRST, band is a rate valve not a filter (fixed 2026-07-04)
**The bug that shipped in the first version:** the split was `(rejected if in_band=='no'
else providers)` — sorting on BAND ALONE. Result on the first live 20: 15 "Providers"
were all `fitness_score=0, is_private=TRUE` (unreadable private randoms that happened to
be in-band), while the real fitness businesses (`atlasstrengthco` score 39, `_fitsociety`
24, `6.for.6` 27) got REJECTED for being out-of-band. Exactly backwards.

**Correct rule — a three-way `classify(p)` gate:**
- `provider` ⇐ fitness_score ≥ FITNESS_MIN (=24, i.e. ≥2 keyword hits) AND (in-band OR seattle)
- `review`   ⇐ error (unreadable) OR fitness_score == 0 (private/no-signal). NEVER auto-promote these.
- `rejected` ⇐ has fitness signal but fails band-and-city (e.g. real fitness biz, wrong size)

Key principles this encodes:
- **Score gates, band informs.** A score-0 row is never a provider no matter its follower
  count. Band alone must never promote.
- **Private accounts return no bio/link/posts → score 0 → Review**, not Provider. They're
  unreadable, not qualified.
- **Seattle filters IN, never OUT** — an out-of-band Seattle fitness acct still qualifies.
- Write THREE tabs: Providers / Rejected / **Review**. `process()` returns 3 lists;
  `write_results(sh, providers, rejected, review)` upserts all three.
- Verify `classify()` offline against the observed 20 before re-firing (private+score0→review,
  Atlas/FitSociety→rejected, in-band-fit→provider). Cheap, catches the sort direction instantly.

## Firing it from Friday's side (the enrich command)
Added an `enrich` handler to `listener_sheet.py` alongside crawl/kill. Row schema
reuses the 8-col Commands format, repurposing two fields:
    command=enrich | target=<TabName> | depth=<batch_limit> | status=pending
- target  = the dated tab to READ handles from (e.g. "Jul 03"), NOT a handle.
- depth   = batch size / limit (default 20).
Listener calls `enrich.py --tab <Tab> --limit <N>`, which reads the tab (unwrapping
any =HYPERLINK formula to recover the bare handle via regex on instagram.com/<h>),
enriches, and writes/overwrites the **Providers** and **Rejected** tabs (header
bold+centred+frozen). run_enrich strips the leading log timestamp for a clean cell.

## Provider-gated chaining — the self-propagating seed engine (built 2026-07-04)
Tanzim rejected static seed-picking ("not dynamic enough") and rejected manually
naming Seattle fitness accounts too. The dynamic answer: **every CONFIRMED provider
becomes the next crawl seed.** Fitness people follow fitness people, so a provider's
follower graph is a far richer vein than a random or personal one. The graph walks
itself toward fitness density and compounds.

`queue_provider_seeds(sh, providers)` in enrich.py, called from `__main__` after the
write (unless `--no-chain`):
- For each confirmed provider, append a `pending` depth=0 `crawl` row to Commands.
- **Dedupe guard (the loop-breaker):** build a set of every handle that has EVER been
  a crawl `target` in Commands; skip any provider already seeded, and skip in-batch
  dups. Without this it re-crawls the same accounts forever.
- Test the guard offline with a fake sh/ws before pushing (already-seeded → skip,
  in-batch dup → skip, genuinely new → queue exactly one row, command=='crawl').

**This is provider-gated chaining, NOT depth chaining.** Depth (crawler `depth=1+`)
walks EVERYONE's followers blindly and explodes. Provider-gating only follows accounts
that already PASSED the filter — targeted, not exponential. Keep crawler depth=0; let
the provider gate decide who gets chained.

**Deliberately one-hop / human-paced, not runaway.** The loop is self-feeding but NOT
fully closed: a queued provider crawl produces a new dated tab, but that tab still needs
an `enrich` command (Friday fires it from here) to process. This is intentional — keeps a
hand on the throttle so it can't crawl 200 accounts overnight and torch cookie trust. The
cold-rotation budget (≈150 handles per account per rotation) means full-auto is unsafe
anyway. Full closed-loop later = a paced scheduler job, not a code change.

## Trust protection
- Default --limit 20 (small first batch).
- human_pause(4, 9) between every profile — human cadence, protects the cookie.
- headless launch is fine here (JSON call, not a visible scroll).

## Files
- enrich.py — full extraction + scoring + Providers/Rejected write (SHEET_KEY bound).
- listener_sheet.py — enrich command wired into the poll loop.
Both committed to github.com/tanzimozer/Bulldozer; Mac must `git pull` + restart the
listener before the first `enrich` row will fire.
