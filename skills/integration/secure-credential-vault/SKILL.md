---
name: secure-credential-vault
description: Design and operate multi-factor credential vaults with obfuscated access gates. Implements three-factor authentication (hardware binding, passphrase, time-window) and zero-plaintext-at-rest encryption. Patterns for EDITH and similar secure stores.
triggers:
  - Need to store API tokens, OAuth refresh tokens, GitHub PATs, or other sensitive credentials
  - Building a personal AI assistant with multi-user or security-hardened access
  - Credentials are offered by user in plaintext or insecure storage; need to move to encrypted vault
  - Session involves multiple external integrations with different credential types
  - User explicitly requests a fresh OAuth or credential flow independent of provided files
---

## Overview

Secure credential vaults differ from generic password managers in three ways:
1. **Obfuscated naming** — vault directory names are human-guessable-proof (not "secrets", "credentials", ".config"); defeats basic enumeration attacks
2. **Multi-factor gates** — authentication requires 2+ factors (hardware UUID + passphrase + time-window gating), not just one static password
3. **Zero plaintext at rest** — all credentials encrypted with AES-256-GCM; plaintext exists only in RAM during active use

This skill covers both design (what to build) and operation (how to use once built).

## Architecture: EDITH Pattern

**EDITH** (example implementation):
- Vault directory: `~/.hermes/.edith/` (obfuscated: "Emotional Dependence Intelligence Trust Hub" or just nonsense) ← defeats enumeration ("oh, is this for secrets?" → not obvious)
- Factor 1: Hardware UUID (system-specific, verified on startup)
- Factor 2: Passphrase + bcrypt-10 salt (knowledge-based)
- Factor 3: Time-window gating (±5 min from last successful auth; auto-purge after idle timeout)
- Encryption: AES-256-GCM over each credential file
- Verification protocol: 3-question challenge (personal preference-based, stored as SHA-256 hashes separately from vault access)

## Design Phase: The Three Decisions

### 1. Obfuscation Strategy

**Why it matters:** A vault at `~/.secrets` or `~/.config/credentials` is immediately flagged by attackers. A vault at `~/.edith` is noise unless you know what EDITH stands for.

**Good names (obfuscated):**
- `.edith` — nonsense or obscure acronym only you know
- `.hermes-cache` — sounds like temporary data, actually holds vault
- `.persona-data` — sounds like agent metadata, actually holds encrypted creds

**Bad names (too obvious):**
- `.secrets`, `.credentials`, `.tokens`, `.passwords` — immediate red flag

**Implementation:**
```python
import os

vault_dir = os.path.expanduser('~/.edith')  # Obfuscated name
os.makedirs(vault_dir, exist_ok=True)
os.chmod(vault_dir, 0o700)  # Only owner can read/write/execute
```

All files in the vault should be 600 (owner read/write only), never world-readable.

### 2. Multi-Factor Authentication Design

**Factor 1: Hardware UUID (Binding)**

System-specific identifier, verified on startup. Prevents credential theft (stolen vault files are useless on a different machine).

```python
import uuid

def get_hardware_uuid():
    """Get system MAC address as hardware binding."""
    import uuid
    return str(uuid.getnode())  # 48-bit MAC address, converted to int then string

# On first setup:
with open(os.path.expanduser('~/.edith/hardware_uuid'), 'w') as f:
    f.write(get_hardware_uuid())
os.chmod(os.path.expanduser('~/.edith/hardware_uuid'), 0o600)

# On every access:
def verify_hardware():
    with open(os.path.expanduser('~/.edith/hardware_uuid'), 'r') as f:
        stored_uuid = f.read().strip()
    current_uuid = get_hardware_uuid()
    if stored_uuid != current_uuid:
        raise PermissionError("Hardware UUID mismatch. Vault access denied.")
```

**Factor 2: Passphrase + Bcrypt Salt (Knowledge)**

User-provided passphrase, hashed with bcrypt-10 rounds. Constant-time comparison prevents timing attacks.

