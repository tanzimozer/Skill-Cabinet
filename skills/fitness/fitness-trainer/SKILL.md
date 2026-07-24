---
name: fitness-trainer
description: Full-pipeline fitness coaching skill. Runs a 10-question conversational WhatsApp assessment with a new client, builds their Google Sheet (Assessment + Training + Nutrition tabs), generates an 8-week training program + full macro/supplement nutrition plan via role-based expert prompting, QCs the output, then sends the sheet link to Tanzim for approval. On approval, stamps each tab.
tags: [fitness, coaching, assessment, whatsapp, google-sheets, nutrition, training, opus]
model: claude-opus-4-5
triggers:
  - Tanzim says "Friday, let's build [Name]'s fitness profile" in a WhatsApp group
---

# Fitness Trainer Skill

## Overview
End-to-end client fitness program pipeline. Triggered naturally in a WhatsApp group. Zero errors required — use Opus at every generative stage.

---

## Trigger
**Phrase:** `"Friday, let's build [Name]'s fitness profile"`
- Fired by Tanzim in a WhatsApp group chat that includes the client
- Extract the client name from the phrase
- Create the Google Sheet immediately (blank, named `[Name] Fitness Profile`)
- Begin the conversational assessment in the same group chat

---

## Stage 1 — Conversational Assessment (WhatsApp)

Ask exactly 10 questions, **one at a time**. Wait for the client's response before sending the next. Address the client by first name. Keep tone warm, casual, professional.

### The 10 Questions (in order)

1. "What's your full name and age?"
2. "What's your primary goal — fat loss, muscle gain, or both?"
3. "What's your current weight and height? And do you know your body fat %?"
4. "How would you describe your training experience — beginner, intermediate, or advanced? And how many years have you been training?"
5. "How many days per week can you commit to training?"
6. "Where do you train — gym, home, or both? And what equipment do you have access to?"
7. "Do you have any injuries, pain, or physical limitations I should know about?"
8. "Any dietary restrictions or food allergies?"
9. "How would you describe your current eating habits — do you follow any specific diet?"
10. "Are you currently taking any supplements?"

### Rules
- One question per message. No batching.
- If a client's answer is unclear or incomplete, ask one follow-up before moving on.
- Do NOT skip questions.
- After Q10 is answered, confirm: "Perfect, that's everything I need. Give me a moment to build your profile."

---

## Stage 2 — Populate Assessment Tab

Write all 10 answers into the **Assessment** tab of the client's Google Sheet.

### Assessment Tab Layout

| Field | Client Response |
|---|---|
| Full Name | |
| Age | |
| Primary Goal | |
| Current Weight | |
| Height | |
| Body Fat % | |
| Training Experience Level | |
| Years Training | |
| Training Days Per Week | |
| Training Location | |
| Equipment Access | |
| Injuries / Limitations | |
| Dietary Restrictions / Allergies | |
| Current Eating Habits / Diet | |
| Current Supplements | |

- Row 1: Header row (bold, frozen)
- Column A: Field name (bold)
- Column B: Client's response
- Column widths: A=250px, B=400px

---

## Stage 3 — Training Program (Role: Certified Fitness Trainer, 10 years experience)

**System prompt to use for this stage:**
> You are a certified personal trainer with 10 years of experience specialising in body recomposition, hypertrophy, and fat loss. You have worked with hundreds of clients across all fitness levels. You build evidence-based, periodised programs that are practical and sustainable. You do not use cookie-cutter templates — every program is built from the client's individual assessment data.

Build an **8-week training program** using the assessment data.

### Training Tab Layout

#### Header block (rows 1–3)
- Client name, goal, program duration (8 weeks), days/week, location/equipment

#### Program structure
- Organised by week blocks: Week 1–4 (Phase 1: Foundation), Week 5–8 (Phase 2: Progression)
- Each training day:
  - Day label (e.g. "Day 1 — Chest & Triceps")
  - Exercise table: Exercise | Sets | Reps | Rest | Notes
  - Minimum 4, maximum 7 exercises per session
- Rest days clearly marked
- Progressive overload rule stated explicitly (e.g. "+2.5kg or +1 rep each week on compound lifts")
- Deload protocol stated for Week 8 (reduce volume 40%, maintain intensity)

### Rules
- Name sessions by muscle group, not movement pattern ("Back" not "Upper Pull")
- Respect all injuries and limitations from assessment
- No medical advice — flag anything clinical
- Program must fit stated days/week and available equipment exactly

---

## Stage 4 — Nutrition Plan (Role: Certified Nutritionist & Dietitian, 10 years experience)

**System prompt to use for this stage:**
> You are a certified nutritionist and registered dietitian with 10 years of experience in sport and performance nutrition. You specialise in evidence-based macro programming, body recomposition, and supplementation protocols. You build practical, sustainable nutrition plans tailored to the individual's goals, dietary restrictions, and lifestyle.

Build a **full daily nutrition plan** using the assessment data.

### Nutrition Tab Layout

#### Header block
- Client name, goal, dietary restrictions, calorie target, macro split

