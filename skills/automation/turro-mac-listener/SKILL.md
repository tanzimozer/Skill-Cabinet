---
name: turro-mac-listener
description: Setup and operation of the TURRO local Flask listener on Tanzim's Mac Mini — the control plane for IG read/scrape jobs. Covers first-run setup, start/stop, health check, and the TURRO five-step setup checklist.
---

# TURRO — Mac Listener (Step 5)

## What it is
A Flask HTTP listener running on Tanzim's Mac Mini at `~/Desktop/Friday/TURRO/`. It receives scrape job commands from Friday and fires them against the IG burner cookie pool. Port **5055**, secret `turro-secret-2026`.

## Location
```
~/Desktop/Friday/TURRO/
├── venv/               # Python 3.9 virtualenv (flask, requests)
├── listener.py         # Main Flask app
└── cookies/            # Cookie files (live: seattle.gym, timbr.us)
```

## Start the listener
```bash
cd ~/Desktop/Friday/TURRO && source venv/bin/activate && python3 listener.py
```
**Leave the Terminal window open** — closing it kills the process. It is NOT daemonised.

## Endpoints
- `GET /health` — returns `{"status": "live", "service": "TURRO listener"}`
- `POST /read` — body `{"secret": "turro-secret-2026", "handle": "<ig_handle>"}` — queues a read job

## Check if running
```bash
ps aux | grep listener.py
```
If the only result is the grep itself → not running. Start it.

## Mac details
- **User:** tanzimozer
- **Host:** Tanzims-Mac-mini
- **IP (LAN):** 10.217.135.195
- **Python:** 3.9.6

## TURRO five-step setup checklist

| Step | What | Status as of 2026-07-10 |
|------|------|------------------------|
| 1 | Master account (tanzim_ozer) validated | ✓ Done |
| 2 | Burner pool — 10 clean read accounts + live cookies | ⏳ 2/10 live; 6 accounts locked (need recovery inbox) |
| 3 | Master Google Sheet provisioned | ✓ Done |
| 4 | WhatsApp bridge re-authed | ✓ Done |
| 5 | Mac listener live | ✓ Done (2026-07-10) |

## Step 2 blocker
6 IG accounts are locked — password `#IGTheta22x` and `#ThetaThetaTheta22x` both rejected. Need Tanzim to confirm recovery inbox (socialmedia@timbr.fit, info@timbr.fit, or tanzim.seattle@gmail.com) before reset flow can run.

## Live cookies as of 2026-07-10
- `seattle.gym` — fresh, minted that session
- `timbr.us` — live
- 4 others (community, hub, events, timbr.fit) — expired ~3 weeks old, need fresh login

## Cookie rotation cadence
- **20-day cycle** — IG sessions die ~3 weeks; refresh before expiry
- **Towsif ("Salsa")** — human partner who executes the physical logins every 20 days
- **Friday** — owns the operation, pings Towsif when refresh window opens
- **Stagger logins 15–20s apart** — prevents IG checkpoint on simultaneous logins from same IP

## First-run setup (if directory doesn't exist)
```bash
mkdir -p ~/Desktop/Friday/TURRO
cd ~/Desktop/Friday/TURRO
python3 -m venv venv
source venv/bin/activate
pip install flask requests --quiet
```
Then write `listener.py` (template below) and start it.

## Pitfall — Bulldozer directory doesn't exist on this machine
Earlier sessions referenced `~/Desktop/Bulldozer/` — that path never existed on Tanzims-Mac-mini. The canonical path is `~/Desktop/Friday/TURRO/`.

## listener.py template
```python
from flask import Flask, request, jsonify
import requests, json, os

app = Flask(__name__)
CONTROL_SECRET = "turro-secret-2026"
COOKIES_DIR = os.path.expanduser("~/Desktop/Friday/TURRO/cookies")

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "live", "service": "TURRO listener"})

@app.route("/read", methods=["POST"])
def read():
    data = request.json
    if data.get("secret") != CONTROL_SECRET:
        return jsonify({"error": "unauthorized"}), 401
    handle = data.get("handle")
    if not handle:
        return jsonify({"error": "no handle provided"}), 400
    return jsonify({"status": "received", "handle": handle})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5055)
```
