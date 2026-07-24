---
name: populate-persona-qa-to-sheets
description: Populate persona Q&A responses to Google Sheets from chat messages
category: automation
---

# Populate Persona Q&A to Google Sheets

When you have persona interview responses from a group chat that need to be logged to a Google Sheet.

## When to use

- User shares screenshot/message of persona interview answers (Blair, Shumon, Taylor, etc.)
- Answers are in conversational format that need to be structured
- Target is a "Persona" tab on a Google Sheet

## Steps

1. **Extract Q&A pairs from the message/image**
   - Question number and full text
   - Full answer text (preserve Blair's voice — don't paraphrase)

2. **Load Google OAuth token** (JSON format at `~/.hermes/google_token.json`)
   ```python
   import json
   from google.oauth2.credentials import Credentials
   from google.auth.transport.requests import Request
   
   TOKEN_PATH = os.path.expanduser("~/.hermes/google_token.json")
   with open(TOKEN_PATH, 'r') as f:
       token_data = json.load(f)
   
   creds = Credentials(
       token=token_data.get('token'),
       refresh_token=token_data.get('refresh_token'),
       token_uri=token_data.get('token_uri'),
       client_id=token_data.get('client_id'),
       client_secret=token_data.get('client_secret'),
       scopes=token_data.get('scopes')
   )
   
   # Refresh if expired
   if creds.expired and creds.refresh_token:
       creds.refresh(Request())
   ```

3. **Find next available row**
   ```python
   service = build('sheets', 'v4', credentials=creds)
   result = service.spreadsheets().values().get(
       spreadsheetId=SHEET_ID,
       range="[Name]'s Persona!A:B"
   ).execute()
   existing_rows = result.get('values', [])
   next_row = len(existing_rows) + 1
   ```

4. **Structure data as 2-column array**
   - Column A: Question with number (e.g., "Q12: What food...")
   - Column B: Full answer text

5. **Append to sheet**
   ```python
   body = {'values': qa_pairs}
   service.spreadsheets().values().append(
       spreadsheetId=SHEET_ID,
       range=f"[Name]'s Persona!A{next_row}",
       valueInputOption='RAW',
       insertDataOption='INSERT_ROWS',
       body=body
   ).execute()
   ```

6. **Confirm with row count + sheet link**

## Known sheet IDs

- Blair's Fitness Sheet: `1sNSE4gRkGMJW5lpTcIJYM69m88JAXks9qQADXmWY6dk`
  - Tab: "Blair's Persona"

## Error handling

- **Token missing**: Inform user, don't auto-run OAuth (skill-authoring exception doesn't cover OAuth flows)
- **Token expired**: Auto-refresh with `creds.refresh(Request())`
- **Sheet/tab not found**: Report specific error, confirm sheet ID and tab name
