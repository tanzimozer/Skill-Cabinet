---
name: job-tracker-sheets
description: "Look up a specific job listing in Tanzim's Google Sheets job trackers. Covers TERRAjob (TERRA system) and Job_Tracker (manual tracker). Knows the sheet structure, tab naming conventions, and how to find a specific company/role."
version: 1.0.0
tags: [google-sheets, job-search, tanzim, terra]
related_skills: [gmail-interview-search]
---

# Job Tracker Sheets Lookup

Tanzim maintains two active Google Sheets job trackers. When asked "where's [company] in my job tracker", check both.

## Known Sheets

| Sheet Name | Drive ID | Last Modified | Notes |
|---|---|---|---|
| **TERRAjob** | `1vhK1ys152Rem0J6ygntEB9uyajz8trGi7JlmCLHLniI` | 2026-05-28 | Auto-populated by TERRA crawler. Date-named tabs. |
| **Job_Tracker** | `1v6CY46PBfGyrde8uuMzPv1cETZrOiflUj_HY34SJC_Q` | 2026-05-21 | Manual + hybrid tracker. More tabs, richer data. |

Other sheets exist (Job Crawler, Career-Ops Tracker, Job Log, Data Job) but are older / less active.

## TERRAjob Structure

Tabs: `Master`, plus date-named daily tabs (`05/23`, `05/24`, `05/27`, etc.)

- **Master** — full deduplicated list of all jobs
- **Date tabs** — jobs processed/applied on that date, with resume filename (e.g. `23_Ozer_Tanzim_PlantPeople.pdf`)

Columns (0-indexed): `[resume_file, score, company, title, location, applied_flag, ?, ?, date_posted, ?, date_added, url, source]`

## Job_Tracker Structure

Tabs: `Master Tracker`, then date-named tabs by batch (`Sheet 9 APR 15`, `05/05`, `5/8`, `5/16`, `Interviews`, `Hot Companies`, etc.)

- **Master Tracker** — full list, columns: `[status, company, title, location, salary, score, source, date_posted, date_added, url]`
- **Date tabs** — batch of jobs pulled that day, similar structure
- **Interviews** tab — may track interview status separately

## Lookup Pattern

```python
from googleapiclient.discovery import build

sheets = build('sheets', 'v4', credentials=creds)

def search_sheet_for_company(sheet_id, company_name, role_keywords=None):
    meta = sheets.spreadsheets().get(spreadsheetId=sheet_id).execute()
    tab_names = [s['properties']['title'] for s in meta['sheets']]
    
    hits = []
    for tab in tab_names:
        result = sheets.spreadsheets().values().get(
            spreadsheetId=sheet_id, range=f"'{tab}'"
        ).execute()
        for i, row in enumerate(result.get('values', [])):
            row_str = ' '.join(str(c) for c in row).lower()
            if company_name.lower() in row_str:
                if role_keywords is None or any(kw.lower() in row_str for kw in role_keywords):
                    hits.append({'tab': tab, 'row': i+1, 'data': row})
    return hits
```

Search **both sheets** in parallel. Return the most specific hit — prefer a date-named tab (where a specific resume file is listed) over Master, as it confirms which application batch it belongs to.

## Reporting Format

When Tanzim asks "which tab/sheet is [role] in":

```
Sheet: Job_Tracker
Tab: 5/8 (row 5, entry #4)
Role: Operations Coordinator — Essex Property Trust
Salary: $24–$33/hr | Bellevue, WA
Source: Indeed
```

Short. Lead with sheet name + tab name — that's what he asked for. Include role title, company, and salary if present.

## Pitfalls

- **Essex Property Trust appears in multiple tabs** (Master Tracker rows 44 & 153, date tabs 5/8 and 5/16, and TERRAjob). When user asks "where is it", give the most specific / actionable one — the date tab where a resume PDF is listed, since that confirms the application went through.
- **Tab name case varies** — `5/8` not `05/08`. Match against what the sheet actually has.
- **Sheets API quota** — reading all tabs of both sheets = ~20-30 API calls. Fine for one-off lookups; don't loop this in a cron.
- **TERRAjob is auto-populated** — entries may appear before they're applied to. Check the `applied_flag` column (index 5) — `TRUE` means applied, empty/FALSE means not yet.
- **Google Calendar API** is NOT enabled in the GCP project (throws 403). Don't attempt to use it. Use Gmail `.ics` search as the calendar fallback.
