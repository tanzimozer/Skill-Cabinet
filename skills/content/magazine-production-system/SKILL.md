---
name: magazine-production-system
description: "End-to-end system for producing, analysing, and managing TIMBR digital magazines — from Canva export to Google Sheets PRD, change tracking, and MCP-ready edit instructions."
version: 1.0.0
tags: [TIMBR, magazine, Canva, Google Sheets, production, PRD, content]
related_skills: [canva-connect, google-workspace, api-credentials-manager]
---

# Magazine Production System

Covers the full lifecycle: extracting content from Canva designs → analysing structure → building a production Google Sheet → generating change records for MCP execution.

## Sheet Reference
- **Magazine Production Sheet:** `1J4Rv-_NInf_jtjOHNYhTvVEfel0LK_uCfjjozshB2Ew`
- **URL:** https://docs.google.com/spreadsheets/d/1J4Rv-_NInf_jtjOHNYhTvVEfel0LK_uCfjjozshB2Ew/edit

## Tab Structure (as of May 2026)

| Tab | Purpose |
|---|---|
| PRD | Reverse-engineered product requirements from all 5 issues |
| CHANGES | MCP-ready change records (CHG-001 to CHG-030+) |
| Workout Series — Glutes & Hamstring | Per-page analysis |
| Workout Series — Shoulder & Core | Per-page analysis |
| Workout Series — Quads & Calf | Per-page analysis |
| Workout Series — Chest & Tricep | Per-page analysis |
| Workout Series — Back & Bicep | Per-page analysis |

## Column Schema (per issue tab, A–I)

| Col | Header | Content |
|---|---|---|
| A | Page | Page number (1–8) |
| B | Section | Section name |
| C | Content | Extracted raw content from PDF |
| D | Design Pattern / Principle | Why this page works structurally |
| E | Notes / Action | Reusable template rules |
| F | Page Nature | Dynamic or Static |
| G | Purpose | What the page is trying to accomplish |
| H | Underlying Principle | The strategic logic behind how it was built |
| I | Content Creation Questions (5) | 5 questions to answer to produce the page |

## 8-Page Structure (TIMBR Workout Series)

| Page | Section | Nature |
|---|---|---|
| 1 | Cover | Dynamic |
| 2 | TOC + Intro | Dynamic |
| 3 | The Program | Dynamic |
| 4 | Gyms in Seattle | Dynamic |
| 5 | Work & Corporate Life | Dynamic |
| 6 | Recovery Guide | Dynamic |
| 7 | Nutrition / Cross-sell | Static |
| 8 | Subscribe CTA | Static |

Pages 7–8 are identical across all 5 issues. Pages 4–5 share near-identical copy. Only pages 1–3 and 6 are fully issue-specific.

## Canva Design IDs (Series 01)

| Issue | Design ID |
|---|---|
| Glutes & Hamstring | DAHFfAiLO3E |
| Shoulder & Core | DAHKu7sMKdE |
| Quads & Calf | DAHKuy17o8s |
| Chest & Tricep | DAHKuyPqxww |
| Back & Bicep | DAHKu6XleTQ |

## Workflow: Canva → Sheet Population

### Step 1 — Export all designs to PDF
```python
import requests, time, json

creds = json.load(open('/home/hermes/.hermes/.canva_credentials'))
headers = {'Authorization': f'Bearer {creds["access_token"]}', 'Content-Type': 'application/json'}

design_ids = ["DAHFfAiLO3E", "DAHKu7sMKdE", "DAHKuy17o8s", "DAHKuyPqxww", "DAHKu6XleTQ"]

for did in design_ids:
    r = requests.post('https://api.canva.com/rest/v1/exports',
        json={"design_id": did, "format": {"type": "pdf", "export_quality": "regular"}},
        headers=headers)
    job_id = r.json()['job']['id']

    # Poll
    for _ in range(20):
        time.sleep(3)
        r2 = requests.get(f'https://api.canva.com/rest/v1/exports/{job_id}', headers=headers)
        if r2.json()['job']['status'] == 'success':
            url = r2.json()['job']['urls'][0]
            pdf = requests.get(url).content
            open(f'/tmp/{did}.pdf', 'wb').write(pdf)
            break
```

### Step 2 — Extract text from PDF
```bash
pdftotext /tmp/DAHFfAiLO3E.pdf -
```

### Step 3 — Populate sheet tab
Use `sheets.values().update()` with range `'Tab Name'!A1:I9` for all 8 pages + header.

## CHANGES Tab Schema

| Col | Header | Description |
|---|---|---|
| A | Change ID | CHG-001 format |
| B | Tab | Which issue tab this applies to |
| C | Canva Design ID | Design to edit |
| D | Page | Page number |
| E | Element | Element name/type |
| F | Element Description | What the element currently looks like |
| G | Current Value | Exact current text/state |
| H | New Value | What it should become |
| I | Action Type | UPDATE_TEXT / REMOVE_ELEMENT / ADD_ELEMENT |
| J | MCP Instruction | Full natural-language instruction for Claude/MCP |
| K | Rationale | Why this change is being made |
| L | Status | PENDING / DONE / SKIPPED |

## Page 1 (Cover) Changes Applied (May 2026)
Per issue, 3 changes:
1. **Benefit statement** — replace descriptive subtitle with outcome-led line (e.g. "Strength that shows up Monday morning.")
2. **Remove secondary URL** — delete `WWW.SEATTLE.FITNESS`; keep `WWW.TIMBR.FIT` only
3. **Add acquisition CTA** — add `timbr.fit/series` bottom-right corner, small, white/light grey

## Page 2 (TOC + Intro) Changes Applied (May 2026)
Per issue, 3 changes:
1. **Expand TOC** — add missing sections (Work & Lifestyle p.05, Recovery p.06, Subscribe p.08)
2. **Tighten intro opening** — lead with outcome line from cover + "Here is how you build it."
3. **Standardise anti-Instagram line** — "Real strength. Real shape. Built for life — not for Instagram."

## Key Insights (PRD Summary)

- **50% of the magazine is templated** — pages 4, 5, 7, 8 are largely shared across all issues
- **Cross-sell always on pages 3 and 7** — Sprint Progression (p.3), Nutrients eBook (p.7)
- **Working lifter = the target identity** — every page addresses time-constrained professionals
- **Series numbering builds collection behaviour** — state it on every cover
- **Recovery section signals sophistication** — most fitness products skip it; TIMBR includes it

## Pitfalls
- Canva API cannot rename designs or edit text elements — use MCP or Canva UI for those
- Tab names with spaces in Sheets range strings must be wrapped in single quotes: `'Tab Name'!A1:I9`
- When appending rows to CHANGES, use `insertDataOption='INSERT_ROWS'` not overwrite
- `pdftotext` must be available on the VM (`apt install poppler-utils`) — confirmed working May 2026
