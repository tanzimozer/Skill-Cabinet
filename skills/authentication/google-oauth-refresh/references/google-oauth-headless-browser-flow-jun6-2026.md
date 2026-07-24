# Google OAuth Authentication — Headless Environment (No Browser) — Jun 6 2026

**Status:** VERIFIED PATTERN. Successfully authenticated Google Sheets API from VM using browser-less flow.

## The Scenario

You're running on a VM (no display, no browser). User is on their Mac. Google API needs OAuth token. Standard `run_local_server()` won't work because there's no browser to open on the VM.

**Solution:** Use the **Out-Of-Band (OOB) redirect URI** pattern.

## How It Works

1. **Agent generates auth URL** on the VM (no browser involved)
2. **Agent sends URL to user** (via message, print, email, etc.)
3. **User opens URL in their own browser** (on their Mac)
4. **User signs in, gets auth code** shown on screen
5. **User pastes code back to agent** (via message/input)
6. **Agent exchanges code for token** on the VM
7. **Token stored locally**, ready for API calls

## Implementation

### Step 1: Generate the Auth URL

```python
import json
import urllib.parse
import urllib.request

CLIENT_SECRET_FILE = "/home/hermes/.hermes/google_client_secret.json"

with open(CLIENT_SECRET_FILE) as f:
    client_data = json.load(f)

# Handle both "installed" (desktop app) and "web" (web app) client types
creds = client_data.get("installed", client_data.get("web", {}))

# OOB redirect URI — user will paste code manually
params = {
    "client_id": creds["client_id"],
    "redirect_uri": "urn:ietf:wg:oauth:2.0:oob",
    "response_type": "code",
    "scope": "https://www.googleapis.com/auth/spreadsheets https://www.googleapis.com/auth/drive https://www.googleapis.com/auth/gmail.modify",
    "access_type": "offline",  # Get refresh token
    "prompt": "consent"  # Force consent screen (even if already authed)
}

auth_url = "https://accounts.google.com/o/oauth2/auth?" + urllib.parse.urlencode(params)
print(f"Open this URL in your browser and copy the auth code:\n{auth_url}\n")
```

### Step 2: User Opens URL, Gets Code

User does:
1. Click/paste the URL in their browser
2. Sign in with Google account
3. Grant permission to the scopes
4. See a page showing: `Please copy this code, switch to your application and paste it there: 4/0AZrh...`
5. Copy the code (starts with `4/0AZrh...`)

### Step 3: Agent Receives Code from User

```python
auth_code = input("Paste the auth code here: ").strip()
```

Or via message system:
```python
# e.g., from a Slack message or direct input
auth_code = message_from_user  # "4/0AZrh..."
```

### Step 4: Exchange Code for Token

```python
def exchange_auth_code_for_token(auth_code, client_data):
    """Exchange authorization code for access + refresh tokens."""
    creds = client_data.get("installed", client_data.get("web", {}))
    
    data = urllib.parse.urlencode({
        "client_id": creds["client_id"],
        "client_secret": creds["client_secret"],
        "code": auth_code,
        "grant_type": "authorization_code",
        "redirect_uri": "urn:ietf:wg:oauth:2.0:oob"
    }).encode('utf-8')
    
    req = urllib.request.Request(
        "https://oauth2.googleapis.com/token",
        data=data,
        method="POST"
    )
    
    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            token_data = json.loads(response.read())
            return token_data
    except urllib.error.HTTPError as e:
        error_body = json.loads(e.read())
        raise Exception(f"Token exchange failed: {error_body}")

# Get the tokens
token_response = exchange_auth_code_for_token(auth_code, client_data)
```

### Step 5: Save Token for Future Use

