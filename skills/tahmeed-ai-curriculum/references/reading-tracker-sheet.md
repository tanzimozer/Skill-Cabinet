# Reading Tahmeed's Tracker / Profile Sheets — Reliable Method

## The problem
The browser tools (`browser_navigate`, `browser_snapshot`, `browser_vision`) frequently
hang/timeout on the live Google Sheets editor — it's too heavy for the session browser.
Confirmed Jun 2026 on the Anthropic-Academy progress tracker sheet.

## The fix — CSV export
If the sheet is **link-shared** ("Anyone with the link can view"), pull any tab
directly as CSV. No browser, no auth, instant:

```bash
curl -sL "https://docs.google.com/spreadsheets/d/<SHEET_ID>/export?format=csv&gid=<GID>" -o /tmp/sheet.csv
head -50 /tmp/sheet.csv
```

- `<SHEET_ID>` is in the URL between `/d/` and `/edit`.
- `<GID>` is the tab id — in the URL after `gid=`. Loop over candidate gids if unsure;
  the wrong one returns an HTML login/error blob instead of clean CSV.
- A **clean CSV** starts with the header row. An **HTML blob** (`<!DOCTYPE html>...`)
  means either the sheet is still private OR you hit the wrong gid.

## If it returns a sign-in HTML wall
The sheet is private. Ask Tanzim to set it to "Anyone with the link can view" and
re-pull. Don't fight the browser — it's the slow path and usually hangs anyway.

## No Google API creds on this box
There's no gcloud / Google API credentials installed. You cannot create or write into
a Google Doc/Sheet programmatically from `execute_code`. Creating Docs requires either
the browser (logged-in Google session) or the user doing it. State this plainly rather
than promising a Doc you can't produce. Offer alternatives: hand the user formatted text
to paste, or publish content as a standalone web page / markdown file with a link.
