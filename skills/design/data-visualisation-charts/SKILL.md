---
name: data-visualisation-charts
description: Generating high-quality presentable charts and visual maps for Tanzim — team structures, roadmaps, architecture diagrams, ecosystem flywheels.
---

# Data Visualisation & Charts

## Critical lesson — NEVER use matplotlib for presentable output

Tanzim explicitly rejected matplotlib charts as "cartoon", "not presentable", "not aesthetic", "not readable". **matplotlib = internal debugging only.** Never deliver matplotlib output to Tanzim or any stakeholder.

## The correct stack

**HTML + CSS → Playwright screenshot → PNG**

This is the only approach that produces presentation-quality output.

### Workflow
1. Write clean HTML/CSS
2. Save to `/tmp/chart_name.html`
3. Render via Playwright (venv python):
```python
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={"width": 1600, "height": 1000})
    page.goto(f"file:///tmp/chart_name.html")
    page.wait_for_timeout(500)
    page.screenshot(path="/tmp/chart_name.png", full_page=False)
    browser.close()
```
4. Send via WhatsApp `/send-media` with filePath (absolute path)

**Playwright is in:** `~/.hermes/hermes-agent/venv/bin/python3`
Run as: `~/.hermes/hermes-agent/venv/bin/python3 script.py`

## Apple-style design principles (Tanzim's preference)

- **Background:** `#FAFAFA` (page) / `#FFFFFF` (cards)
- **Font:** `-apple-system, 'SF Pro Display', 'Helvetica Neue', Arial, sans-serif`
- **Primary text:** `#1A1A1A` · Secondary: `#636366` · Tertiary: `#AEAEB2`
- **Cards:** white bg, `border: 1px solid #E5E5EA`, `border-radius: 14–18px`, subtle `box-shadow: 0 2px 8px rgba(0,0,0,0.06)`
- **Accent colours (muted, never garish):**
  - Teal `#00897B` · Blue `#1976D2` · Purple `#7B1FA2`
  - Amber `#F57C00` · Green `#2E7D32` · Red `#C62828`
- **Accented cards:** `border-top: 3px solid {colour}` — clean Apple look
- **Section labels:** `9–10px; font-weight:700; letter-spacing:1.4px; text-transform:uppercase; color:#AEAEB2`
- **Generous whitespace:** padding 28–36px, gaps 16–20px
- **No gradients, no dark backgrounds, no neon**
- Dividers: `1px solid #E5E5EA` or `1px solid #F2F2F7`
- Header bar: `background:#F5F5F7; border-bottom:1px solid #E5E5EA`

## Chart types

### Team/Org map (1600×1000)
- Header bar + title/subtitle
- Founders row connected by thin line + dot
- Section ALL-CAPS labels in tertiary colour
- Two-column split: ops left, commercial right
- Vertical divider between columns

### Architecture — Two-engine (1600×1000)
- Two columns, dashed vertical divider
- Steps: white card + coloured border-top + `↓` arrow connector
- Foundation bar full-width at bottom (absolute positioned)

### Roadmap — Horizontal timeline (1600×900)
- `::before` spine line at fixed Y
- Phase nodes: numbered circles with `box-shadow`
- Phase cards below line, bullet lists inside
- "NOW" badge on current phase (dark pill, white text)
- Phase order for TIMBR: Fitness(01) → Nutrition(02) → Physio(03) → Events(04) → Healthcare(05)

### Ecosystem flywheel (1600×1000)
- CSS Grid 3×2, `.wide` and `.tall` modifiers
- Tiles: white card, `border-radius:18px`, accent-bar (4px × 48px) top-left
- Pill tags: `background:#F2F2F7; border-radius:99px; font-size:11px`

## TIMBR-specific content
- Tanzim: "Orchestrates · Automates · Directs" (not just strategy/infra)
- Sagar: "Builds · CTO · Product"
- Waseem: "Builds the machines · AI & Automation · 2.5–4% equity"
- BlackWire: "Raw footage + reference URL in → polished content out · SaaS"
- Roadmap: Fitness → Nutrition → Physio → **Events** → Healthcare (Events BEFORE Healthcare — confirmed)
- Always "TIMBR" never "Timber"
- Maureen: no AI language, no role introductions (she knows the team)
