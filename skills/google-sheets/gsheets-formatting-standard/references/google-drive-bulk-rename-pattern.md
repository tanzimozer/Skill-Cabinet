# Google Drive — Bulk File Rename Pattern (from 2026-07-23 session)

## Task: Identify and rename scanned exam pages in a Drive folder

### Problem
60 scanned JPG pages (`Pg 1.jpg` → `Pg 60.jpg`) contain multiple Cambridge exam papers concatenated. Need to:
1. Identify which physical pages belong to which paper (find cover pages)
2. Rename files with meaningful names e.g. `English_Mock_2025_P1`

### Approach

**Step 1 — List folder contents**
```python
files = drive.files().list(
    q=f"'{FOLDER_ID}' in parents and trashed=false",
    fields="files(id, name, mimeType)",
    orderBy="name"
).execute()
```
Note: `orderBy="name"` sorts alphabetically, so Pg 10 comes before Pg 2. Sort by number in Python after fetching.

**Step 2 — Download sample pages and vision-scan for cover pages**
- Download every 5th page first to find approximate boundaries
- Then download the ±2 pages around each boundary to pin the exact start
- Use `browser_navigate(url=f"file:///tmp/exam_pages/{name}.jpg")` then `browser_vision()` to read cover page details

**Step 3 — Vision prompt that works**
```
"Is this a cover page of a Cambridge exam paper? What is the EXACT paper code 
(like 1123/11 or 1123/21), year, session (May/June or Oct/Nov)? 
What page number is visible at the bottom?"
```
Vision reliably reads: paper code, year, session, compiled-book page number.

**Step 4 — Confirm naming convention with user BEFORE renaming**
Clarify: does P1/P2/P3 mean:
- Sequential part number (Part 1, Part 2 of the compiled book)?
- Paper type (Paper 1 Reading / Paper 2 Writing)?
- Something else?

**Step 5 — Rename via Drive API**
```python
drive.files().update(
    fileId=file_id,
    body={"name": "English_Mock_2025_P1"}
).execute()
```

### Cambridge 1123 paper code cheat sheet
- `1123/11` = Paper 1 Reading (variant 1) — Oct/Nov
- `1123/12` = Paper 1 Reading (variant 2) — Oct/Nov  
- `1123/21` = Paper 2 Writing (variant 1) — Oct/Nov
- `1123/22` = Paper 2 Writing (variant 2) — May/Jun
- INSERT = separate reading passage booklet (4 pages), no marks, accompanies Q paper

### What we found in this session (2025 O/N paper book, ~60 pages)
Approximate boundaries (cover pages at):
- Pg 1–4:   2025 Oct/Nov Paper 1 INSERT
- Pg 5–15:  2023 Oct/Nov Paper 1 Q Paper (1123/11)
- Pg 16–22: 2025 Oct/Nov Paper 1 Q Paper (1123/12)
- Pg 23–30: 2025 Oct/Nov Paper 2 Q Paper (1123/21)
- Pg 31–34: 2025 May/Jun Paper 1 INSERT
- Pg 35–45: 2022 May/Jun Paper 1 Q Paper
- Pg 46–52: 2019 May/Jun Paper 1 Q Paper (1123/12)
- Pg 53–60: 2022/23 Paper 2 Q Paper
(Boundaries approximate — session ended before full confirmation)

### Pitfall — sorting
`orderBy="name"` in Drive API sorts Pg 10 before Pg 2. Sort in Python:
```python
files_sorted = sorted(files, key=lambda f: int(f['name'].replace('Pg ', '').replace('.jpg','')))
```
