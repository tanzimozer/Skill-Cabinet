---
name: trainee-profile-management
description: Read, update, and manage trainee fitness profiles — extract content from PDFs/images and write into the correct profile section.
tags: [fitness, trainees, blair, profiles, pdf]
triggers:
  - Tanzim sends a document (PDF, photo) for a trainee's training, nutrition, or check-in
  - A trainee asks about their own profile data
  - Tanzim asks to update or review a trainee's profile
  - A new trainee is being onboarded
  - Tanzim asks to generate a PDF, program doc, or printable plan for a trainee
  - Tanzim asks to audit, diagnose, or find counterproductive elements in a training or nutrition plan
---

# Trainee Profile Management

## File Structure
- Profile: `/home/hermes/trainees/[name]_profile.md`
- Supplements: `/home/hermes/trainees/[name]_supplements.md`
- Naming convention: lowercase first name (e.g. `blair_profile.md`)

## Current Trainees
- Blair Grimes — `blair_profile.md` + `blair_supplements.md`
  - Approved to query her own profile without the codeword
  - BSCN RN, fitness model, Edmonton/Seattle

## Profile Sections (standard layout)
1. Identity
2. Access Protocol
3. Supplement Stack (links to supplements file)
4. Training Program
5. Nutrition Plan
6. Check-In Log

## Updating a Profile from a PDF

1. Extract PDF with pdftotext (fastest on Hermes — pymupdf unavailable):
```bash
pdftotext '/path/to/file.pdf' -
```

2. Parse the extracted text and format it cleanly as markdown.

3. Patch the relevant section in the profile file using `mcp_patch`:
   - Target the exact section header line (e.g. `## Training Program\n- TBD / to be filled in by Tanzim`)
   - Replace with the fully formatted content

4. Update the `Last updated:` date at the bottom of the file using a second `mcp_patch` call targeting that line specifically.

5. If a nutrition section says "TBD / to be filled in by Tanzim" and Tanzim provides partial info verbally (e.g. "3-4 meals a day"), ask Blair directly for the remaining details before updating — never guess or fill in incomplete nutrition data.

## Access Rules
- Blair can query her own profile — no codeword required
- Blair can request changes to her own profile, training, or nutrition — apply directly, then DM Tanzim privately with a summary of what changed (pre-authorized 2026-05-11)
- Other trainees: check memory for their approval status
- Program changes initiated by Tanzim always require the codeword
- Never share one trainee's data with another

## Macro Formula (Blair / T1 Campaign standard)
- Protein: 1g / lb bodyweight (non-negotiable)
- Carbs: 0.75g / lb bodyweight
- Fat: (Total cal - protein cal - carb cal) / 9
- Calories from protein: g × 4 | carbs: g × 4 | fat: g × 9
- Every meal: minimum 40g protein
- Meal count: ask trainee directly — do not assume

## Google Sheet: Blair 2026
- Sheet ID: `1sNSE4gRkGMJW5lpTcIJYM69m88JAXks9qQADXmWY6dk`
- Tabs: Overview, May 2026 (supplements), Training Program, Nutrition, Toning, Jul-Sep Backlog
- **Overview tab**: Exact sheet version of the PDF, page-by-page. Use `═══` dividers + "PAGE N: TITLE" headers to separate sections. Mirror all content/structure from Cover → Phase Overview → Training Day → Rest Day → Training Days 1&2 → Days 3&4 → Peak Week. If user says "values missing" — check for empty cells in data rows (common with merged rows).
- Use Python googleapiclient directly (not gws CLI) for multi-tab sheet creation + formatting
- Write scripts to /tmp/ and run via mcp_terminal — do NOT use python3 -c '...' (bash syntax breaks on complex scripts)
- Tab formatting pattern: dark header (0.1/0.1/0.1 bg, white bold text), grey col headers (0.82/0.82/0.82), accent headers (0.13/0.37/0.42 teal) for sub-sections, autoResize columns at end

