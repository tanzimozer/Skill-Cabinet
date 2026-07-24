---
name: matplotlib-pitch-visuals
category: data-visualisation
description: Creating investor/pitch-deck quality A4 PNGs with matplotlib — radar charts, credential cards, team profiles
triggers:
  - pitch deck visual
  - team radar chart
  - A4 PNG matplotlib
  - credential cards
  - investor visual
  - team profile image
---

# Matplotlib Pitch Visuals

## Canvas setup

**Default: Landscape A4 @ 150 dpi** (user preference for team profile visuals):

```python
matplotlib.use('Agg')  # always first — no display required
fig = plt.figure(figsize=(14.07, 10.0), facecolor=BG, dpi=150)
# Output: ~2110×1500 px
plt.savefig("output.png", dpi=150, bbox_inches='tight', facecolor=BG)
```

Portrait A4 `(10, 14.07)` is available but NOT used for TIMBR team profiles — see Layout section.

## Colour palette (TIMBR team standard)

```python
BG     = "#0d0d0d"   # page background
CYAN   = "#00d4ff"   # Tanzim
GREEN  = "#00e676"   # Sagar
ORANGE = "#ff6d00"   # Waseem Ahmad
GOLD   = "#ffd700"   # footer accent
WHITE  = "#ffffff"
LGREY  = "#888888"
CARDBG = "#111111"   # card fill
```

## Layout: radar top, cards bottom

Use `fig.add_axes([x, y, w, h])` for precise absolute placement.

Stable split that works:
- Radar: `[0.07, 0.44, 0.86, 0.52]` (top 52%)
- Cards: y0=0.052, h=0.36 each, 3-wide with gap=0.022
- Footer: `[0, 0, 1, 0.040]`

## Card legibility rules (hard-won)

The most common failure mode is text too small to read at pitch-deck scale. Rules:

1. **Less content, bigger type** — never more than 3 stat lines per card. Cut ruthlessly.
2. **Pitch format, not CV format** — coloured bold stat LABEL (9–10pt), grey subdescription below (7.5–8pt). NOT a paragraph of wrapped text.
3. **Stat lines need vertical breathing room** — minimum 0.10 fig-fraction gap between each stat block (label + sub).
4. **No textwrap** — if a line needs wrapping, it's too long. Shorten the text.
5. **Skill tags** — evenly spaced with `np.linspace(0.15, 0.85, n)`, FancyBboxPatch pill, 6–7pt font. Max 3 tags.
6. **Card height** — minimum 0.36 fig-fraction for 3 stat lines to breathe.

## Card anatomy (working pattern)

```
┌─────────────────────────────┐  ← colour top bar (name, bg=col, fg=BG, 10.5pt bold)
│  NAME                       │
├─────────────────────────────┤
│  ROLE  [BADGE PILL]         │  ← 7pt role + FancyBboxPatch badge, right-aligned
│  Pedigree line              │  ← 10.5pt bold white — biggest readable line
│  Hook. Italic grey.         │  ← 8.5pt italic #aaaaaa
├╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌┤  ← axhline rule
│  STAT LABEL    9.5pt col    │
│  sub text      7.5pt grey   │
│                             │
│  STAT LABEL                 │
│  sub text                   │
│                             │
│  CLAIM LINE   9.5pt col bold│  ← the punch line
├╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌┤
│  [tag1]  [tag2]  [tag3]     │  ← FancyBboxPatch pills, evenly spaced
└─────────────────────────────┘
  col accent bar (alpha=0.18)    ← bottom glow strip
```

## Radar chart setup (polar)

```python
rax = fig.add_axes([0.07, 0.44, 0.86, 0.52], facecolor=BG, polar=True)
angles = np.linspace(0, 2*np.pi, N, endpoint=False).tolist()
angles += angles[:1]  # close the polygon

for name, (scores, col) in teams.items():
    vals = scores + scores[:1]
    rax.plot(angles, vals, color=col, linewidth=2.4, zorder=3)
    rax.fill(angles, vals, color=col, alpha=0.13)
    rax.scatter(angles[:-1], scores, color=col, s=45, zorder=4)

rax.set_ylim(0, 10)
rax.set_facecolor(BG)
rax.spines['polar'].set_color("#333")
rax.grid(color="#252525", linewidth=0.8)
```

## Legend placement

One legend row below the radar, using `fig.text()` — NOT radar_ax.legend() which clips.

```python
legend_y = 0.457
for name, role, col, lx in legend_items:
    fig.text(lx,       legend_y, "●", color=col, fontsize=10, ha='left', va='center')
    fig.text(lx+0.025, legend_y, f"{name}  ·  {role}",
             color=WHITE, fontsize=7.5, ha='left', va='center', fontfamily='monospace')
```

