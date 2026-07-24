# TURRO Unfollow Engine — Design Reference

Built: 2026-07-13. Engine 2 inside Project TURRO (sits alongside the follower crawler).

## Purpose
Automate unfollowing non-followers from Tanzim's Instagram account via browser automation.
No API access — headless browser only, inheriting the live Chrome session.

## Key constraint: no credential handling
Playwright launches against **Tanzim's real local Chrome profile**, inheriting his
logged-in Instagram session. Zero credentials in code. Profile path:
`/Users/tanzimozer/Library/Application Support/Google/Chrome/Default`

## Stack
- **Python + Playwright** (not Selenium — faster, async, native Chromium, better on Mac)
- Reads from Google Sheet (Project TURRO, TANZIM tab, col C)
- Runs locally on Mac (same IP/fingerprint constraint as the crawler)

## Source data — TANZIM tab confirmed schema
Sheet ID: `1ZmyV2nBq5uoql7WD9hxr7q6nM1ofT8nyJ8Q1C45Z4pc`
Tab: `TANZIM`
Total rows: 1,501 (1 header + 1,500 data rows)
Columns: `FOLLOWERS | FOLLOWING | NON-FOLLOWERS`
- Col A = accounts that follow Tanzim
- Col B = accounts Tanzim follows
- Col C = **NON-FOLLOWERS** (he follows them, they don't follow back) → unfollow targets

Active non-follower handles: ~1,080 (as of 2026-07-12)
Deleted accounts: ~2 (prefixed `__deleted__`) — skip these
Header row 1: skip in all reads

## Execution flow
1. `sheet_reader.py` — pull col C from TANZIM tab, skip row 1 (header), skip `__deleted__` entries
2. Playwright launches Chrome at local profile path → navigates to `instagram.com/{handle}`
3. Locate "Following" button → click → confirm "Unfollow" on modal
4. Log result: `handle | unfollowed / already-not-following / blocked / error | timestamp`
5. Sleep 3s → next handle

## Pulse / rate
- **3 second gap** between unfollows (Tanzim's spec: run until Meta blocks, no daily cap)
- No hard daily ceiling — run until throttled/blocked, log the block state

## File structure (inside TURRO repo at ~/Turro)
```
unfollow_engine/
  main.py           ← entry point (--dry-run, --limit flags)
  sheet_reader.py   ← pulls col C from TANZIM tab
  unfollower.py     ← Playwright browser logic
  logger.py         ← session log CSV (handle / result / timestamp)
  config.py         ← Chrome profile path, sheet ID, pulse delay
  setup.sh          ← one-command Mac setup
  secrets/
    google_token.json   (gitignored)
    google_oauth.json   (gitignored)
  CLAUDE_CODE_SETUP.md  ← self-contained instructions for Claude Code on Mac
```

## Headless toggle
Default: **`headless=False`** — browser is visible on first run so Tanzim can confirm it's clicking correctly. Flip to `True` in `unfollower.py` once confirmed working.

## Modal handling
Instagram shows a confirmation modal after clicking "Following" → "Unfollow".
Script must:
1. Click "Following" button
2. Wait for modal
3. Click "Unfollow" confirm button
4. Catch: block screen, rate-limit modal, "User not found" — log and continue

## Pitfalls
- Instagram button selectors change frequently — build with fallback selectors and a screenshot-on-fail
- "Already not following" is a valid state (handle may have been removed between sheet generation and run) — log and skip, don't error
- Private accounts may render the button differently — handle gracefully
- If Instagram shows a "Try Again Later" interstitial, stop the run and log — don't retry into a block
- Do NOT run this on a server IP — same fingerprint constraint as the crawler (Mac only, home IP)

## Portable credentials pattern (built 2026-07-13)
`sheet_reader.py` must work on BOTH the Hermes server and Tanzim's Mac.
The pattern that works:

```python
_HERE    = os.path.dirname(os.path.abspath(__file__))
_SECRETS = os.path.join(_HERE, "secrets")

def _resolve(filename, fallback):
    local = os.path.join(_SECRETS, filename)
    return local if os.path.exists(local) else os.path.expanduser(fallback)

TOKEN_PATH = _resolve("google_token.json",  "~/.hermes/google_token.json")
OAUTH_PATH = _resolve("google_oauth.json",  "~/.hermes/GOOGLE_OAUTH_ACTIVE.json")
```

- `secrets/` folder sits inside `unfollow_engine/` — .gitignored
- On Mac: drop `google_token.json` + `google_oauth.json` into `secrets/`
- On Hermes server: `secrets/` is empty, falls back to `~/.hermes/` paths automatically
- `google_oauth.json` on Mac is a minimal file: `{"client_id": "...", "client_secret": "..."}`
- ig-venv path guard: `if os.path.exists(VENV_SITE) and VENV_SITE not in sys.path` — safe on Mac where the venv doesn't exist

## Mac setup — always ship a setup.sh (built 2026-07-13)
Always ship a `setup.sh` with Mac-targeting engines. It removes ALL manual steps.
One command does everything: installs Playwright browsers, copies credentials, runs dry-run to confirm.

When the user says "write a script for Claude to build it, Claude has access" — that means build and commit a setup script, not give a list of paste steps.

Rule: prefer a setup script over instructing the user to run 3-4 manual commands.

## Claude Code handoff pattern (locked 2026-07-13)
When Tanzim says "Claude has terminal access on my Mac" and needs setup done there,
write a self-contained instruction doc (`CLAUDE_CODE_SETUP.md`) in the repo and
tell him to paste one line into Claude Code:

```
Read ~/Turro/unfollow_engine/CLAUDE_CODE_SETUP.md and execute everything in it.
```

The doc must:
- Be completely self-contained (no "see README" references)
- List steps as numbered bash commands Claude can execute directly
- Include expected output so Claude can verify success
- End with "report back" instructions so Tanzim gets a result summary
- Include all context: repo path, credentials source, expected output, what NOT to do

**Pitfall**: If the repo isn't cloned yet on the Mac, the file won't exist.
Fix: embed the full instructions directly in the prompt instead:
```
Clone https://github.com/tanzimozer/Turro.git into ~/Turro, then: [full steps inline]
```

## Copy-paste delivery rule (locked 2026-07-13)
When giving Tanzim commands or code to run, send each copyable block as its own
separate message — no surrounding explanation mixed in. He copies directly from chat
and filters nothing. One block per message.

If bridge is down, use isolated inline code blocks with blank lines between — never
embed copy-paste content inside prose on the same line.

Do NOT send a numbered list of commands in one message. Each command = its own block/message.
