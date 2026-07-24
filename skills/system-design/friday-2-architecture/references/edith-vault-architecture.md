# EDITH Vault Architecture

**EDITH** = Encrypted Distributed Identity Token Handler

## Overview

Secure credential storage for Google API keys, GitHub PATs, MCP tool secrets, and other soft credentials. Designed to be human-guessable-proof: even if an attacker breaches the filesystem, they cannot know what to target.

## Naming Strategy (Obfuscation by Misdirection)

**Why "EDITH":**
- Reverse acronym that sounds like a legitimate system config or user name
- Defeats keyword-based filesystem enumeration (attackers search for "vault", "secret", "credential", "key" — finds nothing)
- Distributed challenge factors across multiple filesystem paths (no single "vault" file)
- Semantic misdirection defeats automated scanning

**How it works:**
```
Attacker's enumeration search:
  grep -r "secret\|vault\|credential\|key" /home/hermes/
  → Finds nothing (EDITH is stored under benign paths)

Filesystem looks like:
  /home/hermes/.config/edith/
  /home/hermes/.edith/
  ~/.local/share/edith/
  → All appear as legitimate config directories

Actual structure:
  - Three-factor challenge stored across distributed paths
  - No plaintext anywhere
  - Even intermediate values hashed
```

## Access Protocol (3-Factor)

### 1. Possession Challenge
- Hardware UUID verification
- Must match enrolled device
- No alternative bypass

### 2. Knowledge Challenge
- User passphrase + salt verification
- SHA-256 hashed comparison
- Constant-time comparison (side-channel hardening)

### 3. Behavior Challenge
- Time window validation (±5 min from last successful access)
- Nonce + timestamp verification
- Replay attack protection

**Access decision:** All three must pass. Failure on any → complete denial, no fallback.

## Storage Format

### Encrypted Blob Structure
```
[16-byte header (nonce, version, magic)]
[Encrypted JSON payload (per-credential encryption)]
[16-byte GCM authentication tag]
```

### Encryption Details
- Algorithm: AES-256-GCM
- Key derivation: PBKDF2 (100,000 iterations, SHA-256)
- Per-credential encryption: yes (each secret encrypted separately)
- Authentication: GCM tag prevents tampering
- Replay protection: nonce + timestamp + behavioral window

### Credential Structure (Encrypted)
```json
{
  "credential_id": "goog-oauth-key-001",
  "type": "google-api-key",
  "secret": "[encrypted]",
  "metadata": {
    "created_at": "2025-06-07T18:39:00Z",
    "expires_at": "2026-06-07T18:39:00Z",
    "rotation_required": false,
    "scope": ["sheets", "drive"]
  },
  "access_log": "[encrypted hash only, never plaintext]"
}
```

## Security Properties

| Threat | Mitigation |
|--------|-----------|
| Plaintext extraction | AES-256-GCM encryption, per-credential encryption |
| Tampering | GCM authentication tag, cryptographic validation |
| Replay attacks | Nonce + timestamp + behavioral window |
| Side-channel attacks | Constant-time comparisons, no conditional branches on secret data |
| Enumeration attacks | Obfuscated naming (EDITH), distributed storage, no "vault" keyword |
| Credential rotation | Metadata tracks expiration, rotation requirements flagged async |

## Expiration & Auto-Purge

- **Idle timeout:** 5 minutes (credentials auto-purged if no access)
- **Credential lifetime:** Per-secret metadata (default 1 year)
- **Rotation tracking:** Metadata flags when rotation is due
- **Audit-only logging:** Access logs encrypted, never consulted for access decisions

## Verification Protocol (Tanzim)

Three unconventional questions, stored separately from vault:

```
Q1: Favourite football team? A: Real Madrid
Q2: Favourite character? A: Pepper Potts
Q3: Favourite person? A: Myself
```

Answers hashed, verified via EDITH access gate. This is the only human-memorable path into the vault.

## Implementation Checklist

- [ ] Define hardware UUID enrollment process
- [ ] Generate PBKDF2-derived key from passphrase
- [ ] Implement AES-256-GCM encryption / decryption
- [ ] Set up distributed storage paths (benign names)
- [ ] Implement three-factor access gate
- [ ] Add time window validation
- [ ] Implement constant-time comparison for secrets
- [ ] Set up 5-minute idle expiration
- [ ] Create credential rotation tracking
- [ ] Log access (encrypted hashes only)
- [ ] Test replay attack scenarios
- [ ] Document credential lifecycle (add, update, rotate, revoke)

## Related Files

- `references/tanzim-framework-schema.yaml` — Personal framework (how to identify Tanzim)
- GitHub repo: `tanzimozer/Tanzim_Frameworks` (stores verification logic)

---

**Status:** Design complete. Implementation pending Tanzim approval.
