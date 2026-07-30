# TIMBR House Standards

The rulebook the board judges against. Locked rules are owner decisions — never re-litigate them, never "suggest" the alternative.

---

## 1. Voice

**Spine:** editorial-athletic. Cultural-cool sensibility. Confident, never confrontational.

**Body tonality (Workout Series, LOCKED):** the seasoned coach.
- Honesty over hype. No "shredded in 30 days" energy.
- Reader autonomy — the reader decides, the copy informs.
- Earned, not given.
- Show up tomorrow. The long game, not the hack.

**Fails:**
- Hype verbs and superlatives doing the work a fact should do.
- Bro-science cadence, gym-influencer punchiness.
- Hedging so soft the sentence says nothing.
- Second-person scolding.

---

## 2. Mechanics (LOCKED)

**Em-dashes are GONE from body paragraphs.** Across all ten ebooks.
- Comma by default.
- Period when it is really two clauses.
- Colon when a list follows.

**KEEP em-dashes in:** titles, subtitles, dividers, footers, workout specs, FAQ questions, cover.

**Per product line.** The lock above is the Essential Series / EST rule. The other two lines are gated differently, and this does not loosen it:
- Magazine issue copy (`--ruleset magazine`): **any** em-dash anywhere is a hard fail.
- Workout Series volumes (`--ruleset workout_series`): one em-dash **aside** per sentence, never stacked. A matched pair bracketing a phrase is one aside, not two dashes. Three or more dashes in one sentence is stacked, and fails.

**Push/pull/legs is blacklisted.** TIMBR is blockless. Never classify or program by push/pull/legs. Group by anatomical region.

**No option-listing in copy.** Copy takes a position.

---

## 3. Fit & char-lock

*Layout-locked surfaces only (Canva, templates). Skip entirely on web and editorial surfaces.*

Treat every box size as fixed. Fit the copy to the box, never the box to the copy.

- Replacement copy must stay **≤ the block's existing char count**. Measure before, report before→after.
- **Last-Line Underfill** is a named defect: a body's last line must fill **≥ ~75%** to the margin. A one-word last line is the worst case. Fix deterministically: append until the row is about to wrap.
- **Narrow side-columns must be ONE continuous paragraph.** A `\n\n` in a narrow column overflows off-page (gate: ~271.91px / 22 rows).
- Same char count ≠ same render height. Always read back `dimension.height` after a fill.
- Calibration: narrow column 22 rows ≈ 1050 chars. Full-width ≈ 100 chars/row.
- Long titles may need a manual `\n` to hold two lines. Hero titles that run to 3 lines break the house look.
- Template stored heights are filler-clamped. The real gate is **page fit**, not stored height.
- Pages with a top body over a sidebar can break by **collision**, not only by footer overrun.

---

## 4. Structure & consistency

*Product lines with a locked spine. On editorial surfaces use §8 instead.*

- Per-session hard-set wording must match the P7 total. 12-set → "ten to twelve". 13-set → "ten to fourteen".
- TOC entries must correspond to pages that actually exist.
- Divider taglines stay **≤52 chars / 2 lines**.
- Every p16 title and footer, and every p17 eyebrow, must be filled — leftovers from the source ebook are a recurring defect.
- Section order and page map must match the locked spine for the product line.

---

## 5. Audience — 50/50

Essential Series must read 50/50 male/female.
- **Dual-register language:** "lifted" and "firm" alongside "full" and "square".
- At least one dual-goal line per piece.
- **No women-only silos.** No separate "for women" section, no softened parallel track.

**Fails:** default-male framing, size-only outcomes, aesthetic language that only lands for one reader.

---

## 6. The premium bar

Essential Series ebooks are **$24.99 paid** products. The bar is *modern encyclopedia*, not blog post.

Judge every page against: **"Worth $24.99?"**

- **Zero filler.** A paragraph that restates the heading is filler. A sentence that only transitions is filler.
- Encyclopedia depth: the reader should learn something they could not get from a free article.
- Premium craft: every line earns its place on the page.