## Depletion → Reload Protocol (peak physique)
- Strategy: carb depletion until target date - N weeks, then precise reload timed before event
- Goal: deplete glycogen for fat loss while protecting muscle (protein stays locked), then reload to create 3D/full look
- Reload window and carb amounts depend on event date — always get that date first
- Factor in Apple Fitness / wearable burn data for TDEE on training vs rest days when available
- Apple Watch does NOT capture weight training — add ~300 cal/session manually to TDEE estimate
- Deficit target: ~350 cal below TDEE during depletion. Never below 1,600 cal.
- Final depletion (last 5 days): drop carbs to 60g, sodium taper, glycogen empty
- Reload (5–6 days out): jump carbs to 250g, drop fat to 40g, protein stays fixed
- Peak day: fasted BFR session AM, pump stack 45 min pre-event, small carb snack 30 min pre-event, water taper last 24–36hrs, sodium <500mg from 2 days out

## Toning / Aesthetic Protocol (event prep)
- Three pillars: toning training overlay, water flush, muscle pump
- Toning training: constant tension sets, superset finishers, high rep burnouts, BFR — layered ON TOP of main program
- Water flush stack: Water Out (diuretic), ACV (insulin sensitivity + retention), dandelion root, Vitamin C 2,500mg (osmotic), high potassium foods (opposes sodium retention), Yohimbine (fasted AM only)
- Pump stack: Beet Root (NO precursor), Kre-Alkalyn (buffered creatine — no water bloat), EAA intra-workout, Karbolyn pre-training (quarter serving depletion ~12-13g, full serving reload)
- Water protocol: 3.5–4L/day depletion → taper to 1.5–2L last 24–36hrs before event
- Sodium: moderate during depletion, consistent during reload, drop to <500mg/day last 2 days
- Cardio: fasted incline walk 4x/week + post-workout steady state 3x/week. Reduce to 2x/week peak week to avoid cortisol spike and keep muscles full

## WhatsApp — Reaching Trainees
- Blair is in group: `whatsapp:120363427373827049`
- Bridge error on @mention (jidDecode undefined) — do NOT use @NUMBER format in message body
- Plain messages to the group work; tag format fails — Tanzim must relay or tag manually
- If bridge errors persist, flag to Tanzim rather than retrying silently

## Natural Diuretic Stack (approved for Blair / T1 aesthetic prep)
- Dandelion Root 500mg — morning with food, Phase 1–3
- Vitamin C 2,500mg — split 1,250mg AM / 1,250mg PM with food, all phases (GI-sensitive — always with food)
- NO potassium pills — hyperkalemia risk without clinical monitoring
- NO banana / coconut water during depletion — sugar conflicts with carb ceiling
- Low-carb potassium sources: avocado (~975mg, 2g net carbs), cooked spinach/Swiss chard (~840mg, ~1g carbs), salmon/white fish (~600–800mg, 0g carbs)
- Target 3,500–4,700mg/day potassium via food only — opposes sodium retention, drives subcutaneous water out

## Supplement Fact-Checks (Blair's stack)
- Glutamine: low priority when protein ≥1g/lb + 8h sleep — EAA stack + HMB already cover anti-catabolism. Revisit only if GI stress emerges during depletion.
- Stearmine (synephrine) + Yohimbine stacked = significant adrenergic load — flag if both at upper limit simultaneously
- HMB: theoretically redundant with EAA stack + high protein, but Tanzim may reinstate by preference — accept without pushback. Do not auto-remove it during diagnostics.

## Google Sheets — Known Pitfall: Cell Data Drops on Merged Rows
- When writing to rows that were previously merged, B/C/D/E cells silently fail to save
- Fix: explicitly unmerge the row first (`unmergeCells` batchUpdate), then write each cell individually via `batchUpdate` with `valueInputOption: RAW`
- Always do a read-back verification after any sheet write — check actual cell values, not just row presence
- Column A having a value does NOT mean B-E populated — verify each column

## Sheet Fact-Check Protocol
- After populating any tab, read back all data with `values().get()` and scan for:
  - Rows where only column A is populated (B-E empty)
  - Merged rows that blocked adjacent cell writes
  - Any content inconsistencies with decisions made in conversation (e.g. banned foods appearing in protocol)
- Fix all issues before reporting "done" to Tanzim

