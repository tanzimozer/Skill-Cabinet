---
name: hermes-gateway-diagnostics
description: Diagnose and recover from Hermes gateway/WhatsApp bridge failures — not responding, crashed, new groups not picked up, or sender access blocked.
triggers:
  - Friday is not responding in a WhatsApp group
  - Friday is not responding to DMs from specific people
  - WhatsApp bridge appears down or disconnected
  - A new WhatsApp group was created and Friday doesn't respond in it
  - User reports Friday went silent after a period of activity
  - Gateway crash or restart loop suspected
  - Someone texts Friday and gets no reply (access/allowlist issue)
---

# Hermes Gateway Diagnostics

## What this covers
Triaging why the Hermes gateway or WhatsApp bridge is not responding — including crashes, restarts, and failure to pick up new groups.

## Step 1 — Quick health check
```bash
hermes status
```
Check:
- Gateway Service: running (and PID)
- WhatsApp: configured
- Note the restart counter if visible

## Step 2 — Deep diagnostics
```bash
hermes doctor
```
Watch for:
- WhatsApp bridge npm vulnerabilities (non-critical but flag it)
- Any tool availability failures that could affect response

## Step 3 — Read the logs
```bash
journalctl --user -u hermes-gateway -n 50 --no-pager
```
Key error patterns to look for:
- `WhatsApp bridge process exited unexpectedly (code -15)` — bridge was killed (usually a drain timeout)
- `Gateway drain timed out` — gateway was overloaded and killed a running agent
- `No response from provider for 180s` — Anthropic API timeout, triggered reconnect
- `SSL record layer failure` — transient SSL error, retried automatically
- `Scheduled restart job, restart counter is at N` — gateway auto-restarted N times

## Step 4 — Check config for mention behavior
```bash
cat ~/.hermes/config.yaml | grep -A5 whatsapp
```
Confirm `require_mention: true` is set if you only want responses on @-tags.

## Step 5 — Check sender/DM access controls (if gateway is up but ignoring specific senders)

The gateway may be running fine but silently dropping messages from certain people. Key config lives in `~/.hermes/.env`:

```bash
cat ~/.hermes/.env | grep -i whatsapp
```

Relevant env vars:
- `WHATSAPP_ALLOWED_USERS` — comma-separated phone numbers (with country code, e.g. `14255203988`) allowed to message Friday. If set, anyone not on this list is silently dropped at the bridge level — the Python gateway never even sees the message.
- `WHATSAPP_ALLOW_ALL_USERS=true` — **WARNING: as of April 2026, this flag is NOT read by `bridge.js`**. Setting it has no effect. The only way to allow additional users is to add them to `WHATSAPP_ALLOWED_USERS`.

**CRITICAL PITFALL:** The bridge JS (`bridge.js`) reads `WHATSAPP_ALLOWED_USERS` directly and drops non-matching senders with `allowlist_mismatch` before any Python code runs. `WHATSAPP_ALLOW_ALL_USERS` is only checked by the Python layer (if at all) — it does NOT bypass the bridge-level filter. This means gateway logs will show no "inbound message" entries for blocked senders — the drop is invisible.

To confirm a drop is happening at the bridge level:
```bash
# Enable bridge debug logging temporarily
sed -i 's/WHATSAPP_DEBUG=false/WHATSAPP_DEBUG=true/' ~/.hermes/.env
# Then restart and watch journalctl for "allowlist_mismatch" events
journalctl --user -u hermes-gateway -f --no-pager
```

**Fix for "others can't message Friday":** Add their phone number (with country code, no +) to `WHATSAPP_ALLOWED_USERS` in `.env`, comma-separated. Example:
```
WHATSAPP_ALLOWED_USERS=14255203988,14255209999
```
Then restart the gateway. Do NOT rely on `WHATSAPP_ALLOW_ALL_USERS=true` — it doesn't work at the bridge layer.

