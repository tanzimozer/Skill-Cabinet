# JOB_HAMMER Filter Architecture

11-stage sequential filtering pipeline. One rule drop kills the job. Boosts stack. All substring matches (case-insensitive).

## F1 — Location
**Target:** Seattle WA, Bellevue, Kirkland, Redmond, Remote
**Sources:**
- JobSpy: Indeed, LinkedIn, Glassdoor, Google, ZipRecruiter (7-day window)
- BuiltInSeattle (Seattle tech jobs board)
- Workday (seed companies' ATS)

## F2 — Hard Exclude Keywords (200+ entries)
**Blocks (substring match):**
- Clearance required (TS/SCI)
- Degree requirements: PhD, MD
- Work model: on-site only, 100% on-site
- Compensation: cold-calling quota, commission-only
- **Geographic blocklist (100+ cities):**
  - India: Manila, Bangalore, Hyderabad, Gurgaon, Noida, Pune, Chennai, Mumbai
  - LATAM: Bogotá, Medellín, Mexico City, Guadalajara, Buenos Aires, São Paulo, Lima
  - Europe: Kraków, Warsaw, Wrocław, Bucharest, Belgrade, Kyiv, Kiev, Amsterdam, Berlin, Munich, Dublin, Vienna, Prague, Copenhagen, Stockholm, Oslo, Helsinki, Brussels, Zurich, Frankfurt, Hamburg, Barcelona, Madrid, Lisbon, Rome, Milan, Athens, Paris, London, etc.
  - Canada: Toronto, Vancouver, Montreal, Calgary, Edmonton, Ottawa
- **Region blocks:** "remote LATAM", "remote APAC", "remote EMEA only", "(EMEA", "(APAC", "(LATAM"
- **Country blocks (with variations):** Philippines, India, Peru, Colombia, Brazil, Mexico, Argentina, Pakistan, Bangladesh, Vietnam, Ukraine, Poland, Romania, Egypt, Nigeria
- **Company blocklist (110+ names via substring):** Amazon, Google, Meta, Tesla, Big 4 consulting (McKinsey, BCG, Bain), CoreWeave, etc.

## F3 — Seniority Exclude (7 regex patterns)
**Blocks:**
1. `\b(intern|internship)\b`
2. `\b(director|VP|vice president|chief|ceo|cfo|coo|head of)\b`
3. `\bsenior\s+(manager|director|sales development representative|sdr|specialist|analyst|coordinator|associate)\b`
4. `\b(principal|staff)\b`
5. `\bprogram manager\b`
6. `\b(account executive|business development|sdr|bdr|sales development|sales representative|sales rep|sales manager|sales associate|sales consultant|inside sales|outside sales|territory manager|quota)\b`
7. `\b(relationship banker|personal banker|branch manager|bank teller|teller|loan officer|mortgage (loan )?officer|financial advisor)\b`

**Allows:** Entry to early-mid roles (no pure IC block)

## F4 — Title Boost
**Priority titles** (+20 points):
- Project Coordinator
- Implementation Specialist
- Operations Specialist

**Wide net titles** (+10 points):
- Assistant Project Manager
- Operations Coordinator
- Implementation Coordinator
- Customer Success Coordinator
- Account Coordinator
- Operations Analyst
- Data Analyst
- Data Coordinator

(Updated 2026-05-22: removed sales titles; added Data roles per user request)

## F5 — Experience Level & Duration
**Rule:** Early (entry to ~2-3 years)
**Max years required:** 5 years (drops jobs demanding 6+)
**Degree filter:** "flexible" (degrees not required; preferred OK)

## F6 — Salary Band
**Floor:** $55k (relaxed from $60k to catch smaller startups)
**Ceiling:** $80k hard cap
**Target:** $70k (center of band)
**Target band:** ±15% of target = ~$59,500–$80,500 gets +5 boost
**Jobs without posted salary:** Pass (benefit of doubt)

## F7 — Work Authorization
**Rule:** US Citizen (no sponsorship)

## F8 — Company Size Preference
**Soft target:** Startup + scaleup (<2,000 employees)
**Enforcement:** Company blocklist only (no headcount data per job)

## F9 — Industry Boost (vertical signals)
**+8:** Mobile banking, Microsoft, University of Washington, Fred Hutch
**+6:** Fitness, supplement
**+5:** Banking, fintech, wellness, nutrition, sports, data roles

(Matched against company.lower() OR description.lower())

## F10 — Work Model
**Default:** "any" (Seattle remote + on-site both OK)
**Override:** Set to "fully_remote" to drop on-site roles

## F11 — Recency
**Crawl window:** 7 days (JobSpy respects this at API level)
**Hard cap:** 21 days (drops anything older than 21d post-crawl)
**Scoring bonus:** If <7 days old

## Output
- Sorted by SCORE descending
- Dedup by URL (persistent in `dedup_index.json`)
- Daily cap: top 50 net-new after dedup
- CSV format with all 11 columns (including JD from job description)
- Sync to Google Sheets via `sync_to_sheet.py`

## Typical Metrics
- 500–800 candidates scraped per crawl (raw)
- 50–100 after F2–F3 (hard excludes + seniority)
- 20–40 net-new after dedup (first run) or 5–15 (subsequent runs)
