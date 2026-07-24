# Job Tracker Lookup Pattern

## Reliable workflow for finding interview details

**Step 1: Interviews tab (canonical source)**
- Sheet: `Job_Tracker` (ID: `1v6CY46PBfGyrde8uuMzPv1cETZrOiflUj_HY34SJC_Q`)
- Tab: **`Interviews`** (GID: `1499246630`)
- Structure: `[#, COMPANY, JOB TITLE, RESUME, JOB LINK, STATUS, INTERVIEW TYPE, DATE, ACTION, NOTES]`
- Search this tab first for any interview — it has everything in one row

**Step 2: Verify GID and tab name**
- When sending Tanzim a sheet link, **always verify** GID matches the actual tab via metadata call
- Do NOT assume: `gid=2001392048` without checking which tab it actually refers to
- Call `sheets_service.spreadsheets().get(spreadsheetId=...)` to get authoritative `sheetId` for each tab
- Build link as: `https://docs.google.com/spreadsheets/d/{SHEET_ID}/edit#gid={GID}`

**Step 3: Resume lookup**
- Resume filename is in the `RESUME` column (e.g. `10.pdf`, `3.pdf`)
- Search Google Drive by exact filename: `name='10.pdf'`
- Get `webViewLink` and `modifiedTime` to confirm correct version

**Step 4: Email confirmation**
- Cross-check with Gmail: `from:company_domain AND (interview OR invitation)`
- Extract: interviewer name, exact time (PT timezone), Zoom/call details, any prep instructions (e.g. STAR method)
- Mail emails are dated; always scan for the most recent message

**Step 5: Date filter (current session)**
- For today's interviews: filter Interviews tab by `DATE = '2026-06-16'` or similar
- Date format in sheet: `YYYY-MM-DD` or `MM/DD/YY` — check actual cell format

## Quick reference — key sheet IDs

| Sheet | ID | Purpose |
|-------|------|---------|
| Job_Tracker | `1v6CY46PBfGyrde8uuMzPv1cETZrOiflUj_HY34SJC_Q` | Master tracker (all applications + interview pipeline) |
| TERRAjob | `1vhK1ys152Rem0J6ygntEB9uyajz8trGi7JlmCLHLniI` | Detailed job listings and custom data |
| Interviews tab | GID `1499246630` | Current interview list (canonical) |

## Common pitfalls

1. **Assuming resume row = PDF number**: Check the actual cell value. Row 4 might contain `69.pdf`, not `4.pdf`.
2. **GID confusion**: A link with `#gid=2001392048` does NOT tell you which tab it is. Always look up metadata.
3. **Date format variance**: Some tabs use `MM/DD`, others use `YYYY-MM-DD`. Check the actual cell before filtering.
4. **Stale interview data**: Interviews tab may have old entries. Always cross-check with Gmail for confirmation.
5. **Missing entries**: If an interview isn't in the Interviews tab yet, check the daily date tabs (`5/8`, `05/27`, etc.) in Job_Tracker or the `jobs` tab.
