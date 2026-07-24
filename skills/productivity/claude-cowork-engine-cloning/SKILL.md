---
name: claude-cowork-engine-cloning
description: "Clone and adapt a structured Claude Cowork prompt engine (multi-file package) for a new user — parse their resume, build their profile JSON, adapt all engine files, and deliver a ready-to-use zip."
tags: [claude, cowork, resume, engine, horcrux, equinox, onboarding, profile, json]
---

# Claude Cowork Engine Cloning

## When to Use
- User asks to clone an existing Claude Cowork "engine" (multi-file project bundle) for a new person
- User provides a source engine folder (e.g. HORCRUX) and a new user's resume
- User wants a named variant (e.g. EQUINOX) with the same architecture but a different profile
- General pattern: *adapt a structured AI prompt package from one user's profile to another's*

## What a Claude Cowork Engine Looks Like

Standard structure (HORCRUX/EQUINOX pattern):
```
ENGINE_NAME/
├── 01_readme_user.md (or named readme)   ← user-facing guide, NOT uploaded
├── 02_claude_instruction.md              ← paste into Cowork Custom Instructions, NOT uploaded
└── Claude Cowork Uploads/                ← everything here gets uploaded to Cowork
    ├── 03_purpose.md                     ← engine mission, rules, test contracts
    ├── 04_layout.md                      ← visual/output spec (fonts, geometry, spacing)
    ├── 04b_deedy_layout.md               ← secondary visual format spec
    ├── 05_soul.md                        ← decision-making logic, scoring psychology
    ├── 06_user_data.json                 ← user profile (THE key file to rebuild per user)
    ├── 07_user_data.template.json        ← annotated schema (copy as-is)
    ├── 08_Master_References.docx         ← quality benchmark (copy or replace)
    └── deedy_essentials/                 ← shared assets (LaTeX cls + fonts, copy as-is)
```

## Two Categories of Files

**User-specific (must rebuild for new user):**
- `06_user_data.json` — full profile built from their resume
- `01_readme_user.md` (or named readme) — adapted for their name, role, workflow preferences

**Engine files (adapt via find/replace):**
- `02_claude_instruction.md`, `03_purpose.md`, `04_layout.md`, `04b_deedy_layout.md`, `05_soul.md`
- Replace: old name → new name, `LastName_FirstName` filename pattern, engine name (HORCRUX → EQUINOX)
- Keep ALL technical logic, pipeline specs, scoring rules, test contracts IDENTICAL

**Copy as-is:**
- `07_user_data.template.json`, `08_Master_References.docx`, `deedy_essentials/`

## Step-by-Step

### 1. Parse the new user's resume
```python
import docx
doc = docx.Document('resume.docx')
for para in doc.paragraphs:
    if para.text.strip():
        print(para.text)
```
Extract: contact info, role history (company, dates, title), bullets per role, skills/tools, education, certs.

### 2. Build 06_user_data.json
Key fields to populate from resume:
- `contact` — name, phone, email, city, linkedin (leave blank if not on resume)
- `target_role_family` + `secondary_role_family` — infer from current/recent roles
- `target_titles` — list 6-8 titles matching their background
- `years_experience` — compute from earliest role start to today
- `focus_phrases` — 6 phrases with keyword arrays (match their domain vocabulary)
- `achievements_pool` — 7 achievements extracted verbatim from resume bullets (with metrics)
- `core_skills` — 6 locked skills (their professional fingerprint)
- `swappable_skills` — 20-25 skills with keyword arrays (JD-scored per generation)
- `roles` — up to 4 roles, each with 14-bullet pool (4-6 source bullets + expanded variants)
- `brand_archetype_default` — one of: builder, optimizer, operator, translator, closer
- `default_voice_register` — one of: industrial, tech, banking, healthcare, customer_success, government
- `title_differentiators`, `brand_triad_nouns` — per archetype, 2-3 options each
- `banned_openers`, `banned_closers`, `density_filler_words` — copy from template

**Bullet pool expansion rule:** Source bullets go in verbatim. Expand to 14 by generating variants covering different angles (scope, efficiency, stakeholder, compliance, delivery). Every bullet ≤122 chars, no wrap.

