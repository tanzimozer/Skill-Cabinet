---
name: timbr-company-brief
description: Standing brief on TIMBR — team, product, strategy, roadmap, and comms guidelines. Load this before drafting any TIMBR communication, deck, or stakeholder-facing document.
triggers:
  - TIMBR
  - timbr brief
  - Maureen
  - stakeholder email
  - company overview
  - BlackWire
  - Taylor Crow
---

# TIMBR — Company Brief

Always spelled **TIMBR** (never Timber).

> **Radar score history:** `references/radar-scores-log.md` — full change log with current verified scores.

## Founders
| Person | Role |
|--------|------|
| Tanzim | Co-Founder — **Orchestrates · Automates · Directs**. Business strategy, infrastructure, data architecture, business intelligence |
| Sagar | Co-Founder & CTO — **Builds**. Product development, iOS platform, technical PM |

## Core Team
| Person | Role | Notes |
|--------|------|-------|
| Waseem | Strategic Tech Advisor | **Builds** — AI & automation systems. 10 hrs/month, 5-yr engagement. 2.5–4% equity, non-diluted, delivery-linked |
| Tossif | Asst. Management, Bangladesh | Full-time. Small equity vesting 5 yrs |
| Imran | Manager Level, Bangladesh | Project-based commission. Small equity vesting 5 yrs |
| Adi | Biz & Marketing Strategy | Hyper-disciplined, numbers-driven execution |
| Blair | Marketing & Sales | Social media presence, medical sales background. Nurse from Edmonton, met in Seattle as travel nurse |
| Hannah | Marketing Strategy Phase 2 | California, onboarding later |
| Taylor Crow | Trainer Affiliate | Seattle. Equinox, Hit Lab, aerial, Madison Park boutique gym owner (Jun 2026). Targets 40+ women's wellness. Sweat equity. Former Starbucks R&D 3-month contract |
| Vendors | App Foundation Dev | External team, foundational layer only |

## Products
1. **TIMBR Platform** — connects clients with local trainers. Resistance training first. Seattle boutique gym focus. Trainer = primary customer.
2. **BlackWire** — end-to-end media production factory. Raw footage + reference URL in → polished content out. Tanzim (PM/orchestrates) + Waseem (builds). Also a standalone SaaS subscription for trainers.

## Roadmap (exact order — confirmed)
1. Fitness
2. Nutrition — macro matching, local food by proximity
3. Physio — injury prevention, practitioner network
4. **Events** — weekly local fitness activations, community loop ← *before healthcare*
5. Healthcare — proprietary data plug-in, medical partnerships

## Data Layer
City-level fitness data infrastructure, Seattle-first. Proprietary, clean, structured. Built exclusively for health and fitness. Eventual plug-and-play asset for healthcare. One mental oversight, self-sustaining pipeline.

## Team Slide / Investor Deck — Skills Radar

### Last approved design (active as of session ~Jul 2026)
- **Format:** matplotlib (polar) + PIL composite. Portrait, ~1240×2073px. Script: `/home/hermes/timbr_v30.py`. Output: `/home/hermes/timbr_radar_v30.png`.
- **Tool:** `whatsapp-media-delivery` skill for delivery (direct `/send-media` curl).
- **Background:** `#000000` pure black. Footer: white `#FFFFFF`.
- **Font:** Roboto throughout (radar labels via `matplotlib.rcParams`, cards via PIL `ImageFont.truetype`).
- **Radar axes (13, in order):** AI/ML · Backend · Mobile Dev · Frontend · Data & Analytics · Product · Marketing · Sales · Growth · Leadership · Fitness Domain · Athlete · Videography
- **Axis label notes:** "Fitness Domain" renders as two lines (`Fitness\nDomain`) in matplotlib. "Product Strategy" was renamed to just **Product**. "Cinematography" was renamed to **Videography**.
- **Radar rotation:** half-spoke width (`np.pi / 13`) to prevent 12 o'clock / 6 o'clock label collision.
- **Fill opacity:** 7% per polygon.
- **Colour coding:** Tanzim = cyan `#00c8f0` · Sagar = green `#00d96b` · Waseem = orange `#ff6500`
- **Radar scores (axis order as above — verified, source-only, zero if unconfirmed):**
  - Tanzim:  `[5, 3, 0, 7, 8, 8, 4, 7, 9, 9, 9, 0, 0]`
  - Sagar:   `[8, 9, 7, 7, 7, 8, 0, 0, 0, 6, 6, 0, 0]`
  - Waseem:  `[9, 5, 10, 9, 5, 8, 0, 0, 0, 9, 6, 0, 0]`

### Score policy
- **Source-verified only** — zero if no data, no filling in guesses.
- Scores updated iteratively by Tanzim via WhatsApp. Always take his word as authoritative.

### Footer (3-line white bar)
- Line 1 (bold, dark): "Looking for a Seattle local videographer, marketer and athlete to join our founding team for sweat equity."
- Line 2 (regular, grey): "We highly encourage University of Washington students to join for impactful equity."
- Line 3 (small, light grey): "© TIMBR FITNESS TECHNOLOGIES"

### Card structure — PIL-rendered (current)
Cards are drawn in PIL (not matplotlib axes-within-axes — that broke at tall aspect ratios). Rendered as a PIL composite below the radar.

1. Accent-colour top bar
2. Name (bold) + role title
3. Narrative line — story-driven, NOT a CV list (companies only, no cert bodies)
4. Highlights block — 2 standout achievements
5. Domain tag chips

### Card content
**Tanzim** · Co-Founder · Product & Data Architecture · TIMBR · US Bank · 24 Hour Fitness  
Narrative: "Took 24 Hour Fitness 255→87 nationwide. Closed $5.7M for US Bank in 9 months."

**Sagar** · Co-Founder · Chief Engineer  
Narrative: "Built the security wall for Amazon Prime Card. Now wiring every layer of TIMBR's stack."

**Waseem** · Founding Senior Engineer · AI Systems & Agentic Workforce  
(credentials from background — source-verified)

### Card copy rules
- No C-suite titles (no CEO/CTO)
- Credentials = company names only, never cert bodies
- Descriptions must tell a story, not read as a bullet CV
- Titles must reflect actual function, not org hierarchy

### Veronica QC checklist for deck renders
- All 13 radar axes visible and labelled
- No text clipping on axis labels (especially Sales at 6 o'clock — rotation fix prevents this)
- Cards equal visual weight
- Footer 3 lines all visible with even spacing
- Minimum score: 8/10 before sending (7.5 accepted if content independently verified correct)

## Comms Guidelines

### For Maureen Searle (mentor/advisor — alex4sea1@gmail.com)
- **Avoid all AI language** — she is not enthusiastic about AI
- Use: "operational systems", "automated pipelines", "efficient systems", "self-sustaining"
- Do NOT mention: salaries, equity details, AI tools, model names
- Tone: warm, professional, strategic — she's a sharp advisor, not a pitch audience
- She already knows the founders — skip org chart intros, lead with what we're working on

### General stakeholder email structure (3-part)
1. **What me and Sagar are working on** (platform)
2. **What me and Waseem are working on** (BlackWire / infrastructure)
3. **Where we're headed** (roadmap)

### Tone
- Confident, clean, no jargon
- Lead with current work, not org structure
- Boutique gym market angle (growing fast) over big chain angle
- City-level infrastructure framing — ambition is clear without being grandiose
