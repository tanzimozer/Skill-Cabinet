---
name: ui-mockup-production
description: "Producing, iterating, and delivering HTML/CSS UI mockups — iOS screens, Robinhood-style dark UI, pixel-accurate colour extraction, screenshot delivery."
version: 1.0.0
platforms: [linux]
metadata:
  hermes:
    tags: [mockup, ui, html, css, ios, robinhood, design, timbr, figma-alternative]
    related_skills: [whatsapp-send-document]
---

# UI Mockup Production

## When this applies
User asks for app screens, UI mockups, or design references as HTML/CSS — typically for dev handoff, PRD discussion, or stakeholder review.

## Stack
- Single self-contained HTML file (no external deps)
- Inline SVG for icons and illustrations
- JS only for dynamic elements (gear paths, computed geometry)
- Screenshot via `chromium-browser --headless`
- Delivery via WhatsApp bridge `/send-media`

---

## Robinhood Design Language

When user specifies "Robinhood-inspired" — these are the EXACT values. Do NOT guess or approximate.

### Colour system (pixel-extracted from actual Robinhood screenshots, 2026-06-01)

| Token | Hex | Use |
|---|---|---|
| Gold (primary accent) | **#A98760** | CTAs, active states, hero numbers, chart lines, rail dots. This is warm bronze-amber — NOT bright yellow-gold. |
| Gold bright | #C4A86A | Hover/active only |
| Gold tint bg | rgba(169,135,96,0.12) | Tag backgrounds, subtle highlights |
| Gold border | rgba(169,135,96,0.22) | Tag/pill borders |
| App background | #000000 or #0C0B09 | Pure black or very slightly warm near-black |
| Card bg | #141210 | Card surfaces |
| Elevated card | #1C1A17 | Modals, sheets |
| Border | #252220 | Card borders (warm dark) |
| Border light | #2E2B26 | Slider tracks, dividers |
| Text primary | #FFFFFF | |
| Text secondary | #AAAAAA | |
| Text muted | #666258 | Warm grey — eyebrow labels, meta |
| Text faint | #3A3830 | Hints |

**CRITICAL:** The common mistake is using `#C9A84C` (too bright, too yellow). Real Robinhood gold is muted, earthy, warm — and the **hue is 43°** (yellow-gold), NOT 33° (bronze). These look similar in a picker but render completely differently on dark backgrounds. Always pixel-extract and check the H value.

### Deep extraction — pixel count by hue range

Use this to find the true dominant gold across multiple reference screens:

```python
from PIL import Image
import colorsys
from collections import Counter

def deep_gold_analysis(path, name):
    img = Image.open(path).convert('RGB')
    pixels = list(img.getdata())
    gold_pixels = []
    for r, g, b in pixels:
        h, s, l = colorsys.rgb_to_hls(r/255, g/255, b/255)
        h_deg = h * 360
        if 30 <= h_deg <= 55 and s > 0.1 and 0.2 < l < 0.8:
            r8, g8, b8 = (r//8)*8, (g//8)*8, (b//8)*8
            gold_pixels.append((r8, g8, b8))
    counts = Counter(gold_pixels)
    print(f"\n{name} — top gold pixels:")
    for (r, g, b), count in counts.most_common(10):
        h, s, l = colorsys.rgb_to_hls(r/255, g/255, b/255)
        print(f"  #{r:02X}{g:02X}{b:02X}  H={h*360:.1f}° S={s*100:.1f}% L={l*100:.1f}%  ×{count}")
```

Run this on **all** reference screens. Use the screen with the highest gold pixel count as ground truth (e.g. Robinhood Gold Card screen had 350,804 gold-range pixels vs 4,754 for Net Worth — very different reliability).

### Robinhood gold calibration (2026-06-01 — 5 reference screens)

| Role | Hex | HSL | Source |
|------|-----|-----|--------|
| Primary (default) | `#A89462` | H=42.9° S=28.7% L=52.2% | 2,036px |
| Darker variant | `#887447` | H=41.9° S=31.0% L=40.7% | Move Money avg |
| Light/highlights | `#BFAA73` | H=43.4° S=37.3% L=60.0% | 2,353px |
| Glow/charts | `#FFD600` | H=50.4° S=100% L=50% | 246px |
| Bronze accents | `#5C513B` | H=40.0° S=21.9% L=29.6% | 1,950px |
| Cream text | `#E0DCD8` | H=30° S=11% L=86% | — |

**User preference on darkness:** When user says "slightly darker", shift L down ~8-10 points. "#A89462 (L=52%) → #887447 (L=41%)" was the correct direction.

