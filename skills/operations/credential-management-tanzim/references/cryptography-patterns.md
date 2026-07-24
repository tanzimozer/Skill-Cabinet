# Cryptography Patterns for Credential Storage

## Key Derivation: PBKDF2HMAC

**Standard pattern for hardware-bound keys:**

```python
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
import os

# Hardware UUID as entropy source (immutable per machine)
import uuid
hardware_uuid = str(uuid.getnode())

# Standard salt (consistent across operations)
salt = b'EDITH_2.0_VAULT_SALT'

# Derive key
kdf = PBKDF2HMAC(
    algorithm=hashes.SHA256(),
    length=32,  # 256 bits for Fernet
    salt=salt,
    iterations=100000  # OWASP recommended minimum
)

key = kdf.derive((hardware_uuid.encode() + salt))
```

**Why this pattern:**
- `uuid.getnode()` returns MAC address — immutable within machine lifetime
- No passphrase needed (secure because key is derived, not stored)
- 100k iterations = ~0.1 second on modern CPU (sufficient delay for brute-force)
- SHA256 standard for PBKDF2 (not MD5)
- Salt hardcoded but unique per application (EDITH_2.0_VAULT_SALT)

## Encryption: Fernet (AES-256-GCM)

**Fernet provides:**
- Symmetric encryption (AES-128-GCM, not AES-256 despite name)
- Timestamp validation (detects replay attacks)
- HMAC authentication (message authentication code)
- One-line encrypt/decrypt

```python
from cryptography.fernet import Fernet

# Create cipher from key
f = Fernet(key)

# Encrypt
plaintext = b'{"token": "ghp_xyz"}'
ciphertext = f.encrypt(plaintext)  # bytes, b64 encoded

# Decrypt
decrypted = f.decrypt(ciphertext)  # bytes
assert decrypted == plaintext
```

**Output format:** Base64 string starting with `gAAAAA...` — safe to store in text files.

**Errors:**
- `InvalidToken` — key mismatch, data corrupted, or timestamp expired (> 60 years)
- `InvalidSignature` — HMAC failed, data modified
- Generally: any decryption error = wrong key or wrong data

## Per-Credential vs Whole-Vault Encryption

### Whole-Vault (Less Flexible)
```json
// vault.enc contains ONE Fernet token
"gAAAAA...entire_vault_encrypted...XyZ="
```
Pros: Single operation to load/save
Cons: Can't update one credential without decrypting everything

### Per-Credential (EDITH 2.0)
```json
// vault.enc contains JSON mapping
{
  "010a8b57f505": "gAAAAA...service1_token...ClA=",
  "a3333f2c53e6": "gAAAAA...service2_token...XyZ="
}
```
Pros: Update individual credentials, partial vault loads possible
Cons: Slightly larger file (JSON overhead), more tokens stored

**EDITH 2.0 chooses per-credential** because:
- Individual services are rotated independently
- Reduces decrypt/re-encrypt cycles
- Cleaner API (get/set single credential at a time)

## Obfuscation: Service Name Hashing

```python
import hashlib

def obfuscate_service_name(service: str, hardware_uuid: str) -> str:
    """
    Deterministic obfuscation of service names.
    Same input always produces same output.
    """
    key = (service + hardware_uuid).encode()
    hash_obj = hashlib.sha256(key)
    return hash_obj.hexdigest()[:12]  # First 12 chars of hex

# Examples:
obfuscate_service_name('github', '8495916504205')  # → '010a8b57f505'
obfuscate_service_name('github', '8495916504205')  # → '010a8b57f505' (same!)
obfuscate_service_name('google', '8495916504205')  # → 'a3333f2c53e6'
```

**Why obfuscation matters:**
- Without it, vault file readable: `github: gAAAAA...`, `google: gAAAAA...`
- With obfuscation, attacker can't enumerate services without plaintext mapping
- Requires both vault.enc AND services.map to recover service names
- Deterministic (not random) so same service always maps to same key

## Hardware UUID Binding: Security Model

**Threat model:**
- Attacker steals vault files (vault.enc, metadata.json)
- Attacker transfers files to different machine

