---
name: github-repository-management
description: Diagnostics, structure setup, and API operations for GitHub repositories
category: automation
tags: [github, api, repository, automation, diagnostics]
---

# GitHub Repository Management

Comprehensive workflow for diagnosing GitHub repositories, setting up structure, managing files, and working around API limitations.

---

## Core Workflow: Repository Diagnostics

**When:** Setting up a new repo, auditing an existing one, or troubleshooting structure issues  
**Owner:** Friday (automated)  
**Output:** Summary report with actionable findings

**Steps:**

1. **Check repo accessibility**
   - Does the repo exist?
   - Is the token authorized to access it?
   - What's the current status (stars, forks, open issues)?

2. **Branch status**
   - How many branches exist?
   - What's the latest commit on each?
   - Is the default branch correct?

3. **Repository structure**
   - How many directories and files at root?
   - Are key directories present (docs/, skills/, references/, etc.)?
   - What critical files exist (README, .gitignore, LICENSE)?

4. **Recent activity**
   - Last 5 commits (sha, date, author, message)
   - Commit frequency (active, stale, dormant?)

5. **Critical files check**
   - README.md exists? Size?
   - .gitignore present?
   - Workflows configured?
   - Key skill files present?

---

## Implementation: Diagnostics Script

```python
import requests
import json
from pathlib import Path

def github_diagnostics(owner, repo_name, token):
    """
    Run full diagnostics on a GitHub repository.
    
    Args:
        owner: GitHub username (e.g., 'tanzimozer')
        repo_name: Repository name (e.g., 'friday-master')
        token: GitHub PAT
    
    Returns:
        Dictionary with diagnostics results
    """
    repo = f"{owner}/{repo_name}"
    headers = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.v3+json'
    }
    
    results = {
        'repo': repo,
        'accessible': False,
        'repo_data': {},
        'branches': [],
        'structure': {},
        'commits': [],
        'critical_files': {}
    }
    
    # 1. Check repo
    try:
        repo_response = requests.get(f'https://api.github.com/repos/{repo}', headers=headers)
        if repo_response.status_code == 200:
            results['accessible'] = True
            results['repo_data'] = repo_response.json()
        else:
            return results  # Stop here if not accessible
    except Exception as e:
        results['error'] = str(e)
        return results
    
    # 2. Branches
    try:
        branches_response = requests.get(f'https://api.github.com/repos/{repo}/branches', headers=headers)
        if branches_response.status_code == 200:
            results['branches'] = branches_response.json()
    except: pass
    
    # 3. Root directory structure
    try:
        contents_response = requests.get(f'https://api.github.com/repos/{repo}/contents', headers=headers)
        if contents_response.status_code == 200:
            contents = contents_response.json()
            results['structure'] = {
                'dirs': [c['name'] for c in contents if c['type'] == 'dir'],
                'files': [c['name'] for c in contents if c['type'] == 'file'],
                'total_items': len(contents)
            }
    except: pass
    
    # 4. Recent commits
    try:
        commits_response = requests.get(
            f'https://api.github.com/repos/{repo}/commits',
            headers=headers,
            params={'per_page': 5}
        )
        if commits_response.status_code == 200:
            results['commits'] = commits_response.json()
    except: pass
    
    # 5. Critical files
    critical_files = ['README.md', '.gitignore', 'LICENSE', '.github/workflows/credential-check.yml']
    for file_path in critical_files:
        try:
            file_response = requests.get(
                f'https://api.github.com/repos/{repo}/contents/{file_path}',
                headers=headers
            )
            if file_response.status_code == 200:
                results['critical_files'][file_path] = 'present'
            elif file_response.status_code == 404:
                results['critical_files'][file_path] = 'missing'
            else:
                results['critical_files'][file_path] = f'error_{file_response.status_code}'
        except:
            results['critical_files'][file_path] = 'error'
    
    return results
```

---

## Repository Structure: Standard Setup

**Recommended directory layout for Friday-style projects:**

