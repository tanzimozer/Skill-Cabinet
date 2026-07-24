# TURRO Unfollow Engine — Build Reference (Jul 2026)

## Repo
`github.com/tanzimozer/Turro` → `unfollow_engine/` directory
Committed: `28390b9` (Jul 2026)

## File structure
```
turro/unfollow_engine/
├── main.py          # entry point, argparse (--dry-run, --limit N)
├── sheet_reader.py  # Google Sheets → list of handles
├── unfollower.py    # Playwright browser loop
├── logger.py        # CSV session log + stdout
├── config.py        # all tunables
└── requirements.txt
```

## config.py tunables
- `SHEET_ID` = `1ZmyV2nBq5uoql7WD9hxr7q6nM1ofT8nyJ8Q1C45Z4pc`
- `SHEET_TAB` = `"TANZIM"`
- `NON_FOLLOWER_COL` = `2` (0-indexed → column C)
- `HEADER_ROW` = `0`
- `PULSE_SECONDS` = `3`
- `CHROME_USER_DATA` = `/Users/tanzimozer/Library/Application Support/Google/Chrome`
- `CHROME_PROFILE` = `"Default"`
- `BTN_FOLLOWING` = `"button:has-text('Following')"`
- `BTN_UNFOLLOW_CFM` = `"button:has-text('Unfollow')"`

## TANZIM tab schema (as of Jul 2026)
- Row 0: `FOLLOWERS | FOLLOWING | NON-FOLLOWERS` (header)
- Rows 1–1500: data
- Col A = followers, Col B = following, Col C = non-followers
- 1,080 active non-followers (2 `__deleted__` entries skipped)

## Playwright launch pattern — Chrome profile inheritance
```python
browser = p.chromium.launch_persistent_context(
    user_data_dir="/Users/tanzimozer/Library/Application Support/Google/Chrome",
    channel="chrome",   # system Chrome, NOT bundled Chromium
    headless=False,
    args=[
        "--profile-directory=Default",
        "--disable-blink-features=AutomationControlled",
    ],
    viewport={"width": 1280, "height": 900},
)
page = browser.new_page()
```
This inherits the user's full logged-in Chrome session — no cookies or credentials needed in code.

## Sanity check on launch
```python
page.goto("https://www.instagram.com/", timeout=15_000)
time.sleep(2)
if "login" in page.url:
    # not logged in — stop
```

## Unfollow click flow per handle
1. `page.goto(f"https://www.instagram.com/{handle}/", wait_until="domcontentloaded")`
2. `time.sleep(1.5)` — let page settle
3. Check for 404: `page.locator("text=Sorry, this page isn't available").count()`
4. `page.locator("button:has-text('Following')").first` — check `is_visible(timeout=6_000)`
5. `.click()` → `time.sleep(0.8)`
6. `page.locator("button:has-text('Unfollow')").first` → `wait_for(state="visible")` → `.click()`
7. `time.sleep(PULSE_SECONDS)` (3s)

## Block detection
```python
if any(k in page.url for k in ["challenge", "checkpoint", "suspended"]):
    # Meta blocker — stop engine immediately
```

## Logger format
`timestamp,handle,result,note` CSV — appended per action.
Results enum: `UNFOLLOWED | SKIPPED | NOT_FOUND | BLOCKED | ERROR`

## Mac setup commands
```bash
pip install playwright
playwright install chromium
cd /path/to/turro/unfollow_engine
python main.py --dry-run           # verify handles load
python main.py --limit 10          # test first 10
python main.py                     # full run
```

## Known IG selector risk
Instagram DOM changes silently. If `button:has-text('Following')` stops matching:
- Open DevTools on a profile page → inspect the Following button
- Common fallback: `[aria-label*="Following"]` or `span:has-text('Following')` inside a button
- The confirm modal button text has historically been "Unfollow" — check if IG added punctuation or changed capitalisation

## Session context
Built Jul 2026 as part of TURRO Project 2 (unfollow engine). Uses Mac-local execution
(device-fingerprint requirement), Google OAuth for sheet reads, no IG account credentials in code.
