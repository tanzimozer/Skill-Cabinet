# PII Scanning History — Lessons Learned

## June 2026 Session: Spreadsheet Contact Detection

### What the user wanted
Find screenshots of Excel/Sheets showing contact lists: rows with name + phone + email. Not photos, not chat screenshots, not single contacts — only multi-row spreadsheet tables.

### Methods tested

**Method 1: OCR + regex (name/phone/email patterns)**
- Result: ~98% noise
- Problem: Too many false positives. Any image with scattered text containing an email or phone got flagged.

**Method 2: Vision-only classification**
- Prompt: "Does this image contain any of these: a person's full name, an email address, or a phone number?"
- Result: Still noisy — OR logic matched too broadly

**Method 3: Strict AND + spreadsheet requirement** ✅ WINNER
- OCR gate: requires ≥2 emails AND ≥2 phones
- Vision prompt: "Is this a spreadsheet with 3+ rows each containing a person name, phone number, and email address? YES or NO only."
- Result: 3 true matches out of 557 images — correct signal

### Critical correction from user
"For filter if an image does not have name + phone number + email, it should not be in PII NEW"

This clarified: AND logic, not OR. All three fields must be present.

### Pipeline failures encountered

1. **Deleted everything on error** — First vision scan returned 401 errors (wrong auth), but the script still marked files as "no PII" and deleted them. All 100 files trashed.
   - Fix: Fail-safe logic — if vision returns ERROR, keep the file

2. **x-api-key header 401** — OAuth token requires `Authorization: Bearer`, not `x-api-key` header
   - Fix: Use Bearer auth for all Anthropic calls with this token

3. **Model 404 errors** — `claude-sonnet-4-5-20250514` and `claude-3-5-sonnet-20241022` returned 404 with OAuth token
   - Fix: Use `claude-haiku-4-5` which works reliably

### Final numbers (June 2026 full scan)

| Folder | Images | OCR Rejected | Vision Rejected | Matched |
|--------|--------|--------------|-----------------|---------|
| iCloud-1 | 176 | 173 | 0 | 3 |
| iCloud-2 | 163 | 161 | 2 | 0 |
| iCloud-3 | 111 | 109 | 2 | 0 |
| iCloud-4 | 107 | 107 | 0 | 0 |
| **Total** | **557** | **550** | **4** | **3** |

### Data extraction output

3 matched images contained 20 total contacts, extracted and written to "PIIX collection" Google Sheet:
- Sheet ID: `1VD_hkS81x8lKcgK412I4Apk-icoGuJISoQbWfuY6zok`
- Columns: Serial, Name, Phone, Email

### Key takeaway
For visual content filtering at scale: OCR gate first (cheap, fast), vision confirm second (expensive, accurate). Never delete on error. AND logic > OR logic when precision matters.
