# vault.json Structure — Tanzim's Credential Store

## Overview
`~/.hermes/vault.json` is the plaintext credential store. No encryption. Accessible via Python json module and shell. Permissions set to 0o600 (read/write owner only).

## Current Structure (as of June 9, 2026)

```json
{
  "google": {
    "oauth": {
      "access_token": "ya29.a0AT3oNZ_UZ-UWasHOUd1jNX1kMfe1Aqb6hpRUX7TC66o...",
      "refresh_token": "<REDACTED_OAUTH_TOKEN>",
      "token_uri": "https://oauth2.googleapis.com/token",
      "client_id": "313611152308-ffm0jsbfr95mnq3r19vd9246p51c01ct.apps.googleusercontent.com",
      "client_secret": "<GOOGLE_OAUTH_CLIENT_SECRET_REDACTED>",
      "type": "authorized_user",
      "scopes": [
        "https://www.googleapis.com/auth/gmail.modify",
        "https://www.googleapis.com/auth/gmail.readonly",
        "https://www.googleapis.com/auth/gmail.send",
        "https://www.googleapis.com/auth/calendar",
        "https://www.googleapis.com/auth/drive",
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/documents"
      ]
    }
  },
  "github": {
    "account": "tanzimozer",
    "pat": "<GITHUB_PAT — see ~/.hermes/vault.json:github_token>",
    "scopes": ["repo", "gist", "user"],
    "created": "2026-06-09",
    "expires": "2027-06-09"
  },
  "icloud": {
    "email": "tanzimx@icloud.com",
    "app_password": "[STORED_SECURELY]",
    "status": "active"
  },
  "webflow": {
    "api_token": "[STORED_SECURELY]",
    "created": "2026-06-09"
  },
  "wix": {
    "api_key": "[STORED_SECURELY]",
    "created": "2026-06-09"
  },
  "instagram": {
    "account": "tanzim.seattle",
    "uid": "40730017115",
    "session_cookies": "[STORED_SECURELY]",
    "last_updated": "2026-06-04",
    "note": "Cookies may be stale; refresh if rate-limited"
  },
  "whatsapp": {
    "bridge_token": "[STORED_SECURELY]",
    "phone": "160799431606497@lid"
  },
  "anthropic_api": {
    "api_key": "[STORED_SECURELY]"
  },
  "hindsight_llm": {
    "api_key": "[STORED_SECURELY]"
  }
}
```

## Access Pattern

### Read from Python
```python
import json

with open(os.path.expanduser('~/.hermes/vault.json')) as f:
    vault = json.load(f)

# Access Google OAuth
google_token = vault['google']['oauth']['access_token']

# Access GitHub PAT
github_pat = vault['github']['pat']
```

### Update in Python
```python
import json
import os

with open(os.path.expanduser('~/.hermes/vault.json')) as f:
    vault = json.load(f)

# Add new credential
vault['new_service'] = {
    'key': 'value',
    'created': '2026-06-09'
}

# Write back
with open(os.path.expanduser('~/.hermes/vault.json'), 'w') as f:
    json.dump(vault, f, indent=2)

# Secure permissions
os.chmod(os.path.expanduser('~/.hermes/vault.json'), 0o600)
```

## Naming Conventions

### Top-level Keys
Use service name (lowercase):
- `google`, `github`, `icloud`, `webflow`, `wix`
- Not: `GOOGLE`, `google_oauth`, `google_cloud`

### Sub-keys
- `account` or `email` — Username / email address
- `token` — OAuth access token
- `refresh_token` — OAuth refresh token
- `pat` — Personal access token (GitHub)
- `api_key` — Service API key
- `api_token` — Service API token
- `app_password` — Email app-specific password
- `secret` — Generic secret string
- `scopes` — List of permission scopes (array)
- `created`, `expires` — ISO date strings (YYYY-MM-DD)
- `status` — "active", "expired", "stale"
- `note` or `_note` — Human-readable annotation

### Example: Well-formed entry
```json
{
  "service_name": {
    "account": "username",
    "api_key": "full_key_string",
    "scopes": ["scope1", "scope2"],
    "created": "2026-06-09",
    "expires": "2027-06-09",
    "status": "active",
    "note": "Refresh token valid for 1 year"
  }
}
```

## Desktop Mirroring
Every credential added to vault.json should also be logged in `~/Desktop/CREDENTIALS_MASTER.md` with the same structure (but full values visible for human reference).

Update Desktop file after every vault.json change.

## File Permissions
Always set to 0o600 (owner read/write, no group/other access):
```bash
chmod 600 ~/.hermes/vault.json
```

## Backup Strategy
- vault.json is the source of truth
- Desktop CREDENTIALS_MASTER.md is the human-readable backup
- Both stored on local machine (not cloud-synced unless user explicitly decides)
