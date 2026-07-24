# GitHub PAT Vault Lifecycle

**Problem:** When GitHub PATs are rotated (old one deleted, new one created), the vault.json can get out of sync. If you try git clone with a stale PAT, it fails silently with "could not read Password" or "repository not found" — indistinguishable from a real repo that doesn't exist.

## Current Active PAT (June 9, 2026)

- **Token:** `<GITHUB_PAT — see ~/.hermes/vault.json:github_token>`
- **Scopes:** repo, gist, user
- **Expiry:** June 9, 2027
- **Status:** Active (verified working)
- **Location in vault:** `vault['github']['pat']`

## Verification Checklist

Before any git clone or bulk GitHub operations:

1. **Check vault contains the active PAT:**
   ```bash
   python3 -c "import json; v=json.load(open('/home/hermes/.hermes/vault.json')); print(f\"Vault PAT: {v['github']['pat'][:10]}...\")"
   ```

2. **Check Desktop credentials master for source of truth:**
   - File: `~/Desktop/CREDENTIALS_MASTER.md`
   - Section: "GITHUB PAT (Active)"
   - If mismatch, update vault with the master file value

3. **Test PAT is active:**
   ```bash
   TOKEN=$(python3 -c "import json,os; print(json.load(open(os.path.expanduser('~/.hermes/vault.json')))['github']['pat'])")
   curl -s -H "Authorization: token $TOKEN" https://api.github.com/user | grep login
   ```
   If this fails (no login output), the PAT is invalid or expired.

## When PAT is Rotated

1. Generate new PAT on GitHub (tanzimozer account)
2. Update `~/.hermes/vault.json` → `github.pat`
3. Update `~/Desktop/CREDENTIALS_MASTER.md` → "GITHUB PAT (Active)" section
4. Test immediately with `curl` check above
5. Revoke old PAT on GitHub

## Stale PAT Signals

- `git clone` returns "could not read Password for 'https://TOKEN@github.com'"
- `git clone` returns "repository not found" (but repo actually exists)
- API calls return 401 Unauthorized
- `curl` test with PAT returns empty or error

**Action:** Check Desktop master file, update vault, test with curl, retry clone.

## Location of Truth

1. **Source of truth:** `~/Desktop/CREDENTIALS_MASTER.md` (kept up to date manually + by CI if available)
2. **Working copy:** `~/.hermes/vault.json` (must sync with master)
3. **Reference:** This file (patterns and lifecycle)

If vault and master disagree, master wins — update vault from master and test immediately.
