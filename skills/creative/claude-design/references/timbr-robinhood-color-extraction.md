# TIMBR / Robinhood Colour Extraction — Session Reference

Extracted via deep pixel analysis from 6 Robinhood reference screenshots (June 2026).
Total gold-range pixels analysed: ~629,460.

## Key Finding: Hue is H=43°, NOT H=33°

Previous sessions used H=33° (bronze). Wrong. The correct gold is H=43° (yellow-gold).
That 10° difference is the visual gap between "right" and "close but off."

## Verified Palette

### Backgrounds
| Name | Hex | HSL | Source |
|------|-----|-----|--------|
| Pure Black | `#000000` | H=0 S=0 L=0 | 23-27% of all screens |
| Warm Black | `#0C0C08` | H=60° S=20% L=4% | Secondary bg |
| Card Surface | `#181814` | H=60° S=9% L=9% | Card backgrounds |
| Elevated | `#1C1814` | H=30° S=17% L=9% | Modals |

### Gold (per screen average, weighted by pixel count)
| Screen | Hex | HSL | Px Count |
|--------|-----|-----|----------|
| Gold Card (TOP source) | `#B39F6C` | H=43.6° S=32% L=56% | 350,804 |
| Primary Gold (use this) | `#A89462` | H=42.9° S=28.7% L=52% | 2,036 |
| Dark Gold | `#887447` | H=41.9° S=31% L=41% | Move Money avg |
| Light Gold (highlights) | `#BFAA73` | H=43.4° S=37.3% L=60% | 2,353 |
| Pure Glow | `#FFD600` | H=50.4° S=100% L=50% | 246 px — charts only |
| Dark Bronze | `#5C513B` | H=40° S=21.9% L=30% | 1,950 — subtle accents |

### Text
| Name | Hex | Usage |
|------|-----|-------|
| Primary | `#E0DCD8` | Large numbers, body |
| Secondary | `#D8D8D4` | Secondary info |
| Muted | `#A09C98` | Labels, timestamps |
| Disabled | `#686460` | Disabled states |

### Status
| `#22C55E` | Green — gains, positive indicators |

## What Is NOT In The Reference

**No red. No purple. No blue.**

Robinhood uses green for positive, gold for brand. That's it.
If you find `--red`, `--pur`, `--blu` in a TIMBR mockup, remove them.

## User Feedback Loop (this session)

1. "color theme did not match" → extracted from 5 screenshots → populated Google Sheet
2. "gold is not the same exact" → deeper analysis, found H=43° not H=33°
3. "slightly darker" → shifted L from 60% → 52% (primary), kept H=43°
4. All three corrections validated the extraction workflow: sheet-first, then rebuild

## Google Sheet
https://docs.google.com/spreadsheets/d/1qy5VKdbi7Antrj-7yNk65ERdB4G4p1o672jZLH-_eLw
Sheet: "Color Specs" tab — full breakdown with pixel counts per screen
