# AI Foundations Week — Full Curriculum Reference
*Jun 1–5, 2026 | 8–10 AM Dhaka | Learn AI group: 120363425196031209@g.us*

## Design Decisions
- **Why not OSI/CS first?** OSI without context = 7 abstract layers to parrot. Tahmeed explicitly said he hates memorisation over real understanding. AI-first lets him understand something he already uses daily (autocomplete, ChatGPT) before introducing networking layers as needed later.
- **Waterfall sequencing rationale:** Day 2 (neural nets) only lands if he already grasps "AI = pattern matching, not magic" from Day 1. Day 3 prompt engineering only makes sense once he knows the model is predicting plausible tokens, not "thinking". Day 4 comparisons need Day 3 vocabulary. Day 5 limitations need the full prior model.
- **Teaching mode:** LIVE in group during 8–10 AM window. I respond to his messages, explain, redirect, encourage. Crons handle structure; live presence handles the actual teaching.

---

## Day 1 — What Is AI? (Sun 1 Jun)

| # | Section | Duration | Content |
|---|---------|----------|---------|
| 1.1 | 📺 Watch: How AI Works (Kurzgesagt) | 15 min | youtu.be/wvWpdrfoEv0 — big picture, history, pattern recognition |
| 1.2 | Intelligence vs Artificial Intelligence | 20 min | What makes humans intelligent. AI = finding patterns in data, NOT thinking. Kill the sci-fi version early. |
| 1.3 | The Evolution of AI | 20 min | Calculators → rule-based → ML → deep learning → LLMs. Each era built on the last, not replaced. |
| 1.4 | Pattern Recognition — The Core Idea | 25 min | Spam filter walkthrough. Training data = showing thousands of examples. Inference = applying learned patterns. |
| 1.5 | ✅ Gate Test | 20 min | Task: "Explain in your own words what happens when your phone autocompletes a sentence." + 5 MCQs |

**Gate test MCQs (Day 1):**
1. AI is different from a calculator because it ___. (A: learns from examples, not follows fixed rules)
2. What is "training data"? (A: examples the model learns patterns from)
3. What does "inference" mean in AI? (A: using learned patterns on new input)
4. True/False: AI thinks the way humans think. (A: False)
5. Which came first: machine learning or deep learning? (A: machine learning)

**Waterfall gate:** Day 2 locked until 1.5 complete.

---

## Day 2 — How It Actually Works (Mon 2 Jun)

| # | Section | Duration | Content |
|---|---------|----------|---------|
| 2.1 | 📺 Watch: But what is a neural network? (3Blue1Brown) | 25 min | youtu.be/aircAruvnKk — 19M views, best visual intro on the internet |
| 2.2 | Data → Training → Model → Output | 20 min | Full loop. Types of training data. How weights shift during training to reduce error. |
| 2.3 | Neural Networks Simply | 20 min | Input → hidden layers → output. Team passing and filtering notes analogy. Each node votes on the answer. |
| 2.4 | Parameters, Weights & Scale | 20 min | Parameter = one number the model learned. GPT-4 ~1.8T of them. Why scale + data + compute = capability. More params ≠ always better. |
| 2.5 | ✅ Gate Test | 15 min | Task: hand-draw a simple neural network, label input/weights/output. + 5 MCQs |

**Gate test MCQs (Day 2):**
1. What is a "parameter" in an AI model? (A: a number the model learned during training)
2. What happens during training? (A: the model adjusts its weights to get better predictions)
3. Input → ??? → Output. What goes in the middle? (A: hidden layers)
4. Does a bigger model always perform better? (A: No — data quality and training matter too)
5. What is the relationship between compute, data, and capability? (A: more of both generally → more capable model, up to a point)

**Waterfall gate:** Day 3 locked until 2.5 complete.

---

## Day 3 — How We Use It (Tue 3 Jun)

| # | Section | Duration | Content |
|---|---------|----------|---------|
| 3.1 | 📺 Watch: Perfect ChatGPT Prompt Formula (Jeff Su) | 15 min | youtu.be/jC4v5AS4RIM — 3M+ views, practical and immediately applicable |
| 3.2 | 📺 Watch: AI Tools You Should Know (Fireship) | 10 min | youtu.be/Ca5mZ4KR4Ek — fast, punchy, Gen-Z friendly format |
| 3.3 | Types of AI Tasks | 20 min | Generative (create), Classification (label), Prediction (forecast), Retrieval (find). Real everyday examples of each. |
| 3.4 | The Tools Landscape | 15 min | Consumer apps vs APIs vs local models. Claude, ChatGPT, Gemini, Ollama, Midjourney — when to use which. |
| 3.5 | Prompt Engineering Basics | 25 min | What a prompt is. Why phrasing changes output. Techniques: be specific, give context, give examples, specify format. System prompts vs user prompts. Live demo: same Q, 3 phrasings. |
| 3.6 | ✅ Gate Test | 15 min | Task: write 3 prompts for same task (weak/medium/strong), run on Claude or ChatGPT, note differences. + 5 MCQs |

