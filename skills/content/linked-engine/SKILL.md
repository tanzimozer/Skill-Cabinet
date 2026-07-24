---
name: linked-engine
description: Autopilot LinkedIn article engine. Researches a topic, fills all variables, renders PDF + PNG + caption .docx, logs to Linked_Posts.csv. Trigger word is "Generate" (with optional topic/palette).
category: content
tags: [linkedin, content, articles, pdf, png]
---

# Linked Engine — Autopilot LinkedIn Article System

## Location
`~/Linked_Engine/` — cloned from github.com/tanzimozer/Linked_Engine

If not present locally, clone it:
```bash
git clone --depth 1 https://github.com/tanzimozer/Linked_Engine.git ~/Linked_Engine
# or to /tmp for ephemeral use:
git clone --depth 1 https://github.com/tanzimozer/Linked_Engine.git /tmp/linked_engine
```

The repo includes `CLAUDE.md` with full system instructions — read it for the complete autopilot protocol.

## What it does
One command produces a fully-researched, fact-checked LinkedIn post:
- `{FILENAME}.pdf` — US Letter article (1 page, enforced)
- `{FILENAME}.png` — 300 DPI image for LinkedIn
- `{FILENAME}_caption.docx` — LinkedIn caption
- Appends a row to `Linked_Posts.csv` (Status=pending → n8n publishes)

## How to run

**As of Jun 2026: Mac crons are STOPPED. Tanzim triggers on-demand via WhatsApp/Friday.**

When he says "Generate" (or a topic), Friday runs the engine on the VM, renders the PNG + caption, and drops both directly into the WhatsApp chat. Do NOT wait for the Mac to run it. Do NOT post to LinkedIn — just deliver PNG + caption inline.

```bash
cd ~/Linked_Engine && python3 linked_engine.py
```

## Trigger phrases from Tanzim
- `Generate` — full autopilot, pick topic + palette automatically
- `Generate Article on [topic]` — autopilot on specific topic
- `Generate [lane]` — e.g. "Generate data infra"
- `Generate coral` — force palette
- Bare topic name → treat as trigger

