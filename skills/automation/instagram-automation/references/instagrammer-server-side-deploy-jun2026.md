# Instagrammer — Server-Side Re-Engineering & Deploy-on-Command (Jun 2026)

Context: Tanzim wants the whole Instagrammer engine runnable **from his AI assistant
on command** ("I tell you deploy, it deploys"), with Friday in close control —
*never logging into his Mac to run it*. This reference captures the diagnostic read,
the two competing architectures evaluated (hub-and-spoke, two teams), and the call.

## The whole problem reduces to ONE thing: discovery egress

Diagnostics on `github.com/tanzimozer/Instagrammer` (Jun 2026):
- The engine runs clean server-side in **dryrun** today — all 7 stages, deps present,
  `python run.py` returns counts with no errors.
- Enrich / filter / store / output / follow all already run server-side fine.
- The ONLY reason Tanzim is chained to the Mac is **Stage 1 CRAWL discovery**:
  IG blocks the discovery surfaces (`/api/v1/web/search/topsearch`,
  `/api/v1/tags/web_info`, `/api/v1/discover/chaining`) from datacenter IPs.
  The Mac runs them from his residential IP via a launchd job and writes handles
  to the Sheet Queue tab.

So "run it from here" = **solve residential-IP discovery egress**, then the whole
thing collapses onto the server under assistant control. Everything else is plumbing.
(This matches the capability split already in the main SKILL: per-handle enrich works
in-browser from the VM; only bulk discovery is IP-walled.)

## LATENT BUG found by BOTH design teams — fix this FIRST, regardless of path

**There is no Sheet→SQLite ingest step anywhere in the codebase.** The Mac writes
discovered handles to the Google Sheet **Queue** tab, but `stages/filter.py` reads the
**SQLite `queue`** table (`SELECT username FROM queue WHERE status='discovered'`).
Nothing bridges Sheet→DB. The pipeline is quietly broken end-to-end *today* — independent
of which deploy architecture is chosen. **Phase 0 of any build is `stages/ingest.py`.**

## Two architectures evaluated (hub-and-spoke, Friday = hub)

### Team A — EGRESS (kill the Mac entirely)
Route the server's discovery browser traffic through a residential egress. Transport seam
already isolated: `stages/crawl.py::make_worker` → Playwright `new_context(proxy=...)` is a
one-line injection point. (A) Commercial residential proxies ~$10–40/mo, no hardware, block
risk MEDIUM. (B) Self-hosted home tunnel (Pi/Mac WireGuard) ~$0 but reintroduces a home box.
(C) Hybrid.

### Team B — SPOKE (keep the Mac as a controllable worker)
Always-on `KeepAlive` agent polls a Google Sheet `Control` tab (HMAC+TTL+nonce commands),
runs discovery on demand, writes status+heartbeat. Zero new infra (both sides already authed
to the Sheet), outbound-poll-only, queues gracefully when Mac offline.

## Friday's original recommendation vs. WHAT GOT BUILT

Original hub call: **Team A egress, proxy-first.** Rationale: literal ask is "never touch the
Mac"; proxy severs the dependency with no hardware.

**DECISION FLIPPED (Jun 27 2026): built Team B (Mac-spoke), zero-cash.** Tanzim said plainly
"I don't want to deploy any cash to it" and "my Mac always stays on." A hard no-spend
constraint + an always-on Mac inverts the tradeoff — the proxy's only advantage (no home
dependency) is moot when he's keeping the Mac up anyway, and it costs money he won't spend.
**Lesson: state the engineering-best recommendation, but when the user gives a hard cost/asset
constraint, re-pick to the constrained-optimal path immediately — don't defend the original.**
The proxy `proxy=` seam stays documented as the paid upgrade if home yield ever disappoints.

## v2 BUILD — shipped Jun 27 2026, commit 231c016 on main

**Discovery rewrite (`core/chase.py`).** Tanzim's locked spec (10 questions, one at a time):
seed = followers of `tanzim.ozer`; chain outward via `discover/chaining` from each survivor;
chase until **100 survivors** or frontier exhausted. **No hashtags, no screenshots.** Pure
orchestration with IG IO injected as `get_followers`/`get_profile`/`get_chain` — identical
loop runs live on Mac and against a synthetic IG in dryrun.

