# Seattle Fitness Magazine — House Handbook

The rulebook the board judges against. Every reviewer brief carries the sections
relevant to its seat.

Absorbed from the retired `editor-in-chief` skill's standards §1, §2, §6–§9 — the
magazine-relevant parts. The layout-locked Canva sections (char-fit, template structure)
did not come across; they never applied to a web surface.

---

## §Kill — should this run at all?

**Commission before craft.** The first question is not how well a piece is written but
whether it should exist.

A piece earns its place by having **one** of:
- something first-hand,
- something nobody else has gathered,
- a position nobody else is taking.

Absent all three, kill it. A well-written piece with nothing to say is still nothing to say.

**The attention bar.** Free is not a lower bar, it is a different one. The paid question is
*worth $24.99?* The free question is **worth a stranger's next four minutes?** A piece that
only aggregates what is already on the first page of search does not clear it.

Then the four practical filters:

1. **Specific.** "Best gyms in Seattle" is not a story. "The four Ballard gyms that open
   before 5am" is.
2. **Local.** A Seattle reader learns something a national site could not tell them.
3. **Useful.** The reader can act on it this week.
4. **Not already run.** Check the existing blog before commissioning a near-duplicate.

Kill anything that is a national trend piece with a Seattle word pasted on, a listicle with
no verdict, or a topic already covered in the last quarter.

---

## §Voice

**Spine:** editorial-athletic. Cultural-cool sensibility. Confident, never confrontational.
Staccato, declarative, opinionated. The register reports; it does not assert or cheerlead.

**Fails:**
- Hype verbs and superlatives doing the work a fact should do.
- Bro-science cadence, gym-influencer punchiness.
- Hedging so soft the sentence says nothing.
- Second-person scolding.
- Press-release register — a venue's own marketing language repeated as fact.
- Flattery of a featured spot, and no negative criticism of one either. Feature and list.
  A verdict is a verdict, not a review score.

**The Forbes test:** could this sentence run unchanged in a generic Forbes wellness
listicle? If yes, rewrite it.

---

## §Mechanics

**No em-dashes in body copy. Any em-dash anywhere is a hard fail on this surface.**
Comma by default. Period when it is really two clauses. Colon when a list follows.

**Push/pull/legs is blacklisted.** TIMBR is blockless. Group by anatomical region.

**No option-listing in copy.** Copy takes a position.

---

## §Machine-detectable AI prose

Copy that reads as machine-written fails whichever voice it is imitating. These are writing
rules — write toward them.

**Blocked vocabulary.** The authoritative list is `BANNED_VOCAB` and `BANNED_PHRASES` in
`~/Desktop/Skill-Cabinet/timbr_eval_v2/hardgate.py`. Read it there. Core set:

> delve, foster, tapestry, vibrant, robust, holistic, leverage, seamless, pivotal,
> transformative, unlock, elevate, revolutionize, journey *(in a fitness or wellness sense —
> "the journey home" is fine)*, empower, thrive, curated, game-changer, deep dive, synergy,
> ecosystem, impactful, actionable, harness, spearhead

One hit is a defect: replace it, do not negotiate it. The ban is on the word in shipped
copy — "harness" naming the eval harness in a brief is not copy.

**Stacked hedging is banned.** One hedge per sentence. "may possibly", "could perhaps
suggest" — two hedges says nothing and reads machine-written. State the claim, or state the
uncertainty once, plainly.

**Transition-stacking is banned.** Moreover, Furthermore, Additionally, In addition,
Notably, Importantly, It is worth noting. Never as consecutive paragraph openers, never more
than once in a piece. A sentence that only transitions is filler.

**Repeated sentence-openers, banned at three.** Three consecutive sentences opening on the
same word or construction is a defect. Vary the entry.

**Sentence rhythm must vary.** Uniformly medium-length sentences are the clearest machine
tell there is. In any run of four or more sentences: at least two under 8 words, at least
two over 20. Short line, long line, short line.

**No identical entry templates.** Ten venues run through the same clause in the same slot
reads as a rendered database table. Vary them.

