"""
compute_alt_exercises.py
Computes Alt Exercise 1 (Col D) and Alt Exercise 2 (Col E) for WORKOUT PLAN DB
using Cluster-based logic locked July 2026.

Rules:
  Alt 1 — same Cluster as Primary, different exercise, same (level, muscle)
  Alt 2 — different Cluster from Primary, not Primary or Alt 1, same (level, muscle)
  Both fall back to any unused same-(level, muscle) exercise if the cluster rule can't be satisfied.
  Deduplication: each column must be unique against everything to its left in the row.
"""

import json
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from collections import defaultdict

# --- Auth ---
with open('/home/hermes/.hermes/google_token.json') as f:
    t = json.load(f)

creds = Credentials(
    token=t.get('token'), refresh_token=t.get('refresh_token'),
    token_uri=t.get('token_uri', 'https://oauth2.googleapis.com/token'),
    client_id=t.get('client_id'), client_secret=t.get('client_secret'),
    scopes=t.get('scopes')
)
svc = build('sheets', 'v4', credentials=creds)
SHEET_ID = '1WrA1wi6Az0bVHd_hrTFbTya4neWFaiBgmBuu8XXy3bo'


def build_pool():
    """Returns pool[(level, muscle)] = [(name, cluster), ...]"""
    result = svc.spreadsheets().values().get(
        spreadsheetId=SHEET_ID, range='STRENGTH DB'
    ).execute()
    rows = result.get('values', [])[1:]
    pool = defaultdict(list)
    for row in rows:
        if len(row) < 13:
            continue
        level, name, cluster, muscle = row[0], row[1], row[12], row[7]
        pool[(level, muscle)].append((name, cluster))
    return pool


def get_alts(pool, level, muscle, primary):
    """
    Returns (alt1, alt2) for a given primary exercise.
    alt1 — same cluster, different exercise
    alt2 — different cluster from primary, not primary or alt1
    Both fall back to any unused same-(level, muscle) exercise.
    """
    candidates = pool.get((level, muscle), [])
    primary_cluster = next((c for n, c in candidates if n == primary), None)

    # Alt 1: same cluster, not primary
    alt1 = next(
        (n for n, c in candidates if n != primary and c == primary_cluster),
        None
    )
    # fallback: any same pool, not primary
    if not alt1:
        alt1 = next((n for n, c in candidates if n != primary), None)

    exclude = {primary, alt1} if alt1 else {primary}

    # Alt 2: different cluster, not already used
    alt2 = next(
        (n for n, c in candidates if n not in exclude and c != primary_cluster),
        None
    )
    # fallback: any same pool, not already used
    if not alt2:
        alt2 = next((n for n, c in candidates if n not in exclude), None)

    return alt1 or '', alt2 or ''


def apply_to_tab(tab_name='WORKOUT PLAN DB', level_filter=None, row_limit=None):
    """
    Reads tab_name, recomputes Col D and Col E per alt logic, writes back.
    level_filter: if set (e.g. 'S1'), only recompute rows at that level.
    row_limit: if set, only recompute first N matching rows (for testing).
    """
    pool = build_pool()

    result = svc.spreadsheets().values().get(
        spreadsheetId=SHEET_ID, range=tab_name
    ).execute()
    rows = result.get('values', [])
    header = rows[0]
    data = rows[1:]

    new_data = []
    count = 0
    for row in data:
        if len(row) < 3:
            new_data.append(row)
            continue
        level, muscle, primary = row[0], row[1], row[2]
        should_process = (
            (level_filter is None or level == level_filter) and
            (row_limit is None or count < row_limit)
        )
        if should_process:
            alt1, alt2 = get_alts(pool, level, muscle, primary)
            new_data.append([level, muscle, primary, alt1, alt2])
            count += 1
        else:
            new_data.append(row)

    svc.spreadsheets().values().clear(
        spreadsheetId=SHEET_ID, range=tab_name
    ).execute()
    svc.spreadsheets().values().update(
        spreadsheetId=SHEET_ID,
        range=f"'{tab_name}'!A1",
        valueInputOption='RAW',
        body={'values': [header] + new_data}
    ).execute()
    print(f"Done. {count} rows recomputed in '{tab_name}'.")


if __name__ == '__main__':
    # Safe test: duplicate tab first, apply to S1 only, first 10 rows
    apply_to_tab(tab_name='WORKOUT PLAN DB - TEST', level_filter='S1', row_limit=10)
