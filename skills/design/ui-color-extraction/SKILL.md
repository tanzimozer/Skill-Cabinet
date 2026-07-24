---
name: ui-color-extraction
description: Extract precise color palettes from reference screenshots for UI design
version: 1
---

# UI Color Extraction

Extract exact color palettes from reference screenshots using pixel analysis, then apply to mockups.

## Workflow

1. **Receive reference screenshots** — wait for ALL references before proceeding
2. **Extract colors** — use Python PIL to analyze pixel frequencies
3. **Document specs** — populate Google Sheet with hex, HSL, and usage notes
4. **Build mockup** — apply extracted palette to HTML/CSS
5. **Deliver** — drop files to appropriate group chat

## Extraction Script

```python
from PIL import Image
import colorsys
from collections import Counter

def extract_palette(path, name):
    img = Image.open(path).convert('RGB')
    width, height = img.size
    
    all_pixels = []
    for y in range(height):
        for x in range(width):
            all_pixels.append(img.getpixel((x, y)))
    
    def bucket(rgb):
        return (rgb[0]//4*4, rgb[1]//4*4, rgb[2]//4*4)
    
    counts = Counter(bucket(p) for p in all_pixels)
    
    # Categorize by lightness and hue
    backgrounds = []  # L < 15%
    accents = []      # Specific hue range (e.g., gold H=20-55°)
    text = []         # L > 80%
    
    for (r, g, b), count in counts.items():
        h, l, s = colorsys.rgb_to_hls(r/255, g/255, b/255)
        h_deg, s_pct, l_pct = h*360, s*100, l*100
        
        if l_pct < 15:
            backgrounds.append(((r,g,b), count, h_deg, s_pct, l_pct))
        elif 20 <= h_deg <= 55 and s_pct > 15 and l_pct > 25:
            accents.append(((r,g,b), count, h_deg, s_pct, l_pct))
        elif l_pct > 80:
            text.append(((r,g,b), count, h_deg, s_pct, l_pct))
    
    return {
        'backgrounds': sorted(backgrounds, key=lambda x: -x[1])[:5],
        'accents': sorted(accents, key=lambda x: -x[1])[:10],
        'text': sorted(text, key=lambda x: -x[1])[:5]
    }
```

## Output Format for Google Sheet

| CATEGORY | NAME | HEX | HSL | USAGE |
|----------|------|-----|-----|-------|
| BACKGROUNDS | Pure Black | #000000 | H=0° S=0% L=0% | Primary background |
| GOLD PRIMARY | Main Gold | #B09C68 | H=43° S=31% L=55% | Primary accent |
| TEXT | Primary Text | #E0DCD8 | H=30° S=11% L=86% | Body text |

## Key Learnings

### Robinhood Gold (reference)
The Robinhood "gold" is actually a warm bronze-amber, NOT saturated yellow:
- **Primary:** #B09C68 (H=43° S=31% L=55%)
- **NOT:** #F0D830 or #C8A84C (too yellow/saturated)

### Common Pitfalls
1. **Don't guess colors** — always extract from actual screenshots
2. **Wait for all references** — user may send multiple screenshots
3. **Document to Sheet first** — confirm colors before building
4. **Use pixel frequency** — most common colors are the design system colors
5. **ONLY use colors that exist in the references** — if there's no red/purple/blue in the screenshots, don't add them. Do NOT invent accent colors, status colors, or "nice to have" colors. Extract what's there, nothing more.
6. **Prefer the darker range** — when a color (e.g., gold) appears at multiple lightness levels, default to the darker variants (L=40-52%) for primary use. Reserve the brightest values (L=60%+) for highlights/glows only. The user explicitly prefers this.
7. **Cross-match before applying** — after extraction, visually compare your chosen hex values against the reference. If it doesn't look the same, you picked wrong.

## Deep Analysis Script

For critical color matching where basic extraction isn't enough, use the deep analysis script:
- `scripts/deep_color_extract.py` — per-screen averaging, lightness sorting, middle-range recommendation

This was developed when basic pixel counting produced values that were "close but missing the spark" — the deep analysis extracts per-screen averages and recommends the middle-dark value, not the brightest.

## Support Files

- `references/robinhood-palette.md` — complete Robinhood Gold palette with pixel counts
- `scripts/deep_color_extract.py` — deep extraction with per-screen analysis

## Delivery

Use `whatsapp-group-file-drop` skill for dropping HTML/screenshots to group chats.
