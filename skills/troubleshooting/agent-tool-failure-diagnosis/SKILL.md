---
name: agent-tool-failure-diagnosis
type: procedure
description: >
  Root-cause a hung or silently-failing agent tool (browser, terminal-backed
  CLIs, daemonised helpers) instead of routing around it. Process inspection →
  direct reproduction → isolate the one variable → persistent fix that survives
  restarts. Distinguishes durable fixes (capture) from environment-transient
  failures (don't capture as constraints).
trigger: |
  - A tool call times out or hangs repeatedly (browser_navigate, snapshot, etc.)
  - Tanzim says "fix it", "get to the root of it", "stop routing around it"
  - A wrapped CLI / daemon tool fails with no useful error
  - Same tool fails N times this turn (loop warning fired)
prerequisites:
  - Terminal access to inspect processes, memory, sockets
  - Ability to locate and run the tool's underlying binary directly
---

## Core principle

When Tanzim says "fix it, get to the root" — he means **diagnose, don't work
around**. Routing around (curl instead of browser) is fine as a *stopgap to
unblock his actual request*, but it is NOT the deliverable. Find why the tool
itself failed and make it work.

## Diagnostic ladder (cheapest first)

1. **Is the process even running?** `ps aux | grep -i <tool/chrome/node>`.
   Often the answer is "nothing launched" → the hang is at startup, not runtime.
2. **Resource starvation?** `free -h` and `df -h /tmp /dev/shm`. Headless Chrome
   needs a few hundred MB to launch; <200 MB free → OOM-stall to timeout.
   Identify the hog with `ps aux --sort=-%mem | head`. **Do not kill daemons
   that hold durable state** (e.g. the hindsight memory daemon — it holds
   long-term memory; leave it even when it's the biggest consumer).
3. **Stale daemon / lock / socket?** Many agent tools (agent-browser) use a
   persistent daemon over a unix socket. A dead daemon holding the socket makes
   the client block forever at 0% CPU / tiny RSS. Look in
   `/run/user/<uid>/<tool>/`, `/tmp/<tool>-*`, for `*.sock`, `SingletonLock`.
   `ss -lxp | grep <tool>` shows if anything actually listens.
4. **Reproduce DIRECTLY against the underlying binary**, bypassing the tool
   wrapper, with a hard timeout and `/usr/bin/time -v`. EXIT 124 + 0% CPU +
   tiny RSS = blocked waiting (socket/daemon). A FATAL stderr line = a real
   launch error you can act on.
5. **Isolate the one variable.** If a clean binary works but the tool hangs,
   find what differs (binary path, sandbox, flags). The classic split: the tool
   defaults to **snap Chromium** (hangs under container confinement) while the
   **Playwright Chromium build works** — and needs `--no-sandbox` in a
   container ("No usable sandbox" FATAL is the tell).

## Make the fix PERSISTENT

A fix that only holds for one shell invocation isn't a fix. Prefer, in order:
config file > env var in the right place > wrapper edit. Verify the fix loads
**with no env vars set** (`env -u VAR ...`) to prove it survives a fresh
session. Then verify end-to-end through the actual agent tool, not just the
binary.

## Capture discipline (what becomes a durable rule vs not)

- ✅ Capture the **FIX**: the config key, the flag, the path. ("Point
  agent-browser at Playwright Chromium with --no-sandbox via
  ~/.agent-browser/config.json.")
- ❌ Never capture "tool X is broken / doesn't work" as a standalone constraint.
  It hardens into a refusal long after the environment changed.
- ❌ Don't capture pure environment-transients (missing binary, unconfigured
  cred) as rules — note the install/config step instead.

## Pitfalls learned

- Chaining a `pkill -f <tool>` and the test command in one shell call kills the
  test too (exit -9). Clean up in a SEPARATE call, then run the test.
- agent-browser's `doctor` runs its own launch probes and will itself hang if
  the launch path is broken — don't use it as your health check; use a real
  `open <url>` with a timeout.
- agent-browser config `args` is a **comma-separated string**, not a JSON array
  (array → "invalid type: sequence, expected a string").

See `references/agent-browser-snap-chromium-hang.md` for the full reproduction
and the exact working config from the Jun 2026 session.
