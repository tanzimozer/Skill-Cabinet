# Sheets: create a tab + format it (full recipe)

Token: `~/.hermes/google_token.json` (live). Build `sheets`/`drive` v4/v3 with
`Credentials.from_authorized_user_file(...)`, refresh if `creds.expired`.

## Inspect first
```python
meta = svc.spreadsheets().get(spreadsheetId=SHEET_ID).execute()
print(meta["properties"]["title"])
for s in meta["sheets"]:
    print(s["properties"]["title"], s["properties"]["sheetId"])
```
Confirm you're in the right file before touching it. A bare share link
(`/spreadsheets/d/<ID>/edit#gid=<gid>`) gives the file ID in the path; the `gid`
is a *tab* id, not the file.

## Add a tab
```python
add = svc.spreadsheets().batchUpdate(spreadsheetId=SHEET_ID, body={"requests":[
    {"addSheet":{"properties":{"title":"IG Creds",
        "gridProperties":{"rowCount":50,"columnCount":4}}}}]}).execute()
new_id = add["replies"][0]["addSheet"]["properties"]["sheetId"]  # numeric sheetId for later formatting
```

## Write header + rows
```python
rows = [["Username","Password","Notes"]] + [[h,"",""] for h in handles]
svc.spreadsheets().values().update(spreadsheetId=SHEET_ID, range="IG Creds!A1",
    valueInputOption="RAW", body={"values":rows}).execute()
```

## Format header (bold + fill + freeze) and widen columns
```python
svc.spreadsheets().batchUpdate(spreadsheetId=SHEET_ID, body={"requests":[
  {"repeatCell":{"range":{"sheetId":new_id,"startRowIndex":0,"endRowIndex":1},
    "cell":{"userEnteredFormat":{"textFormat":{"bold":True},
      "backgroundColor":{"red":0.85,"green":0.92,"blue":0.83}}},
    "fields":"userEnteredFormat(textFormat,backgroundColor)"}},
  {"updateSheetProperties":{"properties":{"sheetId":new_id,
    "gridProperties":{"frozenRowCount":1}},"fields":"gridProperties.frozenRowCount"}},
  {"updateDimensionProperties":{"range":{"sheetId":new_id,"dimension":"COLUMNS",
    "startIndex":0,"endIndex":1},"properties":{"pixelSize":220},"fields":"pixelSize"}},
]}).execute()
```

## Wrap + vertical-middle + horizontal-center the WHOLE tab
`repeatCell` with a `range` that is just `{"sheetId": id}` (no row/col bounds)
applies to every cell in the tab — the right way to do "format the whole tab".
```python
svc.spreadsheets().batchUpdate(spreadsheetId=SHEET_ID, body={"requests":[
  {"repeatCell":{"range":{"sheetId":TAB_ID},
    "cell":{"userEnteredFormat":{"wrapStrategy":"WRAP",
      "verticalAlignment":"MIDDLE","horizontalAlignment":"CENTER"}},
    "fields":"userEnteredFormat(wrapStrategy,verticalAlignment,horizontalAlignment)"}}]}).execute()
```
Field names: `wrapStrategy=WRAP`, `verticalAlignment=MIDDLE`, `horizontalAlignment=CENTER`.

## Rename the whole spreadsheet (file title, not a tab)
"Rename this sheet to X" usually means the file. Echo the interpretation, then:
```python
svc.spreadsheets().batchUpdate(spreadsheetId=SHEET_ID, body={"requests":[
  {"updateSpreadsheetProperties":{"properties":{"title":"Instagrammer"},"fields":"title"}}]}).execute()
```
To rename a *tab* instead, use `updateSheetProperties` with `properties.title` + `fields:"title"`.

## Share with a person (Drive)
```python
drive.permissions().create(fileId=SHEET_ID,
  body={"type":"user","role":"writer","emailAddress":"someone@gmail.com"},
  sendNotificationEmail=True, fields="id,emailAddress,role").execute()
```
role: `writer` (editor), `reader` (viewer), `commenter`.
