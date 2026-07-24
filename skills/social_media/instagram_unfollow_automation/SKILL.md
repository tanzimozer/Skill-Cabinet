---
name: instagram_unfollow_automation
category: social_media
description: Bulk unfollow non-followers on Instagram via direct REST API — no Playwright, no headless browser. Covers queue building, batched execution, log management, and pitfalls.
---

# Instagram Unfollow Automation

## When to use
Tanzim wants to clean up his Instagram following list — remove everyone who doesn't follow back, while preserving mutuals and whitelisted accounts.

## Core approach
Use Instagram's internal REST API directly (not Playwright/headless Chrome — Instagram blocks headless from VM IPs). Session cookies from a real logged-in browser session authenticate all requests.

## Critical: always build queue from the official JSON export
**Do NOT derive the queue from API scraping alone.** Use the official Instagram data export files:
- `followers_1.json` — people who follow Tanzim
- `following.json` — people Tanzim follows

**Parse `following.json` correctly:**
```python
# Username is in 'title', NOT in string_list_data[*]['value']
following = set(item['title'].lower() for item in data['relationships_following'])
```

**Parse `followers_1.json` correctly:**
```python
# Username is in string_list_data[*]['href'], not 'value' (no 'value' key)
followers = set()
for item in followers_data:
    for sv in item.get('string_list_data', []):
        followers.add(sv['href'].split('/')[-1].lower())
```

Non-followers = `following - followers`. This is the authoritative queue.

## API endpoints
```
GET  https://www.instagram.com/api/v1/friendships/{USER_ID}/following/?count=200
POST https://www.instagram.com/api/v1/friendships/destroy/{TARGET_UID}/
     body: user_id={TARGET_UID}
```

Required headers:
```python
{
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 13_6) AppleWebKit/537.36...',
    'X-CSRFToken': '<csrftoken>',
    'X-IG-App-ID': '936619743392459',
    'Referer': 'https://www.instagram.com/',
    'Content-Type': 'application/x-www-form-urlencoded',
}
```

## Execution parameters (tested safe)
- **Per-action delay:** 0.3s (faster is viable; 0.8s+ is needlessly slow)
- **Batch size:** 50 per batch
- **Between-batch pause:** 60s
- **Between-round pause:** 180s (when fetching fresh IDs each round)

## Pagination problem — key pitfall
The following API returns ~157–200 accounts per fetch. `has_more` may return `False` even when more accounts exist — Instagram throttles the view. The workaround: loop rounds, re-fetch IDs each round, action whatever matches the queue, repeat until 3 consecutive empty rounds.

```python
empty_rounds = 0
while remaining:
    id_map = fetch_following_ids()  # ~157-200 per call
    actionable = [(u, id_map[u]) for u in remaining if u in id_map]
    if not actionable:
        empty_rounds += 1
        if empty_rounds >= 3: break
        time.sleep(180); continue
    else:
        empty_rounds = 0
    # run batches...
```

## Log file discipline
- Use a **separate log file per run** (`unfollow_log_v2.json`, etc.) when restarting — overwriting or reusing corrupted logs causes `not_found` status for everything.
- Log structure per entry: `{username, uid, status, ts}` where status = `'unfollowed'` or `'failed_<code>'`.
- Save log after every batch, not just at the end.

## Verifying completion
After the run, confirm via live API:
```python
r = requests.get(f'.../friendships/{USER_ID}/following/', params={'count': 200}, ...)
data = r.json()
print(f"has_more: {data['has_more']}, count: {len(data['users'])}")
```
Cross-check: all remaining following accounts should be mutuals (in followers set).

## Pitfalls
- **Parallel script runs corrupt the log** — never run two unfollow scripts simultaneously. They'll double-process accounts and the log becomes inconsistent.
- **`not_found` in log = log corruption**, not Instagram errors — means the log was reused incorrectly.
- **"814 remaining" after run = stale queue artifact** — trust the live API count, not the queue diff, for final state.
- **Background process buffering** — `process log` may show 0 lines for the first ~60s while Python buffers stdout. It's running; wait before panicking.
- **Don't over-trust `has_more: False`** — Instagram lies. Run 3 empty rounds before concluding the queue is exhausted.

## References
- See `references/tanzim_ig_run_2026-06.md` for session log and account counts from the first full run.
