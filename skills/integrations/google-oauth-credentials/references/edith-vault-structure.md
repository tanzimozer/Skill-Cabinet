# EDITH Vault Structure & Google OAuth Storage

## Location
`~/.hermes/.edith/edith_vault.json`

## Content (example)
```json
{
  "google_oauth": {
    "service": "google_oauth",
    "scopes": ["gmail", "drive", "docs", "sheets", "chat"],
    "access_token": "ya29.a0AT3oNZ8uFZKeEAe4sDB9j_J1HBI1NGzZaaXeABTkbFR...",
    "refresh_token": "1//060n2osCAJ8PgCgYIARAAGAYSNwF-L9Ir3d_ffXubcIzpXT...",
    "expires_in": 3599,
    "token_type": "Bearer"
  },
  "github_pat": {
    "service": "github",
    "account": "tanzimozer",
    "token_type": "personal_access_token",
    "token": "ghp_as...GMFF",
    "scopes": ["repo", "gist", "user"]
  }
}
```

## Key Distinction: Vault vs. Plain JSON

| Aspect | EDITH Vault | Plain JSON File |
|--------|-------------|-----------------|
| **Location** | `~/.hermes/.edith/edith_vault.json` | `~/.hermes/google_oauth_full.json` |
| **Scopes** | Full (gmail, drive, docs, sheets, chat) | Subset (gmail, spreadsheets) |
| **Freshness** | Updated after each re-auth | May be stale |
| **Use in code** | ✓ Load this first | ✗ Fallback only |
| **Trust level** | Authoritative | Legacy/partial |

## When to Update Vault

After successful re-authorization (getting new access + refresh tokens), write the new tokens back to EDITH Vault immediately so:
1. Future sessions have the fresh tokens
2. Vault remains the single source of truth
3. You don't need to re-auth again next session

## Diagnostic: Check Current Scopes

Read the **Credentials** Google Sheet:
- **Sheet ID:** `1QtHeLtYqd21fGWY0FwRqxGgodYgj-rXnM7mXT9MzzLw`
- **Tab:** "Authentication"
- Lists all services, scopes, status, and locations

This sheet is the human-readable audit trail of what's currently authorized.
