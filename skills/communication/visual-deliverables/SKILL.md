---
name: visual-deliverables
category: communication
description: Producing high-quality visual charts, diagrams, and infographics as image files (PNG/JPEG) for Tanzim — org maps, architecture diagrams, roadmaps, ecosystem flywheels, etc.
triggers:
  - "visualise / visualize"
  - "make a chart / diagram / map"
  - "send me an image of"
  - "create a visual"
  - "PNG / JPEG / image format"
---

# Visual Deliverables

## When to use
Any time Tanzim asks for charts, maps, diagrams, infographics, or visual summaries delivered as image files. He expects high-quality PNGs sent directly to WhatsApp.

## Stack — Two valid paths depending on aesthetic

### Path A: HTML/CSS → Playwright → PNG (light/Apple style)
Tanzim's default preference for polished, Apple-aesthetic deliverables:
1. **Write HTML/CSS files** — Apple-style aesthetics (see style guide below)
2. **Render with Playwright** (already in hermes venv) → PNG
3. **Send via WhatsApp** `/send-media`

### Path B: matplotlib → PNG (dark/neon/radar style)
Valid and approved for dark-background compositions — specifically radar charts, skills maps, and neon-palette visuals. Tanzim has approved and iterated on matplotlib dark radar builds (July 2026).

**matplotlib is NOT for light-background deliverables** — those must use Playwright/HTML. The "cartoon" rejection applies to light-theme bar/pie charts, not dark radar compositions.

Use matplotlib when:
- Dark background (`#070A13` or similar) is specified
- Radar/spider charts are the primary element
- Neon colour palette (cyan/green/orange polygons)

See `references/timbr-team-radar-dark-matplotlib.md` for the full approved spec.

### Rendering pipeline

```python
# Write HTML to /tmp/timbr_chartN.html, then:
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1600, "height": 1000})
    page.goto(f"file:///tmp/timbr_chart1.html")
    page.wait_for_timeout(500)
    page.screenshot(path="/tmp/timbr_chart1.png", full_page=False)
    browser.close()
```

Run via: `~/.hermes/hermes-agent/venv/bin/python3 /tmp/render_script.py`

Then send:
```json
POST http://localhost:3000/send-media
{
  "chatId": "<target>",
  "filePath": "/tmp/timbr_chart1.png",
  "mediaType": "image",
  "caption": "TIMBR · Chart Name"
}
```

## Apple-style CSS design system (Tanzim's approved aesthetic)

```css
/* Base */
body {
  background: #FAFAFA;
  font-family: -apple-system, 'SF Pro Display', 'Helvetica Neue', Arial, sans-serif;
  color: #1A1A1A;
}

/* Surfaces */
--bg-card: #FFFFFF;
--bg-page: #FAFAFA;
--bg-section: #F5F5F7;   /* Apple light grey */
--border: #E5E5EA;        /* Apple divider */

/* Text */
--text-primary: #1A1A1A;
--text-secondary: #636366;
--text-tertiary: #8A8A8E;
--text-label: #AEAEB2;    /* section labels, all-caps 9px */

/* Accent colours (muted, Apple-like) */
--teal:   #00897B;  --teal-bg:   #E0F2F0;
--blue:   #1976D2;  --blue-bg:   #E8F1FB;
--purple: #7B1FA2;  --purple-bg: #EDE8FD;
--orange: #D1510A;  --orange-bg: #FBF0E8;
--green:  #2E7D32;  --green-bg:  #E5F5EB;
--red:    #C62828;  --red-bg:    #FAE8E8;
--amber:  #F57C00;  --amber-bg:  #FFF3E0;
--slate:  #455A64;  --slate-bg:  #ECEFF1;

/* Cards */
border-radius: 14–18px;
box-shadow: 0 2px 8px rgba(0,0,0,0.06);
border: 1px solid #E5E5EA;
padding: 20–28px;

/* Section labels */
font-size: 9–10px; font-weight: 700; letter-spacing: 1.4px; text-transform: uppercase; color: #AEAEB2;

/* Accent tops on cards */
border-top: 3px solid <accent-color>;
```

Key rules:
- **White background always** — no dark mode for Tanzim deliverables
- Generous whitespace (padding 20–36px, gap 16–20px)
- Muted colour accents, never garish
- Small all-caps labels above each section (9px, letter-spacing 1.4px)
- Cards have subtle shadow + 1px border, never heavy outlines
- Viewport: 1600×1000 for landscape charts, 1600×1100 for tall ones

## Chart types used
- **Team / Org Map** — two-column layout with divider, layered rows by function, accent-top cards
- **Business Architecture** — side-by-side engine columns, step cards with arrows, shared foundation bar at bottom
- **Roadmap** — horizontal timeline, phase dots on spine, detail cards below
- **Ecosystem / Flywheel** — CSS grid tile layout (3-col), each tile colour-coded by domain

