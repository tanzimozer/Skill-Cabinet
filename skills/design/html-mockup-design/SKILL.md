---
name: html-mockup-design
description: "Build production-quality iOS/app UI mockups as self-contained HTML/CSS files, screenshot them, and deliver via WhatsApp or Drive."
version: 1.0.0
platforms: [linux, macos]
metadata:
  hermes:
    tags: [mockup, html, css, ios, ui, design, screenshot, timbr]
    related_skills: [whatsapp-send-document]
---

# HTML Mockup Design & Delivery

## When to use
User asks for app mockups, UI screens, design references, or "make this look like a production app."

## Workflow

### 1. Gather references BEFORE building
Always ask for (or check image cache for) reference screenshots before writing a line of CSS:
- The user's target design system (Robinhood, Linear, Notion, etc.)
- Any existing sketches / wireframes shared in chat
- Feature doc / PRD for spec details
- Check `~/.hermes/image_cache/` for recently received images

**Failure pattern:** Building from assumptions → Sagar rejected v1 and v2 because they didn't match his reference aesthetic. V3 only landed after references were studied.

### 2. Identify the design language
| App Reference | Key signals |
|---|---|
| Robinhood | Pure `#000000` bg, Gold `#C9A84C` accent, large hero numbers, minimal chrome, line chart motif, "TOTAL + big number" pattern |
| Linear | `#0F0F10` bg, purple/violet accents, dense data tables |
| Notion | Off-white bg, minimal sans, generous whitespace |

### 3. Build the file
- **Self-contained single HTML file** — no external dependencies, no CDN fonts, no remote images
- Phone frame: 393×852px (iPhone 15 Pro), `border-radius: 54px`, `overflow: hidden`
- Grid layout: `repeat(4, 393px)` for 4-up mockup sheets
- Status bar: notch pill `120×34px`, absolute centred top
- Bottom nav: 86px height, 5 icons minimum (Tanzim's apps always have 5 nav items)
- Use SVG inline for icons — never emoji-only, never `<img src="">` external

### 4. Gear / control visual language (Timbr-specific)
For Timbr workout logger sliders:
- Weight slider: Gold `#C9A84C` accent, hero value `font-size: 22px font-weight: 900`
- Reps slider: Purple `#A78BFA`
- Sets slider: Blue `#60A5FA`
- Use clean Robinhood-style track + thumb, NOT mechanical gear SVGs
- Exercise illustration: SVG silhouette of movement, gold fill, 0.18 opacity

### 5. Screenshot the file
```bash
chromium-browser --headless --disable-gpu \
  --screenshot=/home/hermes/out.png \
  --window-size=1820,1200 \
  --no-sandbox \
  "http://localhost:8765/file.html" 2>/dev/null
```
Serve with: `python3 -m http.server 8765` (background process).

### 6. Crop for WhatsApp delivery
WhatsApp bridge `/send-media` uses `filePath` — images must be <~5MB. Crop wide mockup sheets:
```python
from PIL import Image
img = Image.open("/home/hermes/out.png")
w, h = img.size
img.crop((0, 0, w, h//2 + 60)).save("/home/hermes/row1.png")
img.crop((0, h//2 - 60, w, h)).save("/home/hermes/row2.png")
```

### 7. Upload to Drive + send to group
```python
# Upload HTML file
service.files().create(body={"name": "Timbr-Mockup-v3.html", "mimeType": "text/html"},
    media_body=MediaFileUpload("/path/file.html", mimetype="text/html")).execute()

# Send screenshots + HTML to group via bridge
requests.post("http://localhost:3000/send-media",
    headers={"Authorization": f"Bearer {TOKEN}"},
    json={"chatId": "120363427118724513@g.us", "filePath": "/home/hermes/row1.png",
          "caption": "Timbr Mockup v3 · Screens 1–4"})
```

## Timbr colour system (v8 — verified from Robinhood refs)
```
--blk: #0C0804      warm black background (NOT pure #000000)
--s1: #1C1814       card background (warm dark gray)
--s2: #181410       secondary bg
--s3: #201C18       elevated surfaces
--bdr: #302C28      borders
--gold: #A88860     Robinhood Gold — bronze-amber H=33° S=29% L=52%
--gold-light: #B09068
--txt: #E0DCD8      cream text (NOT pure white)
--txt2: #A09C98     secondary text
--txt3: #686460     muted text
--coral: #E84040    Timbr coral-red — primary CTA
--grn: #22C55E      completed / DONE states
--pur: #A78BFA      reps slider
--blu: #60A5FA      sets slider
```

**CRITICAL:** The Robinhood gold is NOT saturated yellow (#F0D830, #C8A84C) — it's a muted bronze-amber (#A88860). Extract via pixel frequency analysis, not visual guessing.

## Pitfalls
- **Don't use `fill: var(--text)` globally on SVG** — it overrides `stroke`-only icons, breaking WiFi/battery in the status bar. Set fill/stroke per icon.
- **Video must be portrait** — 16:9 is landscape. For workout cards use `height: 150px` fixed, not `aspect-ratio: 16/9`
- **Gear SVGs as asterisks** — line spokes from centre look like sun icons, not gears. Either use proper tooth-path geometry via JS, or replace gears with Robinhood-style hero number + clean slider.
- **Don't include dev annotations** in mockup copy — "Path A — All Complete" type labels break production feel.
- **Journal must show ALL exercises** — not a subset. Sagar checks this.
- **Nav must have 5 items** — PRD specifies 5, Sagar checks this.
- **Undo popup progress bar** — show partially depleted (~60%) to communicate the 4s window.

## Iteration loop with Sagar
Sagar is the Timbr PM. He reviews mockups and gives corrections. Pattern:
1. Drop screenshots + HTML file in `TIMBR APP - PRD` group (`120363427118724513@g.us`)
2. If Sagar says "doesn't match my references" — ask him to drop reference screenshots directly in group
3. Analyse images from `~/.hermes/image_cache/` to extract design language
4. Rebuild and re-drop, same group

See `references/timbr-design-refs.md` for Sagar's confirmed reference screenshots and extracted design tokens.
See `references/color-extraction-workflow.md` for the pixel-frequency extraction technique.
