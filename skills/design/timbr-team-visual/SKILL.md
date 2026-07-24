---
name: timbr-team-visual
category: design
description: Canonical spec for the TIMBR founding team radar chart + profile card composition. Covers render pipeline, delivery, QC gate, and all locked design decisions.
triggers:
  - timbr radar
  - team visual
  - skills radar
  - timbr founding team
  - profile cards
---

# TIMBR — Team Visual Skill

End-to-end workflow for rendering and delivering the TIMBR founding team radar chart with bottom profile cards.

---

## Canonical Data

### Radar axes (13, in order — as of v30 final)
AI/ML · Backend · Mobile Dev · Frontend · Data & Analytics · Product · Marketing · Sales · Growth · Leadership · Fitness Domain · Athlete · Videography

**Axis renames applied:**
- `Product Strategy` → `Product` (user: "Change product strategy to just product")
- `Fitness Training` → `Fitness Domain` (renders as two lines: `Fitness` / `Domain`)
- `Cinematography` → `Videography`

**Removed axes:** none currently removed.

**Label rotation:** Use `theta_offset = np.pi/2 + np.pi/N` (half-spoke rotation) so no label lands at 12 o'clock (header collision) or 6 o'clock (clipped by bottom margin). This is the correct fix — do NOT suppress labels via `categories[i] = ""` unless user explicitly requests a hidden axis.

### People & colours
| Person | Colour | Hex |
|---|---|---|
| Tanzim Ozer | Cyan | `#00c8f0` |
| Sagar Giri | Green | `#00d96b` |
| Waseem Ahmad | Orange | `#ff6500` |

### Scores (out of 10) — v30 final (user-corrected)
| Axis | Tanzim | Sagar | Waseem | Source |
|---|---|---|---|---|
| AI/ML | 5 | 8 | 9 | user confirmed |
| Backend | 3 | 9 | 5 | user confirmed |
| Mobile Dev | 0 | 7 | 10 | user confirmed |
| Frontend | 7 | 7 | 9 | user confirmed |
| Data & Analytics | 8 | 7 | 9 | user confirmed |
| Product | 8 | 8 | 8 | user confirmed (all at 8, axis renamed from Product Strategy) |
| Marketing | 4 | 0 | 0 | user confirmed |
| Sales | 7 | 0 | 0 | user confirmed |
| Growth | 9 | 0 | 0 | user confirmed |
| Leadership | 9 | 6 | 9 | user confirmed (Tanzim=9, Waseem=9, Sagar=6) |
| Fitness Domain | 9 | 6 | 6 | user confirmed (Sagar+Waseem=6 this session) |
| Athlete | 0 | 0 | 0 | user confirmed |
| Videography | 0 | 0 | 0 | no source |

#### CRITICAL — zero-fill rule (user-enforced)
**Do NOT assign scores without a specific data source.** If no source exists → score = 0. User explicitly corrected assumed scores multiple times. When in doubt, ask — do not fill. This applies to all three people equally.

#### Tanzim fitness credentials (sourced)
- 12 years of fitness training experience
- Coached a bodybuilding athlete who won 17 gold medals
- Fitness Training = 9, Athlete = 0 (coach, not competitor)

### Card copy (locked)

**Tanzim Ozer**
Co-Founder · Product & Data Architecture
"Took 24 Hour Fitness 255→87 nationwide. Closed $5.7M for US Bank in 9 months."
Highlights: 24H Fitness: 255 → #87 Nationwide · $5.7M Closed · 9 Months @ US Bank
Tags: Product Strategy · Operations · Fitness Training · Analytics / DB

**Sagar Giri**
Co-Founder · Chief Engineer
"Built the security wall for Amazon Prime Card. Now wiring every layer of TIMBR's stack."
Highlights: Amazon Prime Card Security Wall · Amazon SDE L5 · Big-Tech Rigour
Tags: Backend · Mobile Dev · Data & Analytics · AWS Cloud

**Waseem Ahmad**
Founding Senior Engineer · AI Systems & Agentic Workforce
"Solo-wiring the agentic core end-to-end."
Highlights: US Patent Holder · ex-Meta Staff Engineer · ex-Google
Tags: Mobile Dev · AI / ML · Voice AI · Android

#### Card copy rules (critical)
- **No C-suite titles** — do NOT use CEO, CTO
- **Tanzim's domain = Product & Data Architecture**
- **Tanzim's credential line = companies only**: TIMBR · US Bank · 24 Hour Fitness
- **Waseem = Founding Senior Engineer · AI Systems & Agentic Workforce** — NOT "Advisor"
- **Card narrative = story sentence**, not a credential list
- **Fitness Domain tag → Fitness Training tag** in Tanzim's card (must stay in sync with axis removals)

---

## Design Spec

- **Background:** `#000000` (pure black)
- **Card bg:** `(10, 10, 10)` RGB
- **Canvas (13-axis):** W=1240, H=2120
- **TITLE_H:** 70px (PIL-drawn, above radar)
- **RADAR_H:** 1180px
- **SPACER:** 60px (between radar and cards)
- **FOOTER_H:** 110px
- **Polygon fill alpha:** 0.07
- **Polygon line width:** 2.2
- **Grid:** `#333333`, linewidth 1.0
- **Axis labels:** `#cccccc`, fontsize 8.5 bold, pad=18

### Footer
Current footer text:
> "Looking for a Seattle local videographer, marketer and athlete to join our founding team."

Rendered in PIL below the cards: divider line at `#373737`, text at `(210, 210, 210)`, font size 20 (auto-shrinks to 17 if too wide), centred.

---

## Render Pipeline (PIL — v20+)

**Architecture:** matplotlib renders radar ONLY (no title) → BytesIO → PIL Image → PIL draws title + cards + footer → composited onto final PIL canvas.

