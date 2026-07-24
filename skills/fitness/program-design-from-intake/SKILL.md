---
name: program-design-from-intake
description: Design a training program from a client intake (goals, history, constraints). Use when Tanzim asks for a new program for a client.
---

# Program design from intake

Use when building a new training program for a client.

Tanzim is a former trainer; clients include Blair (RN, fitness).

Steps:
1. Capture: goal, training age, injuries/constraints, days/equipment available, timeline.
2. Pick split + weekly structure to fit days/recovery (not a generic template — fit the constraints).
3. Progression model (linear/double-progression) + deload cadence.
4. Lay it into the client's sheet structure; cite exercise selection rationale briefly.
5. Flag anything medical/peptide-related to the dedicated protocol skill — don't freelance health advice.

## Session naming convention
- Name sessions by **muscle group**, not movement pattern. "Back" not "Upper Pull". "Glutes / Hamstrings" not "Lower Pull".
- When a session is thickness-focused vs width-focused, the NAME should reflect the target tissue — "Rhomboids · Mid-Traps" or just "Back" (keep it simple per Tanzim's preference).

## Programme optimisation — the standard gap analysis

When reviewing an existing programme, run this gap scan before proposing changes:
1. **Progressive overload model** — is there a week-on-week progression rule? If not, this is the highest-leverage fix.
2. **Volume and session length** — flag any session over ~22 working sets or 70 mins.
3. **Redundant exercise pairs** — same movement pattern back-to-back (e.g. two cable rows, two vertical pulls). Cut the weaker stimulus.
4. **Missing muscle groups** — check for structural gaps (core, adductors, rear chain) relative to injury history and goals.
5. **Width vs thickness balance** — for back training, confirm the split reflects the client's actual goal. Rows = thickness (rhomboids, mid-traps). Pulldowns/pull-ups = width (lats). A client who already has wide lats needs row-dominant programming, not more vertical pull.

## Intra-set stretch protocol
- For cable/machine rows: the loaded stretch position is **arms fully extended** (not the contracted position with arms in).
- Rationale: mechanical tension is highest at end-range when the muscle is long and under load — that's the hypertrophic stimulus. Passive stretching (no load) has no comparable signal.
- Hold 3s in the extended position between sets.

## Session block structure (back thickness example)
When a client's goal is mid-back thickness, not width:
1. **Block A (Primary):** Compound rows — Chest-Supported Row + T-Bar Row. These are the thickness builders. Full scapular retraction, no torso drive.
2. **Block B (Secondary):** Mid-trap/rear delt isolation — Face Pulls, Reverse Pec Deck.
3. **Block C (Finisher — optional, deprioritised):** Width maintenance only — 2 sets lat pulldown max. Drop entirely if session is already at volume target.

## Subagent use for session builds
- Spawn Veronica (subagent) to build optimised sessions when Tanzim instructs. Brief Veronica with: client profile, goal, confirmed changes, volume target, time target.
- Veronica should run 2 QC passes before output. Flag any programming violations.

## Redundancy audit
- Use a subagent (ideally Opus) to scan the full sheet for: duplicate exercises across days, overlapping muscle group stimulus on adjacent days, redundant/conflicting tab structure, intra-session duplicates.
- Authenticate via `~/.hermes/google_token.json` — do not try the browser for a private sheet.
- Report severity: High / Medium / Low per finding.

## Pitfalls
- No cookie-cutter plans; respect injuries; don't give medical advice — defer to screening.
- Don't name sessions by movement pattern ("Upper Pull", "Lower Push") — name by muscle group.
- Three horizontal pulling variations in one session CAN be intentional (distinct mechanics: fixed/isolated, free compound, cable constant-tension) — not automatically redundant. Flag for fatigue monitoring from Week 3.
- Tab duplication in a sheet is a live version-control risk — flag it immediately if discovered.

Verify: programme fits stated days/equipment/constraints; progression + deload defined; session names are muscle-group specific.
