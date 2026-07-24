# Google Drive Bulk Image Scanning with AI Vision

Pattern for scanning large image collections in Google Drive to find and extract structured data (contacts, tables, specific document types).

## When to use

- User needs to find specific image types across hundreds/thousands of Drive images
- Target images contain structured data (spreadsheets, contact lists, forms, tables)
- User says "make sure you get all of them" or "quality over speed" or "I know there are more"

## Progressive refinement workflow

Don't assume one pass will catch everything. User knows their data better than OCR/vision gates.

### Pass 1: OCR gating (fast, cheap, lossy)
Use when speed matters and some misses are acceptable:
1. Download image
2. Run OCR (pytesseract)
3. Apply regex patterns (emails, phones, names)
4. Only send to vision if OCR passes threshold (e.g., 3+ emails AND 3+ phones)
5. ~0.5s per image, cheap

**Pitfall:** OCR gating WILL miss images where:
- Text is stylized/non-standard fonts
- Image quality is poor
- Data is in grid format that OCR misreads
- Screenshot has overlays/buttons obscuring text

### Pass 2: Full vision (no gating)
Use when user says "you missed some" or "I know there are more":
1. Download image
2. Send EVERY image to vision model
3. Use direct classification prompt
4. ~2-3s per image, catches most

### Pass 3: Deep reasoning (slow, thorough)
Use when user explicitly wants maximum recall:
1. Download image
2. Use research reasoning prompt with step-by-step analysis
3. "Be INCLUSIVE if uncertain" instruction
4. ~5s per image, catches edge cases

**Warning:** Deep reasoning can be TOO inclusive — will flag near-matches that aren't quite right.

### Pass 4: Pattern scan for stragglers
Use after passes 1-3 if user still suspects misses:
1. Sample ~15 images per folder evenly distributed
2. Quick categorization: "Categorize this image in 2-4 words"
3. Look for categories that match target (e.g., "spreadsheet contact list")
4. Check those specific images manually

This pass often catches 1-2 more that all previous passes missed.

## Research reasoning prompt

When accuracy matters, use step-by-step reasoning:

```python
prompt = """You are an expert image analyst. Analyze this image with deep reasoning.

TASK: Determine if this is a screenshot of a [TARGET TYPE].

THINK STEP BY STEP:
1. What type of image is this? (photo, screenshot, document, etc.)
2. If it's a screenshot, what application is shown?
3. Is there a [STRUCTURE] visible?
4. Are there multiple [DATA ITEMS]?
5. For each item, can you identify: [REQUIRED FIELDS]?

A MATCH must have:
- [Specific criteria]

NOT a match:
- [Exclusion criteria]

IMPORTANT: Be INCLUSIVE if uncertain. If it MIGHT be [TARGET], say YES.

Provide your reasoning, then on the FINAL LINE write only: MATCH or NO_MATCH"""
```

## Common false positives to exclude

Deep reasoning with "be inclusive" instruction catches edge cases but also flags these near-misses:

| False Positive | Why it matches | How to filter |
|----------------|----------------|---------------|
| **Zoom/video call screenshots** | "Multiple people in grid" | Exclude "video conferencing", "participant tiles", "gallery view" |
| **Phone call logs** | "Names and phone numbers in list" | Exclude "call history", "recents", "scam likely" |
| **Social media profiles** | "Contact info visible" | Exclude "profile", "followers", "bio" |
| **Chat screenshots** | "Names in conversation" | Exclude "message", "chat", "conversation" |

When verifying matches, have vision describe the image first — if description contains exclusion keywords, delete from results.

## Parallel batch processing

Deploy 4 agents for 4 folders simultaneously:
```python
# Launch 4 background processes
for folder_id, name in folders:
    terminal(background=True, command=f"python3 scan.py {folder_id} '{name}'", notify_on_complete=True)
```

Each agent logs progress to `/tmp/scan_{name}.txt`. Monitor with:
```bash
for i in 1 2 3 4; do echo "=== Folder-$i ==="; tail -3 /tmp/scan_Folder-$i.txt; done
```

