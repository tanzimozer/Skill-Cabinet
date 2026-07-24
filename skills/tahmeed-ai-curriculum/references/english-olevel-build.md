# English O-Level (1123) — Study-Tab & Execution-List Build (Jun 2026)

Built on Tanzim's request: a per-subject study tab + a free-materials-first execution
checklist, on the **"Tahmeed's Library"** sheet (NOT the "Tahmeed profile" sheet).

## Sheet IDs — keep distinct (easy to confuse)
- **Tahmeed's Library** = `1s3wVx3532huo2kBroyLPM6VLxRYs-Aklr5PGACLLNmc` — the course/study tracker.
  Note: the URL Tanzim pastes sometimes has a one-char typo (`Akir` vs `Aklr`). The
  correct ID ends `...Aklr5PGACLLNmc`. Always resolve by trying the variant + reading the
  title back before writing.
- **Tahmeed profile** = `19v5x4oScpEPXkjHBWvt97UHtWChki5UGniJvop258bc` — the AI-curriculum sheet.

## Cambridge O Level English Language — 1123 facts (verified live)
- **Sitting → syllabus mapping:** Oct/Nov 2026 = **2024–2026 syllabus**. 2027+ sittings use
  the 2027–2028 syllabus (spec changes). Confirm sitting year before picking the PDF.
- **Syllabus PDF (2024–2026):** `https://www.cambridgeinternational.org/Images/634453-2024-2026-syllabus.pdf`
- **Structure:** two papers, 2 hrs each, 50% each, grades A*–E.
  - Paper 1 — Reading: structured + extended questions on two texts (comprehension, summary,
    writer's effect, inference, facts vs opinion).
  - Paper 2 — Writing: directed writing + composition. **Six text types to drill: email,
    letter, report, article, speech, summary.** Composition: narrative / descriptive /
    argumentative.
- **No set literature texts** — one of the lighter O-levels to self-prep.

## The endorsed textbook (the one paid item in the whole plan)
- **Cambridge O Level English Language Student's Book (2nd ed.)** — Reynolds & Acres,
  Hodder Education / Hachette Learning. Officially Cambridge-ENDORSED for 1123.
- Print ISBN **9781398360235** (~£29) · eBook ISBN **9781398361027**.
- Publisher page: `https://www.hachettelearning.com/english/cambridge-o-level-english-language-second-edition`
- Note: hoddereducation.com now 301-redirects to hachettelearning.com; old Hodder product
  URLs 404. cambridge.org education pages 403 a bare curl — verify via the Hachette page +
  isbnsearch.org instead.

## Free materials (everything except the textbook)
- All YouTube teaching videos — free. Verify each via the oEmbed endpoint, NOT a bare curl
  (YouTube returns 200 for dead videos):
  `curl -sL "https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v=<ID>&format=json"`
  — a live video returns JSON with a title; dead → 401/404.
- Past papers (free): Cambridge official 1123 past-papers page, GCE Guide
  (`gceguide.com`), PapaCambridge (`pastpapers.papacambridge.com/papers/caie/o-level-english-1123`),
  Save My Exams (mostly free). Verify each with `curl -sIL -w "%{http_code}"`.
- **Don't link pirated textbook PDFs** even when asked if it's "all free" — say plainly the
  book is the one paid item and offer a legitimate cheaper route (regional pricing / aligned
  free alt text) instead.

## Registration / fee facts (British Council Bangladesh)
- Private candidate, single subject. **Site is bot-blocked** (`000`/empty from curl) — could
  NOT pull live fee/deadline this session. Do not fabricate a precise number.
- Working estimates (mark as TO-CONFIRM in any sheet): registration fee ~**BDT 13,000–16,000**
  single subject; Oct/Nov 2026 standard registration deadline typically **early–mid August**.
- When Tanzim asks for a register-by task "15 days before the deadline," build it off the
  assumed deadline and FLAG that it shifts once the real date is confirmed on the portal.

## Build pattern that worked
- Used the Google Sheets API via `~/.hermes/google_token.json` (see SKILL.md "Writing to his
  sheets" section) — added tab, wrote rows with `=HYPERLINK(url,text)` formulas, then applied
  banner/merge/header formatting in a second `batchUpdate`.
- Columns Tanzim wanted on a study tab: Section · Item/Topic · Material(link) · **Notes for
  Tahmeed** · **Notes for Friday**. The two notes columns are a standing preference.
- **Banner row-index pitfall:** blank spacer rows between sections throw off the 0-indexed
  banner/merge row math — banners landed 1–2 rows off twice this session. Always read column
  A back after formatting and correct misplaced banners before declaring done.
- Honest-flag discipline: most "writer's effect"/composition videos are IGCSE 0500-framed,
  not 1123-branded (same skill). Mark which are genuinely 1123-specific in the Friday-notes
  column rather than passing them off as 1123.
