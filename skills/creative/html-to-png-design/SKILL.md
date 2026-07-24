---
name: html-to-png-design
category: creative
description: Building investor-deck slides, infographics, and data visuals as HTML/CSS, then rendering to PNG via Playwright. Covers layout patterns, QC protocol, and common pitfalls.
triggers:
  - render html to png
  - design slide
  - investor deck
  - team slide
  - radar chart
  - skills visualisation
  - credential cards
  - html design
  - playwright screenshot
  - veronica qc
---

# HTML → PNG Design

## Why HTML/CSS over matplotlib/PIL
Matplotlib is unsuitable for layout work — spacing is unpredictable and text overlap is common. HTML + CSS gives pixel-perfect control. Always use this stack for anything that needs to look good.

## Stack
- **HTML/CSS** — layout, typography, colour
- **Chart.js 4.x** (CDN) — radar, bar, line charts
- **Playwright** — headless Chromium → PNG

## Playwright render pattern

```python
import asyncio
from playwright.async_api import async_playwright

async def render(html_path, png_path, width, height):
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={"width": width, "height": height})
        await page.goto(f"file://{html_path}", wait_until="networkidle")
        await page.wait_for_timeout(1800)   # let Chart.js finish drawing
        await page.screenshot(path=png_path, full_page=False)
        await browser.close()

asyncio.run(render("/abs/path/file.html", "/abs/path/out.png", 1080, 1350))
```

- `wait_until="networkidle"` — ensures CDN scripts load
- `wait_for_timeout(1800)` — Chart.js needs time to render
- Viewport must match `body { width: Xpx; height: Ypx; }` exactly

## Layout principles

### Dark-mode investor deck
- Body bg: `#080808`, card bg: `#111`, card border: `1px solid #1E1E1E`
- Body: `display:flex; flex-direction:column; overflow:hidden` — never use `min-height:100vh`
- Use fixed `height` on body, not `min-height`

### Cards that fill evenly (critical)
Flex cards with variable content produce large empty gaps if you use `flex:1` on an inner section.

**Correct pattern:**
```css
.card {
  display: flex;
  flex-direction: column;
  justify-content: space-between;  /* ← distribute space between sections */
}
.creds {
  padding: 0 18px;
  /* NO flex:1 here — that causes the gap */
}
```

**Wrong pattern (produces 40–50% empty void):**
```css
.creds { flex: 1; }  /* ← pushes everything else to the edges */
```

### Chart.js radar config
```js
options: {
  responsive: false,           // false = use canvas width/height attrs
  animation: { duration: 0 }, // no animation in headless render
  plugins: { legend: { display: false } },
  scales: {
    r: {
      min: 0, max: 10,
      ticks: { backdropColor: 'transparent', color: '#2A2A2A' },
      grid: { color: '#1E1E1E' },
      angleLines: { color: '#1E1E1E' },
      pointLabels: { font: { size: 10, weight: '600' }, color: '#4A4A4A' }
    }
  }
}
```

## Veronica QC Protocol

Run a browser_vision QC check before delivery. Ask:
1. Any text clipping or overflow?
2. Large empty gaps in cards?
3. All cards equal visual weight?
4. Chart labels readable?
5. Any element bleeding outside container?
6. Score out of 10 for deck readiness — target ≥ 8 before sending.

Iterate until QC passes. Common fixes:
- **Empty gaps** → `justify-content: space-between` on card, remove `flex:1` from content section
- **Unequal card weight** → add 1–2 more chips/tags to lighter card
- **Chart not rendering** → increase `wait_for_timeout`, check CDN loaded
- **Wrong dimensions** → viewport ≠ body size

## Delivery
After QC pass, use `whatsapp-media-delivery` skill (direct `/send-media` curl).  
Do NOT use `send_message` with `image::` prefix for WhatsApp — always fails.

## Chart.js Radar Centering Fix

Chart.js radar often drifts left when axis labels have unequal lengths. Fixes:

1. **Even padding on chart-wrap** — `padding: 20px` all sides (not asymmetric like `24px 30px 24px 10px`)
2. **Layout padding in options:**
   ```js
   layout: {
     padding: { left: 20, right: 20, top: 10, bottom: 10 }
   }
   ```
3. **Increase pointLabels padding** to `14` so labels don't crowd polygon edges
4. **Grid line visibility on dark bg** — use `rgba(255,255,255,0.08)` not hex dark values

If the chart is still drifting after these, set `canvas` width to slightly smaller than the wrap to give Chart.js more room to centre.

## Radar polygon fill opacity

On dark backgrounds, use `0.07–0.10` for `backgroundColor` on each dataset. Higher values cause a muddy dark blob at the centre where all three polygons overlap, obscuring individual edges.

---

## PIL/matplotlib Composite Pattern

For portrait-orientation team visuals combining a radar chart + card bios:

### Stack split
- **matplotlib** → radar PNG (rendered to BytesIO, pasted into PIL canvas)
- **PIL** → everything else: title, cards, footer