```
repo-root/
├── README.md                          # Project overview, setup, architecture
├── .gitignore                         # Security: exclude vault.json, .env, credentials
├── .github/
│   ├── README.md                      # GitHub config documentation
│   └── workflows/
│       ├── credential-check.yml       # Daily credential refresh & test
│       └── skill-sync.yml             # Sync skill library to upstream
├── docs/
│   ├── CREDENTIAL_MANAGEMENT_LOGIC.md # Architecture decisions
│   ├── BUILD_PLAN.md                  # Overall roadmap
│   └── [other architecture docs]
├── persona/
│   ├── communication-style.md         # Chat register, defaults
│   ├── memory-architecture.md         # Hindsight/Memory/Vault split
│   └── [other persona docs]
├── skills/
│   ├── [category]/
│   │   ├── SKILL.md
│   │   ├── references/
│   │   └── scripts/
│   └── [more categories]
├── operations/
│   ├── cron-jobs/
│   ├── scripts/
│   └── configs/
└── references/
    └── [shared reference materials]
```

---

## File Creation via GitHub API

**Pattern:** Create or update files programmatically

```python
import base64
import requests

def create_or_update_file(owner, repo, file_path, content, message, token):
    """
    Create or update a file in a GitHub repo via API.
    """
    headers = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.v3+json'
    }
    
    url = f'https://api.github.com/repos/{owner}/{repo}/contents/{file_path}'
    encoded_content = base64.b64encode(content.encode()).decode()
    
    # Check if file exists (get its SHA)
    get_response = requests.get(url, headers=headers)
    sha = None
    if get_response.status_code == 200:
        sha = get_response.json()['sha']
    
    # Create or update
    payload = {
        'message': message,
        'content': encoded_content,
        'branch': 'main'
    }
    if sha:
        payload['sha'] = sha
    
    response = requests.put(url, json=payload, headers=headers)
    
    if response.status_code in [201, 200]:
        return {
            'status': 'success',
            'sha': response.json()['commit']['sha'],
            'url': response.json()['content']['html_url']
        }
    else:
        return {
            'status': 'failed',
            'code': response.status_code,
            'error': response.json()
        }
```

---

## API Limitation: Nested Directory Creation

**Issue:** GitHub API (v3) will not create a file in a nested directory that doesn't exist.

**Error:**
```
404 Not Found
{
  "message": "Not Found",
  "documentation_url": "https://docs.github.com/rest/repos/contents#create-or-update-file-contents"
}
```

**Why:** The API requires the parent directory to exist before creating a file in it.

**Workaround 1: Create placeholder file first**
```python
# Create .github/README.md first
create_or_update_file(owner, repo, '.github/README.md', '# GitHub config', 'ci: init .github directory', token)

# Now create .github/workflows/credential-check.yml
create_or_update_file(owner, repo, '.github/workflows/credential-check.yml', workflow_content, 'ci: add workflow', token)
```

**Workaround 2: Use git CLI instead**
```bash
git clone https://github.com/owner/repo.git
cd repo
mkdir -p .github/workflows
echo "..." > .github/workflows/credential-check.yml
git add .github/workflows/credential-check.yml
git commit -m "ci: Add workflow"
git push origin main
```

**Recommendation:** For complex directory structures, use git CLI. For simple file updates, use API with placeholder workaround.

---

## Consolidating Multiple Repos into One (History Preserved)

**When:** Merging N repos into a single repo, each under its own subdirectory, keeping every original commit.

**The correct recipe (git CLI, no filter-repo needed):**
1. Clone each source fresh.
2. Rewrite each source's history so all paths move under a subdir: `git filter-branch --index-filter '...sed prefix...' HEAD`.
3. In a fresh target repo, `git merge --allow-unrelated-histories` each rewritten source.
4. Verify with `git log --oneline -- <subdir>/ | wc -l` — must equal the source's original commit count.

Full working recipe (with the sed one-liner and verification): see `references/repo-consolidation-with-history.md`.

**Two pitfalls that WILL bite (both hit in practice):**

- **`git read-tree --prefix` gives you a SNAPSHOT, not history.** It copies the current tree into a subdir as a single commit — the source's commit log does NOT come with it. If the user wants commits preserved, `read-tree` is wrong. Use `filter-branch` + `merge --allow-unrelated-histories`. Do not combine `merge -X subtree` AND `read-tree` for the same source — that double-writes files (once at root, once nested).
- **sed delimiter collision on hyphenated prefixes.** The classic `filter-branch` index-filter uses `sed "s-\t-&PREFIX/-"`. If PREFIX contains a hyphen (e.g. `ig-1-protocol`), the `-` delimiter breaks silently and the rewrite does NOTHING (filter-branch reports success, tree unchanged). Fix: use a delimiter absent from the prefix, e.g. `sed "s@\t\"*@&ig-1-protocol/@"`. Always verify paths actually moved (`git ls-files | head`) before trusting the rewrite.

