# TURRO Setup State — Jul 13 2026 (updated)

## Project Turro Sheet
ID: `1ZmyV2nBq5uoql7WD9hxr7q6nM1ofT8nyJ8Q1C45Z4pc`
URL: https://docs.google.com/spreadsheets/d/1ZmyV2nBq5uoql7WD9hxr7q6nM1ofT8nyJ8Q1C45Z4pc

## Setup Checklist — ALL STEPS CLOSED
| Step | Item | Status |
|------|------|--------|
| 1 | Master cookie (tanzim.ozer) re-validated | DONE |
| 2 | Burner pool — 10 of 10 live | DONE |
| 3 | Provision master Google Sheet (Crawl Output + Cookie Rotation tabs) | DONE |
| 4 | Re-authorize WhatsApp bridge | DONE — bridge live; 401 was /status endpoint auth, not disconnection |
| 5 | Mac listener live on port 5055 | DONE — Flask listener at ~/Desktop/Friday/TURRO/listener.py |

## Burner Pool (10/10 live as of Jul 12 2026)
| # | Handle | Password | Cookie Source | Validated |
|---|--------|----------|---------------|-----------|
| 1 | seattle.fitness.community | #IGTheta22x | Prior session | Jul 11 |
| 2 | seattle.fitness.hub | #IGTheta22x | Prior session | Jul 11 |
| 3 | seattle.fitness.events | #IGTheta22x | Prior session | Jul 11 |
| 4 | timbr.fit | #IGTheta22x | Prior session | Jul 11 |
| 5 | timbr.us | #IGTheta22x | Prior session | Jul 11 |
| 6 | seattle.gym | — | Towsif Jul 12 | Jul 12 |
| 7 | seattle.wholefoods | — | Towsif Jul 12 | Jul 12 |
| 8 | fitnesshub.seattle | — | Towsif Jul 12 | Jul 12 |
| 9 | soulcycleseattle | — | Towsif Jul 12 | Jul 12 |
| 10 | seattlefitnessfood | — | Towsif Jul 12 | Jul 12 |

**Master (writes only):** `tanzim.ozer` (dot notation — canonical). `tanzim_ozer` was legacy error.

## tanzim.ozer Account State (Jul 13 2026)
- **Followers:** 626 (from official IG export `followers_1.json`)
- **Following:** 1,500 (from official IG export `following.json`)
- **Non-followers:** 1,082 (following - followers)
- **Unfollow queue:** 1,082 total, 0 done, ~7 days at 150/day cap
- **Data location:** Project Turro sheet → TANZIM tab (A=Followers, B=Following, C=Non-Followers)

## TANZIM Tab (Project Turro sheet)
Written Jul 13 2026 from official IG data export files:
- Col A: FOLLOWERS (626 rows)
- Col B: FOLLOWING (1,500 rows)
- Col C: NON-FOLLOWERS (1,082 rows, sorted A–Z)

## Unfollow Script
Location: `~/Desktop/Friday/TURRO/unfollow.py` (delivered Jul 13)
- 150/day cap, 2s pause between each
- Resumes from `~/Desktop/Friday/TURRO/unfollow_log.json`
- Saves after every unfollow (crash-safe)
- Requires ig_results.json at `~/Desktop/Friday/TURRO/ig_results.json`
- NOTE: ig_results.json not yet on Mac — user needs to save followers/following data locally first OR unfollow.py can read from sheet

## Cookie Rotation — COMPLETE (Jul 12 2026)
- First rotation due: ~Aug 1 2026 (20 days from Jul 12)
- Cookie Rotation tab pre-filled in TURRO sheet
- Auto-rotation script: `~/Instagrammer/cookie_rotation.py`
- Mac launchd setup: `~/Instagrammer/setup_rotation_cron.sh`
- **TO ACTIVATE:** `bash setup_rotation_cron.sh` from repo dir on Mac

## TURRO Sheet Tabs (current state Jul 13 2026)
| Tab | Purpose |
|-----|---------|
| Burner Pool | 10 burners + master, cookie status, validated dates |
| Task Log | Setup checklist (Steps 1–5, all DONE) |
| Crawl Output | Schema: timestamp, seed_account, burner_used, target_username, full_name, follower_count, following_count, is_private, is_verified, bio, post_count, profile_url, crawl_depth, status |
| Cookie Rotation | All 11 accounts, rotation_due dates (20-day cycle), last_status, checkpoint_required |
| Cred | Active 10 burners + master with password + full cookie JSON |
| TANZIM | tanzim.ozer followers/following/non-followers lists |

## Mac Listener (Step 5)
- **Port 5055** — `~/Desktop/Friday/TURRO/listener.py` (Flask, Python venv)
- Routes: `GET /health` | `POST /read` (control_secret: `turro-secret-2026`)
- Start: `cd ~/Desktop/Friday/TURRO && source venv/bin/activate && python3 listener.py`
- **Terminal window must stay open** — no launchd yet
- Internal IP: `10.217.135.195:5055`

## IG Cookie Device-Fingerprint Binding — Critical
Cookies from Brave on Mac are bound to that device. Replaying from VM → TooManyRedirects or useragent mismatch.
**For ALL authenticated IG reads: script must run on Mac.**
Delivery: Python heredoc the user pastes into Terminal. Results saved to `~/Desktop/Friday/TURRO/ig_results.json`.

**DevTools console alternative:**
- Type `allow pasting` first, Enter, THEN paste the fetch() snippet
- Must be on instagram.com tab
- Bare fetch('/api/v1/accounts/current_user/?edit=true') returns 400 even logged in — IG's web endpoints are picky about request context

## Relevant Sheets
- **Project Turro**: `1ZmyV2nBq5uoql7WD9hxr7q6nM1ofT8nyJ8Q1C45Z4pc`
- **Instagrammer (IG Creds tab)**: `1NVaI-jXqfS1z6aMLvNlwJCZoSzVMzP-17to24kKMcDA`
- **All IG Handles of TIMBR**: `13xzp7uOywfoktfTfAaBdBx16TD2d4qi2CtFar6bAKfU`

## Google Sheets ops this session (Jul 13)
- Text wrap + middle + centre align applied to ALL 14 tabs of Instagrammer sheet in one batchUpdate
- Method: iterate `meta['sheets']`, build one `repeatCell` request per sheetId with wrapStrategy=WRAP + verticalAlignment=MIDDLE + horizontalAlignment=CENTER
- TANZIM tab written via `values().update()` to range `TANZIM!A1` with header row + data

## Git Commits (Jul 12 2026)
Repo: `github.com/tanzimozer/Instagrammer` (private)
- `80b1a4c` — credentials.json: 48 IG accounts
- `f45d675` — turro_sheet_snapshot.json + timbr_credentials.json
- `6ddeb79` — cookie_rotation.py + setup_rotation_cron.sh