**No fictional cold-opens.** A named person plus a present-tense physical action plus a
staged moment ("Maya laces her shoes before dawn") is fiction unless it happened and you
were there. Report the person, do not stage them. A reported habit is not a cold-open:
"Jade Kim orders the same thing every Tuesday" is reporting and ships.

**Second person: none.** No `you should / your body / try this / you need to / you can /
you will feel / your workout / you want to`. None of us has met the reader's body.

### What is NOT banned

The house devices stay. What is banned is density and formula, not the device:

- **The triad and the parallel construction.** Voice when it lands once for emphasis. Defect
  when it is the default shape of every paragraph.
- **The short declarative kicker. The one-sentence paragraph for weight.** Register signals,
  not tells.

The test: if a device is doing the same job in the same position twice on one page, cut one.
One triad in a page is voice. A triad in every paragraph is a template.

---

## §Facts

Nothing ships unverified.

**Venue pre-flight.** Before publish, confirm live: open/closed status, address, the
underlying link URL, the maps link, and the photo. A dead link or a closed gym costs more
credibility than the piece earns.

- Every price and hour checked against the venue's own current site.
- Every person's name spelled right; every age confirmed.
- Every macro estimate spot-checked against 40P/30C/20F, not assumed.
- Training claims defensible, not just plausible. Flag mechanisms stated as certainty where
  the literature is mixed, numbers with no basis, and a thesis that overstates the evidence.
- **Supporting statistics count.** Do not invent a number to prop up the thesis.
- **Check superlatives against the piece's own numbers.** "The cheapest plate here" must
  actually be the cheapest plate listed.

A fact that cannot be verified gets cut. It never ships hedged. Flag it, quote it, propose
the accurate version — do not silently soften a claim the owner chose.

**Named people and businesses.** Describe what is verifiable. No unsourced characterization
of a private person or a small business. **If a piece is critical of a named operator, that
is an owner decision, not a board decision — escalate, do not ship it quietly.**

You never choose which real people are featured. That is the owner's call.

---

## §Structure

- **Cold open.** Say what this is and why it matters inside the first two paragraphs. No
  throat-clearing, no definitions, no "in today's world."
- **One piece, one argument.**
- **Headline states the actual subject**, not a tease. No listicle framing, no curiosity
  gap, no question headline standing in for an argument.
- **The first sentence carries the piece.** It earns the second sentence or the reader is gone.
- **Pull quotes stand alone** — readable with no surrounding context.
- **End on a line worth remembering**, not a summary of what was just read.
- **The So What test:** the reader finishes with something specific they can use or do.

Real `##` H2 headings, never bold text pretending to be a heading. One continuous paragraph
under each H2.

---

## §Length

Bands are per content type, enforced by `WORD_COUNT_RANGES` in v2's `hardgate.py`:

| Content type | Words |
|---|---|
| `blog_the_guide` / `blog_training` / `blog_culture` | 800–1200 (aim 900–1100) |
| `magazine_*_spot` | 150–400 |
| `product_venue_card` | 40–200 |

The gate measures body prose with headings stripped. TIMBR's own early articles ran ~480
words, half their own blog floor. Do not use published posts as a length reference.

---

## §Seattle specificity

- **Scene posture.** Write from inside the scene, not above it. Report what is there, name
  real places and real people, and never describe a room you have not been in.
- Every neighbourhood reference current and accurate for 2026.
- Written for someone who lives here. No tourist framing, no "the Emerald City."
- Cultural references must land for a 28-year-old in Capitol Hill.
- A national trend needs a genuine local angle attached or it does not run.

---

## §Audience register

Reads 50/50 male and female. Dual-register language throughout — lifted alongside full,
strong alongside square. No women-only silos, no bro-only framing.

---

## §Typography (mobile, blog posts)

Body: **15px / 1.5 line-height.** Owner-set 2026-07-29, down from 18px.

Measured the same day at 375px width, for reference: Apple 17px/25px, Nike 16px/24px,
Airbnb 16px/24px. The house sits one step below all three, deliberately.

A Wix Editor theme setting, not article content. Cannot be changed through the Blog API, and
it applies to every post at once.
