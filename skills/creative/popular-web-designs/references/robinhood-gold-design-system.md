# Robinhood Gold — Design System Reference

Extracted from two sessions with Tanzim building Timbr (fitness app mockup) using Robinhood's own app screenshots as the pixel source. Deep pixel analysis run on 6 reference screenshots (Net Worth, Family, Gold Card, Move Money, Virtual Cards, Banking APY) — June 2026.

---

## Colour Palette — PIXEL-VERIFIED (June 2026 deep extraction)

```css
:root {
  /* BACKGROUNDS — from pixel analysis */
  --bg:    #000000;   /* Pure black (23-27% of each screen) */
  --s1:    #0C0C08;   /* Warm black H=60° S=20% L=4% */
  --s2:    #181814;   /* Card surfaces H=60° S=9% L=9% */
  --s3:    #1C1814;   /* Elevated elements H=30° S=17% L=9% */
  --bdr:   #201E1A;   /* Borders — SOFT, near invisible */
  --bdr2:  #282420;   /* Lighter borders */

  /* GOLD — EXACT from deep pixel analysis (H=43°, NOT H=33°) */
  /* Previous value #C9A84C was WRONG — too bright, wrong hue */
  --gold:        #A89462;   /* PRIMARY: H=42.9° S=28.7% L=52.2% — 2,036px */
  --gold-dark:   #887447;   /* DARK: H=41.9° S=31.0% L=40.7% — Move Money avg */
  --gold-light:  #BFAA73;   /* LIGHT: H=43.4° S=37.3% L=60.0% — highlights only */
  --gold-bright: #FFD600;   /* GLOW: H=50.4° S=100% L=50% — chart lines/glows only */
  --bronze:      #5C513B;   /* DARK: H=40.0° S=21.9% L=29.6% — 1,950px subtle */
  --bronze-muted:#5E533D;   /* MUTED: H=40.0° S=21.3% L=30.4% */

  /* Gold alpha variants */
  --gold2: rgba(168,148,98,0.12);
  --gold3: rgba(168,148,98,0.22);

  /* TEXT */
  --txt:   #E0DCD8;   /* Primary cream H=30° S=11% L=86% */
  --txt2:  #D8D8D4;   /* Secondary H=60° S=5% L=84% */
  --txt3:  #A09C98;   /* Muted H=30° S=4% L=61% */
  --txt4:  #686460;   /* Disabled H=30° S=4% L=39% */

  /* STATUS */
  --grn:   #22C55E;   /* Success/positive */
}
```

### Screen-by-screen gold averages (pixel count)

| Screen | Avg Gold Hex | Pixel Count | Notes |
|--------|-------------|-------------|-------|
| Gold Card | #B39F6C | 350,804 | Highest count — most gold-rich screen |
| Virtual Cards | #665841 | 102,870 | Darkest gold usage |
| Move Money | #887447 | 94,553 | Dark bronze range |
| Family Spending | #9F8860 | 39,466 | |
| Banking APY | #9A865F | 37,013 | |
| Net Worth | #86775C | 4,754 | Very sparse gold |

**Key insight:** Dominant hue is **H=43°** (yellow-gold), NOT H=33° (bronze). Previous reference had wrong hue. The gold reads darker than typical "fintech gold" — L=52% for primary vs L=60%+ for typical bright gold.

---

## Critical Corrections vs. Previous Reference

| Element | OLD (wrong) | NEW (pixel-verified) |
|---------|-------------|---------------------|
| Primary gold | `#C9A84C` | `#A89462` |
| Hue | H=33° (bronze) | H=43° (yellow-gold) |
| Lightness | L=60%+ (too bright) | L=52% (darker, richer) |
| Background | `#0F0F0F` | `#000000` (pure black) |
| Borders | Hard `#1F1F1F` | Soft `#201E1A` — near invisible |
| Card elevation | Box shadow heavy | MINIMAL — borders preferred, no drama |

---

## Typography

- **Font stack:** `'Open Sans', -apple-system, 'SF Pro Display', 'Helvetica Neue', sans-serif`
  - Open Sans is a good match for Robinhood Banking — clean, geometric, readable at small sizes
