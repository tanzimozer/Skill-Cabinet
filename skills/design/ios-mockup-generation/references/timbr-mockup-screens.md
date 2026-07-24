# Timbr Feature 1 — Mockup Screen Inventory
*Generated: May–June 2026 · v0.4.1 spec · File: /home/hermes/timbr-mockup.html*

## Screens Built (8 total, 2 rows of 4)

### Row 1 — Entry & Active Logging
| # | Screen | Key elements |
|---|---|---|
| 01 | Today's Workout | Pre-workout summary card, program tag (Block 2 · Hypertrophy), exercise list preview, Start Workout CTA button |
| 02 | Active Card | Left rail (9 nodes, 2 done), exercise card (Leg Press), 3 gear sliders (Weight/Reps/Sets), video placeholder with edge-fade, note line, refresh icon |
| 03 | Undo Popup | Next card rendered (Leg Extension), transient toast at bottom: "Leg Press marked done · Undo" with 4s progress bar |
| 04 | DONE Card State | Green "Done" banner, desaturated card, disabled refresh icon (greyed), green rail node, "Logged · Values still editable" note |

### Row 2 — Navigation & End Flow
| # | Screen | Key elements |
|---|---|---|
| 05 | Overview Drawer | 2/3-width drawer from left, all 9 exercises with done/active/pending chips, progress bar "3/9" |
| 06 | End Workout Journal | Path B bottom sheet, per-exercise toggle rows (Completed/Skipped chips), Cancel + End Workout buttons |
| 07 | RPE Rating | Behind: wearable summary (42 min, 387 cal, avg HR 138). RPE sheet: 1–10 pip grid, selected=8, "Confirm RPE 8" CTA |
| 08 | Session Complete | Path A — progress ring (9/9), stats row (min/cal/HR/RPE), 12-day streak card, Done CTA |

## Colour Assignments
- Weight gear: `#E84545` (accent red)
- Reps gear: `#A78BFA` (purple)
- Sets gear: `#60A5FA` (blue)
- DONE state: `#22C55E` (green)
- Streak: `#F59E0B` (amber)

## Gear SVG Tooth Counts
- Weight: 16 teeth (sharp lines, stroke-width 1.8)
- Reps: 10 teeth (medium lines, stroke-width 2)
- Sets: 6 rounded lobes (Q bezier paths)

## Key Resolved Decisions Reflected
- Q14: Refresh wraps to alt1 after exhaustion
- Q15: Swipe-right on DONE → advance to next NOT_DONE
- Q16: Refresh icon disabled (opacity 0.2, cursor not-allowed) on DONE cards
- Q17: CSS radial-gradient mask-image for video edge-fade
- Q18: Video autoplay always (shown as ▶ LOOP badge)
- Q19: Zero-DONE → "Save streak only / Discard" (Path C — not built as separate screen but documented)
- Q21: Manual End Workout button (not auto-complete)

## File Delivery Note
Served via `python3 -m http.server 8765` on VM (session proc_407200d7ed50).
Google Drive upload not possible without OAuth credentials — alternatives: GitHub Gist, tiiny.host, direct file transfer.
