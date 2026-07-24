# Color Extraction from Reference Screenshots

When extracting colors from reference screenshots for UI mockups, use pixel-frequency analysis — not visual guessing.

## The Problem

Visual inspection leads to wrong colors. In this session:
- Guessed #F0D830 (too saturated yellow)
- Guessed #C8A84C (wrong hue)  
- Guessed #D8B47C (too light)

Actual dominant gold from Robinhood refs: **#A88860** (H=33° S=29% L=52%)

## Correct Workflow

### 1. Extract ALL colors by frequency

```python
from PIL import Image
from collections import Counter

def extract_palette(path):
    img = Image.open(path).convert('RGB')
    pixels = [img.getpixel((x, y)) for y in range(img.height) for x in range(img.width)]
    
    # Bucket to reduce noise (group similar colors)
    def bucket(rgb): return (rgb[0]//4*4, rgb[1]//4*4, rgb[2]//4*4)
    
    counts = Counter(bucket(p) for p in pixels)
    return counts.most_common(30)
```

### 2. Filter by HSL to isolate color families

```python
import colorsys

def filter_golds(counts):
    """Extract gold/amber colors: H=25-50°, S>20%, L>30%"""
    golds = []
    for (r, g, b), count in counts:
        h, l, s = colorsys.rgb_to_hls(r/255, g/255, b/255)
        h_deg, s_pct, l_pct = h*360, s*100, l*100
        
        if 25 <= h_deg <= 50 and s_pct > 20 and l_pct > 30:
            golds.append(((r, g, b), count, h_deg, s_pct, l_pct))
    
    return sorted(golds, key=lambda x: -x[1])  # Sort by frequency
```

### 3. Use the MOST FREQUENT color

Don't pick the brightest or most saturated — pick the one with highest pixel count. That's the actual palette color, not an edge artifact or highlight.

## Verified Robinhood Palette (June 2025)

From pixel analysis of actual Robinhood screenshots:

| Element | Hex | HSL | Notes |
|---------|-----|-----|-------|
| Primary gold | #A88860 | H=33° S=29% L=52% | Bronze-amber, NOT yellow |
| Background | #0C0804 | H=30° S=50% L=3% | Warm black, NOT pure #000 |
| Cards | #1C1814 | H=30° S=17% L=9% | Warm dark gray |
| Cream text | #E0DCD8 | H=30° S=11% L=86% | NOT pure white |
| Muted text | #686460 | H=30° S=4% L=39% | |

Key insight: Robinhood has a **warm 30° hue tint** across the entire palette — backgrounds, text, accents all share this warmth.
