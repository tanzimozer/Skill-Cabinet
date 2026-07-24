---
name: tahmeed-ai-teaching
category: education
description: Running Tahmeed Ozer's structured AI learning programme — daily sessions, tracking, PDF delivery, and GitHub-linked projects.
---

# Tahmeed AI Teaching Programme

## When to use this skill
Any session involving Tahmeed's AI curriculum — planning, delivering, tracking, or producing session materials.

## Source of truth
**Google Sheet "Tahmeed profile"** — ID: `19v5x4oScpEPXkjHBWvt97UHtWChki5UGniJvop258bc`
- Tab: `User Profile` — 30-question Gallup-style questionnaire (col A = question, col B = answer)
- Tab: `AI Foundations Week` — 5-day daily curriculum (Jun 1–5, status tracked per session)
- Tab: `AI Learnings` — 10 projects (Jun–Sep, status + GitHub repo columns)

**Always read the sheet at the start of a session. Always update it after.**

## Daily session structure
Time: 8:00–10:00 AM Dhaka (BST, UTC+6)
Loop every day:
1. 🎬 **Video hook** (15 min) — YouTube, chosen to spark curiosity before any theory
2. 📖 **Concept** (30 min) — explain in plain language, real analogies
3. 💻 **Hands-on task** (45 min) — apply it immediately
4. ⬆️ **GitHub push** (15 min) — every session ends with a commit. No exceptions.

Gate test at end of each day. Score logged in sheet.

## Teaching philosophy
- Visual-led first. YouTube before text, always.
- No tech background — explain like a sharp curious 14-year-old is the audience.
- Peak interest first, then teach, then apply. Curiosity → concept → build.
- Each day: one visionary leader video (Sam Altman, Dario Amodei, Elon, Karpathy etc.) + one technical video.
- Iteration is daily — watch, learn, apply, push, repeat.

## Programme phases
| Phase | Scope | Timing |
|-------|-------|--------|
| 0 | Know Yourself — 30Q Gallup questionnaire | Week 1 (before teaching starts) |
| 1 | Foundations + Spark — brain vs AI, what is AI, LLMs, visionary leaders | Weeks 1–3 |
| 2 | Technical Skills — Python, APIs, prompting, building with models | Weeks 4–8 |
| 3 | Projects — one real project per fortnight, all on GitHub | Weeks 9+ |

## Delivery
- Materials as PDF with clickable hyperlinks (see `references/pdf-generation.md` for technique)
- Verify all YouTube links before including in PDF
- Drop PDF in the Learn AI WhatsApp group: `120363425196031209`
- Session summary message in group after each session — plain, human register

## When a video link is dead
Dead links are a recurring problem — do not stall the session or apologise repeatedly.

**Priority order:**
1. Check `references/curriculum-videos.md` for a vetted alternative on the same topic
2. If none, look for a replacement (search YouTube mentally or via browser if available)
3. If browser is unavailable or replacement also fails — **teach the topic directly in chat**

**Direct teaching pattern (works well for Tahmeed):**
- Open with a one-para plain-English explanation
- Use a concrete real-world analogy (his phone, his apps, something he uses daily)
- End with exactly 3 gate questions — same as you would post-video
- This is not a degraded fallback; it works. Don't treat it as lesser.

**Flag dead links in `references/curriculum-videos.md`** with ~~strikethrough~~ and a `DEAD` note so future sessions don't reuse them.

## Gate test structure
One gate test at the end of each topic/day. Pattern:
- 3 questions max
- If a question is skipped or dodged, hold on it — don't move forward until answered
- If Tahmeed says "I don't know" on a factual term: explain it in 3–5 lines using an analogy, then ask him to put it back in his own words — this closes the loop
- Log pass/fail + timestamp in the sheet after each gate test

## Key contact
- Tahmeed WhatsApp: `90345106862172@lid`
- Learn AI group ID: `120363425196031209`
- Tanzim is in the group and owns the programme — report to him

## References
- `references/pdf-generation.md` — fpdf2 Unicode fix + link verification pattern
- `references/curriculum-videos.md` — verified YouTube resource bank; dead links flagged with DEAD note
- `references/gate-tests.md` — verified gate test Q&A bank, Days 1–5 + Topics 5–7; teaching notes per question
