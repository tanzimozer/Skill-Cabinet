#!/usr/bin/env python3
"""Probe every candidate Google credential file against the Bulldozer sheet.
Prints which token is LIVE and can open the sheet. Run this FIRST whenever a
gspread write appears to fail — do not assume Friday 'cannot write'.
"""
import json, os
import gspread
from google.oauth2.credentials import Credentials

KEY = '1Nuroehse6WIvruHpb1tiyc8ZayIxuWVzzk0sfnYsGi0'
SCOPES = ['https://www.googleapis.com/auth/spreadsheets',
          'https://www.googleapis.com/auth/drive']
HOME = os.path.expanduser('~')
CANDIDATES = [
    '.hermes/google_token.json',                          # LIVE (verified 2026-07-04)
    '.hermes/instagrammer/mac/secrets/google_token.json', # LIVE
    '.hermes/GOOGLE_OAUTH_ACTIVE.json',                   # missing refresh_token
    'friday_backup/google_token.json',                    # DEAD: deleted_client
]
for rel in CANDIDATES:
    p = os.path.join(HOME, rel)
    print('=== TRYING', rel)
    if not os.path.exists(p):
        print('  (missing)'); continue
    try:
        tok = json.load(open(p))
        if tok.get('type') == 'service_account':
            from google.oauth2.service_account import Credentials as SA
            creds = SA.from_service_account_file(p, scopes=SCOPES)
        else:
            creds = Credentials.from_authorized_user_info(tok, SCOPES)
        sh = gspread.authorize(creds).open_by_key(KEY)
        print('  OK ->', sh.title, '| tabs:', [w.title for w in sh.worksheets()])
    except Exception as e:
        print('  FAIL:', str(e)[:160])
