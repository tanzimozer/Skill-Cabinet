# Debugging a "0 handles" crawl — selector drift is the usual culprit

When the trigger loop is healthy (row goes pending→running→done, `DONE. 0 new
handles` written back) but the catch is **zero**, the bug is almost always in the
Playwright scraper's **CSS selectors going stale** — Instagram reshuffles its DOM
frequently. It is NOT the seed, unless the seed is private.

## The decision tree (learned 2026-07-04)
1. **One zero on a private account** → expected. Followers modal won't open. Ask
   for a public seed. Read the screenshot for the private lock BEFORE firing.
2. **Zero on a PUBLIC account** → scraper bug. Do NOT keep swapping seeds. Two
   more public seeds returning zero (`emccoyy`, `ava.pappas`) only wasted turns.
   Go straight to the code.
3. **Zero across private + public + big-public-verified** → conclusive: the
   scraper is broken, seed is irrelevant. Pull the code and audit selectors.

## The two selector bugs found this session
- **`a[href^='/'][role='link']`** — the `[role='link']` qualifier matched ZERO
  elements. Instagram's follower anchors are plain `<a>` tags and don't carry an
  explicit `role='link'` (it's redundant on an anchor, so IG omits it). Fix: match
  on `href` only — `a[href^='/']` — then filter reserved paths in Python.
- **`a[href$='/followers/']`** as the sole way to open the modal — IG changed the
  profile DOM so this matched nothing to click; modal never opened. Fix: try a
  LIST of selectors in order and click the first that exists:
  `a[href='/{target}/followers/']`, `a[href$='/followers/']`,
  `a:has-text('followers')`, `li:has-text('followers') a`.

## The meta-lesson: make failures self-reporting, in the sheet cell
The original crawler wrote only `DONE. 0 new handles. Found 0 total` — which hides
WHY. Every zero after that was a blind guess. Fix pattern:
- On each failure branch in `scrape_followers`, log a `DIAG:` line with the page
  STATE, not just "failed": `url`, `anchors=<count>`, `login_wall=<bool>`, and a
  `sample` of the first ~8 hrefs seen. Also log which selector opened the modal.
- Surface the DIAG into the sheet result cell so the ops loop shows it without Mac
  access: in `listener_sheet.run_crawl`, when no tab was produced,
  `diag = next((l for l in reversed(out) if "DIAG" in l), "")` and append it to
  the summary. Now the cell reads e.g.
  `DONE. 0 total | DIAG: no followers link for @ava.pappas | url=... | anchors=... | login_wall=False | sample=[...]`.
- This is the anti-blind-fire rule applied to Mac-side code: if the agent can't
  see the browser, the code must narrate its own failure back through the one
  channel the agent CAN see (the sheet).

## Why the agent can't just fix-and-verify locally
The scrape must run Mac-side (Meta blocks server IPs). So the loop is: patch
crawler.py here → commit+push → Claude-on-Mac `git pull` + restart listener →
Friday re-fires the SAME seed from her env → read the DIAG in the sheet cell. The
restart one-liner:
`cd ~/Desktop/Bulldozer && git pull && pkill -f listener_sheet.py; sleep 1; source venv/bin/activate && nohup python listener_sheet.py > logs/listener_sheet.log 2>&1 &`
Only the browser-running step needs Claude; everything else is Friday's.

## RESOLUTION (confirmed 2026-07-04)
The multi-selector fix WORKED. The `a:has-text('followers')` fallback opened the
modal on `ava.pappas` and the scraper pulled **2,492 handles and climbing** — the
zero-catch bug is dead. Both selector fixes are committed to the repo.

## depth=1 CHAINS — the gotcha that made a single test run forever
After the fix, the `ava.pappas` crawl ran 8+ minutes and kept going. NOT stuck —
`depth=1` means it crawled ava.pappas THEN started walking her followers'
followers (chaining outward), which is why the count kept climbing past one list.
That's correct behaviour for depth=1, but WRONG for a single-handle test.
- **Rule: a single "crawl @handle" should run depth=0** — one account's followers,
  no chaining, clean stop. Reserve depth≥1 for deliberate graph-walks.
- If a crawl runs unexpectedly long, suspect chaining before suspecting a hang —
  check depth. A ~200-cap single list finishes in 2–3 min; longer = it's chaining
  or scroll-looping. The live `logs/crawler.log` (tail on Mac) shows the handle
  count climbing per-account, which distinguishes chaining from a true stall.