## Footer

**USER PREFERENCE: No footer on TIMBR team visuals.** Tanzim explicitly rejected the footer — eliminate it entirely. Do not add it back unless he asks.

```python
# OMIT FOOTER — Tanzim does not want it
```

## Vision QA loop

After saving, navigate browser to `file:///path/to/output.png` then call `browser_vision()` to verify legibility before sending. Ask specifically: "Is all text fully readable? Any truncation or overlap?" — the model will score it.

## Layout: landscape vs portrait

**For TIMBR team profile: LANDSCAPE A4** (user corrected this explicitly).
- Portrait stacks three cards side-by-side — they're too narrow, text truncates.
- Landscape: radar LEFT ~44%, cards RIGHT ~54% stacked vertically — 3 cards get full width.

```python
fig = plt.figure(figsize=(14.07, 10.0), facecolor=BG, dpi=150)  # landscape A4
```

Card proportions that work in landscape:
- `cw = 0.520`, `ch = 0.278`, `gap = 0.018` between cards
- Bottom edges: `tops = [0.700, 0.392, 0.084]`
- Left edge: `rx0 = 0.462`

Vertical divider between radar and cards:
```python
dax = fig.add_axes([0.450, 0.04, 0.002, 0.93])
dax.set_facecolor("#202020")
```

## Card template (uniform — all three same structure)

**USER PREFERENCE: all three cards must use identical layout** — same structure, same proportions, only colour and content differ. User explicitly rejected mixed layouts (different card styles per person).

Working uniform template:
```
┌─────────────────────────────────────────────┐  ← colour banner (15–16% height)
│  NAME  (15pt bold, fg=BG)                   │
├─────────────────────────────────────────────┤
│  ROLE (9.5pt bold, col)    Pedigree (9pt)   │  ← two separate text() calls
├╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌┤  ← axhline rule
│ CREDENTIALS (label 7.5pt)  │ DOMAINS (label)│  ← axvline separator at x≈0.578
│  · line 1  (9pt #d0d0d0)   │  [tag pill]    │
│  · line 2                  │  [tag pill]    │
│  · line 3                  │  [tag pill]    │
│                             │  [tag pill]    │
├╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌┤
│ bottom accent strip (col, alpha=0.18)        │
└─────────────────────────────────────────────┘
```

Font sizing that passes QC:
- Name: 15pt bold
- Role: 9.5pt bold col
- Pedigree: 9pt #999999
- Credential lines: 9pt #d0d0d0
- Section labels (CREDENTIALS/DOMAINS): 7.5pt bold col
- Domain tags: 8pt bold col

## Pitfalls

- **Score bars / abbreviated axes** — never use these on pitch cards. They're unreadable at scale and look like a data dump, not a pitch. Kill them.
- **textwrap in cards** — causes truncation artifacts. Shorten the text instead.
- **too many words** — each stat line should be ≤5 words label + ≤6 words sub. If it's longer, the card is a CV, not a pitch.
- **3 items per row in legend** — gets too cramped at 10-inch width. Use 2 rows or abbreviate roles.
- **card height too short** — stat blocks stack too tight, items overlap. Give each card at least h=0.278 in landscape.
- **portrait layout for 3 cards** — DO NOT stack 3 cards side-by-side on portrait A4. They're too narrow. Use landscape.
- **footer** — Tanzim does not want a footer on TIMBR team visuals. Omit entirely.
- **monospace font for all text** — fine for terminal card style but signals "developer demo" not "investor pitch" when used everywhere. Use default sans-serif for credential body text; monospace for decorative headers only.
- **duplicate va= kwarg** — Python raises SyntaxError if you pass `va='center'` twice in one `text()` call. Common when copy-pasting. Check before running.
- **mixed card styles** — user rejected having each person use a different card style (terminal, stat-block, etc.). Stick to one uniform template.
- **vision QA gate** — do NOT send until browser_vision scores readability ≥8/10 AND professional feel ≥8/10. If either is below, fix and re-QA. Sending prematurely wastes iterations and frustrates user.

## TIMBR team data (scores /10)

| Dimension     | Tanzim | Sagar | Waseem |
|---------------|--------|-------|--------|
| AI / ML       | 5      | 6     | 9      |
| Backend       | 4      | 9     | 5      |
| Mobile Dev    | 3      | 7     | 10     |
| Fitness Domain| 10     | 3     | 2      |
| Leadership    | 9      | 5     | 6      |
| Product Strat | 9      | 5     | 4      |
| Data & Analytics| 8    | 7     | 5      |
| Frontend      | 2      | 6     | 3      |

See `references/timbr-team-profiles.md` for full credential detail.
