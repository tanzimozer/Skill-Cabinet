# TerraJob Resume Spec — Key Constants

From `tanzim_resume_layout_5of8.md` Section 15.

## Page Geometry

```
PAGE_WIDTH_TWIPS  = 12240    # 8.5"
PAGE_HEIGHT_TWIPS = 15840    # 11"
MARGIN_TWIPS      = 720      # 0.5" all sides
USABLE_WIDTH_PT   = 540      # 7.5" × 72 pt/in
```

## Typography

```
FONT              = "Calibri"  # NO SUBSTITUTIONS

SIZE_NAME_HP      = 76         # 38pt × 2
SIZE_CONTACT_HP   = 21         # 10.5pt × 2
SIZE_SECTION_HP   = 25         # 12.5pt × 2
SIZE_BODY_HP      = 21         # 10.5pt × 2
```

## Colors

```
COLOR_BLACK       = "000000"
COLOR_PIPE_DARK   = "666666"   # contact, role headers
COLOR_PIPE_LIGHT  = "999999"   # skills, certs, projects, education
```

## Spacing (twips)

| Context | before | after |
|---------|--------|-------|
| Name | 0 | 60 |
| Contact | 0 | 60 |
| Section header | 100 | 20 |
| Summary paragraph | 40 | 40 |
| Skills paragraph | 40 | 40 |
| Role header | 80 | 20 |
| Bullet | 10 | 10 |
| Education paragraph | 40 | 40 |
| Certifications paragraph | 10 | 10 |
| Projects paragraph | 40 | 40 |

## Content Limits

```
BULLET_TARGET_CHARS = 122      # target density
BULLET_MIN_CHARS    = 121      # density floor (±1)
BULLET_MAX_CHARS    = 123      # ceiling (±1)
BULLET_NO_WRAP_SAFE = 117      # ← ACTUAL MAX (118+ wraps)

SUMMARY_MAX_CHARS = 220
SKILL_SLOTS       = 21         # 6 core + 15 swappable
ROLES_PER_RESUME  = 4
BULLETS_SELECTED  = 5          # per role (4 scored + 1 closer)
```

## CRITICAL: 117 vs 122

Section 8.3 says:
> "bullets at 118+ chars start wrapping. Bullets ≤117 chars are wrap-safe regardless of character mix."

**The 122 target exists for "uniform density" but 117 is the HARD wrap-safe limit.**

When in doubt: use 117 as max, fill as close to 117 as possible.

## Pipe Separators

| Section | String | Color | Padding |
|---------|--------|-------|---------|
| Skills | `"  \|  "` | #999999 | Wide (2 spaces) |
| Certifications | `"  \|  "` | #999999 | Wide |
| Projects | `"  \|  "` | #999999 | Wide |
| Education | `"  \|  "` | #999999 | Wide |
| Contact | `" \| "` | #666666 | Narrow (1 space) |
| Role headers | `" \| "` | #666666 | Narrow |

## Overflow Ladder

If >1 page, apply in order:
1. Trim summary 4 → 3 achievements
2. Trim swappable skills 15 → 12
3. Trim swappable skills 12 → 10
4. Trim swappable skills 10 → 8
5. Drop closer bullet from oldest role
6. Drop oldest role's closer + reduce bullets 4 → 3
7. Set max_projects = 3
8. Last resort: ship 2-page with warning

**NEVER:** shrink fonts, change margins, use italics.
