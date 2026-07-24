# Dual-Tab Crawl Output Pattern — Jun 2026 Case Study

## Situation
IG-1 Protocol crawlers (batch + live API + HTML scraping) needed to output results to a Google Sheet. Initial approach created one tab per crawl run (e.g., `Crawl-20260605-142041`), which quickly cluttered the sheet.

**User correction:** Master list should be populated on every crawl (cumulative), AND a dated tab (e.g., "Jun 05") should also be populated with the same run's results. Both tabs in parallel.

## Solution Implemented

**Dual-tab architecture:**
1. **Results tab** — Master cumulative list. Append only. Contains all results from all crawl runs. Row ID / Run ID column distinguishes runs.
2. **Dated tab** — Date-keyed snapshot (one per calendar day). Created fresh or cleared if exists. Receives same data as Results.

**Implementation across three crawlers:**

### ig1_batch_crawler.py
```python
run_id = datetime.now().strftime('%Y%m%d-%H%M%S')
date_tab = datetime.now().strftime('%b %d').lstrip('0')  # 'Jun 05'

results_ws = ig1_sheet.worksheet('Results')

try:
    dated_ws = ig1_sheet.add_worksheet(title=date_tab, rows=5000, cols=11)
except:
    dated_ws = ig1_sheet.worksheet(date_tab)
    dated_ws.clear()

headers = ['Username', 'Full Name', 'Followers', 'Female Score', 'Business Score',
           'Bio Preview', 'Is Business', 'Source', 'Status', 'Crawled At', 'Run ID']
dated_ws.append_row(headers)

# Process results...
for result in results:
    row = [result['username'], result['full_name'], result['follower_count'],
           round(result['female_score'], 2), round(result['business_score'], 2),
           result['biography'][:40], 'Yes' if result['is_business'] else 'No',
           'consolidated', 'analyzed', datetime.now().isoformat(), run_id]
    results_ws.append_row(row)  # Master
    dated_ws.append_row(row)    # Daily
```

### ig1_live_crawler.py & ig1_live_crawler_html.py
Same pattern — Results master + dated snapshot tab, both populated simultaneously.

## Benefits

1. **Master Results tab** — Single source for all historical crawl data. Filter by Run ID to isolate specific runs.
2. **Dated tab** — Daily rollup without needing to filter master (useful for quick daily review).
3. **Run ID column** — Distinguishes multiple runs within the same date (e.g., morning vs. evening crawl).
4. **Clean sheet structure** — No tab explosion. Matches Job Tracker / Job Hammer pattern.

## Key Implementation Details

**Date format:** `datetime.now().strftime('%b %d').lstrip('0')`
- Produces "Jun 05", "Dec 25", etc.
- `.lstrip('0')` removes leading zero from single-digit days
- "Jun 5" not "Jun 05" (matches user's format preference)

**Tab creation/clear pattern:**
```python
try:
    dated_ws = sheet.add_worksheet(title=date_tab, rows=500, cols=11)
except:  # Already exists
    dated_ws = sheet.worksheet(date_tab)
    dated_ws.clear()  # Overwrite previous runs same day
```
Do NOT delete and recreate — that loses headers. Use `.clear()` to reset.

**Simultaneous append:**
```python
results_ws.append_row(row)  # Results (cumulative)
dated_ws.append_row(row)    # Dated (daily snapshot)
```
Single loop, append to both tabs per result.

## Pitfalls & Mitigations

1. **Forgot to clear dated tab before rerunning mid-day**
   - Results in duplicate rows in dated tab if script runs twice
   - Mitigation: Always call `dated_ws.clear()` after getting worksheet if tab exists

2. **Tab name clash** — What if user had a tab named "Jun 05" for something else?
   - Current approach: create/clear without asking
   - Mitigation: Add a one-line header like "# Crawl Results — Jun 5" to distinguish from user tabs
   - Or: Use `Crawl-Jun05` format to namespace explicitly

3. **Run ID column position** — If someone sorts the sheet, Run ID will move
   - Current: Run ID is last column (11)
   - Mitigation: Pin the first 2–3 columns in Google Sheets UI, or document the column order in the sheet's header row comment

## Results

- **IG-1 Protocol v2.1** deployed with dual-tab architecture
- All three crawlers unified on same output pattern
- Sheet stays clean (no per-run tabs; just Results + dated tabs)
- Ready for scaling to 8 cities + Estonia with consistent structure

## Future Enhancements

1. **Consolidation across dates:** Pivot Results tab by date range to build weekly/monthly reports
2. **Pattern analysis:** Cross-tabulate Run ID with female/business scores to track filter effectiveness over time
3. **Alert on anomalies:** If a dated tab has 0 results but same crawl normally returns 50+, flag for investigation
