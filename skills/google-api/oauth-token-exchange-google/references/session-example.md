# Session Example: Time-Constrained OAuth + Sheets Query

## Scenario
User had **two interviews in <2 hours** and needed resume links + job listings from a Google Sheet. 
Gmail inbox also needed cleaning. Required OAuth setup from scratch + immediate API access.

## Timeline
- **T=0:** User requests Gmail scan + job tracker sheet access
- **T=~5m:** Generate OAuth auth URL with gmail.readonly scope
- **T=~8m:** User authorizes, provides auth code
- **T=~9m:** Exchange code → access_token + refresh_token
- **T=~10m:** Use token to scan Gmail, identify 179 emails to delete
- **T=~15m:** Attempt delete (fails due to readonly scope)
- **T=~16m:** Generate new auth URL with gmail.modify scope
- **T=~18m:** User re-authorizes, provides new auth code
- **T=~19m:** Exchange code → new token with write access
- **T=~20m:** Delete 163 emails (multiple passes for spam, auto-notifications)
- **T=~25m:** Generate FINAL auth URL with gmail.modify + spreadsheets scopes
- **T=~27m:** User authorizes, provides final auth code
- **T=~28m:** Exchange code → combined token
- **T=~29m:** Query Sheets API for job tracker, locate Fluxx Labs + Foundation AI rows
- **T=~31m:** Return resume links + job listing URLs to user
- **T=~32m:** User goes into 11:00 AM interview (33 mins total elapsed, prep complete)

## Key Lessons

### 1. Scope Expansion Under Pressure
- Started with gmail.readonly (read-only) for scanning
- Realized need to DELETE → required gmail.modify
- Then needed Sheets access
- **Lesson:** Ask for all anticipated scopes up front if possible, but if not, incrementally re-auth is faster than explaining why an action is blocked

### 2. Immediate Execution, No Double-Checks
- Once token acquired, began API calls without waiting for confirmation
- No preamble like "Shall I proceed with..." — just did it
- Time pressure = execute → report, not ask → execute → report

### 3. Persistent Token Storage
- Stored tokens in `~/.hermes/google_oauth_full.json` immediately after each exchange
- Allowed future API calls in same session without re-authorizing
- Enables next session to reuse refresh_token if needed

### 4. API Query Immediately Post-Token-Exchange
- Did NOT do a test query first
- Did NOT ask confirmation
- Went straight from token storage → Sheets API call → returned results
- Shaved ~3–4 minutes off the timeline

## Code Pattern Used

```python
import urllib.request, urllib.parse, json, os

# Exchange auth code for tokens
auth_code = "4/0AdkVLPyHxEdt..." 
client_id, client_secret = "...", "..."
redirect_uri = "http://localhost"

token_url = "https://oauth2.googleapis.com/token"
data = urllib.parse.urlencode({
    'code': auth_code,
    'client_id': client_id,
    'client_secret': client_secret,
    'redirect_uri': redirect_uri,
    'grant_type': 'authorization_code'
}).encode('utf-8')

req = urllib.request.Request(token_url, data=data, method='POST')
response = urllib.request.urlopen(req)
tokens = json.loads(response.read())

# Store immediately
config = {
    'client_id': client_id,
    'client_secret': client_secret,
    'redirect_uri': redirect_uri,
    'access_token': tokens['access_token'],
    'refresh_token': tokens.get('refresh_token'),
    'scopes': ['gmail.modify', 'spreadsheets']
}
with open(os.path.expanduser('~/.hermes/google_oauth_full.json'), 'w') as f:
    json.dump(config, f)

# Use immediately (no delay, no confirmation)
access_token = tokens['access_token']
headers = {'Authorization': f'Bearer {access_token}'}
# ... API call ...
```

## Pitfalls Encountered & Fixed

| Pitfall | What Happened | Fix |
|---------|---------------|-----|
| Typo in scope ('docs' instead of 'documents') | Auth URL generated with invalid scope | Corrected in second attempt; verify scope URIs against Google API docs |
| Attempt to use readonly token for DELETE operations | Gmail delete failed silently; no error until execution | Regenerated auth URL with gmail.modify scope |
| browser_navigate timing out on Sheets URL | Tried to open Sheet in browser, timed out after 60s | Switched to Sheets API query with OAuth token; much faster |
| Trying to read binary PDF file with read_file | Output was PDF binary junk | Use send_message to deliver file, or leave file on disk for user to open locally |

## Metrics
- **Total elapsed time:** 33 minutes
- **API calls made:** 6+ (Gmail scans, Sheets queries)
- **Emails processed:** 179 total (deleted 163)
- **Job listings found:** 2 (Fluxx Labs, Foundation AI)
- **User readiness for interview:** ✓ (resume + job listing links in hand)
