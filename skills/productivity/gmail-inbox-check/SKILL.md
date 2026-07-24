---
name: gmail-inbox-check
description: "Scheduled Gmail intelligence check — scans inbox, cross-matches sent mail, identifies replied/pending/expired items, delivers a prioritised summary to Tanzim."
version: 1.0.0
tags: [Gmail, email, inbox, accountability, scheduled]
related_skills: [google-workspace]
---

# Gmail Inbox Check

Runs 3x daily (6 AM / 12 PM / 5 PM PDT). Each run does a full inbox scan, cross-matches sent mail, classifies threads, and sends a prioritised summary. Suppresses output if nothing actionable.

## When to use
- Load this skill when building or updating the Gmail check cron jobs
- Reference for the prompt structure and classification logic

## Setup requirement
Google Workspace OAuth token must be live at `~/.hermes/google_token.json`.
Check: `python ~/.hermes/skills/productivity/google-workspace/scripts/setup.py --check`

**Known token states:**
- `AUTHENTICATED` — good to go
- `REFRESH_FAILED: invalid_scope` — token was issued with wrong scopes; need full re-auth
- `AUTHENTICATED (partial)` — token valid but missing one scope (e.g. `documents.readonly`); Gmail checks still work fine, Docs read will fail. Not worth re-auth unless Docs access is needed.

**GAPI path fix:** The `GAPI=` shorthand using `~` in path fails when called as a shell variable — use the expanded path directly:
```bash
python ~/.hermes/skills/productivity/google-workspace/scripts/google_api.py gmail search "in:inbox newer_than:7d" --max 50
```
Do NOT use `$GAPI` with `~` in the path — it resolves to `python: can't open file '/home/hermes/~/.hermes/...'`.

## GAPI shorthand
```bash
# IMPORTANT: Use $HOME or absolute path, NOT ~ — tilde does not expand in cron prompts
GAPI="python /home/hermes/.hermes/skills/productivity/google-workspace/scripts/google_api.py"
# Equivalently:
GAPI="python $HOME/.hermes/skills/productivity/google-workspace/scripts/google_api.py"
```

**Pitfall:** `GAPI="python ~/.hermes/..."` silently fails with "can't open file '/home/hermes/~/.hermes/...': No such file or directory" when the variable is expanded in cron or certain shell contexts. Always use `$HOME` or the full absolute path.



## Execution steps (in order)

### Step 1 — Inbox scan
```bash
$GAPI gmail search "in:inbox newer_than:7d" --max 50
```
Captures all inbox threads in the last 7 days. Note `id`, `threadId`, `from`, `subject`, `date`, `snippet`.

### Step 2 — Sent scan
```bash
$GAPI gmail search "in:sent newer_than:7d" --max 30
```
Gets threads where Tanzim replied. Key field: `threadId`.

### Step 3 — Cross-match
Compare `threadId` between inbox and sent results:
- **Replied** = inbox `threadId` appears in sent results → already handled
- **Pending** = inbox `threadId` NOT in sent → needs action
- **Potentially expired** = pending + age >5 days + subject/snippet contains: `deadline`, `due`, `by [date]`, `respond by`, `expires`, `assessment`, `urgent`

### Step 4 — Classify pending items
For each pending thread, assess urgency from subject + snippet:
- 🔴 **Urgent** — interview, legal, financial, explicit deadline, background check
- 🟡 **Action needed** — recruiter follow-up, waiting on response, task required
- ⚪ **Skip** — newsletters, marketing, automated notifications, receipts

### Step 5 — Format and deliver

```
📬 [Morning/Midday/Evening] Inbox Check

🔴 URGENT (do today):
• [Sender/Company] — [Subject, 1 line] — [deadline if visible in snippet]

🟡 PENDING (needs action):
• [Sender/Company] — [Subject, 1 line]

✅ Replied: [N] threads
⚪ Skipped: [N] newsletters/automated
```

If nothing urgent or pending → output exactly `[SILENT]` to suppress delivery.

## Group chat behaviour — do NOT leak internal state
In group chats, never output internal reasoning, bracketed notes, or tool-progress commentary. The incident on May 31: a message like `[Group chat — Sagar's directing this at me, but Tanzim hasn't signed off...]` was sent to the TIMBR APP PRD group — internal reasoning leaked as a real message. Root cause: interim_assistant_messages was firing in group context before the gateway_notify_interval fix. Fix applied: `gateway_notify_interval: 0` in config. Lesson: internal commentary must NEVER appear as outbound WhatsApp messages, group or DM.

## Cron accountability job pitfall — static context hallucination

⚠️ The Daily Accountability cron (`30660ee62c1d`) has only `file` toolset access and static context. On May 26, 2026 it invented a "Housecall Pro interview at 12:30 PM with Precious Barton" that did not exist. Root cause: static context ("TIMBR and job search are priorities") with no live verification → model fills gaps with plausible-sounding specifics.

