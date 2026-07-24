# TIMBR APP UI — Mockup Reference

iOS workout logger built for Tanzim, using Robinhood Banking as the visual reference. Stored at `github.com/tanzimozer/timbr-ui`.

## Files in Repo

| File | Description |
|------|-------------|
| `index.html` | Styled mockup — Robinhood gold palette |
| `wireframe.html` | Grayscale wireframe — structure only |
| `preview.png` | Screenshot of styled mockup |
| `wireframe-preview.png` | Screenshot of wireframes |
| `index-pre-airbnb.html` | Backup before Airbnb experiment |

## Color Specs Sheet

https://docs.google.com/spreadsheets/d/1qy5VKdbi7Antrj-7yNk65ERdB4G4p1o672jZLH-_eLw

## Screens (8 total)

1. **Home** — User greeting, workout card, CTA, tip
2. **Active Exercise** — Progress rail, video demo, WT/REPS/SETS sliders
3. **Undo Toast** — Exercise completion with undo pill
4. **Completed State** — Revisiting done exercise (dimmed + done banner)
5. **All Exercises Drawer** — Side overlay with exercise list + progress bar
6. **End Workout Journal** — Bottom sheet, toggle completed/skipped
7. **RPE Rating** — Bottom sheet, 1–10 grid, selected state
8. **Session Complete** — Stats grid, progress chart, streak card, CTA

## Design Decisions

### Colors (pixel-verified)
- Primary gold: `#A89462` (H=43°, L=52%)
- Dark gold: `#887447`
- Light gold: `#BFAA73` (highlights only)
- Background: `#000000` (pure black)
- Text: `#E0DCD8` (warm cream)
- See `references/robinhood-gold-design-system.md` for full palette

### Typography
- Font: `'Open Sans', -apple-system, 'SF Pro Display', sans-serif`
- Open Sans chosen over Nunito (Nunito was reverted by Tanzim)
- Labels (WT/REPS/SETS): uppercase, `letter-spacing: 0.08em`, `font-weight: 700`

### Applied Design Principles
- **Robinhood Banking** color palette (exact pixel extraction)
- **Airbnb** spatial principles (shadows over borders, pill CTAs) — WITHOUT font changes
- **Robinhood Banking** nav bar: SVG line icons, gold dot indicator, pure black bg

### Key Corrections Made During Session
1. No red/purple/blue — only black + gold + green + cream
2. Primary gold hue is H=43° NOT H=33° — warmer, less bronze
3. Sets slider color: `--gold-bright` (#FFD600) was wrong → changed to `--gold-light` (#BFAA73) to match Reps
4. Emojis in nav removed → clean SVG line icons
5. WT/REPS/SETS labels should be ALL CAPS
6. COMPLETE text should be gold, not white

## Versioning History

| Version | Key Change |
|---------|-----------|
| v5 | Original gold `#C8A84C` |
| v6 | Coral `#E84040` as primary (wrong) |
| v7 | Robinhood amber palette first attempt |
| v8 | Corrected hue to H=43° |
| v9 | Darker gold (L=52%), Open Sans, nav redesign, Airbnb spacing |

## Wireframe Approach

When user asks for "wireframe separately":
- Create `wireframe.html` alongside `index.html` in same repo
- Pure white/gray palette: `background: #F5F5F5`, cards `#F8F8F8`
- All colors replaced with grayscale (`#333`, `#666`, `#999`, `#CCC`)
- Borders: `1px dashed #CCC`
- No box-shadows, no color accents
- Placeholders: `repeating-linear-gradient(45deg, ...)` hatching pattern
- Same screen count as the styled version
- Push both files to the same repo

## Notes for Future Sessions

- Tanzim iterates fast — always use version suffixes (v9, v10...) and save backups before experiments
- "Revert" = `cp index-pre-<experiment>.html index.html` — fast, no git history needed
- After EVERY change: screenshot → commit → push → drop to TIMBR APP - PRD group
- Drop pattern: HTML file first, then preview image with caption
- Group ID: `120363427118724513@g.us` (TIMBR APP - PRD)
