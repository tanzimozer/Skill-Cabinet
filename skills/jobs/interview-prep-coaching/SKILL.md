---
name: interview-prep-coaching
description: "Prep Tanzim for a scheduled job interview: locate the interview, cross-check it against the Job Hammer tracking sheet, backfill the JD, build a focused prep sheet, and run live one-at-a-time stress-test drills with honest grading."
version: 1.0.0
platforms: [linux]
metadata:
  hermes:
    tags: [jobs, interview, coaching, tanzim, prep]
---

## Interview Prep & Coaching

Downstream of the job CRAWLERS (see `terrajob-crawler` for sourcing/resume generation).
This skill is what to do once an interview is actually scheduled: find it, verify it
against the tracking sheet, fill gaps, and coach Tanzim through it.

### Standard flow
1. **Find the interview.** Check Google Calendar first (often empty), then Gmail.
   Calendar-invite emails carry the When/time + the join link (Zoom or MS Teams).
   Useful Gmail queries: `interview newer_than:Nd`, `zoom interview`, `"June DD" interview`,
   `from:<recruiter> <company>`. Pull: date/time + timezone, interviewer name & title,
   platform + meeting ID/passcode/link.
2. **Cross-check the Job Hammer sheet.** Sheet ID `12FTPE1jSvrzdBeQ5Sjwiv8ccNVEbw7tTWJNdtDkrLZ0`,
   tab `MASTER_TAB`. Columns: `RESUME_PDF, SCORE, COMPANY, TITLE, SALARY, LOCATION, REMOTE, JD, NOTES, APPLIED, CALLBACK`.
   Search ALL dated tabs, not just MASTER_TAB, when asked to "cross-check the full sheet."
   **Name-collision trap:** "Allen Institute" (biosciences, the real interview) vs
   "Ai2 / Allen Institute *for AI*" (OlmoEarth roles) are DIFFERENT employers that share a name —
   never conflate. Same caution for "Booz Allen Hamilton." Report distinct entities separately.
3. **Find the resume in Drive.** The `RESUME_PDF` cell names the file; resolve it to a Drive
   link via `drive.files().list(q="name contains '<stem>'")`. Confirm there isn't a second
   variant before assuming the named one is current.
4. **Backfill the JD if the cell is empty.** Pull the full posting (LinkedIn job view, etc.),
   condense to a tight JD block, and write it to the JD column cell (e.g. `MASTER_TAB!H<row>`,
   `valueInputOption=RAW`). Verify the write by reading the row back. Flag the gap to Tanzim
   before doing it; he'll usually say yes.
5. **Build the prep sheet** — see `references/prep-sheet-and-drills.md`.
6. **Run the stress-test drills** — one question at a time, honest grading, his words back.

### OAuth
All Google ops use `~/.hermes/google_token.json` (OAuth, has calendar + gmail + sheets + drive
scopes). No service account on this machine. Build credentials via `google.oauth2.credentials.Credentials`,
refresh if `not creds.valid`, write the refreshed token back.

### References
- `references/prep-sheet-and-drills.md` — prep-sheet structure, the resume-vs-JD gap analysis
  method, and Tanzim's drill format + coaching style (one question at a time, stress-test, grade hard).

### Tanzim's coaching preferences (learned, durable)
- **One question at a time.** He explicitly asks to be stress-tested one-at-a-time so each answer
  gets pushed before moving on. Never dump all questions at once.
- **Grade honestly, then tighten.** Call out vague phrasing, dropped tool names, missed "why it
  matters" beats. Don't soften it.
- **Make him say it back in his own words** after every model answer — don't let him just read yours.
- When he asks "how should I answer that?" or "propose a full answer," GIVE the full first-person
  script (ready to deliver), then still make him repeat it back.
- Watch for speech-to-text mangling in his practice replies (e.g. "Ella tracking" → "SLA tracking",
  "Gia Sana" → "JIRA/Asana"). Note the fix, don't grade him down for the transcription.
