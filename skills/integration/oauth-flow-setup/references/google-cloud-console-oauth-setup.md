# Google Cloud Console — OAuth App Setup from Scratch

**When to use:** First-time OAuth setup for Google APIs (Gmail, Drive, Sheets, Calendar, etc.). Creates a new GCP project, enables APIs, configures OAuth consent, and generates client credentials.

**Audience:** User doing this for the first time; assumes Google account but no GCP project.

---

## Step 1: Create a new Google Cloud Project

1. Go to: **https://console.cloud.google.com**
2. Click **"Select a Project"** (top left)
3. Click **"NEW PROJECT"**
4. Name it: `hermes-full-access` (or any descriptive name)
5. Click **CREATE**
6. Wait ~30 seconds for the project to initialise

---

## Step 2: Enable APIs

Enable each API your tool needs. Repeat for each:

1. In the left sidebar, click **"APIs & Services"** → **"Library"**
2. Search for the API name (e.g., "Gmail API")
3. Click the result
4. Click **"ENABLE"**
5. Wait for confirmation

**APIs to enable (by use case):**

| Use Case | APIs |
|----------|------|
| Gmail (read/search/trash) | Gmail API |
| Email sending | Gmail API |
| Google Drive | Google Drive API |
| Google Sheets | Google Sheets API |
| Google Docs | Google Docs API |
| Calendar | Google Calendar API |

---

## Step 3: Configure OAuth Consent Screen

Before creating OAuth credentials, set up the consent screen that users see during authorization.

1. Go to **APIs & Services** → **Credentials** (left sidebar)
2. Click **"CONFIGURE CONSENT SCREEN"** (or **"OAuth consent screen"** tab)
3. Choose user type:
   - **External** = for personal/testing (standard choice)
   - **Internal** = for Google Workspace domains only
4. Click **"CREATE"**

**Fill in the form:**

| Field | Value |
|-------|-------|
| **App name** | `Hermes` (or your agent name) |
| **User support email** | Your Gmail (e.g., `tanzimozer@gmail.com`) |
| **Developer contact** | Your Gmail |

5. Click **"SAVE AND CONTINUE"**

---

## Step 4: Add Scopes to Consent Screen

**On the "Scopes" page:**

1. Click **"ADD OR REMOVE SCOPES"**
2. Search for and **select** each scope you need:
   - `https://www.googleapis.com/auth/gmail.modify` (send, trash, label)
   - `https://www.googleapis.com/auth/gmail.readonly` (read, search)
   - `https://www.googleapis.com/auth/gmail.send` (send only)
   - `https://www.googleapis.com/auth/gmail.labels` (manage labels)
   - `https://www.googleapis.com/auth/calendar`
   - `https://www.googleapis.com/auth/drive`
   - `https://www.googleapis.com/auth/docs`
   - `https://www.googleapis.com/auth/spreadsheets`
3. Click **"UPDATE"**
4. Click **"SAVE AND CONTINUE"**

---

## Step 5: Add Test Users

**On the "Test Users" page:**

1. Click **"ADD USERS"**
2. Enter your Gmail (e.g., `tanzimozer@gmail.com`)
3. Click **"ADD"** (or **"SAVE AND CONTINUE"**)
4. Click **"SAVE AND CONTINUE"**
5. Review the summary and click **"BACK TO DASHBOARD"**

---

## Step 6: Create OAuth Client Credentials

Now generate the actual credentials your tool will use.

1. Go to **APIs & Services** → **Credentials**
2. Click **"+ CREATE CREDENTIALS"** → **"OAuth client ID"**
3. **Application type:** Choose **"Desktop application"** (for local/CLI use)
   - ✗ Web application = for servers with public URLs
   - ✓ Desktop application = for local CLI/terminal tools
4. **Name:** `Hermes CLI` (or similar)
5. Click **"CREATE"**

A popup appears with your credentials:

```
Client ID:     XXXXXXXXXXX-xxxxxxxxxxxxxxxxxxxxxxxx.apps.googleusercontent.com
Client Secret: GOCSPX-xxxxxxxxxxxxxxxxxxxxxxx
```

**Copy both and save them** — you need them for the next step.

6. Click **"OK"** (popup closes)

---

## Step 7: Get the Refresh Token (Authorization Code Flow)

The client ID + secret alone aren't enough — you need a **refresh token** by authorizing once. This is a one-time step.

**In your terminal on the VM (or local machine):**

