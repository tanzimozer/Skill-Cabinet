---
name: ig-churn
description: Running the ig-churn Instagram follow/unfollow automation for Tanzim on the Hermes VM. Covers setup, cookie injection, audit, and unfollow phases.
tags: [instagram, automation, playwright, nodejs]
---

# ig-churn — Instagram Follow/Unfollow Automation

## Repo
`github.com/tanzimozer/ig-churn` — cloned to `~/ig-churn` on Hermes VM.

## Setup (one-time per environment)
```bash
cd ~/ig-churn/Sub-Folder
npm install          # installs playwright ^1.47.0
```

Node v20 is available at `/usr/bin/node`. Playwright chromium is bundled via npm.

## Critical patches needed
1. **Headless mode** — the scripts default to `headless: false` (requires a display). VM has no display. Patch before running:
```bash
sed -i 's/headless: false/headless: true/g' ~/ig-churn/Sub-Folder/ig-audit.js
sed -i 's/headless: false/headless: true/g' ~/ig-churn/Sub-Folder/ig-unfollow.js
```

2. **config.json** — must exist before running audit:
```bash
echo '{"username": "tanzim.ozer"}' > ~/ig-churn/Sub-Folder/config.json
```

## Session Cookie Injection

Instagram session cookies expire — need a fresh export each time.

### Getting cookies from Tanzim
1. Tanzim opens `instagram.com` in Chrome (actively logged in, scroll feed first)
2. Opens Cookie-Editor extension → Export as JSON
3. Pastes JSON here — must contain `domain: ".instagram.com"` entries

### Injecting cookies
Write `inject_cookies.js` into `~/ig-churn/Sub-Folder/` and run from that directory:

```javascript
const { chromium } = require('playwright');
const path = require('path');
const PROFILE_DIR = path.join(__dirname, 'ig-profile');

// Convert Cookie-Editor JSON format to Playwright format
// Key fields: name, value, domain, path, expires (not expirationDate), httpOnly, secure, sameSite
// sameSite must be "Strict" | "Lax" | "None" (not "no_restriction" — convert that to "None")

(async () => {
    const ctx = await chromium.launchPersistentContext(PROFILE_DIR, { headless: true, userAgent: UA });
    await ctx.addCookies(cookies);  // array of converted cookies
    const page = await ctx.newPage();
    await page.goto('https://www.instagram.com/', { waitUntil: 'domcontentloaded', timeout: 20000 });
    await page.waitForTimeout(3000);
    const isLoggedIn = !page.url().includes('/accounts/login');
    console.log('Logged in:', isLoggedIn);
    await ctx.close();
    process.exit(isLoggedIn ? 0 : 1);
})();
```

**Run from Sub-Folder:**
```bash
cd ~/ig-churn/Sub-Folder && node inject_cookies.js
```

**Common failure:** `sessionid` already expired server-side → get fresh cookies from Tanzim.

## Running the Audit
```bash
cd ~/ig-churn/Sub-Folder && node ig-audit.js
```
Produces `reports/followers_YYYY-MM-DD.csv`. Takes ~10 minutes. Must be <24h old before running unfollow.

## Running the Unfollow (Phase 2)
```bash
# Dry run first
cd ~/ig-churn/Sub-Folder && node ig-unfollow.js --dry

# Live run
cd ~/ig-churn/Sub-Folder && node ig-unfollow.js
```

3-gate preflight runs before any live action. Any gate failure = exit code 99, zero unfollows.

## Safety rules (Tanzim's requirements)
- **Zero followers must be unfollowed** — only non-followers
- `whitelist.txt` = handles never to unfollow, edit before running
- Max-speed mode: 90-action bursts, 3-min breaks, no daily cap
- Mutual auto-whitelist: anyone in the latest followers snapshot is protected

## Tanzim's Instagram
- Handle: `tanzim.ozer`
- User ID: `40730017115`
