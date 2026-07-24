# Credential Access Hierarchy (Tanzim Preference)

**Signal:** Tanzim said "you didn't find the game memory or I'd say" when Friday asked for EDITH vault passphrase instead of checking Credentials Sheet first. This established an explicit access order.

## The Hierarchy

Tanzim stores credentials in THREE places. **Always check in this order:**

### 1. **Credentials Google Sheet (PRIMARY — Check First)**
- **Location:** Google Drive, Sheet ID `1QtHeLtYqd21fGWY0FwRqxGgodYgj-rXnM7mXT9MzzLw`
- **Name:** "Credentials"
- **Tabs:** Authentication, EDITH Vault, API & MCP
- **Why first:** Accessible, no decryption needed, human-readable, always current
- **What's here:** GitHub PAT, OAuth scopes, API keys, session credentials, MCP configs
- **Access:** No auth required — it's a shared Google Sheet (accessible to Friday via OAuth)

### 2. **USER.md Backups (SECONDARY — Check Second)**
- **Location:** `~/.hermes/backups/USER_*.md` (daily timestamped backups)
- **Latest:** `USER_20260609_062501.md` or similar
- **Why second:** Visible locally, no encryption, survives Sheets outages
- **What's here:** Credentials duplicated from Sheet + historical context, team profiles, operational preferences
- **Access:** Local filesystem read, no decryption

### 3. **EDITH Vault (TERTIARY — Check Last)**
- **Location:** `~/.hermes/.edith/edith_vault.json` (AES-256-GCM encrypted)
- **Why last:** Requires three-factor auth (hardware UUID + passphrase + security questions)
- **What's here:** Full OAuth credentials with all scopes, encrypted at rest
- **Access:** Requires decryption passphrase + one security question answer

## Access Pattern (Pseudocode)

```
if credential_needed(github_pat):
    try:
        pat = pull_from_credentials_sheet()  # 1. Try Sheet first
        if pat is valid:
            return pat
    except (timeout, not_found):
        pass
    
    try:
        pat = read_from_user_md_backup()  # 2. Try USER.md backup
        if pat is valid:
            return pat
    except (timeout, not_found):
        pass
    
    try:
        # 3. Only ask for EDITH passphrase if Sheet + USER.md both failed
        pat = unlock_edith_vault()  # Requires passphrase + security question
        return pat
    except (timeout, not_found, decryption_failed):
        ask_user_to_provide_credential_fresh()
```

## Why This Order Matters

**Efficiency:**
- Sheet access is fast and often succeeds (no re-auth needed)
- USER.md is local, always works
- EDITH vault requires three-factor auth and slows down the session

**User Preference:**
- Tanzim prefers Friday to be resourceful — find credentials without asking
- Asking for EDITH passphrase is a last resort, not a first move
- The whole vault system is designed to avoid repeated auth — but only works if you check accessible sources first

**Failure Resilience:**
- If Sheets times out → USER.md has a backup
- If both Sheets and USER.md fail → EDITH is still there as final fallback
- No credential is truly lost

## Real Example (Jun 9, 2026)

**What Happened:**
Friday needed GitHub PAT to create "10zm Osar" Google Sheet.
- Friday asked for EDITH vault passphrase
- Tanzim said "you didn't find the game memory or I'd say"
- Translation: GitHub PAT is in Credentials Sheet; don't ask for vault auth

**What Should Happen:**
1. Check Credentials Sheet for `github_pat` or `friday-edith-token`
2. If not found, check USER.md (latest backup)
3. Only if both fail, ask for EDITH vault passphrase

**Lesson:** Always try accessible sources first. Encrypted vault is the fallback, not the go-to.

## Implementation in Skills

When any skill needs to access credentials (GitHub, Google, iCloud, etc.):

1. Load the skill that governs that credential type
2. Check the skill for an "Access Hierarchy" or "Credential Loading" section
3. Follow the order: Sheet → USER.md → ask user or EDITH vault
4. Never jump straight to asking for passphrases

If a skill doesn't document this order, **patch it** to add it.

## Credentials Currently in Sheet vs. USER.md vs. EDITH

**In Credentials Sheet (most current):**
- Google OAuth (5 services: Gmail, Drive, Docs, Sheets, Chat)
- GitHub PAT (Friday-EDITH, repo/gist/user scopes)
- iCloud credentials (tanzimx@icloud.com)
- Webflow / Wix API tokens
- Instagram session cookies (if fresh)

**In USER.md Backups (reference):**
- EDITH vault structure (encryption factors, security questions)
- Team roles and cap table
- Operational preferences
- TIMBR company info
- Friday persona rules

**In EDITH Vault (encrypted, full-scope):**
- Google OAuth tokens (all 5 services)
- GitHub PAT
- Backup copies of everything else

**Bottom line:** For 95% of cases, Sheet has what you need. USER.md has context. EDITH is backup.
