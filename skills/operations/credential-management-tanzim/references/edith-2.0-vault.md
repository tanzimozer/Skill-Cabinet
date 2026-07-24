# EDITH 2.0 Vault — Hardware-Bound Encryption

**Updated:** June 10, 2026

## Overview
EDITH 2.0 is a credential vault that uses hardware UUID binding instead of passphrases. All credentials encrypted at rest, but decryption requires the specific machine (no passphrase needed).

## Architecture

### Three-Factor Security
1. **Hardware UUID Binding** — Encryption key derived from machine MAC address only
2. **Verification Protocol** — Q&A challenge for sensitive operations (2/3 required)
3. **Access Logging** — Track reads/writes to vault

### Key Derivation
- Algorithm: SHA256-based key stretching (100k iterations)
- Input: Hardware UUID + fixed salt (`EDITH_2.0_VAULT`)
- Output: 256-bit encryption key (Fernet-compatible)
- **NO passphrase required** — decrypts automatically on correct machine

### Verification Protocol
Three security questions (answers encrypted separately):
- Q1: Real Madrid
- Q2: Pepper Potts
- Q3: Myself
- Required: 2 out of 3 correct answers

## Implementation

### Setup
```python
import uuid
import hashlib
from cryptography.fernet import Fernet

hardware_uuid = str(uuid.getnode())  # MAC address
salt = b'EDITH_2.0_VAULT'
key_material = hashlib.sha256(f"{hardware_uuid}_{salt.decode()}".encode()).digest()

# Strengthen with iteration
for _ in range(100000):
    key_material = hashlib.sha256(key_material).digest()

key = base64.urlsafe_b64encode(key_material[:32])
cipher = Fernet(key)
```

### File Structure
```
~/.hermes/.edith/
├── metadata.json          # Vault config, hardware UUID, version
├── vault.enc              # Encrypted credentials (obfuscated keys)
├── services.map           # Service name → obfuscated key mapping
├── verification.enc       # Encrypted Q&A answers
├── access.log             # Read/write audit trail
└── .recovery              # Recovery instructions
```

### Credential Obfuscation
Service names are obfuscated in vault.enc:
```python
obfuscated_key = hashlib.sha256(f"{service}_{hardware_uuid}".encode()).hexdigest()[:12]
```
This prevents external reconnaissance of what services are stored.

## Usage

### Access Pattern
1. Read metadata.json (unencrypted) to confirm vault version
2. Derive encryption key from hardware UUID automatically (no user input)
3. Decrypt vault.enc using derived key
4. Look up service in services.map to find obfuscated key
5. Return decrypted credential

### Sensitive Operations (Q&A Challenge)
When accessing highly sensitive credentials (like admin tokens):
1. Ask: Q1, Q2, or Q3 (randomly selected)
2. Verify answer matches encrypted verification.enc
3. Log attempt (success/failure) to access.log
4. Only return credential if 2/3 correct (across multiple attempts if needed)

### No Passphrase Required
- ✓ Automatic decryption on correct machine
- ✓ No user passphrase needed
- ✓ Unattended operation (crons, background jobs)
- ✗ Cannot be decrypted on different machines (hardware-locked)

## Migration from Plaintext
When moving credentials from plaintext vault.json to EDITH 2.0:
1. Generate new hardware UUID key
2. Encrypt each credential in plaintext vault
3. Obfuscate service names
4. Save to vault.enc with services.map
5. Delete plaintext vault after confirming all credentials decryptable
6. Update vault location in code/config

## Current Status (Jun 10, 2026)
- ✅ Vault initialized at ~/.hermes/.edith
- ✅ Hardware UUID: 244019394735095
- ✅ 9 services migrated and encrypted
- ✅ Verification protocol configured
- ✅ Access logging enabled
- ✅ No passphrase in use (automatic decryption)

## Recovery
If vault becomes inaccessible:
1. Hardware UUID can be regenerated from machine (uuid.getnode())
2. Recompute encryption key from UUID + salt
3. If key derivation changed, re-encrypt vault with new method
4. Access log shows when last decrypted (can rollback if corrupted)

## Differences from Original EDITH
| Aspect | Original EDITH | EDITH 2.0 |
|--------|---|---|
| Encryption | AES-256-GCM | Fernet (AES-256-GCM wrapper) |
| Key Source | Passphrase + salt | Hardware UUID only |
| Passphrase Required | Yes | No |
| Unattended Access | No | Yes |
| Portability | Cross-machine | Hardware-locked |
| Verification | Optional | Always on (Q&A) |
| Setup Complexity | High | Low |
