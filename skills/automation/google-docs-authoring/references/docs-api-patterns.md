# Docs API — copy-paste patterns

Verified working July 2026 building the TIMBR scope doc.

## Insert a styled section at an anchor

```python
# find anchor paragraph start index
d = docs.documents().get(documentId=doc_id).execute()
insert_index = None
for el in d['body']['content']:
    p = el.get('paragraph')
    if not p: continue
    txt = ''.join(r.get('textRun',{}).get('content','') for r in p.get('elements',[]))
    if txt.startswith('10. Investor Evaluation'):   # your anchor
        insert_index = el['startIndex']; break

# content as (kind, text): S=HEADING_2, T=HEADING_3, B=bullet, P=plain
content = [('S','9.9 Churn'), ('P','intro line'), ('B','a bullet'), ('B','another')]

full = ""; ops = []
for kind, txt in content:
    start = insert_index + len(full)
    full += txt + "\n"
    end = start + len(txt)
    if kind == 'S': ops.append((start, end, 'H2'))
    elif kind == 'T': ops.append((start, end, 'H3'))
    elif kind == 'B': ops.append((start, end, 'BULLET'))

requests = [{'insertText': {'location': {'index': insert_index}, 'text': full}}]
for start, end, style in ops:
    if style == 'H2':
        requests.append({'updateParagraphStyle':{'range':{'startIndex':start,'endIndex':end+1},
            'paragraphStyle':{'namedStyleType':'HEADING_2'},'fields':'namedStyleType'}})
    elif style == 'H3':
        requests.append({'updateParagraphStyle':{'range':{'startIndex':start,'endIndex':end+1},
            'paragraphStyle':{'namedStyleType':'HEADING_3'},'fields':'namedStyleType'}})
    elif style == 'BULLET':
        requests.append({'createParagraphBullets':{'range':{'startIndex':start,'endIndex':end},
            'bulletPreset':'BULLET_DISC_CIRCLE_SQUARE'}})

docs.documents().batchUpdate(documentId=doc_id, body={'requests': requests}).execute()
```

Note: because you insert the whole `full` string at one index, later paragraphs
push down automatically — the recorded `start/end` are all relative to the same
base `insert_index`, so they stay valid within this single batch. Correct.

## Dump the indexed outline (your edit map before a sweep)

```python
d = docs.documents().get(documentId=doc_id).execute()
def para_text(p): return ''.join(r.get('textRun',{}).get('content','') for r in p.get('elements',[]))
for el in d['body']['content']:
    p = el.get('paragraph')
    if not p: continue
    txt = para_text(p).rstrip('\n')
    if not txt: continue
    style = p.get('paragraphStyle',{}).get('namedStyleType','')
    tag = {'TITLE':'#','HEADING_2':'##','HEADING_3':'###'}.get(style,'   ')
    print(f"[{el['startIndex']:>5}-{el['endIndex']:>5}] {tag} {txt[:110]}")
```

## Replace paragraphs by range (descending, one batch)

```python
# edits = list of (startIndex, endIndex, new_text)
edits.sort(key=lambda x: x[0], reverse=True)   # CRITICAL: descending
reqs = []
for s, e, new in edits:
    reqs.append({'deleteContentRange':{'range':{'startIndex':s,'endIndex':e-1}}})  # keep newline
    reqs.append({'insertText':{'location':{'index':s},'text':new}})
docs.documents().batchUpdate(documentId=doc_id, body={'requests': reqs}).execute()
```

To DELETE a whole paragraph (including its newline): one
`deleteContentRange` over `{startIndex:s, endIndex:e}`.

## Stale-phrase scan (prove the sweep before AND after)

```python
full = ""
for el in d['body']['content']:
    p = el.get('paragraph')
    if p: full += para_text(p)
flags = {ph: full.count(ph) for ph in
         ["transaction slice","333 ","$1.5M","$25/mo ceiling","stacked subscription"]}
print(flags)   # all zeros == clean
```

## Gotchas hit in practice

- `deleteContentRange` end is EXCLUSIVE; using `endIndex` vs `endIndex-1` decides
  whether the paragraph's trailing newline (and thus its paragraph style) survives.
  Keep the newline (`endIndex-1`) when replacing text in place; consume it
  (`endIndex`) when deleting the whole paragraph.
- A plain paragraph inserted right after a HEADING can inherit the heading's
  named style and render oversized — set `NORMAL_TEXT` explicitly if body text
  looks too heavy.
- Always re-fetch the doc (`documents().get`) between separate edit passes; never
  reuse stale indices from a prior fetch after you've written.