Config knobs in `~/.hermes/config.yaml` (under the `whatsapp:` section):
- `dm_policy: "open" | "allowlist" | "disabled"` — controls DM access (default: `"open"`)
- `allow_from: [list]` — sender IDs allowed when `dm_policy: allowlist`
- `group_policy: "open" | "allowlist" | "disabled"` — controls group access (default: `"open"`)
- `group_allow_from: [list]` — group JIDs allowed when `group_policy: allowlist`

## Recovery

**If gateway crashed and restarted on its own:**
It's already recovered. New groups created after restart should be visible automatically. Ask the user to tag Friday in the group to test.

**If gateway is stuck or not running:**
```bash
systemctl --user restart hermes-gateway
```

**If a new group still doesn't work after restart:**
The bridge may need a full restart to enumerate new groups:
```bash
systemctl --user restart hermes-gateway
```
Then wait ~30s and have the user tag Friday.

## Known Outbound Send Errors (401 on all sends — confirmed root cause Jun 2026)
**Symptom:** Every `send_message` tool call returns `WhatsApp bridge error (401): {"error":"Unauthorized"}`, even though `curl http://localhost:3000/health` shows connected.

**Root cause:** `hermes-gateway.service` has no `EnvironmentFile` entry — `WHATSAPP_BRIDGE_TOKEN` is never loaded into the gateway process. All outbound sends are unauthenticated.

**Fix:**
```ini
# Add to ~/.config/systemd/user/hermes-gateway.service under [Service]:
EnvironmentFile=/home/hermes/.hermes/.env
```
Then:
```bash
systemctl --user daemon-reload && systemctl --user restart hermes-gateway.service
```

**Verify fix:**
```bash
TOKEN=$(grep WHATSAPP_BRIDGE_TOKEN ~/.hermes/.env | cut -d= -f2)
curl -s -X POST http://localhost:3000/send \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"chatId":"160799431606497@lid","message":"test"}'
# Expect: {"success":true,...}
```

**Note:** Direct curl with token works even when gateway is broken — because curl passes the token explicitly. The gateway fails silently because it never had the env var. This makes it look like a bridge issue when it's actually a service config issue.

## Known Outbound Send Errors

**`jidDecode` error on outbound send to a specific group:**
Symptom: `WhatsApp bridge error (500): {"error":"Cannot destructure property 'user' of 'jidDecode(...)' as it is undefined."}`
This means the bridge cannot parse the group JID for outbound sending. The group can still send messages TO Friday (inbound works), but Friday cannot cold-send TO it.
Fix: restart the gateway — `systemctl --user restart hermes-gateway` — then retry. If the error persists, the group JID may be malformed in the bridge's session cache. Have the user send a message from that group first, then reply to that message rather than cold-sending.

## Per-Chat Model Override (Persistent via Startup Hook)

The gateway's `_session_model_overrides` dict is **in-memory only** — it clears on every restart. There is no native per-chat model field in `config.yaml` for WhatsApp. To make a per-group model override survive restarts, use a gateway startup hook.

