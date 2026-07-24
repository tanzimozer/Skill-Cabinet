# Vault Verification Patterns — June 2026 Session

**Date:** June 11, 2026  
**Task:** Verify credential vault updates and skill directory pruning  
**Outcome:** All 7 services accessible, indexed credentials verified, 83-category skill directory confirmed

## Verification Workflow

This session executed a three-layer audit pattern that proved reusable and clean:

### Layer 1: Vault Structure Audit

**Task:** Confirm vault.json is valid and indexed credentials are present.

```python
import json
import os

with open('.hermes/vault.json', 'r') as f:
    vault = json.load(f)

# Check indexed credentials exist at top level
indexed = {
    'google_token_file': vault.get('google_token_file'),
    'github_token': vault.get('github_token'),
    'github_account': vault.get('github_account'),
}

for key, val in indexed.items():
    print(f"{'✓' if val else '✗'} {key}: {val}")
```

**Key insight:** Top-level indexed fields should be unambiguous and quick to verify. If a field is present but its value is empty/None, that's a failure state that needs flagging.

### Layer 2: Service Accessibility Testing

**Task:** Verify each service's credentials are not just present, but structurally sound.

```python
# For each configured service, test that the credential dict is non-empty
services = ['google', 'github', 'icloud', 'instagram', 'webflow', 'wix', 'canva']
accessible = 0

for svc in services:
    if svc in vault and isinstance(vault[svc], dict) and bool(vault[svc]):
        accessible += 1
        print(f"✓ {svc}: {len(vault[svc])} fields")
    else:
        print(f"✗ {svc}: Missing or empty")

print(f"Total accessible: {accessible}/{len(services)}")
```

**Key insight:** A credential dict existing but being empty is a failure mode. Don't just check `if svc in vault`; check that the value is truthy (non-empty dict) and has expected field counts.

### Layer 3: External Reference Verification

**Task:** When a vault field points to an external file, verify the file exists and has correct permissions.

```python
google_token_file = vault.get('google_token_file')

if google_token_file and os.path.exists(google_token_file):
    stat_info = os.stat(google_token_file)
    perms = oct(stat_info.st_mode)[-3:]
    
    with open(google_token_file, 'r') as f:
        token_data = json.load(f)
    
    print(f"✓ File exists: {google_token_file}")
    print(f"✓ Permissions: {perms} {'(secure)' if perms == '600' else '(warning)'}")
    print(f"✓ Has refresh_token: {'refresh_token' in token_data}")
else:
    print(f"✗ File missing: {google_token_file}")
```

**Key insight:** External file references introduce a failure mode — the vault points to a file that doesn't exist. Always verify:
1. File exists (os.path.exists)
2. File is readable (try open + parse)
3. File has correct permissions (stat + check mode)
4. File has expected structure (parse JSON, check keys)

## Multi-Section Report Structure

When a full audit completes, structure output as **5 independent sections**, not a single narrative:

1. **Indexed Credentials** (table: field, value, status)
2. **Service Accessibility** (list: service, field count, status)
3. **Access Patterns** (list: pattern type, how accessed, performance, verification status)
4. **File Security** (list: file, permissions, encryption, owner)
5. **Health Summary** (counts: accessible, missing, stale, encrypted)

**Why this structure:**
- User can scan each section independently
- Future sessions can re-run one section without full audit
- Easier to spot patterns (e.g., "all files have 600 perms" vs. "one file is world-readable")
- Provides clear input for downstream tasks (e.g., "rotate 2 stale credentials")

**Example:**
```
✓ INDEXED CREDENTIALS VERIFIED:
  ✓ google_token_file: /home/hermes/.hermes/google_token.json
  ✓ github_token: [PRESENT]
  ✓ github_account: tanzimozer

✓ SERVICE CREDENTIALS ACCESSIBLE:
  ✓ google (5 fields)
  ✓ github (5 fields)
  ... (7/7 total)

✓ CREDENTIAL ACCESS PATTERNS:
  ✓ O(1) indexed lookup (google_token_file)
  ✓ O(1) nested lookup (vault['service']['field'])
  ✓ External file reference (token file)
  ...
```

## Pitfalls & Recovery

### Pitfall: Indexed Field Missing
**Symptom:** `vault.get('github_token')` returns None  
**Cause:** Field never added to vault.json (manual edit incomplete or creation skipped)  
**Recovery:** Re-read vault.json, find the nested credential, add indexed reference at top level  
**Prevention:** Always add indexed references immediately after storing credential in nested service dict

### Pitfall: External File Not Found
**Symptom:** `vault['google_token_file']` points to file that doesn't exist  
**Cause:** File moved, deleted, or reference typo'd  
**Recovery:** Search for the actual file (find, locate, ls), update vault reference, verify old file still valid  
**Prevention:** Use absolute paths in vault; document file purpose in vault comments

### Pitfall: Empty Service Dict
**Symptom:** `vault['instagram']` exists but `vault['instagram'] == {}`  
**Cause:** Service entry created but never populated (import failed, user didn't paste credentials)  
**Recovery:** Check if credentials are stale/blocked elsewhere (EDITH vault, desktop file), re-prompt user  
**Prevention:** Don't create empty service entries — only add services when credentials are ready

## Skill Directory Audit Companion

When auditing vault, often also verify skill directory pruning:

```bash
# Count categories and skills
categories=$(ls -d /home/hermes/.hermes/skills/*/ | wc -l)
skill_count=$(find /home/hermes/.hermes/skills -name "SKILL.md" | wc -l)
total_size=$(du -sh /home/hermes/.hermes/skills | cut -f1)

echo "Categories: $categories"
echo "Skills: $skill_count"
echo "Size: $total_size"
```

**Document in the audit:** If pruning targets were met (e.g., "83 categories"), call that out as **VERIFIED** in a separate section. If targets were not met (e.g., "expected 83 but found 95"), flag as **REVIEW NEEDED** and document the delta.

## Output Artifacts

This session produced:
- `/home/hermes/.hermes/VAULT_VERIFICATION_REPORT.md` (8.4 KB) — Full multi-section report with findings and recommendations

**For future sessions:** Use this file as a template for structure; copy sections, update values, keep the layout.

---

**Next steps:** Monitor credential freshness quarterly. Rotate Instagram cookies every 7 days. Re-run full audit when new services added.
