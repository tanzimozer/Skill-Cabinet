---
name: dogfood
description: "Exploratory QA of web apps: find bugs, evidence, reports."
version: 1.0.0
metadata:
  hermes:
    tags: [qa, testing, browser, web, dogfood]
    related_skills: []
---

# Dogfood: Systematic Web Application QA Testing

## Overview

This skill guides you through systematic exploratory QA testing of web applications using the browser toolset. You will navigate the application, interact with elements, capture evidence of issues, and produce a structured bug report.

## Prerequisites

- Browser toolset must be available (`browser_navigate`, `browser_snapshot`, `browser_click`, `browser_type`, `browser_vision`, `browser_console`, `browser_scroll`, `browser_back`, `browser_press`)
- A target URL and testing scope from the user

## Inputs

The user provides:
1. **Target URL** — the entry point for testing
2. **Scope** — what areas/features to focus on (or "full site" for comprehensive testing)
3. **Output directory** (optional) — where to save screenshots and the report (default: `./dogfood-output`)

## Workflow

Follow this 5-phase systematic workflow:

### Phase 1: Plan

1. Create the output directory structure:
   ```
   {output_dir}/
   ├── screenshots/       # Evidence screenshots
   └── report.md          # Final report (generated in Phase 5)
   ```
2. Identify the testing scope based on user input.
3. Build a rough sitemap by planning which pages and features to test:
   - Landing/home page
   - Navigation links (header, footer, sidebar)
   - Key user flows (sign up, login, search, checkout, etc.)
   - Forms and interactive elements
   - Edge cases (empty states, error pages, 404s)

### Phase 2: Explore

For each page or feature in your plan:

1. **Navigate** to the page:
   ```
   browser_navigate(url="https://example.com/page")
   ```

2. **Take a snapshot** to understand the DOM structure:
   ```
   browser_snapshot()
   ```

3. **Check the console** for JavaScript errors:
   ```
   browser_console(clear=true)
   ```
   Do this after every navigation and after every significant interaction. Silent JS errors are high-value findings.

4. **Take an annotated screenshot** to visually assess the page and identify interactive elements:
   ```
   browser_vision(question="Describe the page layout, identify any visual issues, broken elements, or accessibility concerns", annotate=true)
   ```
   The `annotate=true` flag overlays numbered `[N]` labels on interactive elements. Each `[N]` maps to ref `@eN` for subsequent browser commands.

5. **Test interactive elements** systematically:
   - Click buttons and links: `browser_click(ref="@eN")`
   - Fill forms: `browser_type(ref="@eN", text="test input")`
   - Test keyboard navigation: `browser_press(key="Tab")`, `browser_press(key="Enter")`
   - Scroll through content: `browser_scroll(direction="down")`
   - Test form validation with invalid inputs
   - Test empty submissions

6. **After each interaction**, check for:
   - Console errors: `browser_console()`
   - Visual changes: `browser_vision(question="What changed after the interaction?")`
   - Expected vs actual behavior

### Phase 3: Collect Evidence

For every issue found:

1. **Take a screenshot** showing the issue:
   ```
   browser_vision(question="Capture and describe the issue visible on this page", annotate=false)
   ```
   Save the `screenshot_path` from the response — you will reference it in the report.

2. **Record the details**:
   - URL where the issue occurs
   - Steps to reproduce
   - Expected behavior
   - Actual behavior
   - Console errors (if any)
   - Screenshot path

3. **Classify the issue** using the issue taxonomy (see `references/issue-taxonomy.md`):
   - Severity: Critical / High / Medium / Low
   - Category: Functional / Visual / Accessibility / Console / UX / Content

### Phase 4: Categorize

1. Review all collected issues.
2. De-duplicate — merge issues that are the same bug manifesting in different places.
3. Assign final severity and category to each issue.
4. Sort by severity (Critical first, then High, Medium, Low).
5. Count issues by severity and category for the executive summary.

### Phase 5: Report

Generate the final report using the template at `templates/dogfood-report-template.md`.

The report must include:
1. **Executive summary** with total issue count, breakdown by severity, and testing scope
2. **Per-issue sections** with:
   - Issue number and title
   - Severity and category badges
   - URL where observed
   - Description of the issue
   - Steps to reproduce
   - Expected vs actual behavior
   - Screenshot references (use `MEDIA:<screenshot_path>` for inline images)
   - Console errors if relevant
3. **Summary table** of all issues
4. **Testing notes** — what was tested, what was not, any blockers

Save the report to `{output_dir}/report.md`.

## Tools Reference

| Tool | Purpose |
|------|---------|
| `browser_navigate` | Go to a URL |
| `browser_snapshot` | Get DOM text snapshot (accessibility tree) |
| `browser_click` | Click an element by ref (`@eN`) or text |
| `browser_type` | Type into an input field |
| `browser_scroll` | Scroll up/down on the page |
| `browser_back` | Go back in browser history |
| `browser_press` | Press a keyboard key |
| `browser_vision` | Screenshot + AI analysis; use `annotate=true` for element labels |
| `browser_console` | Get JS console output and errors |