- **Pure sans-serif throughout** — no serifs anywhere
- Labels: `font-weight: 700`, `letter-spacing: 0.08em`, `text-transform: uppercase` (BALANCE, TOTAL, WT, REPS, SETS)
- Headings: `font-weight: 900`, tight
- Body: `font-weight: 500–600`

---

## Key Design Principles

1. **Pure `#000000` background** — not near-black, not warm black. Literal pure black.
2. **Gold is sparse** — labels, one accent line on charts, tier badges. Over-applying kills it.
3. **No red, purple, or blue** in the accent palette — Robinhood Banking is strictly black + gold + green (positive) + cream text. Any other color was not in the references.
4. **No decorative imagery** — zero 3D sculptures, no organic shapes, no gradients as decoration.
5. **Soft borders, not hard** — `#201E1A` not `#2A2A2A`. Cards use subtle shadow lift, not sharp outlines.
6. **Gold text on dark bg** — NOT white. Primary text is warm cream `#E0DCD8`.

---

## Navigation Bar (Robinhood Banking style)

```css
.bottom-nav {
  background: #000000;
  border-top: none;
  box-shadow: 0 -1px 0 rgba(255,255,255,0.04);
  height: 82px;
}
.nav-item { position: relative; padding-top: 6px; }
.nav-dot {
  width: 4px; height: 4px;
  border-radius: 50%;
  background: var(--gold);   /* #A89462 */
  position: absolute; top: 0; left: 50%;
  transform: translateX(-50%);
}
/* Active: gold icon + gold label + gold dot above */
/* Inactive: #686460 icon + #686460 label, no dot */
```

**Icons:** Clean SVG line icons (22px), NOT emoji. Stroke weight 1.5px.

---

## Airbnb Design Principles (applied to dark themes)

When user asks to apply "Airbnb aesthetics" to a dark/gold mockup:

- **Elevation over hard borders** — `box-shadow` lifts cards, remove `border: 1px solid`
- **Pill CTAs** — `border-radius: 100px` on all primary action buttons
- **Softer card surfaces** — remove border, add `box-shadow: 0 2px 20px rgba(0,0,0,0.45)`
- **Warmer bg** — `#0A0806` instead of pure `#000000` (slight warmth)
- **Bottom sheets** — `border-radius: 28px 28px 0 0`, shadow-only separation
- **Font:** Airbnb Cereal → substitute with `Open Sans` or `DM Sans` (NOT Nunito — user reverted Nunito)
- **DO NOT change fonts** unless user explicitly asks — font changes get reverted

---

## Pixel Color Extraction Method

When user provides reference screenshots and asks for exact color matching:

```python
from PIL import Image
from collections import Counter
import colorsys

def extract_gold_range(path, name):
    """Extract H=30-55° range pixels — the gold band"""
    img = Image.open(path).convert('RGB')
    pixels = list(img.getdata())
    gold_pixels = []
    
    for r, g, b in pixels:
        h, s, v = colorsys.rgb_to_hsv(r/255, g/255, b/255)
        hue = h * 360
        sat = s * 100
        val = v * 100
        # Gold range: H=30-55°, S>15%, V>20%
        if 30 <= hue <= 55 and sat > 15 and val > 20:
            gold_pixels.append((r, g, b))
    
    # Find most common
    counter = Counter(gold_pixels)
    top = counter.most_common(10)
    
    print(f"\n{name}: {len(gold_pixels)} gold pixels")
    for (r,g,b), count in top[:5]:
        h,s,v = colorsys.rgb_to_hsv(r/255,g/255,b/255)
        print(f"  #{r:02X}{g:02X}{b:02X} — H={h*360:.1f}° S={s*100:.1f}% L={((2-s)*v/2)*100:.1f}% — {count}px")
```

**Process:** Run on each reference screenshot → compare pixel counts → use the highest-count gold from the most gold-rich screen (Gold Card = best source) → cross-check against screen averages.

---

## Google Sheets Integration

For TIMBR color specs: https://docs.google.com/spreadsheets/d/1qy5VKdbi7Antrj-7yNk65ERdB4G4p1o672jZLH-_eLw

---

## Catalogue Note

Robinhood Gold is not in the main template catalogue — used as a **design language source** applied to Timbr. Keep this reference for future "Robinhood-inspired" or "fintech dark gold" requests.

Closest catalogue alternatives: `revolut.md`, `kraken.md`.