---

## 7. Claims

Training and nutrition claims must be accurate and defensible. Flag:
- Mechanisms stated as certainty where the literature is mixed.
- Numbers with no basis (rep ranges, frequencies, percentages).
- A hero thesis that overstates what the evidence supports.

Flag it, quote it, propose the accurate version. Do not silently soften a claim the owner chose.

---

## 8. Editorial surfaces

Applies to blog posts, scene pieces, city guides, venue write-ups — anything not layout-locked. §3 and §4 do not apply. §1, §2, §5, §7, §9 and §10 still do.

**The attention bar.** Free is not a lower bar, it is a different one. The paid question is *worth $24.99?* The free question is **worth a stranger's next four minutes?** A piece that only aggregates what is already on the first page of search does not clear it.

**Commission before craft.** The first question is not how well a piece is written but whether it should exist. A piece earns its place by having one of: something first-hand, something nobody else has gathered, or a position nobody else is taking. Absent all three, kill it — a well-written piece with nothing to say is still nothing to say.

**Verification.** No venue, business, person, date, price or link ships unverified. Before publish, confirm live: open/closed status, address, the underlying link URL, the maps link, and the photo. A dead link or a closed gym costs more credibility than the piece earns.

**Named people and businesses.** Describe what is verifiable. No unsourced characterization of a private person or a small business. If a piece is critical of a named operator, that is an owner decision, not a board decision — escalate, do not ship it quietly.

**Headline and open.** The headline states the actual subject, not a tease. No listicle framing, no curiosity gap, no question headline standing in for an argument. The first sentence carries the piece: it earns the second sentence or the reader is gone. Never open on throat-clearing, definitions, or "in today's world."

**Article structure.** Say what this is and why it matters inside the first two paragraphs. One piece, one argument. End on a line worth remembering, not a summary of what was just read.

**Scene posture.** Write from inside the scene, not above it. Report what is there, name real places and real people, and never describe a room you have not been in.

---

## 9. Machine-detectable AI prose (LOCKED)

Copy that reads as machine-written fails whichever voice it is imitating. Applies to every surface and every product line. These are writing rules — write toward them. They apply the same whether you are drafting by hand or briefing a model.

**Blocked vocabulary.** Never ships, any line:

> delve, foster, tapestry, vibrant, robust, holistic, leverage, seamless, pivotal, transformative, unlock, elevate, revolutionize, journey *(in a fitness or wellness sense — "the journey home" is fine)*, empower, thrive, curated, game-changer, deep dive, synergy, ecosystem, impactful, actionable, harness, spearhead

Three or more in one section is a hard fail. One is still a defect: replace it, do not negotiate it. The ban is on the word in shipped copy — "harness" naming the eval harness in a brief or a report is not copy.

**Workout Series bans nine more**, and one hit is enough: ultimate, amazing, game-changing, level up, unlock, transform, crush, beast mode, no excuses. Exclamation points too, outright.

**Stacked hedging is banned.** One hedge per sentence, and only where §7 says the evidence is genuinely mixed. "may possibly", "could perhaps suggest", "seems to potentially indicate" — two hedges in a sentence says nothing and reads machine-written. State the claim, or state the uncertainty once, plainly.

**Transition-stacking is banned.** Moreover, Furthermore, Additionally, In addition, Notably, Importantly, It is worth noting. Never as consecutive paragraph openers, never more than once in a piece. A paragraph earns its place by what it says, not by announcing that it follows the last one. A sentence that only transitions is filler (§6).

**Repeated sentence-openers, banned at three.** Three consecutive sentences opening on the same word or the same construction — three "The …", three "It is …", three participial phrases — is a defect. Vary the entry.

**Sentence rhythm must vary.** Uniformly medium-length sentences are the clearest machine tell there is. Target, and the shape the athletic register actually rewards: in any run of four or more sentences, at least two under 8 words and at least two over 20. Short line, long line, short line.

