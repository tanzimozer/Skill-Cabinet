# SETUP — for Claude running on Tanzim's Mac

You are Claude, operating on Tanzim's Mac. Your job: get `instagrammer-lite`
running locally so the crawler fires on a WhatsApp keyword. Everything below is
self-contained. Follow it top to bottom.

## What this is
Two files:
- `crawler.py` — logs in with Tanzim's real Instagram cookies, opens a target
  account's followers modal, scrolls it, scrapes every handle. Chains handles as
  next targets (depth-limited). Appends to `out/handles.csv`. No filtering — that
  is a later, separate stage.
- `listener.py` — watches the WhatsApp group. On a message matching
  `crawl @handle [depth=N]`, it runs `crawler.py` locally and replies when done.

**Must run on the Mac, not a server.** Instagram blocks datacenter IPs; it trusts
Tanzim's home connection + logged-in cookies. Do not attempt to run it remotely.

## Step 1 — Environment
```bash
cd ~/instagrammer-lite
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
playwright install chromium
```

## Step 2 — Instagram cookies (the one thing that actually matters)
The crawler needs a live logged-in session. Two options:

**A. Reuse the old ones if they exist and are still valid:**
```bash
ls ~/.instagrammer/secrets/ig_cookies.json 2>/dev/null && \
  cp ~/.instagrammer/secrets/ig_cookies.json ~/instagrammer-lite/secrets/ig_cookies.json && \
  echo "copied old cookies — will verify in Step 4"
```

**B. Export fresh** (if the old ones are gone or return 401): from a browser
logged into Instagram as Tanzim, export cookies for `instagram.com` as a JSON
array and save to `secrets/ig_cookies.json`. Use the template in
`secrets/ig_cookies.template.json` for the required shape. The critical cookies
are `sessionid`, `ds_user_id`, and `csrftoken`.

## Step 3 — Listener config
Copy the template and fill it in:
```bash
cp listener_config.template.json listener_config.json
```
Fields:
- `bridge_url` / `bridge_token` — the WhatsApp bridge this chat runs on. If you
  cannot determine these, run the crawler directly (Step 4) and skip the listener
  until Tanzim provides them.
- `chat_id` — the WhatsApp group ID that should control the crawler.
- `allow_senders` — already set to Tanzim's ID (`160799431606497@lid`). Leave it.

## Step 4 — Verify the crawler works (do this before the listener)
```bash
source venv/bin/activate
python crawler.py tanzim_ozer --depth 1 --max 200 --headful
```
Watch the browser open, log in via cookies, open followers, scroll, and collect.
Then confirm output:
```bash
head out/handles.csv && wc -l out/handles.csv
```
If it fails with a login wall or the followers modal never opens → cookies are
dead. Redo Step 2B with fresh cookies. Check `logs/crawler.log` for detail.

## Step 5 — Start the listener
```bash
source venv/bin/activate
python listener.py
```
Leave it running (or wrap it in a launchd job for persistence — see Step 6).
It now watches the WhatsApp group. Anyone allow-listed typing `crawl @handle`
fires a run. Tanzim typing it and Friday typing it are identical to the machine.

## Step 6 — (Optional) Keep it alive across reboots
Create `~/Library/LaunchAgents/com.tanzim.instagrammer-lite.listener.plist`
pointing at `venv/bin/python listener.py`, then:
```bash
launchctl load ~/Library/LaunchAgents/com.tanzim.instagrammer-lite.listener.plist
```

## Report back to Tanzim
When done, tell him: (1) cookies reused or freshly exported, (2) crawler test
result — how many handles pulled, (3) listener running yes/no, (4) any blocker.

## Trigger reference
In the WhatsApp group:
```
crawl @tanzim_ozer
crawl @somebigfitnessaccount depth=2
```
Output: `out/handles.csv` — columns: handle, source, collected_at.
