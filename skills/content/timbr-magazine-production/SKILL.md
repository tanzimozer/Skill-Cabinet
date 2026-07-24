---
name: timbr-magazine-production
description: "Production workflow for TIMBR Workout Series digital magazines — reading Canva designs, populating Google Sheets, content analysis, and issue templating."
version: 1.0.0
tags: [TIMBR, magazine, canva, google-sheets, content, production]
related_skills: [canva-connect, google-workspace]
---

# TIMBR Magazine Production

End-to-end workflow for producing and analysing TIMBR Workout Series digital magazines. Covers reading Canva designs, mapping content to Google Sheets, and applying the repeatable 8-page template.

## Key Assets

| Asset | ID / URL |
|---|---|
| Magazine Production Sheet | `1J4Rv-_NInf_jtjOHNYhTvVEfel0LK_uCfjjozshB2Ew` |
| Editorial Bible tab | Magazine Production sheet → "EDITORIAL BIBLE" tab |
| Blair Production Tracker | Magazine Production sheet → "BLAIR — PRODUCTION TRACKER" tab |
| Blair content Google Doc | ID `11LbGDU034SFj_AYyqUxNWL3dBE6I8ZxRP3p0dxmc4co` — fully written |
| Shumon content | ❌ No Google Doc — only video files in Drive (posing + reel). Content extraction needed. |
| Taylor content | ❌ No Google Doc — content extraction needed before any Canva work. |
| Canva design registry | See `references/timbr-workout-series-structure.md` in `canva-connect` skill |

## Workout Series Design IDs (Canva)

| Issue | Design ID |
|---|---|
| Glutes & Hamstring | DAHFfAiLO3E |
| Shoulder & Core | DAHKu7sMKdE |
| Quads & Calf | DAHKuy17o8s |
| Chest & Tricep | DAHKuyPqxww |
| Back & Bicep | DAHKu6XleTQ |

## Standard 8-Page Template

Every issue follows the same structure:

| Page | Section | Nature | Key Variable |
|---|---|---|---|
| 1 | Cover / Hero | Dynamic | Muscle group + benefit line |
| 2 | TOC + Intro | Dynamic | Muscle group in headline + intro |
| 3 | The Program | Dynamic | Full exercise list |
| 4 | Gyms in Seattle | Dynamic | Mostly shared copy |
| 5 | Work & Corporate Life | Dynamic | Mostly shared copy |
| 6 | Recovery Guide | Dynamic | Muscle-specific recovery exercises |
| 7 | Nutrition / Macro CTA | Static | Identical across all issues |
| 8 | Subscribe / Outro | Static | Identical across all issues |

~50% of each issue is shared. Only pages 1–3 and muscle-specific recovery lines change meaningfully per issue.

## Reading a Canva Design

Canva API cannot return text content directly. Use PDF export → `pdftotext`:

```python
import requests, time, subprocess, json

creds = json.load(open('/home/hermes/.hermes/.canva_credentials'))
# Always refresh token first — expires every 4 hours
r = requests.post('https://api.canva.com/rest/v1/oauth/token',
    data={'grant_type':'refresh_token','refresh_token':creds['refresh_token'],
          'client_id':creds['client_id'],'client_secret':creds['client_secret']})
if 'access_token' in r.json():
    creds['access_token'] = r.json()['access_token']
    json.dump(creds, open('/home/hermes/.hermes/.canva_credentials','w'), indent=2)

headers = {'Authorization': f'Bearer {creds["access_token"]}', 'Content-Type': 'application/json'}

# Export
r = requests.post('https://api.canva.com/rest/v1/exports',
    json={"design_id": "DESIGN_ID", "format": {"type": "pdf", "export_quality": "regular"}},
    headers=headers)
job_id = r.json()['job']['id']

# Poll
for _ in range(15):
    time.sleep(3)
    r = requests.get(f'https://api.canva.com/rest/v1/exports/{job_id}', headers=headers)
    if r.json()['job']['status'] == 'success':
        pdf_url = r.json()['job']['urls'][0]
        break

# Download + extract
pdf = requests.get(pdf_url).content
open(f'/tmp/canva_{job_id}.pdf', 'wb').write(pdf)
result = subprocess.run(['pdftotext', f'/tmp/canva_{job_id}.pdf', '-'], capture_output=True, text=True)
text = result.stdout
```

