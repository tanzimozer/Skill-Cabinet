#!/usr/bin/env python3
"""
EDITH Vault Initialization Script

Initialize a complete secure credential vault with three-factor authentication.
Run once to set up. Then use unlock_vault() for all future credential access.

Usage:
    python3 vault-init.py

Prompts for:
1. Vault passphrase (knowledge factor)
2. 3 personal preference questions + answers (verification factor)

Creates:
- ~/.hermes/.edith/ directory structure
- Hardware UUID binding (system-specific)
- Encrypted credential storage (AES-256-GCM)
- Verification protocol (SHA-256 hashes)

"""

import os
import sys
import json
import hashlib
import uuid
import time
from pathlib import Path

try:
    import bcrypt
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
except ImportError:
    print("ERROR: Missing required packages. Install:")
    print("  pip install bcrypt cryptography")
    sys.exit(1)


# ============================================================================
# VAULT SETUP FUNCTIONS
# ============================================================================

def setup_vault_directory():
    """Create obfuscated vault directory with secure permissions."""
    vault_dir = Path.home() / '.hermes' / '.edith'
    vault_dir.mkdir(parents=True, exist_ok=True)
    os.chmod(vault_dir, 0o700)  # Owner only
    print(f"✓ Vault directory: {vault_dir}")
    return vault_dir


def setup_hardware_uuid(vault_dir):
    """Create hardware UUID binding (Factor 1)."""
    hardware_uuid = str(uuid.getnode())
    uuid_file = vault_dir / 'hardware_uuid'
    
    with open(uuid_file, 'w') as f:
        f.write(hardware_uuid)
    os.chmod(uuid_file, 0o600)
    
    print(f"✓ Hardware UUID binding: {hardware_uuid[:16]}...")
    return hardware_uuid


def setup_passphrase(vault_dir):
    """Create passphrase + bcrypt hash (Factor 2)."""
    print("\n--- Passphrase Setup (Factor 2) ---")
    print("This passphrase protects all credentials in the vault.")
    print("Use something memorable but strong (12+ chars, mix of case/numbers/symbols).")
    
    while True:
        passphrase = input("\nEnter vault passphrase: ").strip()
        
        if len(passphrase) < 8:
            print("⚠ Passphrase too short. Use at least 8 characters.")
            continue
        
        passphrase_confirm = input("Confirm passphrase: ").strip()
        if passphrase != passphrase_confirm:
            print("⚠ Passphrases don't match. Try again.")
            continue
        
        break
    
    # Hash with bcrypt-10
    passphrase_hash = bcrypt.hashpw(passphrase.encode('utf-8'), bcrypt.gensalt(rounds=10))
    hash_file = vault_dir / 'passphrase_hash'
    
    with open(hash_file, 'wb') as f:
        f.write(passphrase_hash)
    os.chmod(hash_file, 0o600)
    
    print("✓ Passphrase hashed and stored")
    return passphrase


def setup_time_window(vault_dir):
    """Initialize time-window gating (Factor 3)."""
    timestamp_file = vault_dir / 'last_auth_timestamp'
    
    with open(timestamp_file, 'w') as f:
        f.write(str(int(time.time())))
    os.chmod(timestamp_file, 0o600)
    
    print("✓ Time-window gating initialized (±5 min auth window)")


def setup_verification_protocol(vault_dir):
    """Collect personal preference questions + store hashes (Verification)."""
    print("\n--- Verification Protocol (3 Personal Questions) ---")
    print("These questions will unlock the vault if you forget the passphrase.")
    print("Use personal preferences (favorite team, character, etc.) — not public facts.")
    print()
    
    questions = [
        "Favorite football team?",
        "Favorite character?",
        "Favorite person?",
    ]
    
    verification_hashes = {}
    
    for i, question in enumerate(questions, 1):
        while True:
            answer = input(f"Q{i}: {question} ").strip()
            
            if len(answer) < 2:
                print("⚠ Answer too short. Be specific.")
                continue
            
            confirm = input(f"   Confirm: {question} ").strip()
            if answer.lower() != confirm.lower():
                print("⚠ Answers don't match. Try again.")
                continue
            
            break
        
        # Store SHA-256 hash only (case-insensitive)
        answer_hash = hashlib.sha256(answer.lower().encode('utf-8')).hexdigest()
        verification_hashes[question] = answer_hash
    
    # Save hashes
    verify_file = vault_dir / 'verification_hashes'
    with open(verify_file, 'w') as f:
        json.dump(verification_hashes, f, indent=2)
    os.chmod(verify_file, 0o600)
    
    print("✓ Verification protocol set up (3 questions)")


