# Protocol Definitions for Friday 2.0

## Veronica Protocol (Deployment Standard)

**CORRECTION (June 8, 2026):** Veronica was initially logged as "Instagram crawler" — this is **wrong**. Veronica is the Opus deployment protocol. The Instagram crawler is IG-1 Protocol (separate).

### Correct Definition

**Purpose:** Deploy latest Claude Opus model for high-stakes, complex, or parallel-requiring tasks.

**Execution trigger:** User says "deploy veronica" → immediate execution, no confirmation menu.

**What it does:**
1. Switch to Claude Opus (latest version available)
2. Spawn 2–3 subagents in parallel if task complexity requires it
3. Execute at maximum power/tokens needed (no cost constraints)
4. Perform 2-level quality checks at task completion (layer 1 review, layer 2 validation)
5. Return to Sonnet (default model) after task completion

**When to use:**
- Complex reasoning tasks (design, architecture, strategic decisions)
- Tasks requiring parallelization (multi-city operations, batch processing, resume generation with per-item subagents)
- High-stakes deliverables where quality assurance is non-negotiable
- Tasks requiring deep inference or edge-case handling

**Example invocations:**
- "Deploy veronica to generate 5 tailored resumes with subagents (one per resume) + quality check"
- "Deploy veronica to audit IG-Hunter scraper for security vulnerabilities"
- "Deploy veronica to design Friday 2.0 architecture with full research"

### Key Distinction: Veronica vs IG-1

| Aspect | Veronica | IG-1 Protocol |
|--------|----------|--------------|
| **Type** | Deployment standard | Instagram crawler |
| **Trigger** | "deploy veronica" | Scheduled or manual crawl |
| **Tools** | Claude Opus + subagents | Playwright, regex filtering, HTML scraping |
| **Cost** | Full token budget | Zero-token runtime (Opus cost was pre-deployment) |
| **Output** | High-quality reasoning deliverable | Follower list (500–3,500 range, 14 cities) |
| **Use case** | Strategic/design/complex work | Automated data collection (Instagram) |

**Never confuse them.** Veronica = thinking/reasoning/Opus. IG-1 = crawling/scraping/data.

---

## IG-1 Protocol (Instagram Crawler)

**Purpose:** Large-scale Instagram follower mining across 14 cities with zero-token runtime cost.

**Methodology:**
- Hashtag sweeps (10 tags per city: lifestyle, girl, women, blogger, fitness, etc.)
- HTML profile scraping (not API — avoids rate limits)
- Regex-based filtering: follower count 500–3,500, female-presenting accounts only
- Parallel city execution with auto-save

**Status:** Live, zero-token runtime cost, ready for APScheduler integration.

**Integration (Phase 3):** IG-1 → APScheduler (schedule) → Playwright (execute) → SQLite (store) → WhatsApp (notify)

---

## Codewords & Protocol Names

When Tanzim says a protocol name:
- **"Deploy veronica"** = Opus deployment, not Instagram crawler
- **"IG-1" or "IG1"** = Instagram crawler, not Opus
- **"A1"** = Historical protocol (deprecated June 4, 2026 — use Veronica instead)

All protocol definitions are version-controlled in `Tanzim_Frameworks/PROTOCOLS.md` on GitHub.
