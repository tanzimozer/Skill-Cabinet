---
name: fitness-program-documents
description: Create formatted workout/training program documents from structured data sources (JSON, spreadsheets, APIs). Includes extraction, synthesis, and multi-format output (text, HTML, PDF) for tactical fitness reference guides.
tags: [fitness, workout, training, pdf, document-generation, data-extraction]
---

# Fitness Program Documents

Create scannable, tactical workout program documents from structured data sources. Target format: one-page reference guides with exercise tables, progression schemes, and protocol definitions.

## When to Use

- Extracting training program details from JSON, spreadsheets, or APIs
- Creating client workout one-pagers or quick reference cards
- Formatting exercise programming (sets/reps/tempo/RPE tables)
- **Creating nutrition one-pagers** (macros, meal structure, supplement stacks)
- Converting workout/nutrition data into print-ready PDFs
- Synthesizing multi-section fitness data into unified guides

## Core Pattern

### 1. Data Extraction
```python
import json

# Load and extract from structured source
with open('data.json', 'r') as f:
    data = json.load(f)

# Common fitness data sections to look for:
# - Training Program / Workout Split
# - Exercise details (sets, reps, tempo, RPE)
# - Progression schemes
# - Protocol definitions (hyperplasia, toning, etc.)
# - Weekly structure/calendar
```

### 2. Content Synthesis
Fitness programs often span multiple data sections. Synthesize:
- **Training split** (weekly calendar of workout days)
- **Key exercises** with programming details (sets/reps/intensity)
- **Progression scheme** (week-by-week periodization)
- **Protocols/techniques** (advanced methods, special sets)
- **Quick reference** (tempo notation, RPE scale, nutrition timing)

### 3. Output Formats

**Create 3-4 formats for different use cases:**

1. **Plain text** (.txt) - Full reference with ASCII formatting
2. **Enhanced text** (.txt) - Box-drawing characters for visual structure
3. **HTML** (.html) - Styled with CSS for web/PDF conversion
4. **PDF** (.pdf) - Primary deliverable, print-optimized

### 4. HTML-to-PDF Conversion

**Chromium headless (preferred):**
```bash
chromium-browser --headless --disable-gpu --no-sandbox \
  --print-to-pdf=output.pdf input.html
```

**Alternative tools (fallback order):**
- wkhtmltopdf: `wkhtmltopdf input.html output.pdf`
- WeasyPrint: `weasyprint input.html output.pdf` (requires Python package)
- Puppeteer/Playwright (if Node.js available)

**Always check availability first:**
```bash
which chromium-browser chromium google-chrome chrome 2>/dev/null | head -1
```

## Fitness-Specific Formatting

### Nutrition One-Pagers

**Standard structure for nutrition guides:**
```
1. Daily Macros (current phase)
   - Calories, protein, carbs, fat
   - TDEE context
   - Training frequency

2. Meal Structure
   - Number of meals per day
   - Timing (7 AM, 12 PM, 6 PM typical)
   - Protein targets per meal
   - Training day variations

3. Key Foods
   - Proteins (staple sources)
   - Carbs (timing strategy)
   - Fats (EFA priorities)
   - Foods to avoid

4. Meal Prep Approach
   - Daily baseline routine
   - Social navigation strategies
   - Travel protocols

5. Supplement Stack
   - Daily baseline (all days)
   - Training days only
   - Peak week / special phases

6. Macro Progression (if phase-based)
   - Table: Phase | Dates | Cal | Protein | Carbs | Fat

7. Protocol Notes
   - Goal context (cut vs. toning vs. bulk)
   - Deficit/surplus strategy
   - Special timing rules
```

**Extract from actual client data:**
- Breakfast: Look in persona interviews for "What does your protein-heavy breakfast look like?"
- Social tactics: "How do you navigate social dinners?"
- Avoid list: "What food did you think was healthy that turned out to be sabotaging you?"

