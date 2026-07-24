---
name: timbr-essentials-series
description: Production system for the TIMBR Essentials Series — the 22-page, single-muscle, $24.99 premium training-encyclopedia volumes (CHEST flagship, cloned to BACK/SHOULDERS/etc.). Covers the build spec, char-locks, Canva element-ID map, voice rules, and the governing Google Sheets.
version: 1.0.0
tags: [TIMBR, essentials-series, canva, google-sheets, magazine, ebook]
related_skills: [timbr-context, timbr-magazine-production, canva-integration, google-sheets-data-ops]
---

# TIMBR Essentials Series

The Essentials Series is DISTINCT from the Workout Series (see `timbr-magazine-production`, which is the 8-page Seattle 9-to-5 product). Essentials = **one muscle per volume, 22 pages, 559×794 px A4 portrait, $24.99 premium "training encyclopedia."** Flagship = CHEST; every other volume is a 1:1 CLONE of the CHEST Canva design, repopulated.

Series: ES1 CHEST · ES2 BACK · ES3 SHOULDERS · ES4 TRICEP · ES5 BICEPS · ES6 CORE · ES7 GLUTES · ES8 HAMSTRING · ES9 QUADS · ES10 CALVES.

## Single Source of Truth (canonical sheet)

**"Essentials Template"** — `1b1i8tIQOTRm9dT6_uRhgJYLM3hO3xSiiHVpEVIIC6Js` (built 2026-06-24, merged from the two prior files below). One file, whole series. Tabs:
- README · ESSENTIAL SERIES (index) · SERIES VOLUMES (10-volume map: hooks, Canva IDs, TOCs) · TEMPLATE (full build & replication spec — spine, char-locks, element-ID map, workflow) · DESIGN PRINCIPLES · EDITORIAL & VOICE · READING-FLOW · RESEARCH METHOD · PRODUCTION FLOW · ES1-CHEST QA · ES2-BACK QA.

Prior source files (superseded — Essentials Template wins):
- ES template/QA (latest, governed overlap): `1XzddeLZ86EQllM6QyMvQdw8pawS7faAwdXGKyPbDVDo`
- Master Doc (older): `1EI191dM58n3nlmE5TWKiEqaywCQKZCTSzX2-i_c8zwo`
- BACK manuscript & build pack: `1m6rjXYkQXrw3LLH9tKibfYJ2-0jZ6HZ7rzm3TiQwgLc`

## The Non-Negotiables

1. **Clone, don't build.** Always duplicate the CHEST design (`DAG3tQ6_cn8`); never recreate pages. Element + page IDs are IDENTICAL across clones, so the ID map (Template tab §12) works for every volume.
2. **Never break the layout.** Owner-built, owner-locked. Every edit works backward from the existing box — fill the box, don't reshape the page.
3. **Char-lock to the decimal.** Each text block sits in a fixed-size box. Replacement copy must render ≤ the existing block's char count / auto-height. Measure before, report before→after, never ship overflow. Budgets per block live in Template tab §9. Locked dims: footer H=10.8889; TOC title box W=292.439/H=15.4667; TOC number box W=62.153/H=18.36.
4. **API can't do structural changes.** Canva API rewrites/formats EXISTING element text but CANNOT create/duplicate/delete/reorder elements or pages. Those are MANUAL owner actions. Hand the owner a bare numbered task list — steps only, no rationale.
5. **Continuous folios.** Content pages run 06→18; the 2 pull-quote spreads are UNCOUNTED; one near-end page is intentionally EMPTY. Lock TOC numbering LAST.
6. **Blockless.** Never classify by push/pull/legs. Organize by anatomical region.
7. **50/50 audience.** Every volume reads equally for men and women. Series Intro MUST carry the dual-goal line ("Master them, and the shape follows — [male outcome], or [female outcome], same training."). Women woven through, not siloed in the FAQ.

## Canva Design IDs (per volume)

CHEST `DAG3tQ6_cn8` (flagship/template) · BACK `DAHNQG42OA0` · SHOULDERS `DAHNQzWU73E` · TRICEPS `DAHNRKr665I` · BICEPS `DAHNRHOo0jw` · GLUTES `DAHNRVwjEDs` · HAMSTRINGS `DAHNRStLACo` · QUADS `DAHNRW80JUE` · CALVES `DAHNRmGDc8A`. (Full hooks/marquees/TOCs in the SERIES VOLUMES tab.)