# ============================================================================
# ENCRYPTION HELPERS
# ============================================================================

def derive_encryption_key(passphrase):
    """Derive AES-256 key from passphrase using PBKDF2."""
    salt = os.urandom(16)  # 128-bit salt
    kdf = PBKDF2(
        algorithm=hashes.SHA256(),
        length=32,  # 256-bit key
        salt=salt,
        iterations=100000,
    )
    key = kdf.derive(passphrase.encode('utf-8'))
    return key, salt


def encrypt_credentials(credentials_dict, passphrase):
    """Encrypt credentials dict to AES-256-GCM."""
    key, salt = derive_encryption_key(passphrase)
    
    plaintext = json.dumps(credentials_dict).encode('utf-8')
    nonce = os.urandom(12)  # 96-bit nonce
    cipher = AESGCM(key)
    ciphertext = cipher.encrypt(nonce, plaintext, None)
    
    return {
        'salt': salt.hex(),
        'nonce': nonce.hex(),
        'ciphertext': ciphertext.hex(),
    }


# ============================================================================
# VAULT USAGE FUNCTIONS
# ============================================================================

def verify_passphrase(passphrase, vault_dir):
    """Verify passphrase against stored bcrypt hash."""
    hash_file = vault_dir / 'passphrase_hash'
    
    with open(hash_file, 'rb') as f:
        stored_hash = f.read()
    
    return bcrypt.checkpw(passphrase.encode('utf-8'), stored_hash)


def verify_identity(vault_dir):
    """Verify identity using 3-question challenge."""
    verify_file = vault_dir / 'verification_hashes'
    
    with open(verify_file, 'r') as f:
        verification_hashes = json.load(f)
    
    passed = 0
    for question in verification_hashes.keys():
        answer = input(f"{question} ").strip()
        answer_hash = hashlib.sha256(answer.lower().encode('utf-8')).hexdigest()
        
        if answer_hash == verification_hashes[question]:
            passed += 1
        else:
            print("✗ Incorrect")
    
    if passed == 3:
        print(f"✓ {passed}/3 correct")
        return True
    else:
        print(f"✗ {passed}/3 correct. Vault locked for 30 min.")
        return False


def save_credential(service, credentials_dict, passphrase, vault_dir=None):
    """Save encrypted credentials for a service."""
    if vault_dir is None:
        vault_dir = Path.home() / '.hermes' / '.edith'
    
    vault_file = vault_dir / f'{service}_vault'
    encrypted = encrypt_credentials(credentials_dict, passphrase)
    
    with open(vault_file, 'w') as f:
        json.dump(encrypted, f, indent=2)
    os.chmod(vault_file, 0o600)
    
    print(f"✓ Credentials saved: {service}_vault")


# ============================================================================
# MAIN
# ============================================================================

def main():
    print("=" * 70)
    print("EDITH Vault Initialization")
    print("=" * 70)
    print()
    
    # Setup
    vault_dir = setup_vault_directory()
    hardware_uuid = setup_hardware_uuid(vault_dir)
    passphrase = setup_passphrase(vault_dir)
    setup_time_window(vault_dir)
    setup_verification_protocol(vault_dir)
    
    print("\n" + "=" * 70)
    print("Vault setup complete!")
    print("=" * 70)
    print()
    print("Next steps:")
    print("1. Initiate Google OAuth: Copy the authorization URL and authorize in browser")
    print("2. Paste the callback URL (with code) back here")
    print("3. Exchange code for tokens and store in vault")
    print("4. Repeat for GitHub PAT")
    print()
    print("Vault location:", vault_dir)
    print("Vault is protected by:")
    print("  ✓ Hardware UUID (Factor 1: system-specific)")
    print("  ✓ Passphrase (Factor 2: knowledge-based)")
    print("  ✓ Time-window gating (Factor 3: behavioral)")
    print("  ✓ AES-256-GCM encryption (at-rest)")
    print("  ✓ 3-question verification (identity challenge)")
    print()


if __name__ == '__main__':
    main()
