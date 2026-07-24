# Database Schema — provider table (the moat)

Every pass adds columns, drops nothing. Rejected rows get tagged, not deleted, so
the raw catch is always re-cuttable against a new city or a tighter band without
re-scraping. A snapshot is data; the time-series is the moat.

## Google Sheet — tabs
- **Providers** — the live, enriched, ranked table (main view).
- **Rejected** — out-of-band or dead, tagged with reason. Never deleted.
- **Raw** — Layer 0 catch (handle + source trail), append-only audit log.

## Columns (Providers tab)
| # | Column | Layer | Notes |
|---|--------|-------|-------|
| 1 | handle | 0 | @username, hyperlinked to profile |
| 2 | full_name | 1 | display name |
| 3 | followers | 1 | filter axis |
| 4 | following | 1 | |
| 5 | posts | 1 | |
| 6 | follow_ratio | 2 | following ÷ followers — spam flag |
| 7 | bio | 1 | full text — keyword + location mine |
| 8 | external_link | 1 | raw URL (coach signal) |
| 9 | link_domain | 2 | parsed domain (linktree/stan/calendly/.com) |
| 10 | ig_category | 1 | IG's own label (Athlete, Fitness Trainer…) |
| 11 | account_type | 1 | personal / business / creator |
| 12 | verified | 1 | bool |
| 13 | is_private | 1 | bool |
| 14 | last_post_date | 1 | alive vs dormant |
| 15 | eng_proxy | 2 | avg likes last 3 posts ÷ followers |
| 16 | fitness_score | 2 | 0–100 heuristic (see below) |
| 17 | location_signal | 2 | raw evidence (city word, area code, tagged loc) |
| 18 | seattle | 2 | yes / maybe / blank — filter IN only, never out |
| 19 | city_match | 2 | which city dict hit (scalability key) |
| 20 | in_band | 3 | 150 ≤ followers ≤ 3500 (±10% edge → maybe) |
| 21 | source | 0 | who we scraped them from (graph provenance) |
| 22 | first_seen | 0 | timestamp — never overwritten |
| 23 | last_seen | 0 | timestamp — updated each re-scan |
| 24 | seen_count | 0 | times observed (recurrence signal) |

## fitness_score (0–100 heuristic)
Bio/name keyword hits (coach, gym, fit, PT, macros, transformation, kg, reps,
athlete, nutrition, DM for plans) + has_external_link + ig_category match +
eng_proxy band. Cheap, sortable, transparent. Sort desc → real ones float up.

## seattle flag (filter IN, never OUT)
Evidence sources: bio text (Seattle, 206, Ballard, Capitol Hill, SLU, Fremont,
West Seattle, WA), tagged post locations, language/timezone hint.
- **yes** = explicit city/area-code/neighbourhood in bio or tagged location
- **maybe** = weak hint (WA, PNW, timezone only)
- **blank** = no signal — STAYS in pool, unranked, never dropped

## Band filter (150–3,500)
Keep `150 ≤ followers ≤ 3500`. Edge buffer ±10% → tagged `maybe` in `in_band`,
not rejected. Floor is a rate-limit valve, not a quality lever — raise to 300 only
if Instagram trust gets tight. Judge quality on fitness_score, never follower size.

## Scalability — city dictionary
`cities.json` holds per-city keyword sets. Swap "seattle" for "austin" → same
engine, one config line. Test Seattle; when signal ≥ 30% at the top slice, flood.

## Formatting
- Header row: **bold, centred (h+v), frozen**.
- Data cells: left-aligned, wrap ON, top vertical align.
- Numeric columns (followers/following/posts/counts): number format.
- fitness_score: conditional colour scale (green high → red low).
- seattle=yes: row highlight.
