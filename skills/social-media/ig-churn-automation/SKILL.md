---
name: ig-churn-automation
description: Instagram follow/unfollow automation for Tanzim (@tanzim.ozer) using the ig-churn repo — audit followers, unfollow non-mutuals, protect whitelist.
---

# ig-churn Automation

## Repo
- GitHub: `github.com/tanzimozer/ig-churn` (private)
- Local VM: `~/ig-churn/` (clone if not present)
- Clone: `git clone https://github.com/tanzimozer/ig-churn.git ~/ig-churn`

## Stack
- Node v20 + Playwright (in `~/ig-churn/Sub-Folder/node_modules`)
- Install: `cd ~/ig-churn/Sub-Folder && npm install`

## Account
- Handle: `tanzim.ozer`
- User ID: `40730017115`
- Config file: `~/ig-churn/Sub-Folder/config.json` → `{ "username": "tanzim.ozer" }`

## Session cookie injection (required before every run)

Instagram session cookies expire frequently. Each new run needs fresh cookies from Tanzim.

**Ask Tanzim to:**
1. Open Chrome → go to instagram.com (logged in, scroll feed a bit)
2. Open Cookie-Editor extension → Export as JSON → paste here

**Inject via:** `~/ig-churn/Sub-Folder/inject_cookies.js`

Key cookies needed: `sessionid`, `csrftoken`, `ds_user_id`, `datr`, `ig_did`, `mid`, `rur`

Verify session worked:
```js
// inject_cookies.js checks page.url() — if not /accounts/login = success
node inject_cookies.js  // should print "Logged in: true"
```

## Headless patch (required for VM — no display)

The scripts default to `headless: false`. Patch before running:
```bash
sed -i 's/headless: false/headless: true/g' ~/ig-churn/Sub-Folder/ig-audit.js
sed -i 's/headless: false/headless: true/g' ~/ig-churn/Sub-Folder/ig-unfollow.js
```

## Phase 1 — Audit (build followers snapshot)

```bash
cd ~/ig-churn/Sub-Folder
echo "tanzim.ozer" | node ig-audit.js
```

- Takes ~10 minutes
- Output: `reports/followers_YYYY-MM-DD.csv`
- Must be <24h old before unfollow runs
- Script buffers all output — no live progress, prints at end

## Phase 2 — Unfollow

```bash
cd ~/ig-churn/Sub-Folder
node ig-unfollow.js
```

- Runs 3-gate preflight (halts on any failure)
- Protects everyone in latest followers CSV + whitelist.txt
- Burst mode: 90 actions → 3-min break → repeat until queue empty
- `--dry` flag for safe test run (no actual unfollows)
- `--verify` flag to check gates only

## Safety rules (from Tanzim)
- **Zero followers must be unfollowed** — only unfollow non-followers
- Whitelist.txt = accounts to never unfollow regardless

## Common failure modes

| Symptom | Cause | Fix |
|---|---|---|
| "SESSION EXPIRED" | sessionid cookie expired | Get fresh cookies from Tanzim |
| "Missing X server / $DISPLAY" | headless:false on VM | Run headless patch above |
| Script prompts for handle | config.json missing | Create `config.json` with username |
| Audit completes but no CSV | Still scraping (buffered) | Wait — output dumps at end |
| Cookies are Google not Instagram | Exported from wrong Chrome tab | Remind Tanzim to be on instagram.com tab, not Chrome Web Store or Google |
| Script hangs waiting for handle input | config.json missing, stdin not piped | Ensure config.json exists OR pipe: `echo "tanzim.ozer" \| node ig-audit.js` |

## File layout
```
~/ig-churn/Sub-Folder/
  ig-audit.js        # Phase 1 — build followers snapshot
  ig-unfollow.js     # Phase 2 — unfollow non-followers
  ig-follow.js       # Phase 1 follow (separate)
  inject_cookies.js  # Cookie injector (added by Friday)
  config.json        # { "username": "tanzim.ozer" }
  persona.json       # Filter rules, nano-range
  whitelist.txt      # Never-unfollow handles
  ig-profile/        # Playwright persistent browser profile
  reports/           # followers_YYYY-MM-DD.csv, unfollow-log.txt
```
