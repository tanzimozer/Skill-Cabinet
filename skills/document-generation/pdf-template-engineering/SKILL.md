---
name: pdf-template-engineering
description: Building PDF templates with guaranteed fixed layouts using hard character limits
trigger: generating PDFs with fixed layouts, template-based documents, single-page constraints, reportlab layouts
version: 1
---

# PDF Template Engineering

When building PDF templates that must maintain fixed layouts (single-page, specific dimensions, guaranteed formatting).

## Core Principle: Hard Limits, Not Dynamic Sizing

Dynamic content + auto-pagination = layout breakage. For templates with strict layout requirements:

1. **Define hard character limits for every variable field**
2. **Auto-truncate with ellipsis before render, not after**
3. **Print warnings when truncation occurs — don't fail silently**

## Standard Limits Pattern (reportlab, US Letter)

```python
LIMITS = {
    'TITLE': 70,           # ~1 line at 22pt
    'SUBTITLE': 120,       # ~1-2 lines at 10pt
    'SECTION_TEXT': 280,   # ~3 lines at 9pt
    'LIST_ITEM': 85,       # 1 line with number/bullet indent
    'TABLE_CELL': 25,      # Prevents cell wrap
}

def truncate(text, max_len, ellipsis=True):
    text = str(text).strip()
    if len(text) <= max_len:
        return text
    if ellipsis and max_len > 3:
        return text[:max_len-3].rstrip() + "..."
    return text[:max_len]

def enforce_limits(config):
    """Call BEFORE render. Mutates config, returns list of warnings."""
    errors = []
    for field, limit in LIMITS.items():
        if field in config and len(config[field]) > limit:
            config[field] = truncate(config[field], limit)
            errors.append(f"{field} truncated to {limit} chars")
    return errors
```

## Verification Gate

Always verify output before committing state changes:

```python
def _verify_staging(pdf_path):
    import fitz
    doc = fitz.open(pdf_path)
    pages = doc.page_count
    doc.close()
    if pages != 1:
        raise RuntimeError(f"PDF has {pages} pages, expected 1")
```

## Pitfalls

- **Don't rely on auto-pagination for single-page templates** — it triggers AFTER overflow, breaking the layout guarantee
- **GAP/spacing variables are fragile** — if users tune them manually per article, the template will eventually break
- **Test with maximum-length content** — fill every field to its limit and verify layout holds

## References

- `references/linked-engine-limits.md` — specific limits for LinkedIn article template
