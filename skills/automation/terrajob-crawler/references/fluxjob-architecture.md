# FLUXJOB Architecture Reference

Session: June 2, 2026

## Repo state
- Source: `tanzimozer/TERRAjob.V2-personal` (private) — DO NOT MODIFY
- Fork: `tanzimozer/FLUXJOB` (private) — all changes go here
- Local build: `/tmp/FLUXJOB_build/`

## Key gap discovered: orchestrator ↔ render_pipeline disconnect

`tanzim_app_orchestrator_6of6.py` and `render_pipeline.py` are designed to interoperate but are NOT wired together:

1. **resume_data.json is never written by the orchestrator.** `cmd_tailored` only checks for `.docx` and `.pdf` files dropped in manually.
2. **render_pipeline.py is never called by the orchestrator.** No subprocess, no import, no hook.
3. **render_pipeline silently skips jobs missing resume_data.json** — prints `⊘ {job_id}: no resume_data.json` and moves on.

`fluxjob_run.py` bridges this gap by writing `resume_data.json` (via Claude workers) before calling `render_pipeline.py`.

## resume_data.json schema (required fields)

```json
{
  "_tailored_for": {
    "jd_company": "string — used for PDF filename + Sheet row matching",
    "jd_title": "string — used for PDF filename + Sheet row matching"
  },
  "name": "Tanzim Ozer",
  "contact": { "email": "", "phone": "", "location": "", "linkedin": "" },
  "summary": "string ≤220 chars",
  "skills": ["string", ...],
  "experience": [
    { "title": "", "company": "", "location": "", "dates": "", "bullets": ["string", ...] }
  ],
  "education": [{ "degree": "", "school": "", "dates": "" }],
  "certifications": ["string", ...],
  "projects": [{ "name": "", "description": "" }]
}
```

## Sheet sync — how the HYPERLINK gets written

1. `fluxjob_sheet_sync.py` receives list of job_ids after render
2. For each job: reads `_tailored_for.jd_company` + `_tailored_for.jd_title` from `resume_data.json`
3. Uploads the `.docx` file to Drive folder "FLUXJOB Resumes" (creates folder if missing, makes file public)
4. Scans ALL Sheet tabs for a row where `company` column fuzzy-matches company AND `position` column fuzzy-matches title
5. Writes `=HYPERLINK("drive_url","📄 Resume")` formula to `pdf_resume` column on that row

Fuzzy match: word overlap ≥ 50% for company, ≥ 40% for title. Handles "EverCommerce EverPro" vs "EverCommerce".

## LaTeX template pitfall (learned the hard way)

**Do NOT use Python `r"""..."""` strings for LaTeX templates containing `%` characters.**
`%` triggers `%(key)s`-style formatting and raises `ValueError: unsupported format character`.

**Fix:** Write the template to a separate `.tex` file and use `.replace("%%PLACEHOLDER%%", value)`.

Example:
```python
# WRONG — will crash on % in LaTeX
template = r"""\documentclass{...}\pagestyle{fancy}..."""
result = template % {"name": "Tanzim"}  # ValueError

# RIGHT
template = Path("deedy_template.tex").read_text()
result = template.replace("%%NAMESECTION%%", namesection_block)
```

## QC gate spec

| Check | Limit | Fail = blocked |
|-------|-------|---------------|
| Summary | ≤220 chars | Yes |
| Bullet max | ≤117 chars | Yes |
| Bullets per role | ≤4 | Yes |
| Skills count | ≤21 | Yes |
| Bullet underfill | <100 chars | Warning only |

## Output file naming
`Ozer_Tanzim_{CompanyPascalCase}.{ext}`
PascalCase: no spaces, no punctuation. Digits at start spelled out (AP style).
