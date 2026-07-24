---
name: visual-charts-and-diagrams
description: Generating high-quality visual charts, org maps, roadmaps, and diagrams for Tanzim — pitch-deck presentable quality.
triggers:
  - "visualise this"
  - "make a chart"
  - "create a diagram"
  - "org chart"
  - "roadmap visual"
  - "give me images of"
  - "make visuals"
---

# Visual Charts & Diagrams

## Critical rule: NEVER use matplotlib for presentable output
Matplotlib produces cartoon-quality, unreadable visuals — Tanzim explicitly rejected these as "not presentable". It is only acceptable for internal/debug use.

## Correct stack: HTML/CSS → Playwright → PNG
1. Write clean HTML/CSS (Apple-style aesthetic — see below)
2. Render via Playwright: `chromium.launch()` → `page.screenshot()`
3. Output PNG at 1600×1000px, dpi=200
4. Send via WhatsApp `/send-media` endpoint

```python
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={"width": 1600, "height": 1000})
    page.goto(f"file://{html_path}")
    page.wait_for_timeout(500)
    page.screenshot(path=png_path, full_page=False)
    browser.close()
```

Playwright is installed in: `~/.hermes/hermes-agent/venv/bin/python3`

## Apple-style aesthetic (required)
- **Background:** `#FFFFFF` or `#FAFAFA`
- **Font:** `-apple-system, 'SF Pro Display', 'Helvetica Neue', Arial, sans-serif`
- **Primary text:** `#1D1D1F`
- **Secondary text:** `#6E6E73`
- **Dividers:** `#D2D2D7`
- **Cards:** white background, `border: 1px solid #E5E5EA`, `border-radius: 14–18px`, subtle `box-shadow`
- **Accent colours:** muted, Apple-like — `#0071E3` (blue), `#00837A` (teal), `#6E3FF3` (purple), `#D1510A` (orange), `#1A7F3C` (green), `#B72828` (red)
- **Colour accent on cards:** use `border-top: 3px solid [accent]` not full fill
- **Typography hierarchy:** clear size steps — 28–32px titles, 18–22px section headers, 13–16px body, 9–10px tags/labels (uppercase, letter-spacing)
- **Generous whitespace** — padding 28–44px, gaps 16–28px
- **No dark backgrounds, no gradients, no cartoonish colours**

## Chart types & layout patterns

### Org / Team Map
- Header bar (BG2), title + subtitle
- Founder row centred with connector line
- Two-column split (technology left, commercial right)
- Vertical divider line between columns
- Cards stacked with clear section labels

### Business Architecture (two-engine)
- Header + vertical dashed divider splitting left/right engines
- Numbered steps with colour-coded top border
- Arrow connectors (↓) between steps
- Shared foundation bar at bottom

### Roadmap (horizontal timeline)
- `::before` pseudo-element for spine line
- Phase circles (numbered) sitting on the line
- Cards hanging below with bullet points
- "NOW" badge on current phase
- Subtitle shows full sequence: Phase 1 → 2 → 3…

### Ecosystem / Flywheel
- CSS Grid tiles (3-col × 2-row) instead of circular layout
- Each tile = one domain, accent top-border colour-coded
- Pill tags for sub-items
- No matplotlib polar plots — they look amateur

## Delivery
- Send all images via `/send-media` with captions
- Always send as a set — don't send one then ask if they want more
- If feedback received, rebuild only the affected charts, not all four

## Known pitfalls
- **Playwright not in PATH** — always use full venv path: `~/.hermes/hermes-agent/venv/bin/python3`
- **execute_code sandbox doesn't have matplotlib** — use `terminal()` to run chart scripts
- **Circular flywheel layouts** in matplotlib look terrible — use grid tiles in HTML instead
- **Font rendering** — HTML/Playwright uses system fonts and renders beautifully; matplotlib does not
