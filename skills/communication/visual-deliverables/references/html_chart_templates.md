# HTML Chart Templates — TIMBR Apple-style

These are the proven skeletons from the June 2026 TIMBR visual session.
Copy, adapt content, re-render via Playwright.

---

## Shared CSS Reset + Palette

```html
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body {
    width: 1600px; height: 1000px;
    background: #FAFAFA;
    font-family: -apple-system, 'SF Pro Display', 'Helvetica Neue', Arial, sans-serif;
    color: #1A1A1A; overflow: hidden;
  }
  .header {
    background: #fff; border-bottom: 1px solid #E5E5EA;
    padding: 28px 60px 22px; display: flex; align-items: baseline; gap: 16px;
  }
  .header h1 { font-size: 32px; font-weight: 700; letter-spacing: -0.5px; }
  .header span { font-size: 16px; color: #8A8A8E; }
</style>
</head>
```

---

## Pattern: Accent Card

```html
<div style="
  background: #fff;
  border: 1px solid #E5E5EA;
  border-top: 3px solid #00897B;   /* swap colour per domain */
  border-radius: 14px;
  padding: 20px 24px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.05);
">
  <div style="font-size:9px;font-weight:700;letter-spacing:1.3px;text-transform:uppercase;color:#AEAEB2;margin-bottom:8px;">
    LABEL TAG
  </div>
  <div style="font-size:16px;font-weight:700;color:#1A1A1A;margin-bottom:4px;">Title</div>
  <div style="font-size:12.5px;color:#636366;line-height:1.5;">Description text</div>
</div>
```

---

## Pattern: Timeline Roadmap

```html
<div style="position:relative;display:flex;justify-content:space-between;align-items:flex-start;">
  <!-- spine line -->
  <div style="position:absolute;top:30px;left:80px;right:80px;height:2px;background:#E5E5EA;z-index:0;"></div>

  <!-- each phase -->
  <div style="flex:1;display:flex;flex-direction:column;align-items:center;position:relative;z-index:1;">
    <!-- dot -->
    <div style="width:60px;height:60px;border-radius:50%;background:#00897B;
                display:flex;align-items:center;justify-content:center;
                font-size:18px;font-weight:700;color:#fff;
                margin-bottom:20px;box-shadow:0 2px 12px rgba(0,0,0,0.12);">
      01
    </div>
    <!-- card -->
    <div style="background:#fff;border:1px solid #E5E5EA;border-top:3px solid #00897B;
                border-radius:16px;padding:22px 20px;width:260px;
                box-shadow:0 2px 8px rgba(0,0,0,0.06);">
      <div style="font-size:9px;font-weight:700;letter-spacing:1.3px;text-transform:uppercase;color:#00897B;margin-bottom:8px;">Phase 1</div>
      <div style="font-size:18px;font-weight:700;margin-bottom:12px;">Fitness</div>
      <!-- bullets -->
    </div>
  </div>
  <!-- repeat for each phase -->
</div>
```

---

## Pattern: Two-Engine Architecture

```html
<div style="display:flex;gap:40px;padding:36px 60px;height:880px;">
  <!-- Engine 1 -->
  <div style="flex:1;display:flex;flex-direction:column;">
    <div style="font-size:10px;font-weight:700;letter-spacing:1.4px;text-transform:uppercase;color:#00897B;margin-bottom:6px;">Engine 1</div>
    <div style="font-size:24px;font-weight:700;margin-bottom:20px;">Platform Name</div>
    <!-- step cards with ↓ arrows between -->
  </div>

  <!-- vertical divider -->
  <div style="width:1px;background:#E5E5EA;align-self:stretch;"></div>

  <!-- Engine 2 -->
  <div style="flex:1;display:flex;flex-direction:column;">
    <!-- same pattern -->
  </div>
</div>
```

---

## Colour Assignments (TIMBR convention)
| Domain | Accent | Background |
|---|---|---|
| Fitness / Platform | `#00897B` | `#E0F2F0` |
| App / Product | `#1976D2` | `#E8F1FB` |
| BlackWire / Media | `#F57C00` | `#FFF3E0` |
| Marketing | `#7B1FA2` | `#EDE8FD` |
| Trainers | `#C62828` | `#FAE8E8` |
| Healthcare | `#C62828` | `#FAE8E8` |
| Events | `#2E7D32` | `#E5F5EB` |
| Ops / Infra | `#455A64` | `#ECEFF1` |

---

## Playwright Render Script (reusable)

```python
from playwright.sync_api import sync_playwright

charts = [
    ('/tmp/chart1.html', '/tmp/chart1.png'),
    ('/tmp/chart2.html', '/tmp/chart2.png'),
]

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    for html_path, png_path in charts:
        page = browser.new_page(viewport={"width": 1600, "height": 1000})
        page.goto(f"file://{html_path}")
        page.wait_for_timeout(500)   # let CSS settle
        page.screenshot(path=png_path, full_page=False)
        print(f"Rendered: {png_path}")
    browser.close()
```

Run via: `~/.hermes/hermes-agent/venv/bin/python3 /tmp/render.py`