**No fictional cold-opens.** A named person plus a present-tense physical action plus a staged moment ("Maya laces her shoes before dawn") is fiction unless it happened and you were there (§8). Report the person, do not stage them. A reported habit is not a cold-open: "Jade Kim orders the same thing every Tuesday" is People-register reporting and ships.

**Second person.** Magazine: none of `you should / your body / try this / you need to / you can / you will feel / your workout / you want to`. Workout Series: direct address is house voice, but never **prescriptive** (`you should`, `you must`, `you have to`) and never **predictive** (`you will feel`, `you'll feel`). None of us has met the reader's body.

### What is NOT banned

The house devices stay. What is banned is density and formula, not the device:

- **The triad and the parallel construction.** A three-part list, a frame repeated across two clauses. Voice when it lands once for emphasis. Defect when it is the default shape of every paragraph, or runs three paragraphs straight.
- **The colon before a list, the period splitting two clauses, the em-dash where its line allows one** (§2). All three are the locked house punctuation. §9 does not touch them.
- **The short declarative kicker. The one-sentence paragraph for weight.** Both are register signals, not tells.

The test: if a device is doing the same job in the same position twice on one page, cut one. One triad in a page is voice. A triad in every paragraph is a template.

---

## 10. The machine gate (LOCKED)

Four linters gate TIMBR copy before it ships. Floor, not opinion: a piece that fails the machine gate does not ship, whatever the board thinks of it. Invocation is in SKILL.md, Step 2.

| Linter | Gates | Runs on |
|---|---|---|
| **ProhibLint** | blocked vocabulary (§9), the em-dash rule for the line (§2), second person, fictional cold-opens, magazine word-count ranges, magazine mandatory value elements | both rulesets |
| **VoiceLint** | does the section read as its assigned register — athletic / people / fitt — and does it read more like one of the other two (cross-contamination) | magazine only |
| **CharLint** | exact character-count locks, per slot | workout_series only |
| **SynthLint** | AI-fingerprint prose (§9): transition-stacking, stacked hedging, repeated openers, uniform sentence rhythm, extended AI vocabulary | every ruleset |

**Thresholds:**
- ProhibLint — a unit passes at score ≥70 with no hard fail. Any hard fail fails it outright, whatever the score.
- VoiceLint — pass at 85. One cross-contamination flag costs 18 and fails a section on its own, however clean the rest of it reads.
- CharLint — exact. Any miss beyond tolerance (default 0) is a hard fail, in either direction: overflow or underfill. There is no "close enough" band.
- SynthLint — a hard fail is a BLOCKER like any other.

**Warnings are not failures.** The `cover_body` DRIFT warning (PRINCIPLES.txt records 357, the live template measures 351) fires on every workout_series run and is an owner decision, not a finding. Never report a warning as a blocker; never let one hold a ship.

**Register map (magazine):** Training and Culture → athletic. Nutrition and Social → people. Supplements, Recovery, Nightlife → fitt. No register asks for second person, in any section.

**Word-count ranges (magazine):** Training 800–1200 · Nutrition 600–900 · Supplements 400–600 · Recovery 500–800 · Culture 800–1200 · Social 500–700 · Nightlife 400–600.

**Mandatory value elements (magazine, per issue):** rep/set notation somewhere; ≥4 **distinct** named nutrition venues each carrying a street address; ≥2 **distinct** named gyms, studios or run clubs; ≥3 **distinct** named venues with a place-type word or a location anchor. Distinct by name — repeating one venue six times satisfies nothing.

**Coverage is not proof.** A CharLint pass covers its seven locked slots, not a whole volume. A harness PASS means nothing on the page it was not given. Feed it the text that will ship.

Input JSON shape, scorecard keys, exit codes: `/Users/tanzimozer/Desktop/Skill-Cabinet/timbr_eval/README.md`.
