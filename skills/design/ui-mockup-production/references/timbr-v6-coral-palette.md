# Timbr v6 Colour Palette — Coral Primary

Extracted 2026-06-01 from reference screenshots. This corrects v5 which had gold as primary.

## Colour Variables

```css
:root {
  /* Coral-red as PRIMARY accent (from ref #E84040) */
  --coral: #E84040;
  --coral-hover: #D63838;
  --coral2: rgba(232,64,64,0.12);   /* backgrounds */
  --coral3: rgba(232,64,64,0.22);   /* borders */
  
  /* Gold as SECONDARY/premium highlight - multi-tone */
  --gold: #A98760;           /* base bronze */
  --gold-bright: #F4C878;    /* bright highlight */
  --gold-deep: #785828;      /* deep shadow */
  --gold-mid: #C09048;       /* mid tone */
  --gold2: rgba(169,135,96,0.10);
  --gold3: rgba(169,135,96,0.18);
  
  /* Warm blacks */
  --blk: #000000;
  --s1: #0C0B09;
  --s2: #141210;
  --s3: #1C1A17;
  --bdr: #252220;
  --bdr2: #2E2B26;
}
```

## Where each colour is used

### Coral (primary)
- All CTA buttons (`background: var(--coral); color: #fff`)
- Progress rail nodes (done + current)
- Progress rail line fill
- Progress bar fill
- Weight slider fill and label
- RPE selected pip
- "End Workout" / "Done" CTAs
- Toast progress bar

### Gold (secondary)
- "PREMIUM" / "BLOCK 2" pills (gold2 bg, gold3 border, gold text)
- Eyebrow labels ("TODAY'S WORKOUT")
- Streak card border
- "+3 more" text links
- Tip card labels

### Other accent colours (unchanged)
- Reps slider: `--pur: #A78BFA` (purple)
- Sets slider: `--blu: #60A5FA` (blue)
- Success states: `--grn: #22C55E` (green)

## Pixel analysis summary

| Reference Image | Coral Pixels | Gold Pixels | Ratio |
|-----------------|--------------|-------------|-------|
| timbr-screen.png (original ref) | 30,297 | 347 | 87:1 |
| v5-full.png (before fix) | 1,773 | 7,864 | 0.2:1 ❌ |
| v6-full.png (after fix) | 23,832 | 7,210 | 3.3:1 ✅ |

The original reference had coral dominating 87:1 over gold. v5 inverted this. v6 restores coral as primary (3.3:1 ratio is acceptable given the different screen layouts).
