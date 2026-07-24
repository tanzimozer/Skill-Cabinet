---
name: friday-daily-backup
description: Create or update Friday's daily automated backup — essentials-only tar.gz of config, credentials, skills, and scripts, scheduled via cron.
triggers:
  - User asks to back up Friday/Hermes files
  - User asks to update the backup after adding new scripts or credentials
  - User wants a scheduled daily backup
  - New credentials, scripts, or integrations added that should be preserved
---

# Friday Daily Backup

## What this covers
Creating and maintaining a lean daily backup of Friday's essential files — config, credentials, skills, job scripts, voice server — excluding large model caches. Scheduled via Hermes cron to run automatically.

## Key paths
- Backup script: `/home/hermes/backup_friday.sh` (full daily backup)
- Memory backup script: `~/.hermes/scripts/backup_memory.sh` (memory + config only, uploads to Drive)
- Output dir: `/home/hermes/backups/` (local) + Google Drive HERMES folder
- Filename pattern: `friday_backup_YYYYMMDD.tar.gz`
- Retention: 7 days local (auto-pruned), indefinite on Drive
- Google Drive folder ID: `1yGZuAcD4jzf8257cXMTjZeGsfMcK0Ba-`

## What to include in the backup
Always include:
- `.hermes/skills/` — all skills
- `.hermes/config.yaml` — all hermes config
- `.hermes/google_token.json` + `.hermes/google_client_secret.json` — Google OAuth
- `.hermes/auth.json` — Hermes auth
- `.hermes/memories/` — persistent memory (if exists)
- `.hermes/cron/` — scheduled jobs
- `.hermes/hooks/` — event hooks
- `.hermes/webhook_subscriptions.json`
- `.hermes/channel_directory.json`
- `.hermes/SOUL.md`
- `jobs/` — job scraper scripts
- `instagram_unfollower/` — IG automation
- `voice_server.py` — voice assistant
- `backup_friday.sh` — the script itself

## DO NOT include
- `.hermes/hermes-agent/` — large source code, re-cloneable
- `.hermes/models_dev_cache.json` / model caches
- `.hermes/cache/`, `.hermes/image_cache/`, `.hermes/audio_cache/`
- `.hermes/sessions/` — session history, large
- `.hermes/sandboxes/`
- Existing `friday_backup_*.tar.gz` files

## Backup script template
```bash
#!/bin/bash
set -e

BACKUP_DIR="/home/hermes/backups"
DATE=$(date +%Y%m%d)
BACKUP_FILE="$BACKUP_DIR/friday_backup_$DATE.tar.gz"

mkdir -p "$BACKUP_DIR"

tar -czf "$BACKUP_FILE" \
  -C /home/hermes \
  .hermes/skills \
  .hermes/config.yaml \
  .hermes/google_token.json \
  .hermes/google_client_secret.json \
  .hermes/auth.json \
  .hermes/memories \
  .hermes/cron \
  .hermes/hooks \
  .hermes/webhook_subscriptions.json \
  .hermes/channel_directory.json \
  .hermes/SOUL.md \
  jobs/ \
  instagram_unfollower/ \
  voice_server.py \
  backup_friday.sh \
  2>/dev/null

echo "Backup complete: $BACKUP_FILE ($(du -sh "$BACKUP_FILE" | cut -f1))"

# Keep only last 7 days
find "$BACKUP_DIR" -name "friday_backup_*.tar.gz" -mtime +7 -delete
echo "Old backups pruned."
```

## Scheduling via Hermes cron
```
Schedule: 45 23 * * *  (11:45 PM daily)
Deliver: origin
Toolsets: terminal
Prompt: Run /home/hermes/backup_friday.sh and report filename + size.
```

## Pitfalls
- `.hermes/` is 2.2GB+ due to model caches — never tar the whole directory, always list explicit subdirs
- `tar` on large dirs will timeout — keep scope tight
- If a new credential file is added (e.g. new OAuth token), add it explicitly to the script
- Run `bash /home/hermes/backup_friday.sh` manually first to verify before relying on cron
- `chmod +x` the script before first run

## Updating the backup after new integrations
When new scripts, credentials, or config files are added:
1. Edit `/home/hermes/backup_friday.sh` and add the new path to the `tar` command
2. Run it manually once to verify
3. No need to recreate the cron job — it already points to the script

## Google Drive upload (added 2026-05)
The memory backup script (`~/.hermes/scripts/backup_memory.sh`) now uploads to Google Drive:

```python
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from googleapiclient.http import MediaFileUpload

creds = Credentials.from_authorized_user_file('/home/hermes/.hermes/google_token.json')
drive = build('drive', 'v3', credentials=creds)

media = MediaFileUpload('/path/to/backup.tar.gz', mimetype='application/gzip')
drive.files().create(
    body={'name': 'friday_backup_DATE.tar.gz', 'parents': ['FOLDER_ID']},
    media_body=media
).execute()
```

The HERMES folder on Drive also contains `Hermes_SOP_Master.pdf` — a 1-page reference doc with architecture, memory system, credentials locations, and emergency recovery steps.

## SOP/Master Reference PDF
Location: Google Drive > HERMES > `Hermes_SOP_Master.pdf`
Generated with: `fpdf2` (install: `pip install fpdf2` in hermes venv)
Script: `/home/hermes/create_sop_pdf.py`

Regenerate when architecture changes significantly.