## 22-Page Spine (physical → role → folio)

P1 Cover (01) · P2 Manifesto (tonality reference, shared) · P3 Disclaimer (shared verbatim) · P4 Series Intro (carries dual-goal line) · P5 TOC (13 rows) · P6 Blueprint (06) · P7 Workout (07) · P8 Fundamentals (08) · P9 Rest Well (09) · P10 Before You [Verb] (10) · P11 Pull-quote (uncounted, tees marquee) · P12 Marquee deep-dive (11, conversion hero) · P13 Numbers Stall (12) · P14 Anatomy (13) · P15 Pull-quote (uncounted) · P16 Eat to Grow (14) · P17 Feel It (15) · P18 FAQ + Women (16) · P19 Why It Won't Grow (17) · P20 Sessions Gym/Home (18) · P21 EMPTY (kept) · P22 Back cover.

## Voice (seasoned-coach)

Honesty over hype, reader autonomy over obedience, earned-not-given. Second person, short declaratives + one rolling sentence per para, contractions, plain words. NO exclamation points, NO emojis, NO hype adjectives. **Never say:** shredded, jacked, blast, torch, secret, hack, magic, bro, spot-reduce (except to debunk). **Say:** lean, honest, earned, bias, full range, a season, hard sets, the part you skip. Signature devices: "[Part] isn't genetics. It's a [angle/stretch]." · "Bias, not balance." · "Train the movement, not the room." · "Give it an honest run before you judge it."

## Editorial Thesis — "Lead with what you skip"

Every volume leads with the ONE region people under-train; the whole deck (marquee, anatomy, workout order) is built around it. CHEST → upper chest (~30° incline). BACK → lats/width/V-taper. SHOULDERS → side delts. TRICEP → long head. BICEP → the peak. GLUTES → glute med ("the shelf"). HAMSTRING → the stretch (RDL). QUADS → the sweep (deep squat). CALVES → soleus (seated).

## Canva read/write

Reading: Canva API can't return text directly for export-reads — but the **start-editing-transaction** (3-call model: start → perform-editing-operations → commit) returns the full scan (every element's richtext, position, box dims). See `canva-integration` / `timbr-magazine-production` for the PDF-export read path and token-refresh pattern. Browser tools time out on Canva — use the API or have the owner export a PDF.

Reading a delivered PDF for review: render pages to PNG with `pdftoppm`, then read. Canva PDFs export text as outlines, so `pdftotext` returns empty — rely on the rendered images, not text extraction.

## Merging series Google Sheets (the 2026-06-24 task)

When asked to consolidate multiple series sheets into one:
1. **Establish recency first** — pull `createdTime`/`modifiedTime` via Drive API. "Latest wins" on overlap; only fold in what older files uniquely contain.
2. Build the new spreadsheet with all tabs at creation (`spreadsheets.create` with a `sheets` array), then `values.batchUpdate` RAW per tab.
3. Format pass: freeze row 1, bold+dark header, `wrapStrategy=WRAP`, explicit column widths.
4. Add a README tab stating the merge rule and source IDs so provenance survives.
OAuth: keyless via `/home/hermes/.hermes/google_token.json` → `Credentials.from_authorized_user_info`.

## Known open bugs (BACK, as of 2026-06-24 — recorded, not fixed)

From ES2-BACK QA tab: P11 pull-quote says "frame" not "genetics" (wrong format — must follow "[part] isn't genetics. It's a [x]"); Manifesto muscle-word ("how the back is built"); text-block left-alignment off across most pages (header/subheader/closing paras not aligned to body left margin); footer page-name+folio misaligned across all pages (recurring); some bodies overflowing at bottom (P8, P13, P14, P18, P19). These are owner-side alignment/layout fixes.

## Tanzim's working style on this project

- **One question at a time.** When clarifying, ask a single question and wait — do not stack 3 questions in one message. He said so explicitly.
- He talks through the *why* before authorizing a build (delegation/boredom discussion preceded the merge). Read the friction, name it, then move when he commits.
- He delegates execution (to Towsif) but guards the standard — the labour is handed off, the vision is not.