**Rule for ALL accountability/summary cron jobs:**
- If the job mentions specific upcoming events, it MUST have `web` or `file` access to verify (Gmail, Calendar, memory read)
- Without live data access, the prompt must explicitly say: *"Never fabricate specific meetings, names, deadlines, or appointments. If no verified specifics are available, keep items general."*
- Fixed prompt for `30660ee62c1d` was updated May 26, 2026 to include this instruction

## Stale Cron Reminder Audit Pattern

When Tanzim complains that reminders contain wrong/outdated info:
1. Pull the full job list via `schedule_task(action="list")` and read `/home/hermes/.hermes/cron/jobs.json` for full prompt content
2. Cross-check each reminder's task list against current known state (memory + hindsight)
3. Kill jobs that reference expired tasks (past deadlines, completed applications, past dates)
4. Patch jobs that have static context causing hallucination — add "Never fabricate specific meetings, names, or deadlines" to the prompt

**May 26, 2026 example:** 3 interview reminder jobs (`0ff7a3d00edf`, `d2afbb448c20`, `359043ea5b93`) were firing 3x daily with a task list from May 17 — IBM due May 20, State Farm, Kinnect, etc. All stale. Deleted all 3. Daily accountability job (`30660ee62c1d`) was also hallucinating specifics due to no live data source — patched prompt.

**Rule:** Before setting up any recurring reminder with a specific task list, confirm with Tanzim that the tasks are current. Hardcoded task lists in cron prompts rot fast.

## Group chat status message leak — FIXED

⚠️ The `gateway_notify_interval` config (default: 180s) fires "⏳ Still working..." heartbeat messages into **every** platform channel, including WhatsApp groups. This is unacceptable in group chats where other people can see internal agent status.

**Fix — set to 0 in `~/.hermes/config.yaml`:**
```yaml
agent:
  gateway_notify_interval: 0
```

Also ensure group interim messages are disabled:
```yaml
display:
  platforms:
    whatsapp:
      tool_progress: false
      interim_assistant_messages: false
      group_interim_messages: false
```

If a user complains about ⏳ messages in a group, apply both fixes immediately. The messages in-flight before the config change will still arrive — tell the user those are the last ones.

## Resolved: Internal reasoning leaked into WhatsApp group

On 2026-05-31, a message containing `[Group chat — Sagar's directing this at me, but Tanzim hasn't signed off...]` was visibly sent to the TIMBR APP PRD WhatsApp group. This was an internal reasoning note that should never have been delivered.

**Rule:** Internal reasoning, tool status, and deliberation text must NEVER appear in group chat deliveries. Keep group messages to clean, human-register outputs only.

## Google Drive folder listing — use native API, not GAPI script

The `google_api.py` drive subcommand only supports `search` with a freetext query. Listing files **by parent folder ID** requires the native Drive API:

```python
import json, sys
sys.path.insert(0, '/home/hermes/.hermes/hermes-agent/venv/lib/python3.11/site-packages')

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

with open('/home/hermes/.hermes/google_token.json') as f:
    token_data = json.load(f)

creds = Credentials(
    token=token_data.get('token'),
    refresh_token=token_data.get('refresh_token'),
    token_uri=token_data.get('token_uri', 'https://oauth2.googleapis.com/token'),
    client_id=token_data.get('client_id'),
    client_secret=token_data.get('client_secret'),
    scopes=token_data.get('scopes')
)
drive = build('drive', 'v3', credentials=creds)

results = drive.files().list(
    q=f"'{folder_id}' in parents",
    pageSize=200,
    fields="files(id, name, mimeType, modifiedTime, webViewLink, size)"
).execute()
files = results.get('files', [])
```

**DO NOT** try to pass `"'folder_id' in parents"` as a query string to `google_api.py drive search` — it returns HTTP 400 Invalid Value because the script wraps the query in `fullText contains`.

## WhatsApp Group ID discovery pattern

When Tanzim references a group by name but you only have numeric IDs, use this flow:
1. Tell Tanzim: "Ping me from that group and I'll log the ID"
2. His message will arrive with a group JID in the sender/chat context
3. Log the mapping: group name → JID in memory

Never guess group IDs from the `send_message list` output alone — names aren't shown, only IDs.

## ⚠️ Cron toolset pitfall — never include `browser` in Gmail cron jobs

Gmail cron jobs (`8b19da12`, `2eefd5d0`) had `browser` in their `enabled_toolsets`. On May 31 2026, after a VM restart, the browser/Puppeteer service was unavailable — both jobs failed with "Browser tooling is fully unresponsive". The Gmail API works entirely without a browser.

