# EDITH Credential Routing Map

Reference for Upgrade 4 (EDITH Fast-Path). Shows how to structure the credentials index in persistent memory WITHOUT storing raw secrets.

## Principle: Secrets Stay in EDITH, Instructions Stay in Memory

**Memory stores:** Routing instructions only  
**EDITH vault stores:** Actual credentials, encrypted

Example:
```
Memory (persistent): 
  "gmail": "Lookup EDITH.credentials.google_oauth → validate refresh token → auto-refresh if expiry < 7 days"

EDITH vault (~/.hermes/edith/edith_vault.json):
  {
    "credentials": {
      "google_oauth": {
        "access_token": "ya29...",
        "refresh_token": "1//0gP...",
        "expiry": "2026-06-15T00:27:00Z"
      }
    }
  }
```

## Routing Map Template

Structure for persistent memory, Layer 2 (Credentials Index):

```json
{
  "routing_map": {
    "google_oauth": {
      "service_index": "indexed_service_0",
      "lookup_instruction": "Query EDITH.credentials.google_oauth → validate refresh token present → check expiry → auto-refresh if < 7 days → inject into gmail-automation skill",
      "scopes": ["gmail.modify", "gmail.readonly", "gmail.send", "calendar", "drive", "spreadsheets", "documents"],
      "refresh_schedule": "0 5 * * *",
      "fallback": "disk read from ~/.hermes/google_token.json (legacy; deprecate)"
    },
    "github_pat": {
      "service_index": "indexed_service_1",
      "lookup_instruction": "Query EDITH.credentials.github_pat → validate token present → check expiry → alert if < 14 days → inject into github-ops-skill",
      "scopes": ["repo", "gist", "user"],
      "refresh_schedule": "manual (no auto-refresh for PAT)",
      "fallback": "disk read from ~/.hermes/.github_credentials (legacy)"
    },
    "icloud": {
      "service_index": "indexed_service_2",
      "lookup_instruction": "Query EDITH.credentials.icloud → validate app_password present → test IMAP port 993 reachability → inject into email-sync-skill",
      "scopes": ["imap", "smtp"],
      "refresh_schedule": "manual (password-based, no token refresh)",
      "fallback": "prompt user for credentials (requires 2FA)"
    },
    "instagram": {
      "service_index": "indexed_service_3",
      "lookup_instruction": "Query EDITH.credentials.instagram → validate session_id present → check age (< 7 days) → if stale, prompt for re-auth → inject into instagram-automation skill",
      "scopes": ["read:profile", "read:media", "insights:read"],
      "refresh_schedule": "manual (session-based; re-auth when stale)",
      "fallback": "prompt user for Instagram login (browser-based 2FA flow)"
    }
  },
  "access_control": {
    "rule": "All credential lookups must route through this map",
    "enforcement": "If raw credential access attempted (direct disk read, unencrypted), log security event and deny",
    "validation": "On every lookup, verify EDITH 3-factor auth passes before returning credentials"
  }
}
```

## Lookup Flow Diagram

```
User request: "Check Gmail"
    ↓
Agent detects keyword "gmail"
    ↓
Agent queries persistent memory: "routing_map['google_oauth']"
    ↓
Memory returns: {
  "lookup_instruction": "Query EDITH.credentials.google_oauth → ...",
  "scopes": [...],
  "service_index": "indexed_service_0"
}
    ↓
Agent runs lookup_instruction:
  1. Open EDITH vault (3-factor auth required)
  2. Fetch credentials under "credentials.google_oauth"
  3. Validate refresh_token exists
  4. Check expiry field
  5. If expiry within 7 days, auto-refresh
  6. Return access_token + scope list
    ↓
Agent injects token into gmail-automation skill
    ↓
Skill invokes, returns results
    ↓
Total cost: ~40 tokens (vs. ~150 before EDITH fast-path)
```

## Per-Service Details

### Google OAuth (indexed_service_0)
**Key files:** `~/.hermes/google_token.json` (legacy), `~/.hermes/edith/edith_vault.json` (new)

