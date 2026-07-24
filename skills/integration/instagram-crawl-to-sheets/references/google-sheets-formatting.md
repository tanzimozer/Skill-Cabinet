# Google Sheets Formatting Preferences

User-specified formatting standards for all crawl output to Google Sheets.

## Cell Formatting (MANDATORY)

All cells in output tabs must have:
- **Horizontal alignment:** CENTER
- **Vertical alignment:** MIDDLE
- **Text wrap:** ON (enabled)

This applies to all data rows and headers. Apply via batchUpdate request:

```python
format_request = {
    "requests": [
        {
            "repeatCell": {
                "range": {
                    "sheetId": sheet_id,
                    "startRowIndex": 0,
                    "endRowIndex": num_rows,
                    "startColumnIndex": 0,
                    "endColumnIndex": num_cols
                },
                "cell": {
                    "userEnteredFormat": {
                        "horizontalAlignment": "CENTER",
                        "verticalAlignment": "MIDDLE",
                        "wrapStrategy": "WRAP"
                    }
                },
                "fields": "userEnteredFormat(horizontalAlignment,verticalAlignment,wrapStrategy)"
            }
        }
    ]
}
```

## Column Structure (Instagram Crawl)

Exact order and hyperlink rules:

1. **Username** — HYPERLINKED to Instagram profile (`=HYPERLINK("https://instagram.com/{username}","{username}")`)
2. **Followers** — Integer count extracted from bio
3. **Following** — Integer count extracted from bio
4. **Crawled_at** — ISO date string (YYYY-MM-DD format)

**Do NOT include:**
- Bio text
- Method (e.g., "HTML scraper")
- Status field
- follower_approx column
- Any other metadata

## Tab Naming Conventions

- **Format:** 3-letter month + space + zero-padded day (e.g., "Jun 05", not "Jun 5" or "June 05")
- **Same-day crawls:** Populate the existing dated tab, do not create new versions
- **Example progression:** "Jun 05", "Jun 06", "Jun 07" (one tab per calendar day, never "Jun 05 v2")

## Default Behavior

When writing to Google Sheets:
1. Check if dated tab exists (by date)
2. If not, create it
3. Deduplicate against existing usernames in column A
4. Write new rows starting from row 2 (header at row 1)
5. Apply formatting to all cells (no exceptions)
6. Hyperlink usernames automatically

User expectation: **every Google Sheets write should be properly formatted and structured without requiring additional requests.**
