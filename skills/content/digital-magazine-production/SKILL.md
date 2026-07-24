---
name: digital-magazine-production
description: Structure, pricing, and competitive positioning for digital fitness/lifestyle magazines and PDF programs
tags: [content, publishing, fitness, magazines, pricing, market-research]
---

# Digital Magazine Production

Guide for creating, structuring, and pricing digital fitness/lifestyle magazines (PDF format) for direct sale.

## When to Use

- Building personality-driven fitness magazines (training + nutrition + lifestyle blend)
- Pricing digital fitness content products
- Structuring magazine content for professional editorial quality
- Competitive analysis for digital fitness PDFs and programs

## Market Context

### Digital Fitness Product Landscape (2024-2026)

**Top Digital Fitness Programs (by revenue/influence):**
1. **Stronger by the Day (Meg Squats)** — $8/month subscription model
2. **SWEAT by Kayla Itsines** — App-based $20/month (started as $50-70 PDFs)
3. **Shredded by Science (Jeff Nippard)** — Individual programs $50-150/PDF

**Pricing Tiers:**
- **Low end:** $10-20 (basic workout PDFs, minimal depth)
- **Mid tier:** $20-50 (personality-driven content + training insight)
- **High end:** $50-150 (comprehensive 8-12 week periodized programming)

**Revenue Benchmarks:**
- $5,000 milestone = 251 units at $19.99
- $5,000/month recurring = 251 units/month
- $500k revenue = 25,013 units total (or ~8,338 per mag for 3-mag series)

### Competitive Advantage: Personality + Lifestyle Blend

Digital fitness magazines succeed when they sell **the person's full system**, not just workouts:
- Training philosophy and methods
- Nutrition at macro level with practical application
- Lifestyle integration (travel, social dining, work routines)
- Local spots, personal hacks, insider access
- Q&A and personality-driven content

This differentiates from rigid 12-week programs and justifies mid-tier pricing ($19.99-$49.99).

## Professional Magazine Structure

### Standard 75-Page Layout

**FRONT MATTER (pp. 1-5)**
- Editor's Letter — Philosophy, why this exists (1 page)
- Contributors & Credits — Who they are, credentials, social (1 page)
- How to Use This Magazine — Program overview, macro guide, reading order (1 page)

**FOUNDATIONS (pp. 6-15)**
- Training Philosophy — Core beliefs, what makes this different (2 pages)
- Fitness Mistakes — What didn't work, lessons learned (2 pages)
- Current Phase Breakdown — Periodization, training phases explained (2 pages)
- Supplement Stack Deep Dive — What, when, why for each supplement (4 pages)

**THE PROGRAM (pp. 16-35)**
- Week 1: [Phase Name] — Full programming (5 pages)
- Week 2: [Phase Name] — Progressive detail (5 pages)
- Week 3: [Phase Name] — Intensity progression (5 pages)
- Week 4: [Phase Name] — Deload/recovery (5 pages)

*Each week: exercises, sets/reps, tempo, rest, technique cues, optional video QR codes*

**NUTRITION (pp. 36-50)**
- Macro Framework — How to calculate personal numbers (3 pages)
- Phase-Specific Macros — Adjustments for different training phases (2 pages)
- Meal Prep Blueprint — Shopping list, batch-cook strategy (3 pages)
- Restaurant Survival Guide — Social dining strategies (2 pages)
- Travel Hacks — Airport meals, hotel gyms, on-the-road macros (2 pages)
- Common Tracking Mistakes — Portion errors, measurement pitfalls (2 pages)

**LIFESTYLE (pp. 51-65)**
- Daily Routine — Work schedule, productivity hacks (3 pages)
- Social Strategy — Alcohol, dining out, maintaining progress (2 pages)
- Local Spots — Cafes, restaurants, healthy eats with photos (5 pages)
- Travel + Fitness — Staying consistent while traveling (2 pages)
- Recovery Rituals — Sleep, supplements, active rest (3 pages)

