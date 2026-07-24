---
name: matplotlib-data-viz
category: operations
description: Building publication-quality charts and A4 infographics with matplotlib — radar charts, heatmaps, card layouts, dark themes. Covers the iterative vision-QA loop for fixing layout errors.
---

# Matplotlib Data Visualisation

Class-level skill for generating charts, radar plots, A4 infographic layouts, and dark-theme data cards using matplotlib in `execute_code`. Covers Tanzim's preferred aesthetic and the QA loop for catching layout errors before sending.

## Environment
- Use `execute_code` — matplotlib is available in the hermes python env
- Save to `/home/hermes/filename.png`
- Send via `/send-media` (see `whatsapp-bridge-ops` skill)
- DO NOT use `plt.show()` — headless environment, always `plt.savefig()` then `plt.close()`

## Tanzim's aesthetic standard
- **Dark background:** `#080c12` or similar near-black
- **Gold accent:** `#c9a84c` for headers, dividers, section labels
- **White text:** body copy
- **Light grey:** `#aaaaaa` / `#bbbbbb` for secondary text
- **No emojis, no borders heavier than needed**
- Per-person colours: Tanzim=`#38d4ff` (blue), Sagar=`#00e87a` (green), Waseem=`#ff7a45` (orange)
- TIMBR Confidential watermark in footer

## A4 layout (standard)
```python
fig = plt.figure(figsize=(8.27, 11.69), dpi=150)  # A4 portrait at 150dpi
fig.patch.set_facecolor("#080c12")
# Use fig.add_axes([left, bottom, width, height]) for precise placement
# Coordinates are 0–1 fractions of the figure
```

**Layout zones (portrait A4, top to bottom):**
- `[0, 0.963, 1, 0.037]` — gold top bar (title strip)
- `[0.05, 0.930, 0.9, 0.030]` — main title
- `[0.10, 0.880, 0.80, 0.048]` — legend (3 rows stacked)
- `[0.12, 0.455, 0.76, 0.430]` — radar/chart (polar)
- `[0.04, 0.446, 0.92, 0.003]` — gold divider line
- `[0.042, 0.042, 0.283, 0.395]` — card 1 (3 cards side by side)
- `[0, 0, 1, 0.038]` — footer

## Radar chart (polar)
```python
ra = fig.add_axes([0.12, 0.455, 0.76, 0.430], polar=True)
ra.set_facecolor("#0c1520")
N = len(skills)
angles = np.linspace(0, 2*np.pi, N, endpoint=False).tolist() + [0]
ra.set_ylim(0, 10)
ra.set_yticks([2, 4, 6, 8, 10])
ra.set_yticklabels(["2","4","6","8","10"], color="#666666", fontsize=7.5)
ra.grid(color="#1e2d3e", linewidth=0.9)
ra.spines['polar'].set_color("#2a3f55")
ra.set_xticks(angles[:-1])
ra.set_xticklabels(skills, color="#e0e0e0", fontsize=9.5, fontweight="bold")
ra.tick_params(axis='x', pad=14)  # keep labels from colliding with plot edge
for vals, color in [(data1, BLUE), (data2, GREEN)]:
    v = vals + vals[:1]
    ra.plot(angles, v, color=color, linewidth=2.6)
    ra.fill(angles, v, color=color, alpha=0.13)
```

## Legend (stacked rows — avoids crowding)
Never put 3 legend items on one horizontal line — they collide. Stack them:
```python
# 3 separate axes, one per legend row
leg_tops = [0.910, 0.896, 0.882]
for (c, name, detail), lt in zip(leg_data, leg_tops):
    la = fig.add_axes([0.10, lt, 0.80, 0.013])
    la.set_facecolor(BG); la.axis("off")
    la.add_patch(Rectangle((0, 0.15), 0.018, 0.70, color=c, transform=la.transAxes))
    la.text(0.026, 0.55, f"{name}  —  {detail}", va="center", fontsize=8,
            color=WHITE, transform=la.transAxes)
```

## Card layout (3 columns)
```python
cw, gap, ch, cbot = 0.283, 0.024, 0.395, 0.042
for i, card in enumerate(cards):
    cx = 0.042 + i * (cw + gap)
    ca = fig.add_axes([cx, cbot, cw, ch])
    ca.set_xlim(0, 1); ca.set_ylim(0, 1)
    ca.set_facecolor("#0d1822"); ca.axis("off")
    # Add coloured top strip
    ca.add_patch(Rectangle((0, 0.930), 1, 0.070, color=card_color, zorder=2))
    # Coloured card border
    for sp in ca.spines.values():
        sp.set_edgecolor(card_color); sp.set_linewidth(1.3); sp.set_visible(True)
    # Section headers in monospace gold
    ca.text(0.06, 0.793, "SECTION LABEL", fontsize=6, color=GOLD,
            fontweight="bold", va="center", fontfamily="monospace")
```

