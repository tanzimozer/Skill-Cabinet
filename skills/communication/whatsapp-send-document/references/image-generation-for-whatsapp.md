# Image Generation for WhatsApp — Quality Guide

## The matplotlib problem
Matplotlib output looks like "a cartoon" — dark backgrounds, misaligned text, low visual fidelity.
**Never use matplotlib for anything presentable to a stakeholder.**

## Correct approach: HTML → Playwright → PNG

```python
from playwright.sync_api import sync_playwright

charts = [('/tmp/chart1.html', '/tmp/chart1.png'), ...]

with sync_playwright() as p:
    browser = p.chromium.launch()
    for html_path, png_path in charts:
        page = browser.new_page(viewport={"width": 1600, "height": 1000})
        page.goto(f"file://{html_path}")
        page.wait_for_timeout(500)
        page.screenshot(path=png_path, full_page=False)
    browser.close()
```

**Always use:** `~/.hermes/hermes-agent/venv/bin/python3` (NOT system python3 or execute_code)
Playwright is installed in the venv, not system-wide.

## Apple-style design system (Tanzim's preference)

```css
/* Core */
background: #FAFAFA;
font-family: -apple-system, 'SF Pro Display', 'Helvetica Neue', Arial, sans-serif;
color: #1A1A1A;

/* Cards */
background: #FFFFFF;
border: 1px solid #E5E5EA;
border-radius: 14px;  /* or 16-18px for larger cards */
box-shadow: 0 2px 8px rgba(0,0,0,0.06);
padding: 22px 28px;

/* Accent (top border of cards only) */
border-top: 3px solid <accent-color>;

/* Typography hierarchy */
/* Title */        font-size: 32px; font-weight: 700; color: #1A1A1A;
/* Section tag */  font-size: 9-10px; font-weight: 700; letter-spacing: 1.4px; text-transform: uppercase; color: #AEAEB2;
/* Body */         font-size: 13px; color: #636366; line-height: 1.6;

/* Dividers */
background: #E5E5EA;  /* never black */

/* Header bar */
background: #F5F5F7;  /* Apple light grey */
border-bottom: 1px solid #E5E5EA;
padding: 28px 60px;
```

## Colour palette (muted, Apple-like)
- Blue:   `#0071E3` / bg `#E8F1FB`
- Teal:   `#00897B` / bg `#E0F2F0`
- Purple: `#7B1FA2` / bg `#EDE8FD`
- Orange: `#D1510A` / bg `#FBF0E8`
- Green:  `#2E7D32` / bg `#E5F5EB`
- Red:    `#C62828` / bg `#FAE8E8`
- Gold:   `#8A6900` / bg `#FDF5DC`

## Workflow for multi-chart sets
1. Write HTML files to `/tmp/`
2. Render all in one Playwright session (reuse browser)
3. Send via `/send-media` with `mediaType: "image"` and a `caption`
4. 2-second sleep between sends to avoid bridge throttle

## Iterative feedback — what Tanzim rejects
- **Round 1 (matplotlib):** "It looks like a cartoon, this is not presentable"
- **Round 2 (HTML/Playwright):** Accepted the approach but flagged layout issues
- **Key complaints:** text too small, not aligned, not aesthetic, not readable
- **Fix:** Always use Apple design system above. White background. Min 11px fonts. Generous padding. Clean card hierarchy.

## Chart-specific layout patterns that work

### Team / org chart
- Two-column layout with vertical divider
- Left: technology stack; Right: commercial/marketing
- Cards with coloured top-border accent, not full colour fills
- Section labels: 9px, uppercase, letter-spaced, #AEAEB2

### Roadmap (horizontal timeline)
- CSS `::before` pseudo-element for the spine line — NOT matplotlib line
- Phase dots as circles with border-ring
- Cards below the line with coloured top border
- "NOW" badge on current phase

### Architecture (two-engine)
- Split view with vertical dashed divider
- Stepped flow within each side (arrow connectors = `↓` text, not SVG)
- Shared foundation bar pinned to bottom

### Ecosystem / flywheel
- CSS Grid 3×2 tile layout (NOT radial/circular — hard to read)
- Each tile: coloured accent bar, tag, title, pill tags
- One tall tile for roadmap list

## Pitfalls
- Dark backgrounds look terrible on WhatsApp — always white/light
- Small font sizes get crushed in WhatsApp image compression — minimum 11px
- Don't use `execute_code` for Playwright — wrong Python env, no playwright module
- Viewport 1600×1000 works well for landscape charts; 1200×900 for portrait/tall
- Roadmap subtitle: always state the full sequence in the header span (e.g. "Fitness → Nutrition → Physio → Events → Healthcare") — order matters, Tanzim will correct it
- **Order of phases matters** — Tanzim corrected Events before Healthcare. In TIMBR roadmap: Fitness → Nutrition → Physio → Events → Healthcare
- **Content for stakeholders:** Strip org chart detail when Maureen already knows the team. Focus on work streams (who builds what) not titles/positions.
- **AI language:** Maureen is not enthusiastic about AI — avoid AI terminology in anything sent to her. Use "automated systems", "operational infrastructure", "production pipeline" instead.