## Data extraction and deduplication

After finding target images, extract structured data:

1. **Extract with vision:**
```python
prompt = """Extract ALL [records] from this image.
Return ONLY a JSON array: [{"field1": "value", "field2": "value"}, ...]"""
```

2. **Deduplicate against existing data:**
```python
# Load existing emails from sheet
existing_emails = set(row[3].lower() for row in sheet_data)

# Only add truly new contacts
for contact in extracted:
    if contact['email'].lower() not in existing_emails:
        new_contacts.append(contact)
        existing_emails.add(contact['email'].lower())
```

3. **Handle OCR variations:**
   - Same person may appear as `katejune@gmail.com` and `katebjune@gmail.com` (OCR error)
   - Use fuzzy matching on email prefix if strict dedup isn't critical
   - Or keep all and let user clean up manually

## Cross-match verification

After extraction, verify nothing was lost:

1. Re-extract all emails from source images
2. Compare against destination sheet
3. Report any "missing" (accounting for OCR variations)
4. If < 5% missing and they're all near-matches of existing entries, data integrity is confirmed

## Quality check pattern

```python
email_pattern = re.compile(r'^[^@\s]+@[^@\s]+\.[^@\s]+$')
phone_pattern = re.compile(r'^\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}$')

for row in data:
    issues = []
    if not email_pattern.match(row['email'].split('/')[0].strip()):
        issues.append("bad email")
    if not phone_pattern.match(row['phone'].replace(" ", "")):
        issues.append("bad phone")
    if issues:
        # Mark as UNCLEAR rather than guessing
        row['email'] = 'UNCLEAR - ' + row['email']
```

## Pattern analysis for large collections

To understand what's in a large image collection before targeted scanning:

```python
# Sample ~15 images per folder evenly
step = max(1, len(files) // 15)
samples = [files[i] for i in range(0, len(files), step)][:15]

# Quick categorization
prompt = "Categorize this image in 2-4 words. Examples: 'screenshot app', 'person photo', 'food photo', 'document scan', 'meme', 'fitness workout'. Just the category."

# Aggregate results
categories = defaultdict(list)
for img in samples:
    category = vision_analyze(img, prompt)
    categories[category].append(img['name'])

# Report patterns
for cat, files in sorted(categories.items(), key=lambda x: -len(x[1])):
    print(f"{cat.upper()} ({len(files)} images)")
```

Also analyze filename patterns:
- `IMG_` numbered files (standard camera roll)
- UUID-style names (app exports)
- Named files like `Blair_MAIN - 16.png` (project assets)
- `PhotoRoom_*`, `GPTempDownload*` (specific apps)

## After successful extraction

Once data is verified in destination:
1. Delete source images from Drive (they're now noise)
2. Use PATCH with `trashed: true` for trash, or DELETE for permanent removal
3. Add `time.sleep(0.3)` between deletions to avoid rate limiting

## Token usage note

- **Haiku + OAuth token (Bearer)**: Fast, cheap — use for bulk initial scans
- **Sonnet/Opus + API key (x-api-key)**: Use when "deep research reasoning" is needed

The OAuth token only works with Haiku; Sonnet/Opus require ANTHROPIC_API_KEY.

## Session example: PII contact sheet scanning

**Goal:** Find spreadsheet screenshots with Name + Phone + Email from 557 images across 4 folders.

**Results by approach:**
| Approach | Matches | Time | Notes |
|----------|---------|------|-------|
| OCR gate (strict) | 3 | ~10 min | Fast but missed 6 real matches |
| Full vision | 9 | ~25 min | Caught most |
| Deep reasoning | 11 | ~40 min | 2 false positives (Zoom, call log) |
| Pattern scan | +1 | ~5 min | Found `IMG_5496.JPEG` as "spreadsheet contact list" |

**Final:** 10 legitimate contact sheets, 57 contacts extracted to Google Sheet.

**Key learning:** When user says "I know there are more," they're usually right. Progressive refinement (4 passes) beats any single approach.
