# Tracing a Live Interview Back to Its Job Hammer Source Row

When Tanzim asks "which Job Hammer tab/row did this interview come from" — or for
the source + company website for an upcoming interview — use this recipe. It is the
**read/lookup** side of Job Hammer (the SKILL.md covers the crawl/write side).

## Sheet identity (verified Jun 2026)

- **Live master spreadsheet:** `JOB_HAMMER` — ID `12FTPE1jSvrzdBeQ5Sjwiv8ccNVEbw7tTWJNdtDkrLZ0`
  - Drive lookup: `drive.files().list(q="name contains 'JOB_HAMMER'")` returns it as
    a `application/vnd.google-apps.spreadsheet`.
- **STALE — do not use:** an older sheet titled `TERRAjob`
  (ID `1vhK1ys152Rem0J6ygntEB9uyajz8trGi7JlmCLHLniI`). Its only tab is `_MIGRATED`
  containing the single line *"Migrated to JOB_HAMMER MASTER_TAB on 2026-06-16."*
  Several skill references and old configs still point at this ID — ignore them and
  go to `JOB_HAMMER`.

## Tab structure

- `RESEARCH`, `MASTER_TAB`, `Manual Entry`, then one **dated tab per crawl day**
  (`Jun 03`, `Jun 05`, … `Jun 28`).
- `MASTER_TAB` is the deduped roll-up; each dated tab is the raw crawl for that day.
- A job typically appears **twice**: once in `MASTER_TAB` and once in the dated tab
  where it was first crawled. Report both (e.g. "MASTER_TAB row 124, origin Jun 08 row 9").

## Column schema (MASTER_TAB / dated tabs)

`RESUME_PDF | SCORE | COMPANY | TITLE | SALARY | LOCATION | REMOTE | JD | NOTES | APPLIED | CALLBACK`

- `APPLIED` = TRUE/FALSE — confirms whether Tanzim actually applied.
- `RESUME_PDF` = the exact tailored resume filename used (e.g. `Tanzim_EmphasysSoftware.pdf`).
- `SCORE` = the filter-pipeline score (see SKILL.md F1–F11).

## Lookup recipe

1. Resolve the spreadsheet ID via Drive (don't hardcode a stale ID).
2. `spreadsheets.get` to list tab titles.
3. `values.batchGet` across **all** tabs with range `'<tab>'!A1:Z300`.
4. Match rows by company keyword in any cell (lowercased join), then read
   COMPANY / TITLE / APPLIED / RESUME_PDF / SCORE by header index — **do not print
   the whole row** (see JD gotcha).

## Gotchas

- **Bloated JD cells.** The `JD` column holds the entire job description (thousands of
  chars, escaped newlines/markdown). A naive `print(row)` floods output and can blow
  past tool limits. Always select specific columns by header index and truncate JD to
  ~120 chars. Map headers → indices once, then pull only COMPANY/TITLE/APPLIED/etc.

- **Recruiter name ≠ hiring company.** The Gmail interview thread is often from an
  external agency, while Job Hammer indexes the **end employer**. You must alias before
  matching. Confirmed mappings (Jun 2026):
  - **Aquila / TalentMinded (recruiter Kainaz Prasan)** → indexed as **"Emphasys Software"**
    (Emphasys HFA is the product; Aquila is a group within Constellation Software Inc.).
    Title: *Technical Implementation Specialist*. MASTER_TAB row 124, origin Jun 08 row 9.
  - **HousingWire / HW Media (recruiter Jamie Bridges, @hwmedia.com)** → indexed as
    **"HousingWire"**. Title: *Customer Success Specialist*. Jun 16 tab, row 136.
  - Cross-check by **title** + **resume filename** when the company name doesn't match.

- **Not every interview is in Job Hammer.** Cold/inbound outreach (e.g. unnamed
  "internship" mills) and some async OnDemand interviews (Coldwell Banker via ModernHire,
  Crossover Markets via Criteria) never came through the crawl — a keyword search returns
  zero rows. State that plainly rather than forcing a false match.

## Cross-referencing the live interview set

To answer "what are my upcoming interviews," triangulate three sources — they disagree:
1. **Gmail** — search `interview (schedule OR confirmed OR invitation OR zoom OR teams
   OR meet) newer_than:21d`. Surfaces confirmations + recruiter threads.
2. **Google Calendar** — `events.list(timeMin=now)`. The ground truth for *accepted*
   slots. Note: a Gmail invite flagged "unknown sender" is **not** auto-added to the
   calendar (e.g. the Aquila Jul 6 invite sat unaccepted).
3. **Job Hammer sheet** — for the source row, score, resume used, applied status.

Watch for passed-but-recent threads (Fluxx Jun 16, HousingWire Jun 23, Allen Institute
Jun 25) masquerading as "upcoming" — check the date, not just the subject line.