### Design principles
- **Numbers are the heroes.** Large bold values (22px+) in accent colour. The data IS the design.
- **"TOTAL" pattern.** Small uppercase muted label above large gold number — mirrors Robinhood net worth display.
- **Minimal chrome.** Thin warm borders, no gradients except subtle radial gold glows. No drop shadows on cards.
- **Gold line chart.** Thin SVG polyline trending up, glowing endpoint dot, gradient fill below. Use on completion/summary screens.
- **Pure blacks.** Background #000000 or #0C0B09 — NOT dark greys like #080808 which read as cool/grey not Robinhood warm-black.

---

## iOS Phone Frame Spec

```css
.phone {
  width: 393px; height: 852px;  /* iPhone 15 Pro */
  background: #000;
  border-radius: 54px;
  border: 1.5px solid #1E1C18;
  overflow: hidden;
  box-shadow: 0 0 0 1px #0A0A08, 0 48px 120px rgba(0,0,0,.95),
              inset 0 0 0 1px #1C1A17;
}
```

Dynamic island notch:
```html
<div class="sb-notch"></div>
<!-- CSS: width:120px; height:34px; background:#000; border-radius:18px;
     position:absolute; top:0; left:50%; transform:translateX(-50%); -->
```

Status bar: height 54px, time left, notch center, wifi+battery icons right.

Bottom nav: height 86px, 5 icons, active icon in gold with 4px dot below.

---

## Exercise Card Layout (Timbr-specific)

```
Header: < Back | End Workout (gold) | All ≡
─────────────────────────────────────────
Left rail (36px) | Card body (flex:1)
  ○ done (gold ✓) |  Exercise Name (22px 900)
  │               |  Gold "Exercise N of M" badge
  ● current (gold)|  
  │               |  Video area (150px portrait)
  ○               |    SVG silhouette at 20% opacity
  ○               |    Edge-fade vignette
  ○               |    "▶ Demo" + "10s · Loop" badges
  ○               |  
  ○               |  Three slider rows:
  ○               |    [Label] [Value 22px hero] [track]
  ○               |    Weight → gold, Reps → purple, Sets → blue
─────────────────────────────────────────
Bottom nav (5 icons, Workout tab gold)
```

### Slider row pattern
```html
<div class="srow">
  <div class="sl-label sl-w">Wt</div>
  <div class="sl-body">
    <div class="sl-val sl-val-w">80 kg</div>  <!-- 22px 900 gold -->
    <div class="sl-track">
      <div class="sl-fill sf-w"></div>         <!-- gold fill -->
      <div class="sl-thumb st-w"></div>        <!-- 13px circle -->
    </div>
    <div class="sl-range"><span>40 kg</span><span>140 kg</span></div>
  </div>
</div>
```

---

## Exercise Silhouette SVGs

Use inline SVG geometric approximations — circle for head, rects for torso/limbs. Keep it:
- 20% opacity, gold fill
- Matched to the actual exercise (leg press = seated with legs forward, leg extension = leg raised, etc.)
- Centered in a portrait video placeholder with radial edge-fade vignette

---

## Screenshot & Delivery Workflow

```bash
# 1. Serve the file
python3 -m http.server 8765 &  # background

# 2. Screenshot
chromium-browser --headless --disable-gpu \
  --screenshot=/home/hermes/mockup.png \
  --window-size=1820,1200 \
  --no-sandbox \
  "http://localhost:8765/timbr-mockup-v5.html" 2>/dev/null

# 3. Crop rows (PIL)
from PIL import Image
img = Image.open("/home/hermes/mockup.png")
w, h = img.size
img.crop((0, 0, w, h//2+60)).save("/home/hermes/row1.png")
img.crop((0, h//2-60, w, h)).save("/home/hermes/row2.png")
```

Send to group via bridge — see `whatsapp-send-document` skill.

### When `send_message` tool returns 401

The `send_message` tool may not pass the bearer token correctly. If you get 401 Unauthorized but `/health` shows connected, bypass the tool with direct curl:

```bash
curl -s -X POST http://localhost:3000/send-media \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $WHATSAPP_BRIDGE_TOKEN" \
  -d '{"chatId": "GROUP_JID_OR_LID", "filePath": "/home/hermes/mockup.png", "mediaType": "image"}'
```

The token is in `$WHATSAPP_BRIDGE_TOKEN` env var.

---

## Pixel-Level Colour Extraction

When user says "the colour doesn't match" — extract exact values from reference screenshots:

```python
from PIL import Image
import numpy as np

def find_gold(path):
    img = Image.open(path).convert('RGB')
    arr = np.array(img)
    r,g,b = arr[:,:,0].astype(int), arr[:,:,1].astype(int), arr[:,:,2].astype(int)
    # Gold: R>G>B, R>140, G>90, B<120
    mask = (r>140)&(g>90)&(b<120)&(r>g)&(g>b)
    gold = arr[mask]
    if len(gold) > 10:
        med = np.median(gold, axis=0).astype(int)
        print(f"Gold median: #{med[0]:02X}{med[1]:02X}{med[2]:02X}")
        # Cluster top shades
        bk = {}
        for px in gold:
            k = (int(px[0])//8*8, int(px[1])//8*8, int(px[2])//8*8)
            bk[k] = bk.get(k,0)+1
        for (R,G,B), cnt in sorted(bk.items(), key=lambda x:-x[1])[:5]:
            print(f"  #{R:02X}{G:02X}{B:02X}  {cnt}px")
```

