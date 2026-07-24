---
name: browser-tool-troubleshooting
description: "Diagnosing and fixing the agent-browser tool when browser_navigate/snapshot hang or time out — root-cause path and the persistent config fix"
category: operations
tags: [browser, agent-browser, playwright, chromium, troubleshooting, navigate-timeout]
version: 1.0.0
created: 2026-06-28
---

# Browser Tool Troubleshooting

When `browser_navigate` / `browser_snapshot` time out on every call (60s, no error
detail), don't just route around it with curl forever — the underlying agent-browser
tool can be **repaired** at the root. This skill is the diagnostic path and the fix.

## TL;DR fix (if you just want it working)

The agent-browser CLI defaults to **snap Chromium**, which hangs silently under
container confinement. Repoint it at the bundled Playwright Chromium with
`--no-sandbox` via a persistent config file. One file, survives restarts, no env vars:

```bash
mkdir -p ~/.agent-browser
cat > ~/.agent-browser/config.json <<'EOF'
{
  "executablePath": "/home/hermes/.cache/ms-playwright/chromium-1217/chrome-linux/chrome",
  "args": "--no-sandbox,--disable-dev-shm-usage,--disable-gpu"
}
EOF
```

Then clear any stale daemon/socket (see below) and test `browser_navigate` again.
**Confirm the Playwright chromium path** first — the `chromium-1217` build number
changes across installs: `ls ~/.cache/ms-playwright/`.

**Config-file gotchas (confirmed):**
- `args` must be a **comma-separated string**, NOT a JSON array. An array gives
  `invalid type: sequence, expected a string`.
- Keys are `executablePath` and `args` (camelCase). Env equivalents:
  `AGENT_BROWSER_EXECUTABLE_PATH`, `AGENT_BROWSER_ARGS`.
- The file at `~/.agent-browser/config.json` is auto-loaded — no flag needed.

## Root-cause diagnostic path (how it was found)

Work top-down; each step rules a layer out:

1. **Is a browser even running? Is the box out of RAM?**
   ```bash
   ps aux | grep -iE 'chrome|chromium|agent-browser' | grep -v grep
   free -h
   ```
   Chrome needs a few hundred MB to launch. If `available` is ~100MB, it OOM-stalls.
   (This session: hindsight daemon held ~3.2GB — do NOT kill it, it holds long-term
   memory. Reclaim elsewhere or accept the constraint and fix the real cause below.)

2. **Does Chromium launch standalone?** Prove the binary works:
   ```bash
   CHROME=$(ls ~/.cache/ms-playwright/chromium-1217/chrome-linux/chrome)
   timeout 35 "$CHROME" --headless=new --no-sandbox --disable-gpu \
     --disable-dev-shm-usage --dump-dom "https://example.com" | head
   ```
   If this returns DOM, the binary + network are fine — the fault is in the tool layer.

3. **Reproduce the hang through the tool's own CLI** (native Rust binary):
   ```bash
   cd ~/.hermes/hermes-agent/node_modules/agent-browser/bin
   /usr/bin/time -v timeout 60 ./agent-browser-linux-arm64 open "https://example.com"
   ```
   A hang at **0% CPU, ~3.8MB RSS** = it's blocked waiting (dead daemon socket), not
   crunching. An error mentioning **snap/chromium** or **No usable sandbox** points
   straight at the cause.

4. **Find which chromium the tool actually uses.** If processes show
   `/snap/chromium/...` → that's the broken default. Snap Chromium hangs under this
   container's AppArmor/namespace confinement. The Playwright build at
   `~/.cache/ms-playwright/` works once given `--no-sandbox`.

5. **Discover override knobs** from the binary's own strings:
   ```bash
   strings -n 6 agent-browser-linux-arm64 | grep -iE 'AGENT_BROWSER_.*(PATH|ARGS|EXEC)|executablePath|config\.json' | sort -u
   ```
   This is how `AGENT_BROWSER_EXECUTABLE_PATH`, `AGENT_BROWSER_ARGS`, and
   `~/.agent-browser/config.json` were found.

## Clearing stale daemon / socket / orphan chromium

agent-browser runs a persistent daemon. A crashed one leaves a stale socket the CLI
blocks on forever, plus orphaned chrome children eating RAM. Clean slate:

```bash
# Preferred: graceful close via the tool
cd ~/.hermes/hermes-agent/node_modules/agent-browser/bin && ./agent-browser-linux-arm64 close --all
# Then nuke any survivors + stale state
pkill -9 -f 'agent-browser' ; pkill -9 -f 'snap/chromium'
rm -rf /run/user/1000/agent-browser/* /tmp/agent-browser-chrome-*
```
Note: the daemon **respawns on demand**, so seeing fresh chromium procs right after a
kill is normal — it's re-launching, not failing. The socket lives at
`/run/user/1000/agent-browser/default.sock` (or `$XDG_RUNTIME_DIR/agent-browser/`).

## Sandbox error decode

`FATAL ... No usable sandbox!` after repointing to Playwright chromium = container
restricts unprivileged user namespaces. **Expected**, not a regression. Fix is the
`--no-sandbox` flag (already in the config above). Chrome's own error text spells it out.

## Pitfalls

- **Don't capture "browser tools are broken" as a rule.** They work — they were
  mis-pointed at snap chromium. The durable lesson is the *repoint*, not a refusal.
- **`doctor` subcommand hangs too** (it runs its own launch probes through the same
  broken path). Don't wait on it — test with a real `open` instead.
- **Verify the chromium path before writing config** — the `chromium-<NNNN>` build
  number is install-specific. A wrong path silently falls back or errors.
- **When the browser is genuinely down and you need data NOW**, the curl/pdftotext
  fallback for web pages, PDFs, and Google Docs/Sheets export endpoints is documented
  in `tahmeed-ai-curriculum` SKILL.md (sheet CSV export, doc txt export, papacambridge
  past-papers). Fix the tool when you have time; fall back when you don't.
