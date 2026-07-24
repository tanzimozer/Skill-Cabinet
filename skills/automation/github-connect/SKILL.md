---
name: github-connect
description: Connect to GitHub API with stored credentials and perform repo, PR, and issue operations
category: automation
tags: [github, api, automation, repos, pulls, issues]
---

# GitHub Connect

Reusable skill for GitHub API operations using securely stored credentials.

## Credentials (June 2026 Update)

**GitHub credentials are stored in plaintext vault (June 9, 2026 onwards):**

- **Location:** `~/.hermes/vault.json` under `github` key
- **Account:** tanzimozer
- **PAT:** <GITHUB_PAT — see ~/.hermes/vault.json:github_token>
- **Scopes:** repo, gist, user
- **Expiry:** June 9, 2027
- **Status:** Active (tested)

**Important:** See `references/vault-pat-lifecycle.md` for PAT rotation patterns and vault sync verification.

**Load credentials:**

```python
import json
import os

vault_path = os.path.expanduser('~/.hermes/vault.json')
with open(vault_path, 'r') as f:
    vault = json.load(f)

github_token = vault['github']['pat']
```

**Old `.github_credentials` file is deprecated** — use vault.json instead.

## Helper Function

**Updated June 2026 — load from plaintext vault:**

```python
import requests
import json
import os

def github_request(method, endpoint, data=None, params=None):
    """
    Make authenticated GitHub API request.
    
    Args:
        method: HTTP method (GET, POST, PUT, PATCH, DELETE)
        endpoint: API endpoint (e.g., '/repos/owner/repo/issues')
        data: Optional JSON payload for POST/PUT/PATCH
        params: Optional query parameters
    
    Returns:
        Response JSON
    """
    # Load credentials from vault
    vault_path = os.path.expanduser('~/.hermes/vault.json')
    with open(vault_path, 'r') as f:
        vault = json.load(f)
    
    token = vault['github']['pat']
    
    # Build URL
    base_url = f"https://api.github.com{endpoint}"
    
    # Headers
    headers = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.v3+json'
    }
    
    # Make request
    if method == 'GET':
        response = requests.get(base_url, headers=headers, params=params)
    elif method == 'POST':
        response = requests.post(base_url, headers=headers, json=data)
    elif method == 'PUT':
        response = requests.put(base_url, headers=headers, json=data)
    elif method == 'PATCH':
        response = requests.patch(base_url, headers=headers, json=data)
    elif method == 'DELETE':
        response = requests.delete(base_url, headers=headers)
    else:
        raise ValueError(f"Unsupported method: {method}")
    
    response.raise_for_status()
    return response.json()
```

## Common Operations

### Get authenticated user info
```python
user = github_request('GET', '/user')
print(f"Logged in as: {user['login']}")
```

### List repositories
```python
repos = github_request('GET', '/user/repos', params={'sort': 'updated', 'per_page': 100})
for repo in repos:
    print(f"{repo['name']}: {repo['html_url']}")
```

### Get specific repository
```python
repo = github_request('GET', '/repos/tanzimozer/repo-name')
```

### Create a repository
```python
new_repo = github_request('POST', '/user/repos', {
    'name': 'new-repo-name',
    'description': 'Repository description',
    'private': False,
    'auto_init': True  # Create with README
})
```

### List issues
```python
issues = github_request('GET', '/repos/tanzimozer/repo-name/issues', 
                       params={'state': 'open'})
```

### Create an issue
```python
issue = github_request('POST', '/repos/tanzimozer/repo-name/issues', {
    'title': 'Issue title',
    'body': 'Issue description',
    'labels': ['bug', 'high-priority']
})
```

### List pull requests
```python
prs = github_request('GET', '/repos/tanzimozer/repo-name/pulls', 
                    params={'state': 'open'})
```

### Create a pull request
```python
pr = github_request('POST', '/repos/tanzimozer/repo-name/pulls', {
    'title': 'PR title',
    'body': 'PR description',
    'head': 'feature-branch',
    'base': 'main'
})
```

### Merge a pull request
```python
github_request('PUT', f'/repos/tanzimozer/repo-name/pulls/{pr_number}/merge', {
    'commit_title': 'Merge message',
    'merge_method': 'squash'  # or 'merge', 'rebase'
})
```

