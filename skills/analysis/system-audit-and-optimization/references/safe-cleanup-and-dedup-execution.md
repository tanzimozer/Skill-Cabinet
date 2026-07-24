# Safe cleanup & deduplication execution

Phase-4 "ongoing maintenance" in practice: how to actually clean a cluttered
home dir, redundant repos, bloated logs, and over-full memory/knowledge stores
**without breaking configs, credentials, or losing history.** Tanzim's standing
constraint on all cleanup: *"without breaking any configs or rules"* and (for
repos) *"Don't delete — I'll lose contributions. Just organize."*

## The governing principle: archive, don't delete

Default to **move into a dated archive folder**, never `rm`. Deletion is only on
the table after explicit confirmation and when something is provably redundant.

- Archive root: `~/archive/<purpose>-<YYYY-MM-DD>/` with category subfolders.
- This keeps every move reversible and auditable.
- Report the archive size + path so the user can purge later if they choose.
- Offer (don't impose) a time-boxed auto-purge once they're confident.

## Workflow: plan → confirm → dry-run → execute → verify

1. **Survey first, act second.** Map the clutter into named categories before
   touching anything. Present the scope as a short list with counts.
2. **Confirm scope.** Offer scoped options (all / files-only / memory-only /
   plan-only). Re-confirm before anything deletes — even after a blanket "do it".
3. **Dry-run the file moves.** Build the move plan in code and PRINT it (category
   → file list → total) before executing. Let the user see exactly what moves.
4. **Maintain a protect-list.** Configs, credentials, tokens, active scripts,
   and `.dotfiles` are NEVER swept. Hardcode an explicit allow-out set, e.g.:
   client-secret JSON, voice_server.py, voice_history.json, backup scripts,
   OAuth token (`~/.hermes/google_token.json`), START_HERE docs. Skip anything
   starting with `.`.
5. **Execute, then verify.** After moving, run a verification pass that asserts:
   token present, configs/creds present, every git repo still `git status`-clean,
   any background service still healthy, home item count dropped as expected.

## Redundant-repo detection (before archiving a clone)

Don't assume two similar trees are dupes — prove it:

- Compare file lists: `diff <(cd A && find . -type f -not -path './.git/*'|sort) <(cd B && ...)`.
- Confirm same remote: `git -C A remote -v` vs `git -C B remote -v`.
- Confirm superset: compare `git rev-list --count HEAD` and check the larger
  one's `log --oneline` CONTAINS the smaller one's HEAD commit.
- Confirm both pushed: `git log --oneline @{u}..` returns empty on both.
- Only then archive the smaller/older clone. Keep the superset.

## Service-backed stores: use the built-in consolidation, don't hand-edit

For a memory/knowledge service (e.g. Hindsight on a local port) the data lives
behind an API, NOT in a file you should edit live. The 0-byte `~/.hermes/hindsight.db`
is a stub — the real store is the service.

- Discover capability: `curl -s localhost:<port>/openapi.json` → list paths.
- **Back up before any mutation:** `GET .../banks/<bank>/export` to a dated file.
- Dedup via the designed path: `POST .../banks/<bank>/consolidate`, then poll
  `.../operations/<op_id>` until `status: completed`.
- Note: consolidation typically only folds the **recent** window (`deduplicated:
  false` means nothing recent to merge). Deep historical dedup across tens of
  thousands of facts is the service gardener's job — do NOT hand-delete records
  across the store. Run the endpoint, back up, and leave the rest to the scheduler.
- Hindsight specifics seen: bank `hermes`, port `9177`, health at `/health`,
  consolidation rules already say "merge near-duplicates, never delete, preserve
  history" — which matches Tanzim's constraint, so the built-in path is correct.

## Core memory (the agent's own memory tool) cleanup

- When near the cap (≈10k chars), replace/remove **stale setup entries** first:
  completed-task logs, superseded OAuth client blocks, redundant facts that a
  newer entry already covers. Never remove live rules, current credentials, or
  persona/tonality specs.
- When ADDING a rule would exceed the cap, FOLD it into a related existing entry
  via `replace` rather than adding a new one. Compress wording to fit; the
  replace tool is byte-exact, so trim a word at a time if it reports N-over.

## Pitfalls

- Don't `rm` on a "clean up" request — archive. Deletion needs explicit sign-off.
- Don't sweep dotfiles/configs/creds/tokens — keep an explicit protect-list.
- Don't assume two repos are dupes — verify remote + superset + pushed first.
- Don't hand-edit a running service's store — export + use its consolidate API.
- Don't claim a file is "missing" if it's just been archived — check the archive
  before reporting loss.
- Memory `replace` needs both `content` and `old_string`; it fails byte-exactly
  over the cap, so shorten incrementally rather than retrying the same payload.