The title is drawn in PIL, NOT in a matplotlib gridspec subplot. This prevents the title subplot from eating into the radar's vertical space, which caused top/bottom label clipping.

### Radar (matplotlib → PIL)
```python
fig = plt.figure(figsize=(W/150, RADAR_H/150), dpi=150, facecolor='black')
# Single polar axes — generous margins so labels never clip
ax_radar = fig.add_axes([0.08, 0.08, 0.84, 0.84], projection='polar')

# Half-spoke rotation: no label at 12 or 6 o'clock
ax_radar.set_theta_offset(np.pi / 2 + np.pi / N)
ax_radar.set_theta_direction(-1)

buf = io.BytesIO()
plt.savefig(buf, format='png', dpi=150, facecolor='black', pad_inches=0.0)
buf.seek(0)
radar_img = Image.open(buf).convert("RGBA")
radar_resized = radar_img.resize((W, RADAR_H), Image.LANCZOS)
```

### Composite
```python
final = Image.new("RGB", (W, H), BG_COLOR)
draw_final = ImageDraw.Draw(final)

# PIL title
f_title = get_font(22, bold=True)
title_text = "FOUNDING TEAM  ·  SKILLS RADAR"
tw = draw_final.textlength(title_text, font=f_title)
draw_final.text(((W - tw) // 2, (TITLE_H - 22) // 2), title_text, fill=(255,255,255), font=f_title)

# Radar below title
final.paste(radar_resized.convert("RGB"), (0, TITLE_H))

# Cards
card_y = TITLE_H + RADAR_H + SPACER + GAP
for i, card in enumerate(cards_data):
    card_img = draw_card_pil(card, CARD_W, CARD_H)
    final.paste(card_img, (GAP + i * (CARD_W + GAP), card_y))

# Footer
footer_y = H - FOOTER_H
draw_final.line([(GAP*2, footer_y+16), (W-GAP*2, footer_y+16)], fill=(55,55,55), width=1)
draw_final.text(((W - ft_w) // 2, footer_y + 38), footer_text, fill=(210,210,210), font=f_footer)
```

### Working script
Canonical script: `/home/hermes/timbr_v30.py` (13-axis build, PIL pipeline, footer, Roboto font)
Output: `/home/hermes/timbr_radar_v30.png`

---

## QC Gate (Veronica)

Before every send: `browser_navigate` to file → `browser_vision` to score.
- **Minimum score: 8/10 to ship** (7.5 acceptable if content independently verified correct)
- **Override Veronica when she misidentifies the brief** — e.g. she flagged "Fitness Training" as the problem axis when "Fitness Domain" was the one removed. Content correctness confirmed manually overrides a low Veronica score.
- Ask vision to list ALL axis labels clockwise — this catches clipped or missing spokes early
- If browser times out on a tall PNG: use pixel brightness scan in Python to verify footer/card text existence
  ```python
  arr = np.array(Image.open(path))
  bright = (arr[row, :, :].sum(axis=1) > 100).sum()
  # >50 bright pixels on a row = text is rendering
  ```

---

## Delivery

```bash
TOKEN=$(grep WHATSAPP_BRIDGE_TOKEN /home/hermes/.hermes/.env | cut -d= -f2)
curl -s -X POST "http://localhost:3000/send-media" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"chatId":"160799431606497@lid","filePath":"/home/hermes/<file>.png"}'
```

**Never use `send_message` with `image::` prefix** — routes to `/send`, not `/send-media`, silently fails.
**Body key is `chatId`** — not `recipient` (returns 400).

---

## Pitfalls

- **14-axis radar: AI/ML at 12 o'clock + Sales at 6 o'clock both clip** — fix is `theta_offset = pi/2 + pi/N`, NOT label suppression. Suppressing via `""` was the v19 workaround; rotation is the correct fix.
- **Title in matplotlib gridspec eats radar space** — draw title in PIL on the composite canvas instead. Use `fig.add_axes([0.08,0.08,0.84,0.84])` for the radar (single axes, no gridspec).
- **Browser times out on PNGs taller than ~2000px** — use pixel brightness scan as fallback QC (see above).
- **Veronica can misread the brief** — she is a vision model, not domain-aware. Manually verify axis list before accepting her axis-count failures as real bugs.
- **Fitness Domain tag in cards must stay in sync with radar axes** — when an axis is removed, check all three cards' `tags` arrays for stale references.
- **Zero-fill rule** — do NOT guess scores. Ask if no source.
- **No C-suite titles** — CEO/CTO rejected by user.
- **Card narrative = story, not a list** — user rejected bullet-style.
- **Background = pure black `#000000`**.
- **Radar lock can be lifted** — treat as session-level default, not permanent.
- **`send-media` body key = `chatId`** (not `recipient`).
- **Subtitle line removed** — "Three complementary domains" was removed; do not re-add.
- **matplotlib axes-within-axes breaks at portrait aspect ratios** — PIL pipeline is correct approach.
- **Spacer between radar and cards** — SPACER=60px, user requested visible breathing room.

---

## Version History
| File | Notes |
|---|---|
| timbr_radar_v19.py | 8-axis build; AI/ML suppressed via `categories[0]=""` (12 o'clock workaround); radar locked; SPACER=60 |
| timbr_radar_v20.py | Radar unlocked; 6 new axes added; then Fitness Domain removed → 13 axes; AI/ML label restored; theta_offset rotation fix; PIL title; footer added; user corrected all scores; canonical script |
| timbr_v30.py | **Current canonical.** Axis renames: Product Strategy→Product, Fitness Training→Fitness Domain, Cinematography→Videography. Score updates: Leadership (T=9,S=6,W=9), Product all=8, Fitness Domain (S=6,W=6). Roboto font applied. |
