---
name: blair-magazine-data-extraction
description: Extract magazine content answers from Blair's Google Sheets fitness data tabs (Training Program, Nutrition, May 2026 supplements, Toning, Overview) to populate unanswered Magazine Questions in Blair's Persona tab
tags: [magazine, content-extraction, fitness, google-sheets]
---

# Blair Magazine Data Extraction

## Purpose
When building Blair's lifestyle magazine but lacking direct interview answers, extract factual data from her existing Google Sheets tabs (Training Program, Nutrition, Supplements, Toning, Goals) and map them to Magazine Questions in Blair's Persona tab.

## When to Use
- Blair hasn't answered Magazine Questions yet (30 pending)
- Magazine deadline is approaching (Saturday May 24, 2026)
- Need to draft magazine content with available data
- Building narrative from existing fitness tracking sheets

## Key Data Sources (Blair's Fitness Sheet)

### 1. **Overview Tab**
- Goal: Mexico June 13, 2026
- Bodyweight: 178 lbs
- Daily target: 1,750 cal
- Protein: 178g/day
- Training split: 4 weights + 1 Pilates
- Program type: Hypertrophy + Depletion
- 5-phase timeline (Depletion → Intensify → Pre-Peak → Carb Reload → Peak Day)

### 2. **May 2026 Supplements Tab**
- **Active Daily:** HMB (3g/day), Vitamin D (4,000 IU), EGCG (400mg), Beet Root (500mg-1g), Omega-3 (3g EPA+DHA), Yohimbine (5-20mg fasted AM), Noctrine (1 serving/night), Kre-Alkalyn (3g/day)
- **Training Days:** Performance EAA (10-15g intra), Karbolyn (12-13g pre), Collagen Peptides (15g pre)
- **Non-Training Days:** ACV (2 tbsp before carb meals)
- **Peak Week Only:** Water Out (June 7-13)
- **Removed (May 2026):** Synephrine, Cayenne, standard Creatine (diagnostic cleanup)

### 3. **Training Program Tab**
- Goal: 4 lbs lean muscle / zero fat gain
- Equipment: Machines and cables
- Split: 4 days weights + 1 Pilates
- **Hyperplasia Protocols:**
  - Loaded Stretch (30s hold at stretched position, final set)
  - FST-7 (7 sets × 8-12 reps, 30s rest)
  - Lengthened Partials (partial reps in stretched position)
  - Intra-Set Stretch (pause mid-set at stretch)
  - Eccentric Overload (4-5s negatives, slow tempo)
  - BFR (bands at 40-50% occlusion, lighter load, higher reps)
  - Constant Tension (no lockout, sustained metabolic stress)
- **Day 1 Example:** Glutes (Heavy) + Back
  - Smith Machine Hip Thrust: 4×8 @ RPE 8-9, tempo 4/2/1
  - Cable Pull-Through: 4×10 @ RPE 8, tempo 4/1/1
  - Leg Press (wide high foot): 4×10 @ RPE 8, tempo 3/1/2

### 4. **Nutrition Tab**
- **TDEE:** ~2,100 cal (Apple Watch 1,926 + training 300/session avg)
- Bodyweight: 178 lbs
- Meals/day: 3
- Goal: Mexico June 13, lean + tight aesthetic (not full cut)
- **Phase 1 Macros (May 4-24):** 1,750 cal | 178p | 100c | 71f
- **Phase 2 Macros (May 25-Jun 1):** 1,650 cal | 178p | 80c | 69f
- **Phase 3 Macros (Jun 2-6):** 1,600 cal | 178p | 60c | 72f

### 5. **Toning Tab**
- Objective: Tighter look, excess water flush, muscle pump for Mexico
- **5-Phase Timeline:**
  - Phase 1 (Depletion + Flush): May 4-24, 1,750 cal, 100g carbs
  - Phase 2 (Intensify): May 25-Jun 1, 1,650 cal, 80g carbs
  - Phase 3 (Pre-Peak): Jun 2-6, 1,600 cal, 60g carbs
  - Phase 4 (Carb Reload): Jun 7-11, 2,072 cal, 250g carbs
  - Phase 5 (Peak Day Prep): Jun 12-13, 2,000 cal, 200g carbs
- **Toning Protocol:** High rep, short rest (30-45s), constant tension
  - Constant Tension Sets (no lockout, full set)
  - Superset Finishers (2 exercises back-to-back, 3 rounds)
  - High Rep Burnouts (15-25 reps, light-moderate weight)
  - BFR (40-50% occlusion, 3×20-30 reps)

