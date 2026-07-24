---
name: timbr-context
description: Living context document for TIMBR — the company, team, product, and roadmap. Load when working on any TIMBR task, communication, or visualisation.
triggers:
  - "TIMBR"
  - "timbr"
  - "the app"
  - "Sagar"
  - "Waseem"
  - "Towsif"
  - "Imran"
  - "Blair"
  - "Taylor"
  - "BlackWire"
  - "Maureen"
---

# TIMBR — Company Context

## Brand
- Always spelled **TIMBR** — never "Timber"
- Domain: timbr.fit
- Based in Seattle

## Founders & Roles
- **Tanzim** — Co-Founder. Orchestrates, automates, directs. Business strategy, data architecture, infrastructure, business intelligence. Background: 8+ years in ops/PM (Guckenheimer → 24 Hour Fitness → TIMBR LLC → US Bank). 12 years in fitness (Master Trainer → Sports Nutritionist → Sales Manager → General Manager). At 24HR: ranked location 255th → 87th nationally in 6 months. At US Bank: top 10 district producer in 9 months, zero banking background. At TIMBR (PM phase): delivered MVP 45 days early, 6% under budget; built AI automation (n8n + MCP), cut design-to-deploy cycle 30%. Before moving to USA, ran a supplement import/export brokerage from USA to Dhaka, Bangladesh. Based in Seattle, WA. Licensed personal trainer and nutritionist. PMP exam July 2026. His own words: "This resume is not my full picture, it's a part of me."
- **Sagar G.** — Co-Founder & CTO. Builds. Product development, iOS platform, technical PM. Day job: L5 SWE II at Amazon. Full operational authority on TIMBR APP equal to Tanzim's (except codeword-protected actions).

## Core Team
- **Waseem Ahmad** — Strategic technology advisor & AI engineer. Staff SWE at Nextdoor (Feed UX, Android); ex-Meta 7 years (Facebook app → Reality Labs AR/VR); ex-Google intern. Rice University CS. US patent (payment routing, Meta intern project). Builds Claude Code tooling adopted org-wide at Nextdoor. Builds voice AI agents on nights/weekends. Private pilot, Cirrus SR22, Seattle. 10 hrs/month, 5-year engagement. **2.5–4% equity (non-diluted, delivery-linked — exact % not yet finalised)**. Pioneer-level AI operator — 60hrs of output in 10hrs. Stance: bootstrapping over fundraising; raising is last resort. His view: execution speed and leadership talent are the real bottlenecks, not capital.
- **Towsif** — Media & operations, Bangladesh. Full-time. Small equity (<1%) vesting 5 years.
- **Imran** — Hiring & operations, Bangladesh. Runs his own education institution in Bangladesh. Project-based commission. Small equity (<1%) vesting 5 years.
- **Adi** — Business & marketing strategy. Numbers-driven, hyper-disciplined execution.
- **Blair Grimes** — Fitness model and TIMBR magazine subject. BSN-RN (registered nurse). Tanzim's trainee. Social media presence.
- **Hannah** — Second-phase marketing strategy. California. Onboarding later.
- **Taylor Crow** — Main Seattle trainer. Has her own studio, also trains at HITTlab and Equinox. Just opened boutique gym in Madison Park. Works with TIMBR on sweat equity basis.
- **Vendors** — Engaged for foundational app development layer.

## Products

### TIMBR Platform (Engine 1)
- Sagar builds, Tanzim directs
- Connects clients with local trainers — resistance training first
- Seattle launch, boutique gym focus
- iOS first, Android v1.5 later
- Trainer = primary customer

### BlackWire (Engine 2)
- Waseem builds, Tanzim orchestrates
- End-to-end media production factory
- Trainer drops iPhone footage + reference URL → polished publication-ready content out
- Standalone SaaS subscription product for trainers
- Generates cash flow independently of the main platform

## Roadmap (in order)
1. **Fitness** — Platform + BlackWire live, Seattle trainer network
2. **Nutrition** — Food layer, macro matching, local restaurant integration, proximity-based
3. **Physio** — Practitioner network, injury prevention, longevity
4. **Events** — Weekly fitness activations, community loop, social fitness culture
5. **Healthcare** — Proprietary city-level health data plug-in, medical partnerships

## Data Strategy
City-level fitness data infrastructure — clean, structured, proprietary. Built exclusively for health and fitness. Eventually a plug-and-play layer for healthcare/medical services.

## Key contacts
- **Maureen Searle** (alex4sea1@gmail.com) — long-term mentor/advisor. Warm, sharp, invested in Tanzim's success. **Not enthusiastic about AI** — avoid AI language in anything sent to her. Use "systems", "pipelines", "automation" instead.

## Communication rules for Maureen
- No AI language
- No mention of salaries or equity details
- No mention of agent/subagent architecture
- Frame automation as "operational systems" or "infrastructure"

## Reference files
- `references/app-store-market-data.md` — App Store market data: Health & Fitness and Finance category sizes, most-crowded categories, demand>supply opportunity gaps. Load for competitive analysis or investor deck work.
- `references/tanzim-resume-summary.md` — full career timeline, resume file IDs, key outcomes, certifications, and the insight that his titles consistently undersell him.
- `references/maureen-email-template.md` — email template for Maureen.
- `references/plan-generation-engine.md` — the workout plan-generation architecture: exercise DB data model (8-col header; dual Strength/Performance + Strength/Aerobic classification is DESIGN INTENT, the Aerobic-tag column is not yet built — verify the live header), the Foundation/Strength/Performance branching taxonomy with F3 convergence, the 9-stage MB/FL journey maps, scoring formulas, muscle-pairing matrix rules, source-of-truth sheet IDs + verified DRAFT tab/gid map, Sagar's "step 2" definition asks (composite F0–F3, MB:fat-burn ratio), the safe-edit discipline for sheets Sagar reviews, and Tanzim's working style for this project. Load for any exercise-DB / stages / pairing / plan-gen work.
- `references/selection-engine-design.md` — the BUILT plan-generation engine module: STAGE_MAP (stage→tier+difficulty cap), day-label→muscle resolver, the pick rule (filter by muscle+cap, sort hardest-first, big=2/small=1 exercises, conditioning finisher), the big-upper/big-lower guardrail, and known limitations. Rebuild/extend from this — the pick-rule question is answered.
- `references/exercise-scoring-methodology.md` — the exercise-scoring model critique & v2 direction: v1 formulas, the 6 structural flaws (4-spoke review converged), v2 fixes (Risk-as-gate, kill solo spotter −3, Stability single-count, normalise, bands-not-decimals, Skill×2 over Strength×2), the CRITICAL data-modeling pitfall (DBs store computed values not raw sub-inputs → formula retrofits need a full re-score), the "is it scientific" honest answer, and the non-destructive 3-stage-QC workflow. Load for ANY exercise-DB scoring / methodology / Sagar-review work.
