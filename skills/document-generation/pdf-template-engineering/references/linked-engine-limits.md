# Linked Engine Template Limits

Specific hard limits for Tanzim's LinkedIn article PDF generator (Linked_Engine).

## Character Limits (v2.1)

| Field | Max Chars | Notes |
|-------|-----------|-------|
| TITLE_LINE1 | 70 | First title line, 22pt bold |
| TITLE_LINE2 | 60 | Second title line, 22pt |
| SUBTITLE | 120 | Single line preferred |
| SECTION_TEXT | 280 | ~3 lines at 9pt, 4 sections max |
| GET_STARTED item | 85 | 5 items max, numbered list |
| KEY_TAKEAWAY item | 95 | 3 items max, arrowed list |
| ECON_INTRO | 100 | Economics block intro |
| ECON_TAKEAWAY | 100 | Economics block takeaway |
| TABLE_CELL | 25 | 3 rows max |

## Layout Constants

- Page: US Letter (612 x 792 pts)
- Margins: 40pt left/right
- Footer bar: 22pt height
- GAP (line spacing): 14 (default, can range 13-22)
- Safe padding: 16pt above footer

## Guarantee

If all limits are met → output is ALWAYS 1 page, layout never breaks.

## Repo

`github.com/tanzimozer/Linked_Engine` — v2.1 has limits enforced in `enforce_limits()`.