#### Daily Macro Breakdown
| Metric | Value |
|---|---|
| Total Daily Calories | |
| Protein (g) | |
| Carbohydrates (g) | |
| Fats (g) | |
| Fibre (g) | |
| Water intake (L) | |

#### Macro Rationale
- 3–5 sentences explaining why these macros were chosen based on goal + body composition

#### Calorie Calculation Method
- State TDEE estimate + deficit/surplus applied

#### Food Source Guidance
- Protein sources (list 5–8)
- Carbohydrate sources (list 5–8)
- Fat sources (list 5–8)
- Foods to limit/avoid (based on dietary restrictions)

#### Supplement Stack
| Supplement | Dose | Timing | Purpose |
|---|---|---|---|
| | | | |

- Only evidence-based supplements (creatine, protein, omega-3, vitamin D, magnesium, etc.)
- No unproven or unsafe recommendations
- Flag any conflicts with stated medications or conditions

### Rules
- No meal timing (excluded by design)
- Respect all dietary restrictions and allergies — zero exceptions
- Macros must be consistent with stated goal (fat loss = deficit, muscle gain = surplus, both = recomp)

---

## Stage 5 — QC Pass (Role: Experienced Fitness Manager, 10 years experience)

**System prompt to use for this stage:**
> You are a senior fitness manager with 10 years of experience overseeing certified trainers and nutritionists. You conduct rigorous quality control on all client programs before delivery. You check for consistency, safety, evidence basis, and alignment with the client's stated goals and constraints.

Run a QC pass across both the Training and Nutrition tabs.

### QC Checklist
- [ ] Training program matches stated days/week
- [ ] Equipment used matches stated access
- [ ] Injuries/limitations respected throughout
- [ ] Progressive overload model defined and logical
- [ ] Deload included
- [ ] Session names are muscle-group based
- [ ] Volume per session is within 4–7 exercises
- [ ] Macros consistent with stated goal
- [ ] Dietary restrictions respected — zero violations
- [ ] Supplement stack is evidence-based only
- [ ] No medical advice given
- [ ] Both tabs are complete — no blank fields

### If QC fails:
- Fix the issue directly. Do not send a broken program for approval.
- Re-run QC after fixing until all checks pass.

---

## Stage 6 — Approval Request

Once QC passes:
1. Send the Google Sheet link to Tanzim on WhatsApp (private chat or same group — use same group by default)
2. Message format:
   > "Boss, [Name]'s fitness profile is ready for your review. Training, nutrition, and supplement stack are all in. QC passed. [Sheet link]"

Wait for Tanzim's approval response.

**Approval keywords:** "approved", "looks good", "stamp it", "done", "go ahead"

---

## Stage 7 — Approval Stamp

On approval, append to the bottom of each tab (Assessment, Training, Nutrition):

- Leave 2 blank rows after the last row of content
- Add a row with the following in column A:
  > ✓ Approved by Tanzim Ozer CPT, SNS — [Date of approval, format: DD MMM YYYY]
- Format: bold, dark green text (#1a7a1a), no background colour

---

## Sheet Specifications

- **Name:** `[Client First Name] Fitness Profile`
- **Tabs:** Assessment, Training, Nutrition (in that order)
- **Sharing:** Shared with edit access to tanzim.seattle@gmail.com
- **Auth:** Use `~/.hermes/google_token.json`
- **Do not** share directly with the client from the sheet — Tanzim manages that

## Delivery Channel

- **Approval link:** Send to Tanzim's personal WhatsApp DM — `160799431606497@lid`
- **Assessment conversation:** Runs in the group chat where the trigger phrase was sent
- **Stamp confirmation:** Sent back to same DM after stamping is complete

---

## Error Handling

- If Google Sheets API fails: retry once, then report to Tanzim immediately
- If a client gives an ambiguous answer: ask one clarifying follow-up, don't guess
- If QC finds a violation: fix silently, re-check, never send a flagged program
- If Opus generation fails: retry once on Opus, do not fall back to a lesser model — flag to Tanzim

---

## Supporting Script

Location: `~/.hermes/skills/fitness/fitness-trainer/fitness_trainer.py`

Handles:
- Google Sheet creation and tab setup
- Assessment tab population
- Approval stamp writing

Call via `python3 ~/.hermes/skills/fitness/fitness-trainer/fitness_trainer.py`

## GitHub Repository

Skill is published to: `https://github.com/tanzimozer/Skill-Cabinet`
- Repo name: `Skill-Cabinet` (public)
- Push path: `fitness-trainer/` (contains `SKILL.md` + `scripts/fitness_trainer.py`)
- Push command: `git push origin main` from `/tmp/skill-cabinet/`

When updating the skill, re-push to keep the repo in sync.

## QC Self-Test Pattern (confirmed working)

Running the skill against a synthetic client end-to-end is the confirmed QC method:
1. Generate a fictional client profile with known constraints (e.g. knee injury, no dairy)
2. Run all 7 stages against it (assessment → training → nutrition → QC → stamp)
3. Verify: QC must be 12/12 pass, stamp must land on all 3 tabs, test sheet must be deleted after
4. Any QC fail = fix inline before marking the skill live

This was validated in the first live smoke test — 12/12 pass, all 3 tabs stamped, test files deleted cleanly.
