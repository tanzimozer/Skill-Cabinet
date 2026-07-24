# ig-churn Session — June 2, 2026

## What was accomplished
- Cloned repo to VM, npm install, Playwright verified
- Cookie injection via inject_cookies.js — confirmed `Logged in: true`
- ig-audit.js headless patch applied (`sed -i 's/headless: false/headless: true/g'`)
- Discovered audit fails on VM (Instagram modal never renders headless — dead end)
- Switched to direct friendships API — fetched 634 followers, 1454 following
- Official data export (followers_1.json + following.json) provided by user as backup
- Built unfollow queue: 1,004 accounts (443 mutuals protected)
- Ran 84 + 21 unfollows in session 1 & 2 via API
- Launched continuous loop at 100/batch, 60s interval, 0.8s per action

## Key files on disk
- `~/ig-churn/Sub-Folder/reports/followers_2026-06-02.csv` — 634 followers
- `~/ig-churn/Sub-Folder/reports/unfollow_queue_2026-06-02.csv` — 1,004 accounts
- `~/ig-churn/Sub-Folder/reports/unfollow_log.json` — per-action log
- `~/ig-churn/Sub-Folder/reports/following_ids.json` — last username→ID map
- `~/ig-churn/Sub-Folder/inject_cookies.js` — cookie injection script

## Tanzim's verification protocol
1. Show full unfollow list as text first
2. Run in 10–30 name batches, user reviews
3. After 2–3 clean batches → approve full automation
4. Never unfollow anyone in followers list — check twice before running

## Instagram API endpoints confirmed working
- `GET /api/v1/friendships/{uid}/followers/?count=200` ✅
- `GET /api/v1/friendships/{uid}/following/?count=200` ✅  
- `POST /api/v1/friendships/destroy/{uid}/` ✅
- `GET /api/v1/users/web_profile_info/?username=X` ❌ 429 rate-limited aggressively

## Tanzim's account
- User ID: `40730017115`
- Handle: `tanzim.ozer`
- Post-session: ~900 remaining in unfollow queue
