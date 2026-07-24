# Daily Credential Check — Setup & Script

**Created:** June 11, 2026  
**Schedule:** 06:00 UTC every day  
**Output:** `~/Desktop/CREDENTIAL_CHECK_LOG.md`

---

## Script Template

**Path:** `~/.hermes/cron-jobs/daily_credential_check.py`

```python
#!/usr/bin/env python3
"""
Daily credential check — refresh tokens, test APIs, log results.
Scheduled to run at 06:00 UTC every day.
"""

import json
import os
from datetime import datetime
from pathlib import Path

# Configuration
VAULT_PATH = Path.home() / '.hermes' / 'vault.json'
GOOGLE_TOKEN_FILE = Path.home() / '.hermes' / 'google_token.json'
LOG_FILE = Path.home() / 'Desktop' / 'CREDENTIAL_CHECK_LOG.md'

def load_vault():
    """Load encrypted vault."""
    with open(VAULT_PATH) as f:
        return json.load(f)

def refresh_google_token():
    """Refresh Google OAuth token if expired."""
    try:
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        
        creds = Credentials.from_authorized_user_file(str(GOOGLE_TOKEN_FILE))
        
        if creds.expired and creds.refresh_token:
            request = Request()
            creds.refresh(request)
            
            # Write refreshed token back
            token_data = {
                'token': creds.token,
                'refresh_token': creds.refresh_token,
                'id_token': getattr(creds, 'id_token', None),
                'token_uri': creds.token_uri,
                'client_id': creds.client_id,
                'client_secret': creds.client_secret,
                'scopes': creds.scopes,
                'type': 'authorized_user'
            }
            with open(GOOGLE_TOKEN_FILE, 'w') as f:
                json.dump(token_data, f, indent=2)
            
            return "✓ Google OAuth token refreshed"
        else:
            return "✓ Google OAuth token still valid"
    except Exception as e:
        return f"✗ Google OAuth refresh failed: {str(e)[:80]}"

def test_gmail():
    """Test Gmail API connection."""
    try:
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build
        
        creds = Credentials.from_authorized_user_file(str(GOOGLE_TOKEN_FILE))
        gmail = build('gmail', 'v1', credentials=creds)
        gmail.users().messages().list(userId='me', maxResults=1).execute()
        
        return "✓ Gmail API responding"
    except Exception as e:
        return f"✗ Gmail API failed: {str(e)[:80]}"

def test_google_drive():
    """Test Google Drive API connection."""
    try:
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build
        
        creds = Credentials.from_authorized_user_file(str(GOOGLE_TOKEN_FILE))
        drive = build('drive', 'v3', credentials=creds)
        drive.files().list(pageSize=1, spaces='drive').execute()
        
        return "✓ Google Drive API responding"
    except Exception as e:
        return f"✗ Google Drive API failed: {str(e)[:80]}"

def test_google_calendar():
    """Test Google Calendar API connection."""
    try:
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build
        
        creds = Credentials.from_authorized_user_file(str(GOOGLE_TOKEN_FILE))
        calendar = build('calendar', 'v3', credentials=creds)
        calendar.calendarList().list().execute()
        
        return "✓ Google Calendar API responding"
    except Exception as e:
        # Check if it's the "API not enabled" error
        if '403' in str(e) and 'not been used' in str(e):
            return "⚠ Google Calendar API: 403 (service not enabled in Google Cloud project)"
        return f"✗ Google Calendar API failed: {str(e)[:80]}"

def test_github_pat():
    """Test GitHub PAT with API call."""
    try:
        import requests
        
        vault = load_vault()
        token = vault['github']['pat']
        
        response = requests.get(
            'https://api.github.com/rate_limit',
            headers={'Authorization': f'token {token}'}
        )
        
        if response.status_code == 200:
            data = response.json()
            remaining = data['rate']['remaining']
            limit = data['rate']['limit']
            return f"✓ GitHub PAT valid (rate limit: {remaining}/{limit})"
        else:
            return f"✗ GitHub PAT failed: {response.status_code}"
    except Exception as e:
        return f"✗ GitHub test failed: {str(e)[:80]}"

def log_results(results):
    """Write results to log file."""
    timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')
    log_entry = f"\n## {timestamp}\n" + "\n".join([f"- {r}" for r in results])
    
    with open(LOG_FILE, 'a') as f:
        f.write(log_entry)
    
    print("\n".join(results))

def main():
    """Run all checks."""
    results = []
    
    # Refresh tokens
    results.append(refresh_google_token())
    
    # Test connections
    results.append(test_gmail())
    results.append(test_google_drive())
    results.append(test_google_calendar())
    results.append(test_github_pat())
    
    # Log
    log_results(results)

if __name__ == '__main__':
    main()
```

---

## Cron Job Setup

**Add to crontab:**
```bash
crontab -e
```

**Line to add:**
```
0 6 * * * /usr/bin/python3 ~/.hermes/cron-jobs/daily_credential_check.py >> ~/.hermes/logs/cron.log 2>&1
```

**Verify:**
```bash
crontab -l | grep credential_check
```

---

## Log File Format

**Location:** `~/Desktop/CREDENTIAL_CHECK_LOG.md`  
**Example:**

```markdown
# CREDENTIAL CHECK LOG

## 2026-06-11 06:00:00 UTC
- ✓ Google OAuth token refreshed
- ✓ Gmail API responding
- ✓ Google Drive API responding
- ⚠ Google Calendar API: 403 (service not enabled in Google Cloud project)
- ✓ GitHub PAT valid (rate limit: 4987/5000)

## 2026-06-10 06:00:00 UTC
- ✓ Google OAuth token still valid
- ✓ Gmail API responding
- ✓ Google Drive API responding
- ⚠ Google Calendar API: 403 (service not enabled in Google Cloud project)
- ✓ GitHub PAT valid (rate limit: 4993/5000)
```

---

## Troubleshooting

### "Google OAuth refresh failed: ModuleNotFoundError"
**Fix:** Install google-auth-oauthlib
```bash
pip install google-auth-oauthlib
```

### "Gmail API failed: 403 Forbidden"
**Cause:** Token doesn't have gmail.modify scope  
**Fix:** Regenerate OAuth token with proper scopes

### "GitHub test failed: 401"
**Cause:** PAT expired or invalid  
**Fix:** Regenerate new PAT, update vault.json

### Cron job doesn't run
**Check:**
```bash
# Verify Python path
which python3

# Check cron logs
grep CRON /var/log/syslog  # Linux
log stream --predicate 'process == "cron"'  # macOS

# Manually test script
python3 ~/.hermes/cron-jobs/daily_credential_check.py
```

---

## Refinements (Future)

- Slack notification on failures (vs. silent flag)
- Email summary of all checks to user inbox
- Automatic PAT rotation trigger (currently manual)
- GitHub Actions workflow for cloud execution
- Hindsight integration (log check results to long-term memory)

---

**Status:** Ready to deploy  
**Last Updated:** June 11, 2026 at 20:30 UTC
