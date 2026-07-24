# Gmail Deep Search — Interview / Scheduled Event Hunting
Patterns from a May 2026 session scanning for a confirmed interview across all Gmail folders.

## Search sequence (run in this order — broadens gradually)

### 1. Inbox — keyword subjects
```python
q='subject:(interview OR schedule OR invite OR confirm OR meeting) after:2026/05/01'
```

### 2. Inbox — all recent (no filter)
```python
q='after:2026/05/20'  # adjust window as needed, maxResults=30
```
Manually scan all subjects — confirmed interviews often arrive with generic subject lines.

### 3. Calendar invite attachments (.ics files)
```python
q='filename:ics OR filename:invite.ics after:2026/05/01'
```
These are the most reliable signal for *confirmed* (not just invited) interviews. An .ics attachment = a time was agreed.

### 4. Trash — broad
```python
q='in:trash (confirmed OR scheduled OR "phone screen" OR zoom OR teams OR "google meet" OR "May 27" OR "May 28" OR Wednesday) after:2026/05/01'
```
Then also dump ALL trash subjects and scan manually:
```python
q='in:trash', maxResults=50
```

### 5. Everywhere — date strings
```python
queries = [
    'in:anywhere "May 27"',
    'in:anywhere "may 27"',
    'in:anywhere "5/27"',
    'in:anywhere "05/27"',
    'in:anywhere "27th"',
]
```
Run all, deduplicate by message ID.

### 6. Company-specific (when user names a company type)
```python
# Property management example:
q='in:anywhere Greystar OR Equity OR Prometheus OR Cushman OR "Lincoln Property" OR "Aimco" OR Camden OR Apartment OR Realty OR UDR OR AvalonBay interview'
```
Also search by recruiter first names if known.

### 7. Sent mail + calendar booking link follow-up
```python
q='in:sent Foundation AI OR [company] OR interview OR schedule after:2026/05/01'
```
Many calendar booking links (Calendly, Rooster, Greenhouse Scheduling) send confirmation to the *company*, not back to the candidate. Check if the user clicked a link — if so, no inbound confirmation exists.

## Key finding from this session
A confirmed interview booked via a calendar scheduling link (Calendly, Rooster, HireVue, etc.) often does **not** generate an inbound confirmation email to the candidate's Gmail. The booking confirmation goes to the recruiter. The only evidence is:
- The outbound click (no email trace)
- A Google Calendar event (if auto-created from Gmail)
- A text/LinkedIn message the recruiter sent separately

If exhaustive Gmail search turns up nothing and the user insists it exists → check LinkedIn messages, SMS, or whether it was booked through a portal (Workday, Greenhouse, Lever) where confirmations go to the portal inbox, not Gmail.

## Gmail API gotchas
- `in:anywhere` covers inbox + sent + trash + spam in one query
- `in:trash` search requires explicit label — it's NOT included in default inbox searches
- Google Calendar API is `v3` (not v4 — v4 doesn't exist)
- Calendar API may require separate GCP enablement even if Gmail works fine (different API surface)
- `.ics` attachment search is the fastest path to confirmed appointments — run it early
