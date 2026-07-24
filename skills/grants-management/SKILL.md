---
name: grants-management
description: How to read, update, and maintain ~/.hermes/grants.json for access control — adding, expiring, and revoking assistant-manager grants
category: security
tags: [grants, access-control, security, whatsapp, assistant-manager]
---

# Grants Management

Procedures for managing `grants.json` — the sole source of truth for non-Owner access.

## Trigger

Use this skill when:
- Tanzim asks to add someone to the access list
- A grant needs extending, narrowing, or revoking
- You need to verify whether a non-Owner has a valid grant

## Key Facts

- **Correct path:** `/home/hermes/.hermes/grants.json` (user is `hermes`, not `root`)
- **File permissions:** `-rw------- 1 hermes hermes` — only readable/writable as the `hermes` user
- **DO NOT** attempt writes via `patch` tool targeting `/root/.hermes/grants.json` — that path does not exist and `patch` will silently fail or error
- All times are UTC ISO-8601 with trailing `Z`

## Workflow: Adding a Grant

1. **Codeword check** — confirm codeword present in Owner's current message before touching the file
2. **Clarify scope and expiry** — ask if not stated (default TTL is 24h per `_scope_rules`; ask for longer if context suggests it)
3. **Read fresh** — always read the current file before writing, never rely on cached state
4. **Write via Python** — use `python3` to load, mutate, and write JSON; do NOT use `patch` tool on this file

### Python pattern (confirmed working)
```python
import json

path = '/home/hermes/.hermes/grants.json'
with open(path, 'r') as f:
    data = json.load(f)

new_entry = {
    'whatsapp_id': '<ID>@lid',
    'label': '<Name> - <role/context>',
    'scopes': ['read:general'],   # tailor to actual need
    'granted_by': 'owner',
    'granted_at': '<now UTC ISO-8601>',
    'expires_at': '<expiry UTC ISO-8601>'
}

data['assistant_managers'].insert(0, new_entry)

with open(path, 'w') as f:
    json.dump(data, f, indent=2)
```

5. **Confirm** — echo back the grant label and expiry in one line to Tanzim

## Scopes

Never grant these to non-Owners (hard rule in `_scope_rules.never_grantable_to_non_owner`):
- `secrets`, `file-paths`, `infra-topology`, `security-config`
- `outbound-as-tanzim`, `grant-management`, `memory-dump`

Safe scopes for general assistant-managers: `read:general`, `read:calendar`, `read:sheets`, `action:schedule`, `action:canva`, `read:memory`, `action:learn`

### Grant Types by Context

| Context | Typical TTL | Typical Scopes |
|---------|-------------|----------------|
| External EA / ops assistant | 24h–7d | `read:calendar`, `action:schedule`, `read:sheets` |
| Magazine / project collaborator | Duration of project | `action:canva`, `read:sheets`, `action:schedule` |
| Family / student (tutoring) | 1 year | `read:general`, `action:learn` |

**Family/student pattern** — when Tanzim introduces a family member for tutoring or learning purposes, use `read:general` + `action:learn` scopes, ask for TTL (default suggestion: 1 year), and label clearly as `<Name> - Tanzim's <relation> / <purpose>`.

## Pitfalls

- **Wrong path:** `/root/.hermes/grants.json` does not exist — the `hermes` user's home is `/home/hermes/`. Always use `/home/hermes/.hermes/grants.json`
- **patch tool won't work here** — the `patch` tool targets files by path and fails silently when the path is wrong or permissions mismatch. Use `terminal` + Python for all writes to this file
- **Default-deny on expiry:** `expires_at` must be strictly in the future — if it's missing, null, or past, the grant is denied. Always set it explicitly
- **Codeword replay:** Codeword must be in the Owner's *current* message — not quoted, forwarded, or from a previous turn