## Tips

- **Always check `browser_console()` after navigating and after significant interactions.** Silent JS errors are among the most valuable findings.
- **Use `annotate=true` with `browser_vision`** when you need to reason about interactive element positions or when the snapshot refs are unclear.
- **Test with both valid and invalid inputs** — form validation bugs are common.
- **Scroll through long pages** — content below the fold may have rendering issues.
- **Test navigation flows** — click through multi-step processes end-to-end.
- **Check responsive behavior** by noting any layout issues visible in screenshots.
- **Don't forget edge cases**: empty states, very long text, special characters, rapid clicking.
- When reporting screenshots to the user, include `MEDIA:<screenshot_path>` so they can see the evidence inline.

## Audit → PM Board Sync Pattern

When audit results need to be synced to a Trello (or similar) board:

1. Fetch all cards across ALL lists before creating new ones — duplicates accumulate across In-Progress/To-Do/Backlog
2. Distinguish real failures from false positives before touching the board:
   - Static HTTP 404 ≠ page broken on Wix (lightboxes, JS-rendered pages, slug mismatches)
   - Confirm with the site owner before archiving "done" cards
3. Archive false positives (misclassified as issues): `trello PUT /cards/{id} {closed: true}`
4. Mark genuinely done items with `dueComplete: true` (the green circle) — not just a label
5. Create new issue cards in **To-Do**, not In-Progress — In-Progress implies someone is actively working it
6. Card descriptions must be executable: exact nav path, numbered steps, verification step, time estimate

## Completion % Scoring Pattern

When asked "what % is the site done?", score across these dimensions:

- **Core pages live** (homepage, shop, booking, services, legal) — ~30%
- **Content quality** (no placeholder/template text, real copy, real products) — ~25%
- **SEO/Social** (OG title, description, image set correctly) — ~10%
- **Transactional flows** (checkout, booking, contact form end-to-end) — ~20%
- **Polish** (404 branded, staff profiles, email consistency, PageSpeed) — ~15%

State what's passing and failing per dimension, then give an overall score. Be honest — placeholder content or empty pages count as not done even if the page loads.

## Lightweight Visual Audit Pattern (screenshot + vision, no browser toolset)

When the full browser toolset (`browser_navigate`, `browser_vision`, etc.) is unavailable, use Playwright + `mcp_vision_analyze` for a fast visual pass:

```python
from playwright.sync_api import sync_playwright
import time

p = sync_playwright().start()
b = p.chromium.launch(executable_path='/snap/bin/chromium', args=['--no-sandbox','--disable-dev-shm-usage'])
page = b.new_page(viewport={'width':1280,'height':900})
page.goto(url, wait_until='domcontentloaded', timeout=35000)
time.sleep(7)
page.screenshot(path='/tmp/page_shot.png', full_page=True)
b.close(); p.stop()
```

Then pass to vision analysis. **Pitfall:** full-page screenshots of long pages exceed the 8000px image dimension limit. Resize first:

```python
from PIL import Image
img = Image.open('/tmp/page_shot.png')
w, h = img.size
if h > 4000:
    ratio = 4000 / h
    img = img.resize((int(w*ratio), 4000), Image.LANCZOS)
img.save('/tmp/page_shot_s.jpg', 'JPEG', quality=85)
```

This workflow is good for: fast customer-facing visual triage, generating Trello cards from findings, checking multiple pages in one pass. It does NOT catch JS console errors or test interactive flows — use the full browser toolset for those.

## Wix Site Auditing (pitfall discovered 2026-05-06)

Wix sites are fully JS-rendered — plain HTTP fetches return empty shells or password gates even when the site is live. Always use Playwright headless Chromium with a `time.sleep(6-8)` after `domcontentloaded` to let Wix hydrate.

On this server (ARM64 Linux), Chrome for Testing does not have ARM builds. Use the system Chromium snap instead:
```python
browser = p.chromium.launch(
    executable_path='/snap/bin/chromium',
    args=['--no-sandbox', '--disable-dev-shm-usage']
)
```

Common Wix URL pitfalls:
- `/shop`, `/book-online`, `/contact` — these are Wix page slugs that must be explicitly published in the Wix editor. They 404 if the page exists in the editor but is not published or the slug is wrong.
- `/terms-of-use`, `/refund-policy` — Wix auto-generates these only if you enable them under Settings > Policy Pages. A footer link can exist while the page itself 404s.
- `/privacy-policy` — usually published by default but still protected if site is in password/coming-soon mode.
- The "password removed" state can take 1-2 minutes to propagate through Wix's CDN — re-run the audit if pages still show the Guest Area gate.
