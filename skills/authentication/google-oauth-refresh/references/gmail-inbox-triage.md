# Gmail Inbox Triage Pattern

Comprehensive inbox analysis workflow that prioritizes actionable emails.

## Deployment

Best run as a subagent with `["terminal", "files"]` toolsets:

```
Goal: Perform a comprehensive Gmail inbox analysis for Tanzim.

1. Scan the INBOX for the last 50 emails - get sender, subject, date, read/unread status
2. Check SPAM folder for any legitimate emails that may have been misclassified
3. Check TRASH for any important emails that may have been accidentally deleted
4. Cross-reference and identify:
   - HIGH PRIORITY: Job interviews, recruiter responses, urgent action items
   - NEEDS ACTION: Unread emails requiring response within 48 hours
   - EXPIRED: Time-sensitive emails past their deadline
   - LOW PRIORITY: Newsletters, marketing, auto-notifications

Use the Google OAuth token at ~/.hermes/google_token.json (refresh if needed).

Gmail API endpoints:
- List messages: GET https://gmail.googleapis.com/gmail/v1/users/me/messages?labelIds=INBOX&maxResults=50
- Get message: GET https://gmail.googleapis.com/gmail/v1/users/me/messages/{id}?format=metadata
- Labels: INBOX, SPAM, TRASH, UNREAD

Output a concise markdown table with columns: Priority | From | Subject | Date | Status | Action Needed

Sort by priority (HIGH → NEEDS ACTION → LOW → EXPIRED)
```

## Priority Classification

### HIGH PRIORITY — Action Required
- Job interview confirmations/changes
- Recruiter follow-ups ("Quick call about your application")
- Interview link issues
- Time-sensitive deadlines (within 24-48 hours)

### NEEDS ATTENTION — Application Updates
- "Application status updated"
- "We've reviewed your application"
- Company portal notifications

### SPAM RESCUE — Legit Emails in Spam
- **Common false positives:** Calendly bookings, smaller company HR emails, automated job confirmations from lesser-known ATS systems
- **Pattern:** If subject contains "interview", "application", "phone screen" → likely legitimate

### LOW PRIORITY
- "Thank you for applying" auto-confirmations
- Newsletter/marketing
- Google/system notifications
- Receipts/invoices

### EXPIRED
- Past interview dates
- Deadline-based requests where date has passed

## Output Format

```markdown
### 🔴 HIGH PRIORITY — ACTION NOW

| From | Subject | Date | Action |
|------|---------|------|--------|
| **ITC Corp** | RE: Invalid Interview Link | May 31 | **REPLY ASAP** |

### 🟡 NEEDS ATTENTION — Application Updates

| Company | Date | Type |
|---------|------|------|
| DoorDash | Jun 1 | Status update |

### ⚠️ RESCUED FROM SPAM

| From | Subject | Date | Risk |
|------|---------|------|------|
| **Carmel Partners** | Project Manager Application | May 12 | Legit job app |

### 🟢 LOW PRIORITY — No Action
Auto-confirmations, newsletters, system notifications

### 🗑️ TRASH — Safe to Ignore
Expired verification codes, one-time use items
```

## API Implementation Notes

```python
# List messages with specific label
url = f"https://gmail.googleapis.com/gmail/v1/users/me/messages?labelIds={label}&maxResults=50"

# Get message metadata (headers only — faster than full)
url = f"https://gmail.googleapis.com/gmail/v1/users/me/messages/{msg_id}?format=metadata"

# Key headers to extract
headers_to_find = ['From', 'Subject', 'Date']
```

## Timing

Subagent typically takes ~90-120 seconds to:
- Scan 50 inbox messages
- Check 10 spam
- Check 10 trash
- Classify and format output
