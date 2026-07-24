# GitHub Admin PAT Workflow — Temporary Elevated Permissions

**Date Created:** June 9, 2026  
**Pattern:** When destructive operations require elevated scopes, use temporary admin PAT for those ops only, then revert to standard PAT immediately.

## Pattern: Bulk Repository Deletion

**Scenario:** User wants to delete 17 repos from account. Standard PAT has scopes but shouldn't normally carry admin/delete rights. Use temporary admin PAT for the delete operation only.

**Steps:**

1. **Create temporary admin PAT** (GitHub.com Settings → Developer settings → Personal access tokens)
   - Scopes: `repo` (full control), `delete_repo` (if available)
   - Expiry: Same day (e.g., 8 hours from creation)
   - Name: `temp-delete-ops-20260609`
   - Document in `~/Desktop/CREDENTIALS_MASTER.md` with "TEMPORARY" flag

2. **Store in vault temporarily**
   ```python
   import json
   vault_path = os.path.expanduser('~/.hermes/vault.json')
   with open(vault_path, 'r') as f:
       vault = json.load(f)
   
   # Temporarily override with admin token
   vault['github']['temp_admin_pat'] = 'ghp_...'
   with open(vault_path, 'w') as f:
       json.dump(vault, f)
   ```

3. **Run destructive operation** using temp PAT
   ```python
   import requests
   
   temp_pat = vault['github']['temp_admin_pat']
   headers = {
       'Authorization': f'token {temp_pat}',
       'Accept': 'application/vnd.github.v3+json'
   }
   
   # Delete repos
   for repo_name in repos_to_delete:
       url = f'https://api.github.com/repos/tanzimozer/{repo_name}'
       requests.delete(url, headers=headers).raise_for_status()
       print(f"✓ Deleted {repo_name}")
   ```

4. **Immediately revoke temp PAT on GitHub.com**
   - Settings → Developer settings → Personal access tokens → Delete the temp token
   - Confirm deletion

5. **Remove from vault**
   ```python
   vault.pop('github', {}).pop('temp_admin_pat', None)
   with open(vault_path, 'w') as f:
       json.dump(vault, f)
   ```

6. **Update credentials master file**
   - Remove `temp-delete-ops-20260609` entry
   - Log completion with timestamp

## Key Points

- **Never leave admin PAT in vault overnight** — revoke immediately after use
- **Document in CREDENTIALS_MASTER.md with TEMPORARY flag** so it's tracked and visibility is high
- **Standard PAT remains unchanged** — only temp token is rotated
- **Minimum duration** — create immediately before use, revoke immediately after
- **Scopes matter** — temp PAT should have exactly the permissions needed for the operation, no more

## Session Log (June 9, 2026)

**Temp Admin PAT created:** 2026-06-09 22:45 UTC  
**Purpose:** Bulk delete 17 repos (cleanup pass)  
**Repos deleted:** 17  
**Temp PAT revoked:** 2026-06-09 23:02 UTC  
**Duration:** 17 minutes  
**Status:** Complete

Repos kept (9):
- Job_Hammer, Job_Hammer-Personal
- Mag-Seattle
- ig-1-protocol
- friday-master, friday-infra
- Tanzim_Frameworks
- Linked_Engine
- Hermes-agent-bootstrap

Standard PAT (ghp_0E...2ugY) unchanged. No exposure window beyond the 17-minute operation window.