**Gate test MCQs (Day 3):**
1. What type of AI task is "classify this email as spam or not"? (A: Classification)
2. What's the difference between a consumer app and an API? (A: consumer app is for end-users; API is programmatic access for developers)
3. Why does the phrasing of a prompt matter? (A: the model predicts the most likely continuation — different phrasing shifts what "likely" means)
4. What is a "system prompt"? (A: background instructions that set the model's behaviour before the user message)
5. Name two differences between Claude and ChatGPT. (A: any two valid — safety focus, context window, company philosophy, pricing, etc.)

**Waterfall gate:** Day 4 locked until 3.6 complete.

---

## Day 4 — The Company & Model Landscape (Wed 4 Jun)

| # | Section | Duration | Content |
|---|---------|----------|---------|
| 4.1 | 📺 Watch: GPT-4o vs Claude vs Gemini (AI Explained) | 20 min | youtu.be/wBbIFwLBjcE — direct comparisons, honest benchmarks |
| 4.2 | 📺 Watch: Open Source AI Explained (Fireship) | 10 min | youtu.be/KnFNgWA_MoE — Llama, Meta, open-source movement |
| 4.3 | The Major Players | 25 min | OpenAI (GPT-4o) — first mover, MS-backed, closed. Anthropic (Claude) — safety-first, ex-OpenAI. Google (Gemini) — search + multimodal. Meta (Llama) — open source, run locally, free. Mistral — European, efficient, open weight. |
| 4.4 | What Actually Differentiates Them | 20 min | Context window, multimodal capability, speed, cost, safety approach. Build the comparison table live with Tahmeed. |
| 4.5 | Open Source vs Closed Source | 15 min | Closed: API access, company controls. Open weight: run locally, modify, free. Trade-offs: privacy, cost, censorship, customisation. Who controls AI — why it matters. |
| 4.6 | Benchmarks — What They Mean & Why They Lie | 10 min | MMLU, HumanEval, GPQA — what each tests. Companies cherry-pick best results. Gap between benchmark and real-world usefulness. |
| 4.7 | ✅ Gate Test | 20 min | Task: ask same 3 questions to ChatGPT + Claude + Gemini, note style/accuracy/personality differences. + 5 MCQs |

**Gate test MCQs (Day 4):**
1. What does "open source" mean for an AI model? (A: the weights are publicly available, can run locally, modify, free)
2. Name one advantage of a closed model over open source. (A: any valid — better safety guardrails, more compute behind it, enterprise support, etc.)
3. What is a "context window"? (A: how much text the model can read/remember in one session)
4. Why can't you trust benchmark comparisons between companies? (A: companies cherry-pick the benchmarks they win; doesn't reflect real-world use)
5. Which company made Llama? (A: Meta)

**Waterfall gate:** Day 5 locked until 4.7 complete.

---

## Day 5 — The Honest Picture (Thu 5 Jun)

| # | Section | Duration | Content |
|---|---------|----------|---------|
| 5.1 | 📺 Watch: AI Hallucinations Explained (IBM Technology) | 15 min | youtu.be/cfqtFvWOfg0 — clinical, accurate, no fluff |
| 5.2 | 📺 Watch: Why AI is Harder Than We Think (Veritasium) | 15 min | youtu.be/FW9YSEUAjoo — reasoning failures, real limits |
| 5.3 | Hallucinations | 20 min | Confident wrong answers. Why: model predicts plausible, not verified. Famous examples. How to spot and mitigate. Connects back to Day 2: it's predicting tokens, not looking up facts. |
| 5.4 | Bias in AI | 20 min | Biased training data → biased output. Types: representation, historical, measurement. Real examples (facial recognition, hiring tools). Why hard to fix — you can't audit 1.8T parameters. |
| 5.5 | What AI Genuinely Cannot Do | 15 min | True causal reasoning. Long-term planning with real-world feedback. Genuine creativity (remixes, doesn't invent). Real-time knowledge. Physical world understanding. |
| 5.6 | Privacy, Copyright & The Messy Bits | 10 min | What happens to prompts. Training data lawsuits (NYT vs OpenAI). AI content ownership. Job displacement — real but nuanced. |
| 5.7 | Where This Is Heading | 10 min | Agents (AI that acts, not just answers). Multimodal. AGI — what it'd actually mean. Why next 2 years matter more than last 10. |
| 5.8 | ✅ Week 1 Cumulative Test | 15 min | 10 questions across all 5 days. 1 open: "One thing AI surprised you it CAN do + one thing it surprised you it CAN'T." |

**Cumulative test Q bank (Day 5, draw 10 from these):**
- What's a hallucination in AI? Why does it happen?
- Can you always trust a confident AI answer? Why not?
- What is training data bias and where does it come from?
- Name one thing AI genuinely cannot do.
- What is an "AI agent"?
- What's the difference between AI creativity and human creativity?
- Why does your chat history disappear when you start a new conversation?
- What does "multimodal" mean?
- What is AGI and do we have it yet?
- Which is safer for private data: a closed API or a local model?

---

## Sheet Logging Format (10 AM cron)

For each completed section, update the row in "AI Foundations Week" tab:
- **Status**: ⏳ Pending → ✅ Done (or ❌ Skipped if not reached)
- **Key Concepts Covered**: What Tahmeed actually engaged with, in his own words if possible
- **Gate Test Score (/5)**: The score from the gate test (gate tests only — leave blank for content sections)
- **Quiz Questions (logged)**: The 3 questions asked verbatim
- **Blockers / Notes**: Confusion points, things to revisit, energy level, engagement quality

Weekly score row at bottom: sum of all gate test scores (max 30 across 5 days).
