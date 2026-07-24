# TIMBR Founding Team Visual — Canonical Spec
_Last updated: 2026-07-17 (v18). Source of truth for `/home/hermes/timbr_radar_v*.png` builds._

## Current approved file
`/home/hermes/timbr_radar_v18.png` — 1240×1720px, pure black bg, PIL hybrid render

## Render approach (v18+)
**PIL hybrid** — not pure matplotlib. See `matplotlib-data-viz` SKILL.md § "PIL hybrid rendering".
- Radar: matplotlib → PIL image, resized to W×RADAR_H
- Cards: PIL ImageDraw, pixel-exact positions
- Script: `/home/hermes/timbr_v18.py`

## Canvas constants (LOCKED after v18)
```python
W, H    = 1240, 1720
RADAR_H = 1020   # LOCKED — do not change
SPACER  = 60     # gap between radar bottom and cards top
GAP     = 18
CARD_W  = (W - GAP * 4) // 3   # ≈ 388px
CARD_H  = H - RADAR_H - SPACER - GAP * 2  # ≈ 614px
```

## Radar — LOCKED (do not modify)
- 8 axes: `["AI / ML", "Backend", "Mobile Dev", "Fitness\nDomain", "Leadership", "Product\nStrategy", "Data &\nAnalytics", "Frontend"]`
- `theta_offset = π/2`, direction = −1 (clockwise from top)
- `ylim(0,10)`, ytick labels at [2,4,6,8,10] in `#555`, fontsize 6
- Grid colour: `#282828`, linewidth 0.8
- Fill opacity: 7% (`alpha=0.07`)
- Dot markers: `s=34`, edgecolor white, linewidth 0.5
- Radar facecolor: `#080808`
- Title: "FOUNDING TEAM  ·  SKILLS RADAR" — white, fontsize 15, bold
- Subtitle "Three complementary domains..." — **REMOVED** (user request)

## Team data (scores locked)
| Person | Colour | AI/ML | Backend | Mobile | Fitness | Leadership | Product | Data | Frontend |
|--------|--------|-------|---------|--------|---------|-----------|---------|------|----------|
| Tanzim Ozer | `#00c8f0` | 5 | 4 | 3 | 10 | 9 | 9 | 8 | 2 |
| Sagar Giri | `#00d96b` | 6 | 9 | 7 | 3 | 5 | 5 | 7 | 6 |
| Waseem Ahmad | `#ff6500` | 9 | 5 | 10 | 2 | 6 | 4 | 5 | 3 |

## Cards — approved copy (v18, locked)

### Tanzim Ozer
- **Role lines:** ["Co-Founder", "Product & Data Architecture"]
- **Narrative:** "Built the market insight before the product."
- **Highlights:** ["24H Fitness: 255 → #87 Nationwide", "$5.7M Closed · 9 Months @ US Bank"]
- **Tags:** ["Product Strategy", "Operations", "Fitness Domain", "Analytics / DB"]
- **Accent:** `#00c8f0` / RGB (0, 200, 240)

### Sagar Giri
- **Role lines:** ["Co-Founder", "Chief Engineer"]
- **Narrative:** "Now wiring every layer of TIMBR's stack."
- **Highlights:** ["Amazon Prime Card Security Wall", "Amazon SDE L5 · Big-Tech Rigour"]
- **Tags:** ["Backend", "Mobile Dev", "Data & Analytics", "AWS Cloud"]
- **Accent:** `#00d96b` / RGB (0, 217, 107)

### Waseem Ahmad
- **Role lines:** ["Founding Senior Engineer", "AI Systems & Agentic Workforce"]
- **Narrative:** "Solo-wiring the agentic core end-to-end."
- **Highlights:** ["US Patent Holder", "ex-Meta Staff Engineer · ex-Google"]
- **Tags:** ["Mobile Dev", "AI / ML", "Voice AI", "Android"]
- **Accent:** `#ff6500` / RGB (255, 101, 0)
- **Note:** AR/VR not added yet — pending confirmation with Waseem

## PIL card anatomy (pixel values for CARD_H ≈ 614px)
1. Border: `rounded_rectangle([1,1,cw-2,ch-2], radius=10, outline=accent, width=3)`
2. Banner: `rectangle([2,2,cw-3,72], fill=accent)` — name in dark text, fontsize 28 bold
3. Role line 1: y≈130, fontsize 20 bold, accent colour
4. Role line 2: y≈160 (auto-shrink to 17pt if >card_w−2*pad)
5. Divider at y≈196
6. Narrative (wrapped, fontsize 19, centred): y≈216
7. Highlight badge 1: y≈254, full-width rounded rect, accent+18% fill, fontsize 18 bold
8. Highlight badge 2: y≈318
9. Divider at y≈~390
10. "DOMAINS" label: y≈408, fontsize 17 bold
11. 2×2 chip grid: row1 y≈442, row2 y≈502; chip_w=(cw−pad*2−10)//2, chip_h=48
12. Bottom accent strip: last 16px, alpha 25%

## History of rejected / superseded options
- **No C-suite titles** (CEO/CTO) — user explicitly rejected
- **No certs** in credential lines — companies only for Tanzim
- Waseem "Strategic Advisor" — rejected; "Founding Senior Engineer" confirmed
- Waseem "Lead AI Engineer · Full Stack" — superseded by "Founding Senior Engineer / AI Systems & Agentic Workforce"
- Grey/charcoal background — replaced with pure `#000000`
- Subtitle "Three complementary domains. Zero overlap at the top." — **REMOVED** per user request
- Pure matplotlib card rendering — replaced by PIL hybrid at v18 (axes-within-axes drifts on tall figures)
- Narrative as long sentence (original) → split to short tagline + two highlight badges for better fill