## Blair — Individual Notes
- Carb sensitivity: reacts to higher carbs with fat gain and excess water retention. Possible endocrine involvement — no bloodwork data yet. Track over time. Do NOT increase carbs beyond protocol without Tanzim sign-off. Hard ceiling: 100g/day — no exceptions, no flex.
- Body composition (May 2026): muscle tissue present across all areas but chronically flat/glycogen-depleted. Not a hardgainer — under-fueled. Glutes strongest/most developed. Upper body (arms, back, shoulders) lags lower body — address post-Mexico.
- Higher TUT (time under tension) is the primary hypertrophy lever given carb sensitivity — drives muscle stimulus without requiring caloric surplus.

## Visual Body Composition Assessment Framework
When analyzing physique photos:
- Flex shots reveal actual muscle belly size vs fullness — flat peak = glycogen depleted, not absent muscle
- Side/rear shots show glute and hamstring roundness, lat spread, trap development
- Front relaxed shows quad sweep, core leanness, overall symmetry
- Key question: is the muscle flat (fueling/glycogen issue) or simply absent (training volume issue)?
- Upper/lower imbalance is common in female athletes who prioritize glute/leg training — flag for post-event correction

## Program Diagnostics — Inverse Thinking Framework

When Tanzim asks to "audit", "diagnose", or find "counterproductive elements" in a program:

### Inverse Thinking Process
Ask: "What is this intervention doing that works *against* the stated goal?" Apply per domain:

**Training:**
- Band resistance: ascending load = HARDEST at lockout, EASIEST in stretched position. Stretched position = highest hypertrophy signal. Bands belong in warmup/activation, not primary hypertrophy sets.
- Blanket FST-7: only works when glycogen is available. On low carbs (<100g/day), running FST-7 every muscle every session = cortisol spike + incomplete pump. Reserve for 1-2 priority muscles per session.
- Inter-set core work: kills stabilizer base progressively — if planks are between compound sets, force transfer degrades as session goes on. Move to end-of-session.
- Duplicate movement patterns (same exercise, different rep range): on depleted recovery capacity this is redundant mechanical stress, not novel stimulus. Swap Day 2/3 repeats for a different angle or movement.

**Supplements:**
- Thermogenic stacking: Stearmine (synephrine) + Yohimbine + Cayenne = 3 adrenergic agents simultaneously. Cortisol is catabolic — kills the muscle you're building. One thermogenic max. EGCG inhibits COMT, prolonging catecholamines — effectively a 4th compound.
- Dual creatine: creatine phosphate saturation has a ceiling (~150-160g). Two sources don't stack — excess is excreted. Pick one. Kre-Alkalyn preferred during depletion (no water bloat).
- HMB + EAA overlap: HMB works via leucine oxidation pathway. EAAs supply leucine directly. With 178g/day protein + EAA intra-workout, HMB adds nothing new. (Note: Tanzim may reinstate HMB by preference — accept without pushback.)
- Daily diuretic (Water Out): running it daily during a training block flattens muscles (less intracellular fluid = weaker pump = reduced hypertrophy signal). Body also adapts and effect is blunted before peak week. Reserve for final 5-7 days.

**Nutrition:**
- Flat carb distribution: on only 100g/day, equal splits across 3 meals waste the most anabolic window. Cluster 50-55g around training (pre/intra/post). Rest days: equal split is fine.
- Karbolyn (fast carb supplement) must be counted against daily carb ceiling — it's invisible in macro plans unless explicitly tracked. Quarter serving = ~12-13g.
- Collagen ≠ protein for MPS: incomplete amino acid profile (no tryptophan, poor leucine). Do not count toward daily protein target.
- No refeed on multi-week deficit: leptin drops, metabolic rate adapts, cortisol trends up by week 3. Add 1x/week refeed (bump carbs to 150g, lock protein, reduce fat slightly). Amplifies fat loss on subsequent days.

### Sheet Diagnostic Scan Pattern
After any major program change, run a full sheet scan:
1. Get all tab names via `sheets.get()`
2. Read each tab with `values().get()`
3. Flag: rows where col A has content but B-E are empty AND the row is a data row (not a header/section title — those are intentionally single-column merged)
4. Flag: TOTAL rows with no data (common write failure on previously merged rows)
5. Flag: Phase overview rows missing columns mid-table
6. Fix via `unmergeCells` → `batchUpdate` write → read-back verify