**Format principles:**
- Scannable (not paragraph-heavy)
- Actual foods (not generic "lean protein")
- Authentic voice (client's real preferences)

### Exercise Tables
```
# Standard columns for exercise programming:
Exercise | Sets | Reps | RPE | Tempo | Protocol/Notes

# Example row:
Smith Machine Hip Thrust | 4 | 8 | 8-9 | 4/2/1 | LOADED STRETCH: 2s hold at top
```

### Tempo Notation
Format: `Eccentric/Pause/Concentric`
- 4/2/1 = 4s lowering, 2s pause, 1s lifting
- 3/1/2 = 3s lowering, 1s pause, 2s lifting

### RPE Scale (Rate of Perceived Exertion)
```
RPE 7  = Could do 3 more reps (3 RIR)
RPE 8  = Could do 2 more reps (2 RIR)
RPE 9  = Could do 1 more rep (1 RIR)
RPE 10 = Absolute failure (0 RIR)
```

### Common Protocol Definitions
- **Loaded Stretch**: Hold at stretched position 30s on final set
- **FST-7**: 7 sets x 8-12 reps, 30s rest
- **Eccentric Overload**: Slow negatives (4-5s) under heavy load
- **BFR**: Bands at 40-50% occlusion, lighter load, higher reps
- **Constant Tension**: No lockout, no rest at top/bottom

## HTML/CSS Template Pattern

**Key styling principles for workout documents:**
```css
/* Print-optimized */
@page { size: letter; margin: 0.5in; }
body { font-size: 9pt; line-height: 1.3; }

/* Hierarchy */
.section-title { 
    font-size: 11pt; 
    font-weight: 700; 
    border-bottom: 2px solid #000; 
}

/* Exercise tables */
table { 
    font-size: 8.5pt; 
    border-collapse: collapse; 
}
table th { 
    background: #1a1a1a; 
    color: white; 
    font-weight: 700; 
}

/* Grid layouts for multi-column sections */
.two-col { 
    display: grid; 
    grid-template-columns: 1fr 1fr; 
    gap: 16px; 
}

/* Avoid page breaks inside sections */
.section { page-break-inside: avoid; }
```

## Document Structure

**Tactical one-pager layout:**
1. **Header** - Program name, client, goal, duration
2. **Overview** - Quick stats (split, equipment, program type)
3. **Weekly Split** - 7-day training calendar
4. **Protocol Definitions** - Advanced techniques explained
5. **Sample Workout** - Full day with exercise table
6. **Guidelines** - Sets/reps/intensity by day type
7. **Progression Scheme** - Week-by-week periodization
8. **Quick Reference** - Notation guides, scales, timing
9. **Execution Reminders** - Key tactical checkpoints

## Google Sheets — Merge Note Rows

When a workout spreadsheet has single-cell "Note:" rows that span across a multi-column table, the row height clamps awkwardly because the text only occupies column A while B–F are empty. Fix: merge the note row horizontally across all columns via Sheets API `mergeCells`.

```python
# Merge a note row across columns A–F (0-indexed row)
requests = [{
    'mergeCells': {
        'range': {
            'sheetId': SHEET_ID,
            'startRowIndex': row_idx,   # 0-indexed
            'endRowIndex': row_idx + 1,
            'startColumnIndex': 0,
            'endColumnIndex': 6         # A through F
        },
        'mergeType': 'MERGE_ALL'
    }
}]
service.spreadsheets().batchUpdate(spreadsheetId=SPREADSHEET_ID, body={'requests': requests}).execute()
```

**Finding note rows programmatically:**
```python
# Note rows = single-cell rows where content starts with 'Note:' or is a lone string
rows = service.spreadsheets().values().get(
    spreadsheetId=SPREADSHEET_ID, range='Training!A1:F65'
).execute().get('values', [])

note_row_indices = [i for i, row in enumerate(rows) if row and len(row) == 1 and row[0].strip()]
```

**Blair Fitness Profile sheet IDs (active project):**
- Spreadsheet ID: `1kz1XlSb6a0zG6FaJyVLD3MWY6inCTSTEhhYdlAeTvPA`
- Training tab sheetId: `52799403`
- Assessment tab sheetId: `2137559030`
- Nutrition tab sheetId: `1102946294`

## Google Sheets — Merging Single-Cell Rows

When a workout spreadsheet has header/note rows that span only column A (single-cell), they clamp row height awkwardly. Fix: merge them horizontally across all columns.

**Pattern: merge all single-cell rows in one batch**
```python
import sys
sys.path.insert(0, '/home/hermes/.hermes/skills/productivity/google-workspace/scripts')
import google_api

creds = google_api.get_credentials()
from googleapiclient.discovery import build
service = build('sheets', 'v4', credentials=creds)

SPREADSHEET_ID = '<sheet_id>'
SHEET_ID = <tab_sheet_id>  # from spreadsheets().get() metadata

# 0-indexed row indices to merge (convert from 1-indexed row numbers)
rows_to_merge = [0, 1, 6, 7, 18, ...]  # all header/note/phase rows

requests = [
    {
        'mergeCells': {
            'range': {
                'sheetId': SHEET_ID,
                'startRowIndex': row_idx,
                'endRowIndex': row_idx + 1,
                'startColumnIndex': 0,
                'endColumnIndex': 6   # A through F — match your column count
            },
            'mergeType': 'MERGE_ALL'
        }
    }
    for row_idx in rows_to_merge
]

service.spreadsheets().batchUpdate(
    spreadsheetId=SPREADSHEET_ID,
    body={'requests': requests}
).execute()
```

**How to identify rows that need merging:**
```python
# Always scan beyond expected rows — use A1:F200 to catch late-sheet additions
result = service.spreadsheets().values().get(
    spreadsheetId=SPREADSHEET_ID,
    range='Training!A1:F200'  # never cap at a fixed row — sections get added at the bottom
).execute()

for i, row in enumerate(result.get('values', []), 1):
    if len(row) == 1 and row[0].strip():
        print(f'Row {i} (0-indexed {i-1}): {row[0][:60]}')
```

⚠️ **Pitfall:** Scanning a fixed range (e.g. A1:F65) misses rows added below. Blair's Pilates/Active Recovery section (rows 72–73) was missed on first pass for this reason. Always use a generous upper bound.

⚠️ **Pitfall:** Run the merge check on **every tab**, not just Training. Blair's Nutrition tab had the same issue (14 unmerged single-cell rows including section headers and all FOODS TO LIMIT bullet rows). Apply the same scan + merge + left-align pattern to Assessment, Training, and Nutrition in one pass.

**Blair Fitness Profile — Nutrition tab merged rows (July 2026):**
- Row 7: `DAILY MACRO BREAKDOWN — TRAINING DAY`
- Row 16: `REST DAY MACROS`
- Row 23: `MACRO RATIONALE`
- Row 24: Macro rationale body text
- Row 26: `FOOD SOURCE GUIDANCE`
- Row 32: `FOODS TO LIMIT / AVOID`
- Rows 33–39: Bullet items (all single-cell)
- Row 41: `SUPPLEMENT STACK`

**Alignment rule:** merged single-cell rows must always be **left-aligned**. After merging, apply a `repeatCell` request setting `horizontalAlignment: LEFT` across the same row range. Centered text on these rows is wrong.

```python
requests += [
    {
        'repeatCell': {
            'range': {
                'sheetId': SHEET_ID,
                'startRowIndex': r,
                'endRowIndex': r + 1,
                'startColumnIndex': 0,
                'endColumnIndex': 6
            },
            'cell': {'userEnteredFormat': {'horizontalAlignment': 'LEFT'}},
            'fields': 'userEnteredFormat.horizontalAlignment'
        }
    }
    for r in rows_to_merge
]
```

**Blair Fitness Profile — Training tab merged rows (July 2026):**
- Rows 1–5: client metadata (name, goal, duration, days, location)
- Rows 7–8, 10–12: Phase 1 & 2 headers + focus notes
- Rows 14–16: Progressive overload method + rules
- Rows 19, 29, 39, 50, 62: Day headers (DAY 1 through DAY 5)
- Rows 40, 51: Mid-day note rows

## Pitfalls

### Data Extraction
- **Truncated JSON**: Large data files may have truncated arrays. Check total length and use pagination if needed.
- **Multi-section data**: Fitness programs often split across "Training Program", "Overview", "Toning", "Nutrition" tabs. Synthesize from all relevant sections.
- **Persona integration**: For authentic nutrition guides, cross-reference "Nutrition" tab with persona interview answers (breakfast details, social tactics, food preferences). Real client data beats generic templates.
- **Incomplete workouts**: If only Day 1 is present, note it's representative and extrapolate weekly structure from split definition.

### PDF Generation
- **Chromium errors**: DBus/accessibility warnings are normal and don't affect output. Check for "bytes written to file" confirmation.
- **ReportLab HOME errors**: If ReportLab fails with "Could not determine home directory", fall back to HTML + Chromium headless approach (see references/pdf-conversion.md).
- **Missing tools**: Always have fallback format (HTML is universally viewable). PDF is enhancement, not requirement.
- **Page breaks**: Use `page-break-inside: avoid` on sections to prevent awkward splits.

### Formatting
- **Scannable ≠ verbose**: Use tables, grids, bullet points. Avoid paragraph-heavy layouts.
- **WhatsApp context**: If delivering via WhatsApp, avoid markdown. Use plain text or note "MEDIA:<path>" for native file sending.
- **Font sizing**: 8.5-9pt body, 11pt headings for single-page fit. Test print preview.

## Example Workflow

```python
# 1. Extract data
with open('client_data.json', 'r') as f:
    data = json.load(f)

training = data.get('Training Program', [])
overview = data.get('Overview', [])
toning = data.get('Toning', [])

# 2. Identify key sections
# - Weekly split from overview or training section
# - Exercise details with sets/reps/tempo/RPE
# - Protocol definitions
# - Progression scheme

# 3. Create HTML with CSS grid layout
# - Use tables for exercises
# - Use grids for multi-column sections
# - Include quick reference boxes

# 4. Convert to PDF
# chromium-browser --headless --print-to-pdf=output.pdf input.html

# 5. Create supporting text versions for reference
```

## Success Criteria

- **One-page fit** (or max 2 pages for comprehensive programs)
- **Scannable layout** with clear visual hierarchy
- **Complete programming** (sets, reps, tempo, RPE, protocols)
- **Tactical content** (execution reminders, progression rules)
- **Multi-format delivery** (PDF primary, HTML viewable, text backup)
- **Print-ready** (proper margins, page breaks, font sizing)

## Seattle Workout Series (Active project — June 2026)

A Canva e-book (`DAHFfAiLO3E`, 13 pages) targeting Seattle 9-to-5 workers aged 22–35.
Story arc: workout → local Seattle gym → nearby café for post-workout → nutrition guide at the end.
Tanzim's authority: national championship coach, ~15 gold medals, 4 overall wins (Bangladesh).
See `canva-integration` skill and its `references/seattle-workout-series.md` for full brief.

**Workflow for this project:** Always start by reading the Canva design via API (not browser — browser times out on Canva). Audit all 13 pages, identify gaps, then draft missing content. Tanzim pastes into Canva, or use Canva API write endpoints if available.

## Support Files

- **references/pdf-conversion.md** - Chromium headless commands, tool alternatives, troubleshooting
- **templates/workout-onepager.html** - HTML/CSS template with print-optimized styling
- **references/timbr-product-decisions.md** - Timbr PRD decisions: answered questions, wearable architecture, periodisation data model, plan generation engine logic, workout logging UX decisions (Feature 1 v0.4.1)

## Related Skills

- Data extraction from JSON/spreadsheets
- HTML/CSS document styling
- PDF generation and conversion
- Content synthesis from multiple sources
