# Visa Bulletin — live lookup recipe

The State Dept Visa Bulletin is the authoritative source for priority-date wait times. It changes **every month**. Never quote dates from memory — fetch the current month.

## Finding the current bulletin

Hub page lists every month's bulletin. Find the latest 2026 link:

```bash
curl -sL --max-time 30 "https://travel.state.gov/content/travel/en/legal/visa-law0/visa-bulletin.html" \
  -A "Mozilla/5.0" | grep -ioE "visa-bulletin-for-[a-z]+-2026" | sort -u
```

Bulletin URL pattern:
`https://travel.state.gov/content/travel/en/legal/visa-law0/visa-bulletin/<YEAR>/visa-bulletin-for-<month>-<year>.html`

## Parsing the F2A row

Fetch the bulletin and strip HTML to plain text, then grep `F2A` with context:

```bash
curl -sL --max-time 30 "<bulletin-url>" -A "Mozilla/5.0" -o /tmp/vb.html
python3 -c "
import re,html
t=re.sub(r'<[^>]+>',' ',open('/tmp/vb.html').read())
t=re.sub(r'\s+',' ',html.unescape(t))
for m in re.finditer(r'F2A',t):
    print(repr(t[m.start()-10:m.start()+120])); print()
"
```

## Reading the output

Two charts matter, each with a row of columns by country:

- **Final Action Dates** — when the green card can actually be issued.
- **Dates for Filing** — when you can submit paperwork (usually earlier / more current).

Column order is: **All Chargeability Areas | CHINA | INDIA | MEXICO | PHILIPPINES**.
**Bangladesh (and most countries) = "All Chargeability Areas Except Those Listed"** → the FIRST date column.

`C` = Current (no wait). A date (e.g. `01JAN25`) = only priority dates *before* that are being processed; subtract from today to estimate the backlog.

## Example (July 2026 bulletin, verified)

- F2A Dates for Filing, All Chargeability: **C** (current — can file immediately on becoming LPR)
- F2A Final Action, All Chargeability: **01JAN25** (~1.5yr backlog to actual issuance at that time)

F2A is historically the fastest-moving family preference — frequently current or near-current.

## Gotcha

`browser_navigate` may stall on this site; the `curl` + python HTML-strip path above is reliable and fast. Use it directly for any government-page data fetch.
