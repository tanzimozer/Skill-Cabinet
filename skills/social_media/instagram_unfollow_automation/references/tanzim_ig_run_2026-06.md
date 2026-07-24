# Tanzim IG Unfollow Run — June 2026

## Account
- Username: tanzim.ozer
- User ID: 40730017115

## Starting state (from official export)
- Following: 1,454
- Followers: 634
- Mutuals: ~443
- Non-followers to unfollow: 1,011 (export-derived queue)

## What went wrong in earlier sessions
1. **Wrong JSON field** — early scripts tried `string_list_data[*]['value']` on `following.json` but that key doesn't exist; username is in `item['title']`.
2. **Parallel script runs** — two scripts ran simultaneously, both writing to the same log file. Result: 800 entries all status `not_found`, unusable log.
3. **Old CSV queue** — first queue derived from API scraping (200-account window), not the full export. Missed ~800 accounts.
4. **`has_more: False` confusion** — API returned 157 accounts with `has_more: False` partway through; we briefly concluded the run was complete. It wasn't — Instagram throttles the following list view.

## Final state (after corrected run)
- Queue rebuilt from export: 1,011 accounts
- Fresh log: `unfollow_log_v2.json`
- Run parameters: 0.3s/action, 50/batch, 60s between batches, 180s between rounds

## Key numbers
- API returns ~157–200 following accounts per fetch
- 3 empty rounds = safe stopping condition
- Tanzim's IG session cookies expire; re-extract from browser if 401s appear
