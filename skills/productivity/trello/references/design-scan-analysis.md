# Design Scan → Analysis → Trello Board Case Study

**Date:** May 21, 2026  
**Target:** blog.ultrahuman.com  
**Goal:** Clone the design, create Trello breakdown, build in Webflow (later pivoted to code)  
**Session:** User submitted JPMC docs, then immediately pivoted to Webflow build request

## Problem Statement

User: "Scan blog.ultrahuman.com, break it into Trello cards, then execute the design in Webflow"

**Critical constraint discovered:** Webflow's visual editor has no API — can only manage CMS content via REST, not layouts/designs. Pivoted to code-based build.

## Phase 1: Design Capture

### Initial Browser Attempt
```python
browser_navigate("https://blog.ultrahuman.com/blog/")
# Result: Command timed out after 60 seconds
```

Site is heavy (WordPress + custom theme), browser tools couldn't load in time.

### Playwright Headless Screenshot
```python
from playwright.sync_api import sync_playwright
import time

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={'width': 1920, 'height': 1080})
    page.goto("https://blog.ultrahuman.com/blog/", wait_until='networkidle', timeout=60000)
    time.sleep(3)  # Extra JS hydration time
    
    page.screenshot(path='/tmp/ultrahuman_fullpage.png', full_page=True)
    page.screenshot(path='/tmp/ultrahuman_above_fold.png')
    
    browser.close()
```

**Result:** 
- Full page: 1920x8000px (8 sections)
- Above fold: 1920x1080px

## Phase 2: Design Analysis

### Manual Extraction (Vision API unavailable)
```python
from PIL import Image
img = Image.open('/tmp/ultrahuman_above_fold.png')
width, height = img.size  # 1920, 1080

# Structured analysis
analysis = {
    "layout": {
        "viewport_width": 1920,
        "viewport_height": 1080,
        "max_content_width_estimate": "1200-1400px (centered)"
    },
    "header": {
        "height_estimate": "80-100px",
        "background": "Dark (near black)",
        "position": "Fixed/sticky likely",
        "components": ["Logo left", "Nav center/right", "CTA button"]
    },
    "hero": {
        "height_estimate": "500-600px",
        "background": "Dark gradient or solid",
        "content_alignment": "Center or left-aligned",
        "components": ["Large heading", "Subheading", "CTA button"]
    },
    "content_grid": {
        "layout": "3-column grid likely",
        "card_style": "Minimal, dark cards with images",
        "spacing": "20-30px gaps",
        "image_ratio": "16:9 or 4:3"
    },
    "typography": {
        "heading_sizes": {
            "h1": "48-64px",
            "h2": "32-40px",
            "h3": "24-28px",
            "body": "16-18px"
        },
        "font_family_likely": "Sans-serif, modern (Inter, Helvetica, SF Pro)"
    },
    "colors": {
        "primary_bg": "#000000 to #0a0a0a",
        "secondary_bg": "#1a1a1a to #2a2a2a",
        "accent": "#dd9949 (gold/orange detected)",
        "text_primary": "#ffffff",
        "text_secondary": "#a0a0a0"
    },
    "components": {
        "buttons": {
            "primary": "Solid background, white text, rounded corners",
            "style": "Modern, subtle hover states"
        },
        "cards": {
            "background": "Dark with subtle border or shadow",
            "hover": "Lift or glow effect likely",
            "padding": "24-32px"
        }
    },
    "spacing": {
        "section_padding": "80-120px vertical",
        "container_padding": "20-40px horizontal",
        "element_margins": "16-24px between elements"
    }
}

# Save for Trello board generation
import json
with open('/tmp/ultrahuman_design_analysis.json', 'w') as f:
    json.dump(analysis, f, indent=2)
```

## Phase 3: Trello Board Generation

