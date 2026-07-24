"""
Reusable block-based Google Sheets tab builder for Tanzim's formatting standard.

Feed it a list of block tuples; it writes values AND applies formatting
(title banner, section bands, table headers, alignment-by-content-type,
column widths, hidden gridlines).

Block types:
  ('title', text)            -> dark merged banner, white bold centered
  ('sub',   text)            -> italic merged subtitle, left
  ('section', text)          -> grey bold band, merged
  ('p',     text)            -> prose paragraph, merged across, LEFT
  ('bul',   [items])         -> bullet list, each merged across, LEFT
  ('kv',    [h0,h1], [(k,v)])-> two-col table: key centered/bold, value merged-left
  ('tbl',   [cols], [rows])  -> table: header band + body rows

Usage:
  svc = <authorized sheets v4 service>   # see SKILL.md auth boilerplate
  build_tab(svc, SPREADSHEET_ID, 'Tab Name', blocks)

Watch the 60-writes/min quota when building many tabs (see SKILL.md).
"""
NCOLS = 6  # A..F; widen the list below if you need more columns

def build_tab(svc, SID, title, blocks, col_widths=(150, 520, 170, 170, 170, 170)):
    meta = svc.spreadsheets().get(spreadsheetId=SID).execute()
    existing = {s['properties']['title']: s['properties']['sheetId'] for s in meta['sheets']}
    if title in existing:
        sid = existing[title]
        svc.spreadsheets().values().clear(spreadsheetId=SID, range=f"'{title}'").execute()
        svc.spreadsheets().batchUpdate(spreadsheetId=SID, body={'requests': [
            {'updateCells': {'range': {'sheetId': sid}, 'fields': 'userEnteredFormat'}}]}).execute()
    else:
        res = svc.spreadsheets().batchUpdate(spreadsheetId=SID, body={'requests': [
            {'addSheet': {'properties': {'title': title,
             'gridProperties': {'rowCount': 200, 'columnCount': NCOLS}}}}]}).execute()
        sid = res['replies'][0]['addSheet']['properties']['sheetId']

    rows = []; fmts = []
    def add(vals): rows.append(list(vals) + [''] * (NCOLS - len(vals)))
    r = 0
    for b in blocks:
        kind = b[0]
        if kind == 'title':
            add([b[1]]); fmts.append((r, r + 1, 'title')); r += 1
        elif kind == 'sub':
            add([b[1]]); fmts.append((r, r + 1, 'sub')); r += 1
            add(['']); r += 1
        elif kind == 'section':
            add([b[1]]); fmts.append((r, r + 1, 'section')); r += 1
        elif kind == 'p':
            add([b[1]]); fmts.append((r, r + 1, 'prose')); r += 1
        elif kind == 'bul':
            for item in b[1]:
                add(['\u2022  ' + item]); fmts.append((r, r + 1, 'prose')); r += 1
        elif kind == 'kv':
            hdr, data = b[1], b[2]
            add([hdr[0], hdr[1]]); fmts.append((r, r + 1, 'thead2')); r += 1
            for k, v in data:
                add([k, v]); fmts.append((r, r + 1, 'krow')); r += 1
        elif kind == 'tbl':
            cols, data = b[1], b[2]
            add(list(cols)); fmts.append((r, r + 1, 'thead')); r += 1
            for row in data:
                add(list(row)); fmts.append((r, r + 1, 'trow')); r += 1
        add(['']); r += 1  # spacer

    svc.spreadsheets().values().update(spreadsheetId=SID, range=f"'{title}'!A1",
        valueInputOption='RAW', body={'values': rows}).execute()

    DARK = {'red': 0.17, 'green': 0.24, 'blue': 0.31}
    HEAD = {'red': 0.20, 'green': 0.29, 'blue': 0.37}
    SECT = {'red': 0.85, 'green': 0.89, 'blue': 0.93}
    WHITE = {'red': 1, 'green': 1, 'blue': 1}
    def rng(r0, r1, c0, c1):
        return {'sheetId': sid, 'startRowIndex': r0, 'endRowIndex': r1,
                'startColumnIndex': c0, 'endColumnIndex': c1}
    reqs = []
    # base: wrap, middle, LEFT (not center), font 10
    reqs.append({'repeatCell': {'range': {'sheetId': sid}, 'cell': {'userEnteredFormat': {
        'wrapStrategy': 'WRAP', 'verticalAlignment': 'MIDDLE',
        'horizontalAlignment': 'LEFT', 'textFormat': {'fontSize': 10}}},
        'fields': 'userEnteredFormat(wrapStrategy,verticalAlignment,horizontalAlignment,textFormat)'}})
    for i, w in enumerate(col_widths[:NCOLS]):
        reqs.append({'updateDimensionProperties': {'range': {'sheetId': sid, 'dimension': 'COLUMNS',
            'startIndex': i, 'endIndex': i + 1}, 'properties': {'pixelSize': w}, 'fields': 'pixelSize'}})
    for (r0, r1, kind) in fmts:
        if kind == 'title':
            reqs.append({'mergeCells': {'range': rng(r0, r1, 0, NCOLS), 'mergeType': 'MERGE_ALL'}})
            reqs.append({'repeatCell': {'range': rng(r0, r1, 0, NCOLS), 'cell': {'userEnteredFormat': {
                'backgroundColor': DARK, 'horizontalAlignment': 'CENTER',
                'textFormat': {'bold': True, 'fontSize': 15, 'foregroundColor': WHITE}}},
                'fields': 'userEnteredFormat(backgroundColor,horizontalAlignment,textFormat)'}})
        elif kind == 'sub':
            reqs.append({'mergeCells': {'range': rng(r0, r1, 0, NCOLS), 'mergeType': 'MERGE_ALL'}})
            reqs.append({'repeatCell': {'range': rng(r0, r1, 0, NCOLS), 'cell': {'userEnteredFormat': {
                'horizontalAlignment': 'LEFT', 'textFormat': {'italic': True, 'fontSize': 10}}},
                'fields': 'userEnteredFormat(horizontalAlignment,textFormat)'}})
        elif kind == 'section':
            reqs.append({'mergeCells': {'range': rng(r0, r1, 0, NCOLS), 'mergeType': 'MERGE_ALL'}})
            reqs.append({'repeatCell': {'range': rng(r0, r1, 0, NCOLS), 'cell': {'userEnteredFormat': {
                'backgroundColor': SECT, 'textFormat': {'bold': True, 'fontSize': 11}}},
                'fields': 'userEnteredFormat(backgroundColor,textFormat)'}})
        elif kind == 'prose':
            reqs.append({'mergeCells': {'range': rng(r0, r1, 0, NCOLS), 'mergeType': 'MERGE_ALL'}})
        elif kind == 'thead2':
            reqs.append({'repeatCell': {'range': rng(r0, r1, 0, 1), 'cell': {'userEnteredFormat': {
                'backgroundColor': HEAD, 'horizontalAlignment': 'CENTER',
                'textFormat': {'bold': True, 'foregroundColor': WHITE}}},
                'fields': 'userEnteredFormat(backgroundColor,horizontalAlignment,textFormat)'}})
            reqs.append({'mergeCells': {'range': rng(r0, r1, 1, NCOLS), 'mergeType': 'MERGE_ALL'}})
            reqs.append({'repeatCell': {'range': rng(r0, r1, 1, NCOLS), 'cell': {'userEnteredFormat': {
                'backgroundColor': HEAD, 'textFormat': {'bold': True, 'foregroundColor': WHITE}}},
                'fields': 'userEnteredFormat(backgroundColor,textFormat)'}})
        elif kind == 'krow':
            reqs.append({'repeatCell': {'range': rng(r0, r1, 0, 1), 'cell': {'userEnteredFormat': {
                'horizontalAlignment': 'CENTER', 'textFormat': {'bold': True}}},
                'fields': 'userEnteredFormat(horizontalAlignment,textFormat)'}})
            reqs.append({'mergeCells': {'range': rng(r0, r1, 1, NCOLS), 'mergeType': 'MERGE_ALL'}})
        elif kind == 'thead':
            reqs.append({'repeatCell': {'range': rng(r0, r1, 0, NCOLS), 'cell': {'userEnteredFormat': {
                'backgroundColor': HEAD, 'horizontalAlignment': 'CENTER',
                'textFormat': {'bold': True, 'foregroundColor': WHITE}}},
                'fields': 'userEnteredFormat(backgroundColor,horizontalAlignment,textFormat)'}})
        # 'trow' bodies keep base left-align; center specific data columns yourself if needed
    reqs.append({'updateSheetProperties': {'properties': {'sheetId': sid,
        'gridProperties': {'hideGridlines': True}}, 'fields': 'gridProperties.hideGridlines'}})
    svc.spreadsheets().batchUpdate(spreadsheetId=SID, body={'requests': reqs}).execute()
    return sid
