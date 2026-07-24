# Resume Tailoring Pipeline (Stage 2 → Stage 3)

End-to-end workflow for generating tailored PDFs from crawled jobs.

## Prerequisites

1. **Jobs crawled** — `output/jobs.csv` exists with scored jobs
2. **JD packets generated** — `output/jd_packets/jd_packet_*.txt` files
3. **Profile populated** — `Stage_2_Resume_Tailoring/tanzim_resume_profile_4of8.json` has real data (33KB+, not empty template)
4. **Google Drive folder** — `TERRAjob.V2testing` folder ID: `19ne7DfKX7bn1A-guddBhMIr9keAjB1WK`

## Profile JSON Structure (Critical)

The profile uses these field names — NOT generic alternatives:

```python
# Roles
role['default_title']    # NOT role['title']
role['title_options']    # list of alternate titles
role['bullets']          # list of dicts with 'text' and 'tags' keys
bullet['text']           # the bullet text

# Certifications — string list, not dict list
profile['certifications'] = ["PMP, PMI - May 2026", "Google PM Certificate - 2024"]

# Projects — string list, not dict list  
profile['projects'] = ["n8n Automation Workflows - AI pipelines..."]

# Skills — separate keys for core vs swappable
profile['core_skills']      # list of strings
profile['swappable_skills'] # list of strings
```

Always handle both string and dict formats when reading these fields.

## Resume Layout Spec

The resume MUST follow `tanzim_resume_layout_5of8.md` exactly:

| Element | Font | Size | Weight | Notes |
|---------|------|------|--------|-------|
| Name | Calibri | 38pt | Bold | ALL CAPS, centered |
| Contact | Calibri | 10.5pt | Regular | Pipe-delimited, dark gray pipes (#666666) |
| Section header | Calibri | 12.5pt | Bold | ALL CAPS, black bottom border |
| Body text | Calibri | 10.5pt | Regular | Justified |
| Skills/Certs/Projects | Calibri | 10.5pt | Regular | Pipe-delimited, light gray pipes (#999999) |

**Hard constraints:**
- US Letter 8.5×11", 0.5" margins all sides
- 1 page maximum (strict)
- No italics anywhere
- Calibri only (Helvetica fallback if unavailable)

## Pipeline Steps

### 1. Generate Tailored PDFs (via subagent)

Deploy an Opus-level subagent with this goal:

```
Generate N tailored resumes for the TOP scoring jobs from today's crawl:

1. Read the top N jobs from /tmp/TERRAjob.V2-personal/Stage_1_Job_Crawl/output/jobs.csv (sorted by score)
2. For each job, read the corresponding JD packet from the jd_packets folder
3. Read Tanzim's profile from tanzim_resume_profile_4of8.json
4. Generate a tailored 1-page PDF resume using reportlab with:
   - Clean professional layout per tanzim_resume_layout_5of8.md
   - Name: Tanzim Ozer, Phone: 425-520-3988, Email: tanzim.seattle@gmail.com
   - LinkedIn: linkedin.com/in/tanzimozer
   - Use role['default_title'] not role['title']
   - Handle certifications/projects as string lists
   - Name format: Ozer_Tanzim_{Company}_{Position}.pdf
5. Upload each PDF to Google Drive folder 19ne7DfKX7bn1A-guddBhMIr9keAjB1WK
6. Return the list of uploaded PDFs with their Drive links
```

Toolsets: `["terminal", "files"]`

### 2. Update Sheet with PDF Links

After subagent returns Drive links, make them **clickable hyperlinks**:

```python
# Convert plain URLs to HYPERLINK formulas
for i, row in enumerate(rows):
    pdf_url = row[0] if len(row) > 0 else ''
    company = row[2] if len(row) > 2 else ''
    
    if pdf_url and 'drive.google' in pdf_url and not pdf_url.startswith('='):
        formula = f'=HYPERLINK("{pdf_url}", "📄 Resume")'
        updates.append({
            'range': f'Scout_2026-06-01!A{i+2}',
            'values': [[formula]]
        })

# Batch update with USER_ENTERED to process formulas
payload = {
    'valueInputOption': 'USER_ENTERED',
    'data': updates
}
```

## Sheet Schema (MUST MATCH MASTER TAB EXACTLY)

**Critical:** The sheet uses this exact column order (from Master tab):

```
A: pdf_resume    (Drive link to tailored resume — use HYPERLINK formula)
B: score         (job match score)
C: company       (company name)
D: position      (job title)
E: location      (city, state)
F: remote        (TRUE/FALSE)
G: salary_min    (number or empty)
H: salary_max    (number or empty)
I: posted_date   (YYYY-MM-DD)
J: alert         (TRUE/FALSE)
K: first_seen    (YYYY-MM-DD)
L: url           (job posting URL)
M: source        (builtin_seattle, greenhouse, lever, etc.)
```

**DO NOT** use different headers like "Score, Title, Company, Location, Salary Range" — must match Master exactly.

When creating a new tab, copy headers from Master tab first, then populate data rows.

## Output Files

PDFs saved to: `/tmp/TERRAjob.V2-personal/Stage_2_Resume_Tailoring/output/`

Naming: `Ozer_Tanzim_{Company}_{Position_Abbreviated}.pdf`

## Timing

- 5 resumes: ~2 minutes (single subagent)
- 50 resumes: ~10-15 minutes (parallel subagents recommended)

## Common Issues

1. **OAuth token expired** — Refresh before upload (see google-oauth-refresh skill)
2. **Rate limiting on job URL verification** — Add 1.5s delay between requests
3. **Missing JD packets** — Some jobs have stub packets with no description; skip these or use job title only
4. **KeyError on profile fields** — Use `role.get('default_title', role.get('title', ''))` pattern
5. **Wrong sheet column order** — Always check Master tab headers first, never guess
