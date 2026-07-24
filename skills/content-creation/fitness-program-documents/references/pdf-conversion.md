# PDF Conversion Methods for Fitness Documents

## Chromium Headless (Preferred)

### Command
```bash
chromium-browser --headless --disable-gpu --no-sandbox \
  --print-to-pdf=output.pdf input.html
```

### Availability Check
```bash
which chromium-browser chromium google-chrome chrome 2>/dev/null | head -1
```

### Expected Output
```
123036 bytes written to file output.pdf
```

### Common Warnings (Safe to Ignore)
- DBus/accessibility warnings
- libva/VAAPI messages
- AppArmor policy messages
- AT-SPI errors

**Success indicator**: Look for "bytes written to file" message, not absence of warnings.

### Timeout Recommendation
Use `timeout=30` in terminal calls to handle slow rendering.

## ReportLab (Python Library)

### When to Use
Direct PDF generation from Python code (no HTML intermediate step).

### Installation
```bash
python3 -m pip install reportlab
```

### Basic Pattern
```python
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

pdf_file = '/path/to/output.pdf'
doc = SimpleDocTemplate(pdf_file, pagesize=letter, 
                       topMargin=0.5*inch, bottomMargin=0.5*inch)

styles = getSampleStyleSheet()
story = []

# Add content
story.append(Paragraph("Title", styles['Heading1']))
story.append(Spacer(1, 0.2*inch))

# Build PDF
doc.build(story)
```

### Known Issue: HOME Directory Resolution
**Symptom:** `Error: Could not determine home directory`

**Cause:** ReportLab (or underlying font libraries) may fail to resolve `~` or HOME environment variable in certain contexts (background processes, cron jobs, execute_code blocks).

**Workaround:** Use HTML + Chromium headless instead of ReportLab:
1. Generate styled HTML with print-optimized CSS
2. Convert HTML → PDF via `chromium-browser --headless --print-to-pdf`

**When it occurs:**
- Running Python PDF generation in execute_code tool
- Background/scheduled tasks
- When HOME environment variable is unset or misconfigured

**Do NOT capture as:** "ReportLab doesn't work" — it works fine in normal Python environments. This is a context-specific resolution issue.

## Alternative Tools

### wkhtmltopdf
```bash
# Check availability
which wkhtmltopdf

# Convert
wkhtmltopdf input.html output.pdf
```

### WeasyPrint (Python)
```bash
# Install (if needed)
pip install weasyprint

# Convert
weasyprint input.html output.pdf
```

### Puppeteer (Node.js)
```javascript
const puppeteer = require('puppeteer');

(async () => {
  const browser = await puppeteer.launch();
  const page = await browser.newPage();
  await page.goto('file:///path/to/input.html');
  await page.pdf({ path: 'output.pdf', format: 'Letter' });
  await browser.close();
})();
```

## Troubleshooting

### PDF Generation Failed
1. **Check tool availability first** - Don't assume any tool is installed
2. **Fallback order**: Chromium → wkhtmltopdf → WeasyPrint → raw HTML
3. **HTML is always viewable** - PDF is enhancement, not requirement

### Page Breaks Issues
Add to CSS:
```css
@page {
    size: letter;
    margin: 0.5in;
}

.section {
    page-break-inside: avoid;
}
```

### Content Overflow (Doesn't Fit on Page)
- Reduce font size: 9pt body → 8.5pt body
- Reduce margins: 0.5in → 0.4in
- Use grid layouts to maximize space
- Consider 2-page layout for comprehensive programs

### Chromium Snap Restrictions
If Chromium is installed via snap, it may have restricted file access. Use full absolute paths:
```bash
chromium-browser --headless --disable-gpu --no-sandbox \
  --print-to-pdf=/home/user/output.pdf \
  /home/user/input.html
```

## Quality Checks

After PDF generation:
```bash
# Verify file created
ls -lh output.pdf

# Check page count
file output.pdf
# Should show: "PDF document, version 1.4, N page(s)"
```

Expected size range: 80-200 KB for typical workout one-pager (1-2 pages).
