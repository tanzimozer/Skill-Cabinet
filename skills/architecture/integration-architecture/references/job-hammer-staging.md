# Job Hammer: Staging Pipeline

**Status:** Stage 1 complete (49 jobs, June 5, 2026); Stage 2 awaiting scope definition

## Pipeline Overview

```
STAGE 1: Crawl & Score
  ├─ Crawl job boards (Indeed, LinkedIn, Greenhouse, Lever, BuiltIn)
  ├─ Extract: title, company, url, description, salary (if available)
  ├─ Score each job (68–83 scale, relevance to user profile)
  └─ Output: CSV with deduplicated jobs

STAGE 2: Resume Matching & Tailoring
  ├─ Match 48–50 jobs against user resume
  ├─ Identify required skills per job (extract from JD)
  ├─ Tailor resume sections (skills, experience, keywords)
  ├─ Generate application-ready resume variants
  └─ Output: Matched jobs + tailored resumes

STAGE 3: Application Workflow (Optional)
  ├─ Submit applications (Greenhouse, Lever APIs)
  ├─ Generate cover letters (Claude)
  ├─ Track submissions to Google Sheets
  └─ Schedule follow-ups
```

---

## Stage 1 Output (Current)

**Location:** `/tmp/JOB_HAMMER-personal/Stage_1_Crawl/output/jobs.csv`

**Columns:**
- id (unique, dedup-safe)
- title
- company
- url
- source (Indeed, LinkedIn, etc.)
- salary_min / salary_max (if available)
- jd_raw (full job description)
- score (68–83, relevance ranking)
- crawled_at (ISO timestamp)

**Example Top Scores:**
- Operations Specialist (UW): 83
- Project Coordinator (BioTrailMed): 81
- (48 more jobs)

**Deduplication Logic:**
- Hash on (title, company, url)
- Compare against Master tab in Google Sheets
- Append only net-new jobs
- Never delete existing records

---

## Google Sheets Integration

### Master Tab Columns
```
Job ID | Title | Company | URL | Source | Salary | Score | Crawled At | Status
```

### Dated Tabs (Per Crawl)
Naming format: `Jun-05-YYYYMMDD-HHMMSS`  
Contents: Full crawl output (dedup'd) + linked to individual job tabs

### Individual Job Tabs (Per Role)
One tab per job (created on first crawl mentioning that role)  
Columns:
- Job Posting (title, company, url, score)
- Job Description (full text)
- Extracted Skills (AI-parsed from JD)
- Match Status (Not Started | Matched | Tailored | Applied | Rejected)
- Resume Version (link to tailored DOCX)
- Application Status (Submitted | In Review | Interview | Offer | Rejected)

---

## Stage 2 Scope Options (User to Choose)

### Option A: Resume Matching Only
- Match each job against user resume
- Extract required skills from JD
- Identify skill gaps
- Flag top-3 matches
- Output: Scored matches + skill gap analysis

### Option B: Tailoring + Export
- Option A + tailor resume per job
- Generate DOCX/PDF variants
- Export 48 resumes (one per job) to Drive folder
- Generate cover letter templates
- Output: Matched jobs + tailored resumes

### Option C: Full Automation
- Option B + submit applications
- Use Greenhouse/Lever APIs for quick-apply
- Generate personalized cover letters (Claude)
- Track submissions in Sheets
- Schedule reminders (Hermes cron)
- Output: 48 applications submitted, tracked, reminded

---

## Technical Implementation

### Resume Tailoring Algorithm
1. **Extract JD keywords** (Claude)
   - Required skills (hard skills, soft skills)
   - Experience level (years, seniority)
   - Industry/domain focus
   
2. **Match against user resume**
   - Find existing experience that covers requirement
   - Identify new skills to highlight
   - Spot gaps (if any)
   
3. **Tailor sections** (Claude + template)
   - Rewrite "Professional Summary" to match JD
   - Reorder experience sections (most relevant first)
   - Inject matched keywords
   - Preserve integrity (no exaggeration)
   
4. **Export variants**
   - DOCX (Microsoft Word)
   - PDF (for submission)
   - LaTeX (for control)
   - Text (fallback)

### JD Column Extraction (Commit 806b523)
- Claude parses raw HTML JD
- Extracts: title, company, salary, skills, experience level, job level
- Stores in individual job tab
- <2min per job (parallelized across 48 jobs)

---

## Data Model

```python
class JobMatch:
    job_id: str                    # Master tab row ID
    title: str                     # Job title
    company: str                   # Company name
    url: str                       # Application URL
    jd: str                        # Full job description
    extracted_skills: List[str]    # AI-parsed required skills
    user_resume_skills: List[str]  # User's existing skills
    skill_gap: List[str]           # Skills user lacks
    match_score: float             # 0.0–1.0 (% overlap)
    tailored_resume: bytes         # DOCX content
    cover_letter: str              # Personalized letter
    application_status: str        # Not Started, Submitted, etc.
    submitted_at: datetime         # Application timestamp
    reminder_sent_at: datetime     # Last follow-up
```

---

## Next Actions

**User Decision Required:**
Which Stage 2 option?
- [ ] Option A: Resume matching only
- [ ] Option B: Matching + tailoring + export
- [ ] Option C: Full automation (match + tailor + submit + track)

**Once chosen:**
1. Define resume template (what sections to tailor)
2. Set skill extraction rules (what counts as "required skill")
3. Tune match score algorithm (weighting)
4. Decide on cover letter tone/style
5. Set application submission preferences (Greenhouse only? All APIs?)

---

## Known Limitations

- **Source APIs flaky:** Indeed has throttling; LinkedIn blocks scrapers; BuiltIn has rate limits
- **JD parsing variance:** Different job board HTML structures; OCR fallback for PDFs not yet built
- **Salary extraction low:** 60% of postings include salary; gaps common
- **Resume tailoring risk:** Over-customization can reduce authentic signal; using conservative word-injection approach
- **Application submission:** Only Greenhouse/Lever APIs built; LinkedIn/Indeed/BuiltIn manual entry required

---

**Referenced by:** `integration-architecture` (Job Hammer section)  
**Stage 1 Status:** Complete (49 jobs)  
**Stage 2 Status:** Awaiting user scope decision  
**Last Updated:** June 5, 2026
