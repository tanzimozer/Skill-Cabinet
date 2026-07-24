# Validating a Classifier / Decision Framework

How to stress-test a threshold-based classification framework *after* you build it.
Distilled from the Nimbus Engine session (Jul 4 2026): a workout exercise
classifier (S1/S2/S3) built on two axes + a gated modifier, then adversarially
audited.

## The core discipline: fitted ≠ validated

The trap that bites hardest: you tune thresholds to the labelled data, report a
high match rate, and call it validated. It isn't.

- If you searched threshold space to *maximise* agreement with the stored
  labels, the resulting match rate (e.g. "93/97 = 95.9%") is a **fitted**
  number, not a validated one. It is circular until you test against examples
  **not in the training set**.
- Always say this out loud in the verdict. "95.9% — but I tuned the thresholds
  to hit it" is the honest report. "95.9% accurate" alone is misleading.
- Real validation = hold-out cases the framework has never seen. In the Nimbus
  session, the honest next step was a blind game of naming exercises *not* in
  the 97-row DB and checking the calls.

## The collinearity trap: "two axes that are really one"

A framework can *claim* N independent inputs while secretly running on one.

- Compute the correlation between your supposedly-independent axes. If
  Pearson r is high (Nimbus: Physical–Technical r=0.875, raw inputs r=0.935),
  the second axis is doing little or no independent work.
- Symptom: one gate never fires independently — e.g. every low-A row is also
  low-B, so gate B only ever splits rows gate A already flagged.
- Root cause is usually **shared sub-inputs**: axis A and axis B both derive
  from the same primitive (Nimbus: "Skill" was double-weighted inside
  Difficulty *and* was the basis of Learning Curve). Trace each axis back to
  its primitives and look for reuse.
- The fix is not more gates — it's re-deriving the axes so they draw on
  disjoint primitives. State plainly when the design is "one axis in a
  two-axis costume."

### Collinearity can live in the DATA, not the formula (you can't tune it out)

Follow-up lesson (Jul 4 2026, same Nimbus DB, deeper pass): after re-deriving
the two axes from *disjoint* computed primitives (the correct fix above), the
correlation barely moved — r=0.875 → 0.833. The remaining collinearity was **a
property of the exercise library, not the maths**.

- Root cause: the items themselves lay on a single "hard ↔ easy" diagonal.
  Everything physically brutal (barbell squat/deadlift/press) was *also*
  technically hard; everything physically trivial (machine curl, cable
  pushdown) was *also* technically trivial. The **off-diagonal was empty** —
  no heavy-but-brainless item, no light-but-fiendish item.
- A second axis only earns its keep when items *disagree* between the two axes.
  If your data has no disagreement, two axes measure the same thing no matter
  how cleanly you derive them. The formula cannot manufacture independence the
  data doesn't contain.
- Diagnostic: after re-deriving axes, if r stays high, stop tuning the formula
  and inspect the item distribution. Plot/scan the off-diagonal quadrants
  (high-A/low-B and low-A/high-B). If they're empty, that's your answer.
- The real fix is **expanding the dataset with off-diagonal items** (e.g. heavy
  sled push = high load/low skill; pistol squat = low load/high skill), then
  recomputing. Say this plainly; don't promise the formula will separate axes
  the data has fused.

### Remediation hierarchy: fix the primitive, never bolt on an override

When a single item lands in the "wrong" tier and the user wants it moved, there
is a strict order of correct fixes. Nimbus session climax — the user themself
caught the wrong one and rejected it:

1. **BEST — fix the input primitive that's mis-scored.** If a barbell bench
   press scores too low on the Physical axis because the axial-load rule gave a
   braced press a 0, the *error is the primitive*, not the threshold. Correct
   the primitive so the item reaches the right tier **on merit** — the score
   moves it, keeping the model reproducible and auditable. Price: fixing a
   primitive rule may nudge other items sharing that primitive. Always dry-run
   and show the full diff before writing.
2. **WORST — a hard floor / implement override** ("free-barbell compound = S3
   minimum"). This is the trap. It *repeats the exact error the two-axis model
   was built to kill*: letting one attribute (implement) dictate tier regardless
   of the computed axes — the same "Skill baked into everything" collapse in a
   new costume. The user's own history had already caught this (barbell
   curl/shrug wrongly forced up by the bar). A floor also has a huge, hidden
   blast radius: dry-running "free-barbell multi-joint = S3" on Nimbus collapsed
   S2 from 15 rows to 2 and ballooned S3 to 30, sweeping in rows, hip thrusts,
   and rollouts nobody asked to promote.
