# Seattle Fitness Magazine — House Handbook

The rulebook the board judges against. Every reviewer brief carries the sections
relevant to its seat.

---

## §Kill — should this run at all?

A piece runs only if it clears all four:

1. **Specific.** "Best gyms in Seattle" is not a story. "The four Ballard gyms that
   open before 5am" is.
2. **Local.** A Seattle reader learns something a national site could not tell them.
3. **Useful.** The reader can act on it this week.
4. **Not already run.** Check the existing blog before commissioning a near-duplicate.

Kill anything that is a national trend piece with a Seattle word pasted on, a
listicle with no verdict, or a topic already covered in the last quarter.

---

## §Voice

Staccato. Declarative. Opinionated. The register reports; it does not assert or
cheerlead.

**Never:**
- Second person coaching. No "you should," "you need to," "you'll want to."
- Cheerleading. No "crush it," "no excuses," "get after it."
- Press-release register. No venue's own marketing language repeated as fact.
- Chatbot register. No "it's not just X, it's Y." No "in today's world."
- Flattery of a featured spot, and no negative criticism of one either. Feature and
  list. The verdict is a verdict, not a review score.

**The Forbes test:** could this sentence run unchanged in a generic Forbes wellness
listicle? If yes, rewrite it.

---

## §Banned words

Any single hit is a hard fail. The authoritative list is `BANNED_VOCAB` and
`BANNED_PHRASES` in `~/Desktop/Skill-Cabinet/timbr_eval_v2/hardgate.py` — read it there
rather than trusting this excerpt, which is a sample:

delve, dive deep, tapestry, nuanced, multifaceted, pivotal, seasoned, foster, realm,
landscape, bustling, vibrant, beacon, testament, elevate, curate, leverage, unlock,
journey, cutting-edge, game-changer, paradigm, holistic, robust, seamless, notion,
crucial, vital, no excuses, clean eating, crush it, optimize, wellness journey

---

## §Punctuation

- **No em-dashes in body copy.** Hard fail. Comma by default, period for two clauses,
  colon for a list. (Em-dashes are allowed in titles, subtitles and dividers — this
  handbook governs body prose only.)
- No stacked colons mid-sentence.
- No bullet list where prose belongs.

---

## §Length

Bands are per content type, enforced by `WORD_COUNT_RANGES` in v2's `hardgate.py`:

| Content type | Words |
|---|---|
| `blog_the_guide` / `blog_training` / `blog_culture` | 800–1200 (aim 900–1100) |
| `magazine_*_spot` | 150–400 |
| `product_venue_card` | 40–200 |

TIMBR's own early articles ran ~480 words, half their own blog floor. Do not use
published posts as a length reference.

---

## §Seattle specificity

- Every neighbourhood reference current and accurate for 2026.
- Written for someone who lives here. No tourist framing, no "the Emerald City."
- Cultural references must land for a 28-year-old in Capitol Hill.
- A national trend needs a genuine local angle attached or it does not run.

---

## §Facts

Nothing ships unverified.

- Every address confirmed at the stated location and confirmed open.
- Every price and hour checked against the venue's own current site.
- Every person's name spelled right; every age confirmed.
- Every macro estimate spot-checked against the 40P/30C/20F framework, not assumed.
- Training claims must be defensible, not just plausible.

A fact that cannot be verified gets cut. It never ships hedged.

---

## §Training content

- **No push/pull/legs.** TIMBR is blockless. Group by anatomical region.
- Rep ranges by fiber type: Type I 15–20, Type IIA 8–12, Type IIX 3–6.
- Rest 45–60 seconds static.
- If a set total is stated in a table, the prose must match it exactly.

---

## §Structure

- **Cold open.** No throat-clearing, no scene-setting paragraph before the point.
- **Headline matches body.** No bait and switch.
- **Pull quotes stand alone** — readable with no surrounding context.
- **The last line lands.** Weak endings kill strong pieces. A trailing summary is a
  weak ending.
- **The So What test:** the reader finishes with something specific they can use or do.

---

## §Audience register

Reads 50/50 male and female. Dual-register language throughout — lifted alongside
full, strong alongside square. No women-only silos, no bro-only framing.