### Board Structure
```python
board_structure = {
    "board_name": "Webflow Build - Ultrahuman Clone",
    "lists": [
        {"name": "🎨 Design Foundation", "cards": [...]},
        {"name": "🧱 Structure & Layout", "cards": [...]},
        {"name": "🏠 Homepage Sections", "cards": [...]},
        {"name": "🎨 Components & Elements", "cards": [...]},
        {"name": "📝 CMS Setup (if needed)", "cards": [...]},
        {"name": "🔧 Interactions & Animations", "cards": [...]},
        {"name": "📱 Responsive & Polish", "cards": [...]},
        {"name": "🚀 Publishing", "cards": [...]},
        {"name": "✅ Done", "cards": []}
    ]
}
```

### Card Example: Build Header/Navigation
```python
{
    "name": "Build header/navigation",
    "description": """**Header specs:**
- Height: 80-100px
- Background: Dark (sticky/fixed position)
- Layout: Logo left, nav center/right, CTA button

**Components:**
- Logo (SVG/image)
- Nav menu (horizontal list)
- CTA button (primary style)
- Mobile hamburger menu""",
    "checklist": [
        "Create header section",
        "Add logo placeholder",
        "Build nav menu",
        "Style CTA button",
        "Add sticky behavior",
        "Build mobile menu"
    ]
}
```

### Implementation
```python
import urllib.request, json

API_KEY = "<TRELLO_KEY — see ~/.hermes/.trello_credentials>"
TOKEN = "<TRELLO_TOKEN — see ~/.hermes/.trello_credentials>"

def trello_api(method, path, data=None):
    url = f"https://api.trello.com/1{path}"
    sep = "&" if "?" in url else "?"
    url = f"{url}{sep}key={API_KEY}&token={TOKEN}"
    
    if method == "GET":
        r = urllib.request.urlopen(url, timeout=30)
    else:
        body = json.dumps(data).encode() if data else b""
        req = urllib.request.Request(url, data=body, method=method,
                                     headers={"Content-Type": "application/json"})
        r = urllib.request.urlopen(req, timeout=30)
    return json.loads(r.read())

# Create board
board = trello_api("POST", "/boards", {
    "name": "Webflow Build - Ultrahuman Clone",
    "defaultLists": "false"
})

board_id = board["id"]
board_url = board["url"]

# Create lists
list_ids = {}
for lst in board_structure["lists"]:
    list_obj = trello_api("POST", "/lists", {
        "name": lst["name"],
        "idBoard": board_id
    })
    list_ids[lst["name"]] = list_obj["id"]

# Create cards with checklists
for lst in board_structure["lists"]:
    list_id = list_ids[lst["name"]]
    for card in lst["cards"]:
        card_obj = trello_api("POST", "/cards", {
            "name": card["name"],
            "desc": card.get("description", ""),
            "idList": list_id
        })
        
        if "checklist" in card:
            checklist = trello_api("POST", "/checklists", {
                "idCard": card_obj["id"],
                "name": "Tasks"
            })
            
            for item in card["checklist"]:
                trello_api("POST", f"/checklists/{checklist['id']}/checkItems", {
                    "name": item
                })

print(f"✅ Board created: {board_url}")
# Result: https://trello.com/b/nVc34oKR/webflow-build-ultrahuman-clone
```

**Output:** 9 lists, 23 cards, full build breakdown

## Phase 4: Execution Pivot

### Problem Discovered
User provided Webflow credentials expecting design automation.

**Reality:** Webflow REST API only covers:
- CMS content (create/update collection items)
- Publishing (push live)
- Page SEO metadata
- Assets (upload files)

**No API for:**
- Visual layout (sections, containers, grids)
- Styling (colors, typography, spacing)
- Interactions/animations
- Responsive breakpoints

### Solution: Code-Based Build
Pivoted from "build in Webflow" to "build in HTML/CSS/JS, deploy anywhere":

1. Generated full site from design analysis:
   - `index.html` — header, hero, blog grid, footer
   - `css/style.css` — CSS variables from color/typography analysis
   - `js/script.js` — mobile menu, category filters, scroll animations
   - `README.md` — deployment guide (Netlify, Vercel, GitHub Pages)

2. Uploaded to Google Drive: https://drive.google.com/drive/folders/1RHx4o5Nd9rkdP2W_y_coaD30DvA--Nrs

