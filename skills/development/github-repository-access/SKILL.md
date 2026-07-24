---
name: github-repository-access
description: Access and check GitHub repositories, commits, and changes
category: development
---

## When to use

- User asks about repository contents, latest changes, commits
- Need to check specific files or commit history
- User mentions a repository name to investigate

## Workflow

### 1. Check for GitHub token first
Always verify GitHub access before attempting API calls:

```bash
# Check if token exists
ls ~/.hermes/.github_credentials

# If exists, read token structure
cat ~/.hermes/.github_credentials
```

Token should be in format:
```json
{
  "token": "ghp_...",
  "token_name": "Friday-Hermes"
}
```

### 2. Use direct API access, not memory/hindsight first

**CRITICAL:** When user asks about repository contents or latest changes, check GitHub directly FIRST. Do not rely on memory or hindsight as primary source.

**Common pitfall:** Saying "from memory, repo X has Y" when user wants current state. Always verify live state.

### 3. Repository discovery

List all user repositories to find exact names:
```python
import json, urllib.request

TOKEN = json.load(open('/home/hermes/.hermes/.github_credentials'))['token']
headers = {
    'Authorization': f'token {TOKEN}',
    'Accept': 'application/vnd.github.v3+json',
    'User-Agent': 'Friday-Hermes'
}

req = urllib.request.Request('https://api.github.com/user/repos?per_page=100', headers=headers)
resp = json.loads(urllib.request.urlopen(req, timeout=30).read())

# Filter for relevant repos
for repo in resp:
    if 'keyword' in repo['name'].lower():
        print(f"📁 {repo['name']} — {repo.get('description', 'No description')}")
```

### 4. Check latest commits

For specific repository investigation:
```bash
# Clone if needed
git clone https://github.com/username/repo-name.git /tmp/repo-check

# Get latest commits
cd /tmp/repo-check && git log --oneline -5

# Show latest change details
git show HEAD --name-only
```

### 5. Repository name variations

User may refer to repos by:
- Exact name: `TERRAjob.V2`
- Casual name: `Job Hammer` (actually `JOB_HAMMER`)
- Underscore vs dash variations
- Case variations (all caps vs mixed)

Always search through full repo list to match user intent.

## Success criteria

- Found correct repository matching user's description
- Retrieved actual current state (commits, files, changes)
- Provided accurate information about latest changes
- Did not rely solely on stale memory/hindsight data

## Troubleshooting

**Token missing:** Check hindsight/memory for where token might be stored, or ask user for fresh token.

**Repository not found:** List all repos and ask user to clarify which one they meant.

**Private repo access:** Ensure token has appropriate scopes for private repositories.