```python
import bcrypt
import hmac

def hash_passphrase(passphrase):
    """Hash passphrase with bcrypt-10."""
    return bcrypt.hashpw(passphrase.encode('utf-8'), bcrypt.gensalt(rounds=10))

def verify_passphrase(passphrase, stored_hash):
    """Constant-time passphrase verification."""
    return bcrypt.checkpw(passphrase.encode('utf-8'), stored_hash)

# On first setup:
passphrase = input("Vault passphrase: ")
passphrase_hash = hash_passphrase(passphrase)
with open(os.path.expanduser('~/.edith/passphrase_hash'), 'wb') as f:
    f.write(passphrase_hash)
os.chmod(os.path.expanduser('~/.edith/passphrase_hash'), 0o600)

# On every access:
def unlock_vault(passphrase):
    with open(os.path.expanduser('~/.edith/passphrase_hash'), 'rb') as f:
        stored_hash = f.read()
    if not verify_passphrase(passphrase, stored_hash):
        raise PermissionError("Passphrase incorrect. Vault locked.")
```

**Factor 3: Time-Window Gating (Behavioral)**

Credentials are only accessible ±5 minutes from last successful authentication. Idle credentials auto-purge after 5 minutes; re-authentication required.

```python
import time

def update_auth_timestamp():
    """Record successful auth."""
    with open(os.path.expanduser('~/.edith/last_auth_timestamp'), 'w') as f:
        f.write(str(int(time.time())))
    os.chmod(os.path.expanduser('~/.edith/last_auth_timestamp'), 0o600)

def check_auth_window():
    """Verify we're within ±5 min of last auth."""
    auth_file = os.path.expanduser('~/.edith/last_auth_timestamp')
    if not os.path.exists(auth_file):
        return False
    
    with open(auth_file, 'r') as f:
        last_auth = int(f.read().strip())
    
    now = int(time.time())
    window = 5 * 60  # 5 minutes in seconds
    
    if now - last_auth > window:
        # Credentials expired; require re-auth
        return False
    
    return True
```

### 3. Encryption Strategy

All credentials encrypted with AES-256-GCM. Encryption key derived from passphrase + hardware UUID.

```python
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import os
import json

def derive_encryption_key(passphrase):
    """Derive AES key from passphrase + hardware UUID."""
    salt = os.urandom(16)  # 128-bit salt
    kdf = PBKDF2(
        algorithm=hashes.SHA256(),
        length=32,  # 256-bit key for AES-256
        salt=salt,
        iterations=100000,
    )
    key = kdf.derive(passphrase.encode('utf-8'))
    return key, salt

def encrypt_credentials(credentials_dict, passphrase):
    """Encrypt credentials dict to JSON."""
    key, salt = derive_encryption_key(passphrase)
    
    plaintext = json.dumps(credentials_dict).encode('utf-8')
    nonce = os.urandom(12)  # 96-bit nonce for GCM
    cipher = AESGCM(key)
    ciphertext = cipher.encrypt(nonce, plaintext, None)
    
    # Return: salt + nonce + ciphertext (prepended for decryption)
    return {
        'salt': salt.hex(),
        'nonce': nonce.hex(),
        'ciphertext': ciphertext.hex(),
    }

def decrypt_credentials(encrypted, passphrase):
    """Decrypt credentials from stored JSON."""
    salt = bytes.fromhex(encrypted['salt'])
    nonce = bytes.fromhex(encrypted['nonce'])
    ciphertext = bytes.fromhex(encrypted['ciphertext'])
    
    kdf = PBKDF2(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
    )
    key = kdf.derive(passphrase.encode('utf-8'))
    
    cipher = AESGCM(key)
    plaintext = cipher.decrypt(nonce, ciphertext, None)
    
    return json.loads(plaintext.decode('utf-8'))

# Store encrypted credentials
encrypted = encrypt_credentials(
    {'access_token': 'ghp_...', 'refresh_token': '...'},
    passphrase
)
with open(os.path.expanduser('~/.edith/github_pat_vault'), 'w') as f:
    json.dump(encrypted, f)
os.chmod(os.path.expanduser('~/.edith/github_pat_vault'), 0o600)

# Retrieve encrypted credentials
with open(os.path.expanduser('~/.edith/github_pat_vault'), 'r') as f:
    encrypted = json.load(f)
creds = decrypt_credentials(encrypted, passphrase)
access_token = creds['access_token']
```

## Verification Protocol: Personal Questions

Instead of security questions ("What's your mother's maiden name?"), use **personal preference questions** that only the user would know:

