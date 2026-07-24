# EDITH Vault Access & Decryption

## Current Status (as of June 2026)
EDITH vault (`~/.hermes/.edith/edith_vault.json`) is encrypted with AES-256-GCM and requires 3-factor authentication:
1. Hardware UUID (at `~/.hermes/.edith/hardware_uuid`) — automatic
2. Passphrase (bcrypt-10 hashed at `~/.hermes/.edith/passphrase_hash`) — **requires user input**
3. Time-window gating (±5 min from last successful auth, auto-purge after 5 min idle)

## Known Gap
**AI agent cannot decrypt vault without user passphrase.** Security questions (answers stored in hindsight memory) are only one of three factors. The passphrase itself is NOT stored anywhere accessible to the agent — it must be provided by the user at runtime.

### What's in EDITH Vault
- GitHub PAT (account: tanzimozer, scopes: repo/gist/user)
- Encrypted OAuth backup credentials
- Other sensitive tokens not yet mapped

### What's NOT in EDITH (stored in vault.json instead)
- iCloud credentials (app password)
- Webflow API token
- Wix API key
- Instagram cookies
- WhatsApp bridge token
- Anthropic/Hindsight API keys

## Workaround Pattern for Agent (June 2026 Session)
When EDITH vault is needed but agent can't decrypt:
1. Agent retrieves security question answers from hindsight memory
2. Agent prompts user for passphrase
3. User provides passphrase
4. Agent (or external script) decrypts vault using: `passphrase + hardware_uuid + security_answers`
5. Agent extracts needed credential

**This is not a failure of the vault design — it's correct.** The passphrase IS the human factor in 3FA. Agent can orchestrate the unlock but cannot bypass it.

## Future Enhancement
Consider a "bootstrap" pattern:
- On first session, agent acquires EDITH passphrase from user (mark as session-secret, not persistent)
- Agent attempts EDITH unlock once per session (cached decrypted state for that session only)
- On idle timeout or new session, re-ask for passphrase

This would reduce repeated "give me passphrase" prompts without weakening security.

## Related
- vault_access SKILL.md — credential reading (vault.json, google_token.json)
- Tanzim's security questions (in hindsight): Q1=Real Madrid, Q2=Pepper Potts, Q3=Myself
