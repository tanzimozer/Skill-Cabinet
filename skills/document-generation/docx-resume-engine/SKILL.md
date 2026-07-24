---
name: docx-resume-engine
description: Generate DOCX resumes from spec documents with strict validation gates
category: document-generation
created: 2026-06-01
updated: 2026-06-01
status: active
---

# DOCX Resume Engine

Generate DOCX resumes from a spec document and profile JSON. Built for TerraJob but applicable to any spec-driven document generation.

## When to Use

- User asks for tailored resumes from job listings
- Resume generation with strict formatting requirements
- Any DOCX generation with character limits, spacing specs, and validation gates

## Core Approach

### 1. READ THE SPEC END-TO-END FIRST

Never start coding until you've read every spec file completely. The spec is law.

**Critical spec files (TerraJob example):**
- `tanzim_resume_layout_5of8.md` — geometry, typography, spacing, colors
- `tanzim_resume_soul_7of8.md` — content psychology, bullet protocols
- `tanzim_resume_profile_4of8.json` — user data

### 2. SPEC COMPLIANCE IS NON-NEGOTIABLE

**Character limits — the trap:**
- Spec may say "target 122 chars" BUT also say "no wrap"
- If Section 8.3 says "bullets at 118+ chars start wrapping" → **117 is your real max**
- Always find the WRAP-SAFE limit, not just the target
- Target MAX FILL within wrap-safe (no white space at end of row)

**Spacing — use EXACT values:**
- Spec gives twips, use twips (1 inch = 1440 twips)
- Never reduce spacing to "fit more content" — spec values are designed to guarantee 1-page fit
- If content overflows, apply OVERFLOW LADDER (reduce content, not spacing)

### 3. VALIDATION GATES

Build validation into the engine, not as an afterthought:

```python
def fit_bullet(text, wrap_safe=117):
    """Bullet must not wrap — 117 is wrap-safe per spec 8.3"""
    if len(text) <= wrap_safe:
        return text
    # Trim at word boundary to exactly wrap_safe
    cut = text[:wrap_safe]
    last_space = cut.rfind(' ')
    return cut[:last_space].rstrip('.,;:') + '.'
```

Every bullet should log its char count. Every section should validate against spec limits.

### 4. CROSS-MATCH BEFORE SHIPPING

Before delivering ANY output:
1. List every spec constant (from Section 15 or equivalent)
2. List what your engine actually uses
3. Flag every mismatch
4. Fix mismatches before shipping

**Common mismatches that break things:**
- Bullet chars: spec says 122 target, but 117 is wrap-safe
- Spacing: reducing to fit more content
- Skills count: overflow cutting too aggressively
- Pipe colors: mixing up #666666 (contact/roles) vs #999999 (skills/certs)

### 5. OVERFLOW LADDER (when content exceeds 1 page)

Apply IN ORDER, re-render after each step:
1. Trim summary achievements
2. Trim swappable skills (15 → 12 → 10 → 8)
3. Drop closer bullet from oldest role
4. Reduce bullets per role
5. Drop projects/certs

**Never:**
- Shrink fonts
- Reduce margins
- Use italics
- Break the spacing spec

## User Expectations (Tanzim-specific)

- **Exact spec compliance** — he will open the DOCX and measure
- **Cross-match validation** — show the spec vs engine comparison
- **Fill the row** — bullets should use all available chars without wrapping (no white space)
- **One page** — overflow is failure; apply ladder
- **Read the spec** — if you miss something, he'll say "go read the spec again"

## Files

- `references/terrajob-spec-constants.md` — key constants from TerraJob spec

## Pitfalls

1. **122 vs 117** — Spec says target 122, but Section 8.3 says 118+ wraps. Use 117 max.
2. **Spacing shortcuts** — Don't reduce spacing to fit content. It breaks the brand.
3. **Not reading the whole spec** — The critical constraint is often buried in a subsection.
4. **Truncation without word boundaries** — Always cut at word boundary, add period.
5. **Missing validation** — Every bullet should log its char count.
