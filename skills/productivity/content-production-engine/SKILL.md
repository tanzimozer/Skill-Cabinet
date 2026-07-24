---
name: content-production-engine
description: "Create structured production blueprints (engines) for delegating content/creative work to Claude Code — magazines, programs, marketing collateral."
version: 1.0.0
author: Friday
tags: [content, production, blueprint, engine, delegation, claude-code, magazine, program]
---

# Content Production Engine

## When to Use
- User needs to produce repeatable content (magazines, fitness programs, marketing materials)
- Work should be delegated to Claude Code or another AI agent
- User wants to run production in parallel while Friday handles other tasks
- Content has a consistent structure that can be templated

## What a Production Engine Is

A **production engine** is a markdown file that contains:
1. **Product definition** — what's being created, format, price point
2. **Brand voice** — tone, style, what to avoid
3. **Structure template** — page-by-page or section-by-section breakdown
4. **Required inputs** — checklist of what's needed before running
5. **Execution prompt** — copy-paste prompt for Claude Code
6. **Output format** — what the engine produces
7. **Design specs** — colors, fonts, spacing

## Engine Document Structure

```markdown
# [ENGINE NAME] v1.0

**PRODUCT:** [What it is, page count, price, format]

**BRAND VOICE:** [Tone description, what to avoid, cultural positioning]

---

## STRUCTURE

### [SECTION 1]: [Name]
- Bullet points of what goes here
- Photo placement notes

### [SECTION 2]: [Name]
- Content requirements
- Word count guidance

[Continue for all sections...]

---

## INPUTS REQUIRED

| # | Input | Description |
|---|-------|-------------|
| 1 | [Input name] | [What to provide] |
| 2 | [Input name] | [What to provide] |
[Continue for all inputs...]

---

## EXECUTION PROMPT

```
[Copy-paste prompt for Claude Code with placeholders]
```

---

## OUTPUT FORMAT

1. **[Format 1]** — [Description]
2. **[Format 2]** — [Description]

---

## DESIGN SPECS

| Element | Specification |
|---------|---------------|
| Background | [Color/hex] |
| Primary text | [Color/hex] |
| Accent | [Color/hex] |
| Fonts | [Font names] |
| Page size | [Dimensions] |
```

## Step-by-Step Creation

### 1. Define the Product
Ask user:
- What are you creating? (magazine, program, guide, etc.)
- How many pages/sections?
- What's the price point?
- Digital or print format?

### 2. Establish Brand Voice
Ask user:
- What tone? (premium, casual, edgy, professional)
- What cultural context? (Seattle fitness vs LA influencer vs NYC corporate)
- What to avoid? (clichés, specific phrases)

### 3. Map the Structure
Break down the product section by section:
- What content goes on each page?
- Where do photos go?
- What's the flow/narrative arc?

### 4. Define Required Inputs
List everything needed before production can run:
- Text content (bios, quotes, descriptions)
- Photos (with placement notes)
- Data (workout routines, meal plans)
- Branding assets (logos, colors)

### 5. Write the Execution Prompt
Create a complete prompt that:
- Sets context for Claude Code
- References the structure
- Specifies output format
- Includes all placeholders for inputs

### 6. Specify Design System
Document:
- Color palette (hex codes)
- Typography (font families, sizes)
- Layout rules (margins, spacing)
- Photo treatment (filters, overlays)

## Storage Location

Save engines to Google Drive in the HERMES folder (or project-specific folder):
- Filename: `[ENGINE_NAME].md` (e.g., `MAGPROD_ENGINE.md`)
- Include version in the document header

```python
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from googleapiclient.http import MediaFileUpload

creds = Credentials.from_authorized_user_file('/home/hermes/.hermes/google_token.json')
drive = build('drive', 'v3', credentials=creds)

folder_id = 'TARGET_FOLDER_ID'
media = MediaFileUpload('/tmp/ENGINE_NAME.md', mimetype='text/markdown')
f = drive.files().create(
    body={'name': 'ENGINE_NAME.md', 'parents': [folder_id]},
    media_body=media,
    fields='id, name, webViewLink'
).execute()
print(f"Link: {f['webViewLink']}")
```

## Example: MAGPROD_ENGINE (TIMBR Magazine)

**Product:** Digital fitness magazine, 8-12 pages, $14.99, PDF
**Voice:** Premium but approachable, Seattle fitness culture, PNW authentic
**Structure:** Cover → Story → Philosophy → Day in Life → Workout → Mindset → Back Cover
**Inputs:** Trainer name, bio, specialty, principles, meals, workout, quote, photos
**Output:** Markdown content + styled HTML for PDF export

Location: Google Drive > HERMES > MAGPROD_ENGINE.md

## Parallel Execution Pattern

1. Friday creates the engine and stores in Drive
2. User loads engine into Claude Code with filled inputs
3. Claude Code produces the content
4. User reviews and exports to final format
5. Friday handles other tasks simultaneously (e.g., Wix store setup)

## Pitfalls

- **Vague structure:** Be specific about what goes on each page — Claude Code needs clear guidance
- **Missing inputs:** If an input is optional, mark it as such; otherwise production will stall
- **No design specs:** Without colors/fonts, output will be inconsistent
- **Overly complex prompts:** Keep the execution prompt focused; don't try to do too much in one run
- **No output format:** Specify whether you want markdown, HTML, or both

## Related Engines

| Engine | Purpose | Location |
|--------|---------|----------|
| MAGPROD_ENGINE | TIMBR fitness magazines | Drive > HERMES |
| [Add more as created] | | |
