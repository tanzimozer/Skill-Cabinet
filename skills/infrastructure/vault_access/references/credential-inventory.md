# Credential Inventory & Audit Workflow

## When to Run This

Run a full credential audit when:
- Setting up a new environment or migrating credentials
- Onboarding a new service (Slack, AWS, etc.)
- Troubleshooting integration failures
- Quarterly maintenance (check expiry, refresh tokens)
- User asks "what do I have access to?" or "what credentials are set up?"

## Audit Workflow

### Phase 1: Discovery
```bash
# Check all known vault locations
ls -la ~/.hermes/vault.json
ls -la ~/.hermes/.edith/edith_vault.json
ls -la ~/.hermes/google_token.json
ls -la ~/.hermes/.edith/google_oauth_vault
ls -la ~/.hermes/.edith/github_pat_vault

# Find environment credential variables
env | grep -i 'api\|token\|secret\|key\|pass\|auth\|credential'

# Check config files
cat ~/.bashrc | grep -i 'api\|token'
cat ~/.zshrc | grep -i 'api\|token'
```

### Phase 2: Extraction

Read the main vault (plaintext, but sensitive):
```python
import json

with open('/home/hermes/.hermes/vault.json') as f:
    vault = json.load(f)

# List all services and their keys
for service, creds in vault.items():
    if service != '_meta':
        print(f"\n{service.upper()}")
        for key in creds.keys():
            if key in ['token', 'api_key', 'access_token', 'refresh_token', 'app_password']:
                print(f"  {key}: [REDACTED, {len(creds[key])} chars]")
            else:
                print(f"  {key}: {creds[key]}")
```

### Phase 3: Status Check

For each credential, determine:
1. **Location:** Where is it stored? (vault.json, env var, EDITH, file)
2. **Status:** Active, expired, encrypted, missing?
3. **Last verified:** When was it last used/confirmed?
4. **Expiry:** Does it have a known expiration date or rotation cycle?

Use this template:

| Service | Have | Location | Status | Expiry | Last Verified | Action |
|---------|------|----------|--------|--------|---------------|--------|
| Google (Sheets) | ✅ | google_token.json | Active | ~90 days | June 9, 2026 | Test Sheets API call |
| GitHub PAT | ✅ | EDITH vault | Encrypted | ~May 2025 (>1yr old) | Unknown | Decrypt & check age |
| Instagram | ✅ | vault.json | Active | 7–14 days | June 4, 2026 (stale) | Test enrich endpoint |
| iCloud | ✅ | vault.json | Active | Manual | Unknown | Test IMAP connection |
| Webflow | ✅ | vault.json | Active | Annual | Unknown | Check API response |
| Slack | ❌ | Missing | N/A | N/A | N/A | Generate if needed |

### Phase 4: Document & Store

Create a running log on the user's desktop (or persistent location):
- `~/Desktop/CREDENTIALS_MASTER.md` — living document updated as credentials are added/refreshed
- Timestamp every credential with "verified on [date]"
- Mark status: Active, Expired, Pending, Error

## Service-Specific Refresh Cycles

| Service | Refresh Interval | How to Refresh | Notes |
|---------|------------------|----------------|-------|
| Google OAuth | 90 days (auto-refresh) | Token auto-refreshes; full re-auth if scope changes | If invalid_scope: delete token file and re-auth |
| GitHub PAT | Annual (manual) | Visit github.com/settings/tokens; create new, revoke old | Check creation date; rotate if >11 months old |
| Instagram Cookies | 7–14 days | Re-paste from browser (Cookie-Editor extension) | If enrich blocked: use different browser (Firefox/Edge) |
| iCloud App Password | Manual (no expiry) | Update only if account settings change or if access denied | Monitor IMAP connection; re-set if locked out |
| Webflow API | Annual (manual check) | Visit webflow.com/dashboard; check if still valid | No auto-expiry; verify with test API call |
| Wix API | Manual (no known expiry) | Check Wix dashboard; rotate if suspected compromise | Monitor for suspicious activity |
| WhatsApp Bridge | Manual (check quarterly) | Verify bridge is still responding; ask WhatsApp if revoked | Monitor for message failures |
| Slack Bot | Annual (best practice) | Visit workspace → Settings → Bots; rotate if compromised | Generate new token, update vault, revoke old |
| AWS Credentials | 90 days (best practice) | IAM console; create new access key, revoke old | Delete old credentials from vault once verified new ones work |

