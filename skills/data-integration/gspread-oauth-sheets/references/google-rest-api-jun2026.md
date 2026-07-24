# Google REST API recipes (raw urllib, no gspread) — Jun 2026

Token: `~/.hermes/google_token.json`. Use the `refresh()` + `api()` helpers from SKILL.md.
All scopes (Sheets, Drive, Docs, Gmail send/modify/readonly, Calendar, Contacts) are already on the token.

## Create a sheet with header formatting + frozen row + column widths

```python
title="Friday 3.0 Changes — 2026-06-18"
sh=api('https://sheets.googleapis.com/v4/spreadsheets','POST',{'properties':{'title':title}})
sid=sh['spreadsheetId']; url=sh['spreadsheetUrl']

vals=[['Date','Component','Change','Detail','Status'],
      ['2026-06-18','...','...','...','Live']]
api(f'https://sheets.googleapis.com/v4/spreadsheets/{sid}/values/{urllib.parse.quote("Sheet1!A1")}?valueInputOption=RAW',
    'PUT',{'values':vals})

api(f'https://sheets.googleapis.com/v4/spreadsheets/{sid}:batchUpdate','POST',{'requests':[
 {'repeatCell':{'range':{'sheetId':0,'startRowIndex':0,'endRowIndex':1},
   'cell':{'userEnteredFormat':{'textFormat':{'bold':True},
       'backgroundColor':{'red':0.85,'green':0.69,'blue':0.27}}},
   'fields':'userEnteredFormat(textFormat,backgroundColor)'}},
 {'updateSheetProperties':{'properties':{'sheetId':0,'gridProperties':{'frozenRowCount':1}},
   'fields':'gridProperties.frozenRowCount'}},
 {'updateDimensionProperties':{'range':{'sheetId':0,'dimension':'COLUMNS','startIndex':2,'endIndex':4},
   'properties':{'pixelSize':380},'fields':'pixelSize'}},
]})
```

## Append a single log row to an existing sheet (running ledger pattern)
```python
row=[['2026-06-18','Component','Change','Detail','Live']]
api(f'https://sheets.googleapis.com/v4/spreadsheets/{sid}/values/{urllib.parse.quote("Sheet1!A1")}:append?valueInputOption=RAW',
    'POST',{'values':row})
```

## List all spreadsheets, newest first
```python
params=urllib.parse.urlencode({
    'q':"mimeType='application/vnd.google-apps.spreadsheet' and trashed=false",
    'fields':'files(id,name,modifiedTime)','pageSize':50,'orderBy':'modifiedTime desc'})
res=api(f'https://www.googleapis.com/drive/v3/files?{params}')
```
NOTE: `orderBy:'modifiedTime desc'` MUST go through urlencode — the space breaks a hand-built URL.

## Inspect a spreadsheet's tabs (titles, sheetId/gid, row counts)
```python
m=api(f'https://sheets.googleapis.com/v4/spreadsheets/{sid}?fields=sheets(properties(title,sheetId,gridProperties(rowCount)))')
for s in m['sheets']:
    p=s['properties']; print(p['title'], p['sheetId'], p['gridProperties'].get('rowCount'))
```
Finding a tab by its known gid across many files: loop files, fetch this fields mask, compare `sheetId`.

## Create a Google Doc with TITLE + HEADING_2 sections
Docs API quirk: you insert ALL text first at index 1, THEN apply paragraph styles by character offset.
Because insertion shifts indices, compute offsets from the source string (`text.index(sub)+1`, the +1 is the doc's implicit start).
```python
doc=api('https://docs.googleapis.com/v1/documents','POST',{'title':'My Doc'})
did=doc['documentId']
api(f'https://docs.googleapis.com/v1/documents/{did}:batchUpdate','POST',
    {'requests':[{'insertText':{'location':{'index':1},'text':text}}]})
# then style: updateParagraphStyle namedStyleType TITLE/HEADING_2, updateTextStyle bold, by computed ranges
```

## Read a Google Doc as plain text
```python
d=api(f'https://docs.googleapis.com/v1/documents/{did}')
def text(el):
    out=''
    for c in el.get('content',[]):
        p=c.get('paragraph')
        if p:
            for e in p.get('elements',[]):
                tr=e.get('textRun')
                if tr: out+=tr.get('content','')
    return out
print(text(d.get('body',{})))
```

## Gmail search + read body
```python
q=urllib.parse.quote('HousingWire OR "Housing Wire"')
res=api(f'https://gmail.googleapis.com/gmail/v1/users/me/messages?q={q}&maxResults=20')
# per message: format=metadata&metadataHeaders=From&metadataHeaders=Subject&metadataHeaders=Date for headers,
# or format=full then base64.urlsafe_b64decode the text/plain or text/html part. HTML: strip tags + html.unescape.
```
Useful Gmail query operators: `-in:trash`, `newer_than:120d`, `OR`, quoted phrases.

## Make a file link-public (no request, no sign-in)
```python
api(f'https://www.googleapis.com/drive/v3/files/{did}/permissions?supportsAllDrives=true',
    'POST',{'role':'reader','type':'anyone'})
```
Result permission id is `anyoneWithLink`, `allowFileDiscovery:false` — view-only, owner keeps edit.
