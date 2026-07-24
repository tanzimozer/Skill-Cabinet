# Timbr Design References — Confirmed by Sagar (2026-05-31)

## Reference 1: Robinhood Net Worth Screen
- **Background:** Pure black `#000000`
- **Accent:** Gold/yellow `#C9A84C` (line, numbers, underlines)
- **Layout:** Hamburger menu | "Net worth" title | refresh icon
- **Hero pattern:** "TOTAL" label (small caps, gold) → large value `$67,707.24` (gold/cream) → delta `▲ $9,540.48 (16.4%)` (gold)
- **Chart:** Gold line on black, glowing endpoint dot, flat→spike→flat shape
- **Time selectors:** 1W / 1M / 3M / YTD / 1Y / ALL (pill style, gold selected bg)
- **Bottom card:** Light beige/cream, Assets + Liabilities with gold underlines
- **Bottom nav:** 5 icons, minimal, semi-transparent

## Reference 2: Robinhood Accounts Screen
- **Background:** Solid black
- **Header:** White serif font ("Accounts for the family"), gray subtitle
- **Cards:** Dark gray background, rounded corners
  - Gold label (small caps: "Gold card", "Banking")
  - Bold white heading with `>` arrow
  - Gray description text
  - Hero image: physical object (gold card, rings, figurine) — premium tactile feel
- **Color:** Black + white + gold only. No other accent colors.

## Reference 3: Timbr v0.1 Mockup Reference (Sagar's own prior version)
- Dark background (not pure black — `#0A0A0A` range)
- Red human silhouette illustrations for exercises
- Red `Start Workout` button
- Exercise cards showing weight/reps as large values
- Gear metaphor referenced but NOT shown as asterisks — clean slider instead

## Design Token Extraction
| Token | Value | Source |
|---|---|---|
| Background | `#000000` | Robinhood Net Worth |
| Primary accent | `#C9A84C` | Robinhood gold |
| Secondary | `#E84545` | Timbr brand red |
| Card bg | `#0A0A0A–#111` | Robinhood card |
| Card border | `#222` | Robinhood card |
| Hero value size | 22–52px, weight 900 | Robinhood TOTAL display |
| CTA button | Gold bg, black text | Robinhood primary action |
| Nav opacity inactive | ~0.28 | Robinhood bottom nav |

## What Sagar Rejected
- v1: Gear SVGs (looked like asterisks), landscape video, `#080808` grey (not true black)
- v2: Still not matching — gear SVGs still wrong, video still landscape, dev labels in copy
- v3: Accepted direction — pure black, gold accent, silhouette illustrations, Robinhood chart on complete screen
