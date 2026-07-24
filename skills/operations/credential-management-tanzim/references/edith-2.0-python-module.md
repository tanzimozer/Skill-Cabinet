# EDITH 2.0 Python Module Implementation

**Session:** June 9, 2026 (Claude Code)  
**Status:** Complete and tested  
**Module Location:** `/home/hermes/edith.py`  
**Module Size:** ~650 lines, fully documented

## Overview

EDITH 2.0 is a hardware-bound encrypted credential vault module written in pure Python. It provides:
- Automatic hardware UUID key derivation (no passphrase required)
- Fernet (AES-256-GCM) encryption per credential
- Obfuscated service name mapping to prevent enumeration
- 3/3 Q&A verification protocol for sensitive operations
- Complete audit logging of all vault access

## Architecture

### Five Core Engines

1. **EncryptionEngine**
   - Key derivation: PBKDF2HMAC(hardware_uuid + salt, 100k iterations)
   - Cipher: Fernet (AES-256-GCM)
   - Per-credential encryption (not whole-vault)
   - Input: plaintext dict, Output: base64 Fernet token

2. **ObfuscationEngine**
   - Service name obfuscation: SHA256(service_name + hardware_uuid)[:12]
   - Prevents external reconnaissance of stored services
   - Deterministic (same service → same obfuscated key every time)

3. **VerificationEngine**
   - 3-question challenge protocol
   - Answers: "Real Madrid", "Pepper Potts", "Myself"
   - Case-insensitive matching
   - Returns bool: True if 3/3 correct

4. **AccessLogger**
   - Tracks: operation, service, status, timestamp
   - Aggregated stats: access_count, failed_attempts
   - Persisted to `access.log` (JSON)

5. **EDITHVault** (Main Class)
   - High-level API: get_credential(), set_credential(), delete_credential()
   - Initialization: requires vault_dir, optionally validates against current hardware UUID
   - Automatic decryption on correct machine
   - Raises KeyError/ValueError on missing/corrupt credentials

### File Structure

```
~/.hermes/.edith/
├── metadata.json           # Vault config (version, hardware UUID, encryption)
├── vault.enc               # JSON: {obfuscated_key: fernet_token}
├── services.map            # JSON: {service_name: obfuscated_key}
├── verification.enc        # Encrypted Q&A answers (not implemented in basic version)
└── access.log              # JSON: {created, last_accessed, access_count, failed_attempts}
```

## Implementation Notes

### Critical Fix: Cryptography Imports

The module uses `PBKDF2HMAC` not `PBKDF2`:
```python
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
```

(Historical note: PBKDF2 class was renamed in recent cryptography versions. Always check available imports before using.)

### Vault Format: JSON with Individual Token Encryption

Unlike a single whole-vault token, EDITH 2.0 stores:
```json
{
  "010a8b57f505": "gAAAAA...ClA=",  // obfuscated_key: fernet_token
  "00b6e9433720": "gAAAAA...XyZ=",
  ...
}
```

Each credential encrypted independently. On load, the module decrypts all tokens and reconstructs the plaintext vault in memory.

### Services Map Format

Must map `service_name → obfuscated_key` (NOT the reverse):
```json
{
  "google": "00b6e9433720",
  "github": "a3333f2c53e6",
  "icloud": "7ae9d03de9f7"
}
```

This allows quick lookup: given service name, find obfuscated key, decrypt that entry.

### Hardware UUID Binding

- Automatic: `uuid.getnode()` returns MAC address as integer string
- Vault stores this UUID in metadata
- Key derivation uses: `PBKDF2HMAC(hardware_uuid + salt, 100k iterations)`
- **Result:** Vault decrypts ONLY on the machine it was created on
- Cannot be transferred to different hardware without re-encryption

### Verification Protocol

3 questions, must answer all 3 correctly:
1. "Real Madrid"
2. "Pepper Potts"
3. "Myself"

Enforced at credential read/write/delete when `verify=True`.
Can be bypassed for testing with `verify=False`.

## Usage

### Minimal Example

```python
from edith import EDITHVault
from pathlib import Path

# Initialize vault (uses ~/.hermes/.edith by default)
vault = EDITHVault(require_verification=False)

# Store credential
vault.set_credential('github', {'token': 'ghp_...'}, verify=False)

# Retrieve credential
creds = vault.get_credential('github', verify=False)
print(creds['token'])

# List all services
services = vault.list_services()
# → ['github', 'google', ...]

# Delete credential
vault.delete_credential('github', verify=False)
```

### With Verification Enforced

```python
vault = EDITHVault(require_verification=True)

# This will prompt for Q&A before allowing access
creds = vault.get_credential('github')  
# → "Q: Favourite football team? " (user must answer 3/3)
```

### Custom Vault Directory (for Testing)

