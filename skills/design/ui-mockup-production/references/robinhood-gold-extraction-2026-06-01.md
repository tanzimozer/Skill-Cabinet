# Robinhood Gold — Deep Pixel Extraction (2026-06-01)

5 Robinhood reference screenshots analysed. Total gold-range pixels: ~629,460.

## Per-Screen Results

| Screen | Avg Hex | HSL | Gold Pixels |
|--------|---------|-----|-------------|
| Gold Card | `#B39F6C` | H=43.6° S=32.0% L=56.3% | 350,804 ← most reliable |
| Virtual Cards | `#665841` | H=37.8° S=21.9% L=32.8% | 102,870 |
| Move Money | `#887447` | H=41.9° S=31.0% L=40.7% | 94,553 |
| Family Spending | `#9F8860` | H=38.8° S=24.7% L=50.0% | 39,466 |
| Banking APY | `#9A865F` | H=39.9° S=23.6% L=49.1% | 37,013 |
| Net Worth | `#86775C` | H=38.7° S=18.6% L=44.5% | 4,754 ← least reliable |

## Top Individual Pixels (Gold Card screen — most reliable)

| Hex | HSL | Pixel Count | Usage |
|-----|-----|-------------|-------|
| `#BFAA73` | H=43.4° S=37.3% L=60.0% | 2,353 | Light gold / highlights |
| `#A89462` | H=42.9° S=28.7% L=52.2% | 2,036 | **Primary gold (chosen)** |
| `#CAB272` | H=43.6° S=45.4% L=62.0% | 1,069 | Bright/active states |
| `#5C513B` | H=40.0° S=21.9% L=29.6% | 1,950 | Dark bronze accents |
| `#FFD600` | H=50.4° S=100% L=50.0% | 246 | Chart lines, glows |

## Key Finding

**Dominant hue: 43°** — This is yellow-gold, not bronze. Previous attempts used H=33° which
is a brownish bronze. The difference is subtle in isolation but obvious against a black background.

## Refinement History

| Version | Primary Gold | Issue |
|---------|-------------|-------|
| v6 | `#C9A84C` | Too bright, too yellow (H=45° but L=67% — too light) |
| v7 | `#D8B47C` | H=36° — wrong hue direction (too bronze-orange) |
| v8 | `#A88860` | H=33° — still wrong hue |
| v9 initial | `#BFAA73` | H=43° correct but L=60% too light |
| v9 corrected | `#A89462` | H=43° L=52% — user approved as "close" |
| Final | `#887447` | H=42° L=41% — user approved after "slightly darker" request |

## CSS Token Set (Final Approved)

```css
:root {
  --blk: #000000;
  --s1: #0C0C08;
  --s2: #181814;
  --s3: #1C1814;
  --bdr: #302C28;
  --bdr2: #3C3834;
  --txt: #E0DCD8;
  --txt2: #D8D8D4;
  --txt3: #A09C98;
  --txt4: #686460;
  --gold: #A89462;        /* PRIMARY */
  --gold-dark: #887447;   /* DARKER VARIANT — user's preferred final */
  --gold-light: #BFAA73;  /* HIGHLIGHTS ONLY */
  --gold-bright: #FFD600; /* CHART LINES / GLOW ONLY */
  --bronze: #5C513B;
  --bronze-muted: #5E533D;
  --gold2: rgba(168,148,98,0.12);
  --gold3: rgba(168,148,98,0.22);
  --grn: #22C55E;
}
```

## Colors NOT in Robinhood Refs (do not add)
- Red (#E84040 or similar) — NOT present
- Purple (#A78BFA or similar) — NOT present
- Blue (#60A5FA or similar) — NOT present

CTAs, buttons, and active states all use **gold** in Robinhood's design language.
