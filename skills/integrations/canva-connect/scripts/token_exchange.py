#!/usr/bin/env python3
"""
Canva OAuth token exchange script.
Usage: python3 token_exchange.py "<callback_url>"
"""
import sys
import json
import urllib.parse
import requests

CREDS_PATH = '/home/hermes/.hermes/.canva_credentials'

def exchange_code_for_token(callback_url):
    with open(CREDS_PATH, 'r') as f:
        creds = json.load(f)
    
    parsed = urllib.parse.urlparse(callback_url)
    params = urllib.parse.parse_qs(parsed.query)
    
    if 'code' not in params:
        print("❌ No authorization code found")
        return False
    
    auth_code = params['code'][0]
    print(f"✅ Code extracted")
    
    response = requests.post("https://api.canva.com/rest/v1/oauth/token", data={
        "grant_type": "authorization_code",
        "code": auth_code,
        "code_verifier": creds['code_verifier'],
        "client_id": creds['client_id'],
        "client_secret": creds['client_secret'],
        "redirect_uri": creds['redirect_uri']
    })
    
    if response.status_code != 200:
        print(f"❌ Failed: {response.text}")
        return False
    
    tokens = response.json()
    creds['access_token'] = tokens['access_token']
    creds['refresh_token'] = tokens['refresh_token']
    creds['expires_in'] = tokens.get('expires_in', 14400)
    del creds['code_verifier']
    
    with open(CREDS_PATH, 'w') as f:
        json.dump(creds, f, indent=2)
    
    print(f"✅ Connected to Canva API!")
    return True

if __name__ == "__main__":
    exchange_code_for_token(sys.argv[1])
