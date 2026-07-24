---
name: gsheet-bulk-update
description: Safely apply bulk updates to a Google Sheet (append rows, update ranges) without breaking formulas/structure. Use for any multi-cell sheet write.
---

# Safe Google Sheet bulk update

Use for any multi-row/range write to a Sheet (trackers, client sheets, persona extraction tabs).

## Core Steps
1. Read the sheet's structure first (headers, tabs, formula columns).
2. Append rows or write to data cells only — never overwrite formula cells or headers.
3. Batch the write; preserve column order; match existing date/number formats.
4. Re-read a sample after writing to confirm it landed correctly.

## Consolidating Multiple Tabs

When merging two question/data tabs (e.g., "Magazine Questions" + "[Name]'s Persona"):

1. **Read both tabs fully** — Use `.values().get()` with wide range (e.g., `A:Z`)
2. **Identify what to keep**:
   - Answered data (any row where `Answer` column is populated)
   - Better-quality questions (narrative-driven > data-collection)
3. **Build consolidated list**:
   - Start with header row
   - Add all answered questions (preserve exact format)
   - Reformat new questions to match existing structure
4. **Clear and rewrite target tab**:
   - `.values().clear()` the destination range
   - `.values().update()` with consolidated data starting at A1
5. **Verify**: Re-read to confirm row count and that no data was lost

### Code Pattern
```python
# Read both tabs
persona_data = sheets.spreadsheets().values().get(
    spreadsheetId=sheet_id, range="'Persona Tab'!A:E"
).execute().get('values', [])

magazine_data = sheets.spreadsheets().values().get(
    spreadsheetId=sheet_id, range="'Magazine Questions'!A:E"
).execute().get('values', [])

# Extract answered questions
answered = [row for row in persona_data[1:] if len(row) >= 5 and row[4]]

# Build consolidated
consolidated = [persona_data[0]]  # Header
consolidated.extend(answered)
consolidated.extend(new_questions_reformatted)

# Clear and write
sheets.spreadsheets().values().clear(
    spreadsheetId=sheet_id, range="'Persona Tab'!A:E"
).execute()

sheets.spreadsheets().values().update(
    spreadsheetId=sheet_id,
    range="'Persona Tab'!A1",
    valueInputOption='RAW',
    body={'values': consolidated}
).execute()
```

## Pitfalls
- Writing into a formula column silently breaks the sheet
- Mismatched formats corrupt sorting
- **Never clear-then-write without reading first** — you'll lose data if the clear succeeds but write fails
- Don't assume tab structure — always read headers to confirm column positions

## Verification
Post-write read shows new data correct, formulas + headers intact.
