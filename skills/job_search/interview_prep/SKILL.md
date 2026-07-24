---
name: interview_prep
category: job_search
description: Generate structured interview prep briefs for Tanzim from JOB_HAMMER sheet data + Gmail calendar confirms
---

# Interview Prep Skill

## Purpose
Pull all relevant interview intel from JOB_HAMMER Google Sheet + Gmail and format a clean brief for Tanzim before any scheduled interview.

## Data Sources
- **JOB_HAMMER Sheet ID:** `12FTPE1jSvrzdBeQ5Sjwiv8ccNVEbw7tTWJNdtDkrLZ0`
- **Sheet URL:** https://docs.google.com/spreadsheets/d/12FTPE1jSvrzdBeQ5Sjwiv8ccNVEbw7tTWJNdtDkrLZ0/edit
- **Google Token:** `/home/hermes/.hermes/google_token.json`
- **Google Client Secret:** `/home/hermes/.hermes/google_client_secret.json`

## Sheet Structure (MASTER_TAB)
| Col | Field |
|-----|-------|
| A | RESUME_PDF |
| B | SCORE |
| C | COMPANY |
| D | TITLE |
| E | SALARY |
| F | LOCATION |
| G | REMOTE |
| H | JD (full job description) |
| I | NOTES |
| J | APPLIED |
| K | CALLBACK |

Date tabs (e.g. `Jul 11`) contain daily crawl snapshots — check these if MASTER_TAB is missing a posting date.

## Steps
1. Scan Gmail for confirmed interviews (search: `interview after:YYYY/MM/DD`)
   - **CRITICAL: Use direct Python + googleapiclient, NOT the `gmail` subagent toolset.**
   - The `gmail` subagent toolset hits a demo account (emails addressed to "Alex" at alex@example.com). Every result it returns is fake. Never use it.
   - Use: `python3` script with creds at `~/.hermes/google_token.json` and the Gmail REST API directly.
   - See `references/gmail-python-pattern.md` for working boilerplate, or `timbr_dataset/scripts/google_api_boilerplate.py` for the full reusable helper set.
2. If no Gmail match: fall back to email content Tanzim has shared in-chat (screenshot, paste) — that is the PRIMARY source. An email screenshot from Tanzim supersedes any inbox scan.
3. Extract company name from email subject/snippet
4. Search MASTER_TAB col C for matching company → get full row
   - Also use direct Python + Sheets API for this. Same creds. Same reason.
5. Search Google Drive for matching resume PDF (`name contains 'CompanyName'`)
6. Format and send brief (see template below)

## Output Template

```
*INTERVIEW PREP — [COMPANY NAME]*
📅 [Date] · [Time] [Timezone]
👤 [Interviewer Name & Title]
📞 Format: [Google Meet / Phone / Zoom] — [duration]

---
*JOB_HAMMER*
- Tab: MASTER_TAB · Row [N]
- Match score: [SCORE]/100

*Resume PDF:* [Drive link]
*Cover letter:* [Drive link if exists]

---
*COMPANY*
[Company name] — [1-line what they do]
Parent: [if applicable]
Location: [location]
Remote: [Yes/No/Hybrid]

*THE ROLE*
[Title] — reporting to [manager if known]
[2-3 sentence summary of what the role does]

*WHY THEY WANT YOU*
[Bullet the key things from JD that map to Tanzim's background]

*WHAT THEY EXPECT*
[Bullet the core requirements]

*INTERVIEW PROCESS*
[From JD — list the rounds]

*THIS ROUND*
[What this specific round covers — culture fit / technical / etc.]

*JOB LINK*
[URL if found, else 'Not in sheet']

*Posted:* [Date if known]
```

## Notes
- BrightHire = AI recorded — flag this so Tanzim knows
- If salary blank in sheet, note as "Not listed"
- Score < 70 = flag it ("69/100 — worth knowing")
- Always check if round 1 is just a Talent Advisor screen vs technical
- **JOB_HAMMER APPLIED column may say "No" even when a callback exists** — the sheet lags behind reality. Don't treat it as ground truth; trust the email.
- **Interview may not be confirmed yet** — Dan Murphy (Complete Fence, Jul 8 2026) sent an invite-to-book via calendar link, not a confirmed time. Treat "please book via my link" as pending, not confirmed.