## Expiry Monitoring (Quarterly Calendar)

Set reminders for:
- **May (annual):** GitHub PAT rotation, Webflow token check, AWS credentials review
- **Q2, Q3, Q4:** General audit (check Instagram cookies, test Slack/WhatsApp connections)
- **On-demand:** When a credential fails or service integration breaks

## EDITH Vault Access (Encrypted)

Some credentials are stored in `~/.hermes/.edith/edith_vault.json` (AES-256-GCM encrypted). To decrypt:

1. You need three factors:
   - Hardware UUID (automatic, read from `~/.hermes/.edith/hardware_uuid`)
   - Passphrase (bcrypt-10 hashed at `~/.hermes/.edith/passphrase_hash`)
   - Security question answer (time-gated, ±5 min from last auth)

2. Existing implementation gap (as of June 2026): No automated decrypt utility exposed to the agent. Workaround: use `vault_access` skill and fall back to main `vault.json` for most services.

3. Services in EDITH:
   - GitHub PAT (Friday-EDITH)
   - Encrypted backups of OAuth tokens

## Credential Rotation SOP (Step-by-step)

**Example: GitHub PAT rotation**

1. Generate new token on GitHub (Settings → Developer settings → Personal access tokens)
2. Copy the new token
3. Update vault entry:
   ```python
   vault['github']['pat'] = 'new_token_here'
   vault['github']['created'] = '2026-06-09'
   vault['github']['rotated_from'] = 'old_token_id'
   ```
4. Test with `curl -H "Authorization: token [new]" https://api.github.com/user`
5. If test passes: revoke old token on GitHub
6. Document in CREDENTIALS_MASTER.md: "GitHub PAT rotated June 9, 2026"

## Desktop File Structure (Tanzim's preference)

Credentials are logged on desktop in `CREDENTIALS_MASTER.md`:
- **Format:** Markdown table with Service, Token Value (or [REDACTED]), Status, Last Verified
- **Updates:** Add timestamps whenever a credential is added or refreshed
- **Backups:** Main vault remains encrypted; desktop file is a running log
- **Never commit:** Keep desktop file out of Git — it contains live credentials

## Common Failures & Fixes

| Error | Cause | Fix |
|-------|-------|-----|
| `invalid_scope: Bad Request` | Scope mismatch between token and client_id | See google-oauth-scope-troubleshooting.md |
| `401 Unauthorized` | Token expired or revoked | Re-authenticate; check expiry date |
| `403 Forbidden` | Token is valid but lacks required scope | Check scopes; re-auth if needed |
| `429 Too Many Requests` | Rate limited | Implement exponential backoff; use batch operations with delays |
| Instagram enrich returns HTML (not JSON) | Device fingerprint blocked (datr cookie stale or flagged) | Refresh cookies from different browser (Firefox/Edge if Chrome blocked) |
| IMAP connection fails | App password wrong or account locked | Re-set app password in iCloud settings |

## Files to Keep Updated

- `~/Desktop/CREDENTIALS_MASTER.md` — running log (user preference)
- `~/.hermes/vault.json` — main credentials vault (plaintext, 600 permissions)
- `~/.hermes/.edith/edith_vault.json` — encrypted backup (EDITH 3-factor auth)
- `~/.hermes/google_token.json` — primary Google OAuth token (if Sheets needed)
