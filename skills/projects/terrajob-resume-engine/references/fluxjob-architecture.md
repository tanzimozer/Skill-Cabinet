# FLUXJOB Architecture Notes

## Why FLUXJOB exists

TerraJob pipeline inefficiency: every subagent was loading 1,413 lines of spec cold (8 files).
FLUXJOB compiles those to 288 lines and separates Claude's role (content only) from Python's role (rendering).

## Efficiency changes applied

| Problem | Fix | File |
|---------|-----|------|
| 1,413 lines of spec per worker | Compiled to 288 lines | `FLUXJOB_CONTEXT_COMPILED.md` |
| Claude does formatting | Content/render split — Claude → `resume_data.json` only | `fluxjob_run.py` |
| Sequential single-worker | Up to 6 parallel Claude workers | `fluxjob_run.py` |
| No validation gate | QC gate before render (checks bullet length, summary, schema) | `fluxjob_run.py` |
| render_pipeline.py not wired | Orchestrator calls it after QC pass | `fluxjob_run.py` |

## What Claude workers must output

`resume_data.json` schema (see `FLUXJOB_PIPELINE_NOTES.md` for full spec):
```json
{
  "_tailored_for": { "jd_company": "", "jd_title": "", "jd_score": 0 },
  "name": "Tanzim Ozer",
  "contact": { "email": "", "phone": "", "location": "", "linkedin": "" },
  "summary": "",        // ≤220 chars, P1-P12 protocol
  "skills": [],         // 6 core + ≤15 swap = 21 max
  "experience": [{ "title": "", "company": "", "location": "", "dates": "", "bullets": [] }],
  "education": [{ "degree": "", "school": "", "dates": "" }],
  "certifications": [],
  "projects": [{ "name": "", "description": "" }]
}
```

## QC gate rules (in fluxjob_run.py)

- Summary ≤220 chars
- Bullets: 100-117 chars (errors above 117, warning below 100)
- Max 4 bullets per role
- Max 21 skills
- All required keys present

## Commands

```bash
python fluxjob_run.py --top 5           # top 5 by score
python fluxjob_run.py --dry-run --all   # preview
python fluxjob_run.py --qc-only --top 5 # validate existing outputs
python fluxjob_run.py --render-only --top 5  # render without re-generating
```

## Key constraint: content/render separation

Claude's ONLY job: JD + compiled context + profile → `resume_data.json`
Python's ONLY job: `resume_data.json` → 4 format outputs

Claude never makes a formatting decision. Python never makes a content decision.
