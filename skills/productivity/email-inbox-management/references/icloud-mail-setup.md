# iCloud Mail — Setup & Connection

## Credentials location
`~/.hermes/icloud_creds.json`

```json
{
  "email": "tanzimx@icloud.com",
  "app_password": "pxvf-ipel-jsiy-fmuh",
  "imap_server": "imap.mail.me.com",
  "imap_port": 993
}
```

## How to generate a new app-specific password (if needed)
1. Go to **appleid.apple.com** → Sign in
2. **Sign-In and Security** → **App-Specific Passwords**
3. Generate one — name it "Hermes" or "Friday"
4. Copy the 16-character password (format: xxxx-xxxx-xxxx-xxxx)
5. Update `~/.hermes/icloud_creds.json`

Apple's IMAP supports app-specific passwords — main Apple ID password is never used.

## Why iCloud uses IMAP not API
Apple has no OAuth API for personal iCloud Mail. Options:
- **IMAP** ✅ — works, secure with app-specific passwords
- **iCloud.com browser automation** ❌ — fragile, Apple blocks it
- **Local iCloud Drive sync** ❌ — requires Mac with iCloud Drive synced (not available on VM)

## IMAP connection
```python
import imaplib, json

with open('/home/hermes/.hermes/icloud_creds.json') as f:
    creds = json.load(f)

mail = imaplib.IMAP4_SSL(creds['imap_server'], creds['imap_port'])
mail.login(creds['email'], creds['app_password'])
```

## Confirmed working
Connected June 2, 2026. Inbox: 361 emails, 9 unread at time of connection.

## iCloud vs Gmail — separation rule
**NEVER mix iCloud and Gmail results in the same report.**
- `tanzimx@icloud.com` = iCloud = personal
- `tanzim.ozer@gmail.com` = Gmail = also personal
- Timbr work Gmail = coming later (not connected yet)
Report each account separately when Tanzim asks about email.
