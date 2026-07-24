---
name: persona-driven-content-extraction
description: Extract authentic persona content through structured interviews for narrative-first digital products (magazines, guides, courses)
triggers:
  - Building lifestyle/fitness magazines from someone's story
  - Persona extraction for digital content products
  - Structured interviewing for authentic voice capture
  - Converting expertise into narrative-driven products
---

# Persona-Driven Content Extraction

Extract authentic voice and lifestyle content through structured async interviews. Used for **narrative-first digital products** where the person's story wraps around tactical content (not training manuals with a bio section).

---

## When to Use

- Building lifestyle magazines, digital guides, or courses from someone's authentic voice
- The **person is the product** — buyers want access to their system, philosophy, and daily life
- Tactical content (workouts, nutrition, recipes) exists as **1-page appendices**, not the core
- Async extraction over weeks (not live interviews)

---

## Core Principle: Narrative First, Tactics Second

**WRONG structure:**
- 80% training program + nutrition protocols
- 20% personality/story as flavor

**RIGHT structure:**
- 70% narrative — journey, philosophy, daily life, mistakes, wins, routines
- 30% tactical 1-pagers — workout block, macro framework, local spots, gear

**Why:** At $15–30 price points, people buy **the person**, not just the program. Generic programs are free on YouTube. Access to someone's full lifestyle system is the premium product.

---

## Question Budget

**30 questions maximum** for a ~50–75 page magazine.

### Breakdown:
- **20 questions** → Narrative content (story, philosophy, lifestyle, work, recovery)
- **10 questions** → Tactical 1-pagers (program, macros, meal prep, local spots, gym preferences)

**30 questions is a constraint, not a starting point.** Fewer is better if the answers are deep.

---

## Structure

### Narrative Questions (20)

**The Journey (5)**
- Where did this start? What was the trigger?
- What was your biggest mistake early on?
- When did you realize X approach wasn't working?
- What changed when you shifted to Y?
- What keeps you consistent?

**Philosophy & Approach (7)**
- What's your core philosophy in one sentence?
- How do you structure your year/phases?
- Walk me through your current phase — what and why?
- What does your typical week look like?
- Why [unique element]? What does it give you?

**Daily Life & Routines (4)**
- Walk me through your workday and how [domain] fits.
- What's your morning routine?
- How do you stay consistent while traveling?
- What do you do on rest/recovery days?

**Social & Lifestyle (4)**
- How do you handle [social challenge] without derailing?
- What's your relationship with [vice/indulgence]?
- How do you know when to push vs. rest?
- What do people get wrong about [your approach]?

### Tactical 1-Pagers (10)

**Program/System (2–3)**
- Give me your current [X]-week block (exercises/structure).
- What are your top 5 [elements] you'll never skip?

**Nutrition/Fueling (2–3)**
- What are your current [metrics] and how did you calculate them?
- What's your weekly [prep routine]? (Shopping, staples, go-to meals)
- Walk me through a typical day of eating.

**Local/Contextual (4)**
- Top 3 [local spots category 1]?
- Top 3 [local spots category 2]?
- Where do you [exception/treat]?
- Hidden gem nobody knows about?

**Infrastructure (1)**
- Where do you [train/work/operate]? What do you look for?

---

## Execution via Google Sheets

### Setup
1. Create `[Name]'s Persona` tab in their working sheet
2. Columns: `Round | Q# | Category | Question | Answer`
3. Organize questions into **rounds of 5** for digestible async delivery

### Workflow
1. **Pre-check existing answers** — Read sheet, identify what's already covered
2. **Cross-reference** — Don't re-ask answered questions; build on them
3. **Append new questions** — Use `sheets.spreadsheets().values().append()` with `valueInputOption='RAW'`
4. **Send round-by-round** — 5 questions at a time, wait for answers before next round
5. **Monitor responses** — Check sheet periodically, flag gaps

### Consolidating Question Sets

**When you have multiple question tabs** (e.g., "Magazine Questions" and "[Name]'s Persona"):

1. **Read both tabs fully** — Identify which has better narrative questions vs. which has answers
2. **Prioritize narrative quality** — Magazine-style questions ("What moment made you realize...") beat data-collection questions ("What are your work hours?")
3. **Keep answered questions** — Never discard data already collected
4. **Consolidate strategy**:
   - Extract answered questions from Persona tab (where `Answer` column is populated)
   - Reformat Magazine Questions to match Persona tab structure: `[Round, Q#, Category, Question, Answer]`
   - Clear and rewrite Persona tab with: header → answered questions → new narrative questions
5. **Verify post-consolidation** — Re-read the tab to confirm row count and that answered data survived

### Code Pattern
```python
# Read existing
result = sheets.spreadsheets().values().get(
    spreadsheetId=sheet_id,
    range="[Name]'s Persona!A:E"
).execute()

# Append new questions
new_questions = [
    ["Round", "Q#", "Category", "Question", ""],
    # ...
]
result = sheets.spreadsheets().values().append(
    spreadsheetId=sheet_id,
    range="[Name]'s Persona!A:E",
    valueInputOption='RAW',
    body={'values': new_questions}
).execute()
```

---

## Delivery Cadence

- **5 questions per round** (not 10, not 3 — 5 is the rhythm)
- **2–3 hour no-reply window** before same-day re-ask (only if critical path)
- **Don't stack rounds** — wait for 80%+ answers before sending next round
- **Organize by theme** — each round should feel cohesive (all journey, all nutrition, etc.)

---

## Red Flags

### ❌ Training Manual Disguised as Magazine
**Signal:** 60+ questions, heavy on sets/reps/macros, light on story  
**Fix:** Cut tactical depth, double down on narrative

### ❌ Generic Interview Questions
**Signal:** "What's your favorite exercise?" "What do you eat for breakfast?"  
**Fix:** Make questions specific to their unique approach, mistakes, or philosophy

### ❌ Overloading the Subject
**Signal:** 15-question rounds, multi-part questions, asking for essays  
**Fix:** 5 questions max per round, one clear ask per question

### ❌ Buried 1-Pagers
**Signal:** Tactical content scattered across narrative questions  
**Fix:** Consolidate workout/nutrition/local into dedicated 1-pager questions at end

---

## Output: Magazine Structure

**~75 pages total**

1. **Front Matter** (3–5 pp) — Editor's letter, how to use, credits
2. **Narrative Core** (40–50 pp) — Journey, philosophy, daily life, lifestyle, Q&A
3. **Tactical 1-Pagers** (15–20 pp) — Workout block, nutrition framework, local spots, gym
4. **Back Matter** (5–10 pp) — Progress tracker, what's next

**The narrative IS the magazine. The 1-pagers are proof/reference.**

---

## Related

- See `references/fitness-magazine-pricing-2024-2026.md` for pricing strategy and competitive landscape