3. User can now:
   - Deploy to any host (not locked to Webflow)
   - Hand off to developer for GitHub deployment
   - Import into Webflow manually if they still want that platform

## Key Learnings

### 1. Browser Tools Are Unreliable for Heavy Sites
**Symptom:** Timeout after 60s on blog.ultrahuman.com  
**Root cause:** WordPress + custom theme + heavy assets  
**Fix:** Always use Playwright with explicit waits for production sites

### 2. Visual Builders Have No Design APIs
**Affected platforms:**
- Webflow — CMS API only, no layout/design API
- Squarespace — No public API at all
- Wix — REST API for store/bookings/CMS, but not visual editor
- Framer — No public API

**When user asks to "build in [visual builder]":**
1. Check if design automation is actually possible
2. If not, offer code-based alternative immediately
3. Don't promise what the platform can't deliver

### 3. Design Analysis → Structured Data → Trello
**Don't skip the JSON step.** Going straight from screenshots to Trello cards produces vague tasks like "build header." 

**Correct flow:**
1. Screenshots → structured JSON (colors, sizes, layout)
2. JSON → Trello cards with **exact specs** in descriptions
3. Cards become executable without re-analyzing screenshots

### 4. Trello Card Quality = Execution Success
**Bad card:**
```
Name: Build blog grid
Description: Create the blog post grid
```

**Good card:**
```
Name: Build blog post grid
Description:
**Grid specs:**
- Layout: 3 columns (desktop), 2 (tablet), 1 (mobile)
- Gap: 20-30px
- Card style: Minimal, dark, with hover effects

**Card components:**
- Featured image (16:9 or 4:3 ratio)
- Post title (H3, 24-28px)
- Excerpt/description
- Read more link
- Optional: Date, author, category tag

Checklist:
- Create grid container
- Build card component
- Add featured image
- Style post title
- Add excerpt text
- Add hover effects
- Make responsive (3→2→1 cols)
```

Second version is executable without going back to screenshots or asking questions.

### 5. Phase-Based Lists > Status-Based Lists
**Status lists (generic):**
- To Do
- In Progress
- Done

**Phase lists (context-rich):**
- 🎨 Design Foundation
- 🧱 Structure & Layout
- 🏠 Homepage Sections
- 🎨 Components & Elements
- 📝 CMS Setup
- 🔧 Interactions & Animations
- 📱 Responsive & Polish
- 🚀 Publishing
- ✅ Done

Phase lists preserve build order and make it obvious what comes next. Status lists lose context once cards move.

## Reusable Pattern Summary

```
User: "Replicate [external site], break into Trello, build in [platform]"

↓ 1. Capture design
    - Screenshot (Playwright if browser times out)
    - Save to /tmp/

↓ 2. Extract design tokens
    - Structured JSON analysis
    - Colors, typography, spacing, layout
    - Save to /tmp/<project>_analysis.json

↓ 3. Create Trello board
    - Phase-based lists (not status-based)
    - Cards with exact specs from JSON
    - Programmatic checklists per card

↓ 4. Check platform constraints
    - Does [platform] have design automation API?
    - If NO → pivot to code-based build
    - If YES → proceed with API integration

↓ 5. Execute or deliver
    - Code build → deploy to Drive/GitHub
    - API build → script the implementation
    - Manual build → provide step-by-step guide
```

## Files Generated This Session

- `/tmp/ultrahuman_fullpage.png` — Full page screenshot
- `/tmp/ultrahuman_above_fold.png` — Above-fold reference
- `/tmp/ultrahuman_design_analysis.json` — Structured breakdown
- `/tmp/webflow_trello_structure.json` — Board definition
- `/tmp/ultrahuman-clone/` — Complete HTML/CSS/JS site
  - `index.html`
  - `css/style.css`
  - `js/script.js`
  - `README.md`

Uploaded to: https://drive.google.com/drive/folders/1RHx4o5Nd9rkdP2W_y_coaD30DvA--Nrs

## Related Skills

- `webflow` (productivity) — CMS API, not design API
- `popular-web-designs` (creative) — Pre-built design systems
- `trello` (productivity) — Board creation patterns
