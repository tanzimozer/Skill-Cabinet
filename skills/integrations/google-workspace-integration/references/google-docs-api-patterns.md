# Google Docs API — working patterns (verified Jun 2026)

All verified building Tanzim's Timbr feasibility report. Auth via the standard
`~/.hermes/google_token.json` creds (manual refresh first if expired). Build:

```python
docs  = build("docs",  "v1", credentials=creds)
drive = build("drive", "v3", credentials=creds)
```

## 1. Create a doc + insert body text + make shareable

```python
doc = docs.documents().create(body={"title": "Report Title"}).execute()
doc_id = doc["documentId"]

# Insert all body text at the top (index 1)
docs.documents().batchUpdate(documentId=doc_id, body={"requests": [
    {"insertText": {"location": {"index": 1}, "text": body_string}}
]}).execute()

# Anyone-with-link can VIEW (neutral share — Tanzim forwards to whoever)
drive.permissions().create(fileId=doc_id, body={"type": "anyone", "role": "reader"}).execute()

link = f"https://docs.google.com/document/d/{doc_id}/edit"
```

## 2. Insert a REAL table (never ASCII art)

Insert the table at the current end of the doc, THEN populate cells.

```python
# Find current end index
d = docs.documents().get(documentId=doc_id).execute()
end = d["body"]["content"][-1]["endIndex"] - 1

docs.documents().batchUpdate(documentId=doc_id, body={"requests": [
    {"insertTable": {"location": {"index": end}, "rows": 4, "columns": 5}}
]}).execute()
```

## 3. Populate table cells — REVERSE ORDER (the critical gotcha)

After inserting, re-fetch the doc, walk `tableRows`/`tableCells`, grab each cell's
first-paragraph `startIndex`, then insert text **from the last cell to the first**.
If you insert front-to-back, every insertion shifts all later cells' indices and
the text lands in the wrong cells.

```python
d = docs.documents().get(documentId=doc_id).execute()
table_el = next(el for el in d["body"]["content"] if "table" in el)

cells = []
for r, row in enumerate(table_el["table"]["tableRows"]):
    for c, cell in enumerate(row["tableCells"]):
        start = cell["content"][0]["startIndex"]
        cells.append((r, c, start))

data = [
    ["Trainers", "Clients/Trainer", "Total Clients", "Monthly", "Annual"],
    ["255", "15", "3,825", "$95,625", "$1.15M"],
    ["255", "20", "5,100", "$127,500", "$1.53M"],
    ["250", "20", "5,000", "$125,000", "$1.50M"],
]

reqs = []
for r, c, start in sorted(cells, key=lambda x: -x[2]):   # DESCENDING by index
    reqs.append({"insertText": {"location": {"index": start}, "text": data[r][c]}})
docs.documents().batchUpdate(documentId=doc_id, body={"requests": reqs}).execute()
```

## 4. Surgical single-value edits (no rebuild)

Ideal when one number changes (e.g. target 500 → 5,000). Replace exact strings:

```python
reqs = [
  {"replaceAllText": {"containsText": {"text": "Success = 500 paying clients at $25/mo.", "matchCase": False},
                      "replaceText": "Success = 5,000 paying clients at $25/mo."}},
  # ...one entry per string to swap
]
docs.documents().batchUpdate(documentId=doc_id, body={"requests": reqs}).execute()
```

## 5. Full rebuild (wipe + repopulate)

When the structure changes enough that surgical edits get messy, clear the body
and rebuild. Build text+table in separate batchUpdate calls (insertTable needs the
text already in place so the end-index is correct).

```python
d = docs.documents().get(documentId=doc_id).execute()
end = d["body"]["content"][-1]["endIndex"] - 1
if end > 1:
    docs.documents().batchUpdate(documentId=doc_id, body={"requests": [
        {"deleteContentRange": {"range": {"startIndex": 1, "endIndex": end}}}
    ]}).execute()
# then: insert partA text -> insert table -> populate cells (reverse) -> insert partB text
```

## Formatting preferences (Tanzim)
- **Neutral docs** — no recipient names baked in; he forwards to whoever he likes.
- **One point per line** — no wrapping clutter; condensed, easy on the eye.
- **Real tables** for any numeric matrix — never monospace/ASCII spacing.
- Avoid em-dashes-as-bullets producing ragged rows; keep each row a single clean point.
