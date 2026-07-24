"""
Google Sheets / Gmail API — standard auth boilerplate for TIMBR and all Tanzim Google tasks.
Copy and modify. Run from /home/hermes/ (not /tmp/).
"""
import json
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

def get_creds():
    with open('/home/hermes/.hermes/google_token.json') as f:
        t = json.load(f)
    return Credentials(
        token=t.get('token'),
        refresh_token=t.get('refresh_token'),
        token_uri=t.get('token_uri', 'https://oauth2.googleapis.com/token'),
        client_id=t.get('client_id'),
        client_secret=t.get('client_secret'),
        scopes=t.get('scopes')
    )

def sheets_service():
    return build('sheets', 'v4', credentials=get_creds())

def gmail_service():
    return build('gmail', 'v1', credentials=get_creds())

# ── SHEETS QUICK HELPERS ──

def read_tab(svc, sheet_id, tab_name):
    result = svc.spreadsheets().values().get(
        spreadsheetId=sheet_id, range=tab_name
    ).execute()
    return result.get('values', [])

def clear_and_write(svc, sheet_id, tab_name, rows):
    """rows = [header_row, data_row, ...]"""
    svc.spreadsheets().values().clear(
        spreadsheetId=sheet_id, range=tab_name
    ).execute()
    svc.spreadsheets().values().update(
        spreadsheetId=sheet_id,
        range=f'{tab_name}!A1',
        valueInputOption='RAW',
        body={'values': rows}
    ).execute()

def append_rows(svc, sheet_id, tab_name, rows):
    existing = read_tab(svc, sheet_id, tab_name)
    next_row = len(existing) + 1
    svc.spreadsheets().values().append(
        spreadsheetId=sheet_id,
        range=f'{tab_name}!A{next_row}',
        valueInputOption='RAW',
        insertDataOption='INSERT_ROWS',
        body={'values': rows}
    ).execute()

def format_header(svc, sheet_id, sheet_gid, num_cols,
                  bg=(0.08, 0.08, 0.25)):
    r, g, b = bg
    requests = [
        {
            "repeatCell": {
                "range": {"sheetId": sheet_gid, "startRowIndex": 0, "endRowIndex": 1},
                "cell": {
                    "userEnteredFormat": {
                        "textFormat": {"bold": True,
                                       "foregroundColor": {"red":1,"green":1,"blue":1},
                                       "fontSize": 11},
                        "backgroundColor": {"red": r, "green": g, "blue": b},
                        "horizontalAlignment": "CENTER"
                    }
                },
                "fields": "userEnteredFormat(textFormat,backgroundColor,horizontalAlignment)"
            }
        },
        {
            "updateSheetProperties": {
                "properties": {"sheetId": sheet_gid,
                               "gridProperties": {"frozenRowCount": 1}},
                "fields": "gridProperties.frozenRowCount"
            }
        },
        {
            "autoResizeDimensions": {
                "dimensions": {"sheetId": sheet_gid,
                               "dimension": "COLUMNS",
                               "startIndex": 0,
                               "endIndex": num_cols}
            }
        }
    ]
    svc.spreadsheets().batchUpdate(
        spreadsheetId=sheet_id, body={"requests": requests}
    ).execute()

# ── GMAIL QUICK HELPERS ──

def search_gmail(svc, query, max_results=20):
    result = svc.users().messages().list(
        userId='me', q=query, maxResults=max_results
    ).execute()
    return result.get('messages', [])

def get_email(svc, msg_id):
    return svc.users().messages().get(
        userId='me', id=msg_id, format='full'
    ).execute()
