# Robinhood Colour Analysis — Pixel Extraction 2026-06-01

Extracted from actual Robinhood screenshots shared by Sagar G. (TIMBR APP - PRD session).

## Source images (from ~/.hermes/image_cache)
- `img_08d431c0223b.jpg` — Robinhood Net Worth screen (472×1024)
- `img_7f02434592c0.jpg` — Robinhood Accounts screen (1290×2796)
- `img_c6cf453bb7c1.jpg` — Sagar's own Timbr mockup reference (1290×2796)

## Extraction results

### Net Worth screen (img_08d431c0223b.jpg)
- Background: `#0E0A07` (very dark warm near-black, slight brown tint)
- Gold pixels found: 304
- Gold average: `#BCAA4B`
- **Gold median: `#A49754`**
- Top gold shades:
  - `#908870` — 17px
  - `#988870` — 14px
  - `#888068` — 14px
  - `#908868` — 12px
  - `#908060` — 11px

### Accounts screen (img_7f02434592c0.jpg)
- Background: `#181713` (dark warm brown-black)
- Gold pixels found: 37,691
- Gold average: `#AA8962`
- **Gold median: `#A98765`**
- Top gold shades:
  - `#A88860` — 3093px
  - `#987858` — 2701px
  - `#B09068` — 2326px
  - `#907050` — 2276px
  - `#A08060` — 1870px

## Consolidated pick
**`#A98760`** — harmonises both screens, leans toward the Accounts screen (larger sample, richer gold).

## Common mistakes
| Colour | Issue |
|---|---|
| `#C9A84C` | Too bright, too saturated, too yellow. Used in v3/v4, rejected by Sagar. |
| `#FFD700` | Pure gold — not Robinhood at all |
| `#C9A84C` with high opacity glows | Looks like a generic fitness app, not Robinhood |

## What "Robinhood gold" actually looks like
Earthy, muted, warm amber-bronze. Think aged brass or dark honey — not bright jewellery gold. When in doubt: does it look like it belongs in a luxury dark-mode fintech app, or does it look like a trophy emoji? Adjust down.

## Background notes
Robinhood backgrounds are NOT pure #000000 — they carry a subtle warm brown undertone:
- Primary bg: `#0E0A07` to `#0C0B09`
- Card bg: `#141210`
- Borders: `#252220` (warm, not cold grey)

Cold dark greys (`#111111`, `#1A1A1A`) look visually different from the reference — too blue-grey.
