# Safe Repo Consolidation — collapsing duplicate local clones without losing work

When the home folder accumulates multiple clones of the same repo (e.g.
`friday-2.0`, `friday-2.0-active`, `friday-2-0-repo`, `temp-friday-2.0-push`),
consolidate to ONE canonical copy. The risk Tanzim worries about is losing
contributions / the GitHub contribution graph. Reassure with facts, then prove
it before deleting.

## The truth about "will I lose contributions?"

- **Contributions live on GitHub**, tied to commits already **pushed** to the
  remote. Deleting a local folder does NOT touch the remote, so the graph
  doesn't move.
- The only thing genuinely at risk is **uncommitted** or **unpushed** local
  work. Commit + push that first, then delete is 100% safe.
- Never delete on assumption — **verify** every folder's HEAD is already on the
  remote.

## Workflow (verify-salvage-consolidate-delete)

### 1. Map every candidate folder
```bash
cd ~ && find . -maxdepth 3 -type d -iname "*<name>*" 2>/dev/null
for d in <folders>; do
  echo "=== $d ==="; du -sh "$d"
  git -C "$d" remote -v | sed 's/ghp_[A-Za-z0-9_]*/ghp_***/g'   # redact token
  git -C "$d" log --oneline -1
  git -C "$d" status -s | head -5
done
```
Note: which remote each points at (they may differ — e.g. one tracks
`friday-2.0`, another `friday-master`), latest commit, dirty state.

### 2. Salvage uncommitted work FIRST (before any delete)
Find the folder with `git status -s` showing untracked/modified files. Commit
and push it — that folder becomes (or feeds) the canonical copy.
```bash
cd ~/<folder-with-work>
git add -A && git commit -m "<describe salvaged work>"
git push origin HEAD
```

### 3. Verify each delete-candidate is fully on the remote
```bash
for d in <folders-to-delete>; do
  git -C "$d" fetch origin 2>/dev/null
  echo "--- $d ---"
  # any commit on a local branch NOT on any remote = would be lost
  git -C "$d" log --branches --not --remotes --oneline | head -5 || echo "clean"
  git -C "$d" status -s | wc -l | xargs echo "uncommitted:"
done
```
Empty output for both checks = safe. Alternatively confirm a specific HEAD is an
ancestor of the remote:
```bash
git branch -r --contains $(git rev-parse HEAD)   # lists remote branches containing HEAD → safe
```

### 4. Delete the dead folders, keep ONE canonical
```bash
rm -rf <dead-folder-1> <dead-folder-2> ...
ls -d ~/<name>*    # confirm one canonical remains
```

## Token hygiene — pull the PAT out of the remote URL

Old clones often embed the PAT in plaintext in the remote URL
(`https://ghp_xxx@github.com/...`). It sits in `.git/config` on disk. Scrub it:
```bash
cd ~/<canonical>
git remote set-url origin https://github.com/<owner>/<repo>.git   # clean URL
git config --global credential.helper store                       # auth via helper instead
git remote -v                                                     # verify no token
```
Then **advise Tanzim to rotate the token on GitHub** — once a token has lived in
plaintext across several folders, belt-and-braces is to revoke + reissue. Flag
it as a non-urgent follow-up, don't do it unprompted.

## Pitfalls

- **Don't commit `__pycache__`/`*.pyc`.** `git add -A` during salvage will sweep
  in bytecode. Add a `.gitignore` (`__pycache__/`, `*.pyc`), `git rm -r --cached
  __pycache__`, commit, push.
- **Different folders may track different remotes.** Check `remote -v` per folder
  before assuming they're duplicates of the same repo.
- **Always redact tokens in any output you show** — `sed 's/ghp_[A-Za-z0-9_]*/ghp_***/g'`.
- **Sweep, don't delete, loose files.** When the home folder is also cluttered
  with audit/diagnostic `.md`/`.txt` files, move them to `~/archive/<dated>/`
  rather than deleting — reversible, and Tanzim can bin later.
