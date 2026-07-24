---
name: source-text-distillation
description: Distill large source documents (books, reports, long PDFs) down to signal by extracting text, mining high-value seams, and synthesising across one or many sources — instead of summarising from memory.
triggers:
  - User hands over a book/report PDF and asks for "the most important things", "filter me X", or a summary
  - Multiple documents on the same subject need one deduplicated synthesis
  - Any "pull the key ideas / method / playbook" ask against a long text
  - Comparing or contrasting what several sources say about one topic/person
---

# Source-Text Distillation

Turn long source documents into tight, accurate signal. The rule: **read the actual text, do not summarise from memory.** A book you "know" is a book you will misquote. Extract, mine, verify, then synthesise.

---

## Core Workflow

1. **Identify before assuming.** Run `pdfinfo` (Title/Author/Pages) and read the first 1–2 pages. Never ask "what is this?" if the metadata answers it. Confirm what each file actually is — filenames lie (e.g. five files all named "Larry*" were five different books).

2. **Extract to text.** `pdftotext input.pdf out.txt`. Get a word/line count so you know the scale you're working with.

3. **Mine the seams, don't read cover to cover.** Use `grep`/regex for high-signal markers, then pull windowed context (±300–400 chars) around hits. Good marker families:
   - Method/structure: `algorithm`, `principle`, `the key to`, `the lesson`, `my philosophy`, `I believe`, `secret`
   - Author's framing of the subject: `complexity`, `simplicity`, `reality|distort`, named heroes/influences
   - Stance/edge: `compete|crush|destroy`, `risk`, `win|winning`, `I learned`
   - Find chapter titles — they are the author's own signal map (a chapter literally named "The War on Complexity" tells you the thesis).

4. **Quote-anchor every claim.** Pull the subject's *own words* from the text where possible. This is what separates this from a Wikipedia-grade summary the user could get anywhere.

5. **Synthesise, deduplicate, contrast.** For multi-source asks, produce ONE synthesis, not N summaries — sources on one subject overlap heavily. End with the sharp contrast (e.g. "Musk's edge is first principles; Ellison's is simplicity-as-warfare"). The contrast is often the most valuable line.

---

## Lens Discipline (ask once, up front)

Before grinding a long text, pin the lens with ONE quick question so you filter to *them*, not to everyone:
- **Method vs. man** — "how they think/build" vs. "the life/story." Cut accordingly.
- **One synthesis vs. book-by-book** for multi-source. Recommend synthesis for same-subject shelves; flag the heavy overlap as the reason.

Don't ask a pile of clarifying questions — one or two, then go.

## Don't pirate. Route to legitimate.

If the user wants a copyrighted book they don't have, refuse the piracy route plainly and offer legit fast paths (Libby/library, Kindle/Play, audiobook) — OR offer an instant free *distillation of the method* written from your own knowledge as the fallback. Once they supply their own purchased file, work directly from it (better than memory anyway).

---

## Output Shape (this user — Tanzim)

- **Lead with the distilled structure**, numbered, each point one tight para with a quoted anchor where it earns it.
- Bold the spine (the named method / thesis), then corollaries as a short bullet list.
- Close with the single sharpest contrast or takeaway — then **stop**. Offer at most ONE natural next half ("want the 'how he thinks' half next?"), never a menu.
- Keep it compressed. He explicitly does not want everything dumped at once — deliver the asked-for half cleanly and let him pull the next.

---

## The Personal Mirror (this user — beyond the distillation)

For Tanzim, the book distillation is rarely the endpoint — it's a setup for a personal read. He distils founders/operators (Musk, Ellison, Jobs, Hoffman) because they reflect *him*, and he'll often close with "**why do I admire them?**" or pivot to his own situation. When that turn comes:

- Answer it as a mirror, not a book report. Name the trait he shares with the subjects (refusal of inherited constraints, simplicity/subtraction over addition, calculated risk, solo end-to-end ambition) — then name the price those subjects paid (people, health, the wreckage trail) as the one thing to watch.
- **Apply the framework back to his actual operation** — don't leave it abstract. Hoffman's "I to the We," Jobs's A-players, Blitzscaling's "don't do it solo" — map each to where he actually is.
- **Model his situation from current facts, not assumptions, and retract cleanly when corrected.** This session I repeatedly nudged the "you underplay the network/We gear" line; he then revealed a real team (Sagar CTO/co-founder, Waseem ex-Meta staff eng, Towsif ops). The right move was an immediate, clean withdrawal ("Withdrawn") + crediting what he'd built — not defending the earlier read. When new facts land, drop the prior thesis and re-aim at the *next* real risk (here: he's the sole owner of the revenue engine while product has four hands on it).
- The most valuable closing line is usually the **founder-trap / single-point-of-failure** observation aimed at his specific setup, ending on a sharp question he has to answer.

## Relevance-Ranking & Applicability (playbook/advisory texts)

Biographies get distilled as *philosophy to admire*. Playbook/advisory authors (Hoffman, Hormozi, Naval, Levels) must be distilled as *operating manual to apply* — and the most valuable move is ranking the shelf by **applicability to where the user actually is**, not treating every book as equal.

- **Separate "apply" from "admire."** Of a multi-book author, name which 1–2 books map to his current stage and which are reference-only or anti-patterns. E.g. Hoffman: *Startup of You* + *Masters of Scale* are his (early-stage solo founder + job hunt); *Blitzscaling* is the one to read **to know when NOT to** (it's for capitalised winner-take-all land grabs — "blitzscaling solo is burnout with a fancy name"); *The Alliance* matters only once he's formalising tours of duty with his team.
- **Rank the canon when asked "who is most relevant to me."** Don't list — sequence by fit. Hormozi (revenue/offers/leads — his exact day) > Hoffman (career/network) > Musk/Ellison/Jobs (empire philosophy, admire-don't-copy). Lead with the single most relevant and say why.
- **Volunteer the missing author.** When the shelf has a gap for his actual bottleneck, name it. This session: his revenue engine is fitness products sold cold on Instagram → Hormozi is the precise fit; also flag Naval (leverage: code+media are permissionless) and Levels (solo-founder ship-fast mirror).
- **Turn the distillation into a sequenced to-do.** For applicable playbooks, end by mapping the framework onto his operation as an ordered checklist (Hormozi: Avatar → Grand Slam Offer → Core Four leads → Money Model), then offer to build it out. The synthesis is the setup; the personal action plan is the payoff.

## Tooling Notes

- `execute_code` (Python) is the workhorse for multi-file mining: loop files, run regex with windowed context, count hits per marker to decide where the gold is before reading.
- `re.sub(r'\s+',' ',text)` to collapse PDF line-wrap noise before context windows, or quotes come out shredded.
- OCR/scan artifacts are common in older book PDFs (`adliering`, `cantankerous` typos) — read through them; the meaning survives.

---

## Pitfalls

- ❌ Summarising the book from memory. You will get details wrong and the user bought the file precisely so you wouldn't. Read the text.
- ❌ Asking "what is this?" when `pdfinfo` already says. Identify first, ask second.
- ❌ N separate summaries for N books on one subject. Synthesise and dedupe.
- ❌ Dumping the whole analysis at once. Deliver the requested lens, offer one next half, stop.
- ❌ Reading 800 pages linearly. Mine seams; chapter titles + markers get you to signal in minutes.
