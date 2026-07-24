---
name: linux-server-security-hardening
description: Diagnose, assess, and harden a Linux server — run system diagnostics, identify security risks, enable UFW firewall safely, and apply pending system/kernel updates.
triggers:
  - "run system diagnostics"
  - "check server security"
  - "harden the server"
  - "enable firewall"
  - "apply system updates"
  - "check for security risks"
tags: [linux, security, ufw, firewall, apt, diagnostics, devops]
---

# Linux Server Security Hardening

## When to Use
Any time the user asks for system diagnostics, a security check, firewall setup, or OS updates on a Linux (Ubuntu/Debian) server.

## Phase 1 — System Diagnostics

Run a full snapshot in one command:

```bash
echo "=== UPTIME ===" && uptime && \
echo "=== CPU ===" && top -bn1 | grep "Cpu(s)" && \
echo "=== MEMORY ===" && free -h && \
echo "=== DISK ===" && df -h / /home 2>/dev/null && \
echo "=== TOP PROCESSES ===" && ps aux --sort=-%cpu | head -8 && \
echo "=== NETWORK ===" && ip -brief addr
```

Report: uptime, load average, memory %, disk %, top CPU processes, active interfaces.

## Phase 2 — Security Assessment

```bash
# Open ports (only localhost-bound is safe; 0.0.0.0 means public)
ss -tlnp

# Failed login attempts
grep "Failed password" /var/log/auth.log 2>/dev/null | tail -5

# Recent logins
last | head -10

# Sudo group members
getent group sudo

# Firewall status
sudo ufw status verbose

# Fail2ban status
sudo fail2ban-client status

# Pending updates
apt list --upgradable 2>/dev/null
```

### Risk Flags to Look For
- UFW inactive → needs enabling
- SSH (port 22) exposed on 0.0.0.0 without fail2ban → high risk
- Any unexpected public-facing ports
- Kernel or security package updates pending
- Unknown users in sudo group
- Suspicious logins from unexpected IPs

## Phase 3 — Harden: Enable UFW

**CRITICAL: Always allow SSH before enabling UFW or you will lock yourself out.**

```bash
sudo ufw allow OpenSSH
sudo ufw allow 22/tcp
sudo ufw --force enable
sudo ufw status verbose
```

Expected output: default deny incoming, allow outgoing, SSH whitelisted.

## Phase 4 — Apply System Updates

```bash
sudo apt-get update -q && \
sudo DEBIAN_FRONTEND=noninteractive apt-get upgrade -y 2>&1 | tail -20
```

- Set timeout to 300s — kernel updates can take time
- After kernel updates, a reboot is recommended (not always urgent — inform user)
- Services may flag as needing restart — normal, advise reboot at convenience

## Pitfalls

- `ufw status` may fail without sudo — always use `sudo ufw status verbose`
- Hermes runs as `hermes` user with sudo — commands work via terminal tool
- `systemctl is-active hermes` may show inactive even if gateway is running (it's launched directly, not via systemd) — check with `pgrep -a hermes` instead
- `gws` CLI may not be in PATH — fall back to direct Python `googleapiclient` calls for Google Workspace tasks
- Kernel headers update ≠ kernel running updated — reboot required to fully apply

## Post-Hardening Summary to Report

1. UFW status (active/inactive, rules)
2. Fail2ban status (jails active)
3. Updates applied (package names + versions)
4. Any reboot recommended
5. Remaining risks (if any)
