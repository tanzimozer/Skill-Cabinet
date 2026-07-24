# Creating a GitHub Repo from Loaded Documents — Pattern (Jun 2026)

## Scenario
Tanzim shares a multi-file project as individual text documents (e.g. an FFmpeg engine: `engine.py`, `stage1_extract.py`, `stage2_select.py`, `utils/*.py`, `requirements.txt`, `README.md`). The files land in `/home/hermes/.hermes/document_cache/doc_<hash>_<name>`. He says: "Create a repo on my GitHub."

## Key Steps

1. **Reconstruct the real directory structure first.** The cache flattens everything (`doc_<hash>_quality.py`). Read the imports to recover the layout. Here `stage2_select.py` did `from utils.quality import ...`, `from utils.scene_detect import ...`, `from utils.contact_sheet import ...` — so `quality.py`, `scene_detect.py`, `contact_sheet.py`, and the empty `__init__.py` belong under `utils/`, not the root. Map each cached file to its correct destination before copying.

2. **Add a `.gitignore` unprompted.** For any data/media pipeline, exclude generated artifacts so they never get committed by accident. For the FFmpeg engine: frames, videos, `output/`, `_pruned/`, `_contact_sheets/`, `*.jpg`/`*.mp4`, `__pycache__/`, venvs. This is a genuine value-add Tanzim expects, not noise.

3. **Default to PRIVATE.** His personal projects are private unless he says otherwise.

4. **Push, then report the URL + structure in a compact block.** One block, file tree, done.

5. **Flag real code constraints honestly, briefly, once.** Example flagged here: bare `from utils...` imports mean it only runs from repo root and isn't pip-installable. Stated as a constraint, not a bug, then offered to leave or fix. Do NOT pre-fix his code without asking — he said "I will work to improve this before deployment with you." He wants to harden it himself.

## GitHub Auth
Use the admin PAT from vault.json (see github-admin-cleanup.md for scope notes: `repo` minimum; `delete:repo` only for deletion). Repo creation needs `repo` scope. Create via API:

```python
import requests
headers = {'Authorization': f'token {pat}', 'Accept': 'application/vnd.github.v3+json'}
requests.post('https://api.github.com/user/repos',
              headers=headers,
              json={'name': 'ffmpeg-engine', 'private': True,
                    'description': 'Two-stage FFmpeg frame extraction + scene-aware selection'})
```
Then init local git, add remote, commit, push.

## Account
GitHub username: `tanzimozer`.
