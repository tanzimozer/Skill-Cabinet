# MAGPROD_ENGINE Daily Backup

**When to use:** Daily cron or manual run to verify MAGPROD_ENGINE Google Drive folder health and access security.

**Script:** `~/.hermes/scripts/magprod_backup.py`

**What it does:**
1. Lists all files/subfolders in MAGPROD_ENGINE (Drive folder ID: `1OcieuCvhSiEjEzYcdepd2IJxlEagKUKt`)
2. Recursively checks permissions on all items
3. Flags public access (`type: anyone`) or unauthorised user shares
4. Returns status: OK / ERROR / SECURITY_ALERT

**Run:**
```bash
python3 ~/.hermes/scripts/magprod_backup.py
```

**Authorized users (per script):** `tanzim` and `timbr.mustafa@gmail.com` (Towsif)
- Note: cron job brief says "only Tanzim" — if Towsif access is ever revoked, update `AUTHORIZED_USERS` in the script accordingly.

**Pitfalls:**
- Requires valid `~/.hermes/google_token.json` with Drive read + permissions scope
- Permission check silently skips files it can't read perms on (try/except pass) — doesn't flag these as errors
- Security check recurses into subfolders but not infinitely — deeply nested structures may be missed
