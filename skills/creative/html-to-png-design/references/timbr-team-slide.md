# TIMBR Team Slide — Approved Spec (July 2026, v34)

## Stack (current)
- **matplotlib** — polar radar chart (not Chart.js — PIL build replaced HTML/CSS approach)
- **PIL / Pillow** — title, cards, footer; pixel-perfect control
- **Delivery** — curl to `/send-media` with `chatId`, not `send_message`

## Canvas
- **Portrait**: 1240px wide × dynamic height (TITLE_H + RADAR_H + SPACER + GAP + CARD_H + GAP + FOOTER_H)
- Background: pure black `#000000`
- Font: **Roboto** throughout (PIL + matplotlib rcParams)
  - PIL paths: `/usr/share/fonts/truetype/roboto/unhinted/RobotoTTF/Roboto-Bold.ttf` / `Roboto-Regular.ttf`
  - matplotlib: `fm.fontManager.addfont(path)` then `matplotlib.rcParams['font.family'] = 'Roboto'`

## Layout constants (v34)
```python
TITLE_H  = 116   # inflated to compensate for matplotlib's internal top padding (~170px)
RADAR_H  = 1180
SPACER   = 16    # reduced to compensate for matplotlib's internal bottom padding (~271px)
GAP      = 18
CARD_H   = 580   # content-fitted; 720 left ~162px dead space
FOOTER_H = 80
H = TITLE_H + RADAR_H + SPACER + GAP + CARD_H + GAP + FOOTER_H
W = 1240
# Visual north gap ≈ 286px, visual south gap ≈ 287px — balanced
```

> **Radar spacing rule**: matplotlib polar embeds ~170px top / ~271px bottom internal padding.
> To visually equalise: `TITLE_H = target - 170`, `SPACER = target - 271`.
> Target of ~287px gives TITLE_H=116, SPACER=16.

## Colour system (locked)
| Person | Accent (hex) | Accent (RGB tuple) |
|--------|-------------|-------------------|
| Tanzim Ozer | `#00c8f0` | `(0, 200, 240)` |
| Sagar Giri | `#00d96b` | `(0, 217, 107)` |
| Waseem Ahmad | `#ff6500` | `(255, 101, 0)` |

## Radar — 13 axes (locked order)
```python
categories = [
    "AI / ML", "Backend", "Mobile Dev", "Frontend",
    "Data &\nAnalytics", "Product",
    "Marketing", "Sales", "Growth", "Leadership",
    "Fitness\nDomain", "Athlete", "Videography",
]
```
- Rotation: `ax.set_theta_offset(np.pi / 2 + np.pi / 13)` — half-spoke, prevents 12/6 o'clock collision
- Direction: `ax.set_theta_direction(-1)`
- Fill opacity: `alpha=0.07`
- Scale ticks: `[2, 4, 6, 8, 10]`, colour `#666`
- Label colour: `#cccccc`, size 8.5, bold, pad 18

## Radar scores (approved, source-verified — v34)
| Axis (index) | Tanzim | Sagar | Waseem |
|---|---|---|---|
| AI / ML [0] | 5 | 8 | 9 |
| Backend [1] | 3 | 9 | 9 |
| Mobile Dev [2] | 0 | 7 | 10 |
| Frontend [3] | 7 | 7 | 9 |
| Data & Analytics [4] | 8 | 7 | 9 |
| Product [5] | 8 | 8 | 8 |
| Marketing [6] | 4 | 0 | 0 |
| Sales [7] | 7 | 0 | 0 |
| Growth [8] | 9 | 0 | 0 |
| Leadership [9] | 9 | 6 | 9 |
| Fitness Domain [10] | 9 | 4 | 6 |
| Athlete [11] | 0 | 0 | 0 |
| Videography [12] | 0 | 0 | 0 |

> Rule: zero if no source — do NOT guess. User: "if someone is zero, they are zero."

Score array format:
```python
members = [
    ("Tanzim Ozer",  "#00c8f0", [5, 3, 0, 7, 8, 8, 4, 7, 9, 9, 9, 0, 0]),
    ("Sagar Giri",   "#00d96b", [8, 9, 7, 7, 7, 8, 0, 0, 0, 6, 4, 0, 0]),
    ("Waseem Ahmad", "#ff6500", [9, 9, 10, 9, 9, 8, 0, 0, 0, 9, 6, 0, 0]),
]
```

## People data (v34)

### Tanzim Ozer — Co-Founder · Product & Data Architecture
- **Narrative**: "Built the market insight before the product."
- **Highlights**: `["24H Fitness: 255 → #87 Nationwide", "$5.7M Closed · 9 Months @ US Bank"]`
- **Tags**: `["Product Strategy", "Operations", "Fitness Domain", "Analytics / DB"]`

### Sagar Giri — Co-Founder · Chief Engineer
- **Narrative**: "Now wiring every layer of TIMBR's stack."
- **Highlights**: `["Amazon Prime Card Security Wall", "Amazon SDE L5 · Big-Tech Rigour"]`
- **Tags**: `["Backend", "Mobile Dev", "Data & Analytics", "AWS Cloud"]`

### Waseem Ahmad — Founding Senior Engineer · AI Systems & Agentic Workforce
- **Narrative**: "Solo-wiring the agentic core end-to-end."
- **Highlights**: `["US Patent Holder", "ex-Meta Staff Engineer · ex-Google"]`
- **Tags**: `["Mobile Dev", "AI / ML", "Voice AI", "Android"]`

## Footer (v23+)
- White bar (`fill=(255,255,255)`) — full width, FOOTER_H tall
- Dark text `fill=(15,15,15)`, Roboto Bold 20pt, centred
- Text: *"Looking for a Seattle local videographer, marketer and athlete to join our founding team."*

## Axis label history (rename log)
| Old label | New label | Version |
|---|---|---|
| Fitness Training | Fitness Domain | v22 |
| Cinematography | Videography | v29 |
| Product Strategy | Product | v34 |

## Axis label pitfalls
- **Newlines in category strings**: embed `\n` directly — patch tools and sed can double-escape to `\\n`, which renders as a literal backslash-n. Always `grep "Fitness" script.py` to verify after any patch.
- **Card tags must match axis labels** — if radar axis renames, update matching domain tag in `cards_data` too.
- **sed with path separators**: use `|` as delimiter not `/` when paths contain slashes.

## Score update workflow
When user gives a score correction:
1. Identify the axis index from the ordered list above
2. Patch the exact tuple line using sed with full match (include surrounding values to avoid ambiguous match)
3. Verify with `grep "Tanzim\|Sagar\|Waseem"` before running
4. Version the output file (timbr_v{N}.py → timbr_radar_v{N}.png)

## Source file
`/home/hermes/timbr_v34.py` → renders `/home/hermes/timbr_radar_v34.png`