## Multi-chart delivery
When Tanzim asks for "3–4 different visuals", produce all four:
1. Team map
2. Business/systems architecture
3. Roadmap / timeline
4. City ecosystem / summary tiles

Write each chart as a separate HTML file → render all via one Playwright script → send sequentially with 2s sleep between.

## Pitfalls
- **matplotlib = cartoon (light theme only)** — Tanzim rejected matplotlib for light-background charts. Dark-theme radar is approved — see Path B above.
- **Browser viewport lies on tall PNGs** — for PNGs taller than ~1200px, browser_vision on the full file will report clipping that doesn't exist. QC by cropping the bottom 300px with PIL and checking that strip separately.
- **matplotlib radar fill alpha** — keep fill alpha ≤ 0.07 for overlapping polygons. Higher creates muddy blended zones at overlap.
- **matplotlib label placement** — use ax.set_ylim(0, 13.5) and place axis labels at r=11.5 to push them clear of the outermost ring (10). Without ylim expansion, labels clip or overlap the ring.
- **gridspec title subplot kills top/bottom axis labels** — if a title subplot steals vertical space from the radar, the topmost spoke label bleeds into it (looks like a subtitle) and the bottommost spoke clips. Fix: draw title in PIL on the composite; give matplotlib the entire figure for the polar axes via `fig.add_axes([0.08, 0.08, 0.84, 0.84], projection='polar')`.
- **Even spoke count needs half-rotation offset** — with N spokes, `set_theta_offset(np.pi/2)` puts one label exactly at 12 o'clock and one at 6 o'clock. Always apply `set_theta_offset(np.pi/2 + np.pi/N)` to stagger labels off the cardinal axes.
- **Zero scores are intentional** — Tanzim's rule: "Unless there is specific data from a source I've given you, do not fill." Zeros stay zero. Never interpolate or guess scores for the radar.
- **chatId not recipient** — WhatsApp `/send-media` endpoint uses `chatId` key. Using `recipient` returns 400.
- Playwright is in the hermes venv: `~/.hermes/hermes-agent/venv/bin/python3`
- `execute_code` sandbox does NOT have Playwright or matplotlib — always use `terminal` with venv python
- `page.wait_for_timeout(400–500)` needed before screenshot to let CSS render
- `full_page=False` for fixed-size viewport screenshots
- For viewport > 1600px wide, adjust viewport in `new_page()` accordingly
- Google/DDG/Bing all CAPTCHA the VM IP — search scraping via Playwright on this VM is not viable
- **DO NOT use `send_message` with `image::` prefix to deliver PNGs** — this returns 401. Use the REST endpoint: `POST http://localhost:3000/send-media` with `filePath`, `chatId`, `mediaType: "image"`. See rendering pipeline above.
- **Never retry a failed delivery method twice** — if the first send_message image attempt 401s, switch to the REST endpoint immediately. Repeating the same broken call is the recurring mistake Tanzim flags.
- **Partial redesign = only touch what was asked** — if Tanzim says "only the cards" or "only the X", leave every other element untouched. Confirm scope before rebuilding the whole composition.
- `execute_code` sandbox does NOT have Playwright or matplotlib — always use `terminal` with venv python
- `page.wait_for_timeout(400–500)` needed before screenshot to let CSS render
- `full_page=False` for fixed-size viewport screenshots
- For viewport > 1600px wide, adjust viewport in `new_page()` accordingly
- Google/DDG/Bing all CAPTCHA the VM IP — search scraping via Playwright on this VM is not viable
- **DO NOT use `send_message` with `image::` prefix to deliver PNGs** — this returns 401. Use the REST endpoint: `POST http://localhost:3000/send-media` with `filePath`, `chatId`, `mediaType: "image"`. See rendering pipeline above.
- **Never retry a failed delivery method twice** — if the first send_message image attempt 401s, switch to the REST endpoint immediately. Repeating the same broken call is the recurring mistake Tanzim flags.
- **Partial redesign = only touch what was asked** — if Tanzim says "only the cards" or "only the X", leave every other element untouched. Confirm scope before rebuilding the whole composition.

## References
- `references/timbr_chart_palette.md` — TIMBR colour palette and box style reference (may be superseded by Apple palette in SKILL.md)
- `references/html_chart_templates.md` — reusable HTML/CSS chart skeletons (Playwright render pipeline + all card/timeline/engine patterns)
- `references/timbr-team-radar-card-design.md` — TIMBR team radar + credential card layout (Playwright/HTML, light theme, July 2026)
- `references/timbr-team-radar-dark-matplotlib.md` — TIMBR dark radar approved spec (matplotlib, neon palette, 3-line bottom cards, July 2026)
