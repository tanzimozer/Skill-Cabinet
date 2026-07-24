# FLUXJOB Efficiency Patterns
_Lessons from June 2, 2026 optimisation session_

## Architecture

```
Stage 1: Crawl → jd_packets/ (unchanged)
         ↓
Stage 2: fluxjob_run.py
         ├─ Load COMPILED_CONTEXT.md once (288 lines vs 1,413 raw)
         ├─ Fan out N parallel Claude workers (ThreadPoolExecutor, max 6)
         │   └─ Each: reads JD packet → outputs resume_data.json ONLY
         ├─ Quality gate (validates in-memory dict — no disk re-read)
         └─ Single render pass → render_pipeline.py → 4 formats per job
         ↓
Stage 3: tanzim_app_orchestrator_6of6.py (unchanged)
         ↓
Stage 4: fluxjob_sheet_sync.py
         ├─ _get_access_token() — cached, TOKEN_TTL_SEC=3300
         ├─ _get_or_create_folder() — cached after first lookup
         ├─ upload_to_drive() per job
         └─ batch_update_sheet() — ONE call for all jobs
```

## Key Files (FLUXJOB repo)

| File | Purpose |
|------|---------|
| `fluxjob_run.py` | Main orchestrator |
| `fluxjob_sheet_sync.py` | Drive upload + Sheet batch write |
| `Stage_2_Resume_Tailoring/FLUXJOB_CONTEXT_COMPILED.md` | 288-line compiled spec |
| `Stage_2_Resume_Tailoring/FLUXJOB_CLAUDE_WORKER_PROMPT.md` | Worker brief |
| `Stage_3_Application/FLUXJOB_PIPELINE_NOTES.md` | Schema + gap analysis |

## resume_data.json Schema (required fields)

```json
{
  "_tailored_for": {"jd_company": "", "jd_title": "", "jd_score": 0},
  "name": "Tanzim Ozer",
  "contact": {"email": "", "phone": "", "location": "", "linkedin": ""},
  "summary": "≤220 chars",
  "skills": ["string"],
  "experience": [{"title":"","company":"","location":"","dates":"","bullets":[]}],
  "education": [{"degree":"","school":"","dates":""}],
  "certifications": ["string"],
  "projects": [{"name":"","description":""}]
}
```

## Quality Gate Rules

| Check | Limit | Fail = blocked |
|-------|-------|---------------|
| Summary | ≤220 chars | Yes |
| Bullet length | ≤117 chars | Yes |
| Bullets per role | ≤4 | Yes |
| Skills count | ≤21 | Yes |
| Bullet underfill | <100 chars | Warning only |

## Token Reduction Strategy

The compiled context approach:
- Raw: 8 spec files × ~176 lines avg = 1,413 lines
- Compiled: 288 lines (strip rationale, comments, changelog, examples)
- Saving: ~75% per worker call
- For 50 jobs × 6 workers: saves ~millions of tokens per run

## DO NOT Modify

`TERRAjob.V2-personal` is the source-of-truth repo. Never modify it.
All changes go in `FLUXJOB` only. Tanzim's explicit rule.
