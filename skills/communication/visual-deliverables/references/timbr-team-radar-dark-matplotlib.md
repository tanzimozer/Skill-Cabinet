# TIMBR Team Radar — Dark matplotlib + PIL Build (July 2026)

## Context
Tanzim iterated on a dark-background radar chart using matplotlib (radar) + PIL (cards + title).
This is the APPROVED architecture as of v20. Use this for any future rebuild.

---

## Canvas (v20 approved)
- **Total size:** `W=1240, H=1970` px
- **TITLE_H:** 70 px — drawn in PIL directly onto the final composite (NOT in matplotlib)
- **RADAR_H:** 1180 px — matplotlib polar figure, full-figure (no gridspec/title subplot)
- **SPACER:** 60 px between radar and cards
- **Cards:** remainder of canvas

---

## Radar — matplotlib config

### Figure
```python
fig = plt.figure(figsize=(W/150, RADAR_H/150), dpi=150, facecolor='black')
# Single polar axes — generous margins so labels never clip
ax_radar = fig.add_axes([0.08, 0.08, 0.84, 0.84], projection='polar')
```

**CRITICAL: Never use gridspec with a title subplot for the radar.**
If matplotlib renders the title as a subplot, its topmost axis label (`AI / ML` at 12 o'clock)
bleeds into the title area visually and the bottommost label (`Sales` at 6 o'clock) clips.
Fix: draw title in PIL on the composite, give matplotlib the whole figure for the radar.

### Axis rotation
```python
ax_radar.set_theta_offset(np.pi / 2 + np.pi / N)  # N = number of axes
ax_radar.set_theta_direction(-1)
```
The `+ np.pi / N` half-spoke offset is **required** for even-N axis counts.
Without it, one spoke lands exactly at 12 o'clock (becomes title) and one at 6 o'clock (clips).

### Axes (14 as of v20)
```
AI / ML, Backend, Mobile Dev, Frontend, Data & Analytics,
Product Strategy, Marketing, Sales, Growth, Leadership,
Fitness Domain, Fitness Training, Athlete, Cinematography
```
Order matters — spokes are laid out clockwise from theta_offset position.

### Grid
```python
ax_radar.grid(color="#333333", linewidth=1.0)
ax_radar.spines['polar'].set_color("#333333")
ax_radar.set_yticks([2, 4, 6, 8, 10])
ax_radar.set_yticklabels(["2","4","6","8","10"], color="#666", fontsize=6.5)
ax_radar.tick_params(pad=18)
```

### Polygons
```python
# Fill alpha=0.07 — keeps overlap clean, no muddy centre (do not raise)
ax_radar.plot(angles_closed, vals, color=color, linewidth=2.2, zorder=3)
ax_radar.fill(angles_closed, vals, color=color, alpha=0.07, zorder=2)
ax_radar.scatter(angles, scores, color=color, s=34, zorder=4,
                 edgecolors='white', linewidths=0.5)
```

### Savefig
```python
plt.savefig(buf, format='png', dpi=150, facecolor='black', pad_inches=0.0)
```
`pad_inches=0.0` — do not add matplotlib padding; PIL controls spacing.

---

## Scores (v20, source-verified only — zero if no source)

| Axis            | Tanzim (Cyan #00c8f0) | Sagar (Green #00d96b) | Waseem (Orange #ff6500) |
|-----------------|----------------------|-----------------------|-------------------------|
| AI / ML         | 5                    | 6                     | 9                       |
| Backend         | 4                    | 9                     | 5                       |
| Mobile Dev      | 3                    | 7                     | 10                      |
| Frontend        | 2                    | 6                     | 3                       |
| Data & Analytics| 8                    | 7                     | 5                       |
| Product Strategy| 9                    | 5                     | 4                       |
| Marketing       | 7                    | 0                     | 0                       |
| Sales           | 9                    | 0                     | 0                       |
| Growth          | 8                    | 0                     | 0                       |
| Leadership      | 9                    | 5                     | 6                       |
| Fitness Domain  | 10                   | 3                     | 2                       |
| Fitness Training| 9                    | 0                     | 0                       |
| Athlete         | 9                    | 0                     | 0                       |
| Cinematography  | 0                    | 0                     | 0                       |

**Score sourcing rule (hard rule, Tanzim stated explicitly):**
> "Unless there is specific data from any source I've given you, do not fill if you don't have information."
- Zeros are correct and intentional when no data source exists.
- Do NOT guess or interpolate scores. If uncertain, ask.
- Tanzim's Fitness Training = 9, Athlete = 9 sourced from: "12 years of fitness training experience, coached bodybuilding athlete who won 17 gold medals."

---

## PIL Composite Architecture

```python
BG_COLOR = (0, 0, 0)
final = Image.new("RGB", (W, H), BG_COLOR)
draw_final = ImageDraw.Draw(final)

# 1. Draw title in PIL
f_title = get_font(22, bold=True)
title_text = "FOUNDING TEAM  ·  SKILLS RADAR"
tw = draw_final.textlength(title_text, font=f_title)
draw_final.text(((W - tw) // 2, (TITLE_H - 22) // 2), title_text,
                fill=(255, 255, 255), font=f_title)

# 2. Paste radar below title
radar_resized = radar_img.resize((W, RADAR_H), Image.LANCZOS)
final.paste(radar_resized.convert("RGB"), (0, TITLE_H))

# 3. Cards below spacer
card_y = TITLE_H + RADAR_H + SPACER + GAP
```

---

## Cards (PIL, v20 approved)

Three PIL-drawn cards at the bottom. See `timbr_v20.py` for full `draw_card_pil()` function.

Card content (approved copy):
- **Tanzim Ozer** / Co-Founder · Product & Data Architecture
  - Narrative: "Built the market insight before the product."
  - Highlights: ["24H Fitness: 255 → #87 Nationwide", "$5.7M Closed · 9 Months @ US Bank"]
  - Tags: ["Product Strategy", "Operations", "Fitness Domain", "Analytics / DB"]
  - Accent: Cyan `(0, 200, 240)`

- **Sagar Giri** / Co-Founder · Chief Engineer
  - Narrative: "Now wiring every layer of TIMBR's stack."
  - Highlights: ["Amazon Prime Card Security Wall", "Amazon SDE L5 · Big-Tech Rigour"]
  - Tags: ["Backend", "Mobile Dev", "Data & Analytics", "AWS Cloud"]
  - Accent: Green `(0, 217, 107)`

- **Waseem Ahmad** / Founding Senior Engineer · AI Systems & Agentic Workforce
  - Narrative: "Solo-wiring the agentic core end-to-end."
  - Highlights: ["US Patent Holder", "ex-Meta Staff Engineer · ex-Google"]
  - Tags: ["Mobile Dev", "AI / ML", "Voice AI", "Android"]
  - Accent: Orange `(255, 101, 0)`

---

## WhatsApp Delivery
```bash
TOKEN=$(grep WHATSAPP_BRIDGE_TOKEN /home/hermes/.hermes/.env | cut -d= -f2)
curl -s -X POST "http://localhost:3000/send-media" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"chatId":"160799431606497@lid","filePath":"/home/hermes/timbr_radar_v20.png"}'
```
Note: key is `chatId` not `recipient`.

---

## Veronica QC Gate
- Minimum 8.0/10 to ship (7.5 accepted if content verified correct independently)
- Run via `browser_vision` with QC prompt after every render
- QC checks: axis count, polygon distinguishability, card readability, overall quality

---

## Pitfalls

1. **gridspec title subplot = broken axis labels** — top/bottom spokes clip into title or get cut. Fix: PIL title, matplotlib radar only.
2. **Even spoke count + no rotation = 12/6 o'clock labels** — always apply `+ np.pi / N` to theta_offset.
3. **Sales/AI/ML disappearing** — caused by gridspec stealing vertical space. Switched to `fig.add_axes()` with explicit [left, bottom, width, height].
4. **fill alpha > 0.07** — creates muddy muddy overlap at centre where all three polygons intersect.
5. **Zero scores are correct** — do not auto-fill missing scores. Tanzim will provide or they stay zero.
6. **Scope creep** — when Tanzim says "only the cards" or "only the radar", touch ONLY that. Confirmed multiple times.
7. **chatId vs recipient** — WhatsApp bridge uses `chatId`, not `recipient`. Wrong key = 400 error.
8. **pad_inches on savefig** — use 0.0, not 0.02. PIL controls spacing; matplotlib padding breaks alignment.

## Scoping Rule (hard)
Tanzim has stated multiple times: touch only what was asked.
- "I don't want the radar to be replaced only our cards" → cards only
- "Lock the radar, no changes from here" → radar frozen until explicitly lifted
When he says something is locked, treat it as immutable until he explicitly says "we're lifting that."