### 6. **Jul-Sep Backlog Tab (Future Goals)**
- **Priority 1:** Hip Dip / Glute Med Development (post-Mexico)
- **Priority 2:** Upper Body Lagging (arms, back, shoulders volume imbalance)
- **Priority 3:** Peptide: Follistatin (myostatin inhibition, lean muscle gain)
- **Priority 4:** IGF-1 LR3/DES (requires cancer screening clearance first)

## Mapping to Magazine Questions

### Can Answer from Sheet Data:

**Q8 (Routine):** "Walk me through your Sunday night prep ritual"
→ Extract from meal prep patterns, phase-specific shopping lists (Nutrition tab)

**Q10 (Routine):** "How do you structure your training week around a demanding work schedule?"
→ "4 days weights + 1 Pilates, working around 8am-4:30pm M-F + frequent travel" (Overview + answered Q5)

**Q22 (Products):** "What's one fitness product under $30 that dramatically improved your results?"
→ Kre-Alkalyn ($20-25, replaces standard creatine, no bloat during depletion) or EGCG ($15-20, daily baseline) (May 2026 tab)

**Q23 (Products):** "What expensive fitness purchase was totally worth it, and why?"
→ HMB ($40-50/month, 3g/day muscle preservation during deficit) or Yohimbine + EAA stack (May 2026 tab)

**Q24 (Products):** "What app or tool do you use daily that most people sleep on?"
→ Apple Watch for TDEE tracking (1,926 cal baseline) (Nutrition tab)

**Q27 (Aspiration):** "Where do you see your fitness journey in 5 years?"
→ Jul-Sep Backlog goals: glute med development, upper/lower balance, peptide protocols (Backlog tab)

**Q28 (Hot Takes):** "What's an unpopular opinion you have about the fitness industry?"
→ Can infer from hyperplasia focus vs. traditional volume, or diagnostic supplement removal (Training/May 2026 tabs)

**Q29 (Hot Takes):** "What fitness trend do you think is complete BS?"
→ Removed supplements (Synephrine, Cayenne, standard Creatine) = "third thermogenic is redundant, cortisol risk" (May 2026 tab)

### Cannot Answer (Need Blair's Voice):
- Q1-3 (Transformation): Turning point story, lowest point, biggest lie
- Q4-7 (Mindset): Internal monologue, mindset shift, handling judgment
- Q9 (Routine): 15-min non-negotiable morning routine (already answered Q1, but this is about bare minimum)
- Q11-14 (Nutrition): Already answered in Round 2
- Q15-17 (Failures): Already answered Q15-16 partially
- Q18-19 (Travel): Travel bag essentials, maintaining routine on road
- Q20-21 (Work-Life): 12-hour shifts (Blair works 8-4:30, not 12hr), work derailment strategy
- Q25-26 (Identity): Body relationship change, content impact vision

## Extraction Workflow

1. **Read all tabs** from Blair's Fitness Sheet (ID: 1sNSE4gRkGMJW5lpTcIJYM69m88JAXks9qQADXmWY6dk)
   - Overview, May 2026, Training Program, Nutrition, Toning, Jul-Sep Backlog

2. **Identify answerable questions** from Blair's Persona tab (Magazine Questions with empty Answer column)

3. **Extract factual data** (macros, supplements, exercises, phases, goals)

4. **Draft answers in Blair's voice** (use existing Round 1-2 answers as tone reference):
   - Disciplined but not rigid
   - Practical over theoretical
   - Mentions specific numbers/products
   - References her "more is more" shift to intentional training

5. **Populate Blair's Persona tab** with drafted answers (mark as "Extracted from [Tab Name]" in Date column for transparency)

6. **Flag questions needing Blair's direct input** (transformation stories, mindset, identity)

## Output Format

When populating answers:
```
Round | Q# | Category | Question | Answer | Date
R[X] | Q[N] | [Category] | [Question text] | [Extracted answer in Blair's voice] | Extracted: [Source Tab]
```

Example:
```
R7 | Q22 | Products | What's one fitness product under $30... | Kre-Alkalyn creatine. It's $20-25 and replaces standard creatine without the bloat—critical during depletion phases when you're trying to look tight, not puffy. Most people don't realize creatine saturation has a ceiling; adding multiple forms is redundant. | Extracted: May 2026
```

## Success Criteria
- 8-12 Magazine Questions answered from sheet data
- Answers sound like Blair (match Round 1-2 tone)
- Facts are accurate (macros, supplements, exercises match tabs)
- Remaining ~18-22 questions clearly flagged as needing Blair's direct input
- Magazine can be drafted with hybrid content (10 answered + 8-12 extracted = 18-22 total vs. 40 needed)

## Notes
- This is a **gap-fill strategy**, not a replacement for Blair's interview
- Use extracted answers to build magazine skeleton
- Blair can review/revise extracted answers later
- Transparency: mark extracted answers so Blair knows what came from her sheets vs. her direct voice
