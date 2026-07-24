# Incremental Scope Expansion Pattern

**Discovered:** June 8, 2026 during Gmail + Google Sheets OAuth setup for job tracker access

**Scenario:** User needed both Gmail and Sheets access. Gmail was set up first with `gmail.readonly` scope. Job tracker scan failed with 403 Forbidden on Sheets API (scope not authorized). Required re-authorization with both scopes included.

## The Flow (What Happened)

1. **Initial auth:** `gmail.readonly` scope only → successful token exchange
2. **First task attempt:** Scan Google Sheets → 403 Forbidden (API scope not in token)
3. **Correction:** Generate new auth link with both `gmail.modify` (for delete operations) and `spreadsheets` scopes
4. **Re-auth:** User clicks new link, authorizes with expanded scope set
5. **Token exchange:** New token now includes both Gmail + Sheets permissions
6. **Task succeeds:** Sheets API calls now work

## Why This Pattern Matters

- **Scope creep is normal:** You don't always know all scopes needed upfront. Gmail auto-scanning needs `gmail.readonly`, but once user says "delete emails" you need `gmail.modify`. Then they ask for job tracker data and you need `spreadsheets`.
- **Re-authorization is fast:** Don't fight it. A new auth link takes 30 seconds to generate and 2 minutes for user to authorize. It's faster than debugging why Sheets API returns 403.
- **Proactive scope building saves re-auth:** If you suspect you'll need multiple APIs (Gmail + Sheets + Drive + Calendar), request all scopes upfront in a single auth flow. This session would have been faster with one auth that included 5–6 scopes from the start.

## Anti-Pattern

❌ **DON'T:** Keep trying the same API call 3–4 times, hoping the scope magically appears.
❌ **DON'T:** Tell user "Sheets API isn't working" without explaining it's a scope/auth issue.
❌ **DON'T:** Ask permission to re-auth. Just generate the new link and offer it.

## Correct Pattern

1. **Task fails with 403 Forbidden** → immediately identify as scope issue
2. **Generate new auth URL with expanded scope set** → include all scopes user will likely need
3. **Present link + one-line explanation:** "Sheets access requires re-authorization. Click here, authorize, paste the code."
4. **Re-exchange tokens silently**
5. **Retry original task**

## Code Example

```python
# First auth (Gmail only)
scopes = ["https://www.googleapis.com/auth/gmail.readonly"]

# User asks to delete → needs gmail.modify
# User asks for Sheets → needs spreadsheets
# DECISION: Regenerate with expanded scopes

scopes = [
    "https://www.googleapis.com/auth/gmail.modify",        # Gmail full access
    "https://www.googleapis.com/auth/spreadsheets",        # Google Sheets
    "https://www.googleapis.com/auth/drive",               # Drive (for future file ops)
    "https://www.googleapis.com/auth/calendar",            # Calendar (if needed)
    "https://www.googleapis.com/auth/documents",           # Docs (if needed)
]

# Build new auth link with all scopes
scope_string = " ".join(scopes)
auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?...&scope={urllib.parse.quote(scope_string)}&...&prompt=consent"

# User authorizes once with full set
# Single token exchange returns token with all scopes
```

## When to Use This

- User's initial request is narrow (Gmail only), but they later need more APIs
- You detect a 403 Forbidden on API call to new service
- Building an integrated tool that touches multiple Google services
- User says "while you're at it, can you also..."

## Speed Optimization

**Best practice (this session):** When you know upfront that work will need multiple Google services (Gmail + Sheets), request all scopes in ONE auth flow:
- Faster: One auth link click, one code paste
- Cleaner: Single token with all permissions
- No re-auth mid-task

This session had **two auth flows**. One flow with 6 scopes upfront would have been faster.
