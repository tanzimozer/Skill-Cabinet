# Google Credentials in Tanzim's Environment

## Live Paths

### Token File (Unencrypted, Preferred)
- **Location:** `~/.hermes/google_token.json`
- **Format:** JSON with `token`, `refresh_token`, `token_uri`, `client_id`, `client_secret`, `scopes`
- **Status:** Ready to use immediately
- **When to use:** First choice; no decryption overhead

### EDITH Vault (Encrypted, Requires Middleware)
- **Location:** `~/.hermes/.edith/` directory (encrypted files)
- **Files:** `vault.enc`, `services.map.enc`, `metadata.json`
- **Status:** Encrypted; requires hermes vault decryption service
- **When to use:** Only if token file is unavailable or refresh fails

## Scope Coverage

The token file includes these scopes:
```
gmail.modify, gmail.readonly, gmail.send, calendar, drive, spreadsheets, documents
```

This covers Gmail, Drive, Sheets, and Docs operations — sufficient for most jobs.

## Pattern for Robust Loading

```python
def get_google_credentials():
    """Load Google credentials with fallback chain."""
    import json, os
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    
    # Try token file first (always available)
    token_file = os.path.expanduser('~/.hermes/google_token.json')
    try:
        with open(token_file, 'r') as f:
            token_data = json.load(f)
        
        creds = Credentials(
            token=token_data['token'],
            refresh_token=token_data['refresh_token'],
            token_uri=token_data['token_uri'],
            client_id=token_data['client_id'],
            client_secret=token_data['client_secret'],
            scopes=token_data['scopes']
        )
        creds.refresh(Request())
        return creds
    except Exception as e:
        print(f"Token file failed: {e}")
        raise
```

## Dead Credential Files — Do Not Use

- **`~/friday_backup/google_token.json`** — contains a token tied to OAuth client `313611152308-9is3h086p9n4f8d7q`, which has been **deleted**. Attempting to refresh it throws `deleted_client: The OAuth client was deleted.` This file should be ignored; it is not a fallback.
- **`~/friday_backup/google_client_secret.json`** — same deleted client. Useless.

The **only working token** is `~/.hermes/google_token.json` (client ID `990922176945-n9132okninl4isc7l7kd3n9345e`).

## googleapiclient vs urllib Warning

The `google.oauth2.credentials.Credentials` object may report `expired=False, valid=True` even when the underlying OAuth client has been deleted. The library won't fail until the first actual API call, at which point it throws `RefreshError: deleted_client`.

**Workaround:** Test the token with a raw urllib refresh call first (see `raw-rest-gmail-sheets-patterns.md`). If that succeeds, proceed with urllib for the session — do not switch to googleapiclient unless you have a specific reason and the client is confirmed alive.

```python
# Quick token validity test — do this BEFORE building a googleapiclient service
import json, urllib.request, urllib.parse
with open('/home/hermes/.hermes/google_token.json') as f:
    tok = json.load(f)
data = urllib.parse.urlencode({
    'client_id': tok['client_id'], 'client_secret': tok['client_secret'],
    'refresh_token': tok['refresh_token'], 'grant_type': 'refresh_token'
}).encode()
resp = json.loads(urllib.request.urlopen(
    urllib.request.Request('https://oauth2.googleapis.com/token', data=data, method='POST')
).read())
access_token = resp['access_token']  # If this throws, the client is dead
```

## Session Notes

- **Jun 16, 2026:** Confirmed token file path works reliably; EDITH Vault encrypted and not practical for immediate access.
- Browser timeouts should trigger pivot to API-driven approach (Gmail, Sheets API) rather than Greenhouse/browser lookup.
- **Jul 20, 2026:** `friday_backup/` token confirmed dead (`deleted_client`). Primary `~/.hermes/google_token.json` working. googleapiclient masked the failure until first API call; raw urllib refresh is the reliable canary.
