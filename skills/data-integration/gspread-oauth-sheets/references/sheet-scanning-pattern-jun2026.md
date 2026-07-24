# Sheet Scanning & Search Pattern (Jun 2026)

## Context
Task: Scan all 31 worksheets in a large Google Sheet (TerraJob tracking sheet, 1v6CY46PBfGyrde8uuMzPv1cETZrOiflUj_HY34SJC_Q) to locate two target companies by partial keyword match and extract full row data.

## Pattern: Multi-Sheet Scan with Incremental Search Refinement

### Setup
```python
import gspread
from google.oauth2.credentials import Credentials
import json

with open('/home/hermes/.hermes/google_oauth_full.json', 'r') as f:
    creds_data = json.load(f)

creds = Credentials(
    token=creds_data['access_token'],
    refresh_token=creds_data['refresh_token'],
    token_uri='https://oauth2.googleapis.com/token',
    client_id=creds_data['client_id'],
    client_secret=creds_data['client_secret'],
    scopes=creds_data['scopes'].split()
)

gc = gspread.authorize(creds)
sheet = gc.open_by_key(SHEET_ID)
worksheets = sheet.worksheets()
```

### Metadata Phase
```python
# List all tabs to understand scope
print(f"Total worksheets: {len(worksheets)}")
for ws in worksheets:
    print(f"  - {ws.title}")
```

### Scan Phase: Full-Text Search Across All Cells
```python
TARGETS = ['Fluxx Labs', 'Foundation AI']  # Exact targets
SEARCH_TERMS = ['Fluxx', 'Foundation']      # Partial fallback

results = {target: None for target in TARGETS}

for ws in worksheets:
    sheet_name = ws.title
    try:
        values = ws.get_all_values()
        if not values:
            continue
        
        for row_idx, row in enumerate(values, start=1):
            # Join all cells in row to catch matches across columns
            row_text = ' '.join(str(cell) for cell in row).lower()
            
            # First pass: exact match
            for target in TARGETS:
                if target.lower() in row_text:
                    if results[target] is None:
                        results[target] = {
                            'sheet': sheet_name,
                            'row_number': row_idx,
                            'data': row
                        }
                        print(f"FOUND '{target}' at {sheet_name}!{row_idx}")
    
    except Exception as e:
        print(f"Error scanning {sheet_name}: {e}")

# Second pass: partial match fallback if exact match failed
if any(v is None for v in results.values()):
    for ws in worksheets:
        sheet_name = ws.title
        try:
            values = ws.get_all_values()
            for row_idx, row in enumerate(values, start=1):
                row_text = ' '.join(str(cell) for cell in row).lower()
                
                for search_term in SEARCH_TERMS:
                    if search_term.lower() in row_text:
                        # Backfill if this term's target wasn't found yet
                        for target in TARGETS:
                            if target.lower().startswith(search_term.lower()) and results[target] is None:
                                results[target] = {
                                    'sheet': sheet_name,
                                    'row_number': row_idx,
                                    'data': row
                                }
                                print(f"FOUND (partial) '{target}' at {sheet_name}!{row_idx}")
        except:
            continue
```

### Extract Phase: Columnar Data
```python
# Assume headers are in row 1 or data structure is known
for target in TARGETS:
    if results[target]:
        res = results[target]
        row_data = res['data']
        
        # Extract by position (assumes stable column order)
        company_name = row_data[1] if len(row_data) > 1 else None
        job_title = row_data[2] if len(row_data) > 2 else None
        resume_link = row_data[3] if len(row_data) > 3 else None
        job_url = row_data[4] if len(row_data) > 4 else None
        
        print(f"{target}")
        print(f"  Company: {company_name}")
        print(f"  Job Title: {job_title}")
        print(f"  Resume: {resume_link}")
        print(f"  URL: {job_url}")
```

## Key Insights

### Why This Pattern Works
1. **No header assumptions**: `ws.get_all_values()` returns all cells; we search the full text of each row
2. **Graceful partial match**: If company names are typos or abbreviations in the sheet (e.g., "Foundation Al" instead of "Foundation AI"), the partial search catches them
3. **Scope visibility**: Printing metadata (sheet count, tab names) at start confirms the scan runs comprehensively
4. **Efficient two-pass**: Exact match first (fast), fallback to partial only if needed

### Pitfalls
- **Case sensitivity**: Always `.lower()` both search term and row text for robustness
- **Whitespace**: `' '.join(row)` handles mixed empty cells gracefully
- **Large sheets**: `get_all_values()` is simpler than pagination but can be slow on sheets with 10K+ rows; consider adding row limits or using `range()` queries if performance is critical
- **Special characters**: Tab names with `/` (e.g., "05/14") work fine with gspread; no URL encoding needed

### Real Result
Scanned **31 worksheets** in one execution:
- Found "Fluxx Labs" (abbreviated as "Fluxx") in sheet "05/14", row 11
- Found "Foundation AI" (stored as "Foundation Al") in sheet "05/14", row 43
- Extracted full rows with company, job title, resume link, and job URL
- Execution time: <2 seconds for all worksheets

## When to Use This Pattern
- Scanning a multi-sheet job tracker, candidate database, or audit log
- Looking for partial matches or typos across large datasets
- Need to extract full row data once target is located
- No need for filtered views — raw search across all cells is acceptable

## When NOT to Use
- If you need column filtering (e.g., only scan company column): use `get_values(range)` with column-specific notation instead
- If sheet has 100K+ rows and you need sub-second response: add row pagination or use Google Sheets API batching
- If header row is unstable or mixed formats: add a header detection phase first
