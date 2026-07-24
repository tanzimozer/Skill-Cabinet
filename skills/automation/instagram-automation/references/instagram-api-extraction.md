# Instagram Internal API — Full Extraction Script

Bypasses Playwright entirely. Works from the VM. Uses session cookies directly.

## Account details
- Username: tanzim.ozer
- User ID: 40730017115

## Full script

```python
import requests, json, time, csv, os
from datetime import date

COOKIES = {
    'datr': '<datr value>',
    'ds_user_id': '40730017115',
    'csrftoken': '<csrftoken>',
    'ig_did': '<ig_did>',
    'mid': '<mid>',
    'sessionid': '<sessionid>',
}

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
    'X-CSRFToken': '<csrftoken value>',
    'X-IG-App-ID': '936619743392459',
    'Referer': 'https://www.instagram.com/',
}

USER_ID = '40730017115'

def fetch_list(endpoint):
    all_users, after, page = [], None, 0
    while True:
        params = {'count': 200}
        if after:
            params['max_id'] = after
        r = requests.get(
            f'https://www.instagram.com/api/v1/friendships/{USER_ID}/{endpoint}/',
            params=params, cookies=COOKIES, headers=HEADERS, timeout=15
        )
        if r.status_code != 200:
            print(f"Error {r.status_code}: {r.text[:200]}")
            break
        data = r.json()
        users = data.get('users', [])
        all_users.extend([u['username'] for u in users])
        page += 1
        print(f"  Page {page}: {len(users)} users (total: {len(all_users)})")
        after = data.get('next_max_id')
        if not after or not users:
            break
        time.sleep(1.5)
    return all_users

followers = fetch_list('followers')
following = fetch_list('following')

today = date.today().isoformat()
reports = '/home/hermes/ig-churn/Sub-Folder/reports'
os.makedirs(reports, exist_ok=True)

for name, lst in [('followers', followers), ('following', following)]:
    with open(f'{reports}/{name}_{today}.csv', 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['username'])
        for u in lst: w.writerow([u])

# Load whitelist
whitelist = set()
with open('/home/hermes/ig-churn/Sub-Folder/whitelist.txt') as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith('#'):
            whitelist.add(line.lower())

followers_set = set(followers)
following_set = set(following)
non_followers = following_set - followers_set
to_unfollow   = non_followers - whitelist

# SAFETY CHECK
assert len(followers_set & following_set) > 0, "No mutuals — parse error, STOP"

print(f"Followers: {len(followers_set)}, Following: {len(following_set)}")
print(f"Mutuals (protected): {len(followers_set & following_set)}")
print(f"To unfollow: {len(to_unfollow)}")

with open(f'{reports}/unfollow_queue_{today}.csv', 'w', newline='') as f:
    w = csv.writer(f)
    w.writerow(['username'])
    for u in sorted(to_unfollow): w.writerow([u])
```

## Notes
- API returns max 200 per page — paginate with `next_max_id`
- Rate: 1.5s between pages is safe
- If 401: session cookie expired — get fresh cookies from Tanzim
- If 429: rate limited — add longer sleep
