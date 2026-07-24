# Google Sheets Batch Operations (gspread)

## Problem
Individual `ws.update()` calls are slow (~1 sec per call) and fail with 400 validation errors on range syntax.

**Error example:**
```
gspread.exceptions.APIError: APIError: [400]: Invalid value at 'data.values' (type.googleapis.com/google.protobuf.ListValue), "D2"
```

This happens because `ws.update('D2', value)` is deprecated syntax in newer gspread versions.

## Solution: Use `batch_update()`

### Pattern
```python
updates = []
for i, handle in enumerate(handles):
    row_num = i + 2  # Start at row 2 (row 1 is headers)
    updates.append({
        'range': f'D{row_num}:I{row_num}',
        'values': [[val_d, val_e, val_f, val_g, val_h, val_i]]
    })

# Single batch call (fast, atomic)
ws.batch_update(updates)
```

### Key Points
- **Range syntax**: `'D2:I2'` means columns D through I, row 2. Use ranges, not single cells.
- **Values structure**: `[[val1, val2, val3, ...]]` — nested list (outer list = rows, inner list = columns)
- **Single batch call**: One `batch_update()` with 50–100 ranges is 10–50x faster than 50–100 individual `update()` calls
- **Atomicity**: All updates succeed or all fail (no partial writes)

### Example (Full)
```python
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from pathlib import Path
import gspread

# Auth
token_path = Path.home() / '.hermes' / 'google_token.json'
creds = Credentials.from_authorized_user_file(str(token_path))
if creds.expired and creds.refresh_token:
    creds.refresh(Request())
client = gspread.authorize(creds)

# Open sheet
sheet = client.open_by_key('1Wo0kl-vcalbflt3sUgjwVNaP3ZbtRfaNmH0NqA0j5mw')
ws = sheet.worksheet('Consolidated Handles')

# Prepare batch
updates = []
for i, handle in enumerate(['hannahellisss', 'alexis_ren', 'fitgirl_123']):
    row_num = i + 2
    updates.append({
        'range': f'D{row_num}:I{row_num}',
        'values': [['2.3K (micro)', 'fast_growth', 'active (6-12mo)', '8', '2', '8.5']]
    })

# Execute
ws.batch_update(updates)
print(f"✓ Updated {len(updates)} rows")
```

### Quota & Performance
- Batch size: 50–100 updates per call is safe
- Quota: Each call counts as 1 write quota unit (not per-cell)
- Speed: ~0.5 sec per batch of 50 (vs ~50 sec for 50 individual updates)

### Troubleshooting
- **400 error with range**: Check that range syntax is correct (`D2:I2`, not `D2`)
- **Empty cells**: Use empty string `''` for blank cells, not `None`
- **Type errors**: Values must be strings or numbers; convert booleans/objects first
