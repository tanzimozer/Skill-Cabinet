---
name: ios-mockup-generation
description: Generate production-grade iOS app mockup screens as self-contained HTML/CSS from a feature spec or PRD. Covers phone frame, status bar, component patterns, dark design systems, and multi-screen layout.
tags: [ios, mockup, design, html, css, ux, product, timbr]
version: 1.0.0
---

# iOS Mockup Generation

Produce pixel-accurate, production-reference iOS mockup screens as a **single self-contained HTML file** from a feature spec or PRD. No Figma, no external dependencies, no images required. Output is shareable, browser-viewable, and developer-handoff ready.

## When to Use

- Boss has a feature spec / PRD and wants visual mockups before handing to a design/dev vendor
- Quick visual reference for a product discussion or investor conversation
- Screen-by-screen walkthrough of a UX flow that needs to be concrete

## Design System — Timbr (established)

Timbr uses a **Robinhood-dark** aesthetic. Known values:

```css
--bg:      #080808;   /* App background */
--card:    #111111;   /* Card surface */
--card2:   #161616;   /* Secondary card / row backgrounds */
--border:  #1F1F1F;   /* Primary border */
--border2: #2A2A2A;   /* Secondary border */
--text:    #FFFFFF;
--text2:   #AAAAAA;
--text3:   #666666;
--text4:   #3A3A3A;
--accent:  #E84545;   /* Primary / CTA / Weight gear */
--green:   #22C55E;   /* DONE / Completed */
--purple:  #A78BFA;   /* Reps gear */
--blue:    #60A5FA;   /* Sets gear */
--amber:   #F59E0B;   /* Streak / Amber */
```

Font: `-apple-system, 'SF Pro Display', 'SF Pro Text', 'Helvetica Neue', sans-serif`

## Phone Frame Spec (iPhone 15 Pro proportions)

```css
.phone {
  width: 393px; height: 852px;
  background: #000;
  border-radius: 55px;
  border: 1.5px solid #252525;
  overflow: hidden;
  box-shadow:
    0 0 0 1px #111,
    0 40px 100px rgba(0,0,0,0.85),
    inset 0 0 0 1px #2a2a2a;
}
```

**Internal layout (fixed heights):**
- Status bar: 56px
- App area: `852px - 56px - 90px = 706px`
- Bottom nav: 90px

**Status bar anatomy:**
- Dynamic Island pill: `width: 126px; height: 37px; background: #000; border-radius: 20px; position: absolute; top: 0; left: 50%; transform: translateX(-50%);`
- Time left, icons right (signal, wifi, battery SVGs)

**Bottom nav:**
- 4–5 icon items, `height: 90px`, `align-items: flex-start; padding-top: 12px`
- Active item: full opacity + accent dot below label
- Inactive: `opacity: 0.35`
- `border-top: 1px solid var(--border); backdrop-filter: blur(20px)`

## Page Layout (multi-screen gallery)

```css
.screens-grid {
  display: grid;
  grid-template-columns: repeat(4, 393px);
  gap: 40px 32px;
  justify-content: center;
}
```

Add `row-label` divs (`grid-column: 1 / -1`) to group screens by flow stage.

Each screen column:
```html
<div class="screen-col">
  <div class="screen-label">01 — Screen Name</div>
  <div class="phone">...</div>
  <div class="screen-desc">Brief description</div>
</div>
```

## Component Patterns

### Header Bar (logger/detail screens)
```html
<div class="logger-header"> <!-- height: 52px, flex, padding: 0 20px -->
  <div class="lh-back">← Back</div>
  <div class="lh-center">Title / CTA</div>
  <div class="lh-right">Icon</div>
</div>
```

### Cards / Surfaces
```css
.card {
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 24px; /* or 16px for compact */
  overflow: hidden;
}
```

### Bottom Sheet / Modal
```css
.sheet {
  position: absolute; bottom: 0; left: 0; right: 0;
  background: #0C0C0C;
  border-radius: 24px 24px 0 0;
  border-top: 1px solid var(--border);
  z-index: 61;
}
/* Handle */
.js-handle { width: 36px; height: 4px; background: #2A2A2A; border-radius: 2px; margin: 12px auto 0; }
```

**Dim overlay behind sheet:**
```css
.overlay { position: absolute; inset: 0; background: rgba(0,0,0,0.7); z-index: 60; }
```

### Drawer (side panel)
```css
.drawer {
  position: absolute; top: 0; left: 0;
  width: 72%; height: 100%;
  background: #0C0C0C;
  border-right: 1px solid var(--border);
  z-index: 51;
}
```

### Toast / Transient Popup
Dating-app undo toast pattern:
```css
.toast {
  position: absolute; bottom: 16px; left: 50%; transform: translateX(-50%);
  background: rgba(22,22,22,0.97); backdrop-filter: blur(12px);
  border: 1px solid #2E2E2E; border-radius: 100px;
  padding: 10px 8px 10px 16px;
  white-space: nowrap; overflow: hidden;
  box-shadow: 0 4px 32px rgba(0,0,0,0.7), 0 0 0 1px rgba(255,255,255,0.04);
}
/* Progress bar bleeds to zero over 4s */
.toast-bar {
  position: absolute; bottom: 0; left: 0; height: 2px;
  background: var(--accent); opacity: 0.5;
  border-radius: 0 0 100px 100px;
}
```

### Primary CTA Button
```css
.cta-btn {
  width: 100%; height: 56px;
  background: var(--accent); border-radius: 16px; border: none;
  color: #fff; font-size: 16px; font-weight: 800; letter-spacing: -0.3px;
  box-shadow: 0 8px 24px rgba(232,69,69,0.35);
}
```