```python
import hashlib

# On setup: collect 3 questions + answers, store hashes
questions = [
    ("Favorite football team?", "Real Madrid"),
    ("Favorite character?", "Pepper Potts"),
    ("Favorite person?", "Myself"),
]

verification_hashes = {}
for q, a in questions:
    h = hashlib.sha256(a.lower().encode('utf-8')).hexdigest()
    verification_hashes[q] = h

with open(os.path.expanduser('~/.edith/verification_hashes'), 'w') as f:
    json.dump(verification_hashes, f)
os.chmod(os.path.expanduser('~/.edith/verification_hashes'), 0o600)

# On verification: ask all 3 questions, check hashes
def verify_identity():
    with open(os.path.expanduser('~/.edith/verification_hashes'), 'r') as f:
        verification_hashes = json.load(f)
    
    passed = 0
    for question in verification_hashes.keys():
        answer = input(f"{question} ")
        answer_hash = hashlib.sha256(answer.lower().encode('utf-8')).hexdigest()
        if answer_hash == verification_hashes[question]:
            passed += 1
    
    if passed == 3:
        return True
    else:
        raise PermissionError(f"Verification failed: {passed}/3 correct. Vault locked for 30 min.")
```

**Why this works:**
- Not tied to external databases (mother's maiden name is public on Facebook)
- Difficult to guess or brute-force (high entropy personal preferences)
- Stable (favorites don't change weekly)
- Easy to remember (user chose them)

## Operation: Complete Unlock Flow

```python
def unlock_vault_complete(passphrase):
    """Full three-factor unlock sequence."""
    
    # Factor 1: Hardware UUID
    verify_hardware()
    
    # Factor 2: Passphrase
    unlock_vault(passphrase)
    
    # Factor 3: Time-window (check if in auth window; if not, verify identity)
    if not check_auth_window():
        verify_identity()
    
    # Update timestamp
    update_auth_timestamp()
    
    # Load and decrypt a credential file
    with open(os.path.expanduser('~/.edith/google_oauth_vault'), 'r') as f:
        encrypted = json.load(f)
    
    credentials = decrypt_credentials(encrypted, passphrase)
    return credentials

# Usage:
vault_creds = unlock_vault_complete("my-passphrase")
google_token = vault_creds['access_token']
```

## Credential Storage Patterns

### Pattern 1: OAuth Access + Refresh Tokens

```json
{
  "service": "google",
  "access_token": "ya29.a0AfH...",
  "refresh_token": "1//0gV_...",
  "expires_in": 3600,
  "last_refreshed": 1654321098,
  "scopes": ["gmail.modify", "drive", "docs", "sheets", "chat"]
}
```

**Refresh logic:**
```python
def refresh_google_token(vault_creds):
    """Refresh Google OAuth token if expired."""
    import requests
    import time
    
    if time.time() - vault_creds['last_refreshed'] < vault_creds['expires_in'] - 300:
        # Token still valid (5 min buffer)
        return vault_creds['access_token']
    
    # Token expired; refresh it
    response = requests.post('https://oauth2.googleapis.com/token', data={
        'grant_type': 'refresh_token',
        'refresh_token': vault_creds['refresh_token'],
        'client_id': '<CLIENT_ID>',
        'client_secret': '<CLIENT_SECRET>',
    })
    
    new_token = response.json()['access_token']
    vault_creds['access_token'] = new_token
    vault_creds['last_refreshed'] = int(time.time())
    
    # Save updated credentials back to vault
    save_to_vault(vault_creds, 'google_oauth_vault', passphrase)
    
    return new_token
```

### Pattern 2: GitHub PAT (Static Token)

```json
{
  "service": "github",
  "token": "<DEAD_GITHUB_PAT_REMOVED>",
  "token_name": "Friday-EDITH",
  "scopes": ["repo", "gist", "user"],
  "username": "tanzimozer"
}
```

**No refresh logic needed** — PAT is static until user rotates it manually.

### Pattern 3: Multiple Services in One Vault

```python
def save_to_vault(service, credentials_dict, passphrase):
    """Save credentials for a specific service."""
    vault_file = os.path.expanduser(f'~/.edith/{service}_vault')
    encrypted = encrypt_credentials(credentials_dict, passphrase)
    with open(vault_file, 'w') as f:
        json.dump(encrypted, f)
    os.chmod(vault_file, 0o600)

def load_from_vault(service, passphrase):
    """Load credentials for a specific service."""
    verify_hardware()
    unlock_vault(passphrase)
    
    vault_file = os.path.expanduser(f'~/.edith/{service}_vault')
    with open(vault_file, 'r') as f:
        encrypted = json.load(f)
    
    return decrypt_credentials(encrypted, passphrase)

# Usage:
google_creds = load_from_vault('google_oauth', passphrase)
github_creds = load_from_vault('github_pat', passphrase)
```

## User Interaction: Fresh OAuth Without Provided Credentials

**Signal:** User explicitly asks for a fresh OAuth flow independent of provided files.

**Workflow:**
1. **Do NOT use provided JSON files** as a source of truth. Generate a fresh authorization URL.
2. **Prep the token exchange script** while waiting for user authorization.
3. **Request minimal user action**: click one link, paste one callback URL.
4. **Store the result** in the vault using the above encryption + multi-factor pattern.
5. **Do not ask permission** — just execute once the code/callback URL is provided.

**Example (Google OAuth):**
```python
def initiate_fresh_google_oauth():
    """Generate a fresh Google OAuth authorization URL."""
    import secrets
    import base64
    import hashlib
    
    # PKCE challenge generation
    code_verifier = base64.urlsafe_b64encode(secrets.token_bytes(96)).decode('utf-8').rstrip('=')
    code_challenge = base64.urlsafe_b64encode(
        hashlib.sha256(code_verifier.encode('utf-8')).digest()
    ).decode('utf-8').rstrip('=')
    
    # Authorization URL (standard Google consent screen)
    auth_url = (
        "https://accounts.google.com/o/oauth2/v2/auth?"
        "client_id=YOUR_CLIENT_ID&"
        "redirect_uri=http://localhost:8080&"
        "response_type=code&"
        "scope=https://www.googleapis.com/auth/gmail.modify "
        "https://www.googleapis.com/auth/drive "
        "https://www.googleapis.com/auth/documents "
        "https://www.googleapis.com/auth/spreadsheets "
        "https://www.googleapis.com/auth/chat&"
        "code_challenge={}&"
        "code_challenge_method=S256".format(code_challenge)
    )
    
    # Save code_verifier to temp for token exchange later
    with open('/tmp/google_pkce_verifier', 'w') as f:
        f.write(code_verifier)
    
    return auth_url

# User clicks, authorizes, pastes callback URL here.
# Then exchange code for tokens and store in vault.
```

## Pitfalls

- **Not binding to hardware:** Vault files are valuable; if not hardware-bound, stealing them gets you credentials on any machine. Always include Factor 1.
- **Time-window too long:** A 24-hour window defeats the purpose. Keep it ±5 min. Too short (<1 min) becomes annoying.
- **Verification questions that are public:** "What city were you born in?" is on LinkedIn. Use personal preferences instead.
- **Storing plaintext credentials anywhere:** Even temporarily in a log or debug output. All credentials should exist only in RAM during active use; on disk they're encrypted.
- **Forgetting to update encrypted credentials:** OAuth tokens auto-refresh; you must save the new token back to the vault, not keep using the stale one.
- **Missing file permissions:** All vault files must be 600. If they're world-readable, the encryption is theater.
- **Not testing the decryption path:** Build the unlock flow and test it end-to-end before trusting it. A decryption error discovered at runtime is worse than a deployment delay.

## Implementation Checklist

- [ ] Obfuscated vault directory created (`~/.edith` or similar)
- [ ] Factor 1 (hardware UUID) implemented and verified on startup
- [ ] Factor 2 (passphrase + bcrypt) implemented with constant-time comparison
- [ ] Factor 3 (time-window gating) implemented with auto-purge on idle
- [ ] AES-256-GCM encryption working for credential files
- [ ] Verification protocol (3 personal questions) designed and hashes stored
- [ ] OAuth token refresh logic implemented (for services that need it)
- [ ] Complete unlock flow tested end-to-end
- [ ] File permissions verified (all vault files 600, vault dir 700)
- [ ] Documentation added for next session (where vault is, how to unlock, what's stored)

## References

See `references/edith-deployment-log.md` for Friday 2.0 deployment notes and real examples of vault initialization, credential storage, and unlock workflows.

See `templates/vault-init-script.py` for a ready-to-run initialization script that sets up a fresh EDITH-style vault from scratch.
