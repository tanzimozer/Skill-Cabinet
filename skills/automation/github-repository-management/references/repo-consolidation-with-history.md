# Consolidating Repos into Subdirectories — Full Working Recipe

Merges multiple standalone repos into one target repo, each under its own
subdirectory, with **every original commit preserved and attributed to that
subdir**. Verified working (Turro consolidation, July 2026).

## Step 1 — Clone each source fresh

```bash
cd ~/scratch && rm -rf turro-build && mkdir turro-build && cd turro-build
git clone -q https://github.com/OWNER/ig-1-protocol.git ig1-src
git clone -q https://github.com/OWNER/Bulldozer.git    bull-src
git -C ig1-src  rev-list --count HEAD   # record original commit count
git -C bull-src rev-list --count HEAD
```

## Step 2 — Rewrite each history into its subdirectory

CRITICAL: pick a sed delimiter NOT present in the prefix. `ig-1-protocol`
contains `-`, so the usual `s-...-...-` breaks silently. Use `@`.

```bash
cd ~/scratch/turro-build/ig1-src
export FILTER_BRANCH_SQUELCH_WARNING=1
git filter-branch -f --index-filter '
  git ls-files -s | sed "s@\t\"*@&ig-1-protocol/@" |
  GIT_INDEX_FILE=$GIT_INDEX_FILE.new git update-index --index-info &&
  mv "$GIT_INDEX_FILE.new" "$GIT_INDEX_FILE"
' HEAD

# VERIFY the rewrite actually moved paths — do not skip this:
git ls-files | head -3          # must show ig-1-protocol/... prefix
git rev-list --count HEAD       # must equal original count
```

Repeat for the second source with its own prefix (`bulldozer/`).

## Step 3 — Merge rewritten sources into a fresh target

```bash
cd ~/scratch/turro-build && rm -rf turro && mkdir turro && cd turro
git init -q
git commit -q --allow-empty -m "Turro: initial root"
git remote add ig1  ../ig1-src  && git fetch -q ig1
git remote add bull ../bull-src && git fetch -q bull
git merge -q --allow-unrelated-histories --no-edit ig1/main
git merge -q --allow-unrelated-histories --no-edit bull/main
git rev-list --count HEAD        # ~= sum of sources + root + 2 merge commits
```

## Step 4 — README, push, verify nested history intact

```bash
# ...write README.md, git add/commit...
git remote add origin https://github.com/OWNER/Turro.git
git branch -M main
git push -f -q origin main     # -f only if repo pre-created / overwriting

# Prove commits survived under each subdir:
git log --oneline -- ig-1-protocol/ | wc -l   # == source1 count
git log --oneline -- bulldozer/    | wc -l    # == source2 count
```

## Anti-patterns

- `git read-tree --prefix=sub/ -u remote/main` — SNAPSHOT ONLY. Loses source
  commit history. Only acceptable when the user explicitly wants a flat drop.
- Combining `git merge -X subtree=sub` AND `read-tree` for the same source —
  double-writes the tree (files at root AND nested). Pick one path.
- Trusting a hyphenated-prefix `filter-branch` without verifying — it can
  report "Ref rewritten" while changing nothing.

## Destructive follow-up guard

If the plan is "consolidate, then empty/rename the originals": the ORIGINALS
hold the real history. A snapshot merge means emptying them destroys history
permanently. Always push real history into the target and verify per-subdir
commit counts BEFORE touching the sources.

## Step 5 — Retire the source repos (empty + rename tombstone)

Once history is verified safe in the target, retire each source. Empty it to a
single tombstone README pointing at the consolidated repo, then rename to a
delete-marker (e.g. DEL-X-1) so it's obvious the repo is scheduled for removal.

```bash
cd ~/scratch/turro-build && rm -rf empty-work && mkdir empty-work && cd empty-work
for repo in ig-1-protocol Bulldozer; do
  git clone -q https://github.com/OWNER/$repo.git $repo
  cd $repo
  git checkout -q main 2>/dev/null || git checkout -q master 2>/dev/null
  git rm -rq . 2>/dev/null
  printf "# Emptied\n\nContents consolidated into Turro (URL). Scheduled for deletion.\n" > README.md
  git add README.md
  git commit -q -m "Empty repo — consolidated into Turro"
  git push -f -q origin HEAD          # force-push: approval-gated, expected
  cd ..
done

# Rename to delete-markers (gh CLI):
gh repo rename DEL-X-1 --repo OWNER/ig-1-protocol --yes
gh repo rename DEL-X-2 --repo OWNER/Bulldozer     --yes
gh repo list OWNER --limit 200 --json name --jq '.[].name' | grep -E 'DEL-X'
```

Notes:
- Emptying is itself destructive — echo it back and get explicit confirmation
  before running, even after history is safe in the target.
- Leave a tombstone README rather than a truly empty tree, so anyone landing on
  the old URL is redirected to the consolidated repo.
- Rename (not delete) as the retirement step: reversible, and the DEL-X prefix
  makes intent unambiguous without irreversibly destroying the remote yet.
