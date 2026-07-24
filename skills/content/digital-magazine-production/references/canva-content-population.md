# Canva Content Population Workflow

## The Problem

Canva Connect API **cannot directly edit text elements** in designs. The only programmatic content insertion is via Brand Templates with pre-tagged data fields (autofill datasets) — which requires the template creator to manually define `{{field_name}}` placeholders in advance.

**What doesn't work:**
- MCP servers (e.g., `@mcp_factory/canva-mcp-server`) — same underlying API limitation
- Direct text element manipulation via API
- Programmatic page editing without pre-defined data fields

## The Workflow That Works

For personality-driven magazines where content is curated from interview data/sheets:

### 1. Extract Source Data
Pull from Google Sheets tabs (e.g., Blair 2026):
- `Blair's Persona` — interview Q&A
- `Nutrition` — macro phases, food sources, protocol rules
- `Training Program` — split, exercises, hyperplasia protocols
- `Toning` — phase-specific supplements, water strategy, peak day protocol

### 2. Create Copy-Paste Document
Google Doc structured page-by-page matching the Canva template layout:
- Clear section headers with page numbers
- Content pre-formatted for each spread
- Pull **actual quotes and answers** from persona data
- Include real macro numbers, not placeholders

### 3. Manual Population
User opens Canva + Google Doc side-by-side, copies section by section.

### 4. Export PDF for Review
Use Google Drive API to export doc as PDF:
```python
drive_service.files().export_media(fileId=doc_id, mimeType='application/pdf')
```

Then send via WhatsApp bridge:
```bash
curl -s http://127.0.0.1:3000/send-media \
  -H "Content-Type: application/json" \
  -d '{
    "chatId": "<CHAT_ID>",
    "filePath": "/absolute/path/to/file.pdf",
    "mediaType": "document",
    "fileName": "Magazine_Content.pdf"
  }'
```

## Content Curation Principles

When extracting from sheets to magazine copy:

1. **Use actual quotes** — "I haven't fell off" hits harder than paraphrasing
2. **Real numbers** — "178g protein" not "adequate protein"
3. **Specific protocols** — "Loaded Stretch: 30s hold at stretched position" not "advanced techniques"
4. **Phase-specific data** — Show the progression (Phase 1 → Phase 5)
5. **Match page layout** — Structure doc sections to mirror template spreads

## Data Sources Checklist

For fitness personality magazines, pull from:
- [ ] Interview Q&A (morning routine, mistakes, alcohol stance, etc.)
- [ ] Macro phases with exact cal/protein/carb/fat per phase
- [ ] Training program (split, exercises, sets/reps, tempo, protocols)
- [ ] Supplement stack (daily baseline + training day + phase-specific)
- [ ] Toning/peak day protocols if applicable
- [ ] Food source tables by phase
- [ ] Cardio protocol
- [ ] Water/sodium strategy