Replace `CLIENT_ID` in the URL below, then open it in a browser:

```
https://accounts.google.com/o/oauth2/v2/auth?client_id=CLIENT_ID&redirect_uri=http://localhost:8080&response_type=code&scope=https://www.googleapis.com/auth/gmail.modify%20https://www.googleapis.com/auth/gmail.readonly%20https://www.googleapis.com/auth/gmail.send%20https://www.googleapis.com/auth/gmail.labels%20https://www.googleapis.com/auth/calendar%20https://www.googleapis.com/auth/drive%20https://www.googleapis.com/auth/docs%20https://www.googleapis.com/auth/spreadsheets&access_type=offline&prompt=consent
```

**Steps:**

1. Paste the URL into your browser
2. Google prompts you to sign in (if not already)
3. You see a consent screen listing all the scopes you added
4. Click **"Allow"**
5. You're redirected to `http://localhost:8080?code=XXXXX...` — this is the authorization code
6. **Copy the `code` parameter** from the URL (the long string after `code=`)

---

## Step 8: Exchange Code for Tokens

Now exchange the authorization code for access + refresh tokens.

**In your terminal, run:**

```bash
curl -X POST https://oauth2.googleapis.com/token \
  -d "client_id=YOUR_CLIENT_ID" \
  -d "client_secret=YOUR_CLIENT_SECRET" \
  -d "code=AUTHORIZATION_CODE" \
  -d "grant_type=authorization_code" \
  -d "redirect_uri=http://localhost:8080"
```

**Replace:**
- `YOUR_CLIENT_ID` — the client ID from Step 6
- `YOUR_CLIENT_SECRET` — the client secret from Step 6
- `AUTHORIZATION_CODE` — the code from the redirect URL in Step 7

**Response (JSON):**

```json
{
  "access_token": "ya29.a0AT3oNZ98WPK5orz0bQN6rnwoi0N976U4...",
  "expires_in": 3599,
  "refresh_token": "1//065OOPc7KQRTNCgYIARAAGAYSNwF-L9IrhQn56lwRgoRVJ...",
  "scope": "...",
  "token_type": "Bearer"
}
```

**Save these three:**
- `access_token` (expires in ~1 hour, will be refreshed automatically)
- `refresh_token` (long-lived, used to get new access tokens)
- `client_id` + `client_secret` (from Step 6)

---

## Step 9: Store Credentials Securely

Create `~/.hermes/google_oauth_full.json`:

```json
{
  "access_token": "ya29.a0AT3oNZ98WPK5orz0bQN6rnwoi0N976U4...",
  "expires_in": 3599,
  "refresh_token": "1//065OOPc7KQRTNCgYIARAAGAYSNwF-L9IrhQn56lwRgoRVJ...",
  "client_id": "XXXXXXXXXXX-xxxxxxxxxxxxxxxxxxxxxxxx.apps.googleusercontent.com",
  "client_secret": "GOCSPX-xxxxxxxxxxxxxxxxxxxxxxx",
  "token_uri": "https://oauth2.googleapis.com/token",
  "type": "authorized_user",
  "scopes": [
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.labels",
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/docs",
    "https://www.googleapis.com/auth/spreadsheets"
  ]
}
```

**Set permissions:**
```bash
chmod 600 ~/.hermes/google_oauth_full.json
```

---

## Pitfalls

| Problem | Solution |
|---------|----------|
| **Redirect URL mismatch** (400 error) | Must be `http://localhost:8080` in both the GCP console AND the curl command. Check for typos. |
| **"Redirect URI mismatch" in browser** | You didn't save the redirect URL in GCP. Go back to **Credentials** → click the OAuth client → **Redirect URIs** → add `http://localhost:8080` exactly. |
| **"invalid_grant" on token exchange** | Auth code expired (they last ~10 minutes). Re-run the authorization URL and get a fresh code. |
| **"access_denied" on authorization** | You're not a test user. Go back to Step 5 and add your email to the test users list. |
| **403 Forbidden calling the API later** | Scope not enabled. Go back to Step 4 and verify all required scopes are listed. Then refresh the token. |
| **Blank redirect page** | Correct — this is normal for desktop apps. The code is in the URL bar. |

---

## Success

- You have `client_id`, `client_secret`, and `refresh_token`
- Token file exists at `~/.hermes/google_oauth_full.json` with 600 permissions
- Next step: Use the refresh token to fetch fresh access tokens and call the API
