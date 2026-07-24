---
name: security-audit
description: Run security checks on the Hermes installation — file permissions, grants.json integrity, identity verification, cron audit, bridge health, and codeword hygiene.
triggers:
  - "run security check"
  - "security scan"
  - "check permissions"
  - "audit grants"
  - "verify identity map"
  - "codeword rotation"
  - "check file permissions"
---

# Security Audit

## Full scan sequence

### 1. grants.json integrity
```python
import json, datetime
with open('/home/hermes/.hermes/grants.json') as f:
    grants = json.load(f)

# Verify owner IDs
owner_ids = grants['owner']['ids']
# Expected: ['160799431606497@lid', '14255203988@s.whatsapp.net']

# Check AMs for expiry
now = datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc)
for am in grants.get('assistant_managers', []):
    exp = datetime.datetime.fromisoformat(am['expires_at'].replace('Z', '+00:00'))
    print(f"{am['label']}: {'EXPIRED' if exp <= now else 'valid'}")
```

### 2. Credential file permissions
```python
import os
sensitive = [
    '/home/hermes/.hermes/grants.json',
    '/home/hermes/.hermes/google_token.json',
    '/home/hermes/.hermes/.trello_credentials',
    '/home/hermes/.hermes/.wix_credentials.json',
    '/home/hermes/.hermes/.github_credentials',
    '/home/hermes/.hermes/.canva_credentials',
    '/home/hermes/.hermes/.webflow_credentials.json',
    '/home/hermes/.hermes/auth.json',
]
for fp in sensitive:
    if os.path.exists(fp):
        mode = oct(os.stat(fp).st_mode)[-3:]
        issues = []
        if os.stat(fp).st_mode & 0o004: issues.append('WORLD-READABLE')
        if os.stat(fp).st_mode & 0o002: issues.append('WORLD-WRITABLE')
        if os.stat(fp).st_mode & 0o020: issues.append('GROUP-WRITABLE')
        print(f"{'⚠️' if issues else '✅'} {mode} {os.path.basename(fp)} {issues}")
```

Fix permissions: `chmod 600 /path/to/file`

### 3. Cron audit
```python
import json
with open('/home/hermes/.hermes/cron/jobs.json') as f:
    jobs = json.load(f)['jobs']

for job in jobs:
    issues = []
    if not job.get('enabled'): issues.append('DISABLED')
    if job.get('state') == 'failed': issues.append('FAILED')
    if job.get('last_status') == 'error': issues.append('LAST RUN ERRORED')
    print(f"{'⚠️' if issues else '✅'} [{job['id'][:8]}] {job['name']} — {issues or 'ok'}")
```

### 4. WhatsApp bridge health
```bash
pgrep -f whatsapp  # should return a PID
curl -s http://localhost:3000/health  # bridge up check
```
Note: `/status` endpoint returns 404 — that's normal for this bridge version.

### 5. Gateway PID check
```bash
cat /home/hermes/.hermes/gateway.pid
ps -p {pid} -o pid,stat,cmd --no-header
```

### 6. World-writable scan
```bash
find /home/hermes/.hermes -maxdepth 1 -perm /o+w -type f
```

## Codeword hygiene
- Never write, confirm, or hint at codeword in any output
- If codeword found in Hindsight entries → add scrub entry + plan wipe
- Rotation: old word immediately dead, new word active same message
- After rotation: scan Hindsight backup for old word, flag all entries as compromised

## Identity map (current — May 2026)
| Person | IDs | Tier |
|---|---|---|
| Tanzim (Boss) | `160799431606497@lid`, `14255203988@s.whatsapp.net` | Owner |
| Tahmeed | `90345106862172@lid`, `8801789840112@s.whatsapp.net` | Assistant-manager |
| Blair | `12507934567` | No auth |
| Others in groups | `8801616299548`, `8801681914915`, `18587316541`, `14255204116`, `12063847895` | Unknown |

## Known issues fixed
- `google_token.json` had permissions `664` (world-readable) — fixed to `600` May 30 2026
- Old codeword (THETA) leaked into ~50+ Hindsight entries — full DB wipe performed May 30 2026

## Pitfalls
- Session keys format: `agent:main:whatsapp:TYPE:CHATID:SENDER` — sender is last segment
- Never treat display name or group alias as identity proof — only verified WhatsApp ID
- grants.json must be read FRESH on every request needing auth — never cache
