---
name: browser-tool-fix
description: Fix for the agent-browser tool hanging/timing out on every navigate in Tanzim's container environment. Use when browser_navigate, browser_snapshot, or any browser tool times out repeatedly.
category: operations
---

# Browser Tool Fix (agent-browser hangs on navigate)

## Symptom
Every `browser_navigate` / `browser_snapshot` call times out (~60s), no page ever loads. Direct Chromium tests on a blank page may work, but real navigations hang at ~0% CPU and tiny RSS — the process is blocked, not crashing.

## Root cause (diagnosed 2026-06-28)
The agent-browser CLI defaults to **snap Chromium** (`/snap/bin/chromium`), which **hangs silently under this container's confinement**. Compounding: stale daemon sockets and orphaned chrome processes pile up after each failed attempt. RAM is also tight (hindsight daemon ~3.2GB RSS), so there's little headroom.

## The fix (permanent)
Point agent-browser at the working **Playwright Chromium** with `--no-sandbox` (required in this container — unprivileged namespaces are restricted), via its config file:

```bash
mkdir -p ~/.agent-browser
cat > ~/.agent-browser/config.json <<'EOF'
{
  "executablePath": "/home/hermes/.cache/ms-playwright/chromium-1217/chrome-linux/chrome",
  "args": "--no-sandbox,--disable-dev-shm-usage,--disable-gpu"
}
EOF
```

Config keys: `executablePath` (string), `args` (comma-separated string, NOT a JSON array — array fails validation). No env vars needed; the config file alone fixes it and survives restarts.

Note: the Playwright chromium version dir (`chromium-1217`) may change after updates — verify with `ls ~/.cache/ms-playwright/`.

## When it hangs again — clear stale state first
```bash
pkill -9 -f 'agent-browser' 2>/dev/null
pkill -9 -f 'snap/chromium' 2>/dev/null
pkill -9 -f 'agent-browser-chrome-' 2>/dev/null
rm -rf /run/user/1000/agent-browser/* /tmp/agent-browser-chrome-* 2>/dev/null
```
Then retry. The daemon respawns on demand.

## Verify the fix
```bash
cd ~/.hermes/hermes-agent/node_modules/agent-browser/bin
./agent-browser-linux-arm64 open "https://example.com"   # should print: ✓ Example Domain
```
Or just call `browser_navigate` to a simple page.

## DO NOT
- Never kill the hindsight daemon (pid varies, ~3.2GB RSS, `--port 9177`) — it holds long-term memory.
- Don't use the snap Chromium; it's the broken default.
