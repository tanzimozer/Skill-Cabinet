---
name: friday-sos-recovery-sheet
description: Create a Google Sheet SOS recovery guide for Friday/Hermes — captures all credentials, file paths, session info, active projects, and restart procedures in one human-readable document.
triggers:
  - User asks to document how to recover or restart Friday
  - User asks to store credentials and access info somewhere safe
  - User wants an SOS or disaster recovery reference
  - Setting up a new integration and wanting to capture it centrally
  - After a major config change that should be documented for recovery
---

# Friday SOS Recovery Sheet

## What this covers
Creating (or updating) a Google Sheet that serves as a complete human-readable recovery guide. Unlike the daily backup (which is a file archive), this is the document you open *before* you can run anything — when the machine is fresh, the session is gone, or you can't remember what was running.

## Sheet structure (8 tabs)
| Tab | Contents |
|-----|----------|
| Overview | Purpose, quick restart command, key paths |
| Hermes Server | Machine info, file paths, start/check/restart instructions |
| API Credentials | All API keys and tokens (Anthropic, Trello, etc.) |
| Google OAuth | GCP project, client ID/secret, token paths, re-auth steps |
| WhatsApp Session | Session dir, re-pair procedure, corruption recovery |
| Active Projects | All running scripts, cron jobs, integrations, their paths |
| Key Contacts | WA IDs, persona rules, allowed-action notes per person |
| Cron Jobs | Job IDs, schedules, how to recreate |

## Key file locations (Tanzim's Mac Mini / Hermes)
- Hermes home: `/home/hermes/`
- Config dir: `/home/hermes/.hermes/`
- Config file: `/home/hermes/.hermes/config.yaml`
- Auth (Anthropic): `/home/hermes/.hermes/auth.json`
- Google OAuth client secret: `/home/hermes/.hermes/google_client_secret.json`
- Google token: `/home/hermes/.hermes/google_token.json`
- WhatsApp session: `/home/hermes/.hermes/whatsapp/session/`
- WA main creds: `/home/hermes/.hermes/whatsapp/session/creds.json`
- Skills: `/home/hermes/.hermes/skills/`
- Memories: `/home/hermes/.hermes/memories/`
- Cron: `/home/hermes/.hermes/cron/`
- Sessions DB: `/home/hermes/.hermes/state.db`
- Job scraper: `/home/hermes/jobs/`
- IG unfollower: `/home/hermes/instagram_unfollower/`
- Daily state: `/home/hermes/context/daily_state.md`

## Sheet IDs
- **Friday SOS Sheet**: `1Zjp7OyHISLXr-uYMJBBc6SRPFqud9BShDGTIe-d9ZOw`
  - URL: https://docs.google.com/spreadsheets/d/1Zjp7OyHISLXr-uYMJBBc6SRPFqud9BShDGTIe-d9ZOw/edit
- Job Tracker Sheet: `1v6CY46PBfGyrde8uuMzPv1cETZrOiflUj_HY34SJC_Q`

## How to create the sheet (Python via Google Sheets API)

### Step 1: Create with multiple tabs
```python
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

creds = Credentials.from_authorized_user_file("/home/hermes/.hermes/google_token.json")
svc = build("sheets", "v4", credentials=creds).spreadsheets()

body = {
    "properties": {"title": "Friday — SOS Recovery Sheet"},
    "sheets": [
        {"properties": {"title": tab, "index": i}}
        for i, tab in enumerate(["Overview","Hermes Server","API Credentials",
            "Google OAuth","WhatsApp Session","Active Projects","Key Contacts","Cron Jobs"])
    ]
}
ss = svc.create(body=body).execute()
SID = ss["spreadsheetId"]
```

### Step 2: Write each tab
```python
def write(tab, values):
    svc.values().update(
        spreadsheetId=SID,
        range=f"'{tab}'!A1",
        valueInputOption="RAW",
        body={"values": values}
    ).execute()
```

### Step 3: Format (bold headers, freeze row 1, dark header bg)
```python
requests = []
meta = svc.get(spreadsheetId=SID).execute()
for s in meta["sheets"]:
    sheet_id = s["properties"]["sheetId"]
    requests.append({"repeatCell": {
        "range": {"sheetId": sheet_id, "startRowIndex": 0, "endRowIndex": 1},
        "cell": {"userEnteredFormat": {
            "backgroundColor": {"red": 0.13, "green": 0.13, "blue": 0.13},
            "textFormat": {"bold": True, "foregroundColor": {"red": 1, "green": 0.76, "blue": 0.0}}
        }},
        "fields": "userEnteredFormat(backgroundColor,textFormat)"
    }})
    requests.append({"updateSheetProperties": {
        "properties": {"sheetId": sheet_id, "gridProperties": {"frozenRowCount": 1}},
        "fields": "gridProperties.frozenRowCount"
    }})
    requests.append({"autoResizeDimensions": {
        "dimensions": {"sheetId": sheet_id, "dimension": "COLUMNS", "startIndex": 0, "endIndex": 5}
    }})
svc.batchUpdate(spreadsheetId=SID, body={"requests": requests}).execute()
```

## Quick restart procedure (nuclear scenario)
1. SSH into Mac Mini or open terminal
2. `cd /home/hermes/.hermes/hermes-agent && npm start`
3. Watch logs for WA QR code: `tail -f /home/hermes/.hermes/logs/gateway.log`
4. On Tanzim's phone: WhatsApp → Linked Devices → Link a Device → scan QR
5. Friday is back online

## WA session recovery (if corrupted)
1. `rm -rf /home/hermes/.hermes/whatsapp/session/`
2. Restart hermes-agent
3. Re-scan QR code (step 3-5 above)
4. Pre-backup: `tar -czf ~/wa_session_backup.tar.gz /home/hermes/.hermes/whatsapp/session/`

## Google re-auth (if token expires)
```bash
GSETUP="python /home/hermes/.hermes/skills/productivity/google-workspace/scripts/setup.py"
$GSETUP --check           # verify first
$GSETUP --auth-url        # get new auth URL if needed
$GSETUP --auth-code URL   # exchange redirect URL
$GSETUP --check           # verify AUTHENTICATED
```
Google account: tan.biz@icloud.com

## Pitfalls
- Don't include raw secrets in memory entries — keep them in the sheet and in credential files
- The WA session has 50+ files; back up the whole dir, not just creds.json
- Google client secret is only shown once at creation — never delete it from the file without noting it
- The `execute_code` tool often times out for long gather operations — use `mcp_terminal` + `mcp_read_file` separately to collect info before writing the sheet
- Gather all info FIRST, then write the sheet in one pass rather than iterating

## When to update this sheet
- After adding a new API integration or credential
- After a new cron job is created
- After the WA session is re-paired (new device IDs)
- After any major config change
- Prompt: "BETA update the Friday SOS sheet with [new info]"
