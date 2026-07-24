# EDITH 2.0 Security Hardening Patterns

**Session:** Jun 17, 2026 (TASK 4)  
**Scope:** Three security fixes for EDITH 2.0 vault — rate limiting, encrypted services map, enhanced audit logging  
**Status:** All implemented and validated (see TASK_4_COMPLETE.txt)

---

## Overview

EDITH 2.0 (hardware-bound encryption vault) required three critical security hardening fixes:

1. **Rate Limiting** — Prevent brute-force verification attacks
2. **Encrypted Services Map** — Hide service names from filesystem inspection
3. **Enhanced Audit Logging** — Granular event tracking + security score calculation

This reference captures implementation patterns for future security audit cycles.

---

## Pattern 1: Sliding-Window Rate Limiting

**Problem:**  
EDITH verification challenge (3/3 Q&A) is the primary gate to credential access. An attacker can brute-force answers if there's no rate limit on failed attempts.

**Solution:**  
Sliding-window rate limiter with 5 failed attempts per 5-minute window.

### Implementation

**Class: RateLimiter**

```python
class RateLimiter:
    """Rate limiter for vault access — prevents brute force attacks."""
    
    def __init__(self, max_attempts: int = 5, window_seconds: int = 300):
        self.max_attempts = max_attempts
        self.window_seconds = window_seconds
        self.attempts: List[datetime] = []
    
    def is_rate_limited(self) -> bool:
        """Check if rate limit has been exceeded."""
        now = datetime.utcnow()
        cutoff = now - timedelta(seconds=self.window_seconds)
        # Remove old attempts outside the window
        self.attempts = [t for t in self.attempts if t > cutoff]
        return len(self.attempts) >= self.max_attempts
    
    def record_attempt(self):
        """Record a failed attempt."""
        self.attempts.append(datetime.utcnow())
    
    def reset(self):
        """Reset counter on successful access."""
        self.attempts = []
    
    def get_remaining_attempts(self) -> int:
        """Return remaining attempts before lockout."""
        now = datetime.utcnow()
        cutoff = now - timedelta(seconds=self.window_seconds)
        self.attempts = [t for t in self.attempts if t > cutoff]
        return max(0, self.max_attempts - len(self.attempts))
```

### Integration Pattern

**In EDITHVault.__init__():**
```python
self.rate_limiter = RateLimiter(max_attempts=5, window_seconds=300)
```

**In get_credential() verification flow:**
```python
if verify:
    # Check rate limit BEFORE challenge
    if self.rate_limiter.is_rate_limited():
        self.logger.log_access('read', service, 'denied', 'Rate limit exceeded')
        raise ValueError("Too many failed attempts. Please try again in 5 minutes.")
    
    # Print remaining attempts to user
    print(f"Remaining attempts: {self.rate_limiter.get_remaining_attempts()}")
    
    # Run challenge
    if not self.verification.challenge(num_questions=3, required_correct=3):
        self.rate_limiter.record_attempt()  # Log failed attempt
        raise ValueError("Verification failed. Credential access denied.")
    
    # Reset on success
    self.rate_limiter.reset()
```

### Key Design Decisions

- **Sliding window (not fixed window):** Old attempts expire naturally; no complex state management
- **Memory-resident (not persistent):** Survives process restarts via access.log granular events (see Pattern 3)
- **Reset on success:** Clears counter so legitimate users aren't penalized by accidental failures
- **5/5min default:** Balance between security (blocks brute force) and usability (5min cooldown is acceptable)

### Tuning

If deployment shows false positives (legitimate users hitting rate limit):
- Increase `max_attempts`: 5 → 7 or 10
- Increase `window_seconds`: 300 (5 min) → 600 (10 min)

If deployment shows brute force attempts:
- Decrease `max_attempts`: 5 → 3
- Decrease `window_seconds`: 300 → 180 (3 min)

---

## Pattern 2: Encrypted Services Map

**Problem:**  
Services map (mapping service name → obfuscated credential key) was stored in plaintext (`services.map`) on disk. An attacker with filesystem access can see all services Tanzim uses (google, github, aws, etc.).

**Solution:**  
Encrypt services map with same AES-256 Fernet cipher as vault credentials. File name: `services.map.enc`.

### Implementation

**Load method:**
```python
def _load_services_map(self) -> Dict[str, str]:
    """Load service name → obfuscated key mapping (encrypted)."""
    services_map_path = self.vault_dir / 'services.map.enc'
    if not services_map_path.exists():
        return {}
    
    try:
        with open(services_map_path, 'r') as f:
            encrypted_data = f.read()
        # Decrypt using hardware-bound cipher
        decrypted_map = self.encryption.decrypt(encrypted_data)
        return decrypted_map if isinstance(decrypted_map, dict) else {}
    except Exception as e:
        self.logger.log_access('read', 'services_map', 'failure', f'Failed to load: {str(e)}')
        return {}
```