**Step 1 — Find the group ID**
Use the bridge's `/chat/:id` endpoint (requires token):
```bash
source ~/.hermes/.env
curl -s "http://localhost:3000/chat/120363426767339595@g.us" \
  -H "Authorization: Bearer $WHATSAPP_BRIDGE_TOKEN"
# Returns: {"name":"Tahmeed's Desk","isGroup":true,"participants":[...]}
```
To find an unknown group ID: scan sender-key files in `~/.hermes/whatsapp/session/` — filenames contain the group JID and participant LIDs. Match participant LID to the known user (e.g. Tahmeed's LID is `90345106862172`):
```bash
ls ~/.hermes/whatsapp/session/ | grep "90345106862172" | grep "g.us"
# → sender-key-120363426767339595@g.us--90345106862172_1--0.json
```

**Step 2 — Determine session key**
For groups with `group_sessions_per_user: false` (the current config):
```
agent:main:whatsapp:group:<CHAT_ID>
```
Example: `agent:main:whatsapp:group:120363426767339595@g.us`

**Step 3 — Create the hook**
```bash
mkdir -p ~/.hermes/hooks/tahmeed-desk-haiku
```

`~/.hermes/hooks/tahmeed-desk-haiku/HOOK.yaml`:
```yaml
name: tahmeed-desk-haiku
description: >
  On gateway startup, sets claude-haiku-4-5 as the model for Tahmeed's Desk WhatsApp group.
events:
  - gateway:startup
```

`~/.hermes/hooks/tahmeed-desk-haiku/handler.py`:
```python
SESSION_KEY = "agent:main:whatsapp:group:120363426767339595@g.us"

def handle(event_type: str, context: dict) -> None:
    try:
        from gateway.run import _gateway_runner_ref
        runner = _gateway_runner_ref()
        if runner is None:
            return
        runner._session_model_overrides[SESSION_KEY] = {
            "model": "claude-haiku-4-5",
            "provider": "anthropic",
            "api_key": "",
            "base_url": "",
            "api_mode": "",
        }
        evict = getattr(runner, "_evict_cached_agent", None)
        if evict:
            evict(SESSION_KEY)
        print(f"[hook] Model override set: {SESSION_KEY} → claude-haiku-4-5", flush=True)
    except Exception as exc:
        print(f"[hook] Error: {exc}", flush=True)
```

**Step 4 — Restart the gateway**
```bash
hermes gateway restart
```
Confirm in `~/.hermes/logs/gateway.log`: `1 hook(s) loaded`

**Verify after a message arrives in that group:**
```bash
grep "120363426767339595" ~/.hermes/logs/agent.log | tail -5
# Should show model=claude-haiku-4-5
```

**Pitfall:** Hook stdout prints don't appear in `gateway.log` — only the `hook(s) loaded` count does. The override is still active; you can't read it cross-process via weakref from a shell.

## Pitfalls
- `require_mention: true` is the correct config for tag-only responses — untagged messages are silently ignored
- Groups created while the bridge is down should be picked up on next restart automatically, but a manual restart confirms it
- Drain timeouts (`code -15`) are not bugs — they happen when a long-running agent is interrupted by a shutdown signal. The gateway auto-restarts with systemd
- **WhatsApp bridge false crash on shutdown (fixed April 2026):** `_check_managed_bridge_exit()` in `gateway/platforms/whatsapp.py` used to flag the bridge's SIGTERM during shutdown as an unexpected crash, triggering a fatal error mid-drain and causing every restart to exit with code 1. Fix: added an early return in that method when `self._running` is False. If you see the same pattern on a fresh install, apply the patch.
- **`background_process_notifications: none` is invalid** — valid values are `all`, `result`, `error`, `off`. Using `none` logs a warning and defaults to `all`. Use `off` to suppress background process notifications.
- `npm audit` warnings on the WhatsApp bridge are informational — run `cd ~/.hermes/hermes-agent/scripts/whatsapp-bridge && npm audit fix` to clear them
- **Gateway restart during active session blocks for 60s** — if you `systemctl restart hermes-gateway` while an agent is processing a message, it will wait up to 60s for the drain, then force-kill. Messages sent during this window are lost. The `systemctl restart` command itself will also time out (blocked in terminal). Workaround: wait for the current response to finish before restarting, or accept that in-flight and restart-window messages will be dropped.
- **`WHATSAPP_ALLOW_ALL_USERS=true` does NOT open up group/DM access at the bridge level** — see Step 5 above. Adding users to `WHATSAPP_ALLOWED_USERS` is the only reliable fix.

## Finding a WhatsApp Group ID by Name

The bridge does not expose a `/chats` or `/groupMetadata` endpoint — those return 404/HTML. The `send_message` list action returns numeric IDs but no group names, so you can't map name → ID directly.

**Workarounds (in order of preference):**

1. **Ask the user to open WhatsApp Web** → click the group → click group name at top → the page URL updates to `https://web.whatsapp.com/[ID]@g.us`
2. **Invite link** → the bridge cannot resolve invite links to IDs — `/groupInviteInfo` is not a valid endpoint
3. **Ping-and-confirm** → send a distinctive emoji to each unknown group ID one by one, user watches the target chat and confirms when it appears. Note: IDs that return `jidDecode` errors are not valid send targets anyway — skip them
4. **Wait for inbound** → ask the user to send a message from the target group; the inbound event will carry the correct chat ID, which you can then save to memory

**Critical:** `send_message` target format is `whatsapp:NUMERIC_ID` (no `@g.us`). The curl bridge uses `NUMERIC_ID@g.us`. Both refer to the same group.

## Key file locations
- Gateway service: `~/.config/systemd/user/hermes-gateway.service`
- WhatsApp bridge: `~/.hermes/hermes-agent/scripts/whatsapp-bridge/bridge.js`
- Config: `~/.hermes/config.yaml`

## Model Switching for Cost Efficiency

When escalating cost concerns, the gateway supports model switching for dramatic token cost reduction:

**Primary → Fallback swap pattern:**
```bash
# Switch primary to Haiku (10x cost reduction)
hermes config set model claude-haiku-4-5
hermes config set fallback_providers.0.model claude-sonnet-4-20250514

# Increase memory headroom if needed
hermes config set memory.memory_char_limit 10000
```

**Gateway auto-reloads config** — no manual restart needed. Verify switch:
```bash
hermes config get model
```

**Trade-offs:**
- **Haiku primary**: 90% cost reduction, handles searches/ops/file tasks perfectly
- **Loses**: Some nuanced reasoning on complex technical problems
- **Escalation path**: Complex tasks can still bump to Sonnet via fallback

**When to switch:** Hindsight searches burning 3-6k tokens per query, high session volume, or cost alerts. The user's typical workflow (quick questions, file management, system ops) runs efficiently on Haiku with minimal quality loss.

**Cost optimization methodology:** See `references/cost-optimization-methodology.md` for comprehensive token usage reduction strategies.

## Confirming the True Running Model (Diagnostics)

Config.yaml and persona prompts say one thing — the actual API calls may differ. To confirm the real model in use for a given session:

```bash
grep "API call #\|conversation turn:" ~/.hermes/logs/agent.log | tail -20
# Each line shows: model=claude-sonnet-4-6 provider=anthropic in=NNNN out=NNN
```

The `model=` field in `agent.log` is the ground truth — it's what was sent to the provider's API. This is how to answer "what model am I actually running on?" without guessing.

To check a specific chat's model (e.g. Tahmeed's Desk):
```bash
grep "120363426767339595" ~/.hermes/logs/agent.log | grep "model=" | tail -5
```

