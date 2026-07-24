---
name: google-sheets-batch-operations
type: integration
description: Safely execute batch read/write operations on Google Sheets with quota awareness, resumable checkpoints, and rate limiting. Consolidate external data, populate derived metrics, manage large-scale sheet updates without hitting API limits.
tags: [google-sheets, oauth, batch-processing, quota-management, data-consolidation]
---

# Google Sheets Batch Operations

Safely execute batch read/write operations on Google Sheets with quota awareness, resumable checkpoints, and rate limiting. Used for consolidating external data, populating derived metrics, and managing large-scale sheet updates without hitting API limits.

## Core Pattern

```python
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from pathlib import Path
import gspread
import time

# 1. Load OAuth token (persistent across sessions)
token_path = Path.home() / '.hermes' / 'google_token.json'
creds = Credentials.from_authorized_user_file(str(token_path))
if creds.expired and creds.refresh_token:
    creds.refresh(Request())

# 2. Authorize client
client = gspread.authorize(creds)

# 3. Open sheet by ID (not name — avoids quota hits on search)
sheet = client.open_by_key(sheet_id)
ws = sheet.worksheet('tab_name')

# 4. Read all data once, batch process in memory
all_data = ws.get_all_values()  # Single API call
```

## Quota Management

**Rate Limits:**
- Read/write quota: ~300 requests/minute per user
- Batch size: 10–50 rows per operation (depends on data size)
- Delay between batches: 30s–60s (safe margin)
- Worksheet operations (add, clear): 1–2 per minute max

**Safe Workflow:**
1. Read entire sheet once → keep in memory
2. Process in batches (10–50 items)
3. Update rows in small chunks (1 row at a time or small ranges)
4. Sleep 30s between batches
5. On 429 (quota exceeded): sleep 60s, retry

**DO NOT:**
- Repeatedly call `get_all_values()` in a loop — read once, iterate locally
- Update individual cells in tight loops without delays
- Create/delete tabs in rapid succession
- Call `open()` by sheet name — use `open_by_key()` instead

## Consolidation Pattern (Many Sheets → One Master)

Common case: Extract data from N source sheets, deduplicate, populate into a master tracking sheet.

```python
sources = {
    'sheet_name_1': 'sheet_id_1',
    'sheet_name_2': 'sheet_id_2',
}

all_data = set()

for sheet_name, sheet_id in sources.items():
    try:
        source = client.open_by_key(sheet_id)
        for ws in source.worksheets():
            rows = ws.get_all_values()
            for row in rows:
                for cell in row:
                    # Extract relevant field (e.g., Instagram handle)
                    if is_valid(cell):
                        all_data.add(normalize(cell))
        time.sleep(0.5)  # Rate limit between worksheets
    except Exception as e:
        print(f"Skipped {sheet_name}: {e}")

# Now populate master sheet with deduplicated data
master_ws.clear()
master_ws.append_row(headers)
master_ws.append_rows([[item] + ['default', 'values'] for item in sorted(all_data)])
```

## Analysis Metrics & Pattern Recognition

When populating derived columns based on fetched data:

1. **Fetch once per source** (API calls are expensive)
2. **Analyze locally** (CPU-bound, no quota cost)
3. **Update in batches** (cluster writes, not one per item)
4. **Add checkpoints** (track which rows have been updated so partial runs can resume)

Example: Instagram handle analysis (followers, growth velocity, bio signals)

```python
# Fetch profile data (expensive — minimize calls)
profile = fetch_instagram_profile(handle)  # 1 API call per handle

# Analyze locally (free)
analysis = {
    'followers_estimate': categorize_followers(profile['followers']),
    'follower_velocity': calculate_velocity(profile['posts'], profile['followers']),
    'bio_signal_strength': score_bio(profile['bio']),
}

# Update sheet in batch (1 update per row, but many rows in parallel is ok)
ws.update(f'D{row_num}', analysis['followers_estimate'])
```

## Resumable Batch Processing

For long-running analyses (100+ items), implement checkpoints:

```python
all_rows = get_all_values()
checkpoint_col = 8  # Last column

for i, row in enumerate(all_rows[1:], 2):  # Skip header, start at row 2
    if row[checkpoint_col]:  # Already processed
        continue
    
    # Process this row
    result = analyze(row)
    
    # Mark as done + write result
    ws.update(f'H{i}', 'done')
    ws.update(f'D{i}', result)
    
    # Batch checkpoint: every 10 rows, wait
    if i % 10 == 0:
        time.sleep(30)
```

## Common Errors & Fixes

| Error | Cause | Fix |
|-------|-------|-----|
| `SpreadsheetNotFound` | Opening by sheet name instead of ID | Use `open_by_key(sheet_id)` — safer and faster |
| 429 Quota Exceeded | Too many requests too fast | Add `time.sleep(60)` and retry; batch in groups of 10 |
| Credential expired | Token refresh failed | Call `creds.refresh(Request())` before each operation |
| `AttributeError: 'Worksheet' object has no attribute X` | Using incorrect gspread method | Check gspread version; many sheet formatting methods don't exist in older versions |

## Design Decisions

**Why OAuth token instead of service account?**
- User may already have Drive access → reuse existing auth
- Service account requires Google Cloud setup + sharing
- If user already has `google_token.json` in `~/.hermes/`, use it
- Fallback: if no token, guide user to create service account

**Why deduplicate in Python, not formulas?**
- Easier to normalize (lowercase, strip @, validate)
- Faster for 1000+ items
- Can be run in isolation (no sheet recalc overhead)

**Why batch in groups of 10?**
- Sweet spot: large enough to feel efficient, small enough to stay well under quota
- 10 items × 30s = 5 min per 10-batch = ~300 items/hour
- Scales to 1000+ items in a single run (2–3 hours)

## Related Skills

- `instagram-data-extraction` — Profile fetching, rate limiting, session management
- `batch-analysis-patterns` — Structuring analysis for quota-aware execution
