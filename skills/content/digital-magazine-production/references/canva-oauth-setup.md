# Canva OAuth Setup (localhost callback + PKCE)

## When to Use

When integrating Canva Connect API for automated template manipulation (duplicate templates, swap text/images, export PDFs). This flow is for scenarios where the assistant exchanges the auth code for a token on behalf of the user.

## Prerequisites

- Canva Pro or Enterprise account (free accounts lack API access)
- Canva Connect app created at canva.com/developers

## Step-by-Step Flow

### 1. Add Redirect URL in Canva Connect

**Location:** Your app → Authentication tab → "Authorised redirects"

**Action:** Add this exact URL:
```
http://127.0.0.1:8080/callback
```

**Important:** Use `127.0.0.1`, NOT `localhost`. Canva's OAuth is picky about the exact string.

**Why localhost:** The OAuth flow will redirect here after authorization. The page won't load (no local server running), but the auth code will be in the URL bar — that's intentional.

### 2. Obtain Client Credentials

**Location:** Your app → Configuration tab

**Required values:**
- `client_id` — Public identifier for your app
- `client_secret` — Confidential key (never expose in URLs or frontend)

### 3. Generate PKCE Values (Required)

Canva requires PKCE (Proof Key for Code Exchange). Generate before each auth flow:

```python
import secrets
import hashlib
import base64

code_verifier = secrets.token_urlsafe(64)[:128]
code_challenge = base64.urlsafe_b64encode(
    hashlib.sha256(code_verifier.encode()).digest()
).decode().rstrip('=')

# Save code_verifier — needed for token exchange
```

### 4. Generate Authorization URL

**Format:**
```
https://www.canva.com/api/oauth/authorize?
  response_type=code
  &client_id={CLIENT_ID}
  &redirect_uri=http://127.0.0.1:8080/callback
  &scope={SCOPES}
  &code_challenge={CODE_CHALLENGE}
  &code_challenge_method=S256
```

**Full scope set for magazine automation:**
```
design:meta:read design:content:read design:content:write asset:read asset:write brandtemplate:meta:read brandtemplate:content:read brandtemplate:content:write
```

| Scope | Purpose |
|-------|---------|
| `design:meta:read` | Get design metadata (title, page count, thumbnails) |
| `design:content:read` | Read template content |
| `design:content:write` | Modify text and images in templates |
| `asset:read` | Access uploaded images |
| `asset:write` | Upload new images |
| `brandtemplate:meta:read` | List brand templates |
| `brandtemplate:content:read` | Read brand template data fields |
| `brandtemplate:content:write` | Autofill brand template fields |

**Action:** Send this URL to the user. They click it, authenticate with Canva, and authorize the app.

### 5. Capture Auth Code

**What happens:** After authorization, Canva redirects to:
```
http://127.0.0.1:8080/callback?code=XXXXXXXXXXXXX
```

The page won't load, but the URL bar contains the auth code.

**User action:** Copy the full URL and send it to the assistant.

### 6. Exchange Code for Token

**Must include PKCE code_verifier:**

```python
import requests
import base64

client_id = "..."
client_secret = "..."
auth_code = "..."  # from callback URL
code_verifier = "..."  # saved from step 3

credentials = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()

response = requests.post(
    'https://api.canva.com/rest/v1/oauth/token',
    headers={
        'Authorization': f'Basic {credentials}',
        'Content-Type': 'application/x-www-form-urlencoded'
    },
    data={
        'grant_type': 'authorization_code',
        'code': auth_code,
        'code_verifier': code_verifier,
        'redirect_uri': 'http://127.0.0.1:8080/callback'
    }
)
```

**Response:**
```json
{
  "access_token": "...",
  "token_type": "Bearer",
  "expires_in": 14400,
  "refresh_token": "...",
  "scope": "design:meta:read design:content:read ..."
}
```

**Storage:** Save to `~/.hermes/.canva_credentials` (JSON with client_id, client_secret, access_token, refresh_token).

### 7. Token Refresh

Access tokens expire after 4 hours. Refresh tokens last ~2 weeks. Use refresh token to get new access token:

