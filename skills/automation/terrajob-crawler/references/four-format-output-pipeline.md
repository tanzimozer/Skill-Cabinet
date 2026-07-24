# TerraJob 4-Format Output Pipeline (June 2026)

## File: `Stage_2_Resume_Tailoring/output_pipeline.py`

Generates all 4 resume formats in one command. Confirmed working June 2, 2026.

## Quick Run

```bash
cd /tmp/TERRAjob.V2-personal/Stage_2_Resume_Tailoring
python output_pipeline.py \
  --job "Brex_DataAnalyst" \
  --title "Data Analyst II" \
  --company "Brex" \
  --profile tanzim_resume_profile_4of8.json \
  --out output/formatted
```

## Output per job

```
output/formatted/<job_id>/
  Ozer_Tanzim_<Company>_Resume.pdf         # WeasyPrint HTML→PDF
  Ozer_Tanzim_<Company>_Resume.docx        # python-docx ATS-safe
  Ozer_Tanzim_<Company>_Deedy.pdf          # XeLaTeX two-column
  Ozer_Tanzim_<Company>_Deedy.tex          # Source .tex (kept for inspection)
  Ozer_Tanzim_<Company>_CoverLetter.docx   # python-docx cover letter
```

## Format Details

### Format 1: PDF (WeasyPrint)
- Generator: `weasyprint.HTML(string=html).write_pdf()`
- Fonts: Lato (installed on hermes VM at `/usr/share/fonts/truetype/lato/`)
- Layout: single-column, 8.5"×11", 0.5" margins, spec-compliant
- Size: ~18-25KB typical

### Format 2: DOCX (python-docx)
- ATS-safe structure
- Bullets via `List Bullet` style
- Section headers with bottom border via OxmlElement
- Pipe separators: dark `#666666`, light `#999999`
- Size: ~36-40KB typical

### Format 3: Deedy LaTeX PDF
- Compiler: `xelatex -interaction=nonstopmode`
- Template: `deedy_template.tex` (in same dir as output_pipeline.py)
- Class file: `deedy-resume-openfont.cls` — auto-downloaded from GitHub on first run
  - URL: `https://raw.githubusercontent.com/deedy/Deedy-Resume/master/OpenFonts/deedy-resume-openfont.cls`
  - Fallback: minimal Lato-based class written inline if network fails
- Two-column layout (0.33 / 0.66 split)
- Font: Lato via XeLaTeX fontspec
- Size: ~6-10KB typical (sparse LaTeX PDF)

### Format 4: Cover Letter (python-docx)
- Margins: 1.0" top/bottom, 1.25" left/right
- Auto-personalised using `company`, `job_title`, and `top_wins` from profile
- Tone: professional, first-person, 4 paragraphs

## Known Pitfalls

### LaTeX template string pitfall
**NEVER** use Python `r"""..."""` or `"""..."""` for LaTeX template strings containing `%`.
The `%` character triggers Python's `%s`-style string formatting → `ValueError: unsupported format character`.

**Correct approach:** Write template to a separate `.tex` file, use `.replace("%%PLACEHOLDER%%", value)`.

### Deedy class escape chars
LaTeX special chars must be escaped before insertion: `& % $ # _ { } ~ ^ \`
Use an `esc()` function — do not insert raw profile data into .tex.

### XeLaTeX compile output
- Compiled PDF lands in same dir as `.tex` file with same basename
- xelatex also writes `.aux`, `.log`, `.out` — clean these up if desired
- If compile fails silently (exit 0 but no PDF), check `result.stderr[-300:]`

## Dependencies (all confirmed on hermes VM)

```bash
which xelatex   # /usr/bin/xelatex (texlive-xetex)
python3 -c "import weasyprint"   # OK
python3 -c "import docx"         # OK (python-docx)
fc-list | grep -i lato            # Lato font present
```

## Profile Field Mapping

The pipeline reads from the same profile JSON as the resume engine.
Fields used:

```python
profile['name']           # "Tanzim Ozer"
profile['email']
profile['phone']
profile['location']       # "Seattle, WA"
profile['linkedin']
profile['summary']        # string, ≤220 chars recommended
profile['skills_core']    # list[str]
profile['skills_swap']    # list[str]
profile['experiences']    # list[{title, company, location, dates, bullets:[str]}]
profile['education']      # list[{degree, school, dates}]
profile['certifications'] # list[str] OR list[{name:str}]
profile['projects']       # list[{name, description}]
profile['top_wins']       # list[str] — used in cover letter body
```

## Test Run Results (June 2, 2026)

Test profile: manually constructed from known resume data.
Output uploaded to Drive:
- PDF: https://drive.google.com/file/d/1dnEiM8-xWAOXA7vQFJ3VhDDwcJMev_Xv/view
- DOCX: https://drive.google.com/file/d/1oVNS-1WunQ0pQEmh7J6o4ze-dHmQTG_7/view
- Deedy: https://drive.google.com/file/d/1MupVvZNeA5LcVOcVjuNccjZQ2a-TxNRp/view
- Cover Letter: https://drive.google.com/file/d/1noTvKsJr9I1AksaRHzCE8-uhWzFFQN71/view

Note: Deedy PDF at 6KB indicates minimal rendering — full two-column aesthetic requires the real `deedy-resume-openfont.cls` (auto-downloads on first run with internet access).

## Next Steps (not yet built)
1. Wire `output_pipeline.py` into `pipeline.py run --top N` command
2. OAuth-swap in `drive_upload.py` (currently expects service account)
3. Auto-write Drive link + status to Google Sheet on `submitted`
4. Callback signal loop (learn from phone_screen/interview outcomes → boost similar roles in next crawl)
