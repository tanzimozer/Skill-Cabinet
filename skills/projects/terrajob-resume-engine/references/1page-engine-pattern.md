# Working 1-Page Engine Pattern

Validated engine constants that produce 1-page DOCX output. Use these exact values.

## Content Limits (overflow-safe)

```python
ROLES = 4
BULLETS_PER_ROLE = 4          # Reduced from 5
CORE_SKILLS = 6               # Fixed
SWAP_SKILLS = 4               # Reduced from 15 (aggressive for guaranteed fit)
MAX_CERTS = 3
MAX_PROJECTS = 2
MAX_BULLET_CHARS = 117        # Wrap-safe ceiling
SUMMARY_MAX = 220
```

## Spacing (exact twips from Section 6)

```python
SP_NAME = (0, 60)
SP_CONTACT = (0, 60)
SP_SECTION = (100, 20)
SP_SUMMARY = (40, 40)
SP_SKILLS = (40, 40)
SP_ROLE = (80, 20)
SP_BULLET = (10, 10)
SP_EDU = (40, 40)
SP_CERTS = (10, 10)
SP_PROJECTS = (40, 40)
```

## Bullet Trimming Function

```python
def trim(text, limit=117):
    """Trim to limit at word boundary, end with period."""
    text = text.strip()
    if not text.endswith('.'):
        text += '.'
    if len(text) <= limit:
        return text
    cut = text[:limit]
    sp = cut.rfind(' ')
    if sp > limit - 25:
        return cut[:sp].rstrip('.,;:') + '.'
    return cut.rstrip('.,;:') + '.'
```

## Max Fill Principle

Tanzim expects bullets to FILL the row — no visible white space at the end. Target 115-117 chars (tight to limit). If original bullet is too short, don't pad it — just use as-is.

## Subagent Deployment Pattern

When generating multiple resumes:
1. Max 3 concurrent subagents (Hermes limit)
2. Run in batches: first 3, then remaining
3. Add 1 QC agent to verify all outputs
4. QC checks: file exists, file size ~38-40KB, valid DOCX structure

Example batch:
```
Batch 1: Jobs 1-3 (3 resume agents)
Batch 2: Jobs 4-5 (2 resume agents) + QC agent
```

## Post-Generation Workflow

1. Upload DOCX to Drive folder (19ne7DfKX7bn1A-guddBhMIr9keAjB1WK)
2. Update Sheet column A with HYPERLINK formula: `=HYPERLINK("url","📄 Company")`
3. Verify hyperlinks render correctly in sheet

## Profile JSON Key Mapping

Watch for these mismatches between spec and actual JSON:
- `default_title` not `title`
- `core_skills` not `skills.core`
- `swappable_skills` not `skills.swappable`
- Bullets may be dicts with `text` key or plain strings
- Certifications may be strings or dicts
