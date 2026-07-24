# Hermes Alert Types — Group Chat Leak Reference

## File-Mutation Verifier Footer

- **Source:** `agent/conversation_loop.py` → `run_agent.py:1815`
- **Config key:** `display.file_mutation_verifier` (bool, default: `true`)
- **Trigger:** Any `write_file` or `patch` call that failed during a turn and was not superseded by a successful write to the same path
- **Appearance:** `⚠️ File-mutation verifier: N file(s) were NOT modified...` followed by bullet list of paths
- **Suppression:** `file_mutation_verifier: false` under `display:` in `config.yaml`

## Self-Improvement Review / Curator

- **Source:** `tools/skill_provenance.py`, `hermes_cli/config.py` → curator block
- **Config key:** `curator.enabled` (bool, default: `true`)
- **Trigger:** Background fork after sessions — reviews agent-created skills, marks stale/archivable
- **Appearance:** "Self-improvement review: User profile updated" or similar
- **Suppression:** `curator:\n  enabled: false` as top-level key in `config.yaml`

## Tirith Security Layer

- **Source:** `~/.hermes/bin/tirith` — compiled ELF binary
- **Config key:** `security.tirith_enabled` (but disabling this affects security, not recommended)
- **Suppression:** Not suppressable without disabling security checks — generally not an issue in group chats (Tirith alerts are internal to the agent loop, not typically forwarded to WhatsApp)

## Notes

- `file_mutation_verifier` defaults to `true` — intentional for CLI/dev use, not appropriate for end-user group chats
- `curator.enabled` can be re-enabled if Tanzim wants background skill curation to resume; the "Learn AI" group suppression was done because the notice leaked as a visible WhatsApp message
