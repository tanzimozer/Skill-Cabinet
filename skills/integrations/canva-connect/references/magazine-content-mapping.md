# Magazine Content Mapping

## Two-Product Strategy

When building fitness/lifestyle magazines, consider splitting into two product lines:

| Product | Style | Price Point | Purpose |
|---------|-------|-------------|---------|
| **The Magazine** | Editorial, story-driven, photography-heavy | $15-25 | Premium deep read, aspirational |
| **Workout Pack / Playbook** | Utility, clean, screenshot-friendly | $5-10 | Quick reference, repeat use |

Bundle pricing: Magazine + Pack at ~20% discount.

## Standard Editorial TOC Structure

For personal brand magazines, this structure works:

1. **Editor's Note** — Personal voice, the "why" behind sharing
2. **Origin Story** — Background, journey, what shaped them
3. **Philosophy / Mindset** — Core beliefs, mental frameworks
4. **Training / Work / Routine** — The actual schedule, weekly structure
5. **Nutrition / Lifestyle** — Food approach, macros, meal structure
6. **Playbook** — Tactical protocols, supplement stacks
7. **Aesthetic / Fashion / Vibe** — Style, personal expression
8. **On the Move** — Travel, locations, movement outside gym
9. **Closing Feature** — Vision, what's next, call to action

## Content Mapping Table

Map client profile data to template sections:

| Template Section | Profile Questions to Pull From |
|------------------|-------------------------------|
| Cover | Name, tagline, hero photo |
| Editor's Note | Why they're sharing, mission |
| Origin Story | Hometown, early fitness journey, turning points |
| Philosophy | Core beliefs, mental approach, what they've learned |
| Training | Weekly split, exercise selection, RPE/intensity |
| Nutrition | Macro targets, meal timing, staple foods |
| Playbook | Workout protocols, supplement stack |
| On the Move | Favorite spots, gyms, food recommendations |
| Closing | Goals, upcoming events, where to follow |

## Design Option Analysis

When comparing layout options, assess:

| Dimension | Option A | Option B |
|-----------|----------|----------|
| **Focus** | Brand content vs Personal story |
| **Tone** | Utility/clean vs Editorial/aspirational |
| **Photography** | Stock/illustrations vs Custom shoot |
| **Structure** | Loose pages vs Full TOC |
| **Copy style** | Generic/templated vs Personal narrative |

Look for: Hook/tagline that threads through, behind-the-scenes authenticity, lifestyle shots breaking up fitness content.

## Canva Design ID Extraction

From Canva share links:
```
https://canva.link/XXXXX → resolve redirect → extract design_id from URL

Example:
https://canva.link/478qmre0y4lpp69
→ https://www.canva.com/design/DAG9awLrJbg/LYW5D-OcK_NhIJdhFmxb5g/edit?...
→ Design ID: DAG9awLrJbg
```

Use `requests.head(short_url, allow_redirects=True).url` to resolve.
