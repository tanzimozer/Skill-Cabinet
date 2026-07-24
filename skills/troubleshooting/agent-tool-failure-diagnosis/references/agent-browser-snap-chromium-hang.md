# agent-browser hang: snap Chromium under container confinement

Session: Jun 2026. `browser_navigate` timed out on every URL (60s), repeatedly.

## Symptom
- Every `browser_navigate` / `browser_snapshot` call → "Command timed out".
- No browser process running between calls (tool launches fresh each time).

## Root cause (two compounding faults)
1. The agent-browser CLI defaults to **snap Chromium** (`/snap/bin/chromium`,
   `/snap/chromium/<rev>`). Under this container's confinement snap Chromium
   **hangs at launch** and never writes DevToolsActivePort → the navigate runs
   to timeout. Direct test of the snap binary with `--dump-dom` also hung.
2. Stale state piled on top: a dead daemon holding
   `/run/user/1000/agent-browser/default.sock`, plus orphaned chrome processes
   under `/tmp/agent-browser-chrome-*`. The client blocks on the dead socket at
   0% CPU / ~3.8 MB RSS (EXIT 124 under `timeout`).

The **Playwright Chromium** build worked fine directly
(`~/.cache/ms-playwright/chromium-1217/chrome-linux/chrome`, ~200 MB RSS,
loaded example.com) — but through the tool it errored
`No usable sandbox!` until `--no-sandbox` was added (container restriction on
unprivileged user namespaces).

## Reproduction (direct binary, bypass the wrapper)
```bash
cd ~/.hermes/hermes-agent/node_modules/agent-browser/bin
BIN=./agent-browser-linux-arm64        # pick the arch that matches `uname -m`
# hang repro (snap default):
/usr/bin/time -v timeout 60 $BIN open "https://example.com"   # EXIT 124, 0% CPU
# sandbox error repro (playwright, no flag):
PW=/home/hermes/.cache/ms-playwright/chromium-1217/chrome-linux/chrome
$BIN --executable-path "$PW" open "https://example.com"        # FATAL No usable sandbox
```

## The fix (persistent, survives fresh sessions)
Write `~/.agent-browser/config.json` — note `args` is a STRING, not an array:
```json
{
  "executablePath": "/home/hermes/.cache/ms-playwright/chromium-1217/chrome-linux/chrome",
  "args": "--no-sandbox,--disable-dev-shm-usage,--disable-gpu"
}
```
Chromium dir version (`chromium-1217`) can change after a Playwright update —
re-glob `~/.cache/ms-playwright/chromium-*/chrome-linux/chrome` if the path 404s.

## Cleanup before retest
```bash
cd ~/.hermes/hermes-agent/node_modules/agent-browser/bin
./agent-browser-linux-arm64 close --all
# in a SEPARATE call if you need pkill, so it doesn't kill your own test:
pkill -9 -f 'agent-browser'; pkill -9 -f 'snap/chromium'
rm -rf /run/user/1000/agent-browser/* /tmp/agent-browser-chrome-*
```

## Verify
```bash
# prove config alone works, no env vars:
env -u AGENT_BROWSER_EXECUTABLE_PATH -u AGENT_BROWSER_ARGS \
  timeout 60 ./agent-browser-linux-arm64 open "https://example.com"   # -> ✓ Example Domain
```
Then confirm through the actual `browser_navigate` tool.

## Key override knobs (from `strings` on the binary)
- `AGENT_BROWSER_EXECUTABLE_PATH` / `--executable-path` / config `executablePath`
- `AGENT_BROWSER_ARGS` / `--args` / config `args` (comma-separated string)
- Config search order: `~/.agent-browser/config.json` (user) then env vars override.
- Don't trust `agent-browser doctor` as a health check — it runs its own launch
  probes and hangs when the launch path is broken.