**Q&A (pp. 66-72)**
- Compiled questions covering training, nutrition, mindset (7 pages)
- Use persona extraction content here

**BACK MATTER (pp. 73-75)**
- Progress Tracker — 4-week log for training, macros, weight, photos (2 pages)
- What's Next — Program extension, social follow, upcoming content (1 page)

### Why This Structure Works

1. **Front-loaded personality** — Buyers purchase the person, not just workouts
2. **Program is anchor but not entire product** — Differentiates from basic PDFs
3. **Nutrition depth** — Most competitors skimp here; going macro-level + practical adds value
4. **Local spots = unique** — Insider access feel, nobody else provides this
5. **Q&A personalizes** — Uses persona extraction content already being built

### Production Quality Notes

- Mix text with imagery (training shots, food photos, cafe images)
- Infographics for macros, workout splits, phase breakdowns
- QR codes to video demos if available
- Clean typography, white space — premium feel, not cluttered
- Consistent branding throughout

## Sales Strategy (7-Day Launch)

**To sell 251 units in 7 days:**

**Math:**
- 251 units ÷ 7 days = 36 sales/day
- At 2-5% conversion = 720-1,800 visitors/day to sales page

**Requirements:**
- Creator has engaged audience (5k+ followers, high engagement)
- Email list exists and is warmed up
- Landing page + payment flow ready
- Creator willing to promote hard for 7 days (stories, posts, emails, DMs)

**Blockers:**
- Cold audience (no following, no email list)
- No promotion plan ("build it and they'll come")
- Magazine not finished yet
- Creator won't actively promote

**Critical distinction:** 7-day sprint for **building** vs. 7-day sprint for **launch + sales** are two different projects. Layering both is aggressive but achievable only if audience + promotion infrastructure exists.

## CHANGES Tab — MCP Execution Log

When populating the CHANGES tab in Magazine Production sheet, track against this checklist:

| Page | Type | Records per issue | Notes |
|------|------|-------------------|-------|
| 1 | Dynamic | 3 (UPDATE_TEXT, REMOVE_ELEMENT, ADD_ELEMENT) | Cover changes |
| 2 | Dynamic | 4 (3× UPDATE_TEXT + 1 extra) | TOC + intro |
| 3 | Dynamic | 4 (ADD_ELEMENT ×3, UPDATE_TEXT) | Programme + cross-sell |
| 4 | Dynamic | 4 (UPDATE_TEXT, UPDATE_TEXT, ADD_ELEMENT ×2) | Gym spotlight — **easy to skip, audit explicitly** |
| 5 | Dynamic | 4 (UPDATE_TEXT ×2, ADD_ELEMENT ×2) | Lifestyle chapter |
| 6 | Dynamic | 4 (ADD_ELEMENT, UPDATE_TEXT ×2, ADD_ELEMENT) | Recovery — hook + muscle-specific zones + sleep + Zone 3 |
| 7 | Static | 0 | Identical across all issues — no CHANGES entries |
| 8 | Static | 0 | Identical across all issues — no CHANGES entries |

**Series 01 total:** 95 records (CHG-001–CHG-095), plus 20 for Page 4 (CHG-096–CHG-115) = **115 records**

**Always verify page distribution after populating** — run a count grouped by Page column. Page 4 was missed entirely in one session and only caught on audit.

See `references/timbr-changes-mcp-prompt.md` for the full MCP execution prompt to hand Claude when running CHANGES tab against Canva.

## Pitfalls

1. **Treating it as a workout PDF** — Fitness programs alone are commoditized; personality + lifestyle blend justifies pricing
2. **Skipping local spots / lifestyle sections** — These are unique differentiators that competitors don't provide
3. **Macro-light nutrition** — Generic "eat clean" advice doesn't justify $19.99; specific macro breakdowns and phase adjustments do
4. **Assuming organic sales** — 251 units in 7 days requires active promotion from creator with existing audience
5. **Building without audience validation** — Creating 3 magazines before confirming Blair/Shumon/Taylor have audiences ready to buy

