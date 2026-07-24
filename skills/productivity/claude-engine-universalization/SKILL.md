---
name: claude-engine-universalization
description: "Turn a personalized working system into a universal Claude engine with self-configuring onboarding — extract principles, create discovery questions, strip personal data, package for distribution."
tags: [claude, engine, template, onboarding, universal, horcrux, distribution]
---

# Claude Engine Universalization

## When to Use
- User has a working personalized system (scraper, workflow, automation) and wants to share it
- User asks to "make this universal" or "create a template others can use"
- User wants to package a system for Claude Projects / Claude Code / Claude Cowork
- Goal is: others can paste the doc, say "Start", answer questions, and have their own configured version

## Core Philosophy

A universal Claude engine has three parts:
1. **Immutable principles** — the logic that makes the system work (filtering rules, scoring, architecture)
2. **User-configurable parameters** — values that change per user (locations, titles, companies, thresholds)
3. **Self-configuring onboarding** — questions that extract #2 from the user without them reading docs

## Step-by-Step Process

### 1. Audit the Source System
Read ALL source files. Identify:
- Hard-coded personal values (names, phone numbers, paths, API keys, sheet IDs)
- User-specific preferences (locations, salary floors, blocklists)
- Universal logic (filters, scoring formulas, data sources, output formats)

### 2. Design the Onboarding Questions
Create 8-12 questions that capture ALL user-configurable parameters. Each question should:
- Be self-explanatory with examples
- Map to specific config variables
- Have sensible defaults if skipped

**Question template:**
```
"[Clear question about preference]

Examples:
- Option A
- Option B
- Option C

Your answer:"

→ Captures: VARIABLE_NAME (format/type)
```

### 3. Extract Principles into Prose
Convert code logic into readable documentation:
- Filter pipeline as numbered steps
- Scoring system as point breakdowns
- Data sources with endpoints and parsing notes
- Output formats with example structures

### 4. Security Scrub
Remove ALL personal data:
- Names, phone numbers, emails
- API keys, tokens, credentials
- File paths with usernames
- Google Sheet IDs, Trello board IDs
- Company-specific blocklists (generalize to "your blocklist")
- Any identifying information

**Validation:** grep for phone patterns, email patterns, `/home/`, API key patterns, specific names.

### 5. Create the Engine Document

Structure:
```markdown
# ENGINE NAME
## Subtitle explaining what it does

**Activation:** Say "Start" to begin onboarding

---

# PART 1: ENGINE ACTIVATION
[Trigger words and what happens]

# PART 2: ONBOARDING SEQUENCE
[All questions, one section each, with variable mapping]

# PART 3: PROFILE CONFIRMATION
[Template for displaying user's answers]

# PART 4: CORE PHILOSOPHY
[Immutable principles — these don't change per user]

# PART 5: SCORING SYSTEM
[Point values, formulas, thresholds]

# PART 6: FILTER PIPELINE
[Ordered list of checks, drop conditions]

# PART 7: DATA SOURCES
[APIs, endpoints, parsing patterns]

# PART 8: OUTPUT SPECIFICATION
[File formats, column names, example data]

# PART 9: EXECUTION COMMANDS
[What user can say after onboarding]

# PART 10: IMPLEMENTATION SKELETON
[Code template with placeholder variables]

# PART 11: QUICK START
[Copy, paste, say "Start", answer questions, say "Run"]

# PART 12: EXTENSION POINTS
[How to add sources, rules, filters]
```

### 6. Create Companion Files (Optional)
- `user_questions.txt` — just the questions, standalone
- `config_template.json` — empty JSON with all variable names
- `example_config.json` — filled example (use fictional data)

### 7. Upload to Shareable Location
- Google Drive folder with public/link sharing
- All files lowercase, no spaces (use underscores)
- Include both .md and .txt versions if needed

### 8. Final Security Review
Before sharing, verify:
- [ ] No phone numbers
- [ ] No email addresses
- [ ] No API keys or tokens
- [ ] No file paths with real usernames
- [ ] No Google Sheet/Doc/Drive IDs
- [ ] No company-specific data that identifies the original user
- [ ] Examples use generic placeholders (Seattle → "Seattle, WA or Austin, TX")

## Output Checklist
- [ ] Main engine .md file with all 12 parts
- [ ] User questions standalone file
- [ ] All files in shareable Drive folder
- [ ] Lowercase filenames
- [ ] Security scrub complete
- [ ] Test: paste into fresh Claude, say "Start", verify onboarding works

## Example: Job Crawler Engine

Source: `/home/hermes/jobs/scraper.py` (900 lines, Tanzim-specific)
Output: `claude_job_crawler.md` (universal, 700 lines)

Onboarding questions captured:
1. Target location
2. Priority job titles
3. Wider-net titles
4. Experience level
5. Salary floor
6. Deal-breaker keywords
7. Company blocklist
8. Dream companies
9. Education requirements
10. Job freshness

Personal data removed:
- Tanzim's name → removed entirely
- Seattle-specific locations → "Seattle, WA or Austin, TX" examples
- Company blocklist → empty, user fills in
- Sheet ID → removed (user provides their own)
- File paths → generic placeholders

## Pitfalls
- **Don't include "my" or first-person references** — the engine should read as third-party documentation
- **Examples must be generic** — don't use the original user's actual preferences as examples
- **API keys in code comments** — scan code blocks for hardcoded values
- **Relative paths** — `/home/hermes/` leaks the system owner; use `./` or `{PROJECT_DIR}/`
- **Sheet IDs in URLs** — Google Sheets links contain identifying IDs
- **Phone patterns** — grep for `\d{3}[-.]?\d{3}[-.]?\d{4}` and `\d{10}`
- **Email patterns** — grep for `@` in non-code contexts

## Related Skills
- `claude-cowork-engine-cloning` — adapting a multi-file engine for a new user (different pattern)
- `job-board-scraping` — the source system that was universalized in the example