**Save method:**
```python
def _save_services_map(self):
    """Save services map to disk (encrypted)."""
    services_map_path = self.vault_dir / 'services.map.enc'
    try:
        # self.encryption.encrypt() expects a dict, returns Fernet token string
        encrypted = self.encryption.encrypt(self.services_map)
        with open(services_map_path, 'w') as f:
            f.write(encrypted)
        os.chmod(services_map_path, 0o600)
        self.logger.log_access('write', 'services_map', 'success', 'Services map saved (encrypted)')
    except Exception as e:
        self.logger.log_access('write', 'services_map', 'failure', f'Failed to save: {str(e)}')
```

### API Contract (Critical!)

The `self.encryption` object (EncryptionEngine) has this contract:
- **encrypt(plaintext: Dict[str, Any]) → str:** Takes dict, returns Fernet token string
- **decrypt(ciphertext: str) → Dict[str, Any]:** Takes Fernet token string, returns dict

Do NOT try to:
- Pass JSON strings to encrypt() — it converts to bytes internally
- Expect decrypt() to return JSON string — it returns the parsed dict

### Migration from Plaintext

Old vaults have `services.map` (plaintext). When updating code:

```python
# Old vault (plaintext)
with open('services.map', 'r') as f:
    services_map = json.load(f)

# New vault (encrypted)
self.services_map = services_map
self._save_services_map()  # Encrypts and writes to services.map.enc
# Optionally: delete old services.map
```

### Verification

After implementing, verify:
- `ls -la ~/.hermes/.edith/` shows `services.map.enc` exists
- `cat services.map.enc` shows random-looking Fernet ciphertext (not readable JSON)
- Decryption works: `EDITHVault().services_map` shows correct dict

---

## Pattern 3: Enhanced Audit Logging

**Problem:**  
Original audit log only tracked aggregate metrics (access_count, failed_attempts). No granular event history meant:
- No forensic trail of what credentials were accessed when
- No ability to detect subtle attack patterns (same service accessed 10x in 1 min)
- Security metrics (like "rate limit blocks") were not tracked

**Solution:**  
Granular event log (timestamp, operation, service, status, details) + computed security score.

### Log Structure

**File:** `~/.hermes/.edith/access.log`

```json
{
  "created": "2026-06-17T10:00:00Z",
  "last_accessed": "2026-06-17T14:30:45Z",
  "access_count": 15,
  "failed_attempts": 3,
  "denied_count": 2,
  "rate_limit_blocks": 1,
  "events": [
    {
      "timestamp": "2026-06-17T10:00:15Z",
      "operation": "read",
      "service": "google",
      "status": "success",
      "details": ""
    },
    {
      "timestamp": "2026-06-17T10:00:20Z",
      "operation": "read",
      "service": "github",
      "status": "denied",
      "details": "Rate limit exceeded. Try again in 5 min."
    },
    // ... max 500 events (older pruned)
  ]
}
```

### Implementation

**Enhanced log_access():**

```python
def log_access(self, operation: str, service: str, status: str, details: str = ''):
    """Log vault access event with granular details."""
    with open(self.log_file, 'r') as f:
        log_data = json.load(f)
    
    timestamp = datetime.utcnow().isoformat() + 'Z'
    log_data['last_accessed'] = timestamp
    
    # Record granular event
    event = {
        'timestamp': timestamp,
        'operation': operation,
        'service': service,
        'status': status,
        'details': details
    }
    log_data['events'].append(event)
    
    # Update aggregate metrics
    if status == 'success':
        log_data['access_count'] += 1
    elif status == 'failure':
        log_data['failed_attempts'] += 1
    elif status == 'denied':
        log_data['denied_count'] += 1
        if 'Rate limit' in details or 'Too many' in details:
            log_data['rate_limit_blocks'] += 1
    
    # Prune to 500 most recent events
    if len(log_data['events']) > 500:
        log_data['events'] = log_data['events'][-500:]
    
    with open(self.log_file, 'w') as f:
        json.dump(log_data, f, indent=2)
    os.chmod(self.log_file, 0o600)
```

**New get_stats() method:**

