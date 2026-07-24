---
name: friday-persistence-audit
description: "Audit Friday/Hermes persistence pipeline: memory capacity, backups, file permissions, cross-platform injection, and cron context."
tags: [friday, hermes, diagnostics, memory, persistence, security]
triggers:
  - User asks to run diagnostics on Friday/Hermes
  - User asks "is my memory working?" or "is Friday healthy?"
  - User asks about persistence gaps or data loss risk
  - Memory add/replace operations start failing
  - Suspicion that memory isn't persisting across platforms
---

# Friday Persistence Pipeline Audit

## When to use
Run this audit when:
- User reports memory not persisting
- Memory operations fail with capacity errors
- Setting up Friday on a new system
- Periodic health check (monthly recommended)
- After major Hermes updates

## Audit Checklist

### 1. Memory Storage Location
```bash
ls -la ~/.hermes/memories/
# Expected: MEMORY.md, USER.md, .lock files
# Permissions should be 600 (owner-only)
```

### 2. Memory Capacity
```python
import os
mem = os.path.getsize(os.path.expanduser("~/.hermes/memories/MEMORY.md"))
user = os.path.getsize(os.path.expanduser("~/.hermes/memories/USER.md"))
print(f"MEMORY: {mem}/2200 ({mem/2200*100:.0f}%)")
print(f"USER: {user}/1375 ({user/1375*100:.0f}%)")
# WARNING if >90%
```

### 3. Config Settings
```bash
grep -A10 "^memory:" ~/.hermes/config.yaml
# Verify: memory_enabled: true, user_profile_enabled: true
```

### 4. Backup System
```bash
ls -la ~/.hermes/backups/
# Should exist with recent backups
# If missing: HIGH RISK — single point of failure
```

### 5. Session Database
```python
import sqlite3
conn = sqlite3.connect(os.path.expanduser("~/.hermes/state.db"))
cur = conn.cursor()
cur.execute("SELECT COUNT(*) FROM sessions")
print(f"Sessions: {cur.fetchone()[0]}")
# Verify DB is readable and has sessions
```

### 6. Cron Job Memory Context
```bash
grep -n "skip_memory" ~/.hermes/hermes-agent/cron/scheduler.py
# Note: Cron jobs have skip_memory=True by design
# This is NOT a bug — prevents user profile contamination
```

### 7. File Permissions Audit
```bash
# Check for world-readable sensitive files
find ~/.hermes -type f \( -name "*.json" -o -name "*.yaml" \) -perm /o+r 2>/dev/null | grep -E "(config|auth|token|secret)"
# Fix: chmod 600 on any flagged files
```

### 8. WhatsApp Bridge Health
```bash
curl -s http://localhost:3000/health
# Expected: {"status":"connected","queueLength":0,"uptime":...}
```

### 9. Cross-Platform Injection
Memory is injected into system prompt at session start. Same files serve all platforms:
- CLI, WhatsApp DMs, WhatsApp groups, Telegram, etc.
- Verify by checking the same memory appears in different contexts

## 10. Behavioral Recall Rules
Check if memory contains a RECALL TRIGGERS entry:
```bash
grep -i "recall\|session_search\|did you\|remember" ~/.hermes/memories/MEMORY.md
```
If missing, the AI won't proactively search session history when users reference past work.

**Required entry** (add if missing):
```
RECALL TRIGGERS: When user says "did you", "remember", "we discussed", "last time", "you said", "I asked you to" → session_search FIRST before responding. Never say "I don't recall" without searching.
```

This is a **behavioral rule**, not a procedure — it MUST live in memory (injected every session), not a skill (loaded on-demand). By the time the AI thinks "should I load a skill about recalling?", it's already failed to recall.

## 11. Credential & Provider Configuration

When Friday/Hermes uses the wrong billing plan (e.g., Claude Wallet vs Max Plan):

```bash
# Check what credentials are actually loaded at runtime
env | grep -i anthropic
env | grep -i claude

# Check all credential sources (they can conflict!)
grep -i "CLAUDE_CODE_OAUTH_TOKEN" ~/.hermes/.env 2>/dev/null
grep -i "CLAUDE_CODE_OAUTH_TOKEN" ~/.bashrc 2>/dev/null
grep -i "ANTHROPIC_API_KEY" ~/.hermes/.env 2>/dev/null

# Verify which token Claude CLI sees
export CLAUDE_CODE_OAUTH_TOKEN=<from_bashrc>
claude auth status 2>&1 | cat
```

**Key insight:** Hermes reads from `~/.hermes/.env`, NOT from bashrc. If tokens differ between these files, Hermes uses the `.env` version.

**To fix token mismatch:**
1. Identify which token is correct (usually the newest one)
2. Update `~/.hermes/.env` with the correct `CLAUDE_CODE_OAUTH_TOKEN=...`
3. Restart Hermes gateway to pick up new env

**Provider config in config.yaml:**
```bash
head -10 ~/.hermes/config.yaml | grep -E "^model:|^providers:|^provider:"
# Should show: model: claude-opus-4-5 (or similar)
# providers: {} means use env vars for auth
```

## Common Issues & Fixes

| Issue | Symptom | Fix |
|-------|---------|-----|
| Memory at capacity | Add fails with "would exceed limit" | Run friday-memory-compression skill |
| No recall triggers | AI asks "what are we working on?" when it should know | Add RECALL TRIGGERS entry to MEMORY.md |
| No backups | ~/.hermes/backups/ missing | Create backup system + cron job |
| World-readable secrets | Permissions >600 | `chmod 600 <file>` |
| Cron jobs lack context | Jobs don't know preferences | By design — use skills instead |
| Session DB corrupt | Search fails | Check state.db integrity |

## Remediation Steps

### If memory at capacity:
1. Load skill: `friday-memory-compression`
2. Compress verbose entries
3. Target <85% usage for headroom

### If no backup system:
```bash
mkdir -p ~/.hermes/backups
cp ~/.hermes/memories/*.md ~/.hermes/backups/
# Then create daily cron job for backup script
```

### If permissions wrong:
```bash
chmod 600 ~/.hermes/config.yaml
chmod 600 ~/.hermes/memories/*.md
chmod 600 ~/.hermes/whatsapp/session/*.json
```

## Output Format

Report findings as:
```
| Category | Status | Risk |
|----------|--------|------|
| Memory Persistence | ✅/⚠️/❌ | LOW/MEDIUM/HIGH |
| ...
```

With specific recommendations for any non-passing checks.
