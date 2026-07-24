# Timbr Feature 1 — Screen Spec Reference

## 8 Screens (v0.4.1)

| # | Screen | Key Elements |
|---|--------|-------------|
| 01 | Pre-workout Summary | Workout card with hero gradient, exercise list with muscle tags, Start CTA button |
| 02 | Active Exercise Card | Left progress rail, portrait video, 3 gear sliders, exercise badge, swipe hint |
| 03 | Undo Toast | Same card layout + floating pill toast (✓ marked done · Undo · depleting progress bar) |
| 04 | DONE Card State | Green done banner, rail node green, video dimmed, gears full opacity + editable, refresh icon disabled |
| 05 | Overview Drawer | 73% width slide-in, all 9 exercises with done/active/pending chips, progress bar |
| 06 | End Workout Journal | Bottom sheet 85% height, all exercises with toggle chips, sticky Cancel/End Workout actions |
| 07 | RPE Rating | Bottom sheet, 1–10 pip grid (green→amber→red), selected pip scaled 1.12x, wearable stats blurred behind |
| 08 | Session Complete | 9/9 ring with glow, stats row (min/cal/HR/RPE), streak card, Done CTA |

## Design Decisions Encoded

- **Swipe-right = DONE + advance** to next NOT_DONE (skips DONE in Reels-style)
- **Undo popup** = 4s transient toast only; no persistent header Undo button
- **DONE card** = gears editable, refresh locked, video dimmed, green accent
- **Drawer** = swipe-left OR tap "All" in header; shows ALL exercises incl DONE
- **End flow paths**: Path A (all done) = good job popup → RPE; Path B (some skipped) = journal → RPE; Path C (zero done) = streak-only popup, no RPE
- **Video** = portrait half-screen, autoplay/loop/muted, CSS radial-gradient edge fade
- **Gear visual language**: Weight (red, 14 sharp teeth) / Reps (purple, 9 medium) / Sets (blue, 6 smooth lobes)
- **5 nav items**: Home / Workout / Chat / Progress / Profile

## Colour Assignments

| Colour | Hex | Used For |
|--------|-----|---------|
| Coral red | #E84545 | Primary CTA, weight gear, DONE pill, ring |
| Purple | #A78BFA | Reps gear |
| Blue | #60A5FA | Sets gear |
| Green | #22C55E | Completed state, DONE card accent |
| Amber | #F59E0B | Streak card |
| Deep black | #080808 | App background |
| Dark card | #101010 | Card surfaces |

## V1 Bugs Fixed in V2

1. Video was landscape 16/9 → fixed to portrait ~152px height
2. Gear SVGs were asterisk spokes → fixed to proper trapezoidal tooth paths via JS
3. `svg { fill: var(--text) }` global → broke stroke-only icons → removed
4. Only 4 nav items → added Progress as 5th
5. Rail nodes had `max-height:68px` cap → removed, flex distributes naturally
6. DONE card had `opacity:0.75` on whole card → only video/name dimmed now
7. Screen 5 background was empty behind drawer → added real card content
8. "Path A — All Complete" dev annotation → removed
9. Journal only showed 7/9 exercises → fixed to show all 9
10. RPE pips were flat grey → colour-coded green→amber→red