## Score distribution mini-bars (inside cards)
```python
bw = 0.87 / len(scores)
for j, (sc, label) in enumerate(zip(scores, abbrevs)):
    bx = 0.06 + j * bw
    # Background bar
    ca.add_patch(Rectangle((bx, bt - bh), bw - 0.006, bh, color="#1a2535"))
    # Filled portion
    ca.add_patch(Rectangle((bx, bt - bh), (bw - 0.006) * (sc / 10), bh,
                            color=card_color, alpha=0.9))
    # Score above bar
    ca.text(bx + (bw - 0.006) / 2, bt + 0.007, str(sc),
            ha="center", va="bottom", fontsize=7, color=WHITE, fontweight="bold")
    # Abbreviation below bar
    ca.text(bx + (bw - 0.006) / 2, bt - bh - 0.018, label,
            ha="center", va="top", fontsize=6.5, color="#888888")
```

## PIL hybrid rendering for tall cards (preferred over pure matplotlib for card sections)
When the card section is tall (>500px) and has multiple fixed sections, matplotlib's `fig.add_axes()` approach loses precision — relative y-stepping drifts, leaving massive empty gaps or overflowing text that the vision model reads as broken. The fix is a **PIL hybrid**: render the radar via matplotlib → PIL image, then draw cards entirely in PIL with pixel-exact coordinates.

```python
# Pattern: matplotlib radar → buf → PIL image; PIL cards drawn separately; composite
import io
buf = io.BytesIO()
plt.savefig(buf, format='png', dpi=150, facecolor='black', pad_inches=0.02)
buf.seek(0)
radar_img = Image.open(buf).convert("RGBA")
plt.close()
radar_resized = radar_img.resize((W, RADAR_H), Image.LANCZOS)

# Draw cards with PIL ImageDraw — absolute pixel positions, no drift
final = Image.new("RGB", (W, H), (0,0,0))
final.paste(radar_resized.convert("RGB"), (0, 0))
card_y = RADAR_H + SPACER + GAP
for i, card in enumerate(cards_data):
    card_img = draw_card_pil(card, CARD_W, CARD_H)
    card_x = GAP + i * (CARD_W + GAP)
    final.paste(card_img, (card_x, card_y))
final.save(out)
```

**Key PIL card tips:**
- `draw.textlength(text, font)` for centring — measure before placing
- Wrap narrative with `textwrap.wrap(text, width)` then loop lines — PIL doesn't auto-wrap
- Auto-shrink long text: measure with `draw.textlength`, if > card_w − 2*pad, switch to smaller font
- `draw.rounded_rectangle` for chip borders (Pillow ≥ 9.2)
- Font path: `/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf` (always available)

## Multi-line role titles in cards
When a card role spans two lines (e.g. "Co-Founder" / "Chief Engineer"), render each as a separate `ax.text()` call and step `y` down between them. Do NOT try to fit both on one line — long titles like "AI Systems & Agentic Workforce" will clip at the card edge.

```python
for line in data["role_lines"]:   # list of 1–2 strings
    ax.text(0.5, y, line, color=accent, fontsize=8.5, fontweight='bold',
            ha='center', va='center')
    y -= 0.063  # step down per line
```

Font size for role lines should be ≤ 9pt when either line is long (>20 chars). 8.5pt is safe for the card width in an A4 3-column layout.

## Tag-chip bottom-overflow pitfall
Tag chips (2×2 grid) are placed at absolute `y` positions calculated from the role/narrative block above. If the role block is taller than assumed (e.g. two role lines instead of one), the chips can fall below `y=0` and disappear entirely — the card looks empty.

**Fix:** calculate `tag_y1` dynamically from the current `y` cursor after drawing the narrative and divider, not as a fixed constant from the top:
```python
tag_y1 = y - 0.115   # relative to current y after DOMAINS label
tag_y2 = tag_y1 - row_gap
```
Always guard with `if ty < 0.04: break` to catch any remaining overflow silently.

## Vision QC artifact warning — viewport scaling vs real gaps
`browser_vision` scales tall images (1240×1700+px) to fit the viewport. This causes two false positives the vision model consistently reports:

1. **"Massive empty gap"** — reported even when the gap is 25–30% of card height (visually fine). The gap looks larger because the image is compressed vertically in the screenshot.
2. **"Text overflowing across cards"** — narrative text near y≈0.76 in a tall figure can appear to bleed into adjacent cards when the screenshot is scaled down.

