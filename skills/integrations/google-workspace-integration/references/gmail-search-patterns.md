# Gmail Search Patterns — Interview & Job Hunting Context

## Find today's interview-related emails
```python
after = int(datetime.datetime(today.year, today.month, today.day, 0, 0, 0).timestamp())
query = f'(interview OR "phone screen" OR "hiring") after:{after}'
```

## Find scheduled interview confirmation emails (last N days)
```python
query = '(interview scheduled OR "interview confirmation" OR "interview invitation" OR "schedule an interview" OR "we would like to interview" OR "next steps" OR "technical interview" OR "hiring manager") newer_than:14d'
```

## Broader sweep — filters out ATS noise
```python
query = '(interview OR recruiter) newer_than:30d -from:myworkday.com -from:ashbyhq.com -from:greenhouse.io'
```

## Finding interview TIMES reliably
Today-only queries miss confirmations sent days prior. Use 14–30 day window and target reminder emails:
```python
query = '(interview scheduled OR "interview confirmation" OR "REMINDER: Interview") newer_than:14d'
```
Reminder email subject pattern: `REMINDER: Interview Scheduled on [Date] [Time] for the [Role]`
These contain everything: date, time, timezone, Zoom link + password, interviewer name — single source of truth.

Also: search for emails containing the specific time ("4:00 PM", "3 PM") when user mentions a time slot not found in standard queries:
```python
query = '("4:00 PM" OR "4 PM" OR "16:00") newer_than:14d'
```

## Direct email link
```
https://mail.google.com/mail/u/0/#inbox/{message_id}
```

## Body extraction (plain text preferred)
```python
def get_body(payload):
    if payload.get('body', {}).get('data'):
        return base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8', errors='ignore')
    for part in payload.get('parts', []):
        if part['mimeType'] == 'text/plain':
            if part.get('body', {}).get('data'):
                return base64.urlsafe_b64decode(part['body']['data']).decode('utf-8', errors='ignore')
        result = get_body(part)
        if result:
            return result
    return ''
```
Always `text/plain` > `text/html`. Strip HTML with `re.sub(r'<[^>]+>', ' ', body)` if plain not available.

## Finding a job listing in tracker sheets from an interview email
1. Extract company name from interview email
2. Search both Job_Tracker (`1v6CY46PBfGyrde8uuMzPv1cETZrOiflUj_HY34SJC_Q`) and TERRAjob (`1vhK1ys152Rem0J6ygntEB9uyajz8trGi7JlmCLHLniI`) for company name + role keywords
3. Get GID for direct tab link: `https://docs.google.com/spreadsheets/d/{id}/edit#gid={gid}`
4. Report: sheet name, tab name, row number, GID, and direct link

## Searching Drive for content docs when name-search fails
```python
# Broad — all recent Docs if name-based search returns nothing
results = drive.files().list(
    q="mimeType='application/vnd.google-apps.document' and modifiedTime > '2026-03-01T00:00:00Z'",
    fields="files(id, name, modifiedTime)",
    orderBy="modifiedTime desc",
    pageSize=30
).execute()
```
If still nothing: check folder contents by folder ID (use `'<folder_id>' in parents`), then check spreadsheets for tabs that may contain the content inline.

## Parsing PDF résumés from Drive
```python
# Download
request = drive.files().get_media(fileId=file_id)
with open('/tmp/resume.pdf', 'wb') as f:
    f.write(request.execute())

# Parse
import pdfplumber
with pdfplumber.open('/tmp/resume.pdf') as pdf:
    for page in pdf.pages:
        print(page.extract_text())
```
