# IG1 Scraping Lessons — June 2026

## What worked
- **Tag sections API** — `POST /api/v1/tags/{tag}/sections/` — reliable, not rate-limited, returns username + uid + is_private from tag posts
- **Follower count text pattern** — `([\d,]+)\s*[Ff]ollowers` on HTML profile pages — confirmed working on public profiles
- **web_profile_info** — `GET /api/v1/users/web_profile_info/?username={username}` — returns full JSON with followers, bio, following count. Rate-limits after heavy use (429) but recovers in ~45–60 min
- **Friendship status check** — `GET /api/v1/friendships/show/{uid}/` — confirmed working, returns `following`, `followed_by`, `blocking`
- **Follow action** — `POST /api/v1/friendships/create/{uid}/` — 45 accounts followed successfully, zero failures

## What failed and why

### HTML bio extraction — does not work on authenticated requests
Meta description tag `<meta name="description" content="...">` is stripped when cookies are present. `edge_followed_by` JSON blob also absent in most responses. Only the text pattern `X Followers` reliably works from HTML.

### Hard female filter during crawl — produces zero results
Bio is not available from HTML scraping. Running `is_female()` as a hard gate during crawl starved every city sweep to zero across multiple full runs. Fix: soft-flag `likely_female: true/false`, collect all qualifying accounts, QC gender after.

### Enrich endpoint `/api/v1/users/{uid}/info/` — rate-limited silently
Returns full HTML login page with HTTP 200. `r.json()` throws silently. Looks like success but every account drops. Do not use for bulk enrichment.

### Follower list API — blocked for new follows
`/api/v1/friendships/{uid}/followers/` returns empty JSON (not an error) for recently followed accounts. Tried on all 45 seeds immediately after following — zero followers returned across all. Needs days-old relationship.

### Suggested users endpoint — UA mismatch
`GET /api/v1/discover/chaining/?target_id={uid}` returns 400 "useragent mismatch" with mobile UA. Requires desktop Chrome UA.

### Fitness hashtags — zero personal accounts
Full sweeps of 10 fitness tags per city across all 14 cities: zero accounts cleared 500–3500 + public + female filters. Tags dominated by gyms, studios, coaches, brands.
Fix: lifestyle tags — `{city}life`, `{city}girl`, `{city}women`, `{city}lifestyle`, `{city}blogger`, `{city}foodie`, `{city}mum`, bare `{city}`.

## Ollama fallback
- Ollama already running on VM — port 11434, version 0.23.2
- Models available: `llama3.1:8b`, `llama3.2:latest`
- Already configured in `~/.hermes/config.yaml` as fallback_provider after Haiku
- Tunnel to Mac Mini must be active for fallback to work
- Purpose: keeps Friday operational when Claude usage limit hits

## Cookie structure in vault (June 2026)
`vault['instagram']` keys: `sessionid`, `csrftoken`, `datr`, `mid`, `ig_did`, `ds_user_id`
Do NOT pass the whole instagram dict as cookies — extract keys explicitly or requests throws TypeError.
