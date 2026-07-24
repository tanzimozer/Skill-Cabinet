# Google OAuth Scopes Reference

## Common Scopes (Full URIs for space-separated strings)

### Gmail
- `https://www.googleapis.com/auth/gmail.readonly` — Read-only access to Gmail inbox
- `https://www.googleapis.com/auth/gmail.modify` — Full read/write/delete access to Gmail

### Google Sheets
- `https://www.googleapis.com/auth/spreadsheets` — Full Sheets API access (read, write, create)
- `https://www.googleapis.com/auth/spreadsheets.readonly` — Read-only Sheets access

### Google Drive
- `https://www.googleapis.com/auth/drive` — Full Drive access (broad; usually overkill)
- `https://www.googleapis.com/auth/drive.readonly` — Read-only Drive access
- `https://www.googleapis.com/auth/drive.file` — Limited to files created/opened by app

### Google Docs
- `https://www.googleapis.com/auth/documents` — Google Docs API access (NOT 'docs')

### User Info
- `https://www.googleapis.com/auth/userinfo.email` — User's email address
- `https://www.googleapis.com/auth/userinfo.profile` — User's profile info (name, photo, etc.)

## Common Mistakes

| Mistake | Correct |
|---------|---------|
| `'docs'` | `'https://www.googleapis.com/auth/documents'` |
| Comma-separated scopes | Space-separated scopes |
| Partial URI like `gmail.readonly` | Full URI: `https://www.googleapis.com/auth/gmail.readonly` |
| `spreadsheets.readonly` without full URI | `https://www.googleapis.com/auth/spreadsheets.readonly` |

## Scope Incremental Addition Pattern

If you start with `gmail.readonly` and later need `spreadsheets`:
1. Do NOT add them to the same token by making separate requests
2. Generate a NEW auth URL with BOTH scopes space-separated
3. User re-authorizes (sees all requested permissions)
4. Exchange the code for a single token with both scopes
5. Store the new token (refresh_token overwrites old if present)

Example scope string for both:
```
https://www.googleapis.com/auth/gmail.modify https://www.googleapis.com/auth/spreadsheets
```
