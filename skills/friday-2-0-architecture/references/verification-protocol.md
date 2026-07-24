# Friday 2.0 Verification Protocol

**Established:** Jun 10, 2026  
**Purpose:** Multi-factor authentication for EDITH 2.0 vault access, especially sensitive operations

---

## Overview

The verification protocol is a **2-of-3 Q&A challenge** that gates access to sensitive credentials and operations. Not every vault access requires verification — only:

- Admin credentials (Canva admin token, GitHub admin PAT, database root access)
- Sensitive API keys (Anthropic, Hindsight, financial APIs)
- Authorization flows (new OAuth, secret rotation)

Low-sensitivity credentials (public API keys, public GitHub PATs) do not trigger verification.

---

## Questions & Answers

Three questions, chosen randomly; 2 out of 3 correct required.

### Q1: Real Madrid
**Question:** "Which football club did Tanzim reference in the vault security design?"  
**Answer:** Real Madrid (exact, case-insensitive, no accents)  
**Why:** Memorable, specific, unambiguous. Not easily guessable from Tanzim's public profile.

### Q2: Pepper Potts
**Question:** "What is the primary persona reference for Friday's tone and behavior?"  
**Answer:** Pepper Potts (or variations: "Pepper", "Pepper Potts Tony Stark", "75% Pepper Potts")  
**Why:** Defined in Friday's system prompt. Reflects Tanzim's explicit design brief.

### Q3: Myself
**Question:** "According to the Friday persona, who is 'Myself'?"  
**Answer:** Myself (reflexive) or "Tanzim" (acceptable answer to the question "who is myself in this context?")  
**Why:** Self-referential; answers the identity question embedded in the question itself.

---

## Verification Flow

### Trigger Conditions
Vault access attempts are classified:

**✅ No verification needed (low-risk):**
- Reading public API keys (Webflow, Wix)
- Accessing iCloud app password (personal, not admin)
- Instagram credentials (consumer token, not admin)
- Any public GitHub PAT (scopes: public-read)

**⚠️ Verification required (sensitive):**
- GitHub admin token (repo delete scope)
- Canva Client Secret (full design permissions)
- Anthropic API key (billing, model limits)
- Any OAuth refresh token (can generate new access tokens)
- EDITH metadata (hardware UUID, setup history)
- Access log reads

### Challenge Process

```
1. Trigger sensitive credential access
2. System selects 2 random questions from [Q1, Q2, Q3]
3. Display questions and prompt for answers
4. User provides 2 answers
5. If ≥2 correct: Decrypt and return credential
6. If <2 correct: Deny access, log attempt (with answers redacted)
7. Record success/failure in access.log
```

### Implementation (Pseudocode)

```python
import hashlib, json, secrets

# Load verification.enc (encrypted Q&A answers)
vault_metadata = json.load(open('~/.hermes/.edith/metadata.json'))
verification_encrypted = open('~/.hermes/.edith/verification.enc', 'rb').read()

# Decrypt answers using hardware UUID key
answers_plaintext = decrypt_with_key(verification_encrypted, hardware_uuid_key)
answers = json.loads(answers_plaintext)  # { "Q1": "Real Madrid", "Q2": "Pepper Potts", "Q3": "Myself" }

# Select 2 random questions
import random
selected_qs = random.sample(['Q1', 'Q2', 'Q3'], k=2)

# Prompt user
for q_label in selected_qs:
    user_answer = input(f"{questions[q_label]}: ").strip().lower()
    # Normalize: strip accents, remove extra spaces, lowercase
    user_answer_normalized = normalize_answer(user_answer)
    expected_answer_normalized = normalize_answer(answers[q_label])
    
    if user_answer_normalized == expected_answer_normalized:
        print(f"✓ {q_label} correct")
        score += 1
    else:
        print(f"✗ {q_label} incorrect")
        # Do NOT echo correct answer

# Log attempt
log_entry = {
    'timestamp': datetime.now().isoformat(),
    'operation': 'vault_access_sensitive',
    'credential': '[REDACTED]',
    'questions_asked': selected_qs,
    'answers_provided': '[REDACTED]',
    'score': score,
    'result': 'granted' if score >= 2 else 'denied'
}
append_to_access_log(log_entry)

# Return credential or deny
if score >= 2:
    return decrypt_credential(vault, credential_key, hardware_uuid_key)
else:
    raise PermissionError("Verification failed (2/3 required)")
```

---

## Answer Normalization

Answers are normalized before comparison to handle variations:

```python
def normalize_answer(s):
    # Remove accents (é → e, ñ → n)
    s = unidecode(s)
    # Lowercase
    s = s.lower()
    # Remove extra whitespace
    s = ' '.join(s.split())
    # Remove punctuation (optional based on answer)
    return s
```

**Examples:**
- "Real madrid" → "real madrid" ✓
- "PEPPER POTTS" → "pepper potts" ✓
- "Pepper  Potts" → "pepper potts" ✓
- "Pépér Pötts" → "peper potts" ✗ (typo in core word)

---

## Security Properties

| Property | Details |
|----------|---------|
| **Entropy** | 3 questions × 2 selected = C(3,2) = 3 possible pairs; 3^2 = 9 possible answer combinations per pair; 9 × 3 = 27 total attempts needed for brute force with 2/3 scoring |
| **Answer storage** | Encrypted in verification.enc with hardware UUID key (same as vault credentials) |
| **Attempt logging** | All attempts logged (success/failure); answers are redacted; no plaintext logged |
| **Rate limiting** | (Future) After 3 failed attempts in 60 seconds, lock vault for 5 minutes |
| **Recovery** | If Tanzim forgets an answer: only recovery is full vault re-init with new questions (rare) |

---

## Testing Verification (Jun 10 — Jun 16)

- [ ] Trigger sensitive credential access (e.g., GitHub admin PAT read)
- [ ] Verify 2 questions are asked randomly
- [ ] Provide correct answers; confirm credential returned
- [ ] Provide 1 correct + 1 incorrect; confirm access denied
- [ ] Provide 2 incorrect answers; confirm access denied
- [ ] Check access.log entries are created (answers redacted)
- [ ] Verify non-sensitive credentials do NOT trigger Q&A

---

## Edge Cases & Decisions

**What if Tanzim gets an answer wrong?**
- Deny access immediately
- Log attempt with redacted answer
- Do NOT reveal correct answer
- Tanzim can retry once more; if both attempts fail, escalate to manual unlock

**What if verification.enc is corrupted?**
- Fall back to plaintext emergency unlock (stored in .recovery file)
- Log critical event
- Rebuild verification.enc after system is restored

**What if new questions are added?**
- Existing verification.enc can only be read with current questions
- Adding new questions requires re-encrypting all Q&A answers
- Notify Tanzim before making changes

**Can answers be changed without full re-init?**
- Yes — decrypt verification.enc, update answer, re-encrypt with same key
- Still requires manual action (edit, save, encrypt)
- Log change in access.log

---

## Related Docs

- **EDITH 2.0 Vault:** See credential-management-tanzim / references/edith-2.0-vault.md for encryption details
- **Friday 2.0 Architecture:** See friday-2-0-architecture / SKILL.md for full system design
- **Access Logging:** See .hermes/.edith/access.log for all vault operations