### Height calculation — always explicit, never derived
```python
TITLE_H  = 48
RADAR_H  = 1180
SPACER   = 60
GAP      = 18
CARD_H   = 580   # fit to content — measure first, don't guess
FOOTER_H = 80
H = TITLE_H + RADAR_H + SPACER + GAP + CARD_H + GAP + FOOTER_H
```
**Pitfall**: a fixed CARD_H that's too large leaves dead space at the bottom of every card. Use the empty-space scan (below) to calibrate.

### Roboto (or any system font) in both PIL and matplotlib
```python
import matplotlib.font_manager as fm
fm.fontManager.addfont("/usr/share/fonts/truetype/roboto/unhinted/RobotoTTF/Roboto-Regular.ttf")
fm.fontManager.addfont("/usr/share/fonts/truetype/roboto/unhinted/RobotoTTF/Roboto-Bold.ttf")
matplotlib.rcParams['font.family'] = 'Roboto'
```
PIL: pass full path to `ImageFont.truetype(path, size)`. Both must be set — they don't share state.

### sed path-mangling pitfall
When using `sed -i` to swap font paths, if the original path contains directory separators (`/`), sed will corrupt the replacement. Use Python patch tool instead, or use a different sed delimiter:
```bash
sed -i 's|DejaVuSans.ttf|roboto/unhinted/RobotoTTF/Roboto-Regular.ttf|g'  # use | not /
```

### sed score-patching pitfall — ambiguous matches
When patching a score array with sed, include enough surrounding values in the match to be unambiguous. Score values repeat across members, so a short match like `s/\[9, 5,/[9, 9,/` can match the wrong person.

**Safe pattern** — anchor on name colour or enough preceding values:
```bash
# Patch Waseem Backend (index 1): include colour string to anchor
sed -i 's/("Waseem Ahmad", "#ff6500", \[9, 5,/("Waseem Ahmad", "#ff6500", [9, 9,/' script.py
# After patching, always verify:
grep "Tanzim\|Sagar\|Waseem" script.py | head -3
```

**Even safer** — use the patch tool with full tuple lines rather than sed for score edits.

### Empty-space scan (run before shipping)
```python
from PIL import Image
import numpy as np
img = Image.open('output.png')
arr = np.array(img)
row_brightness = arr.mean(axis=(1,2))
in_gap = False; gaps = []; gap_start = 0
for i, b in enumerate(row_brightness):
    if b < 12 and not in_gap:
        in_gap = True; gap_start = i
    elif b >= 12 and in_gap:
        in_gap = False
        if i - gap_start > 15:
            gaps.append((gap_start, i, i - gap_start))
# Flag any gap > 15px as a layout error
```
Radar geometry produces expected dark regions (blank space between spokes) — these are not errors. Gaps > 40px outside the radar zone are real layout problems.

**Use `.mean(axis=(1,2))` not `.mean(axis=(1,2))` on a per-element comparison** — comparing a numpy array with `> 18` in a list comprehension raises `ValueError: The truth value of an array is ambiguous`. Use `np.where(row_brightness > 18)[0]` instead:
```python
content_rows = np.where(row_brightness > 18)[0]
top_pad = int(content_rows[0])
bot_pad = RADAR_H - int(content_rows[-1])
```

### Equalising radar north/south visual spacing
matplotlib embeds its own internal top/bottom padding inside the figure bounds — raw TITLE_H / SPACER values don't reflect what the eye sees. Measure actual content boundaries first:
```python
TITLE_H = 66; RADAR_H = 1180
radar_zone = arr[TITLE_H:TITLE_H+RADAR_H]
row_brightness = radar_zone.mean(axis=(1,2))
content_rows = np.where(row_brightness > 18)[0]
top_pad = int(content_rows[0])   # matplotlib's internal top margin
bot_pad = RADAR_H - int(content_rows[-1])  # matplotlib's internal bottom margin
# Visual north = TITLE_H + top_pad
# Visual south = SPACER  + bot_pad
# Set TITLE_H and SPACER so both visuals are equal
```
Typical matplotlib polar figure with 13 axes: internal top ~170px, internal bottom ~271px (101px asymmetry). Compensate by adding the difference to TITLE_H and reducing SPACER accordingly.

### Footer styling
- **White bar**: `draw.rectangle([0, footer_y, W, H], fill=(255,255,255))`
- **Dark text**: `fill=(15,15,15)`, Roboto Bold
- Centre text: `text_y = footer_y + (FOOTER_H - font_size) // 2`
- Do NOT use a divider line on a dark bg + white footer — the rectangle is the divider.

### Axis label newlines in matplotlib polar
Embed `\n` directly in the string — **not** `\\n`. Patch tools and `sed` can double-escape these:
```python
"Fitness\nDomain"   # correct — renders as two lines
"Fitness\\nDomain"  # wrong — renders as literal backslash-n
```
After any sed/patch operation on category strings, verify with `grep "Fitness" script.py` before running.

---

## References
- `references/timbr-team-slide.md` — approved TIMBR team radar slide spec (v25, July 2026)