### Create a file (via API)
```python
import base64

content = base64.b64encode(b'File content here').decode('utf-8')
github_request('PUT', '/repos/tanzimozer/repo-name/contents/path/to/file.txt', {
    'message': 'Create file',
    'content': content,
    'branch': 'main'
})
```

### Update a file
```python
# Get current file to retrieve SHA
file_info = github_request('GET', '/repos/tanzimozer/repo-name/contents/path/to/file.txt')
current_sha = file_info['sha']

# Update with new content
new_content = base64.b64encode(b'Updated content').decode('utf-8')
github_request('PUT', '/repos/tanzimozer/repo-name/contents/path/to/file.txt', {
    'message': 'Update file',
    'content': new_content,
    'sha': current_sha,
    'branch': 'main'
})
```

### List workflow runs
```python
runs = github_request('GET', '/repos/tanzimozer/repo-name/actions/runs')
```

### Trigger workflow
```python
github_request('POST', '/repos/tanzimozer/repo-name/actions/workflows/workflow.yml/dispatches', {
    'ref': 'main',
    'inputs': {'key': 'value'}
})
```

## Git Operations (Command Line)

**See `references/gh-cli-device-flow.md`** when there is NO usable credential and you must authenticate the `gh` CLI interactively (install steps + the pre-piped `printf 'Y\n' | gh auth login --web` pattern that survives a background PTY). Always try the vault PAT first; device flow is the fallback.

**See `references/safe-repo-consolidation.md`** for the verify-salvage-consolidate-delete workflow: collapsing duplicate local clones to ONE canonical copy without losing contributions, plus pulling embedded PATs out of remote URLs. Use it whenever the home folder has multiple clones of the same repo.

GitHub token is also configured for git HTTPS operations:

### Clone via HTTPS with PAT (Vault-Based)

**CRITICAL:** Always verify vault contains the ACTIVE PAT before cloning. If clone fails with "could not read Password" or "repository not found", check which PAT is in vault.

```bash
# Verify active PAT is in vault
python3 -c "import json; v=json.load(open('/home/hermes/.hermes/vault.json')); print(f'Current PAT: {v[\"github\"][\"pat\"][:10]}...')"

# Clone a repo (public or private) — extract PAT from vault
TOKEN=$(python3 -c "import json,os; print(json.load(open(os.path.expanduser('~/.hermes/vault.json')))['github']['pat'])")
git clone https://${TOKEN}@github.com/tanzimozer/repo-name.git

# Push changes
cd repo-name
git add .
git commit -m "Commit message"
git push origin main

# Pull latest
git pull origin main
```

No password prompt — git uses the embedded token.

### Alternative: ~/.git-credentials (Legacy)

If `~/.git-credentials` is populated with credentials, git commands work without embedding token in URL. But vault.json is now the source of truth (June 2026 onwards).

## Bulk Operations Pattern

When working with multiple repos/issues:

```python
import json
import os
import requests

# Load credentials once
creds_path = os.path.expanduser('~/.hermes/.github_credentials')
with open(creds_path, 'r') as f:
    creds = json.load(f)

token = creds['token']
headers = {
    'Authorization': f'token {token}',
    'Accept': 'application/vnd.github.v3+json'
}

# Get all repos
repos_url = 'https://api.github.com/user/repos?per_page=100'
repos = requests.get(repos_url, headers=headers).json()

# Process each repo
for repo in repos:
    print(f"Processing: {repo['name']}")
    # Do something with each repo
```

## Error Handling

```python
try:
    result = github_request('GET', '/repos/tanzimozer/invalid-repo')
except requests.exceptions.HTTPError as e:
    if e.response.status_code == 404:
        print("Repository not found")
    elif e.response.status_code == 401:
        print("Invalid token or unauthorized")
    elif e.response.status_code == 403:
        print("Rate limit exceeded or insufficient permissions")
    else:
        print(f"Error: {e}")
```

## Rate Limits

Check rate limit status:

```python
limits = github_request('GET', '/rate_limit')
print(f"Remaining: {limits['rate']['remaining']}/{limits['rate']['limit']}")
print(f"Resets at: {limits['rate']['reset']}")
```

GitHub API limits:
- **Authenticated**: 5,000 requests/hour
- **Unauthenticated**: 60 requests/hour

## Token Scopes

**Friday-Hermes token has:**
- ✅ `repo` — Full repo access (read, write, push, PRs)
- ✅ `workflow` — Trigger and manage GitHub Actions
- ✅ `read:org` — Read org and team membership

