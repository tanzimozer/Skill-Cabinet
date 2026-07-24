# TerraJob Output Quality Check

## Comprehensive QC Workflow

Run this full validation after any TerraJob crawl or sheet population:

### 1. Data Completeness Check

```python
import csv, json, urllib.request, os

jobs = []
with open('output/jobs.csv', 'r') as f:
    reader = csv.DictReader(f)
    for row in reader:
        jobs.append(row)

# Group by source
by_source = {}
for j in jobs:
    src = j.get('source', 'unknown')
    by_source.setdefault(src, []).append(j)

print(f"Total jobs: {len(jobs)}")
for src, jlist in by_source.items():
    print(f"  {src}: {len(jlist)}")

# Data completeness by field
fields = ['score', 'company', 'position', 'location', 'url', 'source', 'salary_min', 'posted_date']
for field in fields:
    missing = sum(1 for j in jobs if not j.get(field))
    pct = missing/len(jobs)*100
    status = "✅" if pct < 20 else "⚠️" if pct < 50 else "❌"
    print(f"  {status} {field}: {missing}/{len(jobs)} missing ({pct:.0f}%)")
```

### 2. Score Distribution Analysis

```python
scores = [int(j.get('score', 0)) for j in jobs]
print(f"\n📈 Score Distribution:")
print(f"  Min: {min(scores)}, Max: {max(scores)}, Avg: {sum(scores)/len(scores):.1f}")
print(f"  High (60+): {sum(1 for s in scores if s >= 60)}")
print(f"  Medium (40-59): {sum(1 for s in scores if 40 <= s < 60)}")
print(f"  Low (<40): {sum(1 for s in scores if s < 40)}")

# Priority matches
priority = sum(1 for j in jobs if j.get('priority_match'))
print(f"\n🎯 Priority Matches: {priority}/{len(jobs)} ({priority/len(jobs)*100:.0f}%)")

# Alerts
alerts = sum(1 for j in jobs if j.get('alert', '').lower() == 'true')
print(f"🔔 Alert-worthy: {alerts}/{len(jobs)} ({alerts/len(jobs)*100:.0f}%)")
```

### 3. URL Verification (Rate-Limit Aware)

```python
import urllib.request, ssl, time

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

print(f"\n🔗 URL Spot Check (2 per source):")
results = {'pass': 0, 'fail': 0, 'rate_limited': 0}

for src, jlist in by_source.items():
    print(f"\n  {src}:")
    for j in jlist[:2]:  # Only 2 per source to avoid rate limits
        url = j.get('url', '')
        company = j.get('company', '')[:20]
        try:
            req = urllib.request.Request(url, headers={
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'
            })
            resp = urllib.request.urlopen(req, timeout=15, context=ctx)
            status = resp.getcode()
            if status == 200:
                results['pass'] += 1
                print(f"    ✅ {company}: OK")
            else:
                results['fail'] += 1
                print(f"    ⚠️ {company}: {status}")
        except urllib.error.HTTPError as e:
            if e.code == 429:
                results['rate_limited'] += 1
                print(f"    ⏳ {company}: Rate limited (URL likely valid)")
            else:
                results['fail'] += 1
                print(f"    ❌ {company}: HTTP {e.code}")
        except Exception as e:
            results['fail'] += 1
            print(f"    ❌ {company}: {str(e)[:30]}")
        time.sleep(1.5)  # Rate limit protection

total = results['pass'] + results['rate_limited'] + results['fail']
valid = results['pass'] + results['rate_limited']
print(f"\n  Estimated validity: {valid}/{total} ({valid/total*100:.0f}%)")
```

### 4. Cross-Check: CSV vs Sheet

After populating the Google Sheet, verify data integrity:

```python
# Read sheet data via API
SHEET_ID = "1vhK1ys152Rem0J6ygntEB9uyajz8trGi7JlmCLHLniI"
url = f"https://sheets.googleapis.com/v4/spreadsheets/{SHEET_ID}/values/TabName!A2:M60"
req = urllib.request.Request(url, headers={'Authorization': f'Bearer {gdrive_token}'})
resp = json.loads(urllib.request.urlopen(req, timeout=30).read())
sheet_rows = resp.get('values', [])

# Compare counts
print(f"📊 Record Counts:")
print(f"  CSV: {len(jobs)} jobs")
print(f"  Sheet: {len(sheet_rows)} rows")
print(f"  Match: {'✅ Yes' if len(jobs) == len(sheet_rows) else '❌ No'}")

# Compare key fields (score, company, position)
mismatches = []
for i, (csv_job, sheet_row) in enumerate(zip(jobs, sheet_rows)):
    if str(csv_job.get('score', '')) != str(sheet_row[1] if len(sheet_row) > 1 else ''):
        mismatches.append(f"Row {i+2}: Score mismatch")
    if csv_job.get('company', '') != (sheet_row[2] if len(sheet_row) > 2 else ''):
        mismatches.append(f"Row {i+2}: Company mismatch")

print(f"\n🔍 Data Integrity: {'✅ All match' if not mismatches else f'❌ {len(mismatches)} mismatches'}")
```

### 5. Duplicate Detection

```python
titles_companies = [(j.get('title'), j.get('company')) for j in jobs]
duplicates = [x for x in titles_companies if titles_companies.count(x) > 1]
unique_dups = list(set(duplicates))

print(f"\n🔁 Duplicate Check:")
if unique_dups:
    print(f"  ⚠️ Found {len(unique_dups)} duplicate job listings:")
    for t, c in unique_dups[:3]:
        print(f"    - {c}: {t[:40]}...")
else:
    print(f"  ✅ No exact duplicates found")
```

### 6. Location Filter Validation

```python
non_target = [j for j in jobs if 'seattle' not in j.get('location', '').lower() 
              and 'remote' not in j.get('location', '').lower()
              and 'wa' not in j.get('location', '').lower()]

if non_target:
    print(f"\n⚠️ {len(non_target)} jobs outside target location:")
    for j in non_target[:3]:
        print(f"  • {j.get('company')} - {j.get('title')[:30]}...")
        print(f"    Location: {j.get('location')}")
```

## Expected Metrics (Jun 2026 Benchmark)

| Metric | Expected Range | Notes |
|--------|---------------|-------|
| Total jobs | 35-50 | Per profile target |
| Score range | 50-75 | Avg ~55 |
| Priority matches | 60-80% | If lower, broaden priority_titles |
| Missing salary | 70-90% | Normal — most posts don't include |
| Missing posted_date | 50-80% | Greenhouse/Lever don't expose |
| URL validity | 95%+ | Rate limits may inflate failure count |
| Duplicates | 0 | Should be zero after dedup |

## Rate Limit Notes

- **BuiltInSeattle:** Aggressive — HTTP 429 after 2-3 rapid requests. Use 2+ second delays.
- **Greenhouse/Lever:** More lenient — 0.5s delays sufficient
- **Brex careers:** No rate limit observed

When QC shows rate limiting, treat as "URL likely valid" — the limit itself proves the server is responding.
