---
name: ios-mockup-html
description: "Build production-quality iOS app screen mockups as self-contained HTML files — phone frames, status bar, bottom nav, component states."
version: 1.0.0
platforms: [linux, macos]
metadata:
  hermes:
    tags: [ios, mockup, html, css, design, ui, figma-alternative]
    related_skills: [whatsapp-send-document]
---

# iOS Mockup — HTML/CSS

## When to Use
When Tanzim or a collaborator asks for iOS app screen mockups, UI references, or design previews — and no Figma/design tool is available. Output is a single self-contained HTML file, no external dependencies.

## Design Language: Robinhood Dark

Tanzim's preferred aesthetic — Robinhood-inspired dark UI:

```css
:root {
  --bg: #080808;
  --card: #101010;
  --card2: #181818;
  --border: #1E1E1E;
  --border2: #282828;
  --accent: #E84545;           /* primary CTA, DONE states */
  --accent2: rgba(232,69,69,0.1);
  --green: #22C55E;            /* completed/success */
  --purple: #A78BFA;           /* secondary data */
  --blue: #60A5FA;             /* tertiary data */
  --amber: #F59E0B;            /* streak/warning */
}
font-family: -apple-system, 'SF Pro Display', 'Helvetica Neue', sans-serif;
```

Numbers are the heroes — make values LARGE and coloured.

## iPhone Frame (iPhone 15 Pro dimensions)

```css
.phone {
  width: 393px; height: 852px;
  background: #000;
  border-radius: 54px;
  border: 1.5px solid #222;
  overflow: hidden;
  box-shadow: 0 0 0 1px #0d0d0d, 0 48px 120px rgba(0,0,0,.9),
              inset 0 0 0 1px #252525, inset 0 0 100px rgba(232,69,69,.02);
}
```

## Status Bar

```html
<div class="sb"> <!-- height: 54px -->
  <span class="sb-t">9:41</span>
  <div class="sb-notch"></div>  <!-- Dynamic Island pill -->
  <div class="sb-r"><!-- signal + battery SVGs --></div>
</div>
```

⚠️ **Never use `svg { fill: var(--text) }` globally** — it breaks stroke-only icons. Set fill/stroke per SVG individually.

## Bottom Nav

- Always 5 icons for Timbr: Home / Workout / Chat / Progress / Profile
- Height: 86px, `border-top: 1px solid var(--border)`
- Active item: full opacity + accent colour label + 4px dot below
- Inactive: `opacity: 0.3`

## Layout: 4-column grid

```css
.grid {
  display: grid;
  grid-template-columns: repeat(4, 393px);
  gap: 36px 28px;
  justify-content: center;
}
```

## Gear Sliders (Timbr-specific)

Use JavaScript to render proper gear tooth profiles — NOT line/spoke SVGs.

```javascript
function gearPath(cx, cy, outerR, innerR, hubR, teeth, color, alpha) {
  const step = (Math.PI * 2) / teeth;
  const toothHalf = step * 0.28;
  const tipHalf   = step * 0.16;
  let pts = [];
  for (let i = 0; i < teeth; i++) {
    const a = i * step;
    pts.push([innerR, a - toothHalf]);
    pts.push([outerR, a - tipHalf]);
    pts.push([outerR, a + tipHalf]);
    pts.push([innerR, a + toothHalf]);
  }
  let d = '';
  pts.forEach(([r,a], i) => {
    const x = cx + r * Math.cos(a), y = cy + r * Math.sin(a);
    d += (i===0?'M':'L') + x.toFixed(2) + ',' + y.toFixed(2);
  });
  return `<path d="${d+'Z'}" fill="${color}" opacity="${alpha}"/>
          <circle cx="${cx}" cy="${cy}" r="${hubR}" fill="${color}" opacity="${alpha*.85}"/>
          <circle cx="${cx}" cy="${cy}" r="${hubR*.45}" fill="#000" opacity="0.7"/>`;
}
// Weight: 14 teeth | Reps: 9 teeth | Sets: 6 smooth lobes (use bezier variant)
```

Three gears: Weight (red, 14 teeth sharp), Reps (purple, 9 teeth medium), Sets (blue, 6 smooth lobes).
Use `<defs>` + `<use>` to define each gear once and reuse across screens — avoids duplication.

## Video Placeholder (Portrait)

Video is portrait, NOT landscape. Use `height: ~150–200px` in a card, NOT `aspect-ratio: 16/9`.

```html
<div class="vid" style="height:152px; border-radius:16px; position:relative; overflow:hidden">
  <!-- content -->
  <div class="vid-fade"></div>  <!-- radial-gradient mask -->
  <div class="vid-badge">▶ Demo</div>
  <div class="vid-dur">10s · Loop</div>
</div>
```

```css
.vid-fade {
  position: absolute; inset: 0;
  background: radial-gradient(ellipse at 50% 55%, transparent 35%, var(--bg) 85%);
}
```

## Screenshot + Send to WhatsApp

```bash
# Serve the file
python3 -m http.server 8765 &

# Render with headless Chromium
chromium-browser --headless --disable-gpu \
  --screenshot=/home/hermes/mockup.png \
  --window-size=1820,1200 --no-sandbox \
  "http://localhost:8765/mockup.html"

# Crop into rows with PIL if >150KB
from PIL import Image
img = Image.open("/home/hermes/mockup.png")
w, h = img.size
img.crop((0, 0, w, h//2+60)).save("/home/hermes/row1.png")
img.crop((0, h//2-60, w, h)).save("/home/hermes/row2.png")
```

Then send each row via `/send-media` bridge with `filePath`. See `whatsapp-send-document` skill.

## Pitfalls

- **Video was landscape in v1** — always portrait for mobile logging UI
- **Gear SVGs as asterisks** — must use proper tooth path geometry via JS, not `<line>` spokes
- **Rail nodes collapsing** — use `flex:1` on rail nodes, no `max-height` cap
- **DONE card opacity** — dim video and name only; gears must stay full opacity (still editable)
- **Dev annotations in mockup** — never leave "Path A — All Complete" type labels in production screens
- **Only 4 nav items** — Timbr spec requires 5; always include Progress tab
- **Opus subagent for HTML** — times out on large single-file builds (>500 lines). Build directly instead.

## Upload to Google Drive

```python
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import json

with open("/home/hermes/.hermes/google_token.json") as f:
    d = json.load(f)
creds = Credentials(token=d["token"], refresh_token=d["refresh_token"],
    token_uri=d["token_uri"], client_id=d["client_id"], client_secret=d["client_secret"],
    scopes=d["scopes"])
service = build("drive", "v3", credentials=creds)
file = service.files().create(
    body={"name": "Mockup.html", "mimeType": "text/html"},
    media_body=MediaFileUpload("/home/hermes/mockup.html", mimetype="text/html"),
    fields="id").execute()
service.permissions().create(fileId=file["id"],
    body={"type":"anyone","role":"reader"}).execute()
print(f"https://drive.google.com/file/d/{file['id']}/view?usp=sharing")
```

## References
- `references/timbr-feature1-spec.md` — Timbr Feature 1 screen-by-screen spec summary
