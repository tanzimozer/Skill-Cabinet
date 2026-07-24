---
name: gmail-search-deep
description: "Full-coverage Gmail search methodology — inbox, trash, sent, calendar invites, body content. Use when a surface search returns nothing and the user is confident something exists."
version: 1.0.0
tags: [gmail, search, email, google]
---

# Deep Gmail Search

Use this when a standard inbox search returns nothing but the user believes the email exists. Work through layers in order — stop when you find it.

## Search Layer Order

### 1. Inbox — subject keywords
```python
q='subject:(interview OR confirm OR schedule OR invite OR meeting)'
```

### 2. Full inbox — no subject restriction, date-bounded
```python
q='interview OR schedule OR confirm after:2026/05/01'
```

### 3. Trash — same queries with `in:trash` prefix
```python
q='in:trash interview OR confirm OR schedule after:2026/05/01'
```
Gmail auto-deletes many job application and notification emails. **Trash is often where the answer lives.**

### 4. Anywhere — catch-all including spam
```python
q='in:anywhere "May 27" OR "May 28" OR "Wednesday"'
```

### 5. Calendar invite attachments (.ics files)
```python
q='filename:ics after:2026/05/01'
```
These are actual confirmed scheduled meetings — highest signal for interview confirmations.

### 6. Sent mail — user may have replied to or initiated the thread
```python
q='in:sent interview OR schedule after:2026/05/01'
```

### 7. Body content search — open the full email body
When subject lines are ambiguous, pull the full email body for candidates. Use `format='full'` and decode:
```python
full = service.users().messages().get(userId='me', id=msg_id, format='full').execute()
# Decode plain text or strip HTML
```

### 8. Broad trash dump — list everything, filter manually
If all else fails, pull all trash emails with metadata and list them. Let the user identify the right one by company name or context.
```python
q='in:trash', maxResults=500, paginate with nextPageToken
```

## Pitfalls

- **Calendar API** requires separate OAuth scope — use `calendar v3`, not v4. If 403, the API isn't enabled in the GCP project — flag it, don't retry.
- **Booking link confirmations** often don't send a return email — if the user booked via Calendly/Rooster/HireVue, there may be no email at all. Ask if they used a calendar link.
- **HTML-only emails** return empty body on `text/plain` parse — always fall back to `text/html` and strip tags with regex.
- **1,000+ trash emails** require pagination — always check `nextPageToken` and loop.

## When to stop and ask
If all 8 layers return nothing, the confirmation likely came via:
- SMS / WhatsApp
- LinkedIn message
- Calendar booking link with no confirmation email
- Different email account

State this plainly and ask the user for more context (company name, how they applied) rather than continuing to scan blind.
