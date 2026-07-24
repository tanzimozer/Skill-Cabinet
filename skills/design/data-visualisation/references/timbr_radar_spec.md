# TIMBR Founding Team — Radar Spec (current)

Last updated: 2026-07
Script: `/home/hermes/timbr_v30.py`
Output: `/home/hermes/timbr_radar_v30.png`

---

## Axes (13, in this exact order — index matters for score arrays)

| # | Axis label | Python string |
|---|---|---|
| 0 | AI / ML | `"AI / ML"` |
| 1 | Backend | `"Backend"` |
| 2 | Mobile Dev | `"Mobile Dev"` |
| 3 | Frontend | `"Frontend"` |
| 4 | Data & Analytics | `"Data &\nAnalytics"` |
| 5 | Product | `"Product"` |
| 6 | Marketing | `"Marketing"` |
| 7 | Sales | `"Sales"` |
| 8 | Growth | `"Growth"` |
| 9 | Leadership | `"Leadership"` |
| 10 | Fitness Domain | `"Fitness\nDomain"` |
| 11 | Athlete | `"Athlete"` |
| 12 | Videography | `"Videography"` |

Note: two-line labels use actual `\n` in Python string — NOT escaped `\\n`.

---

## Scores (source-verified; 0 = no data — do not fill in guesses)

| Person | AI/ML | Back | Mob | Front | Data | Prod | Mkt | Sales | Growth | Lead | Fit | Ath | Vid |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Tanzim | 5 | 3 | 0 | 7 | 8 | 8 | 4 | 7 | 9 | 9 | 9 | 0 | 0 |
| Sagar  | 8 | 9 | 7 | 7 | 7 | 8 | 0 | 0 | 0 | 6 | 6 | 0 | 0 |
| Waseem | 9 | 5 | 10 | 9 | 5 | 8 | 0 | 0 | 0 | 9 | 6 | 0 | 0 |

---

## Colours & people

| Person | Colour | Hex |
|---|---|---|
| Tanzim Ozer | cyan | `#00c8f0` |
| Sagar Giri | green | `#00d96b` |
| Waseem Ahmad | orange | `#ff6500` |

---

## Radar settings

- Background: `#000000` (pure black), ax facecolor `#080808`
- Rotation: `set_theta_offset(π/2 + π/13)` — half-spoke, prevents 12/6 o'clock label collision
- Direction: clockwise (`set_theta_direction(-1)`)
- Scale: `ylim(0,10)`, yticks `[2,4,6,8,10]`
- Label style: colour `#cccccc`, fontsize 8.5, bold, `tick_params pad=18`
- Fill opacity: `alpha=0.07` (7%)
- Grid: `#333333`, linewidth 1.0
- Dots: `s=34`, edgecolors white, linewidths 0.5

---

## Canvas layout (PIL composite)

```
W=1240px
TITLE_H=116  RADAR_H=1180  SPACER=16  GAP=18  CARD_H=580  FOOTER_H=108
Total H ≈ 2036px
```

---

## Card copy (current approved)

### Tanzim Ozer
- **Role 1:** Co-Founder
- **Role 2:** Product & Data Architecture
- **Narrative:** Built the market insight before the product.
- **Highlights:** 24H Fitness: 255 → #87 Nationwide · $5.7M Closed · 9 Months @ US Bank
- **Tags:** Product Strategy · Operations · Fitness Domain · Analytics / DB

### Sagar Giri
- **Role 1:** Co-Founder
- **Role 2:** Chief Engineer
- **Narrative:** Now wiring every layer of TIMBR's stack.
- **Highlights:** Amazon Prime Card Security Wall · Amazon SDE L5 · Big-Tech Rigour
- **Tags:** Backend · Mobile Dev · Data & Analytics · AWS Cloud

### Waseem Ahmad
- **Role 1:** Founding Senior Engineer
- **Role 2:** AI Systems & Agentic Workforce
- **Narrative:** Solo-wiring the agentic core end-to-end.
- **Highlights:** US Patent Holder · ex-Meta Staff Engineer · ex-Google
- **Tags:** Mobile Dev · AI / ML · Voice AI · Android

---

## Footer (current text)

Line 1 (bold): "Looking for a Seattle local videographer, marketer and athlete to join our founding team for sweat equity."
Line 2: "We highly encourage University of Washington students to join for impactful equity."
Line 3: "© TIMBR FITNESS TECHNOLOGIES"

---

## Hard user preferences (do not override)

- Radar axes and layout: locked — only data/score changes allowed per explicit instruction
- Pure black background (#000000) — non-negotiable
- No C-suite titles (CEO/CTO) — role descriptors only
- Credentials = companies worked at, not cert bodies
- Narrative = one story sentence, not a list
- Waseem is NOT an advisor — he is Founding Senior Engineer building end-to-end
- Portrait orientation — taller than A4 is acceptable, user has approved
- Source-verify all scores — "if someone is zero, they are zero"

---

## Delivery

```bash
BRIDGE_TOKEN=$(grep WHATSAPP_BRIDGE_TOKEN /home/hermes/.hermes/.env | cut -d= -f2)
curl -s -X POST http://localhost:3000/send-media \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $BRIDGE_TOKEN" \
  -d '{"chatId":"160799431606497@lid","filePath":"/home/hermes/timbr_radar_v30.png","mediaType":"image"}'
```

---

## Build instructions doc (Google Docs)

Full self-contained rebuild guide for Friday:
https://docs.google.com/document/d/1gTrN4G-dGnZBW07r8FLS-1zxKex7a8sT0nyQqDIbfcI
