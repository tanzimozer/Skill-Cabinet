---
name: linux-system-security-hardening
description: >
  Audit and harden a Linux-based AI agent host (Hermes VM / Mac Mini setup).
  Covers vulnerability assessment from an attacker's perspective, then
  systematic remediation of findings. Ordered by impact.
tags: [security, linux, hardening, audit, permissions]
---

# Linux System Security Hardening

## When to use
- User requests a security audit or diagnostics
- Post-setup or post-migration hardening pass
- Any time a new service or port is added to the stack

## Autonomy note
Tanzim delegates this class of work fully. Once codeword is given, proceed to
completion without asking for per-fix permission. Report a consolidated scorecard
at the end.

---

## Phase 1 — Recon / Audit

Run these before touching anything:

```bash
# Open ports — flag anything on 0.0.0.0 that shouldn't be public
ss -tlnp

# Running processes with network exposure
ps aux | grep -E 'python|node|uvicorn|gunicorn|fastapi'

# File permission problems (group/world-readable sensitive files)
find ~/.hermes -maxdepth 3 -not -path '*/venv/*' -not -path '*/node_modules/*' \
  \( -perm -g+r -o -perm -o+r \) -type f 2>/dev/null

# Secrets in config
grep -n "redact_secrets\|INSECURE\|webhook.*secret\|secret.*webhook" ~/.hermes/config.yaml

# .env permissions
ls -la ~/.hermes/.env
```

Rank findings: 🔴 CRITICAL → 🟠 HIGH → 🟡 MEDIUM → 🔵 LOW

---

## Phase 2 — Remediation Checklist

### 2.1 Webhook / gateway secret
- Location: `~/.hermes/config.yaml` → `platforms.webhook.extra.secret`
- Fix: Replace placeholder with `python3 -c "import secrets; print(secrets.token_hex(32))"`
- Default placeholder to watch for: `INSECURE_NO_AUTH`

### 2.2 Secret redaction
- Location: `~/.hermes/config.yaml` → `security.redact_secrets`
- Fix: Set to `true`

### 2.3 Services binding on 0.0.0.0
- Audit: `ss -tlnp | grep "0.0.0.0"`
- Fix per service type:
  - **FastAPI/uvicorn** (e.g. voice_server.py): change `host="0.0.0.0"` → `host="127.0.0.1"` in the `uvicorn.run()` call, then restart the background process
  - **Node/Express**: change `app.listen(PORT, '0.0.0.0', ...)` → `app.listen(PORT, '127.0.0.1', ...)`
- After patching, kill old PID and restart as `terminal(background=True)`

### 2.4 Session file permissions
```bash
chmod 600 ~/.hermes/sessions/*.jsonl ~/.hermes/sessions/*.json 2>/dev/null
```
Default is `664` (group+world readable) — always tighten after setup.

### 2.5 Bearer token auth on internal HTTP bridges

**Pattern** (WhatsApp bridge or similar Express service):
1. Generate token: `python3 -c "import secrets; print(secrets.token_hex(32))"`
2. Append to `~/.hermes/.env`: `echo 'SERVICE_TOKEN=<token>' >> ~/.hermes/.env`
3. Add middleware to the Express app **after** any existing host-validation middleware, **before** route handlers:

```js
const SERVICE_TOKEN = process.env.SERVICE_TOKEN || '';
app.use((req, res, next) => {
  if (req.path === '/health') return next();   // liveness exempt
  if (!SERVICE_TOKEN) return next();           // dev mode fail-open
  const auth = req.headers['authorization'] || '';
  const token = auth.startsWith('Bearer ') ? auth.slice(7) : '';
  if (token !== SERVICE_TOKEN) return res.status(401).json({ error: 'Unauthorized' });
  next();
});
```

4. On the Python client side, read the token from env and inject as a header dict:

```python
_token = os.getenv("SERVICE_TOKEN", "")
self._auth_headers: dict = (
    {"Authorization": f"Bearer {_token}"} if _token else {}
)
```

5. Pass `headers=self._auth_headers` to every `aiohttp` POST/GET call targeting the bridge.
6. Restart the bridge process and smoke-test:
   - Unauthenticated request → expect `401`
   - `/health` unauthenticated → expect `200`

### 2.6 Directory permissions
```bash
# Sensitive config dirs should be 700, files 600
chmod 700 ~/.hermes/hindsight
chmod 600 ~/.hermes/hindsight/config.json
chmod 600 ~/.hermes/.env       # should already be 600
chmod 600 ~/.hermes/google_token.json
```

---

## Phase 3 — Verification

```bash
# Confirm no 0.0.0.0 exposure remains
ss -tlnp | grep "0.0.0.0"

# Confirm session files locked
ls -la ~/.hermes/sessions/*.jsonl | awk '{print $1}' | sort -u

# Smoke test bridge auth
curl -s -o /dev/null -w "%{http_code}" -X POST http://127.0.0.1:<PORT>/send \
  -H "Content-Type: application/json" -d '{"test":"test"}'
# expect: 401

curl -s http://127.0.0.1:<PORT>/health
# expect: 200 / {"status":"connected",...}
```

---

## Known gaps / out-of-scope

- **Hindsight API (port 9177)** — `hindsight-api` binary has no `--api-key` auth flag.
  It's localhost-only so risk is limited to local process compromise.
  Proper fix: put a lightweight auth proxy (nginx/caddy) in front, or patch the binary source.
  Tracked as a known gap until resolved.

- **SSH (port 22)** — open on `0.0.0.0` by design; mitigate via `~/.ssh/authorized_keys`
  + `PasswordAuthentication no` in `/etc/ssh/sshd_config`.

- **Prompt injection via WhatsApp** — architectural risk; no code fix available.
  Mitigated by identity tier system in grants.json. Document, don't panic.

---

## References
- `references/hardening-session-may2026.md` — full vulnerability list from the May 30 audit