```python
credentials = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()

response = requests.post(
    'https://api.canva.com/rest/v1/oauth/token',
    headers={
        'Authorization': f'Basic {credentials}',
        'Content-Type': 'application/x-www-form-urlencoded'
    },
    data={
        'grant_type': 'refresh_token',
        'refresh_token': refresh_token
    }
)
```

**Always save the new refresh_token** — each refresh invalidates the previous one.

## Brand Template Autofill

### The Catch

Canva's autofill API only works with **data fields** that are explicitly configured in the brand template. Empty dataset = nothing to populate.

**To check if template has data fields:**
```python
response = requests.get(
    f'https://api.canva.com/rest/v1/brand-templates/{template_id}/dataset',
    headers={'Authorization': f'Bearer {access_token}'}
)
# Returns {} if no data fields defined
```

### Setting Up Data Fields (User Must Do This in Canva)

1. Open the brand template in Canva
2. Select a text element you want to autofill
3. Right-click → **Connect data** → Name it (e.g., "client_name", "bio", "quote_1")
4. Repeat for all fillable elements
5. Save the template

Only after data fields are defined can the API populate them.

### Autofill API Call

```python
response = requests.post(
    f'https://api.canva.com/rest/v1/brand-templates/{template_id}/autofill',
    headers={
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    },
    json={
        'data': {
            'client_name': 'Blair',
            'bio': 'Fitness coach based in Seattle...',
            'quote_1': 'Train smarter, not harder.'
        }
    }
)
```

## Critical API Limitations

**The Connect API CANNOT directly edit text elements in designs.** No endpoint exists to:
- List individual elements (text boxes, shapes) on a page
- Read text content from specific elements
- Write/update text in specific elements
- Manipulate element positions or properties

**What DOES work:**
- Get design metadata (title, page count, thumbnails)
- List pages with thumbnail URLs
- Export designs as PDF/PNG
- Brand template autofill (only with pre-defined data fields)

**What this means for magazine automation:**
- Cannot programmatically insert content into arbitrary text boxes
- User must either:
  1. Set up data fields in brand template (right-click → Connect data) for autofill
  2. Use copy-paste workflow with formatted content doc
- The Canva Apps SDK (different product) allows element manipulation but requires building a published Canva app

**Fallback workflow when API can't help:**
1. Export page thumbnails via API for reference
2. Upload thumbnails to Drive for user review
3. Provide structured content doc matching page layout
4. User copy-pastes section by section

## Common Pitfalls

1. **localhost vs 127.0.0.1** — Use `127.0.0.1` in both Canva app settings and auth URL. They must match exactly.
2. **Missing PKCE** — Canva requires PKCE. Auth will fail without code_challenge in auth URL and code_verifier in token exchange.
3. **Using auth code twice** — Auth codes are single-use. If token exchange fails, user must re-authorize.
4. **PKCE mismatch** — Each auth code is paired with its code_verifier. A new auth flow = new PKCE pair. Can't mix and match.
5. **Missing scopes** — If you need brand template access, request `brandtemplate:*` scopes during initial auth. Adding scopes later requires re-auth.
6. **Empty dataset** — Brand template autofill silently does nothing if no data fields are configured in Canva. Check dataset endpoint first.
7. **Design vs Brand Template** — Regular designs (`/designs/{id}`) don't support autofill. Must be a brand template (`/brand-templates/{id}`).

## Quick Reference: Key Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/oauth/token` | POST | Exchange code or refresh token |
| `/designs/{id}` | GET | Get design metadata |
| `/designs/{id}/pages` | GET | List pages with thumbnails |
| `/brand-templates` | GET | List brand templates |
| `/brand-templates/{id}/dataset` | GET | Get data field schema |
| `/brand-templates/{id}/autofill` | POST | Populate data fields |

## Credential Storage

Store at `~/.hermes/.canva_credentials`:
```json
{
  "client_id": "OC-...",
  "client_secret": "cnvca...",
  "redirect_uri": "http://127.0.0.1:8080/callback",
  "access_token": "eyJ...",
  "refresh_token": "eyJ..."
}
```

## References

- [Canva Connect API Docs](https://www.canva.dev/docs/connect/)
- [Brand Templates API](https://www.canva.dev/docs/connect/api-reference/brand-templates/)