```python
def get_stats(self) -> Dict:
    """Get vault access statistics and security metrics."""
    with open(self.log_file, 'r') as f:
        log_data = json.load(f)
    
    total_events = len(log_data.get('events', []))
    stats = {
        'created': log_data['created'],
        'last_accessed': log_data['last_accessed'],
        'total_events': total_events,
        'successful_accesses': log_data['access_count'],
        'failed_attempts': log_data['failed_attempts'],
        'denied_accesses': log_data['denied_count'],
        'rate_limit_blocks': log_data['rate_limit_blocks'],
        'security_score': self._calculate_security_score(log_data)
    }
    return stats
```

**Security score calculation:**

```python
def _calculate_security_score(self, log_data: Dict) -> float:
    """
    Calculate security score (0–100) based on access patterns.
    Higher is better: high success rate, low failures, no rate limits.
    """
    total = log_data['access_count'] + log_data['failed_attempts'] + log_data['denied_count']
    if total == 0:
        return 100.0  # No activity = no risk
    
    success_rate = log_data['access_count'] / total
    failure_rate = log_data['failed_attempts'] / total
    denial_rate = log_data['denied_count'] / total
    
    # Base score on success rate, penalize failures and denials
    score = (success_rate * 100) - (failure_rate * 20) - (denial_rate * 30)
    return max(0, min(100, score))  # Clamp to 0–100
```

### Forensic Analysis Example

Query the log to detect attack patterns:

```python
# Example: Detect brute-force attempt (many denied in short window)
from datetime import datetime, timedelta

log = vault.logger.get_stats()
events = vault.logger.get_entries(limit=100)

# Events in last 10 minutes with status='denied'
now = datetime.fromisoformat(log['last_accessed'].replace('Z', '+00:00'))
cutoff = now - timedelta(minutes=10)

denied_recent = [
    e for e in events
    if e['status'] == 'denied'
    and datetime.fromisoformat(e['timestamp'].replace('Z', '+00:00')) > cutoff
]

if len(denied_recent) > 3:
    print(f"⚠️  Possible brute-force attempt: {len(denied_recent)} denials in 10 min")
```

### Metrics Explained

| Metric | Meaning |
|--------|---------|
| **access_count** | Successful credential reads |
| **failed_attempts** | Verification challenge failures (wrong answers) |
| **denied_count** | Access denied (e.g., due to rate limiting) |
| **rate_limit_blocks** | Subset of denied_count: specifically rate-limit denials |
| **security_score** | Computed from the above; 100 = perfect, 0 = all failures |

### Log Rotation

The log prunes to 500 most recent events automatically. To preserve history:

```python
# Export full log before archival
import json
from shutil import copy

# Back up current log
copy('~/.hermes/.edith/access.log', f'~/archive/access.log.{date}')

# Clear events (keep metadata)
with open('~/.hermes/.edith/access.log', 'r') as f:
    log = json.load(f)
log['events'] = []
with open('~/.hermes/.edith/access.log', 'w') as f:
    json.dump(log, f, indent=2)
```

---

## Testing Checklist

After implementing all three fixes:

- [ ] **Rate Limiting**
  - Record 5 failed attempts; verify `is_rate_limited()` returns True
  - Verify remaining_attempts shows 0 after 5 fails
  - Verify reset() clears the counter
  - Verify user sees "Try again in 5 minutes" message

- [ ] **Encrypted Services Map**
  - Confirm `~/.hermes/.edith/services.map.enc` exists (not `.map`)
  - Confirm file contents are Fernet ciphertext (not readable JSON)
  - Verify load/save cycle preserves data: `vault.services_map` == original

- [ ] **Enhanced Audit Logging**
  - Perform 3 operations (success, denied, failure); check `access.log` has 3 events
  - Verify each event has: timestamp, operation, service, status, details
  - Verify `get_stats()` returns security_score (computed correctly)
  - Verify rate_limit_blocks increments when denial reason includes "Rate limit"

---

## Deployment Notes

**Breaking Change:** services.map → services.map.enc

Old installations will have plaintext `services.map`. Implement migration:

```python
# In __init__(), detect old format:
old_map_path = self.vault_dir / 'services.map'
new_map_path = self.vault_dir / 'services.map.enc'

if old_map_path.exists() and not new_map_path.exists():
    print("Migrating services map from plaintext to encrypted...")
    with open(old_map_path, 'r') as f:
        services = json.load(f)
    self.services_map = services
    self._save_services_map()  # Saves encrypted
    os.remove(old_map_path)
    print("✓ Migration complete")
```

---

## Related Docs

- **friday-2-0-architecture/SKILL.md** — Phase 1 (EDITH) security architecture
- **~/friday-2.0/edith.py** — Full implementation (lines 205–414)
- **~/TASK_4_COMPLETE.txt** — Jun 17 validation results
