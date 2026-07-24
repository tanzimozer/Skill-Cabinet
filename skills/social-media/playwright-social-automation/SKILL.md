---
name: playwright-social-automation
description: Browser automation for social media platforms using Playwright — scraping, bulk actions (unfollow, like, DM), with atomicity, resumability, and bot-detection evasion.
tags: [playwright, instagram, automation, scraping, browser, social-media]
---

# Playwright Social Media Automation

## When to Use
- User wants to scrape followers/following/engagement data from a social platform
- User wants to bulk-act (unfollow, like, comment, DM) based on scraped data
- Task requires crash-safe, resumable execution with state persistence
- Any browser automation against Instagram, TikTok, LinkedIn, etc. (no official API or API is too limited)

## Core Architecture (3-Phase Pattern)

Always structure social automation in 3 atomic phases:

1. **Scrape** — collect and save all data locally (JSON) before acting
2. **Cross-match / compute** — pure logic, no network, generate action list
3. **Act** — execute actions one at a time with progress saved after each

This prevents partial-state corruption and makes every run resumable.

## Atomicity Guarantee

```python
def save_json(path, data):
    """Atomic write — prevents corrupt files on crash."""
    tmp = path.with_suffix(".tmp")
    with open(tmp, "w") as f:
        json.dump(data, f, indent=2)
    tmp.rename(path)  # atomic rename on POSIX

# Save progress after EVERY single action
progress["unfollowed"].append(username)
save_progress(progress)  # then wait, then next action
```

Resume logic: on startup, load progress file and skip already-completed items.

## Playwright Setup

### Install (system Python)
```bash
pip install --break-system-packages playwright
playwright install chromium
```

### Install pitfall
The Hermes venv (`~/.hermes/hermes-agent/venv`) does NOT have Playwright. Install to system Python with `--break-system-packages`, then run with `python3` (not the venv python). Confirm: `pip3 show playwright`

### Launch pattern
```python
browser = p.chromium.launch(
    headless=False,   # visible by default — user can see what's happening
    slow_mo=50,       # humanizes timing slightly
    args=["--no-sandbox"]
)
context = browser.new_context(
    viewport={"width": 1280, "height": 800},
    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 ..."
)
```

### Manual login pattern (preferred over storing credentials)
```python
page.goto("https://www.instagram.com/accounts/login/")
print("Log in manually, then press ENTER...")
input()  # user logs in, script resumes
```

## Bot Detection Evasion

- **playwright-stealth:** install with `pip install playwright-stealth`, apply with `stealth_sync(page)` immediately after `context.new_page()`. Makes Playwright undetectable to most bot fingerprinting. Import pattern:
  ```python
  try:
      from playwright_stealth import stealth_sync
      STEALTH_AVAILABLE = True
  except ImportError:
      STEALTH_AVAILABLE = False
  # ...after page = context.new_page():
  if STEALTH_AVAILABLE:
      stealth_sync(page)
  ```
- **Between individual actions:** `random.uniform(8, 20)` seconds
- **Scroll delays:** `random.uniform(0.8, 2.0)` seconds  
- **Page load delays:** `random.uniform(1.5, 3.5)` seconds
- **Batch size:** keep to 50-100 actions per session
- **Human-like UA string:** set via browser context, not launch args
- Never run headless for Instagram — increases detection risk

## Instagram-Specific Notes

### Scraping followers/following
- Navigate to `/{username}/followers/` — a `div[role='dialog']` appears
- Scroll inside the dialog, not the page: `dialog.querySelector("ul").scrollTop = scrollHeight`
- Collect `a[href^='/']` anchors where `href.count('/') == 2` → username format
- Detect end-of-list by tracking count across 3 consecutive scrolls with no change

### Unfollowing
- Navigate to profile page, find `button` with text "Following" or "Requested"
- Click → wait for confirmation dialog (`button:has-text('Unfollow')`) → click
- Some accounts skip the dialog — wrap confirmation in try/except with 3s timeout
- If no "Following" button found, treat as already-unfollowed (success, not error)

## Script Flags Pattern
```
--username    Instagram handle (required)
--phase       1|2|3 — jump to specific phase (default: 1)
--batch-size  Max actions per run (default: 50)
--dry-run     Preview without acting
--force       Re-scrape even if data exists
--headless    Hide browser window
```

## File Layout
```
./ig_data/
  followers.json       # Phase 1 output
  following.json       # Phase 1 output
  unfollow_list.json   # Phase 2 output — review before Phase 3
  progress.json        # Phase 3 state — survives crashes
  run.log              # timestamped action log
```

## Delivering the Script to a Third Party via WhatsApp
When Tanzim asks to send the script to someone else in a group:
- Include `MEDIA:/absolute/path/to/file` in the message body to deliver as a WhatsApp attachment
- If the bridge throws a `jidDecode` / 500 error on the group send, the group JID is likely malformed or the bridge doesn't have it registered — fall back to telling Tanzim to forward manually
- Always include the full setup + usage guide in the same message so the recipient has everything without needing to ask

## Pitfalls
- **Playwright not in venv:** always install to system pip3 with --break-system-packages
- **playwright install chromium** times out in constrained environments — run separately, expect 2-3 min
- **Instagram dialog vs page scroll:** scrolling the page body does nothing inside the followers modal
- **Rate limiting:** Instagram will soft-ban if you unfollow >100/day. Keep batches small.
- **"Following" button text varies:** check for both "Following" and "Requested" (pending follow requests)
- **Atomic write matters:** a plain `json.dump()` that crashes mid-write leaves a corrupt file — always use tmp+rename pattern
