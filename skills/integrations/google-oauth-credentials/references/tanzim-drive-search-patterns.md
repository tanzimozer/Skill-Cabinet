# Drive Search & Sheets Access Patterns (Tanzim Environment)

## Credential File Locations (Verified)

```
~/.hermes/google_token.json          ← PRIMARY (unencrypted, use first)
~/.hermes/.edith/vault.enc           ← Secondary (encrypted, avoid in agent code)
~/.hermes/.edith/services.map.enc    ← Encrypted mapping (avoid)
```

Token file format:
```json
{
  "token": "ya29.a...",
  "refresh_token": "1//06J...",
  "token_uri": "https://oauth2.googleapis.com/token",
  "client_id": "313611152308-ffm0jsbfr95mnq3r19vd9246p51c01ct.apps.googleusercontent.com",
  "client_secret": "<GOOGLE_OAUTH_CLIENT_SECRET_REDACTED>",
  "scopes": [
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/documents"
  ],
  "type": "authorized_user",
  "expiry": "2026-06-15T18:53:26.437089"
}
```

## Key Job Tracking Sheets (Tanzim)

| Sheet Name | ID | Purpose |
|---|---|---|
| JOB_HAMMER | 12FTPE1jSvrzdBeQ5Sjwiv8ccNVEbw7tTWJNdtDkrLZ0 | Master job database, MASTER_TAB with columns: RESUME_PDF, SCORE, COMPANY, TITLE, SALARY, LOCATION, REMOTE, JD, NOTES, APPLIED |
| TERRAjob | 1vhK1ys152Rem0J6ygntEB9uyajz8trGi7JlmCLHLniI | Tailored resumes tracker (5 tabs: Master, 05/23, 05/24, 05/27, Scout_2026-06-01) |
| TerraJob Tailored Resumes Tracker | 1uEX-87Ko5Cd7m4tiytRwwFUPH1c6b4Up6UCtVvLLkq8 | Tracker sheet for tailored resume variants |
| TerraJob Tailored Resumes Folder | 1ceVMVopzB337290GdMJeCzlF64g4fVrM | Drive folder with 50+ tailored resume documents |
| FLUXJOB — Scouted Jobs | 17zj8k0bfJNZYdfZJpzT2UmeAhRCo28HHNj5velYKSXs | Auto-crawled job posting index |

## Search Pattern: Finding Company Data Across Multiple Sheets

When a company (e.g., Fluxx) isn't in the primary sheet, follow this sequence:

1. **Search JOB_HAMMER MASTER_TAB** for company name in all columns (A:Z)
2. **Search TERRAjob all tabs** (Master, date-named tabs, Scout tabs)
3. **Search TerraJob Resumes Tracker** for tailored variants associated with the company
4. **Search the Tailored Resumes folder** for resume documents with company name
5. **If not found in sheets**, fall back to email search (Gmail API) for original application/confirmation emails
6. **Then search the company website or job board** (Greenhouse, LinkedIn, etc.)

## Common Gotchas

- **Company name variations:** Search for partial matches (e.g., "fluxx" in lowercase within larger text strings)
- **Sheets may have 50+ items:** Don't assume first 10 tabs cover the data; iterate all tabs
- **Tailored resumes folder:** Contains 50+ documents but NOT organized by company — must search by name within folder
- **Job posting not in automation:** Often only in email or original job board; sheets track *applications* not *postings*
