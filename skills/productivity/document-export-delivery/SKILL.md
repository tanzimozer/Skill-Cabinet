---
name: document-export-delivery
description: "Convert research/content to PDF and deliver via messaging (WhatsApp, etc)."
version: 1.0.0
author: Friday
platforms: [linux, macos]
metadata:
  hermes:
    tags: [PDF, documents, delivery, WhatsApp, pandoc, export]
    related_skills: [github-repo-management]
---

# Document Export & Delivery

Convert markdown research or structured content to PDF and send via messaging platform.

## Preferred Stack

- **Conversion**: `pandoc` + `weasyprint` (both available on the VM)
- **Delivery**: `send_message` tool → `whatsapp:Tanzim Ozer (dm)`

## Standard Workflow

```bash
# 1. Write content to markdown file
# (use write_file tool)

# 2. Convert to PDF
pandoc /tmp/filename.md -o /tmp/filename.pdf --pdf-engine=weasyprint

# Warnings about unknown CSS properties are safe to ignore — output is fine
```

Then deliver via `send_message`:
- Target: `whatsapp:Tanzim Ozer (dm)`
- Message: `[file]/tmp/filename.pdf[/file]`

## Pitfalls

- **WhatsApp 401**: File delivery via WhatsApp can fail with a 401 auth error. If it does, tell Boss the PDF is at the `/tmp/` path and offer alternative delivery (upload somewhere, try again, etc.). Do not silently fail.
- **pandoc title warning**: `nonempty <title>` warning is benign — add `--metadata title="..."` to suppress if needed.
- **CSS warnings from weasyprint**: `text-rendering`, `overflow-x`, `gap: min(...)` — all ignorable, don't affect output.
- **Sender platform mismatch**: Lark/WhatsApp sender IDs (e.g. `160799431606497@lid`) are NOT valid `send_message` targets. Always use `send_message action=list` to find the right target if unsure.

## When Boss Says "Send it here" / "Drop it on the chat"

That means: convert → PDF → send to `whatsapp:Tanzim Ozer (dm)`. Do it in one pass, no confirmation needed.
