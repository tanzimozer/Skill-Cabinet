# TIMBR Workout Series — Canva Design Registry

## Design IDs (as of May 26, 2026)

| Issue | Canva Design ID | Pages |
|---|---|---|
| Workout Series: Glutes & Hamstring | DAHFfAiLO3E | 8 |
| Workout Series: Shoulder & Core | DAHKu7sMKdE | 8 |
| Workout Series: Quads & Calf | DAHKuy17o8s | 8 |
| Workout Series: Chest & Tricep | DAHKuyPqxww | 8 |
| Workout Series: Back & Bicep | DAHKu6XleTQ | 8 |

Also present: `Copy of Blair_MAIN` (ID: DAHKj74VAvM, 24 pages) — Blair magazine draft.

## Standard 8-Page Template Structure

| Page | Section | Nature |
|---|---|---|
| 1 | Cover / Hero | Dynamic |
| 2 | TOC + Intro | Dynamic |
| 3 | The Program (exercise list) | Dynamic |
| 4 | Gyms in Seattle | Dynamic |
| 5 | Work & Corporate Life | Dynamic |
| 6 | Recovery Guide (Zone 1 + 2) | Dynamic |
| 7 | Nutrition / Macro-Micro CTA | Static |
| 8 | Subscribe / Outro | Static |

**~50% of each issue is shared/static content.** Pages 4–6 (Seattle, Corporate Life, Recovery) use near-identical copy across all 5 issues — only muscle-group-specific references change. Pages 7–8 are completely identical.

## PDF Text Extraction Method

Canva API cannot return text content from designs. Use export → extract:

```python
import requests, time, subprocess

creds = json.load(open('/home/hermes/.hermes/.canva_credentials'))
headers = {'Authorization': f'Bearer {creds["access_token"]}', 'Content-Type': 'application/json'}

# 1. Request export
r = requests.post('https://api.canva.com/rest/v1/exports',
    json={"design_id": DESIGN_ID, "format": {"type": "pdf", "export_quality": "regular"}},
    headers=headers)
job_id = r.json()['job']['id']

# 2. Poll (usually completes in first 3s poll)
for _ in range(15):
    time.sleep(3)
    r = requests.get(f'https://api.canva.com/rest/v1/exports/{job_id}', headers=headers)
    if r.json()['job']['status'] == 'success':
        pdf_url = r.json()['job']['urls'][0]
        break

# 3. Download
pdf = requests.get(pdf_url).content
open(f'/tmp/canva_{job_id}.pdf', 'wb').write(pdf)

# 4. Extract text
result = subprocess.run(['pdftotext', f'/tmp/canva_{job_id}.pdf', '-'], capture_output=True, text=True)
text = result.stdout
```

## Magazine Production Google Sheet

All 5 issues are mapped in:
- **Sheet:** Magazine Production
- **Sheet ID:** `1J4Rv-_NInf_jtjOHNYhTvVEfel0LK_uCfjjozshB2Ew`
- **URL:** https://docs.google.com/spreadsheets/d/1J4Rv-_NInf_jtjOHNYhTvVEfel0LK_uCfjjozshB2Ew/edit

Columns per tab: Page | Section | Content | Design Pattern | Notes/Action | Page Nature | Purpose | Underlying Principle | Content Creation Questions (5)

## Content Production Principles Extracted

1. **Working lifter framing** is the core audience identity — use across all issues
2. **Anti-Instagram positioning** is explicit: "Real strength, real shape — not the ones that look impressive on Instagram"
3. **Cross-sell placement:** Always on Page 3 (program page) — reader is most engaged here
4. **Nutrition page is intentionally thin** — it's a funnel door to timbr.fit, not a chapter
5. **Subscribe CTA at the back** captures reader at peak trust (just finished the product)
6. **Recovery uses HR zones** (Zone 1 <60%, Zone 2 60-70%) — signals coaching sophistication
7. **Seattle identity page** doubles as brand philosophy — TIMBR origin story embedded every issue