## Known Repos (tanzimozer)

**See `references/admin-pat-workflow.md` for temporary elevated-permission PAT pattern (destructive ops like bulk delete).**

**See `references/private-repos-enumeration.md` for discovery pattern and repo disambiguation.**

Public repos visible via API:
- `resume_engine_userx` — Resume engine for Claude Cowork
- `Santifer-career-ops` — AI-powered job search (14 skill modes, Go dashboard, PDF generation)
- `TERRAjob` — public template (V1)
- `friday-master` — Friday's skill library (all skills pushed here on update)
- `timbr-ui` — TIMBR APP UI mockups (public, created June 1, 2026)

**Private repos** (use enumeration pattern to discover):
- `TERRAjob.V2` — staging/testing version of TERRAjob (Stage 1, 2, 3)
- `TERRAjob.V2-personal` — Tanzim's personal working copy (read-only audit)
- `JOB_HAMMER` — separate job crawl system (Stage 1 Crawl, Stage 2 Resume, different structure)
- `FLUXJOB` — Optimised TerraJob fork

## Skills Repo Pattern

Friday's skill library is version-controlled at `github.com/tanzimozer/friday-master`.

```bash
TOKEN=$(cat ~/.hermes/.github_credentials | python3 -c "import json,sys; print(json.load(sys.stdin)['token'])")
cd ~/.hermes/skills
git add -A
git commit -m "Skills update - $(date +%Y-%m-%d)"
git push https://${TOKEN}@github.com/tanzimozer/friday-master.git master:main
```

Push after: creating new skills, significant patches, end of a productive session.

Private repos are NOT returned by `/user/repos` API even with stored token — use `~/.git-credentials` clone path instead:
```bash
git clone https://github.com/tanzimozer/PRIVATE-REPO-NAME
# git will pick up credentials from ~/.git-credentials automatically
```

## Reliable Token Extraction (From Vault)

**Load directly from plaintext vault** (as of June 2026):

```python
import json
vault = json.load(open(os.path.expanduser('~/.hermes/vault.json')))
token = vault['github']['pat']
```

No special extraction needed — just read the vault JSON file.

## Create Repo + Push in One Flow

```bash
TOKEN=$(cat ~/.git-credentials | grep github | sed 's/.*:\/\/[^:]*://' | sed 's/@.*//')

# Create repo
curl -s -X POST https://api.github.com/user/repos \
  -H "Authorization: token $TOKEN" \
  -H "Accept: application/vnd.github+json" \
  -d '{"name":"my-repo","description":"...","private":false}'

# Init and push
cd /path/to/project
git init && git branch -m main
git add . && git commit -m "Initial commit"
git remote add origin https://github.com/tanzimozer/my-repo.git
git push -u origin main
# Credentials picked up automatically from ~/.git-credentials
```

## Pitfalls

- **Load from plaintext vault, not `.github_credentials`** — old file is deprecated as of June 2026. Use `~/.hermes/vault.json` with `vault['github']['pat']`.
- **Admin PAT for destructive ops only** — see `references/admin-pat-workflow.md` for the pattern. Create temporary, use immediately, revoke immediately. Don't leave elevated permissions in vault overnight.
- **API token scope vs git credentials are different.** The GitHub API token may not have all scopes, causing `/user/repos` to return only public repos. Git clones work because `~/.git-credentials` stores the full PAT separately. When listing repos returns fewer than expected, switch to git clone to verify.
- **Private repo discovery:** if you need to list private repos via API, check that the token has `repo` scope via `/rate_limit` or `/user` — if private repos are missing from the list, they exist but the token can't see them.
- **VM vs user's Mac** — You're on the VM; Tanzim is on a Mac. Don't send him VM-specific git commands.
- **Rate limits** — Check `/rate_limit` before bulk operations. Authenticated: 5,000 req/hr.
- **Token security** — Never commit vault.json to version control. Keep file permissions strict (600).
- **Repo names with special chars** — URL-encode in API paths (slashes, spaces, hyphens).

3. **Check rate limits** before bulk operations
4. **Use proper HTTP methods** — POST for create, PATCH for update, PUT for replace
5. **Include Accept header** for v3 API: `application/vnd.github.v3+json`

## Security Note

Never commit `~/.hermes/.github_credentials` or `~/.git-credentials` to version control. File permissions are set to 600 (owner read/write only).

Token name in GitHub: **Friday-Hermes**