**Quality engine (`modules/persona_filter.py`).** ONE shared keep/maybe/drop, imported by Mac
and server. fitness/sport/wellness · female · followers 500–3500 **±10%** · 9 cities (seattle,
sydney, melbourne, gold coast, vancouver, portland, london, alaska, dallas). **LENIENT on every
ambiguous gate** (his explicit "keep it as maybe"): unclear location/gender or near-band →
"maybe" + flag, never silent drop. Hard drops only: male, no-niche, private/business/verified,
promo-shop. Bug a test caught: unisex names (jordan/taylor) in the female dict mislabel men as
keeps — keep names female-leaning, let unisex fall to gender-unknown→maybe.

**Control plane.** `core/control.py` = HMAC-SHA256 command bus over a `Control` tab.
`mac/mac_agent.py` = always-on KeepAlive poller (~20s), verifies sig+TTL+last-done-id, runs
discovery under `caffeinate`, writes status+heartbeat. `orchestrator/deploy.py` = Friday's
"deploy": issue→poll→server pipeline (ingest→enrich→output→follow)→report. Heartbeat freshness
→ "Mac offline, queued" instead of hanging.

**File inventory (this build):**
- Server repo `~/Instagrammer`: `modules/persona_filter.py`, `core/chase.py`, `core/control.py`,
  `stages/ingest.py`, `orchestrator/deploy.py`, edits to `core/sheet_mirror.py`
  (read_tab/append_rows), `orchestrator/loop.py` (ingest-first), `config/engine.config.yaml`
  (targeting + results_tab + control_hmac_ref). Tests: `tests/test_persona_filter.py` (11),
  `tests/test_chase.py` (3), `tests/test_control.py` (5). Full suite 21 passed.
- Mac bundle `~/.hermes/instagrammer/mac/` AND vendored copies in repo `mac/`: `mac_agent.py`,
  `mac_discovery_v2.py`, `ig_fetchers.py`, `install_v2.sh`, `com.tanzim.instagrammer.agent.plist`,
  plus flat-vendored `chase.py`/`control.py`/`persona_filter.py` (installer copies them next to
  the venv; Mac layout = flat imports + `modules/persona_filter.py`).

**Build sequence (worked):** ingest bridge → quality engine + tests → chase + synthetic dryrun
→ control plane + HMAC tests → Mac agent/installer → full regression → commit+push. Each layer
proven with no-network tests before wiring the next. `python run.py` dryruns clean with NO
secrets (ingest fail-soft when no Google token) — the cheap pre-install wiring gate.

## INSTALL HANDOFF — what's left for Tanzim (still pending as of this session)

1. Run `mac/install_v2.sh` once on the Mac (sets up KeepAlive agent, retires the 9am cron,
   applies `pmset -c sleep 0` no-sleep-on-AC posture).
2. Place the shared `control_secret` (HMAC) on BOTH sides — same value in
   `~/.instagrammer/secrets/control_secret` (Mac) and the server's `CONTROL_HMAC` env. Walk
   him through it; he's not a CLI user.
3. First real "deploy" is the true test of live IG API behaviour under rate limits — the
   synthetic dryrun proved the *yield logic* (100/100), NOT live limits. Paced to fail safe.
   Follow stays OFF until he explicitly authorises.

## Render-before-production validation (he asked for this explicitly)

`tests/test_chase.py` builds a fake-IG world (noise majority + target minority + homophily
similar-graph) and proves the chase reaches exactly 100 with zero network. `test_control.py`
proves HMAC accept/tamper/wrong-secret/expired/malformed. The secret-free `run.py` dryrun
proves end-to-end wiring. Promotion gate: live discovery only after these pass; live follow
only after a live-discovery + dryrun-follow pass on the real sheet.

## Process notes (orchestration)

- Tanzim asked for two teams hub-and-spoke → spawn both designs in parallel, deliver the hub's
  synthesis + a single recommendation, not a both-sides shrug.
- A design subagent timed out at the 600s wall on a long doc; fix = re-run tighter (spend budget
  WRITING, ~250 lines, glance not deep-read). Long greenfield design docs are the failure mode.
- Ten-question requirements intake (one at a time) before building worked well for a fuzzy
  "re-engineer the whole thing" ask — read each answer back as a locked spec before coding.
- Both design docs live in repo: `docs/REMOTE_TRIGGER_DESIGN.md`, `docs/RESIDENTIAL_EGRESS_DESIGN.md`.
