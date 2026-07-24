# GitHub Repository Cleanup via Admin PAT — Session June 9, 2026

## Scenario
User has 26 repos, wants to keep only 9. Need to delete 17 repos programmatically using admin PAT.

## Prerequisites
- Admin PAT (scopes: repo, delete:repo)
- GitHub account username
- List of repos to keep

## Script Pattern

```python
import requests

github_pat = "<DEAD_GITHUB_PAT_REMOVED>"  # temp admin PAT
account = "tanzimozer"

headers = {
    'Authorization': f'token {github_pat}',
    'Accept': 'application/vnd.github.v3+json',
}

# Define repos to KEEP (exact repo names)
keep_repos = {
    'JOB_HAMMER',
    'JOB_HAMMER-personal',
    'Mag-Seattle',
    'ig-1-protocol',
    'friday-master',
    'friday-infra',
    'Tanzim_Frameworks',
    'Linked_Engine',
    'hermes-agent-bootstrap',
}

# Fetch all repos (paginated)
repos = []
page = 1
while True:
    url = f'https://api.github.com/user/repos?per_page=100&page={page}'
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        break
    data = response.json()
    if not data:
        break
    repos.extend(data)
    page += 1

# Delete repos NOT in keep list
deleted = []
failed = []

for repo in repos:
    repo_name = repo['name']
    
    if repo_name not in keep_repos:
        url = f'https://api.github.com/repos/{account}/{repo_name}'
        response = requests.delete(url, headers=headers)
        
        if response.status_code == 204:
            deleted.append(repo_name)
        else:
            failed.append((repo_name, response.status_code, response.text))

print(f"✓ Deleted: {len(deleted)}")
print(f"✗ Failed: {len(failed)}")
```

## Important Notes

### Admin PAT Scopes
For deletion to work, PAT must have:
- `repo` — Full control of private repositories
- `delete:repo` — Delete repositories

If using standard PAT (without delete:repo), deletion will fail with 403 Forbidden: "Must have admin rights to Repository."

### Temporary Admin PATs
If admin PAT is temporary/short-lived:
- Store it in vault.json with a `_note` field explaining expiry
- Update ~/Desktop/CREDENTIALS_MASTER.md with expiry date
- Use it immediately, then discard after the session
- Do NOT rely on it persisting across sessions

### Pagination
GitHub API returns max 100 repos per page. Always paginate when fetching all repos:
```python
page = 1
while True:
    url = f'https://api.github.com/user/repos?per_page=100&page={page}'
    response = requests.get(url, headers=headers)
    if not response.json():
        break
    repos.extend(response.json())
    page += 1
```

### Testing Deletion
Before bulk deletion, test on one repo:
```python
test_repo = "ReGen-Scraper"
response = requests.delete(
    f"https://api.github.com/repos/{account}/{test_repo}",
    headers=headers
)
print(f"Test deletion: {response.status_code}")  # Should be 204
```

### Success Indicator
Successful deletion returns HTTP 204 (No Content) with empty response body. Treat 204 as success only.

### Common Errors
- **403 Forbidden:** PAT lacks delete:repo scope or insufficient repo admin rights
- **404 Not Found:** Repo already deleted or name mismatch
- **422 Unprocessable Entity:** Repo may have rules preventing deletion (e.g., branch protection)

## Session Results (June 9, 2026)

| Action | Count |
|--------|-------|
| Total repos scanned | 26 |
| Repos to delete | 17 |
| Successfully deleted | 17 |
| Failed deletions | 0 |

Deleted repos:
- FLUXJOB, FLUXJOB-personal
- ig-churn, IGR_V5
- magazine-engine, Magazine-Production-Template-One
- ReGen-Scraper
- resume-engine, resume_engine_userx, resume_engine_userx_master
- Santifer-career-ops
- TERRAjob.V2-personal
- Timbr, TIMBR-3-Website, timbr-ui
- TIMBR_Workout_Series_Ebook
- wix-control

Kept repos: 9 (as specified)