3. Between the two: narrowing a floor to a cluster ("presses only") is *less*
   wrong but still a floor — it will mis-fire the day a light technique-primer
   item enters that cluster. Prefer it only as a stopgap, and name the future
   failure mode out loud.

Always DRY-RUN any proposed rule against the full dataset and print the exact
blast radius (which rows promote/demote, final distribution) BEFORE writing to
the sheet. A rule that sounds surgical in prose ("free-barbell compound") is
often a wrecking ball in the data — the print is the only way to know.

### A rescaled model needs rescaled thresholds

When you swap hand-scored inputs for computed primitives, the axis *scale*
changes — a locked "high ≥ 9" threshold from the old scale can become
unreachable (Nimbus computed Physical maxed at 8, so ≥9 could never fire).
After any primitive redesign, re-derive the thresholds from the new score
distribution; don't carry old cut-points across a scale change.

### Capstone: when the redesign IS the over-engineering — abandon it, say so

The Nimbus rebuild's honest ending (Jul 4 2026, later pass): after all the work —
8 computed primitives, new axes, recalibrated thresholds, a whole new sheet tab —
the verdict was to **rip the redesign out and keep the original 2-gate formula**
(`Difficulty ≤5→S1 | else LearningCurve ≤7→S2 | else S3`). The rebuild was a
finding, not a product: it *proved* the axes can't separate on this data. That
proof is valuable; the machinery to reach it was not worth keeping.

Lessons that transfer to any "improve the model" request:

- **Diagnose the objective error in ONE sentence before building anything.** Here
  it was: "the two axes aren't independent — Skill is baked into both, so
  r≈0.96, you're paying for two axes and getting one." Everything else was
  symptom. If you can't state the error in a line, you're not ready to redesign.
- **Test the CHEAP fix before the expensive one.** When the user asks "there
  should be a simpler solution — suggest an alternative," take them literally.
  The simplest fix for a double-counted primitive is to *delete it from one axis*
  (strip Skill out of Difficulty), not rebuild the model. Dry-run it: here it
  moved r=0.935→0.903 (~0.03) and collapsed the middle tier to 4 rows — i.e. it
  *also* failed, for the same data-property reason, in ten seconds instead of a
  day. Proving the cheap fix fails is itself the argument for the honest verdict.
- **Collapsing to one axis can be the truthful answer.** If two axes provably
  can't separate on the data and the user won't expand the dataset, the honest
  model is ONE hardness scale with three bands — not two axes in a costume. Say
  "it's one axis; stop pretending" plainly.
- **A full rebuild that lands you back at the original formula is not wasted IF
  you name it as a finding.** Don't defend the redesign to justify the effort;
  report "this proved X, and X says keep the simple thing." Sunk cost is not a
  reason to ship complexity.
- **"Fix the S123 labels" often has nothing to fix.** When the user says clean up
  the labels, first run the formula against every row and count mismatches. On
  this DB the answer was 97/97 already correct — zero drift. The honest
  deliverable was a QC report (formula match, ranges, blanks, dupes, coherence)
  committed as the record, NOT inventing edits to look busy. Editing a clean
  sheet manufactures a problem. And when your own audit script flags
  "divergences" (Hack Squat, Lat Pulldowns scored unlike their cluster-mates),
  check whether it's YOUR classifier mis-tagging (implement auto-detector
  defaulting machines to "barbell") before blaming the sheet — false positives
  from your tooling are not data errors.

## The unstated invariant: "97/97, but it's unguarded, not correct"

The most useful finding on a framework that *passes* its own data. A formula can
be 100% correct on the current dataset **and still latently broken**, because it
silently relies on a correlation the spec never wrote down or enforced. This is
the flip side of the collinearity trap: there, correlation makes a second axis
redundant; here, correlation is the *only* reason the formula passes — and
nothing guards it.