**Closer bullet rule:** Each role needs exactly one `"closer": true` bullet — their narrative anchor (a ranking, a recognition, a transformation arc).

### 3. Create directory structure
```python
import os
base = f"/home/hermes/{ENGINE_NAME}"
os.makedirs(f"{base}/Claude Cowork Uploads/deedy_essentials", exist_ok=True)
```

### 4. Adapt engine files (find/replace pattern)
```python
adapted = (source_text
    .replace("OLD_ENGINE_NAME", "NEW_ENGINE_NAME")
    .replace("OldLastName_OldFirstName", "NewLastName_NewFirstName")
    .replace("Old Full Name", "New Full Name")
    .replace("OldFirstName's", "NewFirstName's")
    .replace("OldFirstName", "NewFirstName")
)
```
Apply to: 02, 03, 04, 04b, 05. Write to their destination paths.

### 5. Copy shared assets
```python
import shutil
cache = "/home/hermes/.hermes/document_cache"
shutil.copy(f"{cache}/doc_XXXXX_07_user_data.template.json", f"{uploads}/07_user_data.template.json")
shutil.copy(f"{cache}/doc_XXXXX_08_Master_References.docx", f"{uploads}/08_Master_References.docx")
shutil.copy(f"{cache}/doc_XXXXX_deedy-resume-openfont.cls", f"{deedy}/deedy-resume-openfont.cls")
```

### 6. Write the user README
Adapt the readme for the new user:
- Their name in the title and profile section
- Their role family, core skills, brand archetype, years of experience
- File naming convention using their LastName_FirstName
- Keep all setup steps (3 steps) identical in structure

### 7. Zip and deliver
```python
import zipfile, os
with zipfile.ZipFile(f'/home/hermes/{ENGINE_NAME}.zip', 'w', zipfile.ZIP_DEFLATED) as zf:
    for root, dirs, files in os.walk(f'/home/hermes/{ENGINE_NAME}'):
        for file in files:
            fp = os.path.join(root, file)
            zf.write(fp)
```
Send zip as MEDIA attachment.

## Known Instances

| Engine | User | Profile | Location |
|---|---|---|---|
| HORCRUX | Tanzim Ozer | Project/Implementation Manager, 8 yrs, Seattle | `/home/hermes/HORCRUX` (source files in doc_cache) |
| EQUINOX | Zara Sadia Mondale | Customer Success / Research Coordinator, 6 yrs, Seattle | `/home/hermes/EQUINOX` |

## Pitfalls
- **Subagent timeout:** Writing 5 files via delegate_task timed out at 600s. Do it directly with mcp_execute_code instead — read all source files, do string replacements in Python, write outputs.
- **Name replacement order matters:** Replace full name first ("Tanzim Ozer"), then possessive ("Tanzim's"), then first name alone ("Tanzim"). Reverse order causes partial replacements.
- **Filename pattern:** Source engine uses `LastName_FirstName` format in filenames — match exactly (e.g. `Mondale_Zara`, not `Zara_Mondale`).
- **07 template:** Copy as-is — it's a schema reference, not user-specific. No adaptation needed.
- **08 Master References:** Copy from source until new user's custom masters are built. Flag in readme that this is a placeholder.
- **deedy_essentials fonts:** Not in the doc_cache (only the .cls was shared). Note in the readme that fonts need to be added before Deedy PDF will compile. The .cls alone is not enough.
- **zip command not available:** Use Python's zipfile module instead of shell zip.
- **06_user_data.json bullet count:** Must be 14 bullets per role. Source resume usually has 4-6 — generate the remainder as variants (different angles, no fabrication).

## Quality Check Before Delivering
- [ ] 06_user_data.json has 4 roles, 14 bullets each, at least one `"closer": true` per role
- [ ] All engine files have no leftover references to the original user's name
- [ ] File naming convention matches new user's `LastName_FirstName`
- [ ] README uses new engine name throughout
- [ ] deedy_essentials/ folder present (even if fonts missing — note it)
- [ ] Zip builds without errors and contains full directory tree
