---
name: instagram-crawl-to-sheets
description: Automated Instagram profile crawling via HTML scraper with deduplication, quality checks, and Google Sheets integration using dated tabs
aliases:
  - ig-crawl
  - ig-protocol
  - instagram-pipeline
triggers:
  - User asks to crawl Instagram profiles and export data
  - User requests bulk Instagram data collection
  - User needs deduplication + quality checks on crawl results
  - User wants automated dated Google Sheets integration
---

# Instagram Crawl to Google Sheets Pipeline

Automated workflow to scrape Instagram profiles (via HTML, bypassing API rate limits), deduplicate results, run quality checks, and write clean data to dated Google Sheets tabs with proper formatting.

## Core Pattern

**Three-stage pipeline:**
1. **HTML Crawler** — BeautifulSoup-based scraper (targets 50 profiles per run, ~1.2 sec per profile, ~60 sec total)
2. **Deduplication + Quality Check** — compare incoming data against existing sheet records, remove duplicates, validate data integrity
3. **Write to Dated Tab** — auto-create/populate tab named by date (e.g., "Jun 05"), format cells (centered, middle, text wrap), hyperlink usernames

## Why HTML Scraper?

Instagram API returns HTTP 429 (rate-limited) for bulk profile requests. HTML parsing:
- ✅ No API detection risk
- ✅ Bypasses rate limits entirely
- ✅ Sufficient for public profile data (username, bio, follower counts)
- ❌ Cannot access user's own follower/following lists (Instagram blocks this, even with cookies)

**Backup:** Residential proxy ($5–20/month) restores full API speed if HTML scraper proves insufficient for future use cases.

## Implementation Details

### Authentication
- **Instagram session:** Store cookies at `~/.hermes/.ig_cookies.json` (600 perms, owner read/write only)
- **Google Sheets OAuth:** Store tokens at `~/.hermes/google_token.json` (from OAuth client credentials)
- **Never transmit credentials** — keep locally, revoke via browser logout if needed

### Crawler Script (run_html_crawler.py)
- Targets 50 profiles per batch
- Uses BeautifulSoup to parse HTML directly
- Extracts: username, followers (from bio), following (from bio), crawl timestamp
- Outputs: `/tmp/ig1_html_crawl_results.json`
- **Timing:** ~1 minute per 50-profile batch

### Sheet Writer Script (write_to_sheets.py)

**Three responsibilities:**

#### 1. Deduplication
- Query existing tab for usernames (column A)
- Compare incoming batch against sheet records
- Skip any duplicates (log with ⚠️ for visibility)
- New profiles only → written to sheet

#### 2. Quality Check
- Validate followers field (reject empty/invalid entries)
- Count valid rows vs. duplicates vs. invalid records
- Calculate **quality score** (0–100):
  - Base: % of valid rows
  - Penalty: -0.5 per duplicate detected
  - Flag if score < 70 (warning: review before publishing)
- Report: total rows, valid rows, duplicates removed, invalid followers, quality score

#### 3. Sheet Write + Format
- **Dated tab naming:** Auto-create tab named by current date (e.g., "Jun 05")
- **Same-day multiple crawls:** Append/replace rows in the same tab (no new versions)
- **Columns (in order):**
  - Username (hyperlinked to Instagram profile)
  - Followers (count)
  - Following (count)
  - Crawled_at (ISO date)
- **NO columns:** bio, method, status, follower_approx (removed per user preference)
- **Cell formatting (all cells):**
  - Horizontal alignment: CENTER
  - Vertical alignment: MIDDLE
  - Text wrap: ON

### Full Pipeline Command

```bash
source ~/.hermes/ig-venv/bin/activate && cd /home/hermes/.hermes/ig-1-protocol-repo && python3 << 'EOF'
import subprocess
from datetime import datetime

# Step 1: Crawl
subprocess.run(['python3', 'run_html_crawler.py'])

# Step 2: Dedupe + QC + Write
subprocess.run(['python3', 'write_to_sheets.py'])
EOF
```

## User Preferences (EMBEDDED)

- **Dated tabs only.** Every crawl writes to a single date-based tab (e.g., "Jun 05"). Multiple crawls on the same day populate the same tab, never create new versions.
- **No duplicates in output.** Deduplication is mandatory, not optional. Older instances removed in favor of newer.
- **Quality checks on every crawl.** QC report printed to console. Score < 70 triggers warning but does not block write.
- **Cell formatting is default.** All Google Sheets writes apply: centered, middle, text wrap, without needing explicit request.
- **Hyperlinked usernames.** Username column is always clickable links to Instagram profiles.
- **Minimal columns.** Only: Username (linked), Followers, Following, Crawled_at. No bio, method, or status columns.

## Common Workflows

### Run a single 50-profile crawl
```bash
cd /home/hermes/.hermes/ig-1-protocol-repo && source ~/.hermes/ig-venv/bin/activate && python3 write_to_sheets.py
```

### Check for duplicates before running
Query the date tab and scan column A for existing usernames.

### Rerun the same batch (intentional)
The deduplication system will skip all 50 if they're already present. If you want to refresh data for the same profiles, manually delete rows or create a new batch.

## Troubleshooting

### HTTP 429 (rate limited)
- Expected if using Instagram API directly (not HTML scraper). HTML scraper should never see this.
- If it does: Instagram may have changed page structure. Inspect HTML, update BeautifulSoup selectors.

### Missing followers/following data
- Instagram bio may not include counts for some profiles. Marked as "TBD" in output.
- Quality check flags these as `invalid_followers` but still writes them (reviewer decision to filter).

### Google Sheets write fails
- Verify OAuth token is current (expires after ~1 year, needs refresh).
- Check sheet ID matches `SHEET_ID` variable in script.
- Ensure Google Sheets API is enabled in Google Cloud Console.

### Duplicate detection not working
- Verify tab name matches format (e.g., "Jun 05" with space and zero-padded day).
- Check that existing usernames are in column A, row 2 onwards (header in row 1).

## Reporting style with Tanzim (EMBEDDED — hard rule)

When running crawls/enrichment for Tanzim, **report results in 1–3 lines, not
analysis dumps.** He pushed back mid-session — "you are dumping a lot of information
at me" — after a run report that stacked headline numbers, per-tab breakdowns,
interpretation, and a next-steps menu. Do NOT do that. For a completed run:

- Lead with the outcome in one line (e.g. "202 handles → Jul 04 tab, hyperlinked").
- Add at most the one fact that changes his decision.
- End with a single clean choice ("keep running, or stop here?") — not a menu.

Hold the deeper read/interpretation UNLESS he asks for it. He drives; you don't pitch.
The rich detail belongs in the reference files, not in the chat.

## References
- See `references/sheet-triggered-playwright-architecture.md` for the Bulldozer
  pattern: sheet-Commands-tab trigger channel, vault-token writes, Playwright+cookies
  crawler, live `web_profile_info` band-prune, provider-gated chaining, and the
  selector/handle pitfalls hit this session.
- See `references/ig-1-protocol-setup.md` for initial credential setup
- See `templates/write_to_sheets.py` for current implementation
- See `scripts/validate_sheet_auth.py` for OAuth token validation

## Session Notes
- **First deploy:** June 5, 2026 — HTML crawler working, 50/50 success rate, dedup system tested and working
- **Quality check threshold:** 70/100 (configurable)
- **Batch size:** 50 profiles (configurable, adjust in run_html_crawler.py)
