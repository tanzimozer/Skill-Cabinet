# TURRO Mac Listener — Setup Reference (2026-07-11)

## What it is
A Flask HTTP listener running on Tanzim's Mac mini that receives scrape jobs from Friday. Lives at `~/Desktop/Friday/TURRO/listener.py`.

## Runtime details
- **URL:** `http://10.217.135.195:5055`
- **Health:** `GET /health` → `{"status": "live", "service": "TURRO listener"}`
- **Trigger:** `POST /read` with JSON body `{"secret": "turro-secret-2026", "handle": "<target>"}`
- **Control secret:** `turro-secret-2026`
- **Python env:** `~/Desktop/Friday/TURRO/venv` (Python 3.9.6, Flask + requests installed)

## Start command
```bash
cd ~/Desktop/Friday/TURRO && source venv/bin/activate && python3 listener.py
```
**Terminal window must stay open** — process dies if closed. For persistence, wrap in a launchd plist or use `nohup`.

## Check if running
```bash
ps aux | grep listener.py
```
If only the grep itself appears (no `python3 listener.py` row), it's down — start it.

## Build history
Built 2026-07-11 from scratch because `~/Desktop/Bulldozer` didn't exist on this Mac. Steps taken:
1. `mkdir -p ~/Desktop/Friday/TURRO`
2. `cd ~/Desktop/Friday/TURRO && python3 -m venv venv && source venv/bin/activate`
3. `pip install flask requests`
4. Wrote `listener.py` via heredoc
5. Started — Flask confirmed running on all addresses, port 5055

## Mac context
- Username: `tanzimozer` / Hostname: `Tanzims-Mac-mini`
- Python: 3.9.6 (system), pip 21.2.4 (upgrade available but not required)
- Shell: zsh
