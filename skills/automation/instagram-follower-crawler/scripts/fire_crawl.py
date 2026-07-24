#!/usr/bin/env python3
"""Fire a crawl trigger DIRECTLY from Friday's environment — no Claude relay.
Writes a correctly-shaped 8-column `pending` row to the Commands tab. The Mac
listener_sheet.py polls every 10s, runs the crawl, writes status back.

Usage: python3 fire_crawl.py <handle> [depth]
"""
import sys, json, os, uuid
from datetime import datetime, timezone
import gspread
from google.oauth2.credentials import Credentials

KEY = '1Nuroehse6WIvruHpb1tiyc8ZayIxuWVzzk0sfnYsGi0'  # bind by KEY, never name
SCOPES = ['https://www.googleapis.com/auth/spreadsheets',
          'https://www.googleapis.com/auth/drive']
TOKEN = os.path.expanduser('~/.hermes/google_token.json')  # LIVE token

def main():
    if len(sys.argv) < 2:
        sys.exit('usage: fire_crawl.py <handle> [depth]')
    target = sys.argv[1].lstrip('@')
    depth = sys.argv[2] if len(sys.argv) > 2 else '1'
    tok = json.load(open(TOKEN))
    gc = gspread.authorize(Credentials.from_authorized_user_info(tok, SCOPES))
    c = gc.open_by_key(KEY).worksheet('Commands')
    # SCHEMA: id | command | target | depth | status | result | requested_at | done_at
    rid = uuid.uuid4().hex[:8]
    now = datetime.now(timezone.utc).isoformat()
    c.append_row([rid, 'crawl', target, depth, 'pending', '', now, ''])
    print(f'WROTE pending id={rid} target={target} depth={depth} at {now}')

def status():
    """Poll: print all command rows + current tab list."""
    tok = json.load(open(TOKEN))
    gc = gspread.authorize(Credentials.from_authorized_user_info(tok, SCOPES))
    sh = gc.open_by_key(KEY)
    print('TABS:', [w.title for w in sh.worksheets()])
    for r in sh.worksheet('Commands').get_all_values()[1:]:
        print('ROW:', r[:5], '| result:', (r[5][:90] if len(r) > 5 else ''))

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == '--status':
        status()
    else:
        main()
