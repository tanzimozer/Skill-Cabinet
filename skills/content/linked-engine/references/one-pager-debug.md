# One-Pager Debug — Session Notes (May 27 2026)

## The invariant
Engine enforces exactly 1 page. If `_verify_staging` raises `RuntimeError: PDF has N pages` the batch is aborted with no tracker/CSV changes — safe to re-run with the same batch ID.

## Root cause found this session
**TITLE_LINE1 was 610pt wide on a 532pt canvas.** ReportLab's `drawString` doesn't word-wrap — it just overflows. The header drew off the right edge, consuming extra vertical space on wrap, cascading the whole article over the page boundary.

Width check before writing any title:
```python
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os
font_path = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"
if os.path.exists(font_path):
    pdfmetrics.registerFont(TTFont("Arial-Bold", font_path))
w = pdfmetrics.stringWidth("Your Title Here", "Arial-Bold", 22)
print(f"{w:.1f}pt — limit 532pt — {'OK' if w <= 532 else 'TOO LONG'}")
```
Safe rule: TITLE_LINE1 ≤ ~40 chars, TITLE_LINE2 ≤ ~55 chars at 22pt bold.

## Secondary cause: GAP=14 too tight for full article
With 4 sections + ECON block + GET_STARTED + KEY_TAKEAWAYS, GAP=14 leaves ~2.5pts of headroom. Last KEY_TAKEAWAY line triggered page break at y=51 (floor=38, need=15.5 → result=35.5).

**Fix: GAP=12** — saves ~14pts across 7 blocks. Confirmed working.

## Diagnostic monkey-patch recipe
```python
import sys
sys.path.insert(0, '/home/hermes/Linked_Engine')
import linked_engine as le

# Find where page break fires
page_breaks = []
orig = le.Layout.page_break
def traced(self):
    page_breaks.append(self.y)
    print(f"PAGE BREAK at y={self.y:.1f}")
    orig(self)
le.Layout.page_break = traced

# Find exact trigger line
space_log = []
orig_space = le.Layout.space
def logged(self, need_h):
    if self.y < 100:
        result = self.y - need_h
        space_log.append((need_h, self.y, result))
    orig_space(self, need_h)
le.Layout.space = logged

# Suppress side effects for diagnosis
le._verify_staging = lambda *a, **kw: None
le.log_post_row = lambda *a, **kw: None
le.register_article = lambda *a, **kw: None

le.generate()

print("Space requests near floor:")
for need, y, result in space_log:
    flag = "← PAGE BREAK" if result < 38 else ""
    print(f"  need={need:.1f} at y={y:.1f} → {result:.1f} {flag}")
```

## Confirmed safe config (full article, all blocks)
- `GAP = 12`
- TITLE_LINE1 ≤ 40 chars
- TITLE_LINE2 ≤ 55 chars
- SECTIONS: ~50 words each (not 60)
- GET_STARTED items: ≤75 chars each (spec says 85 but tighter is safer)
- ECON table: ≤3 rows, short cell text to avoid row wrapping
- KEY_TAKEAWAYS: ≤80 chars each

## Trim order when still overflowing
1. Shorten titles first (biggest impact, no content loss)
2. GAP 14→12 (free ~14pts)
3. Trim longest SECTIONS text
4. Trim GET_STARTED item text
5. Reduce ECON table cells