**Batch export:** Run all export requests first (they're async), then poll all jobs — faster than sequential export+wait per design.

## Populating the Magazine Production Sheet

Tab name format: `Workout Series — [Muscle Group]`

Column structure (A–I):
- A: Page number
- B: Section name
- C: Content (extracted from PDF)
- D: Design Pattern / Principle
- E: Notes / Action
- F: Page Nature (Dynamic / Static)
- G: Purpose (why the page exists)
- H: Underlying Principle (strategic logic)
- I: Content Creation Questions (5 per page)

When adding a new tab, check existing tabs first with `sheets.get()` to avoid duplicate names or sheet ID mismatches. Always apply:
- Black header row with white bold text
- `wrapStrategy: WRAP` on all data rows
- Explicit `pixelSize` column widths (never auto-resize)
- `frozenRowCount: 1` to freeze the header

**Pitfall:** After adding new tabs with `addSheet`, the sheet IDs change. Re-fetch with `sheets.get()` before any `batchUpdate` that references `sheetId` — stale IDs silently fail.

## Content Extraction Principles (from Series Analysis)

These are the core editorial patterns Tanzim uses across all issues:

1. **Working lifter framing** — every page speaks to the 9-to-5 professional who trains seriously
2. **Anti-Instagram positioning** — "Real strength, real shape — not the ones that look impressive on Instagram"
3. **Cross-sell on the program page** — reader is most engaged here; embed naturally, not as an ad
4. **Nutrition page = funnel door** — minimal content, drives to timbr.fit. Never pad it.
5. **Subscribe CTA at the back** — captures reader at peak trust (just finished the product)
6. **Recovery uses HR zones** (Zone 1 <60%, Zone 2 60-70%) — signals coaching sophistication over "just rest"
7. **Seattle = brand philosophy page** — not a gym directory. TIMBR origin story embedded every issue.

## Magazine Production Content Questions (per page)

Use these when helping Tanzim produce a new issue. Each page has 5 questions to answer:

- **Page 1 (Cover):** Muscle group + benefit, series number, secondary benefits, visual mood, brand URLs
- **Page 2 (TOC/Intro):** 3 sections + page numbers, 3-sentence intro, anti-Instagram line, beyond-aesthetics benefit, reader hook
- **Page 3 (Program):** Full exercise list, activation choice rationale, compound lift rep range, cross-sell connection, finisher
- **Page 4 (Seattle):** New venue to name?, outdoor-to-muscle connection, TIMBR origin update needed?, philosophy tie-in, timely local hook
- **Page 5 (Corporate Life):** Lifestyle challenge for this muscle group, mindset shift delivered, scheduling tip, closing line
- **Page 6 (Recovery):** Zone 1 protocol, Zone 2 protocol + highest-ROI movement, scheduling language, muscle-specific mobility, injury risk warning
- **Page 7 (Nutrition):** Product being cross-sold, curiosity gap hook, landing page URL, thematic connection to issue, date stamp
- **Page 8 (Subscribe):** Subscribe URL + offer, cadence statement, brand close line, social/QR, immediate subscriber benefit

## Target Audience (23–35 Young Professionals)
- **Identity:** "The working lifter" — serious about training, 9–5 schedule, treats training as craft, not cardio
- **Key tension:** Time-constrained but ambitious. The 9–5 is structure, not a barrier.
- **Tone rules for this audience:**
  - Short declarative sentences — no motivational filler
  - Outcome-first — not product-description-first
  - By page 2 they've already bought — STOP PITCHING. Speak like they made a smart call.
  - Anti-Instagram as conviction, not defense: "Built for life — not for Instagram"
  - RPE language is appropriate — this audience trains seriously enough to understand it

## Change Management (CHANGES Tab)
All proposed edits live in the **CHANGES** tab of the Magazine Production sheet. MCP-ready instructions in column J.

Column structure:
- A: Change ID (CHG-001 format)
- B: Tab / Issue
- C: Canva Design ID
- D: Page number
- E: Element name
- F: Element description  
- G: Current value
- H: New value
- I: Action type (UPDATE_TEXT / ADD_ELEMENT / REMOVE_ELEMENT)
- J: **MCP Instruction** — exact natural language for Canva MCP to execute
- K: Rationale
- L: Status (PENDING / DONE)

**Changes logged as of May 27, 2026:** CHG-001 to CHG-115 covering Pages 1–6 across all 5 issues. Pages 7–8 are static — no CHANGES entries needed by design.

When adding new changes, always write the MCP Instruction (column J) as a precise, self-contained natural language instruction that includes the design ID, page number, element description, and exact new value. Claude executing via MCP should not need to look anything up — the instruction should be complete.

**PITFALL — Page 4 is easy to skip.** When iterating pages 1–6, Page 4 (Gyms) does not have a tightly defined page-by-page analysis framework like Pages 1–3, 5–6. It is easy to jump from Page 3 to Page 5 without noticing. Always verify page distribution in the CHANGES tab before declaring a page set complete: `{page: count for row in rows}` — all 6 dynamic pages must appear. Page 4 changes per issue: headline (neighbourhood name), equipment callout tied to session, best-time callout (ADD_ELEMENT), credibility line (ADD_ELEMENT).

**MCP Execution Prompt** — see `references/mcp-execution-prompt.md`. Use this when handing off CHANGES tab to Claude for Canva MCP execution.

## Page Improvement Frameworks (from 23-35 audience audit)

### Page 1 — Cover changes required
- Remove secondary URL (`WWW.SEATTLE.FITNESS`) — one brand URL only (`WWW.TIMBR.FIT`)
- Replace descriptive subtitle with outcome line: e.g. "Strength that shows up Monday morning." (not "A 50-minute workout for...")
- Add acquisition signal: small `timbr.fit/series` in bottom-right corner

### Page 2 — TOC + Intro changes required
- Expand TOC from 3 to 6 sections (add Work & Lifestyle, Recovery, Subscribe)
- Open with outcome line from cover + "Here is how you build it."
- Standardise close: "Real strength. Real shape. Built for life — not for Instagram."

### Page 3 — Program changes required
- Add programming logic line above exercise list ("The order is intentional...")
- Add time breakdown: "50 MIN TOTAL | Activation 5 min / Main work 35 min / Finisher 10 min"
- Add intensity guidance: RPE scale per exercise type
- Fix cross-sell: add muscle-group-specific connecting sentence before Sprint Progression stats

## Gym Rotation System (Page 4)
6 neighbourhoods: South Lake Union, Capitol Hill, Fremont, Queen Anne, Downtown Seattle, First Hill.

Page 4 now features 2 real gym features (Name / Neighbourhood / 1-sentence description / muscle-group tie-in) rather than generic Seattle editorial copy.

**Full rotation matrix:** GYM ROTATION tab in Magazine Production sheet (`1J4Rv-_NInf_jtjOHNYhTvVEfel0LK_uCfjjozshB2Ew`)

Rules:
1. 2 gyms per issue, each from a different neighbourhood
2. Never repeat a neighbourhood pair within a series (15 unique pairs across 3 series)
3. Never repeat the same gym across any issue
4. Each neighbourhood appears exactly 5 times across 15 issues
5. Always verify gym is still operating before publishing
6. Contact featured gym before publishing — opens partnership conversation

## Wix Store — Current Product State (May 30, 2026)

See `wix-api-operations` skill for full API reference and product IDs.

**Taylor Crow:** Hidden. Wrong PDF attached (BELLA SKY.jpg). Needs real PDF from Tanzim → upload to Wix Media Manager → API attach → re-enable.

**Workout Series Vols 01–05:** Hidden. PDFs uploaded to Wix Media Manager. Blocked on Tanzim doing Physical→Digital toggle in Dashboard UI (Wix Catalog V1 API cannot do this). After toggle, Friday can attach PDFs via API PATCH and flip visible.

**Products with no images (5):** Taylor Crow, Complete Bundle, Hoodie, Cap, Performance Bra. Blocked on Tanzim providing photography.

## Digital PDF Sales Strategy (added May 2026)

### Pricing
| Product | Price |
|---|---|
| Individual trainer magazine | $19.99 |
| 3-trainer bundle (Blair + Shumon + Taylor) | $49.99 |
| Foundation Workout Series (individual) | $9.99 |
| Foundation Workout Series (complete) | $39.99 |
| Complete library | $79.99 |

### Wix Shop Structure — "TIMBR Digital Library"
- Frame as a **collection**, not individual PDFs (Netflix shelf concept)
- Series 1: Trainer Magazines (personality-led — Blair, Shumon, Taylor)
- Series 2: Foundation Workout Series (programme-led)
- Each listing: full-bleed portrait cover + **3-line hook** (not a description) + price
- Free 1-page preview PDF → email capture → sell full magazine to warmed list

### Listing Copy Rules
1. Title = specific promise + time frame (not a topic label)
2. Description = 3-line hook, not a contents list
3. Cover image = full bleed, portrait, magazine-quality (not a Canva mockup)
4. "Vol. 01" framing on every issue — signals series, creates anticipation

### Cover Line Rule (critical)
**WRONG:** "A peek at Blair's lifestyle, fitness and more."  
**RIGHT:** "Build Blair's Body. Her exact system. 6 weeks."

Every cover line must be a **promise**, not a description.

## Editorial Bible Cross-Match Process (Blair template — May 2026)

When cross-matching a trainer magazine against editorial standards:

1. Load the trainer's content Google Doc
2. Check each section against these standards:
   - Cover: promise-based cover line?
   - All body copy: second person ("you") or third person ("Blair does")?
   - Feature pages: authority anchor stat present?
   - Programme: every exercise has name + sets + reps + rest + coaching cue?
   - Nutrition: grocery list present? (non-negotiable)
   - Closing page: Vol. N+1 tease present?
3. Build a production tracker tab in the Magazine Production sheet
4. Output a priority fix list (Critical → High → Medium → Low)
5. Estimate time: ~5 mins per fix, ~45 mins total for Blair-scale issue

**Blair Issue 01 priority fixes (May 29, 2026):**
| Priority | Fix | Where |
|---|---|---|
| CRITICAL | Cover line → "Build Blair's Body. Her exact system. 6 weeks." | Page 1 |
| CRITICAL | Add grocery list (chicken breast, egg whites, tilapia, Greek yogurt 0%, salmon, jasmine rice, sweet potato, oats, blueberries, avocado, spinach, olive oil, rice cakes, apple) | Pages 12–13 |
| HIGH | Add Vol. 02 tease to closing page | Page 24 |
| HIGH | Flip 3rd person → YOU on pages 4–5, 20–21 | Pages 4–5, 20–21 |
| MEDIUM | Add cardio phase table | Pages 18–19 |
| MEDIUM | Add training philosophy anchor stat | Pages 6–7 |
| LOW | Add toning summary box | Pages 16–17 |

## PRD Location
Full reverse-engineered PRD lives in the **PRD tab** of the Magazine Production sheet. Covers product overview, target audience, page structure, content rules, technical specs, distribution, and Series 02 roadmap gaps.

## Blair — Injury-aware programming note (May 2026)

Blair has a right hip injury (greater trochanteric bursitis / glute med / TFL strain, suspected). Severity 7/10 as of May 28. No lower body loading until physio clearance. Magazine training programme pages should note this — either add a modification callout or hold Day 1/3/4 programme pages until she's cleared. See `Blair's tracking sheet → Mobility & Injuries tab` for full log.

## Trainer Magazine Series — Current State (May 2026)

Three personality-led trainer magazines (separate from Foundation Series):

| Trainer | Status | Content Doc |
|---|---|---|
| Blair Grimes | Canva in progress — 7 priority fixes needed | `11LbGDU034SFj_AYyqUxNWL3dBE6I8ZxRP3p0dxmc4co` |
| Shumon Asef | No content doc — extraction pending | Drive folder: `1ABgAz70gdDrsSPMnTpKCHXE41GuZL8fS` (video only) |
| Taylor Crow | No content doc — extraction pending | Nothing in Drive yet |

Pricing: $19.99 each / $49.99 bundle. Platform: Wix TIMBR Digital Library.
Trello board: https://trello.com/b/U7StsSvp (ID: `6a0e81483e169b28504ba8c1`).
Lists: TO DO (`6a0e81499eade99efbbaa28c`), IN PROGRESS (`6a0e814993006a98af881696`), IN REVIEW (`6a0e8149409a6f9a8e3bf7ff`), LAUNCH PREP (`6a0e81496392d9a63c836ce4`), DONE (`6a0e814aa49ecbff5b43677f`).

## References

- `references/editorial-bible.md` — benchmark magazine methodology, 3-layer article structure, tonality rules, power phrases, section order, pricing research
- `references/mcp-execution-prompt.md` (in `canva-connect` skill) — full 3-series neighbourhood pairing matrix, gym pool per neighbourhood, rotation rules
- `references/gym-rotation-series01-03.md` — full 3-series neighbourhood pairing matrix
- `wix-api-operations` skill — all Wix REST API patterns, product IDs, blog/draft IDs, API limitations, and full launch state audit
