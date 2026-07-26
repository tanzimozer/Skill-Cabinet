# VOL.01 Production Notes — Seattle Fitness Culture 2026

## What Worked
- Fitt Insider voice landed better than People Magazine voice for TIMBR — staccato, declarative, verdict-led
- PDF programmatic pipeline (ReportLab) is cleaner and more reliable than Canva for recurring issues
- Section colour coding by hex made the PDF feel premium without a designer
- Pull quotes from real lines (not editorial summaries) read significantly better

## What Didn't Work
- People Magazine voice (v2) rejected by Tanzim — "I don't like the text content"
- Generic second-person wellness register is explicitly banned from TIMBR
- Curly quotes inside Python f-strings cause SyntaxError — replace with HTML entities (&quot; &ldquo; &rdquo;) before building PDF

## Python PDF Pitfalls
- Curly/smart quotes in body text must be converted to HTML entities before insertion into ReportLab Paragraph strings
- Fix: `content.replace('"', '&ldquo;').replace('"', '&rdquo;')` before writing to .py file
- NextPageTemplate must appear BEFORE the content for that page, not after
- Section colour state stored in mutable dict `state = {"colour": ...}` — accessed in page callback

## Voice Iterations
- v1: Generic editorial voice — too bland
- v2: People Magazine (named people, scene-first) — rejected
- v3: Fitt Insider adapted (staccato, declarative, verdict-led) — approved direction

## File Locations
- Script: `/home/hermes/timbr/timbr_vol01.py`
- Sections module: `/home/hermes/timbr/build_sections.py`
- Images: `/home/hermes/timbr/images/` (12 images)
- Output: `/home/hermes/timbr/TIMBR_VOL01_SEATTLE-FITNESS-CULTURE_2026-07.pdf`

## Google Assets
- Content doc: https://docs.google.com/document/d/1qk9sS4EE4qB9qxNUFpnmqRUW9Xoc2Z-Ylv8JMIjQx8U
- Production tracker: https://docs.google.com/spreadsheets/d/1wtP5nkAdcgx6tZsZBsX3s9U_5xKuYV4kLqH9FrjgNZM
- Images Drive: https://drive.google.com/drive/folders/1ATuTENat85wG-N-MDo72E1BTqrQL_pIO

## EIC Checklist Build Status
Checklist being built interactively with Tanzim. Items defined so far:
1. Reader Satisfaction — culture + fitness angle exceptional; people supporting not leading
2. Value to Reader — 4 mandatory elements: workout plan, nutrition spots, fitness spots, location features
Items 3+ = resume next session. Next question: does every issue require all 4 value elements or varies by theme?
