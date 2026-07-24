# Private Repos Enumeration Pattern

When the `/user/repos` API call returns only a subset of actual repos (or none), the issue is token scope vs credential storage. Use this pattern to reliably discover and enumerate private repos.

## Problem

`/user/repos` with stored GitHub token returns only **public repos** even if token has `repo` scope. Private repos exist but are not returned.

## Root Cause

GitHub API's `/user/repos` is NOT the same as GitHub web's "Your Repos" page. The API filters based on token scope at API request time, separate from how git credentials work. A token with `repo` scope should return both, but server-side filtering sometimes hides private repos if they're not associated with the OAuth app that generated the token (e.g., PATs from different contexts, or org-private repos).

## Solution: Direct Curl Query with Per-Page Filtering

Instead of trusting the API response summary, enumerate with explicit filters and parse all pages:

```bash
TOKEN=$(jq -r '.token' ~/.hermes/.github_credentials)

# Query with explicit private=true filter
# If this works, private repos exist but API is hiding them by default
curl -s -H "Authorization: token $TOKEN" \
  "https://api.github.com/user/repos?type=all&per_page=100" | \
  jq '.[] | select(.private == true) | {name, url, private}'
```

Returns JSON array of private repos. If empty, the token genuinely lacks scope.

## Multi-Repo Scenario: Tanzim's Setup

**Public repos** (visible via `/user/repos`):
- `resume_engine_userx`
- `Santifer-career-ops`
- `TERRAjob` (V1 template)
- `friday-master` (skills repo)
- `timbr-ui`

**Private repos** (hidden by default, visible with explicit filter):
- `TERRAjob.V2` — staging/testing version of TERRAjob
- `TERRAjob.V2-personal` — Tanzim's personal working copy (do not modify directly)
- `JOB_HAMMER` — separate job crawl system (different structure from TERRAjob)
- `FLUXJOB` — optimized TerraJob fork

**Key distinction:**
- `TERRAjob.V2` has Stage 1 Job Crawl, Stage 2 Resume Tailoring, Stage 3 Application
- `JOB_HAMMER` has Stage 1 Crawl, Stage 2 Resume, plus onboarding docs
- Both are live, separate systems

## Shell Pattern for Session Work

```bash
#!/bin/bash
TOKEN=$(jq -r '.token' ~/.hermes/.github_credentials)

# List all private repos with keyword filter
list_private_repos() {
  local keyword="$1"
  curl -s -H "Authorization: token $TOKEN" \
    "https://api.github.com/user/repos?type=private&per_page=100" | \
    jq ".[] | select(.name | contains(\"$keyword\")) | {name, url, private, updated_at}"
}

# Pull a specific private repo
pull_private() {
  local repo_name="$1"
  if [ -d "/tmp/$repo_name" ]; then
    cd "/tmp/$repo_name" && git pull origin main
  else
    git clone https://github.com/tanzimozer/$repo_name.git "/tmp/$repo_name"
  fi
}

# Usage:
list_private_repos "job"        # Shows JOB_HAMMER, TERRAjob.V2*
pull_private "TERRAjob.V2-personal"
```

## In Execute_code (Python)

```python
import requests, json, os

creds_path = os.path.expanduser('~/.hermes/.github_credentials')
with open(creds_path) as f:
    token = json.load(f)['token']

headers = {'Authorization': f'token {token}'}
resp = requests.get(
    'https://api.github.com/user/repos',
    params={'type': 'all', 'per_page': 100},
    headers=headers
)

private_repos = [r for r in resp.json() if r['private']]
for repo in private_repos:
    print(f"{repo['name']:40} — {repo['updated_at']}")
```

## Pitfall: Ambiguous Repo Names

Tanzim has **3 repos with "TERRAjob" in the name**:
1. `TERRAjob` — public template/reference
2. `TERRAjob.V2` — private, staging version
3. `TERRAjob.V2-personal` — private, personal working copy

**Do NOT confuse them.** When pulling:
- Use full exact name: `TERRAjob.V2-personal` not `TERRAjob.V2` (wrong system)
- Both are live simultaneously
- TERRAjob.V2-personal should not be modified directly (Tanzim's personal work)

Similarly, **JOB_HAMMER is not related to TERRAjob** — completely separate system with different structure.

## Discovery Checklist

Before pulling any repo:
1. Confirm the exact name via `list_private_repos` (case-sensitive)
2. Check `/tmp/` for existing clone — prefer `git pull` over re-clone
3. Verify the system it powers (JOB_HAMMER → job crawl, TERRAjob.V2 → resume tailoring, etc.)
4. If Tanzim says "personal version", assume TERRAjob.V2-personal (read-only audit)
