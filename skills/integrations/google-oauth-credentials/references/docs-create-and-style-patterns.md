# Google Docs — Create + Style Programmatically

Recipe for building a formatted Google Doc from scratch (title, headings, bullets)
via the Docs API. Verified working in Tanzim's environment against
`~/.hermes/google_token.json` (has `documents` + `drive` scopes).

## The whole flow

1. Load creds (see SKILL.md primary path), `creds.refresh(Request())`.
2. `docs = build('docs','v1',credentials=creds)` and (optional) `drive = build('drive','v3',...)`.
3. Create empty doc: `docs.documents().create(body={'title': '...'}).execute()` → grab `documentId`.
4. Insert **all** body text in one `insertText` at index 1, then apply paragraph
   styles by range in the same `batchUpdate`.

## The index-tracking gotcha (the part that bites)

Docs indices start at **1**, not 0. When you build one big text blob and want to
style individual lines, track each line's start/end as you concatenate — DON'T try
to recompute indices after insertion. Build the string and the style ranges together:

```python
full = ""
ranges = []  # (start, end, kind)
for kind, txt in content:            # content = list of (kind, text)
    start = len(full) + 1            # +1 because Docs is 1-indexed
    full += txt + "\n"
    end = start + len(txt)
    ranges.append((start, end, kind))

requests = [{'insertText': {'location': {'index': 1}, 'text': full}}]
for start, end, kind in ranges:
    if kind in ('TITLE', 'HEADING_2'):
        requests.append({'updateParagraphStyle': {
            'range': {'startIndex': start, 'endIndex': end + 1},   # +1 to catch the paragraph mark
            'paragraphStyle': {'namedStyleType': kind},
            'fields': 'namedStyleType'}})
    elif kind == 'BULLET':
        requests.append({'createParagraphBullets': {
            'range': {'startIndex': start, 'endIndex': end},
            'bulletPreset': 'BULLET_DISC_CIRCLE_SQUARE'}})

docs.documents().batchUpdate(documentId=doc_id, body={'requests': requests}).execute()
```

## Notes

- Named style types: `TITLE`, `SUBTITLE`, `HEADING_1`..`HEADING_6`, `NORMAL_TEXT`.
- `createParagraphBullets` turns existing paragraphs into a bulleted list; the
  bullet preset auto-nests disc/circle/square by indent level.
- One `batchUpdate` handles insert + all styling — no need to round-trip.
- Doc is created in the account's Drive root; share/move via the `drive` client if needed.
- Resulting URL: `https://docs.google.com/document/d/{doc_id}/edit`.
- For scope docs / drafts, flag figures as "modelled, not verified" in the body when
  numbers are estimates — Tanzim wants nothing leaving looking like fact unchecked.
