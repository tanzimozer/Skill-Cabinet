# Browser Timeout Fallback Patterns

## Session Context
Jun 2026: Browser tools (Google Search, career pages) timed out repeatedly on Fluxx job posting lookup. `curl` with grepped patterns succeeded where headless navigation failed.

## Pattern: When Browser Navigation Times Out

**Do NOT retry the same tool endlessly.** If `browser_navigate` times out at 60s:

1. **For job posting pages (Greenhouse, LinkedIn, company careers):**
   ```bash
   curl -sL "https://url" 2>&1 | grep -i "implementation\|specialist\|title" | head -20
   curl -sL "https://careers-page" | grep -oP '<a[^>]*href="[^"]*job[^"]*"[^>]*>[^<]*</a>'
   ```
   This works for HTML-based pages. JavaScript-heavy pages (LinkedIn, modern job boards) won't yield structured data.

2. **For company main pages:**
   ```bash
   curl -sL "https://fluxx.io" 2>&1 | grep -i "job\|career\|hire"
   curl -sL "https://company.com" | grep -oP 'href="[^"]*careers[^"]*"'
   ```
   Look for navigation links to careers subpages.

3. **For Greenhouse-hosted boards:**
   ```bash
   curl -s "https://boards.greenhouse.io/companyname"
   ```
   Often returns empty with curl (JS-rendered), but static job URLs may be present in HTML.

4. **Fallback: Email source of truth**
   If curl and browser both fail, check Gmail for original application/confirmation emails from recruiting. They often contain job details, salary, interview format, interviewer names.

## When Email Search Succeeds Better Than Web Search

- Original posting emails may have been sent 2-4 weeks prior to interview round
- Search pattern: `gmail.users().messages().list(q='[company]')`
- Extract URLs from email body and interviewer details from thread
- Company email headers contain recruiter contact info for clarification

## Known Limitations

- LinkedIn job boards block curl/scripted access (returns partial HTML)
- Greenhouse boards may be JS-rendered, requiring headless browser
- Company careers pages may 302-redirect or require JS
- Job postings may be archived/removed between application and interview date

## Recommendation

**For Tanzim's interview prep workflow:**
1. Always search email first (fastest, contains historical context)
2. If not in email, search job sheets and trackers (Drive, Sheets)
3. Only then attempt web access (browser → curl → give up)
4. Ask user directly if none of the above yield the posting
