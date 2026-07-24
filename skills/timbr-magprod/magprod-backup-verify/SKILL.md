---
name: magprod-backup-verify
description: Verify the daily MAGPROD backup actually ran and is complete. Use when Tanzim asks about backup health or weekly.
---

# MAGPROD backup verify

Use on request or as a periodic health check.

A daily backup cron copies MAGPROD content to backups/ at 11pm.

Steps:
1. Check backups/ has a fresh dated backup from the last run.
2. Spot-check it's non-empty and includes the current issue + blueprints.
3. If missing/stale: report it plainly as a single heads-up (don't silently ignore) — backup failure is a real risk.

Pitfalls: a "present" folder isn't a verified backup — check contents/size; don't assume the cron ran.
Verify: latest backup dated within 24h and non-trivial in size.
