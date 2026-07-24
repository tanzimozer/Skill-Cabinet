# Tanzim's Connected Services — Auth Map

Tanzim gets frustrated when asked to re-explain connections that are already set up.
**Check here first before asking him for credentials.**

## Google (OAuth)
- Token: `~/.hermes/google_token.json`
- Scopes: calendar, drive, gmail.modify, spreadsheets
- Accounts: tanzim.seattle@gmail.com, tanzim.ozer@gmail.com
- Client secret: `~/.hermes/google_client_secret.json`

## Instagram
- Session cookies from Cookie-Editor (Chrome extension, cgagnier, blue icon)
- Export: open instagram.com → Cookie-Editor → Export → plain JSON
- Previous sessions get flagged on per-user enrich endpoint (/api/v1/users/{uid}/info/) after heavy use
- Tag fetch endpoint (/api/v1/tags/{tag}/sections/) stays live longer
- Fresh cookies needed when enrich returns HTML 200 or feedback_required/is_spam

## iCloud
- Creds: `~/.hermes/icloud_creds.json`

## Rule
Do NOT ask Tanzim for credentials without first checking this file and the token files on disk.
If auth is broken, diagnose the specific failure before surfacing it to him.
