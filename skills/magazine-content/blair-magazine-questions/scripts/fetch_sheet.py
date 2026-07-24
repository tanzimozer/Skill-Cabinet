#!/usr/bin/env python3
"""
Fetch Blair's Persona sheet data via Google Sheets API.
Handles token refresh automatically if expired.

Usage: python3 fetch_sheet.py [--raw]
  --raw: Print raw JSON instead of summary

Requires: ~/.hermes/google_token.json with valid refresh_token
"""

import json
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

try:
    import requests
except ImportError:
    print("ERROR: requests not installed. Run: pip install requests")
    sys.exit(1)

TOKEN_PATH = Path.home() / ".hermes" / "google_token.json"
SHEET_ID = "1sNSE4gRkGMJW5lpTcIJYM69m88JAXks9qQADXmWY6dk"
RANGE = "Blair's Persona!A:F"


def load_credentials():
    with open(TOKEN_PATH) as f:
        return json.load(f)


def save_credentials(creds):
    with open(TOKEN_PATH, "w") as f:
        json.dump(creds, f, indent=2)


def is_expired(creds):
    if "expiry" not in creds:
        return True
    expiry = datetime.fromisoformat(creds["expiry"].replace("Z", "+00:00"))
    return datetime.now(timezone.utc) >= expiry


def refresh_token(creds):
    response = requests.post(creds["token_uri"], data={
        "client_id": creds["client_id"],
        "client_secret": creds["client_secret"],
        "refresh_token": creds["refresh_token"],
        "grant_type": "refresh_token"
    })
    if response.status_code != 200:
        raise Exception(f"Token refresh failed: {response.status_code} {response.text}")
    
    new_token = response.json()
    creds["token"] = new_token["access_token"]
    if "expires_in" in new_token:
        expiry = datetime.now(timezone.utc) + timedelta(seconds=new_token["expires_in"])
        creds["expiry"] = expiry.isoformat().replace("+00:00", "Z")
    save_credentials(creds)
    return creds


def fetch_sheet(creds):
    url = f"https://sheets.googleapis.com/v4/spreadsheets/{SHEET_ID}/values/{RANGE}"
    headers = {"Authorization": f"Bearer {creds['token']}"}
    response = requests.get(url, headers=headers)
    if response.status_code == 401:
        raise Exception("Token invalid after refresh")
    response.raise_for_status()
    return response.json()


def analyze_answers(data):
    """Return dict of answered and pending questions."""
    rows = data.get("values", [])[1:]  # Skip header
    answered = []
    pending = []
    
    for row in rows:
        if len(row) < 4:
            continue
        round_num, q_num, category, question = row[:4]
        has_answer = len(row) >= 5 and row[4].strip()
        
        # Normalize key
        r = round_num if round_num.startswith("R") else f"R{round_num}"
        q = q_num if q_num.startswith("Q") else f"Q{q_num}"
        key = f"{r}:{q}"
        
        if has_answer:
            answered.append(key)
        else:
            pending.append(key)
    
    return {"answered": answered, "pending": pending}


def main():
    raw_mode = "--raw" in sys.argv
    
    creds = load_credentials()
    
    if is_expired(creds):
        print("Token expired, refreshing...", file=sys.stderr)
        creds = refresh_token(creds)
    
    data = fetch_sheet(creds)
    
    if raw_mode:
        print(json.dumps(data, indent=2))
    else:
        analysis = analyze_answers(data)
        print(f"Answered: {len(analysis['answered'])}")
        print(f"Pending: {len(analysis['pending'])}")
        print(f"\nAnswered: {', '.join(analysis['answered'])}")
        print(f"\nPending: {', '.join(analysis['pending'])}")


if __name__ == "__main__":
    main()
