---
name: image-editing-bw
category: creative
description: |
  Black & white image editing for Tanzim using PIL/Pillow. Covers channel mixing, tone curves, contrast, grain, and Drive delivery. Includes hard-learned lessons about style-matching from reference samples.
triggers:
  - Tanzim asks for a B&W edit on a photo
  - Tanzim sends a reference sample and wants his photo matched to that style
  - Image editing, filter, or tone adjustment requested
---

# B&W Image Editing — Tanzim

## CRITICAL LESSON (learned 2026-07-20)
**Do NOT over-darken portrait photos.** The first two attempts used aggressive power curves (^2.2–^3.5) that crushed nearly all pixels to black, destroying the subject. Tanzim said: *"That ruined my image."*

The target aesthetic is **high-contrast editorial B&W with preserved subject detail** — NOT extreme shadow-crush street photography.

## Style Reference: What Tanzim Wants
From his sample (expert.bnw / @didisorgenfrey style):
- Deep, rich shadows — but subject (face, skin) stays in **clean midtones**, readable
- Background goes dark; subject pops by contrast
- No muddy grey wash — it's contrasty, not flat
- Subtle film grain — present but not gritty
- Sharp subject, not over-processed

**Sample stats (target range):**
- Mean brightness: ~50–70 (NOT sub-20)
- Dark pixels (<50): ~60–72%
- Mid pixels (50–200): ~20–35%
- Light pixels (>200): ~5–8%

## Working Recipe (PIL/Pillow)

```python
from PIL import Image, ImageEnhance, ImageFilter
import numpy as np

img = Image.open('input.jpg')

# Step 1: Channel mix — red-boosted for skin tones to render as mid-grey
r, g, b = img.split()
r_arr = np.array(r, dtype=np.float32)
g_arr = np.array(g, dtype=np.float32)
b_arr = np.array(b, dtype=np.float32)
bw_arr = 0.40 * r_arr + 0.40 * g_arr + 0.20 * b_arr
bw_arr = np.clip(bw_arr, 0, 255).astype(np.uint8)
bw = Image.fromarray(bw_arr, mode='L')

# Step 2: Tone curve — power ~1.95, moderate shadow crush
lut = []
for i in range(256):
    v = i / 255.0
    out = v ** 1.95  # moderate darkening, not aggressive
    if out < 0.25:
        out = out * 0.55  # crush ONLY the deepest shadows
    lut.append(int(min(out, 1.0) * 255))
bw_curved = bw.point(lut)

# Step 3: Contrast — firm but not brutal
enhancer = ImageEnhance.Contrast(bw_curved)
bw_contrast = enhancer.enhance(2.0)

# Step 4: Light sharpening
bw_sharp = bw_contrast.filter(ImageFilter.UnsharpMask(radius=1.2, percent=105, threshold=3))

# Step 5: Subtle film grain
arr = np.array(bw_sharp, dtype=np.float32)
noise = np.random.normal(0, 4, arr.shape).astype(np.float32)
arr = np.clip(arr + noise, 0, 255).astype(np.uint8)
final = Image.fromarray(arr, mode='L')
final.save('output.jpg', quality=95)
```

## Style-Matching Workflow (when Tanzim sends a reference)
1. Load the reference sample, convert to greyscale
2. Measure: mean, std, dark%, mid%, light%
3. Tune the power curve and shadow-crush threshold to match those stats
4. Keep the mean within ~10 points of the reference
5. Never let dark% exceed ~75% for portrait subjects — subjects go muddy/lost

## What NOT to Do
- **Power curve ^2.2–^3.5** = too aggressive for portraits, ruins the image
- **Contrast enhance >2.5** without careful curve prep = crushed blacks everywhere
- **Simple `.convert('L')`** = flat, lifeless, not editorial — always do channel mixing

## Delivery
Upload to Google Drive and share the link. Use `~/.hermes/google_token.json` for OAuth (refresh first). See `google-oauth-credentials` skill for the upload pattern.

## Iteration Protocol
After delivering, ask what's off (too dark / too flat / too much grain) rather than guessing. One targeted question beats re-running blind.
