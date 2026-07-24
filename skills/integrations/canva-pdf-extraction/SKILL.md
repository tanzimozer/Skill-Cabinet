---
name: canva-pdf-extraction
description: "Export a Canva design as PDF and extract text content page by page. The only reliable way to read Canva design content programmatically — the API does not expose text elements directly."
version: 1.0.0
tags: [canva, pdf, extraction, content, design]
related_skills: [api-credentials-manager]
---

# Canva PDF Extraction

The Canva Connect API cannot read text content from design elements. The only reliable way to extract copy from a Canva design is to export it as PDF, then extract text with `pdftotext`.

## When to use
- Tanzim asks you to "read" a Canva design
- Need to analyse or populate a sheet from Canva content
- Building a change log or PRD from existing designs

## Prerequisites
- Valid Canva access token in `~/.hermes/.canva_credentials`
- `pdftotext` available on the system (part of poppler-utils)
- If token is expired: see `api-credentials-manager` skill for re-auth flow

## Step 1 — Refresh token
Always refresh before use — Canva access tokens expire every 4 hours:

```python
import json, requests

creds = json.load(open('/home/hermes/.hermes/.canva_credentials'))
r = requests.post('https://api.canva.com/rest/v1/oauth/token',
    data={'grant_type':'refresh_token','refresh_token':creds['refresh_token'],
          'client_id':creds['client_id'],'client_secret':creds['client_secret']})
if 'access_token' in r.json():
    creds['access_token'] = r.json()['access_token']
    if 'refresh_token' in r.json():
        creds['refresh_token'] = r.json()['refresh_token']
    json.dump(creds, open('/home/hermes/.hermes/.canva_credentials','w'), indent=2)
else:
    print("REFRESH FAILED:", r.json())  # Full re-auth needed
```

## Step 2 — Find the design ID
```python
headers = {'Authorization': f'Bearer {creds["access_token"]}'}
r = requests.get('https://api.canva.com/rest/v1/designs?query=<search_term>&limit=50', headers=headers)
for d in r.json().get('items', []):
    print(f"'{d['title']}' | {d.get('page_count','?')} pages | ID: {d['id']}")
```

## Step 3 — Request PDF export
```python
r = requests.post('https://api.canva.com/rest/v1/exports',
    json={"design_id": "DAH...", "format": {"type": "pdf", "export_quality": "regular"}},
    headers=headers)
job_id = r.json()['job']['id']
```

**Pitfall:** Format must be `{"type": "pdf", "export_quality": "regular"}` — NOT `"format": "pdf"` (that returns `invalid_field: 'type' must not be null`).

## Step 4 — Poll for completion
```python
import time
for i in range(15):
    time.sleep(3)
    r = requests.get(f'https://api.canva.com/rest/v1/exports/{job_id}', headers=headers)
    status = r.json().get('job', {}).get('status')
    if status == 'success':
        url = r.json()['job']['urls'][0]
        break
    elif status == 'failed':
        print("Export failed:", r.json())
        break
```

## Step 5 — Download and extract text
```python
dl = requests.get(url)
path = f'/tmp/canva_{job_id}.pdf'
open(path, 'wb').write(dl.content)

import subprocess
result = subprocess.run(['pdftotext', path, '-'], capture_output=True, text=True)
text = result.stdout
```

## Step 6 — Multi-design batch export
For multiple designs (e.g. a full series), kick off all export jobs first, then poll all in sequence:

```python
job_ids = {}
for name, design_id in designs.items():
    r = requests.post('https://api.canva.com/rest/v1/exports',
        json={"design_id": design_id, "format": {"type": "pdf", "export_quality": "regular"}},
        headers=headers)
    job_ids[name] = r.json()['job']['id']

pdf_texts = {}
for name, job_id in job_ids.items():
    for i in range(20):
        time.sleep(3)
        r = requests.get(f'https://api.canva.com/rest/v1/exports/{job_id}', headers=headers)
        if r.json().get('job', {}).get('status') == 'success':
            url = r.json()['job']['urls'][0]
            dl = requests.get(url)
            path = f'/tmp/canva_{job_id}.pdf'
            open(path, 'wb').write(dl.content)
            result = subprocess.run(['pdftotext', path, '-'], capture_output=True, text=True)
            pdf_texts[name] = result.stdout
            break
```

## Canva API read capabilities summary
| Operation | Supported | Notes |
|---|---|---|
| List designs | ✅ | `GET /v1/designs?query=...` |
| Get design metadata | ✅ | `GET /v1/designs/{id}` |
| Get page thumbnails | ✅ | `GET /v1/designs/{id}/pages` |
| Export to PDF | ✅ | `POST /v1/exports` |
| Read text elements | ❌ | Not exposed in API |
| Edit text elements | ❌ | No PATCH/PUT for design content |
| Rename design | ❌ | `PATCH /v1/designs/{id}` returns 404 |

## Pitfalls
- `GAPI="python ~/.hermes/..."` fails — use absolute path
- Export format: `{"type": "pdf"}` not `"pdf"` (flat string)
- Token expires every 4 hours — always refresh first
- If `invalid_grant: Token lineage has been revoked` → full re-auth, not just refresh
- `pdftotext` extracts content but loses layout — text from multi-column designs may merge across columns
