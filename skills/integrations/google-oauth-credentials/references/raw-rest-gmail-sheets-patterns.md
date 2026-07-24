# Raw REST patterns for Gmail + Sheets (no gspread, no google-api-client)

When you just need to read mail or sheet values, you don't need any Google
client libraries — the token file plus stdlib `urllib` is enough and avoids
dependency/version friction. Verified working Jun 2026 against
`~/.hermes/google_token.json`.

## Token refresh (stdlib only)
The token file already carries `client_id`, `client_secret`, `refresh_token`.
Refresh in-place and reuse the access token across calls:

```python
import json, urllib.request, urllib.parse, os
TOKEN_PATH = os.path.expanduser('~/.hermes/google_token.json')

def refresh():
    with open(TOKEN_PATH) as f: tok = json.load(f)
    data = urllib.parse.urlencode({
        'client_id': tok['client_id'], 'client_secret': tok['client_secret'],
        'refresh_token': tok['refresh_token'], 'grant_type': 'refresh_token'}).encode()
    r = json.loads(urllib.request.urlopen(urllib.request.Request(
        'https://oauth2.googleapis.com/token', data=data, method='POST')).read())
    tok['token'] = r['access_token']
    with open(TOKEN_PATH, 'w') as f: json.dump(tok, f)
    return r['access_token']

T = refresh()
def gapi(url):
    return json.loads(urllib.request.urlopen(urllib.request.Request(
        url, headers={'Authorization': f'Bearer {T}'})).read())
```

## CRITICAL gotcha: always urlencode query params
Building URLs by f-string with raw values throws
`http.client.InvalidURL: URL can't contain control characters` the moment a
value has a space (e.g. `orderBy=modifiedTime desc`, or a `q=` with spaces).
**Always** build the query string with `urllib.parse.urlencode({...})`:

```python
params = urllib.parse.urlencode({
    'q': "mimeType='application/vnd.google-apps.spreadsheet' and trashed=false",
    'fields': 'files(id,name,modifiedTime)', 'pageSize': 50,
    'orderBy': 'modifiedTime desc'})
files = gapi(f'https://www.googleapis.com/drive/v3/files?{params}')['files']
```

## Gmail: search → read → decode body
```python
def gmail_search(q, n=100):
    out, pt = [], None
    while True:
        u = 'https://gmail.googleapis.com/gmail/v1/users/me/messages?' + \
            urllib.parse.urlencode({'q': q, 'maxResults': 100})
        if pt: u += f'&pageToken={pt}'
        r = gapi(u); out += r.get('messages', [])
        pt = r.get('nextPageToken')
        if not pt or len(out) >= n: break
    return out[:n]

# Fast metadata read (headers only — much cheaper than full)
def headers(mid):
    d = gapi(f"https://gmail.googleapis.com/gmail/v1/users/me/messages/{mid}"
             "?format=metadata&metadataHeaders=From&metadataHeaders=Subject&metadataHeaders=Date")
    return {h['name']: h['value'] for h in d['payload']['headers']}, d.get('labelIds', [])

# Full body — many emails are HTML-only, so strip tags as fallback
import base64, re, html
def body_text(mid):
    d = gapi(f"https://gmail.googleapis.com/gmail/v1/users/me/messages/{mid}?format=full")
    acc = []
    def walk(p):
        b = p.get('body', {}).get('data')
        if b: acc.append((p.get('mimeType',''), base64.urlsafe_b64decode(b).decode('utf-8','ignore')))
        for sp in p.get('parts', []) or []: walk(sp)
    walk(d['payload'])
    text = ''
    for mt, c in acc:
        if 'html' in mt: c = html.unescape(re.sub(r'<[^>]+>', ' ', c))
        text += c + '\n'
    return text
```
Query tips: scope with `-in:trash newer_than:120d` to avoid dredging old/archived
noise. `q='interview'` plus dedup-by-company gives a clean interview-pipeline list.

## Sheets: read values + enumerate tabs
```python
SID = '...'
# tab metadata (titles, sheetIds, row counts)
meta = gapi(f'https://sheets.googleapis.com/v4/spreadsheets/{SID}'
            '?fields=sheets(properties(title,sheetId,gridProperties(rowCount)))')

# values — A1 range must be url-quoted (tab names with spaces/symbols)
def rng(a1):
    return gapi(f'https://sheets.googleapis.com/v4/spreadsheets/{SID}/values/'
                f'{urllib.parse.quote(a1)}').get('values', [])
rows = rng("MASTER_TAB!A1:K1288")
hdr, data = rows[0], rows[1:]
ci = {h: i for i, h in enumerate(hdr)}
def col(r, name):
    i = ci.get(name); return r[i] if i is not None and i < len(r) else ''
```

## Cross-match workflow (Gmail email ↔ Sheet) — Tanzim job pipeline
The recurring ask "check the email then cross-match with the sheet for the total
list": the **source of truth for live interviews is the inbox, not the sheet.**
- MASTER_TAB (`12FTPE1jSvrzdBeQ5Sjwiv8ccNVEbw7tTWJNdtDkrLZ0`) tracks *applied*
  jobs with a `CALLBACK` column, but that column is often left unfilled — don't
  treat empty CALLBACK as "no interview".
- Career-Ops Tracker (`1iooOAvVOVpA8rg6QAx5L060XkfceWWCwPEf_rb-IN9Q`, Sheet1) is a
  *sourcing/scoring* list (Status = New/Priority only), NOT an interview tracker.
- There is **no live "Interviews" tab** in any current sheet (an old one was
  deleted). Build the interview list from Gmail `q='interview'`, dedup by company,
  and confirm each company exists in MASTER_TAB to distinguish real callbacks from
  cold applications.
