---
name: google-docs-authoring
description: Create and iteratively edit Google Docs programmatically via the Docs API — index-safe text insertion, paragraph/heading styling, bullets, and clean-sweep find-and-replace-by-range. Use when Tanzim wants a scope doc, brief, or any structured document built and then revised section-by-section over a conversation.
category: automation
---

# Google Docs Authoring (programmatic, iterative)

Class-level skill for building and evolving a Google Doc through the Docs API in
`execute_code`, section by section, across a long working conversation. The
canonical case: a living **scope / brief document** that grows and gets rewritten
as the user talks through a model (e.g. the TIMBR scope doc — North Star, revenue
model, churn math, investor Q&A).

## Auth (same token as Sheets/Gmail)

`~/.hermes/google_token.json` is a live authorized-user token whose scopes
include `documents` and `drive`. Build the creds and refresh once:

```python
import json
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
t = json.load(open('/home/hermes/.hermes/google_token.json'))
creds = Credentials(token=t.get('token'), refresh_token=t.get('refresh_token'),
    token_uri=t.get('token_uri','https://oauth2.googleapis.com/token'),
    client_id=t.get('client_id'), client_secret=t.get('client_secret'),
    scopes=t.get('scopes'))
if not creds.valid: creds.refresh(Request())
docs = build('docs','v1',credentials=creds)
```

Create a doc → `docs.documents().create(body={'title': '...'}).execute()` returns
`documentId`. URL is `https://docs.google.com/document/d/<id>/edit`. **Persist the
id** (e.g. `open('/tmp/<name>_doc_id.txt','w').write(doc_id)`) so every later edit
in the conversation reuses it instead of spawning a new doc.

## The insertion model — indices are 1-based and SHIFT on every write

The Docs API addresses everything by character index; the body starts at index 1.
The load-bearing rules:

- **Build one big text string, track ranges as you go**, then insert once with a
  single `insertText` at the target index, then apply styling by the recorded
  ranges. Full pattern in `references/docs-api-patterns.md`.
- **Insert bottom-up when doing multiple independent edits**, or apply
  deletes/replaces sorted by start index DESCENDING — otherwise the first edit
  invalidates every later index. This is the #1 footgun.
- To append a NEW section before a known anchor line (e.g. the closing note or
  "Section 10"), fetch the doc, find the anchor paragraph's `startIndex`, insert
  there. Scan paragraphs with:
  `''.join(r.get('textRun',{}).get('content','') for r in p.get('elements',[]))`.

## Styling

- Headings: `updateParagraphStyle` with `namedStyleType` = `TITLE` /
  `HEADING_2` / `HEADING_3`, `fields:'namedStyleType'`, range `startIndex..endIndex+1`.
- Bullets: `createParagraphBullets` with `bulletPreset:'BULLET_DISC_CIRCLE_SQUARE'`
  over the range spanning the bullet lines.
- Bold a single line (e.g. a Q&A question): `updateTextStyle` with
  `textStyle:{'bold':True}`, `fields:'bold'`.
- **Styling-leak pitfall:** when you insert a plain paragraph immediately after a
  HEADING and don't reset its style, it can inherit the heading style — body text
  renders oversized. If body paras look too heavy, explicitly set them to
  `NORMAL_TEXT`. Watch this when the same insert batch mixes headings and prose.

## Clean-sweep editing (the doc drifted, reconcile it)

When a model evolves mid-conversation (e.g. pricing went $25→$20 net, trainer
count was a guess that got corrected), earlier sections contradict later ones.
The sweep:

1. **Dump the whole doc as an indexed outline first** — print every paragraph's
   `[startIndex-endIndex]`, style tag, and text prefix. This is your edit map.
2. **Scan for stale phrases** by string-counting the assembled full text
   (`full.count("transaction slice")`, `full.count("333 ")`, etc.). Zero = clean.
   Run this scan AGAIN after editing to prove the sweep landed.
3. **Replace-by-range**: for each stale paragraph, `deleteContentRange`
   (startIndex..endIndex-1, keeping the trailing newline so paragraph style
   survives) then `insertText` at startIndex with the corrected text. Apply all
   edits in ONE batchUpdate, sorted descending by start index.
4. **Full-paragraph deletion** (removing a now-redundant subsection):
   `deleteContentRange` over startIndex..endIndex (include the newline).

## Working style for scope/brief docs (Tanzim)

- He builds the model by TALKING — each voice note resolves one decision
  (fee-bearer, margin split, churn rate, switching cost). Capture each as its own
  numbered subsection the moment it's resolved; don't wait for the whole thing.
- **Flag the tension, don't just transcribe.** After writing a resolved section,
  name the contradiction or risk it creates one line (e.g. "the $5 incentive
  sunsets exactly when churn would spike unless earned stickiness replaces it").
  He wants the honest downstream implication, not a clean stenographer.
- **Mark unresolved items OPEN explicitly** in the doc body, and flag figures as
  "modelled, not verified" when they're estimates — never let a guess read as
  fact. When he later gives real data, sweep the guesses out.
- When he says "focus everything on <metric>", plant it as a Section 0 North Star
  at the very top and reframe/replace the sections that used the old framing so
  the whole doc reads backwards from that one number.
- Correct his arithmetic quietly but explicitly if a voice note garbles it
  (transcription mangles numbers — "$20 multiplied by $5" meant "20 clients × $5").

See `references/docs-api-patterns.md` for copy-paste insert/style/sweep snippets.
