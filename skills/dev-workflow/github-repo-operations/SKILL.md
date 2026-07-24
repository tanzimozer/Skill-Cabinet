---
name: github-repo-operations
description: Creating GitHub repos and pushing for Tanzim (account tanzimozer) via API + git. Covers the PAT fallback/validation chain when a stored token is dead, creating a repo over the REST API, pushing with a token-in-URL remote, and sanitizing the remote afterward. Use whenever a task says "build/push X on my github" or needs a repo created.
---

# GitHub Repo Operations (Tanzim)

Tanzim's account is **tanzimozer**. Git identity: `Tanzim Ozer <tanzim.seattle@gmail.com>` (already set in global config). No `gh` CLI installed — use the REST API + plain git.

## PAT fallback + validation chain (the key technique)

Stored tokens go stale. Don't trust the first one you find — validate every candidate against `GET /user` before using it. Known token locations, in order:

1. `~/.hermes/.github_credentials` — JSON `{"token": "...", "token_name": "..."}`. Often **dead** (was 401 this session).
2. `~/Desktop/CREDENTIALS_MASTER.md` — running credential log; grep for `gh[po]_[A-Za-z0-9]{20,}`. **This held the live one.**
3. `~/.hermes/.env` — grep same pattern; may hold a stale/placeholder.

Validation probe (run over all candidates, pick the one that returns 200):

```python
import json, re, urllib.request
cands = []
cands += re.findall(r'gh[po]_[A-Za-z0-9]{20,}', open('/home/hermes/Desktop/CREDENTIALS_MASTER.md').read())
# also: ~/.hermes/.github_credentials (json), ~/.hermes/.env
for tok in dict.fromkeys(cands):  # dedupe, keep order
    req = urllib.request.Request('https://api.github.com/user',
        headers={'Authorization': f'token {tok}', 'User-Agent': 'friday'})
    try:
        u = json.load(urllib.request.urlopen(req))
        print('VALID', u['login'], '...'+tok[-6:]); break
    except Exception as e:
        print('invalid ...'+tok[-6:], e)
```

If NO candidate validates, ask Tanzim for a fresh PAT — do not stall silently.

## Create a repo over REST

```python
data = json.dumps({"name": "Instagrammer", "description": "...", "private": True}).encode()
req = urllib.request.Request('https://api.github.com/user/repos', data=data,
    headers={'Authorization': f'token {tok}', 'User-Agent': 'friday',
             'Accept': 'application/vnd.github+json'})
json.load(urllib.request.urlopen(req))  # returns repo object; full_name, html_url, private
```

Default to **private** unless told otherwise (personal projects).

## Push, then sanitize the remote

Push with the token embedded in the remote URL, then immediately strip it so the
token isn't left sitting in `.git/config`:

```bash
git init -q && git add -A
git -c user.name="Tanzim Ozer" -c user.email="tanzim.seattle@gmail.com" commit -q -m "..."
git branch -M main
git remote add origin https://${TOK}@github.com/tanzimozer/Instagrammer.git
git push -u origin main
git remote set-url origin https://github.com/tanzimozer/Instagrammer.git   # SANITIZE — drop the token
```

## Pitfalls
- A 401 from `GET /user` means the token is dead — don't keep trying it against repo endpoints, move to the next candidate.
- Never commit secrets: scaffold a `.gitignore` covering `.env`, `state/`, `logs/`, `session/`, `*.sqlite` BEFORE the first `git add -A`.
- Leaving the token in the remote URL is a leak; always `set-url` back to the clean HTTPS URL after pushing.