Distilled from the Nimbus re-review (a later "my confidence is low, stress-test
it" pass on the same S1/S2/S3 formula: `Diff ≤5→S1 | else LC ≤7→S2 | else S3`).

- **The pattern:** a gate short-circuits before a second input is ever read
  (once `Diff ≤ 5`, Learning Curve is never consulted → straight to S1). This
  *looks* like a bug (an ignored input), but on the real data it never mis-fires
  because low-Difficulty items are also always low-LC. The formula is correct —
  but only *because* the axes are collinear, a fact it neither states nor
  enforces.
- **State the load-bearing invariant explicitly.** Here it was:
  `low Difficulty ⟹ low Learning Curve`. The formula is valid **iff** this holds.
  It's load-bearing and invisible — nothing in the sheet asserts or checks it.
  Naming it out loud is 80% of the value; it's usually *why* the user's gut says
  "low confidence" without being able to point at a failing row.
- **The hole is the empty off-diagonal quadrant.** The one item class that breaks
  it is the one the dataset happens not to contain: **low-Difficulty + high-LC**
  (a light-load but highly *technical* move — a skill primer, a lightly-loaded
  Olympic derivative, a pistol/TRX-type drill). It routes to S1 (anyone,
  unguided) despite "months to own, technical failure dangerous." Note the
  structural corollary: because S3 requires `Diff > 5 AND LC > 7`, a
  dangerous-but-light lift can **never** reach S3 — a whole tier is unreachable
  for that quadrant.
- **Tie it back to the empty-off-diagonal diagnostic** (see collinearity section):
  the invariant holds *only* because that quadrant is empty in the current
  library. The day someone adds an off-diagonal item, the latent fault becomes an
  active one. "Works today because the data honours a rule you never wrote down."
- **Verdict language:** the formula isn't broken, it's **unguarded**. Don't call
  it wrong (it's 97/97) and don't call it safe. Say: correct-but-latent — it
  depends on an unstated, unenforced invariant.
- **Remediation — respect the hierarchy above.** The *cheap, correct* fix is a
  **validation assert**, not a new routing rule: flag any row where
  `Diff ≤ 5 AND LC ≥ 7` (or ≥8) as needs-review. Zero hits today; it catches the
  off-diagonal item the day it's added — a tripwire, not a classifier change. A
  reordered gate (`IF LC ≥ 8 → S3` first) is a real routing change: dry-run its
  blast radius first, and be aware it's closer to a "floor" than the assert is.
- **Beware re-diagnosing blind.** On the *first* (no-sheet) pass this session, the
  cold read was "the formula ignores LC and muddles skill-tier with
  intensity-tier" — plausible but **wrong** once the actual rubric was in hand
  (the axes are intentional and defined; they just happen to be collinear). Lesson:
  a formula shown without its rubric invites a confident-but-wrong critique. Pull
  the spec (rubric tab, axis definitions, score distribution) BEFORE delivering a
  verdict. The refined finding (unstated invariant) is far sharper than the blind
  one (ignored input) and only reachable with the data open.

## Break-hunting a "passing" formula with the live sheet open (three durable break-classes)

When the user says "test it, I know it will break, you have N attempts," don't
theorise — pull the actual data and find breaks with **named rows and real
numbers**. Distilled from the Nimbus "3 attempts to break it" pass (same
`Diff ≤5→S1 | else LC ≤7→S2 | else S3` formula, live STRENGTH DB open). The
formula reproduced all 97 labels, so the arithmetic wasn't the target — its
*validity* was. Three break-classes recurred, each provable from live rows:

1. **The verbal rule you've been preaching may not exist in the engine.**
   All session the agent asserted an "isolation floor" (single-joint → S1). The
   DB's own **Barbell Front Raise** and **Barbell Curl** — both single-joint
   isolation — compute **S2** (Diff 7, LC 7). The formula has *no joint-count
   term*; it never floored isolation. It only *looked* like it honoured the floor
   because most isolation happened to score low. Lesson: when you catch yourself
   quoting a rule ("isolation caps at S1", "machines are always S2"), grep the
   actual data for the counterexample before trusting your own narration. A
   verbal invariant the formula doesn't encode is a landmine — the two disagree
   the moment a high-scored isolation row appears.

2. **A `≤ threshold` gate silently eats a whole band of the next axis.** The
   `Diff ≤ 5` gate fires before LC is ever read — so LC 6 *and* LC 7 under Diff 5
   land in S1 unconsulted, same bucket as a leg press. The earlier `LC ≥ 8 → S3`
   guard only plugs the *top* of the hole; LC 6–7 still fall straight through.
   Lesson: an early gate on axis A mutes axis B across A's entire pass-band, not
   just at the extreme. When auditing a short-circuit gate, enumerate *every*
   value of the muted axis that the gate swallows, not only the dramatic one.

3. **A perfect fit can be fragile at named rows, not robust.** 97/97 held only
   because three live rows sat *exactly* on a boundary: **Barbell Shrug**,
   **Hack Squat**, **Smith Split Squat** — all Diff 5, one point from flipping
   S1→S2. Difficulty is a 5-term subjective composite `(Skill×2)+Flex+Grip+Load−3`;
   a single-point rescore on any term flips the tier and breaks the fit. Lesson:
   distinguish **fit** (reproduces stored labels) from **robustness** (survives a
   1-point wobble in a subjective input). Report the knife-edge rows by name —
   "your 97/97 is three rescores from 96/97" is far sharper than a clean pass.

The through-line for all three: the formula is *mechanically clean, conceptually
leaky*. It passes because the data was scored to fit it, and every break lives at
a **boundary** decided by a one-point human judgment. That's the missing few
percent — structural, concentrated at the seams, never scattered.

### Navigating a locked Google Sheet you can only read via canvas snapshots

Practical tool note from this pass: the Sheets canvas often won't page on a
scroll command. Reliable pattern — click the **Name box**, type a deep cell ref
(`A25`, `A40`), press Enter to jump the viewport, then `browser_vision` to
transcribe the visible band. Sweep the tiers by targeting where labels change
(top = S3, middle = S2/S3 seam, lower = S1) rather than reading all 97 rows.

## Red team / blue team adversarial validation

When the user asks for "extreme quality testing" or a red/blue split, deploy two
subagents with the SAME full dataset and spec, opposite mandates:

- **BLUE — validate + harden.** Reproduce the framework in code. *Pin down every
  numeric definition the spec leaves loose* (exact "high" threshold per axis,
  exact modifier weight, exact scaling). Find the definition set that maximises
  agreement, report that match rate honestly, and rewrite the loose prose into
  tight one-line definitions ready to paste back into the spec.
- **RED — break it.** Assume it's flawed; hunt for proof. Attack fronts:
  1. **Under-spec / ambiguity** — find rows whose tier *flips* on a
     reasonable-but-unstated threshold choice. Each is a spec hole.
  2. **Derivation fragility** — if a primitive is hand-scored but meant to be
     computed, find rows where a defensible re-derivation changes the tier.
  3. **Core-claim attack** — take each stated invariant ("isolation caps at
     S2", "S3 is compound-only") and hunt the strongest counterexample, in-set
     or plausible-real.
  4. **Binary-gate edges** — where a gate switches a modifier between "full" and
     "near-zero" with nothing between, find cases the binary clearly mis-handles.
- Ask RED for a **ranked** top-N of most-damaging findings (flaw class, why it
  breaks, severity blocker/major/minor). Explicitly instruct: no padding with
  confirmations.

## Don't trust the subagent summary — verify the number yourself

Subagent summaries can cut off before the verdict lands (happened this session).
When the teams return, **recompute the headline metric yourself** with the raw
data in hand (execute_code, a few lines). Never report a match rate or
correlation you didn't see computed. If both teams "set up" but neither printed
the final number, that's not a result — run it.

## The seam is where frameworks fail

Mismatches cluster, they don't scatter. In Nimbus all 4 unresolvable rows sat on
the **S2/S3 boundary** — within 1 point of flipping. That's not noise; it's the
spec's soft spot. When "high" is never numerically defined, boundary rows are
decided by an unchosen threshold, not the model. The fix is a deliberate
boundary rule, not more tuning.

## Verdict discipline (what the user actually wants)

When the user says "no bias, truth only" after an audit:
- Separate **what held** from **what failed** as two clean bullet lists.
- Distinguish the *philosophy* (may be sound) from the *boundary math* (may not
  be). A framework can have correct principles and broken thresholds.
- State "not production-ready" plainly if the seam is unresolved. Do not soften
  a real structural weakness into a positive.
- Flag the fitted-vs-validated caveat every time, even when the number is good.

## Reusable subagent probe shape

Both teams need the full dataset **inlined in their context** (they cannot see
your files). Format each row compactly: `StoredLabel|Name|feature=v|feature=v...`
Tell them explicitly to paste the inline data into a heredoc and NOT to search
for an external file — otherwise they waste turns hunting a file that isn't there.
