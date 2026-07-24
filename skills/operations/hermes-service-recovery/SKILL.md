---
name: hermes-service-recovery
category: operations
description: "Diagnosing and recovering Hermes infrastructure services — Hindsight, gateway, bridge — when they go down or partially fail."
tags: [hermes, hindsight, infrastructure, ops, recovery, systemd]
triggers:
  - "hindsight offline"
  - "hindsight not running"
  - "memory search failing"
  - "service down"
  - "bridge 401"
  - "run systems diagnostics"
  - "all systems check"
---

# Hermes Service Recovery

## Full Systems Diagnostics — Quick Script

Run this to get a one-shot health picture:

```python
import subprocess, json, os, requests

results = {}

# 1. Hindsight API
try:
    r = requests.get('http://127.0.0.1:9177/health', timeout=3)
    results['hindsight'] = r.json()
except:
    results['hindsight'] = 'UNREACHABLE'

# 2. Systemd user services
r = subprocess.run(['systemctl','--user','list-units','--state=running','--no-pager'], capture_output=True, text=True)
results['services'] = r.stdout.strip()

# 3. Vault
vault_path = os.path.expanduser('~/.hermes/vault.json')
vault_exists = os.path.exists(vault_path)
vault_perms = oct(os.stat(vault_path).st_mode)[-3:] if vault_exists else 'missing'
results['vault'] = f"exists={vault_exists}, perms={vault_perms}"

# 4. Disk
r = subprocess.run(['df','-h','/'], capture_output=True, text=True)
results['disk'] = r.stdout.strip()

# 5. RAM
r = subprocess.run(['free','-h'], capture_output=True, text=True)
results['ram'] = r.stdout.strip()

# 6. WhatsApp bridge
import os
try:
    token = subprocess.run(['grep','WHATSAPP_BRIDGE_TOKEN',os.path.expanduser('~/.hermes/.env')],
                           capture_output=True, text=True).stdout.strip().split('=',1)[1]
    r = subprocess.run(['curl','-s','http://localhost:3000/health',
                        '-H', f'Authorization: Bearer {token}'], capture_output=True, text=True)
    results['whatsapp_bridge'] = r.stdout.strip()
except Exception as e:
    results['whatsapp_bridge'] = f'error: {e}'

# 7. Instagram targets
ig_path = '/tmp/ig_final_v5.json'
if os.path.exists(ig_path):
    import json as _json
    results['ig_targets'] = f"{len(_json.load(open(ig_path)))} targets in /tmp"
else:
    results['ig_targets'] = 'file missing'

for k, v in results.items():
    print(f"\n=== {k.upper()} ===\n{v}")

# 8. IMPORTANT: also run schedule_task(action='list') and scan every job for last_delivery_error
```

Also run `schedule_task action=list` and scan every job for `last_delivery_error` — delivery failures are silent otherwise.

**Expected healthy state:**
- `hermes-gateway.service` — running
- `hindsight.service` — running  
- `friday-voice.service` — running
- `friday-fallback-watchdog.service` — running
- Hindsight health: `{"status":"healthy","database":"connected"}`
- Vault: exists, perms=600
- Disk: <80% used
- RAM: watch if free drops below ~200MB (no swap on this VM)

---

## Hindsight — API Layer Not Running

**Symptom:** `hindsight_recall` / memory search fails with connection refused on port 9177.
Hindsight health check: `curl -s http://127.0.0.1:9177/health` → connection refused or times out.

**Diagnosis:**
```bash
# Check if Postgres is alive (it often is even when API is down)
ps aux | grep postgres | grep -v grep

# Check systemd service status
systemctl --user status hindsight.service

# Check what the daemon itself thinks
~/.hermes/hermes-agent/venv/bin/hindsight-embed -p hermes daemon status
```

**Root cause pattern:** The `hindsight.service` systemd unit starts Postgres (Type=forking) and reports active, but the API layer (`hindsight-embed` process on :9177) didn't come up. `systemctl restart hindsight.service` restarts Postgres but does NOT re-launch the API layer.

**Fix — manual daemon start:**
```bash
~/.hermes/hermes-agent/venv/bin/hindsight-embed -p hermes daemon start
```
Expected output: `✓ Daemon started successfully!` with `Daemon responding` confirmation.
Then verify: `curl -s http://127.0.0.1:9177/health` → `{"status":"healthy","database":"connected"}`

**Do NOT restart the gateway to fix Hindsight** — they are independent processes.

---

## Cron Job Audit — Stale & Dead Jobs

When doing a diagnostics pass, also audit cron jobs for:

1. **Dead group JIDs** (`item-not-found` 401) — test each WhatsApp group target with the bridge directly
2. **Duplicate jobs** — same schedule + same group = two messages land at once. Kill the older one.
3. **Stale one-shot jobs** — completed `repeat: 0/N` jobs that are `state: completed` can be removed for hygiene
4. **Jobs that will fail** — if Instagram session is checkpointed, any IG automation job scheduled that day should be removed immediately rather than left to fail

**Quick audit pattern:**
```python
# After schedule_task(action='list'), scan for issues:
for job in jobs:
    if job.get('last_delivery_error'):
        print(f"⚠️  {job['name']}: {job['last_delivery_error'][:80]}")
    if job.get('state') == 'completed':
        print(f"🗑️  Completed: {job['name']} — safe to remove")
```

---

## WhatsApp Bridge — 401 Errors on Cron Jobs

**Symptom:** Cron jobs show `delivery error: WhatsApp bridge error (401): {"error":"Unauthorized"}`.

**Step 1 — Check bridge health (no auth needed):**
```bash
curl -s http://localhost:3000/health
# Good: {"status":"connected","queueLength":0,"uptime":...}
# Bad: connection refused → bridge process is actually down
```

**Step 2 — If bridge is healthy, 401 = wrong/missing auth token.** Test with token:
```bash
TOKEN=$(grep WHATSAPP_BRIDGE_TOKEN ~/.hermes/.env | cut -d= -f2)
curl -s -X POST http://localhost:3000/send \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"chatId":"TARGET_GROUP_JID@g.us","message":"test"}'
```

**Step 3 — If auth works but get `item-not-found`:** The group JID is dead (account removed from group, or group deleted). Find the correct live group via `send_message action=list`, test each candidate, update the cron job `deliver` target.

**Field names:** `chatId` (not `to`), `message`. Getting `chatId and message are required` = you used `to`.

**Cron job 401 does NOT mean the bridge is down** — it almost always means a stale group JID.

---

## Gateway — Not Responding

**⚠️ NEVER restart bridge.js directly.** See the system prompt operational rules.

If `hermes-gateway.service` is the issue:
```bash
systemctl --user status hermes-gateway.service
systemctl --user restart hermes-gateway.service
```

Gateway restart is safe. Bridge restart is not — it's managed as a child of the gateway.

---

## Pitfalls

- **`systemctl restart hindsight.service` does not fix the API layer** — only `hindsight-embed daemon start` does
- **Cron 401 ≠ bridge down** — always health-check first, then test with token
- **Hindsight Postgres running ≠ Hindsight working** — the API server is a separate process on :9177
- **RAM pressure watch:** On the 5.8G VM, if free RAM drops below ~200MB with no swap, services can start failing silently. `free -h` is the quick check.