**On-demand delivery flow:**
1. Edit variables in `linked_engine.py` directly (do NOT monkey-patch from a tmp script — caption DOCX won't regenerate correctly)
2. Run `python3 linked_engine.py` from `~/Linked_Engine/`
3. Send PNG via `/send-media` to `160799431606497@lid`
4. Paste caption inline in the same chat (do not rely solely on the DOCX)

## Autopilot flow (when triggered)
1. Read `article_tracker.json` → get next batch ID (LE###) + history (anti-repeat memory)
2. Pick lane + topic — NO repeats vs last 10 entries; pick different lane than most recent
3. Web research — concrete numbers, dates, named players, token/cost pricing
4. Verify trend + timing on LinkedIn; default `POST_TIMING = "Daily 9:00 AM PT"`
5. Pick palette (auto by tone, or forced if named in trigger)
6. Fill ALL variables in `linked_engine.py`
7. Run `python3 linked_engine.py`
8. Verify: 1-page PDF, PNG exists, caption exists
9. Deliver: batch path, caption inline, palette + rationale, POST_TIMING

## 4 Topic Lanes
1. **Project Management + AI** — AI-run delivery, agentic PM, ROI
2. **Data Infrastructure** — pipelines, warehouses, vector stores
3. **AI Workflow Automation** — orchestration, agents, n8n/LangGraph
4. **AI Economics & Token-Cost Engineering** — pricing, unit economics, caching

### Content strategy — what Tanzim wants (updated Jun 2026)

**✅ DO: Skills-and-systems posts (first-person, grounded in what he's actually building)**
- Data pipeline decisions and the reasoning behind them
- Org design at TIMBR — how a small team punches above its weight
- Infrastructure choices and their business logic
- Specific tools or systems he's implementing and why
- How autonomous pipelines are built (avoid "AI" as a buzzword — keep tone down)
- City-level fitness data architecture, boutique gym market, lean ops

**❌ DON'T: News/prediction posts — Tanzim explicitly rejected this format**
- "X company is doing Y to cut jobs / drop AI / adopt AI"
- Industry news round-ups
- Predictions about the world
- Trend commentary / "here's what's happening in tech"
- Posts where Tanzim is opining on others' work rather than showing his own

**The test:** Is this grounded in what Tanzim is actually building, shown from his POV, without telling anyone what to do? If not, rewrite. Posts must never instruct the reader — the reader draws their own conclusions.

## LinkedIn persona — critical (Jun 2026)
Tanzim's LinkedIn presence is **job-seeking AI implementation practitioner**, NOT founder/startup voice.

**What this means in practice:**
- **No TIMBR correlation.** Posts must stand alone — zero mention of TIMBR, no "my company", no co-founder framing. If TIMBR is the origin of a workflow, abstract it out.
- **Target roles:** AI implementation, project management, AI-native ops. Every post should make a hiring manager in that space think "this person knows what they're doing."
- **Tool-specific, named.** Claude Code, n8n, Python, data pipelines — name the actual tools. Vague "AI automation" language is useless. Named tools = credibility.
- **First-person practitioner.** "I built this", "I automated X using Y", "Here's the flow" — not "companies should..." or "the industry is shifting toward..."
- **Actionable takeaway always.** Reader leaves with something they can do this week. Insight without action is LinkedIn fluff.

## Headline format
Tanzim's preferred hook style: **short punchy fragment, often a question answered by the hook itself.**
- Pattern: `[Topic]? [Subversion].` — e.g. "Time? Non-renewable." / "Busy? That's the problem."
- 2–5 words max. No full sentences. No exclamation marks. No emoji in headline.
- The headline must earn the scroll — contrarian angle preferred over agreeable opener.

## Content pillars (what actually performs)
① **What I built** — specific workflow, named tools, real output. "I automated X using Claude Code + n8n. Here's the exact flow."
② **Decision logic** — why one tool over another. Shows taste + technical judgment. Hiring managers love this.
③ **Time recovered** — a specific number. "This took 3 hrs/week. Now it takes 0." Boring and specific = credible.

**Strong editorial angles:**
- "The Operator's Stack" — a specific architecture/infrastructure decision + reasoning
- "Fewer People. More Output." — efficiency-by-design, not headcount (10hrs → 60hrs value as anchor)
- "Building before shipping" — pipeline decisions that come before the product

## 10 Palettes
| Name | BG | Accent | Use for |
|------|-----|--------|---------|
| Amber | #1E2126 | #F0A030 | Bold, high-energy |
| Mint | #1A1D23 | #2ECC71 | Fresh, modern, growth |
| Violet | #141018 | #A855F7 | Premium, frontier |
| Coral | #191C20 | #E85D4A | Urgent, contrarian |
| Paper | #F5F0E8 | #1A1D23 | Light, credibility |
| Sky | #EBF4FA | #1565C0 | Data, research |
| Sage | #EDF3ED | #2E7D32 | Sustainability |
| Charcoal | #27272A | #A855F7 | Premium dark, modern tech |
| Midnight | #0F172A | #F97316 | Bold contrast, navy + orange |
| Slate | #1E293B | #38BDF8 | Modern tech, dark blue-gray |

**User preference:** Colors deferred as of Jun 2 2026 — Tanzim reviewed 10+ palettes across multiple rounds and chose to keep the existing template (`#1E2126` / `#F0A030` / `#FFFFFF`) for now. Do not change colors without showing rendered swatches first and getting explicit approval.

### Jun 2026 palette review — shortlisted and rejected
Tanzim reviewed 10 custom palette previews across 3 rounds. Results:

**Shortlisted (approved for consideration):**
- Chalk & ink — `#EDECE8` bg · `#111111` text · `#2D5BE3` accent
- Midnight plum — `#160E1E` bg · `#F2EEE8` text · `#9B6FD4` accent

**Rejected (do not reuse):**
- Obsidian editorial (`#0E0E0E` / `#F5F0E8` / `#C9A84C`)
- Arctic tech (`#F7F9FC` / `#0D1B2A` / `#00B4D8`)
- Slate + ember (`#1C2331` / `#E8E4DD` / `#E05C2A`)
- Forest & gold (`#1A2618` / `#EDE8DC` / `#D4A843`)
- Bone & carbon (`#F0EDE6` / `#1A1A1A` / `#C1440E`)
- Iron & frost (`#212529` / `#F8F5F0` / `#5B9CF6`)
- Parchment & pitch (`#E8E2D5` / `#0D0D0D` / `#4A9E7F`)

Note: Dark palettes (Charcoal, Midnight, Slate) need matching dark footers:
- Charcoal: footer #1C1C1E, text #A1A1AA
- Midnight: footer #020617, text #A1A1AA (near-black footer with orange accents)

## Key variables in linked_engine.py
```python
BATCH_ID = ""          # auto-assigned
FILENAME = "..."       # snake_case slug
BG_COLOR / ACCENT_COLOR / TEXT_COLOR  # palette
TITLE_LINE1 / TITLE_LINE2 / SUBTITLE
BYLINE_NAME = "Tanzim Ozer"
BYLINE_ROLE = "AI Implementation Project Manager"
DATE_STR = ""          # auto-fills today
SECTIONS = [{"label": "...", "text": "..."}]  # exactly 4
TABLE_LABEL / TABLE_HEADER / TABLE_ROWS  # optional
ECON_LABEL / ECON_INTRO / COST_TABLE_ROWS / ECON_TAKEAWAY  # optional
GET_STARTED = [...]    # 5 items
KEY_TAKEAWAYS = [...]  # 3 items
POST_TIMING = "Daily 9:00 AM PT"
CAPTION_TEXT = "..."
```

## One-pager rules (hard)
- Exactly 4 SECTIONS, each 40–60 words
- No standalone table when ECON block is used (TABLE_LABEL=None)
- ECON block: ≤3 rows, short cells; ECON_INTRO ≤1 line; ECON_TAKEAWAY ≤1 line
- SUBTITLE ≤95 chars; GET_STARTED items ≤85 chars; KEY_TAKEAWAYS items ≤95 chars

## Output structure
```
~/Linked_Engine/
├── linked_engine.py      ← fill variables + run
├── article_tracker.json  ← LE### history (anti-repeat memory)
├── Linked_Posts.csv      ← publish queue (n8n reads this)
└── output/
    └── LE###/
        ├── {FILENAME}.pdf
        ├── {FILENAME}.png
        └── {FILENAME}_caption.docx
```

## Dependencies (already installed in hermes venv)
- reportlab, PyMuPDF (fitz), python-docx, Pillow
- All installed in `/home/hermes/.hermes/hermes-agent/venv`
- Install issues, venv path confusion, Pillow conflicts → see `references/dependencies.md`

## Delivering output to Tanzim
**Use the WhatsApp bridge `/send-media` endpoint — NOT `send_message`, NOT Google Drive links.**

`send_message` with `file://` URIs renders as plain text. Google Drive links are a fallback Tanzim explicitly rejected. Use this for every file delivery:

```bash
# PDF
curl -s http://localhost:3000/send-media \
  -H "Content-Type: application/json" \
  -d '{"chatId":"160799431606497@lid","filePath":"/home/hermes/Linked_Engine/output/LE###/filename.pdf","mediaType":"document","fileName":"LE###_title.pdf","caption":"LE### — PDF"}'

# PNG
curl -s http://localhost:3000/send-media \
  -H "Content-Type: application/json" \
  -d '{"chatId":"160799431606497@lid","filePath":"/home/hermes/Linked_Engine/output/LE###/filename.png","mediaType":"image","caption":"LE### — PNG"}'

# Caption DOCX
curl -s http://localhost:3000/send-media \
  -H "Content-Type: application/json" \
  -d '{"chatId":"160799431606497@lid","filePath":"/home/hermes/Linked_Engine/output/LE###/filename_caption.docx","mediaType":"document","fileName":"LE###_caption.docx","caption":"LE### — Caption"}'
```

Send all three. See `whatsapp-send-document` skill for full bridge reference.

## GAP tuning — full-page vs spacing issues

`GAP` controls vertical spacing between blocks. The engine enforces a hard 1-page limit — so GAP interacts directly with how full the page looks.

| Situation | GAP value |
|-----------|-----------|
| Full content (4 sections + ECON + GET_STARTED + KEY_TAKEAWAYS) | 12–13 |
| Medium content | 14–15 |
| Light content (few sections, no ECON) | 16–20 |

**"There is a spacing issue, it needs to be a full pager"** = GAP is too low for the amount of content → content floats near the top leaving dead space below. Increase GAP.

**"PDF has 2 pages"** = GAP is too high OR content is too long → reduce GAP first (13→12), then trim section text.

**Jun 2026 confirmed:** Full article (4 sections + ECON 3-row table + GET_STARTED 5 items + KEY_TAKEAWAYS 3 items) fits cleanly at `GAP=13`.

## Headline rules — Tanzim's explicit preferences

**Format:** Short fragment, not a sentence. 2–6 words. No exclamation marks. No emoji.

**Tone:** Confident, first-person practitioner. Never preachy. Never tells people what to do.

**Rejected styles:**
- Instructional: `"Stop managing tasks. Start designing flows."` — sounds like advice, Tanzim hates this
- Full sentences: `"I don't have a productivity system. I have infrastructure."` — too long
- Generic: `"The system is the strategy"` — no number, too abstract for the engine spec

**What works:**
- Fragment + subversion: `"Time? Non-renewable."` — question answered by the hook
- First-person specific: `"15 Hours. Recovered. Every Week."` — boring and specific = credible
- Contrarian opener: `"My workflow runs itself."` — confident, stops the scroll

**Engine hard rule:** TITLE_LINE1 must contain a number. "My workflow runs itself" technically breaks this — always try to work in a concrete figure.

## Content tone — what Tanzim corrected multiple times this session

**"It sounds like I'm telling people what to do — I don't like that."**

The post is a window into what *you're* doing. Never a how-to. Never imperative framing. Reader draws their own conclusions.

❌ `"Here's how you can do this too"`
❌ `"Three things you should implement this week"`
❌ `"If you're a PM, you need to..."`

✅ `"Here's what my workday actually looks like"`
✅ `"I automated X using Y. Here's the exact flow."`
✅ `"The result: 15 hrs of overhead removed. That's the model."`



## Pitfalls
- Always run from `~/Linked_Engine/` dir (tracker + output paths are relative)
- NEVER use `&` characters in Python string variables — use `+` or `and` instead (breaks CSV)
- Vary palette from the most recent tracker entry; mix dark and light
- **Caption DOCX may carry stale content when monkey-patching.** When using `/tmp/le_render.py` import approach, the `CAPTION_TEXT` global may not propagate correctly into the DOCX. Always read and verify the DOCX after render — if it looks like a prior post's caption, write the caption manually and send it inline instead of from the file.
- **Entry point when monkey-patching is `le.generate()`, NOT `le.main()`.** `main()` does not exist as a module-level function.
- **Company name is TIMBR** (not Timber, not Timbr — all caps, four letters). Never write "Timber" in any post, doc, caption, or output. This is a hard correction Tanzim made explicitly.
- **Always verify caption separately from the PNG.** Send PNG first, then paste the caption inline — do not rely solely on the DOCX file if there's any doubt about its freshness.
## Title width — MUST CHECK before rendering
**TITLE_LINE1 and TITLE_LINE2 must fit within USABLE_W=532pt at 22pt bold.** ReportLab's `drawString` does NOT word-wrap — overflow silently bleeds off the right edge, consumes extra vertical space, and causes a 2-page failure that only surfaces at verify time.

Quick check:
```python
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
pdfmetrics.registerFont(TTFont("Arial-Bold", "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"))
for title in [TITLE_LINE1, TITLE_LINE2]:
    w = pdfmetrics.stringWidth(title, "Arial-Bold", 22)
    print(f"{w:.1f}pt {'OK' if w <= 532 else 'TOO LONG — shorten'}")
```
Safe rule: TITLE_LINE1 ≤ ~40 chars, TITLE_LINE2 ≤ ~55 chars.
- **One-pager tight on space?** Reduce GAP from 14→12 first (saves ~14pts). Then trim section text. Last resort: shorter ECON table cells.

## One-pager debugging (PDF has 2 pages)
The verify step raises `RuntimeError: PDF has N pages, expected 1`. Engine auto-paginates silently so you won't see overflow until then.

**Diagnosis:**
1. Monkey-patch `Layout.page_break` to `print(self.y)` — tells you how far over you are
2. Monkey-patch `Layout.space` to log `(need_h, self.y)` when `y < 100` — identifies exact trigger
3. Break fires when `self.y - need_h < floor` where `floor = 38` (FOOTER_BAR_H=22 + SAFE_PAD=16)

**Fixes in order of preference:**
1. **Title too wide** — split TITLE_LINE1 to be shorter; move words to LINE2
2. **Reduce GAP** — 14→12 saves ~14pts across 7 blocks. Safe range: 12–16
3. **Trim SECTIONS** — target ~50 words each, not 60
4. **Trim GET_STARTED items** — each ≤75 chars is safer than the 85 spec
5. **ECON table cell text** — short cells prevent row wrapping

**Verified safe config for full article (4 sections + ECON + GET_STARTED + KEY_TAKEAWAYS):**
`GAP=12`, sections ~50 words, ECON 3 short-cell rows, GET_STARTED ≤75 chars/item

See `references/one-pager-debug.md` for the session trace.

## Layout diagnostics (when user reports "template broke")

Before guessing, run the PyMuPDF margin violation scan:
```python
import fitz
doc = fitz.open('output/LE###/filename.pdf')
page = doc[0]
for b in page.get_text('dict')['blocks']:
    for line in b.get('lines', []):
        for span in line['spans']:
            if span['bbox'][2] > 572:  # right margin
                print(f"RIGHT VIOLATION: {span['text'][:40]}")
```

If user shows a screenshot with dark border — that's the viewing app (iOS, Drive, WhatsApp), not the template. Verify by checking PNG edge pixels directly.

See `references/pdf-layout-diagnostics.md` for full diagnostic scripts or run `scripts/verify_pdf.py` directly.

## Bulletproof mode (v3)

v3 introduces **pre-render enforcement + post-render verification** — template CANNOT break:

**Hard limits enforced automatically:**
| Field | Max chars | Why |
|-------|-----------|-----|
| TITLE_LINE1 | 58 | Fits 1 line at 22pt bold in 532pt width |
| TITLE_LINE2 | 55 | Slightly shorter for visual balance |
| SUBTITLE | 100 | 1-2 lines at 10.5pt |
| Each SECTION | 250 | ~3 wrapped lines at 9pt |
| Each GET_STARTED item | 75 | 1 line at 8.5pt |
| Each KEY_TAKEAWAY | 85 | 1 line at 8.5pt |
| ECON_INTRO | 95 | Single line |
| ECON_TAKEAWAY | 90 | Single line |
| TABLE_CELL | 22 | No cell wrapping |

**Pre-render:** `enforce_all_limits()` auto-truncates content with "..." if over limit.  
**Post-render:** `verify_pdf()` scans for margin violations — fails build if any found.

If content is truncated, engine prints warnings but still generates valid output.

## Version history
- **v3** (Jun 2025): Bulletproof template — pre-render hard limits + post-render verification. Build FAILS if any margin violation detected. Added Charcoal palette.
- **v2.2** (Jun 2025): Titles now use `wrap_text()` — auto-wrap instead of silent overflow. Fixed right margin violations on long titles.
- **v2.1**: Added hard character limits with auto-truncation for single-page guarantee.
