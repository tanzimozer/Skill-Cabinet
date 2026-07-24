#!/usr/bin/env python3
"""
Test Instagram session health before launching a full scrape.
Checks both tag fetch and per-user enrich endpoints.
Run before any scraping job to confirm cookies are live.
"""
import requests, json, sys

with open('/home/hermes/.hermes/vault.json') as f:
    ig = json.load(f)['instagram']

COOKIES = {
    'datr': ig['datr'], 'ds_user_id': ig['ds_user_id'],
    'csrftoken': ig['csrf_token'], 'ig_did': ig['ig_did'],
    'mid': ig['mid'], 'sessionid': ig['session_id'],
}
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
    'X-CSRFToken': ig['csrf_token'],
    'X-IG-App-ID': '936619743392459',
    'Referer': 'https://www.instagram.com/',
}

print("=== Instagram Session Health Check ===\n")

# Test 1: Tag fetch
print("1. Tag fetch (melbournefit)...")
r = requests.post('https://www.instagram.com/api/v1/tags/melbournefit/sections/',
    cookies=COOKIES, headers=HEADERS, data={'tab':'recent','page':1,'count':33}, timeout=15)
print(f"   Status: {r.status_code}")
if r.status_code == 200:
    d = r.json()
    uids = {}
    for section in d.get('sections', []):
        for media in section.get('layout_content', {}).get('medias', []):
            user = media.get('media', {}).get('user', {})
            uid, uname = str(user.get('pk','')), user.get('username','')
            if uid and uname: uids[uid] = uname
    print(f"   ✅ Tag fetch OK — {len(uids)} candidates found")
    test_uid, test_uname = next(iter(uids.items())) if uids else (None, None)
else:
    print(f"   ❌ Tag fetch FAILED")
    test_uid, test_uname = None, None

# Test 2: Enrich endpoint
if test_uid:
    print(f"\n2. Enrich endpoint (@{test_uname}, uid {test_uid})...")
    r2 = requests.get(f'https://www.instagram.com/api/v1/users/{test_uid}/info/',
        cookies=COOKIES, headers=HEADERS, timeout=12)
    print(f"   Status: {r2.status_code}")
    if r2.status_code == 200 and r2.text.strip().startswith('{'):
        u = r2.json().get('user', {})
        print(f"   ✅ Enrich OK — @{u.get('username')} | {u.get('follower_count')} followers")
        print(f"\n✅ SESSION FULLY HEALTHY — ready to scrape")
        sys.exit(0)
    elif r2.status_code == 429:
        print(f"   ⚠️  Rate limited (429) — wait 30-60 mins or get fresh cookies")
    elif r2.text.strip().startswith('<!'):
        print(f"   ❌ Enrich BLOCKED — HTML response (device flagged)")
        print(f"   → Need fresh cookies from a DIFFERENT browser (different datr cookie)")
    else:
        print(f"   ❌ Enrich failed: {r2.status_code} — {r2.text[:100]}")
    print(f"\n⚠️  TAG FETCH OK but ENRICH BLOCKED — scrape will return 0 results")
    sys.exit(1)