**Structure in EDITH:**
```json
{
  "credentials": {
    "google_oauth": {
      "client_id": "313611152308-...",
      "client_secret": "GOCSPX-...",
      "access_token": "ya29...",
      "refresh_token": "1//0gP...",
      "expiry": "2026-06-15T00:27:00Z",
      "token_uri": "https://oauth2.googleapis.com/token",
      "scopes": ["gmail.modify", "gmail.readonly", "gmail.send", "calendar", "drive", "spreadsheets", "documents"]
    }
  }
}
```

**Auto-refresh schedule:** 5 AM PDT daily (cron `0 5 * * *`)  
**Validation:** Verify Calendar API is enabled in Google Cloud Console (not just in token scopes)

### GitHub PAT (indexed_service_1)
**Key files:** Stored in EDITH only (no fallback)

**Structure in EDITH:**
```json
{
  "credentials": {
    "github_pat": {
      "token": "ghp_...",
      "token_name": "Friday-EDITH",
      "scopes": ["repo", "gist", "user"],
      "expiry": "2027-06-09T00:00:00Z",
      "repositories": ["tanzimozer/Tanzim_Frameworks", "tanzimozer/IG-Hunter", "tanzimozer/TERRAjob"]
    }
  }
}
```

**Refresh:** Manual (GitHub PATs don't auto-rotate). Set calendar alert 2 weeks before expiry.

### iCloud (indexed_service_2)
**Key files:** EDITH (primary), app password in 1Password or similar (backup)

**Structure in EDITH:**
```json
{
  "credentials": {
    "icloud": {
      "email": "tanzimx@icloud.com",
      "app_password": "xxxx-xxxx-xxxx-xxxx",
      "imap_server": "imap.mail.me.com",
      "imap_port": 993,
      "smtp_server": "smtp.mail.me.com",
      "smtp_port": 587
    }
  }
}
```

**Refresh:** Manual (iCloud app passwords don't expire unless revoked)  
**Validation:** Test IMAP connection on each lookup (port 993, TLS required)

### Instagram (indexed_service_3)
**Key files:** EDITH (session credentials), fallback to browser-based 2FA

**Structure in EDITH:**
```json
{
  "credentials": {
    "instagram": {
      "username": "tanzim.seattle",
      "session_id": "...",
      "user_id": "12345...",
      "session_created": "2026-06-14T00:00:00Z",
      "session_age_days": 0,
      "backup_credentials": {
        "password_stored_elsewhere": "See 1Password vault 'Social'"
      }
    }
  }
}
```

**Refresh:** Session-based (Instagram sessions expire after ~7 days of inactivity)  
**On stale:** Prompt user for re-auth or trigger browser login flow

## Cost Comparison

### Before (Credential Lookup Cost)
```
Disk read (~/.hermes/google_token.json):     20 tokens
JSON parse:                                   20 tokens
Token validation (check expiry, scopes):      50 tokens
Refresh logic (if needed):                    60 tokens
────────────────────────────────────────────
Total per lookup:                            150 tokens

If 5 lookups/day × 150 tokens = 750 tokens/day
If 30 days: 750 × 30 = 22,500 tokens/month (~$13.50/month)
```

### After (EDITH Fast-Path)
```
Memory index lookup:                          10 tokens
EDITH vault open (3-factor):                  10 tokens
Token validation:                             15 tokens
Refresh logic (if needed):                     5 tokens (cached)
────────────────────────────────────────────
Total per lookup:                             40 tokens

If 5 lookups/day × 40 tokens = 200 tokens/day
If 30 days: 200 × 30 = 6,000 tokens/month (~$3.60/month)

Savings: 22,500 - 6,000 = 16,500 tokens/month (~$9.90/month)
```

## Migration Checklist

- [ ] Create EDITH vault structure (`~/.hermes/edith/edith_vault.json`)
- [ ] Migrate all credentials from legacy vaults into EDITH
- [ ] Create routing_map in persistent memory (DO NOT include raw credentials)
- [ ] Test each lookup: memory → EDITH → validation → injection → skill invocation
- [ ] Verify EDITH 3-factor auth works (UUID + passphrase + security questions)
- [ ] Set up auto-refresh cron job (5 AM PDT for Google OAuth)
- [ ] Deprecate legacy vault files (keep as read-only backup for 1 month)
- [ ] Monitor: confirm all credential lookups route through EDITH (zero direct disk reads)
- [ ] Validate cost reduction (measure tokens/month for 2 weeks, compare to baseline)
