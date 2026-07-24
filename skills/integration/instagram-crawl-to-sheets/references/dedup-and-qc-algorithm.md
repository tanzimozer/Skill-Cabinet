# Deduplication + Quality Check Algorithm

Mandatory validation logic that runs on every crawl before writing to Sheets.

## Deduplication Logic

**Input:** Crawl results (50 profiles) + existing sheet data (usernames in column A)

**Process:**
1. Query existing tab, extract all usernames from column A (starting row 2, skip header)
2. Build set of existing usernames
3. Iterate through crawl batch:
   - If username exists in sheet: SKIP (log with ⚠️)
   - If username is new: KEEP
4. Only new profiles proceed to QC

**Output:** Cleaned batch with duplicates removed

**Logging:**
```
  ⚠️  Duplicate found: leoniemhikes — skipping (already in sheet)
  Duplicates skipped: 50
```

## Quality Check Scoring

Run after deduplication. Validates data integrity of new (non-duplicate) rows.

### Validation Rules

For each row in the cleaned batch:
- **Followers field:** Check if value exists and is not empty
  - "TBD" is acceptable (marked as `invalid_followers` but included in output)
  - Empty string: counts as invalid
- **Username field:** Must exist (dedupe already guarantees this)
- **Crawled_at field:** Must be a valid date string

### Score Calculation

```
quality_score = (valid_rows / total_rows) * 100 - (duplicates_removed / total_rows) * 50
```

**Range:** 0–100
- 100 = all rows valid, no duplicates
- 70+ = acceptable (passes default threshold)
- <70 = warning (print to console, log flagged rows, but still write)

### Quality Check Report

Print after validation completes:

```
✅ QUALITY CHECK REPORT
   Total rows: 50
   Valid rows: 48
   Duplicates removed: 0
   Invalid followers: 2
   Quality score: 96/100
```

### Score Interpretation

- **90+:** Excellent. Data ready for immediate use.
- **70–89:** Good. Minor data gaps (marked as TBD). Review before publishing if critical.
- **<70:** Warning. Significant data quality issues. Review before publishing.

## Why Dedup + QC?

1. **Deduplication prevents data sprawl** — same profile never appears twice in sheet
2. **Quality checks ensure trustworthiness** — score tells you data quality at a glance
3. **Logging provides visibility** — console output shows exactly what was skipped and why
4. **Non-blocking validation** — score <70 triggers warning but does not prevent write (user decision to filter)

## Error Scenarios

### All 50 profiles are duplicates
- Total rows: 50, Valid rows: 0, Duplicates removed: 50
- Quality score: 0/100 (warning triggered)
- Output: Header row only (no data rows)
- This is correct behavior (no new data to write)

### 40 new, 10 duplicates
- Total rows: 50, Valid rows: 40, Duplicates removed: 10
- Quality score: ~80/100 (passes threshold)
- Output: Header + 40 new rows

### Some profiles missing follower counts
- Marked as "TBD" in output
- Counted in `invalid_followers` but included in valid rows
- Example: "TBD" vs. "512K" in Followers column
- User can filter these later if needed

## Implementation Notes

- **Session cookies required:** Script uses Instagram session (stored at `~/.hermes/.ig_cookies.json`)
- **Google OAuth required:** Token stored at `~/.hermes/google_token.json`
- **Batch size:** 50 profiles per crawl (configurable)
- **Threshold:** 70/100 for quality score warning (configurable)