```python
from pathlib import Path

vault = EDITHVault(vault_dir=Path('/tmp/test-edith'), require_verification=False)
```

### Vault Statistics

```python
stats = vault.get_vault_stats()
# → {
#   'services': 9,
#   'hardware_uuid': '8495916...',
#   'encryption': 'Fernet (AES-256-GCM)',
#   'access_count': 15,
#   'failed_attempts': 2,
#   'created': '2026-06-10',
#   'last_accessed': '2026-06-10T14:32:05Z'
# }
```

## Testing Checklist

When creating a new vault or modifying the module:

- [ ] Vault directory exists with all 5 files
- [ ] Metadata version is "2.0"
- [ ] Hardware UUID matches current machine
- [ ] vault.enc parses as JSON
- [ ] services.map is valid JSON
- [ ] Can instantiate EDITHVault without errors
- [ ] Can list services (even if empty)
- [ ] Can set credential without verification
- [ ] Can get credential and verify data matches
- [ ] Can delete credential
- [ ] Vault integrity check passes
- [ ] Access log updates on operations

## CLI Interface

```bash
# List services
python3 edith.py list

# Get credential (prompts for verification)
python3 edith.py get github

# Store credential
python3 edith.py set myservice --token "token_value"

# Delete credential
python3 edith.py delete github

# View statistics
python3 edith.py stats

# View access log
python3 edith.py log

# Verify integrity
python3 edith.py verify

# Use alternate vault directory
python3 edith.py --vault /tmp/test-edith list
python3 edith.py --no-verify set test '{"data":"value"}'
```

## Pitfalls & Workarounds

### Pitfall 1: Hardware UUID Mismatch

**Problem:** Vault was created on Machine A, trying to decrypt on Machine B.

**Error:** `InvalidToken` from Fernet decrypt

**Fix:** Either:
- Transfer vault back to Machine A
- Or re-encrypt vault with Machine B's UUID (requires decrypting with old key first)

**Code to detect:**
```python
import uuid
current = str(uuid.getnode())
if vault.hardware_uuid != current:
    print("WARNING: Vault created on different machine")
    print(f"  Current: {current}")
    print(f"  Vault:   {vault.hardware_uuid}")
```

### Pitfall 2: Services Map Mapping Wrong Direction

**Problem:** Code had `services_map[obfuscated_key] = service_name` instead of reverse.

**Symptom:** Credential stored successfully but cannot be retrieved → `KeyError: Service not found`

**Fix:** Ensure mapping is always `service_name → obfuscated_key`:
```python
# CORRECT
self.services_map[service_name] = obfuscated_key

# WRONG
self.services_map[obfuscated_key] = service_name
```

### Pitfall 3: Vault Paths Hardcoded

**Problem:** Module had global `VAULT_DIR = Path.home() / '.hermes' / '.edith'`

**Result:** Test vault at `/tmp/test-edith` ignored; module always used default directory

**Fix:** Make vault_dir dynamic parameter:
```python
def __init__(self, vault_dir: Path = None, ...):
    if vault_dir is None:
        vault_dir = DEFAULT_VAULT_DIR
    self.vault_dir = Path(vault_dir)
    # Then use self.vault_dir everywhere
```

### Pitfall 4: Empty Vault Causes Decryption Errors

**Problem:** When vault.enc contains `{}`, code tried to decrypt empty string as Fernet token.

**Fix:** Check JSON structure:
```python
vault_json = json.load(f)  # Already parsed
for obfuscated_key, fernet_token in vault_json.items():
    # Only decrypt if items exist
    decrypted = self.encryption.decrypt(fernet_token)
```

Empty dict `{}` is valid JSON and iterates over zero items — no problem.

## Integration with Friday 2.0 Core

The module is designed for import by Friday 2.0:

```python
# In Friday core code
from edith import EDITHVault

class CredentialManager:
    def __init__(self):
        self.vault = EDITHVault(require_verification=True)
    
    def get_service_token(self, service: str) -> str:
        cred = self.vault.get_credential(service)
        return cred.get('token')
```

Module is:
- ✅ Fully importable
- ✅ No external dependencies beyond cryptography (standard package)
- ✅ Type hints throughout
- ✅ Error messages descriptive
- ✅ Can disable verification for automation (background jobs, crons)
- ✅ Audit logging for all operations

## Future Enhancements (Not in Scope)

- [ ] Verification.enc encryption (currently placeholder)
- [ ] Credential rotation scheduling
- [ ] Backup/recovery procedures
- [ ] Cross-machine migration (re-encryption tooling)
- [ ] Hardware UUID binding confirmation on first initialization
- [ ] Rate limiting on failed verification attempts

---

**Created:** June 9, 2026  
**Module:** `/home/hermes/edith.py`  
**Tests Passed:** Store/retrieve/delete cycle verified  
**Status:** Production-ready for Friday 2.0 core integration
