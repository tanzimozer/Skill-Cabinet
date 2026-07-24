---
name: data-visualisation
description: "Producing presentation-quality charts, diagrams, and visual maps for Tanzim"
version: 1.2.0
platforms: [linux, macos]
metadata:
  hermes:
    tags: [charts, visualisation, design, infographic, html, playwright, timbr, radar]
    related_skills: [whatsapp-send-document]
---

# Data Visualisation & Chart Production

## When to use this skill
Any time Tanzim asks for a visual map, chart, org chart, roadmap, architecture diagram, or infographic to be delivered as an image (PNG/PDF) and sent via WhatsApp.

---

## Radar Charts (Matplotlib / PIL)

### Approach
Use **matplotlib polar axes** — not Chart.js/HTML — for radar charts. Gives pixel-perfect control and no browser-rendering race conditions.

### Tested-good settings
```python
fig = plt.figure(figsize=(12, 9.5), facecolor='#070A13')
ax  = fig.add_axes([0.08, 0.13, 0.84, 0.78], polar=True, facecolor='#070A13')
```

### Label visibility — critical lessons
- **Always draw axis labels manually** via `ax.text(angle, radius, cat, ...)` — never rely on `ax.set_xticklabels()` for radar; they clip and scale poorly.
- `label_r = 11.5` (i.e. outside `ax.set_ylim(0, 13.5)`) pushes labels clear of the outermost ring — never set ylim to 10 if labels need space.
- `fontsize=12, fontweight='bold', color='#FFFFFF'` is the minimum for legibility on dark background.
- Add a subtle dark bbox behind each label: `bbox=dict(boxstyle='round,pad=0.3', facecolor='#070A13', edgecolor='none', alpha=0.55)` — prevents label/polygon bleed.
- Multi-line labels (`'Data &\nAnalytics'`) need `multialignment='center'` and `linespacing=1.4`.

### Scale numbers
- Place ring-level numbers on **3 spokes** (e.g. spoke indices 0, 2, 4) not just one — one spoke is insufficient for cross-axis value reading.
- `fontsize=8.5, fontweight='bold', color='#CCCCCC'` — visible but not dominant.

### Polygon overlap / muddy centre fix
- Keep fill alpha at **0.07** — anything above 0.10 produces muddy blended zones when three polygons overlap.
- Outlines at `linewidth=2.5, alpha=0.95` stay crisp without the fill muddying things.
- Data-point dots: `markersize=6`, dark edge (`markeredgewidth=1.2`) so they pop off the fill.

### Grid
- Ring lines: `alpha=0.15, linewidth=0.8` — visible but non-dominant.
- Spoke lines: `alpha=0.20, linewidth=1.0`.
- `ax.spines['polar'].set_visible(False)` — always hide the outer spine.

### Legend placement
- `bbox_to_anchor=(0.5, -0.22)` keeps the legend **below** the chart without clipping the bottom axis labels (particularly 'Leadership' at ~270°).

---

## Profile Cards (below radar) — PIL approach (preferred)

**Use PIL, not matplotlib axes-within-axes.** Matplotlib sub-axes break at tall aspect ratios and fight each other for space. PIL gives exact pixel control.

### Canvas architecture (confirmed working)
```python
# Constants
W        = 1240
TITLE_H  = 116
RADAR_H  = 1180
SPACER   = 16
GAP      = 18
CARD_H   = 580
FOOTER_H = 108
H = TITLE_H + RADAR_H + SPACER + GAP + CARD_H + GAP + FOOTER_H

CARD_W = (W - GAP * 4) // 3   # four gaps: left + between 3 + right

# Assembly
final = Image.new("RGB", (W, H), (0, 0, 0))
# 1. Draw title in PIL at (TITLE_H - 22) // 2
# 2. Paste radar at (0, TITLE_H)
# 3. For i, card: paste at (GAP + i*(CARD_W+GAP), TITLE_H+RADAR_H+SPACER+GAP)
# 4. Draw footer rectangle + text at H - FOOTER_H
```

### Title in PIL, NOT matplotlib
Draw the title text onto the PIL canvas **after** matplotlib renders the radar. Never use matplotlib's `fig.suptitle()` or a title subplot — it steals space from the radar and causes label clipping.

```python
f_title = get_font(22, bold=True)
title_text = "FOUNDING TEAM  ·  SKILLS RADAR"
tw = draw_final.textlength(title_text, font=f_title)
draw_final.text(((W - tw) // 2, (TITLE_H - 22) // 2), title_text, fill=(255,255,255), font=f_title)
```

### Per-card PIL layout (top-to-bottom)
Each card: `Image.new("RGB", (CARD_W, CARD_H), (10,10,10))`, `pad = 22`

