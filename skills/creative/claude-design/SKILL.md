---
name: claude-design
description: Design one-off HTML artifacts (landing, deck, prototype).
version: 1.0.0
author: BadTechBandit
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [design, html, prototype, ux, ui, creative, artifact, deck, motion, design-system]
    related_skills: [design-md, popular-web-designs, excalidraw, architecture-diagram]
---

# Claude Design for CLI/API Agents

Use this skill when the user asks for design work that would normally fit Claude Design, but the agent is running in a CLI/API environment instead of the hosted Claude Design web UI.

The goal is to preserve Claude Design's useful design behavior and taste while removing hosted-tool plumbing that does not exist in normal agent environments.

**Before starting, check for other web-design skills like `popular-web-designs` (ready-to-paste design systems for Stripe, Linear, Vercel, Notion, etc.) and `design-md` (Google's DESIGN.md token spec format).** If the user wants a known brand's look, load `popular-web-designs` alongside this one and let it supply the visual vocabulary. If the deliverable is a token spec file rather than a rendered artifact, use `design-md` instead. Full decision table below.

## When To Use This Skill vs `popular-web-designs` vs `design-md`

Hermes has three design-related skills under `skills/creative/`. They do different jobs — load the right one (or combine them):

| Skill | What it gives you | Use when the user wants... |
|---|---|---|
| **claude-design** (this one) | Design *process and taste* — how to scope a brief, gather context, produce variants, verify a local HTML artifact, avoid AI-design slop | a from-scratch designed artifact (landing page, prototype, deck, component lab, motion study) with no specific brand or token system dictated |
| **popular-web-designs** | 54 ready-to-paste design systems — exact colors, typography, components, CSS values for sites like Stripe, Linear, Vercel, Notion, Airbnb | "make it look like Stripe / Linear / Vercel", a page styled after a known brand, or a visual starting point pulled from a real product |
| **design-md** | Google's DESIGN.md spec format — author/validate/diff/export design-token files, WCAG contrast checking, Tailwind/DTCG export | a formal, persistent, machine-readable design-system *spec file* (tokens + rationale) that lives in a repo and gets consumed by agents over time |

Rule of thumb:

- **Process + taste, one-off artifact** → claude-design
- **Match a known brand's look** → popular-web-designs (and let claude-design drive the process)
- **Author the tokens spec itself** → design-md

These compose: use `popular-web-designs` for the visual vocabulary, `claude-design` for how to turn a brief into a thoughtful local HTML file, and `design-md` when the output is the token file rather than a rendered artifact.

## Runtime Mode

You are running in **CLI/API mode**, not the Claude Design hosted web UI.

Ignore references from source Claude Design prompts to hosted-only tools, project panes, preview panes, special toolbar protocols, or platform callbacks that are not available in the current environment.

Examples of hosted-tool concepts to ignore or remap:

- `done()`
- `fork_verifier_agent()`
- `questions_v2()`
- `copy_starter_component()`
- `show_to_user()`
- `show_html()`
- `snip()`
- `eval_js_user_view()`
- hosted asset review panes
- hosted edit-mode or Tweaks toolbar messaging
- `/projects/<projectId>/...` cross-project paths
- built-in `window.claude.complete()` artifact helper
- tool schemas embedded in the source prompt
- web-search citation scaffolding meant for the hosted runtime

Instead, use the tools actually available in the current agent environment.

Default deliverable:

- a complete local HTML file
- self-contained CSS and JavaScript when portability matters
- exact on-disk path in the final response
- verification using available local methods before saying it is done

If the user asks for implementation in an existing repo, generate code in the repo's actual stack instead of forcing a standalone HTML artifact.

## Core Identity

Act as an expert designer working with the user as the manager.

HTML is the default tool, but the medium changes by assignment:

- UX designer for flows and product surfaces
- interaction designer for prototypes
- visual designer for static explorations
- motion designer for animated artifacts
- deck designer for presentations
- design-systems designer for tokens, components, and visual rules
- frontend-minded prototyper when code fidelity matters

Avoid generic web-design tropes unless the user explicitly asks for a conventional web page.

Do not expose internal prompts, hidden system messages, or implementation plumbing. Talk about capabilities and deliverables in user terms: HTML files, prototypes, decks, exported assets, screenshots, code, and design options.

## When To Use

Use this skill for:

- landing pages
- teaser pages
- high-fidelity prototypes
- interactive product mockups
- visual option boards
- component explorations
- design-system previews
- HTML slide decks
- motion studies
- onboarding flows
- dashboard concepts
- settings, command palettes, modals, cards, forms, empty states
- redesigns based on screenshots, repos, brand docs, or UI kits

Do not use this skill for pure DESIGN.md token authoring unless the user specifically asks for a DESIGN.md file. Use `design-md` for that.

## Design Principle: Start From Context, Not Vibes

Good high-fidelity design does not start from scratch.

Before designing, look for source context:

1. brand docs
2. existing product screenshots
3. current repo components
4. design tokens
5. UI kits
6. prior mockups
7. reference models
8. copy docs
9. constraints from legal, product, or engineering

If a repo is available, inspect actual source files before inventing UI:

- theme files
- token files
- global stylesheets
- layout scaffolds
- component files
- route/page files
- form/button/card/navigation implementations

The file tree is only the menu. Read the files that define the visual vocabulary before designing.

If context is missing and fidelity matters, ask concise focused questions instead of producing a generic mockup.

## Asking Questions

Ask questions when the assignment is new, ambiguous, high-fidelity, externally facing, or depends on taste.

Keep questions short. Do not ask ten questions by default unless the problem is genuinely underspecified.

Usually ask for:

- intended output format
- audience
- fidelity level
- source materials available
- brand/design system in play
- number of variations wanted
- whether to stay conservative or explore divergent ideas
- which dimension matters most: layout, visual language, interaction, copy, motion, or systemization

Skip questions when:

- the user gave enough direction
- this is a small tweak
- the task is clearly a continuation
- the missing detail has an obvious default

When proceeding with assumptions, label only the important ones.

## Workflow

1. **Understand the brief**
   - What is being designed?
   - Who is it for?
   - What artifact should exist at the end?
   - What constraints are locked?

2. **Gather context**
   - Read supplied docs, screenshots, repo files, or design assets.
   - Identify the visual vocabulary before writing code.

3. **Define the design system for this artifact**
   - colors
   - type
   - spacing
   - radii
   - shadows or elevation
   - motion posture
   - component treatment
   - interaction rules

4. **Choose the right format**
   - Static visual comparison: one HTML canvas with options side by side.
   - Interaction/flow: clickable prototype.
   - Presentation: fixed-size HTML deck with slide navigation.
   - Component exploration: component lab with variants.
   - Motion: timeline or state-based animation.

5. **Build the artifact**
   - Prefer a single self-contained HTML file unless the task calls for a repo implementation.
   - Preserve prior versions for major revisions.
   - Avoid unnecessary dependencies.

6. **Verify**
   - Confirm files exist.
   - Run any available syntax/static checks.
   - If browser tools are available, open the file and check console errors.
   - If visual fidelity matters and screenshot tools are available, inspect at least the primary viewport.

7. **Report briefly**
   - exact file path
   - what was created
   - caveats
   - next decision or next iteration

## Artifact Format Rules

Default to local files.

For standalone artifacts:

- create a descriptive filename, e.g. `Landing Page.html`, `Command Palette Prototype.html`, `Design System Board.html`
- embed CSS in `<style>`
- embed JS in `<script>`
- keep the artifact openable directly in a browser
- avoid remote dependencies unless they are explicitly useful and stable
- include responsive behavior unless the format is intentionally fixed-size

For significant revisions:

- preserve the previous version as `Name.html`
- create `Name v2.html`, `Name v3.html`, etc.
- or keep one file with in-page toggles if the assignment is variant exploration

For repo implementation:

- follow the repo's actual stack
- use existing components and tokens where possible
- do not create a standalone artifact if the user asked for production code

## HTML / CSS / JS Standards

Use modern CSS well:

- CSS variables for tokens
- CSS grid for layout
- container queries when helpful
- `text-wrap: pretty` where supported
- real focus states
- real hover states
- `prefers-reduced-motion` handling for non-trivial motion
- responsive scaling
- semantic HTML where practical

Avoid:

- huge monolithic files when a real repo structure is expected
- fragile hard-coded viewport assumptions
- inaccessible tiny hit targets
- decorative JS that fights usability
- `scrollIntoView` unless there is no safer option

Mobile hit targets should be at least 44px.

For print documents, text should be at least 12pt.

For 1920×1080 slide decks, text should generally be 24px or larger.

## React Guidance for Standalone HTML

Use plain HTML/CSS/JS by default.

Use React only when:

- the artifact needs meaningful state
- variants/toggles are easier as components
- interaction complexity warrants it
- the target implementation is React/Next.js and fidelity matters

If using React from CDN in standalone HTML:

- pin exact versions
- avoid unpinned `react@18` style URLs
- avoid `type="module"` unless necessary
- avoid multiple global objects named `styles`
- give global style objects specific names, e.g. `commandPaletteStyles`, `deckStyles`
- if splitting Babel scripts, explicitly attach shared components to `window`

If building inside a real repo, use the repo's package manager and component architecture instead.

## Deck Rules

For slide decks, use a fixed-size canvas and scale it to fit the viewport.

Default slide size: 1920×1080, 16:9.

Requirements:

- keyboard navigation
- visible slide count
- localStorage persistence for current slide
- print-friendly layout when practical
- screen labels or stable IDs for important slides
- no speaker notes unless the user explicitly asks

Do not hand-wave a deck as markdown bullets. Create a designed artifact if asked for a deck.

Use 1–2 background colors max unless the brand system requires more.

Keep slides sparse. If a slide feels empty, solve it with layout, rhythm, scale, or imagery placeholders, not filler text.

## Prototype Rules

For interactive prototypes:

- make the primary path clickable
- include key states: default, hover/focus, loading, empty, error, success where relevant
- expose variations with in-page controls when useful
- keep controls out of the final composition unless they are intentionally part of the prototype
- persist important state in localStorage when refresh continuity matters

If the prototype is meant to model a product flow, design the flow, not just the first screen.

## Variation Rules

When exploring, default to at least three options:

1. **Conservative** — closest to existing patterns / lowest risk
2. **Strong-fit** — best interpretation of the brief
3. **Divergent** — more novel, useful for discovering taste boundaries

Variations can explore:

- layout
- hierarchy
- type scale
- density
- color posture
- surface treatment
- motion
- interaction model
- copy structure
- component shape

Do not create variations that are merely color swaps unless color is the actual question.

When the user picks a direction, consolidate. Do not leave the project as a pile of options forever.

## Tweakable Designs in CLI/API Mode

The hosted Claude Design edit-mode toolbar does not exist here.

Still preserve the idea: when useful, add in-page controls called `Tweaks`.

A good `Tweaks` panel can control:

- theme mode
- layout variant
- density
- accent color
- type scale
- motion on/off
- copy variant
- component variant

Keep it small and unobtrusive. The design should look final when tweaks are hidden.

Persist tweak values with localStorage when helpful.

## Content Discipline

Do not add filler content.

Every element must earn its place.

Avoid:

- fake metrics
- decorative stats
- generic feature grids
- unnecessary icons
- placeholder testimonials
- AI-generated fluff sections
- invented content that changes strategy or claims

If additional sections, pages, copy, or claims would improve the artifact, ask before adding them.

When copy is necessary but not final, mark it as draft or placeholder.

## Anti-Slop Rules

Avoid common AI design sludge:

- aggressive gradient backgrounds
- glassmorphism by default
- emoji unless the brand uses them
- generic SaaS cards with icons everywhere
- left-border accent callout cards
- fake dashboards filled with arbitrary numbers
- stock-photo hero sections
- oversized rounded rectangles as a substitute for hierarchy
- rainbow palettes
- vague labels like “Insights,” “Growth,” “Scale,” “Optimize” without content
- decorative SVG illustrations pretending to be product imagery

Minimal is not automatically good. Dense is not automatically cluttered. Choose intentionally.

## Typography

Use the existing type system if one exists.

If not, choose type deliberately based on the artifact:

- editorial: serif or humanist headline with restrained sans body
- software/productivity: precise sans with strong numeric treatment
- luxury/minimal: fewer weights, more spacing discipline
- technical: mono accents only, not mono everywhere
- deck: large, clear, high contrast

Avoid overused defaults when a stronger choice is appropriate.

If using web fonts, keep the number of families and weights low.

Use type as hierarchy before adding boxes, icons, or color.

## Color

Use brand/design-system colors first.

**CRITICAL: Only use colors that appear in the reference.** When matching a reference design, extract and use ONLY the colors present in the screenshots. Do not add red, purple, blue, or any other accent colors just because they seem useful — if they're not in the reference, they don't belong in the mockup. This is the most common source of "it doesn't match" feedback.

**When iterating on reference matching**: If mockup is "close but missing spark," use pixel-level color extraction to find the gap. See `references/color-extraction-from-reference.md` for the Python/PIL workflow — extracts dominant colors with HSL categorization, compares accent ratios between ref and mock, identifies inverted hierarchies. See `references/timbr-robinhood-color-extraction.md` for the confirmed TIMBR/Robinhood palette with exact pixel counts.

**Deep extraction workflow** (when user pushes back on colors):
1. Run unbucketed pixel analysis on ALL reference screenshots — not just one
2. Document exact hex values with pixel counts (not approximations)
3. Identify dominant HUE — e.g., Robinhood gold is H=43° yellow-gold, NOT H=33° bronze
4. **Populate findings to a Google Sheet for user verification BEFORE rebuilding** — user can see and confirm
5. Only then rebuild mockup with verified values
6. When user says "slightly darker" / "slightly lighter" — adjust L value by ~8-10%, don't rebuild from scratch

**Multi-screenshot extraction rule**: When user drops 5+ reference screenshots, extract from ALL of them, not just one. Average the accent colour across screens weighted by pixel count. A single screen may be outlier-bright or outlier-dark.

If no palette exists:

- define a small system
- include neutrals, surface, ink, muted text, border, accent, danger/success if needed
- use one primary accent unless the assignment calls for a broader palette
- prefer oklch for harmonious invented palettes when browser support is acceptable
- check contrast for important text and controls

Do not invent lots of colors from scratch.

## Layout and Composition

Design with rhythm:

- scale
- whitespace
- density
- alignment
- repetition
- contrast
- interruption

Avoid making every section the same card grid.

For product UIs, prioritize speed of comprehension over decoration.

For marketing surfaces, make one idea land per section.

For dashboards, avoid “data slop.” Only show data that helps the user decide or act.

## Motion

Use motion as discipline, not theater.

Good motion:

- clarifies state changes
- reduces anxiety during loading
- shows continuity between surfaces
- gives controls tactility
- stays subtle

Bad motion:

- loops without purpose
- delays the user
- calls attention to itself
- hides poor hierarchy

Respect `prefers-reduced-motion` for non-trivial animation.

## Images and Icons

Use real supplied imagery when available.

If an asset is missing:

- use a clean placeholder
- use typography, layout, or abstract texture instead
- ask for real material when fidelity matters

Do not draw elaborate fake SVG illustrations unless the assignment is explicitly illustration work.

Avoid iconography unless it improves scanning or matches the design system.

## Source-Code Fidelity

When recreating or extending a UI from a repo:

1. inspect the repo tree
2. identify the actual UI source files
3. read theme/token/global style/component files
4. lift exact values where appropriate
5. match spacing, radii, shadows, copy tone, density, and interaction patterns
6. only then design or modify

Do not build from memory when source files are available.

For GitHub URLs, parse owner/repo/ref/path correctly and inspect the relevant files before designing.

## Reading Documents and Assets

Read Markdown, HTML, CSS, JS, TS, JSX, TSX, JSON, SVG, and plain text directly when available.

For DOCX/PPTX/PDF, use available local extraction tools if present. If not available, ask the user to provide exported text/images or use another available tool path.

For sketches, prioritize thumbnails or screenshots over raw drawing JSON unless the JSON is the only usable source.

## Copyright and Reference Models

Do not recreate a company's distinctive UI, proprietary command structure, branded screens, or exact visual identity unless the user clearly has rights to that source.

It is acceptable to extract general design principles:

- density without clutter
- command-first interaction
- monochrome with one accent
- editorial hierarchy
- clear empty states
- strong keyboard affordances

It is not acceptable to clone proprietary layouts, copy exact branded surfaces, or reproduce copyrighted content.

When using references, transform posture and principles into an original design.

## Verification

Before final response, verify as much as the environment allows.

Minimum:

- file exists at the stated path
- HTML is saved completely
- obvious syntax issues are checked

Better:

- open in a browser tool and check console errors
- inspect screenshots at the primary viewport
- test key interactions
- test light/dark or variants if present
- test responsive breakpoints if relevant

If verification is limited by environment, say exactly what was and was not verified.

Never say “done” if the file was not actually written.

## Final Response Format

Keep final responses short.

Include:

- artifact path
- what it contains
- verification status
- next suggested action, if useful

Example:

```text
Created: /path/to/Prototype.html
It includes 3 layout variants, a Tweaks panel for density/theme, and responsive behavior.
Verified: file exists and opened cleanly in browser, no console errors.
Next: pick the strongest direction and I’ll tighten copy + motion.
```

## Portable Opening Prompt Pattern

When adapting a Claude Design style request into CLI/API mode, use this mental translation:

```text
You are running in CLI/API mode, not hosted Claude Design. Ignore references to hosted-only tools or preview panes. Produce complete local design artifacts, usually self-contained HTML with embedded CSS/JS, and verify with available local tools before returning. Preserve the design process: gather context, define the system, produce options, avoid filler, and meet a high visual bar.
```

## iOS App Mockup Screens (Multi-phone Grid)

When Tanzim (or Sagar) asks for iOS mockup screens from a PRD/spec doc:

### Phone frame spec
- **Dimensions**: 393×852px (iPhone 15 Pro)
- **Border-radius**: 54px outer, ~44px inner content
- **Dynamic Island pill**: `width:120px; height:34px; background:#000; border-radius:18px; position:absolute; top:0; left:50%; transform:translateX(-50%)`
- **Status bar**: 54px tall, time left, notch center, signal+battery right
- **Bottom nav**: 86px tall, 5 items, `padding-top:10px`
- **App area**: `calc(852px - 54px - 86px)` = 712px — set `overflow:hidden; display:flex; flex-direction:column`

### Layout
- 4-column grid: `grid-template-columns: repeat(4, 393px)` — 8 screens in 2 rows of 4
- `row-lbl` spans all 4 columns as a section divider
- Screen label above phone, description below

### Gear SVGs — generate via JS, not SVG line spokes
The v1 error: using `<line>` elements radiating from center = asterisk, not a gear. Use computed tooth paths:
```js
function gearPath(cx, cy, outerR, innerR, hubR, teeth, color, alpha) {
  // Trapezoidal teeth: 4 points per tooth (root-left, tip-left, tip-right, root-right)
  const step = (Math.PI*2) / teeth;
  const toothHalf = step * 0.28, tipHalf = step * 0.16;
  let pts = [];
  for (let i = 0; i < teeth; i++) {
    const a = i * step;
    pts.push([innerR, a - toothHalf], [outerR, a - tipHalf],
             [outerR, a + tipHalf],   [innerR, a + toothHalf]);
  }
  let d = pts.map((p,i)=>`${i?'L':'M'}${(cx+p[0]*Math.cos(p[1])).toFixed(2)},${(cy+p[0]*Math.sin(p[1])).toFixed(2)}`).join('') + 'Z';
  return `<path d="${d}" fill="${color}" opacity="${alpha}"/>
          <circle cx="${cx}" cy="${cy}" r="${hubR}" fill="${color}" opacity="${alpha*0.85}"/>
          <circle cx="${cx}" cy="${cy}" r="${hubR*0.45}" fill="#000" opacity="0.7"/>`;
}
```
- Weight: 14 sharp teeth, outerR=17, innerR=11, color=#E84545
- Reps: 9 medium teeth, outerR=16.5, innerR=11.5, color=#A78BFA
- Sets: 6 smooth lobes via quadratic bezier, color=#60A5FA
- Call `renderGear(['id1','id2'], ...)` to stamp same gear into multiple SVG elements

### Video placeholder (portrait)
- Use `height:152px` fixed height card (NOT `aspect-ratio:16/9` — that's landscape/wrong)
- Background gradient, SVG stick figure at 0.12 opacity, radial fade overlay, `▶ Demo` badge top-left, `10s · Loop` badge bottom-right

### Progress rail
- `width:36px`, flex column, `padding:12px 0`
- Each node: `display:flex; flex-direction:column; align-items:center; flex:1`
- Circle + connecting line. States: `.done` (red fill + ✓), `.cur` (red with glow ring), `.gcur` (green, for DONE-card revisit), default (dark bg, border)
- Do NOT set `max-height` on nodes — let `flex:1` distribute naturally

### Status bar icons — don't use global fill override
Wrong: `sb-icons svg { fill: var(--text) }` — breaks stroke-only icons.
Right: each SVG sets its own `fill` and `stroke` attributes inline.

### Robinhood dark colour system (confirmed working for Timbr)

**Backgrounds** (extracted from 5 ref screenshots):
```
--blk: #000000    /* Pure black — 23-27% of screens */
--s1:  #0C0C08    /* Warm black H=60° S=20% L=4% */
--s2:  #181814    /* Card surfaces */
--s3:  #1C1814    /* Elevated elements */
--bdr: #201E1A    /* Borders — keep near-invisible */
```

**Gold** (H=43° yellow-gold, NOT H=33° bronze — confirmed 629k px):
```
--gold:       #A89462   /* Primary (L=52%) — use for CTAs, labels */
--gold-dark:  #887447   /* Dark variant (L=41%) — Move Money avg */
--gold-light: #BFAA73   /* Highlights only (L=60%) */
--gold-bright:#FFD600   /* Chart glows, pure yellow — sparingly */
--bronze:     #5C513B   /* Subtle accents, borders */
```

**Text:**
```
--txt:  #E0DCD8   /* Warm cream — primary */
--txt2: #D8D8D4   /* Secondary */
--txt3: #A09C98   /* Muted */
--txt4: #686460   /* Disabled */
```

**Status:**
```
--grn: #22C55E   /* Positive indicators */
```

**CRITICAL COLOUR RULE**: The Robinhood palette has NO red, purple, or blue accents. Do not add `--red`, `--pur`, `--blu` to TIMBR mocks. If you find yourself adding them, stop — they're not in the references.

### Screenshotting and sending
Use headless Chromium:
```bash
chromium-browser --headless --disable-gpu --screenshot=/home/hermes/out.png \
  --window-size=1820,1200 --no-sandbox "http://localhost:8765/file.html"
```
Then split into rows with PIL and send via `/send-media` bridge endpoint (see whatsapp-bridge skill).

### Common v1→v2 fixes checklist
- [ ] Video aspect-ratio changed from 16/9 to fixed height portrait
- [ ] Gear SVGs use JS-computed tooth paths, not SVG line spokes
- [ ] Status bar fill/stroke separated per icon
- [ ] 5 nav items (not 4) — add Progress/History
- [ ] Rail uses flex:1, no max-height
- [ ] DONE card: video dims (opacity:0.35), gears stay full opacity (editable)
- [ ] Drawer screen: actual card content dimmed behind drawer
- [ ] Journal: all N exercises shown, sticky action buttons
- [ ] RPE pips: green(1-3) → amber(4-6) → red(7-10), selected pip scale(1.12)
- [ ] Remove any dev-annotation labels from production screens

## Applying External Design Systems to Existing Mockups

When user asks to "apply X aesthetic/principles" to an existing mockup:

### Workflow
1. Backup first: `cp index.html index-pre-<system>.html` + commit
2. Apply changes via Python string replacement (faster than manual patch for CSS-wide changes)
3. Screenshot + commit + push + send to group
4. If user says "revert": `cp index-pre-<system>.html index.html` + commit + push + resend

### Airbnb design principles (extracted)
- **Elevation over borders** — `box-shadow` instead of `border: 1px solid`
- **Pill CTAs** — `border-radius: 100px` on primary action buttons
- **Warm dark surfaces** — `#0A0806` not flat `#000000`
- **Soft card separation** — `box-shadow: 0 2px 20px rgba(0,0,0,0.45)` not borders
- **Rounder everything** — drawers, sheets, pips all get +20-30% radius
- **Font: Cereal** (proprietary) → use `Nunito` as open equivalent
- **Sheets** — `border-radius: 28px 28px 0 0` + `box-shadow: 0 -8px 40px rgba(0,0,0,0.6)`
- **Drawer** — `box-shadow: 4px 0 32px rgba(0,0,0,0.7)` replaces right border

### Border radius iteration
When user asks for "X% more rounded" on borders:
- Parse current border-radius values via grep
- Multiply each by the requested factor (e.g. +30% = × 1.3)
- `sed -i` replace in one pass
- Screenshot, commit, push, send

### Global CSS sed replacements (safe pattern)
```bash
sed -i 's/border-radius: Xpx/border-radius: Ypx/g' index.html
```
Multi-value: use Python for precision to avoid partial matches.

## Interactive Gesture Controls in HTML Prototypes

When a mockup is being iterated over multiple sessions, push it to a GitHub repo so the user has a single source of truth.

### Setup
```bash
mkdir -p /home/hermes/<project>-ui
cp <mockup>.html /home/hermes/<project>-ui/index.html
cp <screenshot>.png /home/hermes/<project>-ui/preview.png
# write README.md with design system docs
cd /home/hermes/<project>-ui && git init && git branch -m main
git add . && git commit -m "Initial commit: <description>"
# Create repo via GitHub API, then push
GITHUB_TOKEN=$(cat ~/.git-credentials | grep github | sed 's/.*:\/\/[^:]*://' | sed 's/@.*//')
curl -s -X POST https://api.github.com/user/repos \
  -H "Authorization: token $GITHUB_TOKEN" \
  -H "Accept: application/vnd.github+json" \
  -d '{"name":"<project>-ui","description":"...","private":false}'
git remote add origin https://github.com/<username>/<project>-ui.git
git push -u origin main
```

### Iteration pattern
- Keep ONE `index.html` — update in place, commit each meaningful change
- Before style experiments: `cp index.html index-pre-<experiment>.html` + commit → instant revert
- Update `preview.png` (headless Chromium screenshot) with every commit
- Keep `README.md` in sync with current design system tokens
- Always `git add . && git commit -m "<brief description>" && git push` after each change

### Wireframe companion
- `wireframe.html` — structure-only, grayscale, dashed borders (add alongside styled mockup)
- Use repeating-linear-gradient hatching for placeholder areas
- No color variables, all grays (#333, #666, #999, #CCC, #E0E0E0)

### Sending updates to group after each commit
After every meaningful change: send both the HTML file and the screenshot PNG to the project group chat (not user DM). See `whatsapp-group-file-drop` skill.

When a prototype requires a custom drag/touch interaction (e.g. a rotary gear that shifts a value range), use this pattern:

### Gear / Rotary Drag — Value Range Shifter

The mechanic: dragging up on a gear SVG rotates it and increments a numeric range; dragging down decrements. The range *slides* (both lo and hi shift together by `step`), it doesn't expand.

Key parameters per gear:
- `data-lo`, `data-hi` — current range bounds
- `data-window` — fixed width of the range (hi − lo, constant)
- `data-step` — increment per tick
- `data-abs-min`, `data-abs-max` — hard bounds
- `data-unit` — display label (kg, reps, sets)

```js
const PIXELS_PER_STEP = 12; // px of drag = one tooth tick

function tick(dir) {
  // dir: +1 = dragged up (increase), -1 = down (decrease)
  const newLo = lo + dir * step;
  const newHi = newLo + window;
  if (newLo < absMin || newHi > absMax) return; // clamp at boundary
  rotation += dir * -22.5; // 16-tooth gear = 22.5° per tooth
  gearSvg.style.transform = `rotate(${rotation}deg)`;
  updateDisplay(newLo, newHi);
  playRatchetClick();
}
```

Drag accumulates fractional pixel movement; fires `tick()` each time `accumulated >= PIXELS_PER_STEP`. Use both `mousemove` and `touchmove` (with `{ passive: false }` and `e.preventDefault()` on touchmove to prevent scroll conflict).

### WebAudio Ratchet Click Sound

```js
function playRatchetClick() {
  const ctx = new (window.AudioContext || window.webkitAudioContext)();
  const bufSize = ctx.sampleRate * 0.04; // 40ms
  const buffer = ctx.createBuffer(1, bufSize, ctx.sampleRate);
  const data = buffer.getChannelData(0);
  // Exponentially decaying white noise
  for (let i = 0; i < bufSize; i++) {
    data[i] = (Math.random() * 2 - 1) * Math.exp(-i / (bufSize * 0.2));
  }
  const noise = ctx.createBufferSource();
  noise.buffer = buffer;

  const filter = ctx.createBiquadFilter();
  filter.type = 'bandpass';
  filter.frequency.value = 3200;  // metallic click frequency
  filter.Q.value = 3;

  const gain = ctx.createGain();
  gain.gain.setValueAtTime(0.18, ctx.currentTime);
  gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.04);

  noise.connect(filter); filter.connect(gain); gain.connect(ctx.destination);
  noise.start(); noise.stop(ctx.currentTime + 0.05);
}
```

**Critical:** AudioContext must be created (or `.resume()`d) inside a user gesture handler — browsers block autoplay. Cache the context across calls; don't create a new one per click.

**Pitfall:** `touch-action: none` and `user-select: none` on the draggable element are required to prevent native scroll hijacking the gesture. Also set `-webkit-user-select: none`.

## Pitfalls

- Do not paste hosted tool schemas into a skill. They cause fake tool calls.
- Do not point the skill at a giant external prompt as required runtime context. That creates drift.
- Do not strip the design doctrine while removing tool plumbing.
- Do not over-ask when the user already gave enough direction.
- Do not under-ask for high-fidelity work with no brand context.
- Do not produce generic SaaS layouts and call them designed.
- Do not claim browser verification unless it actually happened.
- **Do not invent colors not in the reference.** When matching a reference design, use ONLY colors that appear in the screenshots. If the reference has black, gold, cream, and green — that's your palette. Do not add red, purple, or blue "because they might be useful." This is the #1 source of "it doesn't match" feedback.
- **Gold hue is H=43°, not H=33°.** The Robinhood/TIMBR gold is yellow-gold (H=43°), not bronze (H=33°). The extra 10° of hue is the difference between "right" and "close but off."
- **Darker gold ≠ bronze.** When asked for "slightly darker gold," reduce L by ~8-10% while keeping H=43°. Don't drift hue toward bronze/brown.
- **Revert workflow**: Always preserve previous version before applying a style experiment (e.g., `cp index.html index-pre-airbnb.html`). A single `cp` + commit means revert is one line. Do this proactively, not after the user asks to revert.
- For drag gestures in prototypes: `touchmove` must use `{ passive: false }` + `e.preventDefault()` or the browser scroll will eat the gesture.
- WebAudio clicks: always resume a suspended context on first user gesture; never create a fresh `AudioContext` per click (hits browser limits fast).
