# TURRO — screenshot-driven scrape + paced follow/unfollow engine (Jul 2026)

`github.com/tanzimozer/Turro` (private). Built by consolidating `ig-1-protocol`
+ `Bulldozer` into one repo (histories preserved — see
`github-repository-management/references/repo-consolidation-with-history.md`),
then retiring ig-1-protocol as redundant. The live engine is Bulldozer's code.
Full spec lives in the repo at `SPEC.md`; this is the durable design summary.

## The one job
Grow a target account's following via scraped graph data + paced, human-like
follow/unfollow. Three functions, all screenshot/sheet-driven:
1. **Scraper** — drop a handle (as a screenshot in chat) → open that account →
   scrape FULL followers + following → one combined, deduped master table.
2. **Follower Engine** — read `pending` rows from master → visit each → follow.
3. **Unfollower Engine** — follow-back check; drop non-reciprocators.

## Architecture decision — READ/WRITE ACCOUNT SPLIT (Tanzim's refinement)
The anti-detection core. Separate reading from writing across different accounts:
- **Scraping (read) = 10 burner accounts, rotating pool.** Bulk reads trigger
  read-rate flags — spread across 10 so each looks like a casual browser. Burners
  are disposable; if one burns, nothing of value is lost.
- **Follow/unfollow (write) = 1 master account only.** Only the master builds the
  real social graph. It never bulk-reads → minimal surface area, stays clean. If
  a burner is flagged, the asset that matters is untouched.
- This is the clean resolution of the tension the older Instagrammer engine
  wrestled with (pool crawl, single follow). Generalise it: **reads pool, writes
  don't.** Only the acting identity can follow on your behalf, so rotating write
  accounts buys nothing and adds cluster-detection risk.
- **Pitfall:** don't let one handle sit in BOTH pools. Tanzim's personal handle
  (`tanzim_ozer`) was wired as both a burner and the master — reads and writes
  must never share an account or the split is defeated. Pull it from the burner
  pool, keep it master-only, add a fresh burner in its place.
- Burners still need believable cookies + light warm-up or IG spots them as a
  cluster and burns them fast. Disposable ≠ zero-maintenance.

## Rate governor (locked spec)
No "max without flagging" — only safe throughput via human mimicry.
- **Daily ceiling: 200 actions/day** (master).
- **Activity windows: 11am–1pm and 5pm–7pm Pacific** (Tanzim's chosen Seattle
  peak-active windows; he explicitly rejected quiet-hours — wants to hit when
  people are online). 200 across 4h ≈ one action / 72s + jitter.
- **Randomised pacing** (30–90s jitter, not fixed intervals — robotic timing is
  the #1 tell).
- **Warm-up curve keyed to account age** — fresh master opens ~20/day, ramps over
  weeks. MANDATORY for a cold master; 200/day out of the gate on a fresh account
  is a burn.
- **One action type per session** — never follow and unfollow together.
- **Completion guarantee within the cap:** the full queue clears by end of day,
  but only up to 200. Overflow (e.g. a 500-handle scrape) rolls to tomorrow,
  **FIFO** (oldest first, no queue-jumping). A queue > one day's cap simply takes
  multiple days; the guarantee is per-day-within-cap.

## Scraper rules
- **Full list every time, no cap** (Tanzim's call — scrape the target's entire
  followers + following however big).
- **Combined into ONE table, dedupe on handle.** Followers + following of the same
  seed produce duplicates (anyone mutual appears twice) → collapse to one row.
- **Whole-sheet dedupe = permanent master list.** A handle captured once from ANY
  seed is never re-added. The master is a growing, zero-repeat register.
- Screenshot is just the delivery mechanism for the handle; the scraper opens the
  account and reads the lists directly (no OCR needed — operator reads the handle).

## Master list schema (detailed by design — full audit trail)
`handle` (unique key) · `profile_url` (hyperlinked) · `source_seed` ·
`relationship` (follower/following/both) · `date_scraped` · `follow_status`
(pending/followed/failed) · `date_followed` · `unfollow_status`
(pending/unfollowed/failed/na) · `date_unfollowed` · `followed_back`
(yes/no/unchecked). State columns let both engines resume after any pause.

## Unfollower Engine
- **Trigger = follow-back check.** Only unfollow handles that did NOT follow back.
- **Grace period = 3 days (72h)** from `date_followed` before eligible. Without a
  grace period you'd unfollow people before they've even seen the notification.

## Auth
Session cookies (sessionid, ds_user_id, csrftoken), never password login (server
IP → checkpoints + 2FA). `sameSite:null` patch required on sessionid+csrftoken.
Cookies ~90-day life, refresh at day 60. Runs from a Mac on a home IP (IG blocks
scraping from server IPs — see the datacenter-wall notes in the main SKILL).