| Element | Detail |
|---|---|
| Border | `rounded_rectangle`, accent colour, width=3, radius=10 |
| Banner | solid accent fill, y=2 to banner_h=72; name Roboto Bold 28px fill (5,5,5) centred |
| Role 1 | Roboto Bold 20px, accent colour, centred |
| Role 2 | Roboto Bold 20px (shrinks to 17px if too wide), accent colour |
| Divider | line colour (42,42,42) |
| Narrative | Roboto Regular 19px, (210,210,210), centred, text-wrapped |
| Highlights | 2 badge chips — rounded rect, accent 12% blend fill, Roboto Bold 18px white, badge_h=52, badge_gap=12 |
| Divider | same |
| Domains label | "DOMAINS" Roboto Bold 17px accent |
| Tag chips | 2×2 grid, chip_w=(CARD_W-pad*2-10)//2, chip_h=48, gap 10px, Roboto Regular 16px |
| Bottom strip | accent at 25% alpha blend, height=16px |

```python
def blend(color, alpha, bg=(10, 10, 10)):
    return tuple(int(c * alpha + b * (1 - alpha)) for c, b in zip(color, bg))
```

### Card content rules (Tanzim's hard preferences)
- **Credentials = companies worked at**, not certifications or tools.
- **Role line = descriptor**, not C-suite title. No CEO/CTO. Use e.g. "Co-Founder · Product & Data Architecture".
- **Narrative = one story sentence** — not a credential list. Who they are + what they're doing.
- Waseem Ahmad is **NOT an advisor** — he's solo-building agentic AI end-to-end. Title: "Founding Senior Engineer · AI Systems & Agentic Workforce".

### Font: Roboto throughout
```python
def get_font(size, bold=False):
    path = "/usr/share/fonts/truetype/roboto/unhinted/RobotoTTF/Roboto-Bold.ttf" if bold \
           else "/usr/share/fonts/truetype/roboto/unhinted/RobotoTTF/Roboto-Regular.ttf"
    return ImageFont.truetype(path, size)

# Also register for matplotlib:
fm.fontManager.addfont("/usr/share/fonts/truetype/roboto/unhinted/RobotoTTF/Roboto-Regular.ttf")
fm.fontManager.addfont("/usr/share/fonts/truetype/roboto/unhinted/RobotoTTF/Roboto-Bold.ttf")
matplotlib.rcParams['font.family'] = 'Roboto'
```

---

## Footer (white bar)

```python
footer_y = H - FOOTER_H
draw_final.rectangle([0, footer_y, W, H], fill=(255, 255, 255))
```

### Footer spacing — measure font metrics, don't guess
```python
# Actual Roboto metrics at these sizes:
# Bold 20px:   ascent=19 descent=5  total=24px
# Regular 17px: ascent=16 descent=5  total=21px
# Regular 15px: ascent=14 descent=4  total=18px
# Gap between lines = total_height + 8px breathing room
text_y = footer_y + 15
draw_final.text(((W - ft_w)  // 2, text_y),      line1, fill=(15,15,15),    font=f1)
draw_final.text(((W - fuw_w) // 2, text_y + 32),  line2, fill=(60,60,60),   font=f2)
draw_final.text(((W - fc_w)  // 2, text_y + 61),  line3, fill=(130,130,130), font=f3)
```

**Do not use fixed 40px or 80px gaps** — they look loose. Measure with `font.getmetrics()` → `(ascent, descent)` and add ~8px gap only.

### Save
```python
final.save(out, dpi=(150, 150))
```

---

## WhatsApp Delivery

### Only working method: curl to `/send-media` with JSON body
```bash
BRIDGE_TOKEN=$(grep WHATSAPP_BRIDGE_TOKEN /home/hermes/.hermes/.env | cut -d= -f2)
curl -s -X POST "http://localhost:3000/send-media" \
  -H "Authorization: Bearer $BRIDGE_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"chatId\":\"<recipient>\",\"filePath\":\"<abs_path>\",\"caption\":\"<text>\"}"
```

**Never** use `send_message` with `image::` prefix — routes to `/send`, which doesn't handle media.  
**Never** use multipart form (`-F`) — use JSON body; the bridge expects `chatId` + `filePath` as JSON keys.

---

## QC Gate (Veronica)
- Use `browser_navigate` to file:// URL then `browser_vision` to score the render before sending.
- Minimum pass score: **8 / 10** overall.
- If vision returns a blank white page, the file path is wrong or the browser hasn't rendered yet — re-navigate and retry.
- Score each element: labels, polygons, grid, legend, title. Fix the lowest-scoring element first.

---

## TIMBR Team Radar — reference spec
- `references/timbr_radar_spec.md` — axes (13), current scores, card copy, footer text, delivery curl, Google Doc link
- `references/google-docs-creation.md` — confirmed pattern for creating Google Docs via API (token path, insert pattern, gotchas)

---

## Pitfalls
- `ax.set_xticklabels([])` then manual labels: do this every time — built-in tick labels fight manual ones.
- `ax.set_ylim(0, 10)` with label_r=11.5 means labels are outside ylim — bump ylim to 13–14 or labels vanish.
- Legend overlapping bottom label: always use `bbox_to_anchor=(0.5, -0.22)` or lower.
- `ax.set_xticks([])` must be called after `ax.set_xticks(angles[:-1])` to suppress tick marks while keeping manual labels.
- Chart.js/HTML radar via browser: unreliable centering when label strings differ in length — avoid for precision work.