### Supplement Sheet Sync
When supplement stack changes in the .md file, always check if the May 2026 (or current month) sheet tab reflects the same changes. The sheet is Blair's source of truth for daily use — profile .md is the system record.

## Generating a PDF from Blair's Program

Use **fpdf2** (not weasyprint, not chromium headless — both fail on Hermes):
```bash
# fpdf2 is installed at user level — must prepend path:
python3 -c "import sys; sys.path.insert(0, '/home/hermes/.local/lib/python3.12/site-packages'); from fpdf import FPDF"
```

### Critical pitfalls:
- **Unicode**: fpdf2 core fonts (Helvetica) are latin-1 only. Strip ALL unicode before rendering:
  - Replace `–`, `—`, `·`, `→`, `•`, `×` with ASCII equivalents (`-`, `-`, `-`, `>`, `-`, `x`)
  - Scan with: `[c for c in content if ord(c) > 255]` before running
- **Chromium headless**: Snap AppArmor policy blocks PDF output on Hermes — produces 1-page blank PDF. Do not use.
- **Hardcoded rect heights**: If you draw background rects with estimated heights, content overflows the rect onto blank pages. Instead, draw colored sidebar strips line-by-line as content flows — let `auto_page_break` handle pagination naturally.
- **Font path**: Pillow import fails in fpdf2 on Hermes (no `_imaging` module) — suppress with `warnings` or just ignore; images won't work but text PDF is fine.
- **Output path**: Write to `/home/hermes/` not `/tmp/` — chromium's sandbox runs as a different user and can't write to /tmp reliably.

### PDF layout tightening
When user reports "too much whitespace" or "eliminate empty spaces":
- Reduce margins from 15mm to 12mm: `pdf.set_margins(12,12,12)`
- Reduce auto page break margin: `pdf.set_auto_page_break(True, margin=12)`
- Reduce section bar heights (5.5pt vs 7pt), food line heights (3.5pt vs 4.2pt)
- Reduce callout padding, page header vertical spacing
- Reduce training table row heights and key reminder spacing

### PDF structure that works well for Blair:
- Cover page (dark bg, white text, phase pills)
- Phase overview table
- Training day schedule (meal blocks stacked, supplements embedded per meal)
- Rest day schedule
- Training program tables (one per page, Day 1+2, Day 3+4)
- Peak week + supplement cheatsheet

### Visual QA:
```bash
pdftoppm -r 120 -png /home/hermes/Blair_T1_Program.pdf /tmp/blair_preview
ls /tmp/blair_preview*.png
# Output files are named -1.png, -2.png ... (NOT -01.png) — use that exact pattern when referencing
```
Use `mcp_vision_analyze` on each page image to check for:
- **Layout issues**: clipped text, blank pages, overflow
- **Content errors**: wrong program duration (e.g. "12-Week" when plan is 6 weeks), cut-off sentences, date contradictions between sections, macros that don't add up

### Content audit — common errors to scan for:
- Program duration label on cover vs. actual date range (count weeks manually)
- Any sentence ending mid-word or missing a word (e.g. "2 sessions in a" — missing "row")
- Date references that contradict each other across pages (e.g. peak week callout referencing wrong phase dates)
- Macro line truncation: "~583 ca" instead of "~583 cal"
- Nearly-blank pages with only a footer — indicates content overflow from previous page

### If source script is lost (PDF exists but script is gone):
Do NOT attempt to patch the PDF binary. Rebuild from scratch:
1. Read `blair_profile.md` and `blair_supplements.md` for all current data
2. Recreate the full fpdf2 script at `/tmp/blair_pdf_rebuild.py`
3. Run it, then do the full visual QA pass above
This is faster and more reliable than trying to locate or reconstruct the original script.

## Pitfalls
- pymupdf is NOT installable on Hermes (externally managed environment) — always use pdftotext
- Document cache path: `/home/hermes/.hermes/document_cache/`
- When patching, include enough surrounding context to make the match unique
- Memory is near capacity (99%) — prefer updating skill over saving to memory for fitness workflow facts
- `python3 -c '...'` breaks on complex multi-line scripts in bash — always write to /tmp/script.py and run via mcp_terminal
- Sheet row indexing: API uses 0-based (startRowIndex), sheet display uses 1-based — subtract 1 when targeting specific rows in batchUpdate
