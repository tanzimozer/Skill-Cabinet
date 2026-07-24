# iCloud Mail — Integration Patterns (June 2026)

## Connection
- **Protocol:** IMAP SSL, `imap.mail.me.com:993`
- **Auth:** App-specific password (NOT Apple ID password)
- **Credentials:** `~/.hermes/icloud_creds.json`
- **Account:** `tanzimx@icloud.com`

```python
import imaplib, json, os
creds = json.load(open(os.path.expanduser('~/.hermes/icloud_creds.json')))
mail = imaplib.IMAP4_SSL(creds['imap_server'], creds['imap_port'])
mail.login(creds['email'], creds['app_password'])
```

## Folder Structure (Tanzim's iCloud)
```
INBOX                   — Primary inbox
Maureen Searle          — Dedicated folder for Maureen Searle correspondence
Archive
Documents/Lease
Documents/Westdale
USCIS
idctan                  — Secondary inbox (marketing/subscriptions land here)
SIXT.
Appointments
Robinhood
IDC-TAN
TAN-BIZ / Tan Biz
Junk
Sent Messages
Deleted Messages
Drafts
Notes
```

**Note:** `idctan` folder accumulates huge volumes of marketing email. When scanning for actionable items, scan `INBOX` + specific folders (Maureen Searle, TAN-BIZ) — don't scan `idctan` for urgent items.

## Key Contacts
- **Maureen Searle** (`alex4sea1@gmail.com`) — Important long-running correspondent. 94+ threads going back to June 2025. Topics: AI in healthcare, fitness/longevity, Timbr business model, general world affairs. Has her own dedicated folder. Check BOTH `Maureen Searle` folder AND `INBOX` — newer threads land in INBOX.

## Email Classification Rules (Tanzim)

### Actionable (flag, report to Tanzim)
- Direct personal correspondence requiring reply
- Financial statements / payment notices (Merrick Bank)
- Parking appeals / legal notices
- Job application responses (phone screens, interviews, rejections)
- Recruiter outreach

### Noise (delete on request)
- Marketing/promotional emails (Banana Republic, Pottery Barn, Starbucks Rewards, etc.)
- "Thank you for applying" auto-confirmations
- Nextdoor newsletters
- Retail sale alerts

## Scanning Strategy
When asked to scan for "emails needing reply":
1. Use `UNSEEN` flag to find unread only — faster than scanning ALL
2. Scan `INBOX` + `Maureen Searle` + `TAN-BIZ` folders
3. Skip `idctan`, `Junk` for actionable items
4. For Maureen specifically: search both `INBOX` and `Maureen Searle` folder with `SINCE 1-May-2026`
5. Filter senders: skip `noreply`, `no-reply`, `newsletter`, `notification`, `alerts`, `promo`

## Large Folder Timeout
Scanning ALL emails across ALL folders times out at 300s. Solution:
- Use `UNSEEN` filter — reduces scope dramatically
- Limit per-folder fetch to last 50 message IDs
- Use `BODY.PEEK[HEADER.FIELDS ...]` not full `BODY.PEEK[]` for initial scan
- Only fetch full body for actionable messages

## Email Separation Rules
**CRITICAL — never mix these in reports to Tanzim:**
- `tanzimx@icloud.com` = **iCloud (personal)**
- `tanzim.ozer@gmail.com` = **Gmail (personal/job search)**
- Timbr work Gmail = coming later

Report them separately. If asked about iCloud specifically, only report iCloud results.

## Deleting Noise
When Tanzim says "delete them" after seeing a list:
```python
# Move to Deleted Messages (soft delete)
mail.select('INBOX')
# Search for the noise pattern
status, msgs = mail.search(None, 'FROM', '"noreply@"')
for msg_id in msgs[0].split():
    mail.store(msg_id, '+FLAGS', '\\Deleted')
mail.expunge()
```
Or use Gmail API (for Gmail) with `trash` action — preserves 30-day recovery window.
