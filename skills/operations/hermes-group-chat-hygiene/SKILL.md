---
name: hermes-group-chat-hygiene
description: How to suppress Hermes backend system alerts (file-mutation verifier, curator, Tirith) from leaking into WhatsApp group chats with end-users
category: operations
tags: [hermes, whatsapp, groups, config, alerts, hygiene]
---

# Hermes Group Chat Hygiene

## Trigger

Use this skill when:
- Backend system messages (⚠️ verifier alerts, "self-improvement review", Tirith notices) are appearing in a WhatsApp group chat with end-users
- Tanzim asks to clean up or suppress system noise from a group chat

## The Problem

Hermes surfaces two types of backend alerts into group chats by default:
1. **File-mutation verifier footer** — appended when a `write_file` / `patch` call failed during a turn. Appears as a ⚠️ block with a file list.
2. **Self-improvement review / curator** — background skill-curation notices that can surface as system messages.

These are useful in the CLI/owner-only context but must not leak to end-users (clients, family members, students).

## The Fix

Two config keys in `~/.hermes/config.yaml`:

```yaml
# Under the display: block
display:
  file_mutation_verifier: false   # suppresses ⚠️ file-mutation footer

# Top-level
curator:
  enabled: false                  # suppresses background self-improvement review
```

### Exact patch steps

```python
# 1. Suppress file-mutation verifier — add under display: section
# Find: "  tool_progress: none"
# Add after: "  file_mutation_verifier: false"

# 2. Suppress curator — add as top-level key after hooks block
# Find: "hooks: {}\nhooks_auto_accept: false"
# Add after: "curator:\n  enabled: false"
```

Use the `patch` tool on `/home/hermes/.hermes/config.yaml`. Takes effect on next session restart.

## Pitfalls

- **Tirith** is a compiled binary (`~/.hermes/bin/tirith`) — cannot be suppressed via config edit. The verifier and curator cover the two alerts that actually leak into chat; Tirith alerts are internal.
- **`/root/.hermes/`** — doesn't exist. The Hermes user home is `/home/hermes/`. Always use `/home/hermes/.hermes/config.yaml`.
- Config changes take effect on **next gateway restart** — not immediately.

## References

- See `references/alert-types.md` for a breakdown of each alert type and its source.
