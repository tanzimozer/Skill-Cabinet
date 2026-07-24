---
name: pil-radar-composite
category: creative
description: Rendering portrait-orientation team visuals — matplotlib polar radar + PIL card compositing. Covers axis labelling, score management, card layout, footer, and delivery.
---

# PIL Radar Composite

Class-level skill for building multi-person radar chart + card visuals in Python (matplotlib polar + PIL), delivered via WhatsApp bridge.

## Architecture

```
matplotlib polar axes  →  radar PNG in memory (BytesIO)
PIL composite canvas   →  title + radar + cards + footer assembled top-to-bottom
curl /send-media       →  WhatsApp delivery
```

## Canvas height formula — compute explicitly, not magic numbers
```python
TITLE_H  = 70
RADAR_H  = 1180
SPACER   = 60
GAP      = 18
CARD_H   = 720
FOOTER_H = 80
H = TITLE_H + RADAR_H + SPACER + GAP + CARD_H + GAP + FOOTER_H
```
Never hard-code H — derive it from components so dead space is impossible.

## Radar axis labels — multiline pitfall

**CRITICAL:** When writing multiline axis labels in Python source, use a **real string literal with `\n`**, NOT the escape sequence inside a patch/sed replacement. The `patch` tool double-escapes `\n` to `\\n`, producing a literal backslash-n on the rendered chart.

**Wrong (via patch tool):**
```python
"Fitness\\nDomain",   # renders as "Fitness\nDomain" — literal backslash
```

**Correct — use sed for this specific edit:**
```bash
sed -i 's/"Fitness\\\\nTraining"/"Fitness\\nDomain"/' script.py
```
Or write the label directly in the source file with a real newline in the string.

**Verification:** After any axis label change, `grep` the file and confirm only `\n` (single backslash-n) appears, not `\\n`.

## Score array index map (13-axis standard)
```
[0]  AI / ML
[1]  Backend
[2]  Mobile Dev
[3]  Frontend
[4]  Data & Analytics
[5]  Product Strategy
[6]  Marketing
[7]  Sales
[8]  Growth
[9]  Leadership
[10] Fitness Domain
[11] Athlete
[12] Cinematography
```
Always cross-check index positions before patching a score. Count from 0.

## Sync rule: axis label ↔ card domain tag
When an axis label is renamed, the matching domain tag in `cards_data[n]["tags"]` must be updated in the same edit. They are separate strings and will silently diverge otherwise.

## Radar rotation
```python
ax_radar.set_theta_offset(np.pi / 2 + np.pi / N)  # half-spoke offset for N axes
```
Prevents label collision at 12 o'clock and 6 o'clock with 13+ axes.

## Radar rendering — title in PIL, not matplotlib
Draw the title on the PIL canvas, not as a matplotlib suptitle/title. matplotlib title eats into figure space and causes label clipping at the edges.

```python
# In matplotlib: NO title — full figure for radar
fig = plt.figure(figsize=(W/150, RADAR_H/150), dpi=150, facecolor='black')
ax_radar = fig.add_axes([0.08, 0.08, 0.84, 0.84], projection='polar')

# On PIL canvas: draw title manually
f_title = get_font(22, bold=True)
title_text = "FOUNDING TEAM  ·  SKILLS RADAR"
tw = draw_final.textlength(title_text, font=f_title)
draw_final.text(((W - tw) // 2, (TITLE_H - 22) // 2), title_text, fill=(255,255,255), font=f_title)
```

## Footer — white background, dark text
```python
FOOTER_H = 80
footer_y = H - FOOTER_H
draw_final.rectangle([0, footer_y, W, H], fill=(255, 255, 255))
f_footer = get_font(20, bold=True)
ft_w = draw_final.textlength(footer_text, font=f_footer)
if ft_w > W - GAP * 4:
    f_footer = get_font(17, bold=True)
    ft_w = draw_final.textlength(footer_text, font=f_footer)
text_y = footer_y + (FOOTER_H - 20) // 2
draw_final.text(((W - ft_w) // 2, text_y), footer_text, fill=(15, 15, 15), font=f_footer)
```

## Score update workflow
1. Read the current members array from the script
2. Write out the index map (above) and cross-check each named axis
3. Apply changes; verify by printing the updated line and reading indices aloud
4. Verify card domain tags still match any renamed axes

## Design constants (TIMBR team)
- Background: `#000000` pure black
- Tanzim colour: `#00c8f0` (cyan)
- Sagar colour: `#00d96b` (green)
- Waseem colour: `#ff6500` (orange)
- Fill opacity on polygons: 7% (`alpha=0.07`)
- Canvas width: 1240px, dpi: 150
- Font: DejaVuSans-Bold / DejaVuSans from `/usr/share/fonts/truetype/dejavu/`

## QC before delivery
Run a quick pixel check before sending:
```python
from PIL import Image
import numpy as np
img = Image.open('/path/to/output.png')
arr = np.array(img)
print('Non-black pixels:', (arr > 20).sum())
print('Footer avg RGB:', arr[-FOOTER_H:].mean(axis=(0,1)).round(1))
```
Footer avg RGB should be ~241 (white). Non-black count should be well above zero.
