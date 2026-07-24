# Gmail Archive Rules — TIMBR / Tanzim

## Auth note
Token: `~/.hermes/google_token.json`. If refresh fails (HTTP 400), the token is stale. Fix: generate fresh OAuth URL from VM client secret, Tanzim clicks on Mac, pastes code back with codeword. Re-auth is manual — token does NOT sync automatically.

## API gotcha
`format=metadata` with `metadataHeaders` often returns blank From/Subject. Always use `format=full` for reliable results.

## Hard-keep senders (never archive, ever)
chase.com, jpmchase.com, jpmorgan, fieldprint, ibm.com, apify.com, reliancem, amazon.jobs, criteriacorp, paycomonline, modernhire, itccorp.com, evercommerce, fieldprintusa, ashbyhq.com, lever.co, workday, adp.com

## Keep subject keywords (override sender noise signals)
interview, offer, action required, assessment, schedule, availability, onboarding, background, congratulations, follow up, next steps, additional information, invoice, payment, verification code, reminder, canceled

## Archive signals (confirmed noise)
- Generic "thank you for applying" / "we received your application" with no follow-up activity
- Expired one-time security codes for applications already processed
- Duplicate pre-adverse action copies (keep 1, archive rest)
- State Farm / `notifications+reply=` spam (always multiple copies)
- Job board marketing: Adzuna, Virtual Vocations, Jobgether, Vaia, micro1 cold outreach, Microsoft talent spam
- "Incomplete job application alert" where no other contact from that employer
- "Tired of applying?", "Find jobs faster" filler marketing

## Action pattern
1. Always report what will be archived BEFORE doing it — let Tanzim confirm with "A"
2. Remove INBOX label: `POST /messages/{id}/modify` with `{"removeLabelIds": ["INBOX"]}`
3. Never hard-delete unless explicitly instructed — archive is reversible

## Context
Tanzim's inbox (May 2026) is ~116 msgs, heavily job-hunt. JPMorgan Chase onboarding is the active priority — protect all Chase threads absolutely.
