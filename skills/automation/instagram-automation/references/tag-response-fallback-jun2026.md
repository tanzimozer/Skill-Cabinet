# Instagram Tag Response Fallback — June 2026

## Problem
Full scraper run returns 0 results despite finding candidates at tag level.

## Root Cause
`/api/v1/users/{uid}/info/` returns HTML (200 OK, not JSON) when session is flagged/checkpointed.
The silently-passing 200 means the enrich function returns None for every user — all filtered out.
The tag endpoint `/api/v1/tags/{tag}/sections/` stays live much longer — candidates show but can't be enriched.

## Detection
```python
r = requests.get(f'https://www.instagram.com/api/v1/users/{uid}/info/', ...)
if not r.text.strip().startswith('{'):
    print("BLOCKED — HTML response, session flagged — stop run, get fresh cookies")
```
Always test one enrich call before committing to a full scrape run.

## Fallback: Use Data Already in Tag Response
The sections API embeds user data directly on each media item — use it when enrich is blocked:

```python
for section in data.get('sections', []):
    for media in section.get('layout_content', {}).get('medias', []):
        user = media.get('media', {}).get('user', {})
        # Available without enrich:
        #   pk, username, full_name, profile_pic_url
        #   media.like_count, media.comment_count
        # NOT available without enrich:
        #   biography, follower_count, is_private, is_business
```

**Strategy:** collect usernames from tag response, save to file, enrich in a separate session when cookies are fresh.
This preserves the discovery run even when the account is flagged.

## Fix
Fresh cookies via Cookie-Editor Chrome extension (cgagnier, blue icon).
Must export from instagram.com tab while logged in.
Correct export = plain JSON array. Wrong export (hotcleaner.com URL in output) = encrypted, unusable.

## Two-phase workaround when session partially flagged
1. **Phase 1 (now):** Harvest usernames from tag sections API only — save raw list
2. **Phase 2 (fresh session):** Load saved usernames, enrich each, apply filters, push to sheet
This decouples discovery from enrichment and survives partial session flags.
