# PDF → Reviewable Images

When you need to *see* a PDF (design critique, layout review, vision analysis) and
only have the file, convert it to images first. Vision tools and humans both work
off PNGs, not raw PDF.

## Render pages to PNG (poppler)

```bash
# Inspect first
pdfinfo file.pdf            # pages, page size, producer (e.g. Canva)

# One PNG per page at review resolution
mkdir -p pages
pdftoppm -png -r 80 file.pdf pages/p     # -> pages/p-01.png, p-02.png, ...
```

- `-r 80` is fine for a thumbnail/contact-sheet pass; bump to `-r 150` for detail.
- Canva/design exports are often **outline text** — `pdftotext` returns empty.
  Don't expect to read copy from the text layer; you must render and look.

## Contact sheet WITHOUT ImageMagick

`montage`/`convert` are frequently not installed. Don't block on them — assemble
the grid with PIL instead:

```python
from PIL import Image
import glob, os
files = sorted(glob.glob('pages/p-*.png'))
imgs = [Image.open(f) for f in files]
w, h = imgs[0].size
cols = 5
rows = (len(imgs) + cols - 1) // cols
sheet = Image.new('RGB', (cols*w, rows*h), 'gray')
for i, im in enumerate(imgs):
    sheet.paste(im, ((i % cols)*w, (i // cols)*h))
sheet.save('contact.png')
```

Then send individual pages or the contact sheet to the vision tool.

## Pitfalls

- **Don't critique a design you cannot actually see.** If the vision pipeline is
  unavailable, say so and ask for screenshots — never fabricate a visual opinion.
- **Canva `/edit` and most share links require login** and will hang a headless
  browser indefinitely. Ask for an "anyone with the link can view" URL or the
  exported file; don't keep retrying the edit URL.
