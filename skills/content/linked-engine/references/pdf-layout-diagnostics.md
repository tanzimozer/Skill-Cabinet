# PDF Layout Diagnostics

## When user reports "template broke" or "margins violated"

### Step 1: PyMuPDF margin scan
```python
import fitz

doc = fitz.open('output/LE###/filename.pdf')
page = doc[0]

MARGIN_L = 40
MARGIN_R = 572  # PAGE_W - MARGIN_L = 612 - 40

violations = []
for b in page.get_text('dict')['blocks']:
    for line in b.get('lines', []):
        for span in line['spans']:
            bbox = span['bbox']
            if bbox[0] < MARGIN_L:
                violations.append(f"LEFT: {span['text'][:40]} at x={bbox[0]:.1f}")
            if bbox[2] > MARGIN_R:
                violations.append(f"RIGHT: {span['text'][:40]} at x={bbox[2]:.1f}")

print(f"Violations: {len(violations)}")
for v in violations:
    print(f"  ⚠️ {v}")
```

### Step 2: Check PNG edge colors
If user shows screenshot with dark border — check if it's from template or viewing app:

```python
from PIL import Image

# Check my generated PNG
img = Image.open('output/LE###/filename.png')
w, h = img.size

# Sample corners
positions = [
    ('top-left', (5, 5)),
    ('top-right', (w-5, 5)),
    ('bottom-left', (5, h-5)),
    ('bottom-right', (w-5, h-5)),
]

for name, (x, y) in positions:
    print(f"{name}: {img.getpixel((x, y))}")

# If corners show expected BG_COLOR → dark border is from viewer app, not template
```

### Step 3: Content bounds check
```python
import fitz

doc = fitz.open('output/LE###/filename.pdf')
page = doc[0]

blocks = page.get_text('dict')['blocks']
lowest_y = min(b['bbox'][1] for b in blocks if 'lines' in b)
highest_y = max(b['bbox'][3] for b in blocks if 'lines' in b)

print(f"Content spans Y: {lowest_y:.1f} to {highest_y:.1f}")
print(f"Page height: {page.rect.height}")
print(f"Footer starts at: 22 (FOOTER_BAR_H)")
print(f"Safe floor: 38 (22 + 16 SAFE_PAD)")

if highest_y < 38:
    print("⚠️ Content too close to footer!")
```

## Common issues

### Dark border in screenshot
**Cause:** iOS/Google Drive/WhatsApp preview letterboxing a portrait image.
**Verify:** Check PNG edge pixels — if they match BG_COLOR, border is external.
**Fix:** None needed — template is correct.

### Title overflowing right margin
**Cause:** TITLE_LINE1 or TITLE_LINE2 too long for 532pt usable width.
**Fix:** v2.2+ uses `wrap_text()` for titles. Pre-v2.2: manually shorten title.

### Two-page PDF
**Cause:** Accumulated content height exceeded floor limit.
**Fix:** See main skill — reduce GAP, trim sections, shorter GET_STARTED items.

## Standalone verify script
See `scripts/verify_pdf.py` for a comprehensive verification tool.