## Hindsight DB access (for dedup / maintenance)
```python
import json, subprocess, os
inst = json.load(open('/home/hermes/.pg0/instances/hindsight-embed-hermes/instance.json'))
pw, user, db, port = inst['password'], inst['username'], inst['database'], inst['port']
env = {**os.environ, 'PGPASSWORD': pw}
pg = '/home/hermes/.pg0/installation/18.1.0/bin/psql'
# Run: pg -h localhost -p {port} -U {user} -d {db}
```

**Dedup exact duplicates:**
```sql
DELETE FROM memory_units WHERE bank_id='hermes' AND id NOT IN (
  SELECT DISTINCT ON (LEFT(text, 200)) id FROM memory_units WHERE bank_id='hermes'
  ORDER BY LEFT(text, 200), access_count DESC, mentioned_at ASC NULLS LAST
);
```

**Always backup first:**
```bash
/home/hermes/.pg0/installation/18.1.0/bin/pg_dump \
  -h localhost -p 5432 -U hindsight hindsight \
  -f ~/.hermes/backups/hindsight_backup_$(date +%Y%m%d_%H%M%S).sql
```

**config.yaml memory limit keys:**
```yaml
memory:
  memory_char_limit: 15000   # MEMORY.md cap
  user_char_limit: 12000     # USER.md cap (bumped from 6000 Jun 2026)
```
