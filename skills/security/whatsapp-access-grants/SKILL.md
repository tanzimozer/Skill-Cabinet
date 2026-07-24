---
name: whatsapp-access-grants
category: security
description: Managing grants.json for WhatsApp user access — adding, updating, and troubleshooting non-owner grants.
triggers:
  - "add [user] to access list"
  - "whitelist [person]"
  - "grant access to"
  - "add to grants"
---

# WhatsApp Access Grants

## Overview
Grants are stored in `~/.hermes/grants.json` (owned by `hermes` user). All access control is read fresh on every request. Default-deny if missing/malformed/expired.

## File location
```
/home/hermes/.hermes/grants.json
```
Note: `/root/.hermes/grants.json` does NOT exist — always use `/home/hermes/.hermes/`.

## Adding a new grant

```python
import json
path = '/home/hermes/.hermes/grants.json'
with open(path, 'r') as f:
    data = json.load(f)

new_entry = {
    "whatsapp_id": "<ID>@s.whatsapp.net",   # or @lid — add BOTH if uncertain
    "label": "Human-readable name / role",
    "scopes": ["read:general", "action:learn"],
    "granted_by": "owner",
    "granted_at": "<ISO8601Z>",
    "expires_at": "<ISO8601Z>"
}

data['assistant_managers'].append(new_entry)

with open(path, 'w') as f:
    json.dump(data, f, indent=2)
```

## Critical pitfall: @lid vs @s.whatsapp.net mismatch

**The single biggest failure mode.** WhatsApp routes messages via two ID formats:
- `@lid` — linked-device ID (e.g. `90345106862172@lid`) — used when Tanzim mentions/tags someone
- `@s.whatsapp.net` — phone-number ID (e.g. `8801789840112@s.whatsapp.net`) — used as the actual sender ID in messages

**Always add BOTH.** When given a `@lid`, look up the corresponding phone number:
```bash
cat ~/.hermes/whatsapp/session/lid-mapping-<lid_number>_reverse.json
```
This returns the phone number. Add `<number>@s.whatsapp.net` as a second entry.

If you only add the `@lid`, the user's messages will be denied because they arrive as `@s.whatsapp.net`.

## Verification
After adding, confirm both IDs are present:
```bash
python3 -c "import json; d=json.load(open('/home/hermes/.hermes/grants.json')); [print(e['whatsapp_id'], e['label']) for e in d['assistant_managers']]"
```

## Scopes for students / general users
```json
["read:general", "action:learn"]
```

## Default TTL
- Standard: 24 hours
- Extended by owner request: up to 1 year (`expires_at` = +365 days from `granted_at`)

## References
- See `references/lid-resolution.md` for the LID mapping lookup process.