```python
def save_token(token_data, output_file="/home/hermes/.hermes/google_token.json"):
    """Save token with metadata for refresh."""
    # Add client credentials to the token for future refresh
    with open(CLIENT_SECRET_FILE) as f:
        client_data = json.load(f)
    
    creds = client_data.get("installed", client_data.get("web", {}))
    
    full_token = {
        "token": token_response.get("access_token"),
        "refresh_token": token_response.get("refresh_token"),
        "token_uri": "https://oauth2.googleapis.com/token",
        "client_id": creds["client_id"],
        "client_secret": creds["client_secret"],
        "scopes": [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",
            "https://www.googleapis.com/auth/gmail.modify"
        ],
        "type": "authorized_user",
        "created_at": datetime.datetime.now().isoformat()
    }
    
    with open(output_file, 'w') as f:
        json.dump(full_token, f, indent=2)
    
    import os
    os.chmod(output_file, 0o600)  # Read/write owner only
    print(f"✅ Token saved to {output_file}")
    return full_token

token = save_token(token_response)
```

## Complete Workflow (One Script)

```python
#!/usr/bin/env python3
"""
Authenticate Google Sheets API from headless VM.
User opens browser URL, pastes code back, token is stored locally.
"""

import json
import urllib.parse
import urllib.request
import datetime
import os
import sys

CLIENT_SECRET_FILE = "/home/hermes/.hermes/google_client_secret.json"
OUTPUT_TOKEN_FILE = "/home/hermes/.hermes/google_token.json"

def generate_auth_url():
    """Generate Google OAuth URL for user to visit."""
    with open(CLIENT_SECRET_FILE) as f:
        client_data = json.load(f)
    
    creds = client_data.get("installed", client_data.get("web", {}))
    
    params = {
        "client_id": creds["client_id"],
        "redirect_uri": "urn:ietf:wg:oauth:2.0:oob",
        "response_type": "code",
        "scope": "https://www.googleapis.com/auth/spreadsheets https://www.googleapis.com/auth/drive https://www.googleapis.com/auth/gmail.modify",
        "access_type": "offline",
        "prompt": "consent"
    }
    
    return "https://accounts.google.com/o/oauth2/auth?" + urllib.parse.urlencode(params)

def exchange_code(auth_code):
    """Exchange authorization code for access + refresh tokens."""
    with open(CLIENT_SECRET_FILE) as f:
        client_data = json.load(f)
    
    creds = client_data.get("installed", client_data.get("web", {}))
    
    data = urllib.parse.urlencode({
        "client_id": creds["client_id"],
        "client_secret": creds["client_secret"],
        "code": auth_code,
        "grant_type": "authorization_code",
        "redirect_uri": "urn:ietf:wg:oauth:2.0:oob"
    }).encode('utf-8')
    
    req = urllib.request.Request(
        "https://oauth2.googleapis.com/token",
        data=data,
        method="POST"
    )
    
    with urllib.request.urlopen(req, timeout=15) as response:
        return json.loads(response.read())

def save_token(token_response):
    """Save token for future API calls."""
    with open(CLIENT_SECRET_FILE) as f:
        client_data = json.load(f)
    
    creds = client_data.get("installed", client_data.get("web", {}))
    
    full_token = {
        "token": token_response.get("access_token"),
        "refresh_token": token_response.get("refresh_token"),
        "token_uri": "https://oauth2.googleapis.com/token",
        "client_id": creds["client_id"],
        "client_secret": creds["client_secret"],
        "scopes": [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",
            "https://www.googleapis.com/auth/gmail.modify"
        ],
        "type": "authorized_user",
        "created_at": datetime.datetime.now().isoformat()
    }
    
    with open(OUTPUT_TOKEN_FILE, 'w') as f:
        json.dump(full_token, f, indent=2)
    
    os.chmod(OUTPUT_TOKEN_FILE, 0o600)
    return full_token

def main():
    print("=== Google OAuth Authentication (Headless) ===\n")
    
    # Step 1: Generate URL
    auth_url = generate_auth_url()
    print(f"Step 1: Open this URL in your browser:\n{auth_url}\n")
    print("Step 2: Sign in, grant permission, and copy the code shown on screen.")
    print("Step 3: Paste the code below:\n")
    
    # Step 2: Get code from user
    auth_code = input("Auth code: ").strip()
    if not auth_code:
        print("❌ No code provided. Aborting.")
        sys.exit(1)
    
    # Step 3: Exchange code
    print("\nExchanging code for token...")
    try:
        token_response = exchange_code(auth_code)
    except Exception as e:
        print(f"❌ Exchange failed: {e}")
        sys.exit(1)
    
    # Step 4: Save token
    print("Saving token...")
    token = save_token(token_response)
    print(f"✅ Token saved to {OUTPUT_TOKEN_FILE}")
    print(f"\nToken expires: {token_response.get('expires_in')} seconds from now")
    print(f"Refresh token stored: {bool(token.get('refresh_token'))}")

if __name__ == "__main__":
    main()
```