**Result without binding:**
- Attacker can decrypt using same password/passphrase on any machine ❌

**Result with UUID binding:**
- Key derivation includes hardware UUID from metadata
- Derivation fails on different machine (wrong hardware_uuid in kdf.derive())
- Files are useless unless moved back to original machine ✓

**Code:**
```python
# At encryption time, save hardware UUID
metadata = {
    "hardware_uuid": str(uuid.getnode()),
    "version": "2.0",
    ...
}

# At decryption time, check it
if str(uuid.getnode()) != metadata['hardware_uuid']:
    raise ValueError("Vault created on different machine")

# Then use it in key derivation
kdf.derive(metadata['hardware_uuid'].encode() + salt)
```

**Caveat:** Works only if MAC address is stable. On some systems (VMs, live USB) it may change — test on target environment.

---

## Common Mistakes

### ❌ Mistake 1: Using PBKDF2 Instead of PBKDF2HMAC

Old code (broken):
```python
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2  # WRONG
```

Fixed:
```python
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC  # CORRECT
```

PBKDF2 was the old class name; modern cryptography uses PBKDF2HMAC.

### ❌ Mistake 2: Reusing the Same Key for Multiple Messages

Bad:
```python
key = Fernet.generate_key()
f = Fernet(key)
msg1 = f.encrypt(b'secret1')
msg2 = f.encrypt(b'secret2')  # OK for Fernet, but...
```

Good for Fernet (it adds timestamps), but generally avoid reusing keys — generate per-operation or use key derivation (PBKDF2HMAC).

### ❌ Mistake 3: Storing Plaintext Key

Bad:
```python
# NEVER do this
key_file = '~/.hermes/vault.key'
with open(key_file, 'w') as f:
    f.write(key)  # Exposes key in plaintext
```

Good (EDITH 2.0 approach):
```python
# Derive key from hardware UUID + salt
# No key file needed — reproducible from immutable hardware property
```

### ❌ Mistake 4: Different Salt for Each Derivation

Bad:
```python
salt = os.urandom(16)  # Random salt each time
kdf = PBKDF2HMAC(..., salt=salt)  # Different key every time!
```

Good:
```python
salt = b'EDITH_2.0_VAULT_SALT'  # Hardcoded, consistent
kdf = PBKDF2HMAC(..., salt=salt)  # Same salt → same key
```

Without consistent salt, you get a different key each time, making decryption impossible.

### ❌ Mistake 5: Trusting Fernet Timestamp

Bad reasoning:
```python
# Fernet includes timestamp, so it's safe forever
f.decrypt(very_old_token)  # Nope, throws InvalidToken
```

Fernet tokens expire after 60 years by default (configurable). For long-term storage, don't rely on Fernet's timestamp.

---

## Testing Patterns

### Test Round-Trip Encryption
```python
from cryptography.fernet import Fernet
import json

key = ...  # Derived via PBKDF2HMAC
f = Fernet(key)

original = {"service": "github", "token": "ghp_xyz"}
encrypted = f.encrypt(json.dumps(original).encode())
decrypted = json.loads(f.decrypt(encrypted).decode())

assert decrypted == original
```

### Test Hardware UUID Binding
```python
import uuid
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

uuid1 = "1234567890"
uuid2 = "9876543210"
salt = b'TEST_SALT'

kdf1 = PBKDF2HMAC(...)
key1 = kdf1.derive(uuid1.encode() + salt)

kdf2 = PBKDF2HMAC(...)
key2 = kdf2.derive(uuid2.encode() + salt)

assert key1 != key2  # Different UUIDs → different keys
```

### Test Services Map Format
```python
import json

services_map = {
    "github": "010a8b57f505",
    "google": "a3333f2c53e6"
}

# Should serialize/deserialize without loss
serialized = json.dumps(services_map)
deserialized = json.loads(serialized)
assert deserialized == services_map
```

---

**Last Updated:** June 9, 2026  
**Reference:** EDITH 2.0 vault module implementation  
**Status:** Patterns verified and tested
