---
name: friday-memory-compression
description: Compress existing user/memory entries to make room for new approved content when storage is near or at capacity.
tags: [memory, persona, storage, compression]
---

# Friday Memory Compression

## When to use
- User approves new evergreen content to save (intro, bio, brand copy, preferences)
- Memory reports near or at capacity (>85% full)
- `mcp_memory add` fails with "would exceed the limit" error

## Strategy (in order)

1. **Check current usage** — note how many chars are free vs how many you need.
2. **Offload to skills first** — scan memory for credentials, API configs, project-specific procedures. If a matching skill exists (wix, trello, webflow, job-board-scraping, etc.), verify the info is already there, then DELETE from memory. This alone can free 30-50%.
3. **Remove stale/temporary entries** — sprint deadlines, config settings that are discoverable, paused projects. If it won't matter in 30 days, remove it.
4. **Merge short related entries** — combine entries that share a topic into one.
5. **Compress verbose entries** — rewrite long entries to remove redundant phrasing while preserving all facts. Keep meaning identical.
6. **Remove truly redundant entries** — if an entry duplicates info already captured elsewhere, remove the duplicate.
7. **Retry the add** — after each compression step, check if space is now sufficient before continuing.

## What belongs WHERE

| Content Type | Where it goes |
|--------------|---------------|
| API keys, tokens, credentials | Skill (e.g. wix, trello, webflow) |
| Project file paths, folder IDs | Skill or session search |
| Cron job IDs | Session search (recoverable) |
| People's names, roles, permissions | USER profile |
| Security rules, access control | Memory (keep verbatim) |
| Communication preferences | Memory or USER |
| Sprint deadlines, temporary goals | Nowhere — use session search |
| Config settings (discoverable) | Nowhere — check config.yaml |

## Pitfalls
- Memory limit is hard: 1,375 chars for user profile. Each entry + separator counts.
- Do NOT compress entries that contain critical security or access-control rules — preserve those verbatim or near-verbatim.
- After compressing, verify the entry still reads as a declarative fact, not an imperative command.
- Sometimes two compress rounds are needed — check available space after each step before assuming it's enough.

## Multi-Round Reality
A single replace rarely frees enough space. Expect 3-5 replace operations across different entries before the target fits:
1. Try the add/replace — note how many chars over you are
2. Pick the *largest* non-security entry and compress it
3. Retry — repeat until it fits
4. Aim to land below 90% after saving, to leave future headroom

## Verification
- Confirm the new entry saved with `"success": true`
- Check final usage % is below 90% to leave headroom for future additions
