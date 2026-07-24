---
name: canva-reauth
category: integrations
description: Re-authenticate Canva OAuth when token lineage is revoked. Covers the full flow including setting up a public redirect to avoid localhost 404 errors.
---

# Canva Re-Auth

## Credentials location
- File: `~/.hermes/.canva_credentials`
- Fields: `client_id`, `client_secret`, `access_token`, `refresh_token`
- Client ID: `OC-AZ5TE93EPw0y`
- Redirect URI registered: `http://127.0.0.1:8080/callback`

## Why it breaks
Canva revokes the entire token lineage if the OAuth app is idle or re-authorized elsewhere. Refresh token stops working → need full re-auth.

## The localhost 404 problem
The registered redirect URI is `http://127.0.0.1:8080/callback` — this only works if a local server is running on the VM to catch the callback. Sending Tanzim to this URL from his phone gives a 404 because his device has no server on port 8080.

## Fix: spin up a callback server on the VM first

```bash
# On the VM — start a one-shot callback listener
python3 -c "
import http.server, urllib.parse, threading

code_received = []

class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        params = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
        code = params.get('code', [None])[0]
        if code:
            code_received.append(code)
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'Auth complete! You can close this tab.')
        else:
            self.send_response(400)
            self.end_headers()
    def log_message(self, *args): pass

srv = http.server.HTTPServer(('0.0.0.0', 8080), Handler)
print('Listening on :8080')
while not code_received:
    srv.handle_request()
print('CODE:', code_received[0])
" &
```

Then expose port 8080 publicly (ngrok or VM port-forward) OR use a different redirect URI entirely.

## Simpler fix: use a public redirect catcher
Register a new redirect URI in Canva Developer Portal pointing to a public endpoint (e.g. `https://hermes.timbr.fit/oauth/canva/callback` or use a service like `https://oauthlink.com`).

Until that's set up: **ask Tanzim to paste the full redirect URL** (even if page 404s, the URL bar has `?code=...`). Then exchange manually:

```python
import json, urllib.request, urllib.parse, os

code = "PASTE_CODE_HERE"

with open(os.path.expanduser('~/.hermes/.canva_credentials')) as f:
    creds = json.load(f)

data = urllib.parse.urlencode({
    'grant_type': 'authorization_code',
    'code': code,
    'redirect_uri': creds['redirect_uri'],
    'client_id': creds['client_id'],
    'client_secret': creds['client_secret'],
    'code_verifier': ''  # omit if PKCE not used
}).encode()

req = urllib.request.Request(
    'https://api.canva.com/rest/v1/oauth/token',
    data=data, method='POST'
)
resp = json.loads(urllib.request.urlopen(req).read())
print(resp)

creds['access_token'] = resp['access_token']
creds['refresh_token'] = resp['refresh_token']
with open(os.path.expanduser('~/.hermes/.canva_credentials'), 'w') as f:
    json.dump(creds, f)
print("Saved.")
```

## Auth URL to send Tanzim
```
https://www.canva.com/api/oauth/authorize?client_id=OC-AZ5TE93EPw0y&response_type=code&scope=design%3Acontent%3Aread%20design%3Acontent%3Awrite%20design%3Ameta%3Aread&redirect_uri=http%3A%2F%2F127.0.0.1%3A8080%2Fcallback
```

## After re-auth: update SOS sheet
Add Canva row to "API Credentials" tab in sheet `1Zjp7OyHISLXr-uYMJBBc6SRPFqud9BShDGTIe-d9ZOw`.

## Pitfalls
- Canva access tokens expire in 4hr — auto-refresh works until lineage is revoked
- Lineage revocation = must do full re-auth, not just refresh
- Double-encoded scopes in URL (`%253A` instead of `%3A`) will give a 400 — always single-encode
- Scope string: `design:content:read design:content:write design:meta:read`
