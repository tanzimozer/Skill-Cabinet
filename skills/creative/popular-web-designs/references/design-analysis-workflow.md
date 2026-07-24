# Design Analysis & Replication Workflow

When a user wants to **replicate a live site's design** but the source platform has no automation API (Webflow, Squarespace, Wix visual editor), use this workflow.

## Pattern

1. **Capture the design**
   - Navigate to the target URL
   - If browser tools time out, use headless Playwright to screenshot (full page + above-fold)
   - Save screenshots to `/tmp/` for analysis

2. **Extract design tokens**
   - Analyze screenshots (programmatically or via vision tool when available)
   - Create structured breakdown as JSON:
     - Layout (max-width, grid columns, breakpoints)
     - Header (height, sticky behavior, components)
     - Color palette (bg, text, accent, borders)
     - Typography (font family, sizes, weights, hierarchy)
     - Spacing (section padding, gaps, margins)
     - Components (buttons, cards, image treatment)
   - Save to `/tmp/<project>_design_analysis.json`

3. **Create Trello breakdown** (optional but recommended for complex builds)
   - Define board structure from design analysis
   - Lists: Design Foundation, Structure & Layout, Components, Interactions, Responsive, Publishing
   - Cards: One per major task (header, hero, grid, footer, etc.)
   - Each card has checklist items with concrete steps
   - Use the `trello` skill to create programmatically

4. **Build in code** (not in the visual tool)
   - Write HTML/CSS/JS using the extracted design tokens
   - Use the relevant template from `popular-web-designs` if the style matches a known brand
   - Otherwise, generate from scratch using the JSON breakdown
   - Output: `index.html`, `css/style.css`, `js/script.js`, `README.md`

5. **Deliver to user**
   - Upload to Google Drive if they have access
   - Or create a GitHub repo if they provide credentials
   - Include deployment guide (Netlify, Vercel, GitHub Pages)

## Example: blog.ultrahuman.com Clone

**Input:** "Build a site like blog.ultrahuman.com in Webflow"

**Problem:** Webflow's visual editor has no automation API. Can only manage CMS content via REST API, not layouts/designs.

**Solution:** Pivoted to code-based build:

1. Screenshot blog.ultrahuman.com (timed out via browser, used Playwright)
2. Extracted design tokens:
   ```json
   {
     "colors": {
       "primary_bg": "#000000",
       "secondary_bg": "#1a1a1a",
       "accent": "#dd9949",
       "text_primary": "#ffffff",
       "text_secondary": "#a0a0a0"
     },
     "typography": {
       "font_family": "Inter",
       "h1": "48-64px",
       "h2": "32-40px",
       "h3": "24-28px",
       "body": "16-18px"
     },
     "layout": {
       "max_content_width": "1200-1400px",
       "grid_columns": "3 → 2 → 1 (responsive)"
     }
   }
   ```
3. Created Trello board: 9 lists, 23 cards covering full design breakdown
4. Built site in HTML/CSS/JS using extracted tokens
5. Uploaded to Google Drive: https://drive.google.com/drive/folders/1RHx4o5Nd9rkdP2W_y_coaD30DvA--Nrs

**Result:** Full responsive site ready to deploy, bypassing the visual-builder limitation.

## When to Use This Workflow

- User wants to replicate a site's design but the platform is GUI-only (Webflow, Squarespace, Framer, Wix visual editor)
- User wants design analysis before building (to understand structure before coding)
- User wants a Trello board to track the build (for delegation or phased execution)

## Design Analysis Script Template

```python
from playwright.sync_api import sync_playwright
import json

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={'width': 1920, 'height': 1080})
    page.goto(target_url, wait_until='networkidle', timeout=60000)
    
    # Screenshots
    page.screenshot(path='/tmp/site_fullpage.png', full_page=True)
    page.screenshot(path='/tmp/site_above_fold.png')
    
    browser.close()

# Manual analysis (or automated with vision API when available)
analysis = {
    "layout": {...},
    "header": {...},
    "colors": {...},
    "typography": {...},
    "spacing": {...},
    "components": {...}
}

with open('/tmp/site_design_analysis.json', 'w') as f:
    json.dump(analysis, f, indent=2)
```

## Trello Board Structure Template

```python
board_structure = {
    "board_name": "Site Build - [Project Name]",
    "lists": [
        {
            "name": "🎨 Design Foundation",
            "cards": [
                {"name": "Set up style guide & variables", "checklist": [...]},
                {"name": "Define typography scale", "checklist": [...]}
            ]
        },
        {
            "name": "🧱 Structure & Layout",
            "cards": [
                {"name": "Build header/navigation", "checklist": [...]},
                {"name": "Build footer", "checklist": [...]}
            ]
        },
        # ... more lists
    ]
}
```

## Pitfalls

- **Don't assume visual builders have APIs** — Most don't. Check documentation before promising automation.
- **Screenshot early** — Browser tools time out on heavy sites. Use Playwright with explicit waits.
- **Extract tokens, don't eyeball** — Structured JSON prevents guessing colors/spacing mid-build.
- **Build in code, not screenshots** — Pixel-perfect copying from screenshots wastes time. Extract principles, build clean.
- **README is critical** — User needs deployment guide + customization instructions.

## Related Skills

- `webflow` — CMS content management via API (not visual design)
- `trello` — Board/card creation via API
- `popular-web-designs` — 54 pre-built design systems (when style matches a known brand)
- `claude-design` — Design process and taste (when creating from scratch)