## Canva API Integration

See `references/canva-oauth-setup.md` for OAuth flow with localhost callback (used when assistant exchanges auth code for token on user's behalf).

See `references/canva-content-population.md` for the actual workflow that works — Canva API cannot edit text elements directly; use Google Doc as copy-paste source instead.

See `references/timbr-workout-series-template.md` for the confirmed 8-page TIMBR Workout Series issue structure, exercise order pattern, cross-sell pattern, and Magazine Production sheet format.

See `references/editorial-bible-and-blair-crossmatch.md` for the full editorial methodology, benchmark magazine analysis, Blair Issue 01 section-by-section cross-match results, and priority fix list.

See `references/timbr-product-lineup.md` for the authoritative product lineup — what's in production vs what's already done (Foundation Series). Critical distinction: Foundation Series ebooks ≠ Personality Magazines.

## Product Lineup — Key Distinction

**Foundation Series (11 ebooks):** Already done and uploaded to Wix. Standalone muscle-group workout programmes. NOT in the personality magazine production queue. Do not conflate.

**Personality Magazines (3 in production):**
1. Blair Grimes Issue 01 — content doc complete, Canva in progress
2. Shumon Asef Issue 01 — NO content doc yet (only video files in Drive). Content extraction needed before any Canva work.
3. Taylor Crow Issue 01 — NO content doc yet. Same situation.

**Critical:** When Tanzim asks "what are we producing", the answer is 3 magazines — Foundation Series is separate and done.

## Platform Migration

See `references/wix-to-webflow-migration.md` for full decision rationale, API limitations, migration scope, credential requirements, execution log (May 2026), and pitfalls. Includes:
- Which Webflow token type to get (site-level, NOT workspace-level — they look identical but workspace tokens have no site scopes)
- Webflow plan tier gate: page creation via API requires CMS plan+; Starter plan blocks it
- Wix blog API does NOT return post body text — only title, slug, excerpt, category IDs
- HTTP 202 from Webflow CMS = success (draft created), not failure
- Don't spawn one subagent for the full migration — times out; execute phase by phase

Short version: Webflow is the right call when there's no existing SEO traffic and you want programmatic content control. Credentials must arrive with codeword in the **same message** — never store a token sent without codeword authorization.

## Editorial Bible — Benchmark Methodology

Derived from Women's Health, Elle, Shape, Self editorial practice. Stored in Magazine Production sheet tab "EDITORIAL BIBLE".

### 3-Layer Article Structure
Every article uses exactly this order:
1. **Hook** — Provocative/relatable opener. Never a question. Grabs immediately.
2. **Authority Anchor** — Expert, credential, or stat in first 2–3 sentences. Earns trust.
3. **Actionable Payoff** — Specific steps, numbers, timeline. Reader buys the promise.

### Tone Rules
- Always 2nd person ("you", never "women" or "people")
- 12–14 word average sentence length, active voice only
- Aspirational-but-attainable: "strong" not "skinny", "energy" not "weight loss"
- No jargon without a same-sentence gloss

### Power Phrases That Convert
| Phrase | Why |
|--------|-----|
| "Here's exactly how to..." | Signals precision, real answer coming |
| "The truth about..." | Implies insider knowledge, myth-busting |
| "What experts actually recommend" | Authority + the word 'actually' |
| "In X weeks" | Time-bound promise, achievable and specific |
| "You don't need to..." | Removes objection, reader relaxes |

### Standard 9-Section Order (Women's Health / Elle formula)
1. **Cover** — One promise, not a description. "Lean & Strong in 6 Weeks" not "Fitness Guide Vol 1"
2. **Editor's Letter** — 1 page, first person, personal story, warm close
3. **Quick Hits** — 2–3 scannable pages, 50–80 words per item
4. **Feature Story** — 4–6 pages, one hero story, specific details, journey arc
5. **Programme** — Visual-heavy. Every exercise: name + sets + reps + rest + coaching cue
6. **Nutrition + Grocery List** — Grocery list is non-negotiable. Most-used page in fitness mags.
7. **Mindset / Lifestyle** — Sleep, stress, recovery. Whole-person feel.
8. **Products** — Max 4–6 items, one-line reason each. Never feel like an ad.
9. **Back Page** — Vol. 02 tease. Essential for series continuity.

### Cross-Match Process (Blair reference, May 30 2026)
When a new trainer content doc exists, run this before touching Canva:
1. Pull content doc from Drive
2. Check each section against this 9-section order
3. Flag: ✅ strong / ⚠️ needs fix / ❌ missing entirely
4. Build a PRODUCTION TRACKER tab in Magazine Production sheet with priority fixes
5. Estimate time per fix, order by impact
6. Only then open Canva

**Blair Issue 01 findings (May 30):** Content doc was strong but missing grocery list and Vol.02 tease. Cover line was descriptive not a promise. 3rd person used throughout — needs flip to "you". Cardio section lacked scannable phase table. Full priority list in BLAIR—PRODUCTION TRACKER tab.

### Common Gaps to Check on Every Issue
- Cover line is a **promise**, not a topic title
- Grocery list present (even 10–15 items)
- Vol. 02 tease on closing page
- All "Blair/trainer does X" flipped to "here's how YOU do X"
- One anchor stat per article (adds credibility)
- Cardio/phase content formatted as a table, not paragraphs

## Wix Digital Library — Shop Structure

When building the TIMBR shop page on Wix, frame it as a **collection** ("TIMBR Digital Library"), not individual downloads. Think Netflix shelf.

### Series framing
- **Series 1 — Trainer Magazines** (personality-led): Blair, Shumon, Taylor — $19.99 each / $49.99 bundle
- **Series 2 — Foundation Workout Series** (programme-led): already done, $9.99 each / $39.99 bundle

### Per-listing rules
- Cover image: full bleed, portrait orientation, magazine-quality — this IS the sell
- Description: 3-line hook max — not a contents list, a promise
- Label every issue "Vol. 01" — signals series, creates anticipation for Vol. 02
- Free teaser page per magazine → email capture → sell full PDF to warm list

### Pricing psychology
| Price | Psychology | Use for |
|-------|-----------|---------|
| $9–12 | Impulse — no hesitation | Entry product, low-page PDFs |
| $17–27 | Perceived value sweet spot | Full magazines (20–40pp) |
| $47+ | Needs social proof first | Bundles, complete series |

## Gmail / Job Automation Crons

Three crons active (created May 30, 2026):

| Job ID | Name | Schedule | Purpose |
|--------|------|----------|---------|
| 8b19da12 | Gmail Cleanup — Nightly Junk Scan | 11:45 PM daily | Flags junk by category, sends list to Tanzim for delete permission — never deletes without approval |
| 2eefd5d0 | Morning Job Brief | 9:00 AM daily | Scans Gmail for interviews today, actions needed, new recruiter outreach — sends to WhatsApp |
| 7a02da23 | Memory Organisation + Identity Audit | 3:00 AM daily | Consolidates memory, audits identity map, runs silently unless anomaly found |

**Nightly sweep categories:** Job rejections, marketing/newsletters, app notifications, receipts (no action needed), other low-value. Always flags — never auto-deletes.

**Morning brief rule:** Only report what is verifiably in Gmail. Never invent tasks, names, or deadlines. Hallucinating a fake interview (as happened May 2026 — Housecall Pro/Precious Barton) is a hard failure.

## Related Skills

- `timbr-magazine-production` — **OVERLAPS with this skill** (Workout Series template, Canva export patterns, Magazine Production sheet structure). Prefer `timbr-magazine-production` for TIMBR-specific operational work; use this skill for editorial methodology, pricing research, and market positioning.
- `content-extraction` — Persona questionnaire rounds for magazine content
- `canva-design` — Magazine layout and production
- `wix-digital-products` — Sales page and payment setup
