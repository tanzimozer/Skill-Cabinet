# Friday Self-Diagnostic Protocol

**Context:** Tanzim expects Friday to proactively identify operational inefficiencies and surface them directly. This is NOT a code debugging skill — it's a self-audit protocol for AI assistant performance.

## When to Run Self-Diagnostics

Triggered by:
- Explicit user request: "run self diagnostics on your inefficiencies"
- Pattern of repeated failures on the same class of problem
- User frustration signals: "you didn't check X first", "why didn't you just..."
- Credential/access failures that should have been prevented

## The Self-Diagnostic Framework

### 1. Inventory Recent Failures (Last 30 mins)
- What did you attempt?
- What failed? (timeouts, auth errors, missing data, wrong path)
- Did you retry? How many times?
- Did you give up or ask the user?

### 2. Identify Pattern
- Is this the first time you've hit this failure? (instance problem)
- Or the N-th time on the same class of problem? (pattern problem)
- What caused this time? (different root vs. same root)

### 3. Trace Ownership
- **Environment failures** (missing binary, fresh install, unconfigured creds, missing package): User owns. Document the fix, don't own it.
- **Tool/feature failures** (tool doesn't work, API broken): External. Identify workaround, don't declare tool "broken" in skills.
- **Process failures** (you didn't check the right place first, wrong tool order, didn't read existing data): **You own this.**
- **Transient errors** (temporary 429, one-time timeout that resolved on retry): Don't capture as skill — just the retry pattern.

### 4. Classify Inefficiencies (Process Failures Only)

**Inefficiency Type: Access Hierarchy Violation**
- **Instance:** Tried encrypted EDITH vault first without checking unencrypted Credentials Sheet.
- **Pattern:** Always pull from most-accessible source first (Sheet > USER.md backups > encrypted vault).
- **Owner:** Friday (me).
- **Fix location:** `references/credential-access-hierarchy.md` in `credential-management` skill.

**Inefficiency Type: Browser Tool Over-reliance**
- **Instance:** Attempted Google Sheets API 3 times via browser, all timeouts. Should have tried Python API with retry logic.
- **Pattern:** Browser tools timeout on Google services; use Python SDK + exponential backoff instead.
- **Owner:** Friday (me).
- **Fix location:** Patch `google-sheets-batch-operations` skill.

**Inefficiency Type: Diagnostic Skipping**
- **Instance:** Hit OAuth error, didn't check if EDITH vault had the right scopes before re-generating auth flow.
- **Pattern:** Always audit existing credentials first — check what's stored, what scopes exist, whether the issue is misconfiguration vs. missing token.
- **Owner:** Friday (me).
- **Fix location:** New reference file `references/oauth-credential-audit.md` in `google-oauth-refresh` skill.

### 5. Report

Format:
```
SELF-DIAGNOSTIC REPORT

Failures Analyzed: [N] in past [timeframe]
Patterns Identified: [X] process inefficiencies, [Y] external blockers

INEFFICIENCY 1: [Class]
- Instances: [when/what]
- Root: [why it happened]
- Fix: Updated skill [name] with reference [file] or patch [section]

INEFFICIENCY 2: [Class]
...

EXTERNAL BLOCKERS (not yours to fix):
- [Blocker]: [why user owns it]

NEXT SESSION:
- Load and review: [updated skills]
- Verify: [patterns don't repeat]
```

### 6. Make the Fix (Skills Only)

Once you've identified a process inefficiency:
1. Find the skill that governs that class of work
2. Patch it with the lesson
3. Add a reference file if the detail is session-specific
4. One-line pointer in SKILL.md so next agent finds it

**Never** capture as skill:
- Environment setup failures
- Tool/feature negative claims ("X doesn't work")
- One-off transient errors
- One-session task narratives

---

## Example: Credential Access Inefficiency

**What Happened:**
Tanzim said: "you didn't find the game memory or I'd say" — meaning I should have checked Credentials Sheet first instead of asking him for passphrases.

**Self-Diagnostic:**
- Failure: Asked for EDITH vault access (passphrase + security questions) when GitHub PAT was already in Credentials Sheet
- Pattern: This is repeatable — happens when credentials exist in multiple places
- Root: No documented access hierarchy. I treated all sources as equally difficult.
- Owner: Me (process failure, not tool)
- Fix: Document credential access hierarchy in skill

**The Fix:**
In `credential-management` skill (or create `friday-credential-access-patterns`), add reference file:

```markdown
# Credential Access Hierarchy

Tanzim stores credentials in three places:
1. **Credentials Google Sheet** (accessible, no auth required) — pull here first
2. **USER.md backups** (visible in ~/.hermes/backups/) — pull here second
3. **EDITH vault** (~/.hermes/.edith/edith_vault.json, AES-256-GCM encrypted) — pull here last

**Rule:** Always try in this order. Only ask for EDITH passphrase/questions if credential is not in Sheet or USER.md.
```

Next session: I load the updated skill and start at source 1, not source 3.

---

## Why This Matters

Tanzim said "run self diagnostics" because:
1. He expects me to own my mistakes (not blame tools)
2. He wants the diagnosis documented so next session starts improved
3. He's testing whether I can identify patterns, not just execute
4. This builds confidence in the system — I get better through self-reflection

**Self-diagnostics = Skills updates = Better next session.**
