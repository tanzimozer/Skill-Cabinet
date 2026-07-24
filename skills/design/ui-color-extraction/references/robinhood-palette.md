# Robinhood UI Palette (2026-06)

Extracted from 5 reference screenshots: Move Money, Net Worth, Family Spending, Gold Card, Virtual Cards, Banking APY.

## Backgrounds
| Name | Hex | HSL | Usage |
|------|-----|-----|-------|
| Pure Black | #000000 | H=0° S=0% L=0% | Primary bg (23-27%) |
| Warm Black | #0C0C08 | H=60° S=20% L=4% | Secondary bg |
| Card Surface | #181814 | H=60° S=9% L=9% | Card backgrounds |
| Elevated | #1C1814 | H=30° S=17% L=9% | Modals, elevated |

## Gold (Primary) — USE DARKER RANGE BY DEFAULT
| Name | Hex | HSL | Usage |
|------|-----|-----|-------|
| **Primary Gold** | **#A89462** | H=42.9° S=28.7% L=52.2% | **DEFAULT — CTAs, accents** |
| Dark Gold | #887447 | H=41.9° S=31.0% L=40.7% | Darker variant, Move Money avg |
| Light Gold | #BFAA73 | H=43.4° S=37.3% L=60.0% | **Highlights ONLY** |

⚠️ **Key learning:** User explicitly prefers the darker gold range (L=40-52%) over bright gold (L=60%+). Don't default to the brightest variant.

## Gold (Glow/Highlights ONLY)
| Name | Hex | HSL | Usage |
|------|-----|-----|-------|
| Bright Gold | #C8B070 | H=44° S=44% L=61% | Active states |
| Pure Yellow-Gold | #FFD600 | H=50° S=100% L=50% | Chart lines, glows |

## Bronze (Subtle Accents)
| Name | Hex | HSL | Usage |
|------|-----|-----|-------|
| Dark Bronze | #5C513B | H=40° S=21.9% L=29.6% | Subtle accents (1,950px Virtual Cards) |
| Muted Bronze | #5E533D | H=40° S=21.3% L=30.4% | Borders, muted elements |

## Text
| Name | Hex | HSL | Usage |
|------|-----|-----|-------|
| Primary | #E0DCD8 | H=30° S=11% L=86% | Body text, numbers |
| Secondary | #D8D8D4 | H=60° S=5% L=84% | Secondary info |
| Muted | #A09C98 | H=30° S=4% L=61% | Timestamps |
| Disabled | #686460 | H=30° S=4% L=39% | Disabled states |

## Status
| Name | Hex | Usage |
|------|-----|-------|
| Success Green | #22C55E | Positive indicators |

⚠️ **NO other status colors** — the references only show green for positive. No red, purple, blue. Don't add colors that aren't in the source.

## Per-Screen Averages (deep analysis)
| Screen | Gold Average | Lightness |
|--------|--------------|-----------|
| Gold Card | #B39F6C | L=56% |
| Family | #9F8860 | L=50% |
| Banking APY | #9A865F | L=49% |
| Move Money | #887447 | L=41% |

The spread shows L=41% to L=56%. Default to the middle-dark range (#A89462 at L=52%), not the bright end.

## Source
- Google Sheet: TIMBR APP UI
- GitHub: github.com/tanzimozer/timbr-ui
- Session: 2026-06-01