### Toggle Chip (completed/skipped)
```css
.toggle-done { background: rgba(34,197,94,0.12); color: #22C55E; border: 1px solid rgba(34,197,94,0.25); border-radius: 20px; padding: 6px 12px; font-size: 11px; font-weight: 800; }
.toggle-skip { background: #161616; color: #666; border: 1px solid #2A2A2A; border-radius: 20px; padding: 6px 12px; font-size: 11px; font-weight: 800; }
```

### Status Chip (done/active/pending)
```css
.chip-done    { background: rgba(232,69,69,0.12); color: #E84545; }
.chip-active  { background: rgba(232,69,69,0.2);  color: #E84545; }
.chip-pending { background: #161616; color: #666; }
/* All: border-radius: 6px; padding: 3px 8px; font-size: 10px; font-weight: 800; */
```

### Progress Ring (SVG)
```html
<svg width="140" height="140" viewBox="0 0 140 140">
  <circle cx="70" cy="70" r="60" fill="none" stroke="#1A1A1A" stroke-width="8"/>
  <circle cx="70" cy="70" r="60" fill="none" stroke="#E84545" stroke-width="8"
    stroke-dasharray="377" stroke-dashoffset="0"  <!-- 0 = full, 377 = empty -->
    stroke-linecap="round" transform="rotate(-90 70 70)"
    style="filter:drop-shadow(0 0 8px rgba(232,69,69,0.5))"/>
  <text x="70" y="65" text-anchor="middle" font-size="24" font-weight="800" fill="#fff">9/9</text>
  <text x="70" y="84" text-anchor="middle" font-size="12" fill="#666">EXERCISES</text>
</svg>
```
`stroke-dashoffset = 377 * (1 - completion_fraction)` → partial ring fill.

### SVG Gear Controls (Timbr-specific)
Three distinct visual styles per gear type — drawn inline SVG, no images:
- **Weight** (spiky): 16 sharp teeth radiating from center circle — `stroke-width: 1.8`, accent red
- **Reps** (medium): 10 medium teeth — `stroke-width: 2`, purple
- **Sets** (smooth): 6 rounded lobe paths (Q bezier curves), blue

Each gear paired with a range slider built from div track + fill div + thumb div.

### Vertical Progress Rail (Timbr logger)
```html
<div class="p-rail"> <!-- width: 38px, flex column, align center -->
  <!-- One .rail-node per exercise -->
  <div class="rail-node"> <!-- flex column, max-height: 68px -->
    <div class="rail-c rc-done rc-check"></div> <!-- 14px circle -->
    <div class="rail-line rl-done"></div>        <!-- 1.5px line between nodes -->
  </div>
</div>
```
States: `rc-done` (accent fill + checkmark pseudo), `rc-current` (larger, pulsing), default (desaturated).

## Technique: Dim / Blur Background Behind Modal

When showing a sheet or drawer, dim the background layer in place:
```html
<div class="logger-wrap" style="filter:brightness(0.3)">
  <!-- existing screen content -->
</div>
<div class="overlay-bg"></div>
<div class="modal-sheet">...</div>
```
This avoids needing a separate blurred copy of the screen.

## Video Placeholder (no actual video)

```html
<div class="ec-video"> <!-- border-radius: 18px, aspect-ratio: 16/9 -->
  <div class="ecv-inner"> <!-- centered content -->
    <!-- Optional: SVG body silhouette at low opacity -->
  </div>
  <div class="ecv-fade"></div> <!-- radial-gradient fade to card bg -->
  <div class="ecv-badge">▶ LOOP</div>
</div>
```
Edge-fade CSS:
```css
.ec-video::after { /* or a child overlay div */
  background: radial-gradient(ellipse at 50% 60%, transparent 40%, var(--bg) 88%);
}
```

## Section Glow / Radial Accents

Subtle red radial glow behind cards for depth:
```css
.card-hero::before {
  content: '';
  position: absolute; top: -40px; right: -40px;
  width: 180px; height: 180px;
  background: radial-gradient(circle, rgba(232,69,69,0.15) 0%, transparent 70%);
  pointer-events: none;
}
```

## Design Notes Footer

Always add a colour system reference, gear visual language explanation, and key-decisions-reflected checklist at the bottom of the mockup page. This serves as handoff documentation for designers and devs.

## File Delivery

- Output: single `.html` file, no external dependencies
- Self-hosted via `python3 -m http.server` on the VM if a live URL is needed
- Google Drive upload via `google_token.json` at `/home/hermes/.hermes/google_token.json` — confirmed working (May 31 2026 session, uploaded Timbr mockup successfully)
- GitHub Gist: token "Friday-Hermes" for tanzimozer is NOT stored on VM disk — always ask Tanzim to paste it before attempting a Gist upload; do not claim it's available
- Offer tiiny.host or 0x0.st as zero-login alternatives if neither credential is available

## Pitfalls

- **browser_navigate to file:// URLs times out** — always serve via HTTP (python3 -m http.server), not file:// protocol
- **4-column grid at 393px each** = ~1700px minimum width — works fine for desktop viewing, note this in delivery
- **Status bar pill must be `position: absolute`** inside the status bar div or it fights the flex layout
- **Bottom sheet z-index stack:** overlay at 60, sheet at 61, any sub-modals at 70+
- **`filter: brightness()` on background** is cleaner than a separate blurred copy for modal backgrounds — no duplication of DOM

## Support Files

- **references/timbr-mockup-screens.md** — Screen inventory and design decisions from the Timbr Feature 1 v0.4.1 mockup session
