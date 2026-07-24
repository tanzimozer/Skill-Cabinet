# TIMBR STRENGTH DB — Restore from FX - 2

## When to use
STRENGTH DB was cleared or overwritten with wrong data. FX - 2 is the canonical backup.

## FX - 2 Column Mapping
FX - 2 row structure:
`S-Level | Exercise Name | Difficulty | Learning Curve | Risk of Injury | Muscle Size | Muscle Part | Muscle Group | Skill | Flexibility | Grip | Load | Cluster`

This maps directly to STRENGTH DB columns — rename `S-Level` → `Computed Level` in the header only.

## Restore Procedure
```python
# Read FX - 2
result = svc.spreadsheets().values().get(spreadsheetId=SHEET_ID, range='FX - 2').execute()
fx2_rows = result.get('values', [])

exercises = []
header = ['Computed Level', 'Exercise Name', 'Difficulty', 'Learning Curve', 'Risk of Injury',
          'Muscle Size', 'Muscle Part', 'Muscle Group', 'Skill', 'Flexibility', 'Grip', 'Load', 'Cluster']

for row in fx2_rows:
    if not row: continue
    if row[0] in ('S1', 'S2', 'S3') and len(row) >= 13:
        exercises.append(row[:13])

# Clear and rewrite STRENGTH DB
svc.spreadsheets().values().clear(spreadsheetId=SHEET_ID, range='STRENGTH DB').execute()
svc.spreadsheets().values().update(
    spreadsheetId=SHEET_ID,
    range='STRENGTH DB!A1',
    valueInputOption='RAW',
    body={'values': [header] + exercises}
).execute()
```

## Known row counts
- FX - 2 canonical: 60 exercises (20 per S-level)
- STRENGTH DB after Jul 2026 expansion: 149 exercises (88 added by Friday)

## Note
FX - 2 only contains the original 60 exercises. The 88 added by Friday in Jul 2026 are NOT in FX - 2.
If a full restore is needed from the expanded state, use Google Sheets version history (File → Version history → See version history).
