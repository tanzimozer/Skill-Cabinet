---
name: systemd-service-port-conflicts
description: "Fix systemd services that crash-loop due to port already in use — add ExecStartPre to kill the port before each start."
tags: [systemd, linux, port, crash-loop, devops]
triggers:
  - A systemd service is crash-looping with "address already in use"
  - A server process (FastAPI, uvicorn, Node, etc.) fails to bind its port on restart
  - Service restart counter is in the hundreds due to rapid restart cycles
  - Port is held by a zombie/previous instance of the same service
---

# Systemd Service Port Conflict Fix

## Problem
When a service crashes hard, systemd restarts it before the OS releases the port. The new process fails with `[Errno 98] Address already in use`, causing a rapid crash loop (can hit hundreds of restarts quickly).

## Fix — Add ExecStartPre to kill the port

In the `[Service]` block, add before `ExecStart`:

```ini
ExecStartPre=-/bin/bash -c "fuser -k PORT/tcp || true"
ExecStart=...
```

- `-` prefix: tells systemd to continue even if ExecStartPre fails (e.g. nothing on that port)
- `|| true`: prevents non-zero exit if no process is found
- `fuser -k PORT/tcp`: kills any process holding the port

## Full Example

```ini
[Unit]
Description=My Server
After=network.target

[Service]
Environment="PATH=/home/user/.local/bin:/usr/local/bin:/usr/bin:/bin"
ExecStartPre=-/bin/bash -c "fuser -k 8645/tcp || true"
ExecStart=/usr/bin/python3 /home/user/server.py
Restart=always
RestartSec=5

[Install]
WantedBy=default.target
```

## Apply the fix

```bash
# Edit the service file
nano ~/.config/systemd/user/myservice.service

# Reload and restart
systemctl --user daemon-reload
systemctl --user restart myservice.service

# Verify
systemctl --user status myservice.service --no-pager
```

## Also add PATH if hermes/local binaries are used

Systemd user services don't inherit the shell's PATH. If the service spawns local binaries (e.g. `hermes`), add:

```ini
Environment="PATH=/home/hermes/.local/bin:/usr/local/bin:/usr/bin:/bin"
```

Without this, you'll get `[Errno 2] No such file or directory` when the process tries to spawn a subprocess.

## Pitfalls
- `fuser` must be installed — on Debian/Ubuntu it's in `psmisc` package (`apt install psmisc`)
- `RestartSec=5` gives the OS time to release the port before the next attempt — set at least 3-5s
- If the crash loop has already hit hundreds of restarts, systemd may be in a rate-limited state — `systemctl --user reset-failed myservice` to clear it before restarting
