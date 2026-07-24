# Account Pool Management (Turro / scrape-and-follow ops)

Context for the Turro project: separating read and write load across owned IG accounts,
and where the owned-handle ledger lives.

## The owned-handle ledger — "IG Creds" tab
- **Sheet:** `Instagrammer` — ID `1NVaI-jXqfS1z6aMLvNlwJCZoSzVMzP-17to24kKMcDA`
- **Tab:** `IG Creds`
- **Columns:** `Username | Password | Accessible | Cookies | Notes`
- Other tabs in this sheet: Overview, 1·CRAWL…7·SCHEDULE, Infrastructure, Config, Questions, Results, Queue.

An account is **fully usable for scraping** only if it has: password on file AND a cookie AND
`Accessible = TRUE`. Name-only rows are not reachable without provisioning.

Query for ready candidates (password present, no cookie yet):
```python
# has password + no cookie = candidate to warm up and grab a cookie
if p and not c: candidate
```
Watch the Notes column — accounts flagged "Log in from another device security check point"
are NOT clean pickups; the checkpoint must be cleared (login from trusted device/home IP,
pass the challenge) before a cookie can be grabbed.

## Read/write separation rule (Turro architecture)
- **Reads** run through a pool of disposable **burner** accounts (target: 10) to spread
  read-rate flags. **Writes** (follow/unfollow) run through ONE **master** account that builds
  the real social graph and never bulk-reads.
- **An account must never be both master and burner.** If the master appears in the burner
  pool (e.g. `tanzim_ozer` doubling in), drop it from reads — master-only — and add a fresh
  burner to keep the count.

## Handle-typo trap
`tanzim_ozer` (underscore) is the single canonical account. "tanzim.ozer" and "tanzimozer"
are typo variants of the SAME handle, not separate accounts — don't count them as extra.

## Cookie hygiene when working with a human handing you cookies
- Validate every pasted cookie live (see SKILL.md §1, web-app endpoints) before wiring it in.
- `sessionid`/`csrftoken` carry an expiry — check it reaches into the future (past runs used
  cookies good into 2027).
- Confirming *which* account is the designated master is the account owner's (Tanzim's) call
  to sign off — log the confirmation, don't rubber-stamp it yourself.
- Warm up fresh burners lightly before first production scrape, or Instagram burns them as a
  cluster on the first run.