Do this BEFORE writing the mockup if given reference images. Don't guess colours.

---

## Iteration pattern

1. **Analyse refs first** — pixel-extract colours, note layout hierarchy
2. **Identify PRIMARY vs SECONDARY accent** — count pixel frequency by hue range. The most-used saturated colour is the primary accent (CTAs, progress rails, active states). Don't assume gold is primary just because "Robinhood-inspired" — the ref might use coral-red primary with gold secondary.
3. **Write the HTML** — full 8 screens in one file
4. **Screenshot and deliver** — two cropped rows + HTML file to WhatsApp group
5. **Wait for feedback** — don't pre-emptively iterate; let Tanzim call the next change
6. **For large rebuilds** — use `subagent` with `claude-opus-4-5` model; provide exact spec including extracted hex values

### Pitfall: Inverting the accent hierarchy
In Timbr v5, gold was used as primary CTA colour because "Robinhood-inspired" suggested gold. But the actual reference screenshots used **coral-red (#E84040)** as the primary action colour with gold only for premium badges and subtle highlights. Always count pixel frequency by hue before deciding which colour is primary:

```python
# Quick hue-category count
coral_count = 0  # H 340-10°, S>50%, L 40-75%
gold_count = 0   # H 20-55°, S>20%, L 30-70%
# ... iterate pixels, categorize by HSL
print(f"Coral: {coral_count}, Gold: {gold_count}")
# If coral >> gold, coral is primary accent
```

## Subagent for large builds
Opus can generate the full HTML but times out on 8-screen specs in a single pass. Mitigation:
- Split the spec into CSS + screen-by-screen structure
- Or give Opus the CSS separately and ask it to write just the HTML body
- Check if the file was written even if the subagent reports timeout — it often completes the write before the API call times out

---

## Wireframe Separation

Always produce two files — styled mockup AND a wireframe:
- `index.html` — full styled mockup with color palette
- `wireframe.html` — structure-only, grayscale, dashed borders

Wireframe rules:
- White background (#FFF), light gray (#DDD) solid borders, dashed (`border: 1px dashed #CCC`) for placeholder areas
- Crosshatch pattern for image/video placeholders: `repeating-linear-gradient(45deg, #F0F0F0, #F0F0F0 10px, #E8E8E8 10px, #E8E8E8 20px)`
- No colors, no gold — everything in #333, #666, #999, #CCC
- Label every placeholder with what it represents (e.g. "Video Demo Placeholder")
- Same screen count/layout as the styled version

Push both to the same GitHub repo under the same commit.

## Border Radius Calibration

Modern iOS-style UIs expect generous radii. Starting point after pixel-extracted Robinhood refs:

| Element | Radius |
|---------|--------|
| Phone frame | 54px |
| Main cards | 28px |
| Slider rows / input sections | 26px |
| Video placeholder | 28px |
| Stat cells | 24px |
| Sheet action buttons | 24px |
| Tip/info cards | 22px |
| Pills / chips | 100px |

When user asks "rounder" or "+30% more", apply to ALL section radii at once — not just one element. Use `sed -i` to batch-replace.

## GitHub Repo Creation from CLI

Token extraction that reliably works (no credentials file needed):
```bash
TOKEN=$(cat ~/.git-credentials | grep github | sed 's/.*:\/\/[^:]*://' | sed 's/@.*//')

curl -s -X POST https://api.github.com/user/repos \
  -H "Authorization: token $TOKEN" \
  -H "Accept: application/vnd.github+json" \
  -d '{"name":"<project>-ui","description":"...","private":false}'

cd /home/hermes/<project>-ui
git init && git branch -m main
git add . && git commit -m "Initial commit"
git remote add origin https://github.com/tanzimozer/<project>-ui.git
git push -u origin main
```

## Color Spec Sheet (Google Sheets)

After completing extraction, populate a Google Sheet:
- Sheet name: `<PROJECT> APP UI`
- Columns: CATEGORY, NAME, HEX, HSL, PIXEL COUNT, USAGE
- Include per-screen averages and pixel counts for source credibility
- Update when palette changes — don't just create on first run

## Files
- `references/robinhood-colour-analysis.md` — pixel extraction results from 2026-06-01 session (5 screens, 629k gold pixels)
- `references/timbr-v6-coral-palette.md` — corrected palette with coral-red primary, gold secondary