**Rule:** Gmail check/cleanup/sweep crons must ONLY use `["terminal", "file"]` toolsets. Never add `browser`, `web`, or `whatsapp` to Gmail API crons — they don't need them and they will fail when the browser session is unavailable.

Fix applied May 31: updated both jobs via `schedule_task(action="update", enabled_toolsets=["terminal", "file"])`.

## Cron GAPI path pitfall
⚠️ In cron job prompts, define the GAPI path using the full absolute path, not a shell variable with `~`:
```bash
# WRONG in cron prompts — ~ doesn't expand in double-quoted strings
GAPI="python ~/.hermes/skills/..."

# CORRECT — use $HOME or full path
GAPI="python $HOME/.hermes/skills/productivity/google-workspace/scripts/google_api.py"
# OR invoke directly:
python /home/hermes/.hermes/skills/productivity/google-workspace/scripts/google_api.py gmail search ...
```

## Static-context cron hallucination pitfall
⚠️ Cron prompts with only static context (no live data tool access) will hallucinate specific tasks, names, and deadlines. The Daily Accountability job (`30660ee62c1d`) learned this the hard way — invented a "Housecall Pro interview at 12:30 PM with Precious Barton" that didn't exist.

**Rule:** If a cron job mentions specific upcoming events, it MUST have tool access to verify them (Gmail, Calendar, memory). Without it, keep items general ("TIMBR", "job search") and explicitly instruct the prompt to never fabricate specifics.
When Tanzim asks for a manual Gmail overview, pipe results to `/tmp/inbox.json` and `/tmp/sent.json`, then run a Python cross-match inline rather than trying to parse JSON in bash. The verified working pattern is the Thread Cross-Match Pattern below — use `execute_code` with the full inline Python block. Jobot messages and personal recruiter outreach should always be flagged 🔴 even if they don't contain classic urgent keywords — they're human-initiated and time-sensitive.
```bash
python ~/.hermes/skills/productivity/google-workspace/scripts/google_api.py gmail search "in:inbox newer_than:7d" --max 50 2>/dev/null > /tmp/inbox.json
python ~/.hermes/skills/productivity/google-workspace/scripts/google_api.py gmail search "in:sent newer_than:7d" --max 30 2>/dev/null > /tmp/sent.json
```
Then run a `python3 << 'EOF'` heredoc to cross-match threadIds, calculate age in days, and classify urgency. This is more reliable than shell pipelines for JSON manipulation.

## Output format for on-demand scans
When Tanzim asks for a full overview directly (not cron), use a richer format:
- Group by: 🔴 URGENT / 🟡 PENDING / ✅ Replied / ⚪ Skipped
- Include age in days for items >1 day old
- Include one-line snippet context per urgent item
- End with a plain-language callout of the 2–3 most time-sensitive items

## GAPI Shorthand — Path Issue

The `~` in `GAPI="python ~/.hermes/..."` does NOT expand inside Python when used as a shell variable. Use `$HOME` instead or expand the full path:

```bash
python $HOME/.hermes/skills/productivity/google-workspace/scripts/google_api.py gmail search "in:inbox" --max 50
```

Or hardcode:
```bash
python /home/hermes/.hermes/skills/productivity/google-workspace/scripts/google_api.py gmail search "in:inbox" --max 50
```

## Thread Cross-Match Pattern (verified working)

```python
import json, subprocess

inbox = json.loads(subprocess.run([
    'python', '/home/hermes/.hermes/skills/productivity/google-workspace/scripts/google_api.py',
    'gmail', 'search', 'in:inbox newer_than:7d', '--max', '50'
], capture_output=True, text=True).stdout)

sent = json.loads(subprocess.run([
    'python', '/home/hermes/.hermes/skills/productivity/google-workspace/scripts/google_api.py',
    'gmail', 'search', 'in:sent newer_than:7d', '--max', '30'
], capture_output=True, text=True).stdout)

sent_thread_ids = {m['threadId'] for m in sent}
pending = [m for m in inbox if m['threadId'] not in sent_thread_ids]
replied = [m for m in inbox if m['threadId'] in sent_thread_ids]
```

## Rules / pitfalls
- Never fabricate deadlines not visible in subject or snippet
- Skip anything that's clearly automated (no-reply, donotreply, notifications@)
- Max 8 bullets total for cron delivery — surface only what matters
- One line per item in cron — no summaries, no padding
- If token is expired (`NOT_AUTHENTICATED` or `REFRESH_FAILED`), alert Tanzim: "⚠️ Gmail token expired — re-auth needed before inbox checks can run."
- `REFRESH_FAILED: invalid_scope` means the token is stale and needs a fresh OAuth flow — run `--auth-url` and walk Tanzim through re-auth (takes ~2 min, client secret already on VM)
- Token partial auth (`AUTHENTICATED (partial)`) is fine for Gmail operations — missing `documents.readonly` scope doesn't affect inbox checks
