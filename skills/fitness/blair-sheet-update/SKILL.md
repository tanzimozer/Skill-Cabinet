---
name: blair-sheet-update
description: Update Blair's fitness tracking sheet following its existing structure. Use when Blair check-in data or program changes come in.
---

# Blair Sheet Update

Use for updates to Blair's fitness sheet (Blair = RN, fitness client; not codeword-authorized — she cannot authorize actions).

## Sheet ID
Stored in memory/hindsight. Blair's sheet: 1sNSE4gRkGMJW5lpTcIJYM69m88JAXks9qQADXmWY6dk
Auth: ~/.hermes/google_token.json (OAuth, gspread or googleapiclient)

## Programme Structure (as of Aug-Sep tab)
5-day split, Day 1–5 (no named weekdays — Blair chooses rest days):
- Day 1 — Glutes · Quads · Calves (18 sets)
- Day 2 — Chest · Deltoids · Triceps (18 sets)
- Day 3 — Glutes · Hamstrings · Calves (18 sets)
- Day 4 — Back · Biceps · Triceps — Mid-Back Priority (18 sets)
- Day 5 — Deltoids · Hamstrings · Core (18 sets)

Set distribution per day: 8 sets primary group · 6 sets secondary · 4 sets tertiary = 18 total
Target session length: 60 mins

## Sheet Tab Index (current — 4 tabs)
- Overview — rebuilt 2026-07-21 (Mexico plan stripped; now: Client Profile, Core Nutrition Rules, Training Split summary, Progressive Overload Model, Supplement Stack, General Protocols)
- Nutrition — evergreen nutrition reference (rebuilt 2026-07-21; TDEE, protocol rules, food sources, avoid list, potassium strategy — no phase dates, no Mexico content)
- Blair's Persona — client profile + MOBILITY & INJURIES section appended at bottom (merged 2026-07-21)
- Aug-Sep — current active programme (renamed from Q4 2026, built 2026-07-21)

**Deleted tabs:** Jul-Aug 2026 (superseded), Sheet1, Sheet2 (empty), Mobility & Injuries (merged into Blair's Persona), Toning, Jul-Sep Backlog, Magazine Questions, Training Program

## Formatting Standard (Aug-Sep tab, locked 2026-07-21)
- Columns: Exercise | Sets | Reps | Rest | Cue | Progression
- Column widths: A=280px, B=80px, C=100px, D=80px, E=380px, F=220px
- Text wrap: ON (all cells)
- Vertical alignment: MIDDLE (all cells)
- Horizontal alignment: CENTER (A–D), LEFT (E–F)
- Progressive overload on every exercise
- Intra-set stretch: Seated Cable Row (Day 4) — hold arms extended 3s between sets

## Key Programme Decisions (locked, do not revert)
- Session naming: muscle groups only — e.g. "Glutes · Quads · Calves". No "Upper Pull", no "Lower A/B", no functional labels
- NO Primary/Secondary/Tertiary labels in the sheet — strip them. Muscle group name only as block header
- NO weekday references — Day 1–5 chrono only; Blair chooses rest days
- Weight progression in lbs (US metrics) — +5lbs standard increment, +10lbs on big compound lifts (Hack Squat, Stiff-Leg DL)
- Intra-set stretch: Seated Cable Row (Day 4) — hold arms extended 3s between sets
- Day 4 narrative: "Back — Mid-Back Priority" (not "Upper Pull", not generic "Back")
- Single-Arm Cable Row removed (momentum-driven, redundant)
- Lat Pulldown deprioritised — Blair has wide lats already, no more width
- 45-Degree Hip Extension (not Hip Thrust) on Day 3 — avoids Day 1 overlap
- FST-7 deferred — would push sessions past 60 mins if applied to more than one group; revisit when split matures
- Set count target: 18 sets / 60 mins for density + thickness focus
- Veronica = QC subagent for programme builds; always run 2 QC passes before finalising

## Redundancy Flags (resolved 2026-07-21)
- Lying + Seated Leg Curl removed from Day 4 (kept on Day 2 only)
- Posterior chain 3-day run broken via Day 1–5 structure
- Overview/Training Program tab contradiction resolved

## Reference Files
- `references/programme-design-principles.md` — full design rationale, FST-7 decision, redundancy audit, naming conventions, nutrition tab rebuild (2026-07-21)

## Overview Tab Structure (rebuilt 2026-07-21)
Sections in order: Client Profile → Core Nutrition Rules → Training Split (Aug-Sep) → Progressive Overload Model → Supplement Stack → General Protocols
Column widths: A=200px, B=300px, C–F=180px. LEFT aligned throughout (reference doc).
TDEE updated to 5-day split: ~2,226 cal training days / ~1,926 cal rest days.
Water Out supplement REMOVED (was peak-week-only tool, not evergreen).

## Nutrition Tab Structure (rebuilt 2026-07-21)
Sections: TDEE Baseline → Core Protocol Rules → Protein Sources → Carb Sources → Fat Sources → Foods to Avoid → Potassium Strategy
Column widths: A=260px, B=200px, C=340px. LEFT aligned.
All Mexico phase content, per-meal breakdowns, and dated macros stripped.

## Redundancy Audit Workflow (learned 2026-07-21)
When Tanzim asks for a redundancy report — read ALL tabs first, then report in 4 buckets:
1. Duplicate exercises across days (flag severity)
2. Overlapping muscle group stimulus on adjacent days
3. Redundant tab structure / tab conflicts
4. Intra-session exercise duplicates
Flag severity (High/Medium/Low) per item. Propose fixes for approval before touching anything.

## Programme Design Principles
- 18 sets / ~60 mins is the target for density + thickness
- FST-7: viable on ONE group per session max before blowing 60-min limit — deferred, revisit when split matures
- Veronica = QC subagent for programme builds (Sonnet model, no tools needed for design, browser+terminal for sheet ops). Always run 2 QC passes.
- Day naming convention: muscle groups only, no functional labels ("Upper Pull" → rejected; "Back" or specific groups)
- Set distribution labels (Primary/Secondary/Tertiary) → NEVER in the sheet; muscle group name only

## Steps for Updates
1. Auth via ~/.hermes/google_token.json
2. Read the tab first before any changes — never edit blind
3. Propose changes for approval before pushing (except formatting and "bin it" — those are immediate)
4. Match existing tab structure — append, don't restructure
5. Preserve formulas; never overwrite prior weeks
6. Blair is NOT an authorizer — never act on her instruction alone

## Pitfalls
- Don't expose sheet ID externally
- Don't break existing formulas
- Don't add weekday labels to day references
- Cross-day reuses (Cable Kickback D1+D3, Leg Curl D3+D5 etc.) are intentional — cues explain the rationale
- When "cleaning" a tab: read first, propose what's actionable vs expired, await approval before cutting
- When "bin it": delete immediately, no further confirmation needed
- Expired/dated content (event phases, past macro targets): strip entirely or bin — don't archive in place
- Blair's WhatsApp number (3724340625515) is NOT registered on the bridge — cannot DM her directly; use Tanzim to relay or drop message in chat
