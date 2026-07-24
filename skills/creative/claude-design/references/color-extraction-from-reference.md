# Color Extraction from Reference Screenshots

When a mockup is "close but missing the spark" — the user can see the design doesn't match the reference but can't articulate exactly why — use pixel-level color analysis to find the gap.

## CRITICAL: Only Use Colors From References

**Do NOT invent colors.** When matching a reference design:
- Extract colors from the provided screenshots
- Use ONLY those extracted colors
- If the reference has black, gold, cream, and green — your mockup gets black, gold, cream, and green
- Do NOT add red, purple, blue, or any accent "because it might be useful"
- If you're unsure whether a color appears, run extraction first

This is the #1 source of "it doesn't match" feedback.

## The Pattern

1. **Extract dominant colors from reference** with HSL categorization
2. **Document to Google Sheet** for user verification (before rebuilding)
3. **Rebuild mockup** with verified values only
4. **Re-analyze** to verify the palette matches

## Deep Analysis Workflow (When User Pushes Back)

When simple extraction isn't enough, use unbucketed pixel analysis:

```python
from PIL import Image
import colorsys
from collections import Counter

def deep_gold_analysis(path, name):
    """Extract gold/amber/yellow tones with NO bucketing — exact values"""
    img = Image.open(path).convert('RGB')
    width, height = img.size
    
    gold_pixels = []
    
    for y in range(height):
        for x in range(width):
            r, g, b = img.getpixel((x, y))
            h, l, s = colorsys.rgb_to_hls(r/255, g/255, b/255)
            h_deg = h * 360
            s_pct = s * 100
            l_pct = l * 100
            
            # Gold range: H 20-55°, saturation > 10%, lightness 20-80%
            if 20 <= h_deg <= 55 and s_pct > 10 and 20 < l_pct < 80:
                gold_pixels.append((r, g, b, h_deg, s_pct, l_pct))
    
    print(f"\n{'='*80}")
    print(f"  {name}")
    print(f"  Total gold pixels: {len(gold_pixels):,}")
    print(f"{'='*80}")
    
    # EXACT hex values — no bucketing
    exact_counts = Counter((p[0], p[1], p[2]) for p in gold_pixels)
    
    print(f"\n  TOP 20 EXACT HEX VALUES:")
    for (r, g, b), count in exact_counts.most_common(20):
        h, l, s = colorsys.rgb_to_hls(r/255, g/255, b/255)
        hex_col = f"#{r:02X}{g:02X}{b:02X}"
        print(f"    {hex_col}  count={count:5d}  H={h*360:5.1f}° S={s*100:4.1f}% L={l*100:4.1f}%")
    
    # Average color
    if gold_pixels:
        avg_r = sum(p[0] for p in gold_pixels) / len(gold_pixels)
        avg_g = sum(p[1] for p in gold_pixels) / len(gold_pixels)
        avg_b = sum(p[2] for p in gold_pixels) / len(gold_pixels)
        print(f"\n  AVERAGE: #{int(avg_r):02X}{int(avg_g):02X}{int(avg_b):02X}")
```

### Key Insight: Dominant HUE Matters

The session that produced this workflow revealed:
- I was using H=33° (bronze) 
- Reference was H=43° (yellow-gold)
- That 10° hue shift makes a massive visual difference

Always report and compare the **dominant hue** across screens.

## Google Sheets Integration

Before rebuilding, populate findings to a Sheet for user verification:

```python
from googleapiclient.discovery import build

# Create sheet with extracted values
values = [
    ['CATEGORY', 'NAME', 'HEX', 'HSL', 'PIXEL COUNT', 'USAGE'],
    ['GOLD - PRIMARY', 'Primary Gold', '#BFAA73', 'H=43.4° S=37.3% L=60.0%', '2,353 px', 'CTAs, card accents'],
    ['GOLD - PRIMARY', 'Medium Gold', '#A89462', 'H=42.9° S=28.7% L=52.2%', '2,036 px', 'Labels, secondary'],
    # ... etc
]

sheets.spreadsheets().values().update(
    spreadsheetId=spreadsheet_id,
    range='Color Specs!A1',
    valueInputOption='RAW',
    body={'values': values}
).execute()
```

This lets the user verify the extraction before you rebuild.

## Full Multi-Screen Analysis Script

When user provides multiple reference screenshots:

```python
def analyze_all_screens(image_paths):
    """Analyze multiple screens, compile findings"""
    
    all_findings = {}
    
    for path, name in image_paths:
        img = Image.open(path).convert('RGB')
        width, height = img.size
        
        gold_pixels = []
        for y in range(height):
            for x in range(width):
                r, g, b = img.getpixel((x, y))
                h, l, s = colorsys.rgb_to_hls(r/255, g/255, b/255)
                h_deg, s_pct, l_pct = h * 360, s * 100, l * 100
                
                if 20 <= h_deg <= 55 and s_pct > 10 and 20 < l_pct < 80:
                    gold_pixels.append((r, g, b, h_deg, s_pct, l_pct))
        
        if gold_pixels:
            # Compute average
            avg_r = sum(p[0] for p in gold_pixels) / len(gold_pixels)
            avg_g = sum(p[1] for p in gold_pixels) / len(gold_pixels)
            avg_b = sum(p[2] for p in gold_pixels) / len(gold_pixels)
            avg_h, avg_l, avg_s = colorsys.rgb_to_hls(avg_r/255, avg_g/255, avg_b/255)
            
            all_findings[name] = {
                'count': len(gold_pixels),
                'avg_hex': f"#{int(avg_r):02X}{int(avg_g):02X}{int(avg_b):02X}",
                'avg_hue': avg_h * 360,
                'avg_sat': avg_s * 100,
                'avg_light': avg_l * 100,
            }
            
            # Top exact values
            exact_counts = Counter((p[0], p[1], p[2]) for p in gold_pixels)
            all_findings[name]['top_values'] = [
                (f"#{r:02X}{g:02X}{b:02X}", count) 
                for (r, g, b), count in exact_counts.most_common(5)
            ]
    
    # Report
    print("\n" + "="*70)
    print("  COMPILED FINDINGS")
    print("="*70)
    
    # Sort by pixel count (most gold pixels = most reliable source)
    sorted_screens = sorted(all_findings.items(), key=lambda x: -x[1]['count'])
    
    for name, data in sorted_screens:
        print(f"\n  {name}:")
        print(f"    Average: {data['avg_hex']} (H={data['avg_hue']:.1f}°)")
        print(f"    Pixels: {data['count']:,}")
        print(f"    Top values: {data['top_values'][:3]}")
    
    # Recommend primary gold from highest-count screen
    best_screen = sorted_screens[0][0]
    best_data = sorted_screens[0][1]
    print(f"\n  RECOMMENDED PRIMARY: {best_data['top_values'][0][0]}")
    print(f"  Source: {best_screen} ({best_data['count']:,} gold pixels)")
```

## Session Example: Timbr BFAA73 Discovery

### The Problem
User said "color doesn't match" through multiple iterations. I kept adjusting but never hit it.

### The Fix
Deep unbucketed analysis of 6 Robinhood reference screenshots revealed:

| Screen | Avg Gold | Pixel Count | Dominant Hue |
|--------|----------|-------------|--------------|
| Gold Card | #B39F6C | 350,804 | H=43.6° |
| Move Money | #887447 | 94,553 | H=41.9° |
| Virtual Cards | #665841 | 102,870 | H=37.8° |

The Gold Card screen had the MOST gold pixels, so its top value (#BFAA73, 2,353 exact pixels) became the primary gold.

**Key lesson**: Trust pixel counts. The screen with the most gold pixels is the most reliable source for the gold tone.

### CSS Variables After Deep Analysis

```css
/* GOLD - EXACT from deep pixel analysis */
--gold: #BFAA73;           /* PRIMARY: H=43.4° S=37.3% L=60.0% (2,353px) */
--gold-med: #A89462;       /* MEDIUM: H=42.9° S=28.7% L=52.2% (2,036px) */
--gold-light: #CAB272;     /* BRIGHT: H=43.6° S=45.4% L=62.0% (1,069px) */
--gold-bright: #FFD600;    /* GLOW: H=50.4° S=100% L=50% (246px highlights) */
--bronze: #5C513B;         /* DARK: H=40.0° S=21.9% L=29.6% (1,950px) */

/* Gold alpha variants — use extracted RGB values */
--gold2: rgba(191,170,115,0.12);
--gold3: rgba(191,170,115,0.22);
```

## Common Pitfalls

| Mistake | Fix |
|---------|-----|
| Adding colors not in reference | Extract first, use only extracted values |
| Using bucketed/rounded hex values | Use exact values from unbucketed analysis |
| Picking gold from decorative elements | Sample the specific element type you're matching |
| Guessing the hue | Report dominant hue numerically (43° vs 33° matters) |
| Skipping verification | Populate to Sheet, let user verify before rebuild |
| Using averages instead of top values | Top exact values are more reliable than averages |
