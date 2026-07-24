#!/usr/bin/env python3
"""Auto-refresh Canva access token."""
import json
import requests
from datetime import datetime, timedelta

CREDS_PATH = '/home/hermes/.hermes/.canva_credentials'

def refresh():
    with open(CREDS_PATH, 'r') as f:
        creds = json.load(f)
    
    response = requests.post("https://api.canva.com/rest/v1/oauth/token", data={
        "grant_type": "refresh_token",
        "refresh_token": creds['refresh_token'],
        "client_id": creds['client_id'],
        "client_secret": creds['client_secret']
    })
    
    if response.status_code != 200:
        return None
    
    tokens = response.json()
    creds['access_token'] = tokens['access_token']
    if 'refresh_token' in tokens:
        creds['refresh_token'] = tokens['refresh_token']
    creds['last_refreshed'] = datetime.now().isoformat()
    
    with open(CREDS_PATH, 'w') as f:
        json.dump(creds, f, indent=2)
    
    return creds['access_token']

def get_token():
    with open(CREDS_PATH, 'r') as f:
        creds = json.load(f)
    return creds.get('access_token') or refresh()

if __name__ == "__main__":
    print(get_token()[:50] + "...")
