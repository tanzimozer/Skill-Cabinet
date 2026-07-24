# PDF Generation with fpdf2 — Technique & Gotchas

## Unicode fix (critical)
Default Helvetica in fpdf2 is Latin-1 only. Em-dashes (—), smart quotes, emoji all crash it.
**Fix: load a Unicode TTF font at init.**

```python
from fpdf import FPDF

FONT_REG  = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
FONT_BOLD = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'

pdf = PDF()
pdf.add_font('DV',  '', FONT_REG)
pdf.add_font('DVB', '', FONT_BOLD)
# Then use: pdf.set_font('DV', '', 9) and pdf.set_font('DVB', '', 11)
```

DejaVu fonts confirmed present at `/usr/share/fonts/truetype/dejavu/` on this VM.
Also available: Liberation Sans at `/usr/share/fonts/truetype/liberation/`.

## Clickable hyperlinks
Pass `link=url` to any `cell()` or `multi_cell()` call:
```python
pdf.cell(0, 5, url_text, link='https://...', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
```
Works in PDF readers; not in all email clients.

## Link verification before inclusion
Always check YouTube links resolve (200) before building the PDF:
```python
import urllib.request
def check_youtube(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    r = urllib.request.urlopen(req, timeout=10)
    return r.status  # 200 = live
```
YouTube returns 200 for valid videos even without auth. Dead/private videos return 4xx.

## execute_code sandbox caveat
`sheets_service` and other API clients built in one `execute_code` block are NOT available
in subsequent blocks — each block is an isolated Python process. Rebuild credentials
and clients at the top of each block.

## Output
```python
pdf.output('/tmp/filename.pdf')
```
File persists in /tmp across the session. Size check: `os.path.getsize(path)`.