## Testing the Token

Once saved, test it with a simple Sheets API call:

```python
import json
import requests

with open("/home/hermes/.hermes/google_token.json") as f:
    token_data = json.load(f)

headers = {"Authorization": f"Bearer {token_data['token']}"}

# List the user's spreadsheets
r = requests.get(
    "https://sheets.googleapis.com/v4/spreadsheets",
    headers=headers
)

if r.status_code == 200:
    print(f"✅ Token works! Found {len(r.json().get('spreadsheets', []))} spreadsheets")
else:
    print(f"❌ Token invalid: {r.status_code} {r.text}")
```

## Why OOB Over run_local_server()?

| Approach | Works on VM | Works on User's Mac | Setup | Browser Required |
|----------|-------------|---------------------|-------|------------------|
| **OOB** | ✅ | ✅ | Simple | No |
| **run_local_server()** | ❌ (no display) | ✅ | More setup | Yes |
| **browser.open()** | ❌ (no display) | ❌ | Complex | Yes |

OOB is the cleanest for headless environments.

## Common Errors

### `redirect_uri_mismatch`
**Cause:** The `redirect_uri` in the URL doesn't match the one used in the token exchange.

**Fix:** Must be exactly `urn:ietf:wg:oauth:2.0:oob` in BOTH places (auth URL generation AND code exchange).

### `invalid_client` or `unauthorized_client`
**Cause:** `client_id` or `client_secret` is wrong, or the file is from the wrong Google Cloud project.

**Fix:** Download fresh `client_secret.json` from Google Cloud Console → your project → OAuth 2.0 Client IDs → download JSON.

### `invalid_grant` after 10 minutes
**Cause:** Auth code expires after 10 minutes of user visiting the auth URL.

**Fix:** User must complete the auth flow and paste code within 10 minutes. If more than 10 minutes have passed, regenerate the URL and start over.

### `access_denied`
**Cause:** User clicked "Cancel" or didn't grant permission.

**Fix:** User needs to repeat the flow and grant permission to all scopes.

## Session Log — Jun 6 2026

**Setup:**
- VM: Linux environment, no browser
- User: On Mac with Chrome
- Goal: Authenticate Google Sheets API to write crawl results

**Execution:**
1. Generated auth URL on VM
2. User opened URL in Mac browser
3. User signed in with Google account
4. User granted "Spreadsheets", "Drive", "Gmail" permissions
5. User copied auth code from consent screen
6. Pasted code back to VM prompt
7. VM exchanged code for token
8. Token saved to `~/.hermes/google_token.json`
9. Tested: Sheets API call successful

**Result:** ✅ Token valid, writable to Google Sheets API. Next session can use stored token without re-auth.

## Next Steps

After obtaining the token:
1. **Verify refresh token exists** in `~/.hermes/google_token.json`
2. **Test token** with a simple API call (see "Testing the Token" above)
3. **Store securely** — file has 0o600 permissions (read/write owner only)
4. **Set up refresh** — see main `google-oauth-refresh` skill for refresh patterns

On next token expiry, use the refresh flow (see main skill) — no need to repeat the OOB flow.
