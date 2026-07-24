---
name: contact-enrichment
category: data
description: Enriching contact lists (Google Sheets or CSV) with social profiles, LinkedIn URLs, company data, and other third-party signals. Cross-matching names and emails against public sources.
triggers:
  - "find their LinkedIn"
  - "cross-match contacts"
  - "add LinkedIn column"
  - "enrich the sheet"
  - "look up profiles"
  - "find profiles for these contacts"
---

# Contact Enrichment

## When to use
Any task that involves taking a list of names/emails and finding additional data — LinkedIn profiles, company info, titles, social handles — and writing results back to a Google Sheet or file.

## Approach

### 1. Pull the sheet first
Always read the sheet before starting — confirm column structure, total row count, and what's already populated.

```python
sheets.spreadsheets().values().get(spreadsheetId=SHEET_ID, range='A1:Z100').execute()
```

### 2. LinkedIn — choose the right method

**The VM IP is CAPTCHAd by Google, DuckDuckGo, and Bing.** Headless Playwright from this server hits rate limits immediately. Do NOT attempt:
- `site:linkedin.com/in` Google search via Playwright or requests
- DuckDuckGo — returns 418 from the VM IP
- Raw Bing requests — no LinkedIn URLs in response

**Viable options (pick one, confirm with Tanzim before spending):**

| Option | Cost | Quality | Setup |
|---|---|---|---|
| **SerpAPI** | ~$50/mo | ✅ Excellent | API key → `SERPAPI_KEY` env var |
| **Apollo.io API** | Freemium | ✅ Professional contacts | API key |
| **Hunter.io** | Freemium | ✅ Email + profile | API key |
| **PhantomBuster** | ~$59/mo | ✅ LinkedIn native | LinkedIn session cookie |
| **Manual** | Free | ⚠️ Slow | Export names, Tanzim pastes back |

If no API key is available, tell Tanzim the options and costs before starting. Don't burn time on approaches that will CAPTCHA out.

### 3. SerpAPI pattern (when available)

```python
import requests

def find_linkedin_serpapi(name, email, api_key):
    r = requests.get('https://serpapi.com/search', params={
        'engine': 'google',
        'q': f'site:linkedin.com/in "{name}"',
        'api_key': api_key,
        'num': 3,
    })
    data = r.json()
    for result in data.get('organic_results', []):
        link = result.get('link', '')
        if 'linkedin.com/in/' in link:
            return link.split('?')[0].rstrip('/')
    return 'NOT FOUND'
```

### 4. Write results back to sheet

Add header first, then batch-write the column:
```python
# Header
sheets.spreadsheets().values().update(
    spreadsheetId=SHEET_ID, range='E1',
    valueInputOption='RAW', body={'values': [['LinkedIn']]}
).execute()

# Data
sheets.spreadsheets().values().update(
    spreadsheetId=SHEET_ID, range=f'E2:E{1+len(results)}',
    valueInputOption='RAW', body={'values': [[r] for r in results]}
).execute()
```

### 5. Verify URLs before writing
Don't assume a found URL is live. LinkedIn returns 200 even for deleted profiles (redirects to login). Real verification requires authenticated session — flag 'UNVERIFIED' if you can't confirm.

## Pitfalls
- **Google/DDG/Bing CAPTCHA the VM IP** — do not attempt headless search scraping, it wastes time
- LinkedIn requires login for any people search — direct API calls without session cookie always redirect
- `execute_code` sandbox lacks requests/playwright — use `~/.hermes/hermes-agent/venv/bin/python3` via `terminal`
- Always confirm API cost with Tanzim before setting up a paid service

## PIIX Sheet
- Sheet ID: `1VD_hkS81x8lKcgK412I4Apk-icoGuJISoQbWfuY6zok`
- 57 contacts (as of June 2026)
- Columns: Serial, Name, Phone, Email → LinkedIn (col E, to be added)
