# Linked Engine — Dependency Install Notes

## Environment
- Python in use: **3.11** via `/home/hermes/.hermes/hermes-agent/venv`
- `which python3` → `/home/hermes/.hermes/hermes-agent/venv/bin/python3`
- System python3 is 3.12 at `/usr/bin/python3` — do NOT use this for the engine

## Install command (hermes venv pip)
```bash
/home/hermes/.hermes/hermes-agent/venv/bin/pip3 install PyMuPDF reportlab python-docx
```

## Why `pip install` alone doesn't work
Running `pip install` from inside the venv shell calls the **system pip** (PEP 668 blocks it). 
Use the venv pip3 path directly, or:
```bash
# Alternative — activate first
source /home/hermes/.hermes/hermes-agent/venv/bin/activate
pip install PyMuPDF reportlab python-docx
```

## PyMuPDF / fitz confusion
`import fitz` is the correct import name for PyMuPDF. If `fitz` is not found:
1. Confirm install: `/home/hermes/.hermes/hermes-agent/venv/bin/pip3 show PyMuPDF`
2. Check you're using the venv python: `python3 -c "import sys; print(sys.executable)"`
3. If installed in `.local/lib/python3.12/` but running 3.11 venv — reinstall into the venv

## Pillow conflict
If `from PIL import Image` raises `ImportError: cannot import name '_imaging'`:
```bash
pip uninstall Pillow -y --break-system-packages
pip install Pillow --break-system-packages --force-reinstall
```
This happened when two Pillow installs (3.11 venv + 3.12 .local) collided on PATH.

## Font fallback
Engine tries Liberation Sans (Linux Arial-equivalent) → falls back to Helvetica.
Liberation Sans path: `/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf`
If missing: `sudo apt-get install fonts-liberation`
