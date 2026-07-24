# IG Cookie-Connection Drive — cron-driven validate-and-wire loop (Jun 2026)

Pattern for the overnight/recurring task that turns pasted IG cookies into live
crawl-pool sessions. Used when a teammate (e.g. Towsif) pastes Cookie-Editor
exports into the "Instagrammer" Google Sheet and Friday connects them while
Tanzim sleeps. Driven by a repeating cron job (e.g. every 15m, times=4).

## The sheet
- Spreadsheet "Instagrammer", tab **IG Creds**, ID `1NVaI-jXqfS1z6aMLvNlwJCZoSzVMzP-17to24kKMcDA`, gid `801410514`.
- Columns: **A=Username, B=Password, C=Accessible (checkbox), D=Cookies**.
- Auth: `/home/hermes/.hermes/google_token.json` (spreadsheets+drive scope; refresh via SDK or raw POST).

## Each-run loop
1. Read `IG Creds!A1:D60`. Find rows where D (Cookies) is populated.
2. **Validate each cookie** (parse + structural check — see below).
3. For each valid cookie with C != TRUE → tick C TRUE. For malformed/expired → leave unticked, note for re-grab.
4. **Re-apply CLIP + 24px row height** to data rows so pastes don't balloon the sheet (see below).
5. Wire validated accounts into the engine crawl pool (see below). Back up config first.
6. Post status to WhatsApp group "Towsif's Desk": connected this run, failed validation (ask to re-grab), next 2–3 priority accounts still missing cookies.
7. On the **final run**, also post a consolidated overnight report for Tanzim — lead with numbers (total connected, total validated, failures, live-session count in pool).

## Cookie parsing (handles all formats Towsif pastes)
```python
def parse_cookie(raw):
    raw = raw.strip()
    try:
        data = json.loads(raw)
        if isinstance(data, list):   # Cookie-Editor JSON array of {name,value}
            return {c.get("name"): c.get("value") for c in data if isinstance(c, dict)}
        if isinstance(data, dict):
            return data
    except Exception:
        if ";" in raw:               # "name=value; name=value" header style
            return {p.split("=",1)[0].strip(): p.split("=",1)[1]
                    for p in raw.split(";") if "=" in p}
    return None
```

## Validation: STRUCTURAL is authoritative — NOT liveness
- **Valid = has `sessionid` AND (`csrftoken` OR `ds_user_id`).** That's the gate for ticking Accessible and wiring into the pool.
- **Do NOT gate connection on a live HTTP liveness probe.** Instagram blocks/garbles
  requests from datacenter/server IPs regardless of cookie validity. Confirmed Jun 2026:
  every structurally-valid cookie returned `302`/`400` on `/api/v1/accounts/current_user/`
  and `{"status":"fail","message":"...something went wrong..."}` on the mobile endpoint —
  even cookies known-good. The VM IP is the problem, not the cookie. Liveness from the VM
  is informational only; never let it un-tick or block a structurally-valid session.
- Real liveness is established later when the engine actually runs (often from a cleaner
  IP / real session context). Connection at this stage = structural validity, full stop.

## Wiring into the crawl pool (Instagrammer engine)
The engine reads cookies two ways (see `core/config.py` + `stages/crawl.py::_build_pool`):
- `secrets.ig_crawl_cookies_ref` → env `IG_CRAWL_COOKIES` (JSON list), OR
- `secrets.ig_crawl_cookie_dir` → **directory of per-account `<handle>.json` files** (preferred for incremental connect).

Default dir: `~/.hermes/instagrammer/crawl_cookies/`. To wire a validated account, drop
the **original cookie payload** (the JSON array, not the name→value dict) as `<handle>.json`:
```python
cdir = os.path.expanduser("~/.hermes/instagrammer/crawl_cookies")
os.makedirs(cdir, exist_ok=True)
json.dump(original_cookie_array, open(f"{cdir}/{handle}.json", "w"))
```
Back up `config/engine.config.yaml` first (timestamped `.bak-<UTC>`) even though appending
files doesn't touch it — keeps the "don't break existing config" guarantee. Pool target = 10
crawl accounts; FOLLOW account stays separate (`ig_follow_cookie_ref`), never mixed.

## Sheet hygiene — CLIP + 24px (prevents paste balloon)
```python
reqs = [
 {"repeatCell": {"range": {"sheetId": GID, "startRowIndex": 1, "endRowIndex": 60,
    "startColumnIndex": 3, "endColumnIndex": 4},
    "cell": {"userEnteredFormat": {"wrapStrategy": "CLIP"}},
    "fields": "userEnteredFormat.wrapStrategy"}},
 {"updateDimensionProperties": {"range": {"sheetId": GID, "dimension": "ROWS",
    "startIndex": 1, "endIndex": 60}, "properties": {"pixelSize": 24}, "fields": "pixelSize"}},
]
svc.spreadsheets().batchUpdate(spreadsheetId=SHEET_ID, body={"requests": reqs}).execute()
```

## Cron-run state & delivery
- Save run state to `~/.hermes/ig_cookie_task_state.json` (last_run_utc, run_index,
  connected_accounts, failed_validation, rows_with_cookies) so each run can diff "newly
  populated since last run."
- Find run index / total from the cron job entry in `~/.hermes/cron/jobs.json`
  (`repeat.completed` / `repeat.times`). On `completed == times-1` (the 4th of 4), emit the
  consolidated Tanzim report.
- The job's `deliver: origin` + `origin.chat_id` is the Towsif's Desk group — the scheduled
  job's final response is auto-delivered there. Do NOT call send_message yourself in a cron
  job; just produce the report as the final response. WhatsApp groups show as numeric IDs in
  `channel_directory.json`, so identify by the job's origin chat_id, not by name.

## Priority crawl set (original order, fill cookies in this order)
queen.anne.fitness, timbr.info, seattle.gym, slu.fitness, soulcycleseattle,
seattle.fitness.club, south.lake.union, bothell.fitness, seattlefitnessfood,
lakeunion.fitness, timbr.fit

## Autonomy boundary for this task
Task-level permission is pre-granted — tick checkboxes, wire cookies, format sheet, post
status without asking. Still gated (wait for Tanzim): spending money, changing account
passwords, deleting data, anything needing personal sign-off.

## Run 1/4 result (Jun 21 2026, baseline)
Connected 5: seattle.fitness.community, seattle.fitness.hub, seattle.fitness.events,
timbr.fit, timbr.us (all structurally valid, all ticked TRUE — timbr.us arrived mid-run).
Zero failed validation. Pool at 5/10. Next priorities still missing: queen.anne.fitness,
timbr.info, seattle.gym.