**Workaround:** Crop individual cards before QC review. A single card at native resolution gives an accurate read:
```python
from PIL import Image
img = Image.open('/home/hermes/output.png')
w, h = img.size
img.crop((0, int(h*0.44), w//3 + 60, h)).save('/tmp/card1_check.png')
```
If the cropped card reads clean, trust it over the full-image vision report. Only re-render if the crop itself shows a real issue.

## QC for tall images — split-crop before vision review
`browser_vision` captures only what's in the viewport. For A4 portrait images (1240×1753px), the bottom half is cut off. Split before reviewing:
```python
from PIL import Image
img = Image.open('output.png')
w, h = img.size
img.crop((0, 0, w, h//2)).save('/tmp/top_half.png')
img.crop((0, h//2, w, h)).save('/tmp/bottom_half.png')
```
Then navigate to `/tmp/bottom_half.png` and run vision QC on the cards specifically. Avoids false "cards are empty" reports from the vision model seeing only the radar.

## Vision QA loop
Always run `browser_navigate` + `browser_vision` to check the output before sending:
```python
browser_navigate("file:///home/hermes/output.png")
browser_vision("List every visual error, overlap, clipping, or readability issue.")
```
Fix and re-run until vision confirms clean. Common issues caught this way:
- Legend items overlapping radar axis labels (fix: stack legend into separate row axes)
- Score bar abbreviations unreadable (fix: increase fontsize to 6.5+, use abbreviated labels)
- Card text overflow (fix: reduce fontsize or shorten strings)
- Subtitle colliding with legend (fix: add a dedicated subtitle axis ABOVE legend)

## Sending the final image
```bash
BRIDGE_TOKEN=$(grep WHATSAPP_BRIDGE_TOKEN ~/.hermes/.env | cut -d= -f2)
curl -s -X POST http://localhost:3000/send-media \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $BRIDGE_TOKEN" \
  -d '{"chatId": "160799431606497@lid", "filePath": "/home/hermes/output.png", "mediaType": "image", "caption": "caption here"}'
```

## Canvas height sizing for radar + cards
The total canvas height must account for three zones: `RADAR_H + SPACER + CARD_SECTION_H`. Typical working values for TIMBR layout:
```python
W, H    = 1240, 1720   # total canvas (adjust H until cards fill without gap)
RADAR_H = 1020         # LOCKED — do not change once radar is approved
SPACER  = 60           # breathing room between radar and card section
GAP     = 18           # margin around cards
CARD_W  = (W - GAP * 4) // 3
CARD_H  = H - RADAR_H - SPACER - GAP * 2
```
Content in a standard TIMBR card (banner + 2 role lines + narrative + 2 badges + domains + 4 chips) needs ~520–560px. Verify `CARD_H` is in that range. If cards are sparse, reduce H; if content clips at the bottom, increase H.

## TIMBR team visual
Full canonical spec (colours, scores, approved card copy, layout constants, rejected options) in `references/timbr-team-visual-spec.md`. Load before any iteration on the founding team radar/card asset.

## Reading PDFs from Google Drive
To read a PDF from Drive (e.g. a resume):
```python
# Download via Drive API
from googleapiclient.http import MediaIoBaseDownload
import io
request = drive.files().get_media(fileId=file_id)
buf = io.BytesIO()
downloader = MediaIoBaseDownload(buf, request)
done = False
while not done:
    _, done = downloader.next_chunk()
with open('/tmp/file.pdf', 'wb') as f:
    f.write(buf.getvalue())
```
Then extract text with pdfplumber (available in hermes venv):
```bash
/home/hermes/.hermes/hermes-agent/venv/bin/python3 -c "
import pdfplumber
with pdfplumber.open('/tmp/file.pdf') as pdf:
    for page in pdf.pages:
        print(page.extract_text())
"
```
Note: use the full venv path `/home/hermes/.hermes/hermes-agent/venv/bin/python3` — system python3 is externally managed. pdfplumber is already installed in the hermes venv.

## Google Drive credentials pattern
```python
import json
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

with open('/home/hermes/.hermes/vault.json') as f:
    vault = json.load(f)
token_file = vault['google']['token_file'].replace('~', '/home/hermes')
with open(token_file) as f:
    token_data = json.load(f)
creds = Credentials(
    token=token_data['token'],
    refresh_token=token_data.get('refresh_token'),
    token_uri=token_data.get('token_uri', 'https://oauth2.googleapis.com/token'),
    client_id=token_data.get('client_id'),
    client_secret=token_data.get('client_secret'),
)
drive = build('drive', 'v3', credentials=creds)
```

## Export vs download (Drive API)
- `export_media` — only works for Google Docs native files (Docs, Sheets, Slides). Returns 403 for .docx, .pdf uploads.
- `get_media` — works for ALL files including uploaded PDFs and .docx. Always use this for non-native files.
