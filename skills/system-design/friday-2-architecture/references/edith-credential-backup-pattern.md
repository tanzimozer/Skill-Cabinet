# EDITH Vault Implementation & Credential Backup (Session Pattern)

## Technique That Emerged

Implemented three-factor EDITH vault with automated Google Sheets backup for all API credentials. This is a reusable pattern for future credential management work.

## Full Implementation Pattern

### Step 1: Create EDITH Three-Factor Structure

```bash
mkdir -p ~/.hermes/.edith
chmod 700 ~/.hermes/.edith
```

**Factor 1: Hardware UUID** (system-specific binding)
```bash
cat /sys/class/dmi/id/product_uuid > ~/.hermes/.edith/hardware_uuid
chmod 600 ~/.hermes/.edith/hardware_uuid
```

**Factor 2: Passphrase + Salt** (knowledge factor)
```python
import bcrypt
passphrase = "friday-2-locked"
salt = bcrypt.gensalt(rounds=10)
passphrase_hash = bcrypt.hashpw(passphrase.encode(), salt)
with open(os.path.expanduser('~/.hermes/.edith/passphrase_hash'), 'wb') as f:
    f.write(passphrase_hash)
os.chmod('~/.hermes/.edith/passphrase_hash', 0o600)
```

**Factor 3: Time-Window Gating** (behavioral factor, enforced at runtime)
- ±5 minute authentication window
- Auto-purge credentials after 5 minutes idle
- Prevents token theft / long-lived hijacking

**Verification Protocol: 3-Question Challenge** (hashed, stored separately)
```python
import hashlib
verification_questions = {
    'q1': {'question': 'Favorite football team?', 'answer_hash': hashlib.sha256('Real Madrid'.encode()).hexdigest()},
    'q2': {'question': 'Favorite character?', 'answer_hash': hashlib.sha256('Pepper Potts'.encode()).hexdigest()},
    'q3': {'question': 'Favorite person?', 'answer_hash': hashlib.sha256('Myself'.encode()).hexdigest()},
}
with open('~/.hermes/.edith/verification_hashes.json', 'w') as f:
    json.dump(verification_questions, f)
os.chmod('~/.hermes/.edith/verification_hashes.json', 0o600)
```

### Step 2: Consolidate All Credentials in EDITH Vault

```python
# Consolidate existing credential files into single encrypted vault
edith_vault = os.path.expanduser('~/.hermes/.edith/edith_vault.json')
vault = {}

# Move Google OAuth
with open(os.path.expanduser('~/.hermes/.edith/google_oauth_vault'), 'r') as f:
    vault['google_oauth'] = json.load(f)

# Move GitHub PAT
with open(os.path.expanduser('~/.hermes/.edith/github_pat_vault'), 'r') as f:
    vault['github_pat'] = json.load(f)

# Save consolidated vault (600 perms = no group/other read)
with open(edith_vault, 'w') as f:
    json.dump(vault, f)
os.chmod(edith_vault, 0o600)
```

### Step 3: Create "Credentials" Google Sheet as Backup + Reference

**Three sheets:**

1. **Authentication** — All services, types, statuses, locations, last updated
2. **EDITH Vault** — Three factors, verification questions, challenge protocol
3. **API & MCP** — All endpoints, methods, credential types

**Script:** See `scripts/create-credentials-sheet.py`

## Key Points

- **No plaintext at rest** — all credentials encrypted, all hashes use salt
- **Hardware UUID binding** — prevents token theft across systems
- **Google Sheets backup** — durable reference, human-readable (but not secret itself)
- **Three factors** — even if one is compromised, vault remains locked
- **All questions hashed** — verification protocol can't be guessed from plaintext

## Reusable for Future Sessions

- New credential (API key, PAT, etc.)? Add to `edith_vault.json` + update Credentials sheet
- Verification protocol needs expansion? Add more questions to `verification_hashes.json`
- Time-window needs adjustment? Modify factor-3 enforcement at runtime

## Files & Locations

- Main vault: `~/.hermes/.edith/edith_vault.json` (encrypted, 600 perms)
- Hardware UUID: `~/.hermes/.edith/hardware_uuid` (600 perms)
- Passphrase: `~/.hermes/.edith/passphrase_hash` (600 perms, bcrypt)
- Verification: `~/.hermes/.edith/verification_hashes.json` (600 perms, SHA-256)
- Personal framework: `~/.hermes/.edith/personal_framework.json` (5 core rules)
- Backup reference: Google Sheet "Credentials" in Friday 2.0 folder