**Always confirm scope before destructive follow-up:** when the user says "combine then empty the originals," flag that emptying destroys the source commit history — snapshot merges leave the originals as the ONLY holder of that history. Push real history into the target first, verify commit counts, THEN empty.

**Retiring source repos after consolidation (empty + rename tombstone):** once history is verified safe in the target, empty each source to a single tombstone README pointing at the consolidated repo, then `gh repo rename` it to a delete-marker (e.g. DEL-X-1) rather than hard-deleting — reversible, unambiguous intent. Echo back and confirm before emptying (it's itself destructive). Full recipe: Step 5 in `references/repo-consolidation-with-history.md`.

---

## Forking an External Repo to tanzimozer

**One-liner — no local clone needed:**
```bash
gh repo fork <owner>/<repo> --clone=false
# Returns: https://github.com/tanzimozer/<repo>
```
`gh` reads the stored auth (`tanzimozer`) and creates the fork instantly. Use `--clone=true` only if you need it locally too.

**Finding the right upstream repo:** GitHub search by name often returns 60+ noise results. YouTube search (`<tool> <author>`) surfaces the canonical repo faster via video descriptions — then confirm with `gh` or browser. Used this to find `garrytan/gstack` (124k stars) in one shot.

---

## Pitfalls & Fixes

### Pitfall 1: Token Scope Mismatch
**Symptom:** "API returned 403 — insufficient permissions"  
**Check:** Does the token have `repo` scope (required for private repos and write access)?
```bash
curl -H "Authorization: token YOUR_TOKEN" https://api.github.com/user/repos
```

### Pitfall 2: `/user/repos` returns only public repos
**Symptom:** Private repos are missing from API list  
**Cause:** Token doesn't have full `repo` scope, or API filtering is default-public  
**Fix:** Use `git clone` instead (credentials from `~/.git-credentials` or embedded token)

### Pitfall 3: Rate limit exceeded
**Symptom:** "API rate limit exceeded"  
**Check:** 
```bash
curl -H "Authorization: token TOKEN" https://api.github.com/rate_limit
```
**Limit:** 5,000 requests/hour (authenticated), 60/hour (unauthenticated)

### Pitfall 4: Workflow files not triggering
**Symptom:** `.github/workflows/credential-check.yml` exists but no runs  
**Cause:** Workflow syntax error or branch not correct  
**Debug:**
- Check workflow syntax via `https://github.com/owner/repo/blob/main/.github/workflows/credential-check.yml`
- Look for "This workflow has errors" banner
- Check Actions tab for run history

### Pitfall 5: .gitignore not working after commit
**Symptom:** Files in .gitignore are still in the repo  
**Cause:** Files were committed before .gitignore was added  
**Fix:**
```bash
git rm --cached sensitive_file
git commit -m "Remove sensitive file from tracking"
git push
```

---

## Diagnostics Checklist

Use this checklist when auditing a repo:

- [ ] Repository is accessible (token authorized)
- [ ] Default branch is correct (usually `main`)
- [ ] README.md exists and is current
- [ ] .gitignore excludes credentials, build artifacts, node_modules
- [ ] docs/ directory exists with architecture decisions
- [ ] .github/ directory configured with workflows
- [ ] No sensitive files in recent commits (check last 10)
- [ ] Branch protection rules configured (if needed)
- [ ] Collaborators and permissions are correct
- [ ] Latest commit is recent (not stale)
- [ ] Issues and PRs are triaged (if applicable)

---

## Session Context (June 11, 2026)

**What happened:**
- Ran full diagnostics on friday-master repo
- Discovered missing README.md, .gitignore, .github/workflows
- Created README, .gitignore via API
- Created .github/README.md to establish directory
- Attempted to create workflow file but hit 404 (nested directory limitation)
- Documented workaround: use git CLI for complex nested structures

**Decision made:**
- README.md and .gitignore are critical — always create early
- .github/workflows files need placeholder .github/ entry first
- For future nested structures, recommend git CLI over API

---

## Related Skills

- **github-connect** — GitHub API operations and authentication
- **credential-management-tanzim** — credentials that power GitHub operations
- **git-workflow** (if exists) — local git operations

---

**Status:** Production  
**Last Updated:** June 11, 2026 at 20:35 UTC
