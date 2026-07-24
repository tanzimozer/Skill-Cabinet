---
name: trainee-program-pdf
description: Generate professional dark-themed fitness program PDFs for trainees using fpdf2, with matching Google Sheets Overview tabs
version: "1.0"
triggers:
  - PDF program
  - transformation plan PDF
  - create program document
  - trainee PDF
  - program overview sheet
---

# Trainee Program PDF Generation

Generate professional fitness program PDFs with dark theme and Google Sheets Overview tabs.

## PDF Structure (7 pages)

1. **Cover** - Dark bg, trainee name, program duration, key stats (bodyweight, calories, protein, split), phase timeline with color coding
2. **Phase Overview** - Macro table by phase, refeed rules, non-negotiables (3 columns: Protein/Carbs/Avoid)
3. **Training Day** - Meal cards with supplements inline, carb timing callout
4. **Rest Day** - Same structure, different carb distribution
5. **Training Program Day 1 & 2** - Exercise tables with tempo/RPE/protocol
6. **Training Program Day 3 & 4** - Exercise tables + weekly volume + key reminders
7. **Peak Week** - Carb reload, peak day sequence, water protocol, full supplement cheatsheet

## Design System

```python
# Palette
DARK       = (15, 15, 15)      # Background
CARD_BG    = (26, 26, 26)      # Card backgrounds
WHITE      = (255, 255, 255)
GREY_LIGHT = (200, 200, 200)
GREY_MID   = (140, 140, 140)
GREY_DARK  = (70, 70, 70)
TEAL       = (34, 95, 107)     # Primary accent
TEAL_LIGHT = (220, 242, 246)   # Callout bg
ORANGE     = (220, 128, 32)    # Supplement headers
AMBER      = (190, 148, 40)    # Refeed callouts

# Phase colors (index 0-4)
PHASE_COLORS = [
    (38, 120, 100),   # P1 teal-green
    (60,  95, 165),   # P2 blue
    (160, 100, 35),   # P3 amber
    (120, 50, 155),   # P4 purple
    (185, 50,  60),   # P5 red
]
```

## Layout Rules

- **Margins**: 12mm all sides (compact)
- **Page break threshold**: 278mm (auto page break at margin=12)
- **Section bars**: 5.5pt height, dark bg, white text
- **Meal cards**: Left teal accent border (1.5px), supplements in ORANGE
- **Callouts**: Full width, left colored border (2px), light bg
- **Tables**: Alternating row colors ROW_A=(248,248,248), ROW_B=(237,237,237)

## Key Components

### meal_card(title, tag_text, foods, supps)
- Dark section bar header
- Foods as bullet list (7pt)
- Supplements section in orange if present
- Left teal accent border

### training_table(day_title, mobility, exercises)
- Dark header bar
- Mobility note in italic
- 6-column table: #, EXERCISE, SETS x REPS, RPE, TEMPO, PROTOCOL
- Exercise notes in smaller italic text

### callout(text, border_color, bg_color)
- Full-width box with left accent border
- Used for carb timing rules, protocol rules, warnings

## Google Sheets Overview Tab

Mirror PDF structure exactly with page dividers:
- Use `═══...═══` separators with `PAGE N: TITLE` headers
- Same data, same order
- Column widths: A=200, B=200, C=100, D=60, E=60, F=150
- Dark headers, phase-colored rows, orange supplement names
- Lock as "Template-1" when finalized

## File Locations

- PDF output: `/home/hermes/[Name]_T1_Program.pdf`
- Generation script: `/tmp/[name]_pdf.py`
- Trainee profile: `/home/hermes/trainees/[name]_profile.md`
- Supplements: `/home/hermes/trainees/[name]_supplements.md`

## Dependencies

```python
import sys
sys.path.insert(0, '/home/hermes/.local/lib/python3.12/site-packages')
from fpdf import FPDF
from fpdf.enums import XPos, YPos
```

## Character Encoding

Always sanitize text for latin-1:
```python
def c(s):
    repl = {'\u2013':'-','\u2014':'-','\u2019':"'",'\u2018':"'",
            '\u201c':'"','\u201d':'"','\u2022':'-','\u2192':'->',
            '\u00d7':'x','\u2248':'~','\u2264':'<=','\u2265':'>='}
    for u,a in repl.items(): s = s.replace(u,a)
    return s.encode('latin-1','replace').decode('latin-1')
```

## Reference Implementation

See `/tmp/blair_v3.py` for full working example (30KB, 7 pages).
