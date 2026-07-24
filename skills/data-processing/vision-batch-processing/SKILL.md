---
name: vision-batch-processing
description: Processing large image sets with vision AI for classification, PII detection, or content extraction
trigger: scanning images for patterns, PII detection in photos, classifying image libraries, batch vision analysis
version: 1
---

# Vision Batch Processing

When processing large image sets (100s-1000s) with vision AI for classification, detection, or extraction.

## Multi-Pass Strategy

For high-stakes detection (PII, sensitive content), use progressive passes:

1. **Fast pre-filter** (OCR/regex) — cheap, catches obvious matches
2. **Full vision scan** — every image through vision API, no pre-filtering
3. **Deep reasoning scan** — inclusive matching with research layer

Each pass catches different things. Fast pre-filter has false negatives; deep reasoning has false positives.

## Parallel Batch Architecture

```python
# Split into batches, run parallel workers
BATCH_SIZE = ~150-200 images per worker
MAX_WORKERS = 4-6 (balance API limits vs speed)

# Each worker:
# 1. Lists files from source (Google Drive, local, S3)
# 2. Downloads image → base64
# 3. Sends to vision API with classification prompt
# 4. Logs result, moves/copies matches
```

## Classification Prompt Pattern

```
Analyze this image. Classify into ONE category:
- fitness (workout plans, gym photos, exercise content)
- screenshots_app (app interfaces, settings)
- screenshots_chat (messaging conversations)
- documents (scans, forms, receipts)
- photos_selfie (self-portraits)
- photos_travel (landscapes, travel)
- contact_sheets (names + phone/email in list format)
- uncategorized (doesn't fit above)

Return ONLY the category name, nothing else.
```

## False Positive Handling

Deep reasoning scans are intentionally inclusive — they catch edge cases but also noise.

Common false positives for "contact list" detection:
- Zoom call screenshots (grid of faces with names)
- Call logs (phone numbers but not contact data)
- App notification lists

**Solution:** After matching, run extraction and verify actual data exists before committing.

## Pitfalls

- **OCR pre-filtering misses handwritten or stylized text** — for critical detection, always do a full vision pass
- **Vision API rate limits** — add delays between calls, handle 429s with backoff
- **Large images** — resize before base64 encoding to stay under token limits
- **Auth confusion** — OAuth tokens use `Authorization: Bearer`, API keys use `x-api-key` header

## References

- `references/pii-detection-prompts.md` — specific prompts for PII/contact detection
- `references/pdf-to-reviewable-images.md` — turn a PDF into PNGs for vision review (pdftoppm + PIL contact sheet, no ImageMagick)
