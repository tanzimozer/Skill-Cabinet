# TIMBR Team Radar + Card Design (July 2026)

## Layout

- **Canvas**: 1400×820px, `background: #F1F4F8`, flexbox row, `padding: 36px`, `gap: 28px`
- **Left panel** (500px wide): white card, border-radius 20px, contains radar chart + legend
- **Right panel** (flex:1): three equal-height stacked cards with 18px gap

## Radar

- Library: Chart.js 4.4.0 via CDN (`chart.umd.min.js`)
- Type: `radar`, 8 axes: Fitness Domain, Product & Leadership, Data & Analytics, AI/ML, Backend Eng, Mobile/Frontend, Voice AI, Business
- Legend rendered in HTML (not Chart.js legend) — colour dots + name + role subtitle
- `animation: { duration: 0 }` for Playwright screenshot
- Grid: `#E8EBF0`, point labels 11px semi-bold `#4B5563`

### Scores (as of July 2026)
| Axis | Tanzim (blue #3B82F6) | Sagar (green #10B981) | Waseem (amber #F59E0B) |
|---|---|---|---|
| Fitness Domain | 10 | 7 | 5 |
| Product & Leadership | 9 | 6 | 5 |
| Data & Analytics | 8 | 7 | 4 |
| AI / ML | 5 | 5 | 9 |
| Backend Eng | 3 | 9 | 7 |
| Mobile / Frontend | 2 | 5 | 10 |
| Voice AI | 2 | 3 | 8 |
| Business | 9 | 5 | 4 |

## Cards (uniform template, vary only accent colour + content)

Each card:
- White background, `border-radius: 16px`, subtle box-shadow
- Top accent banner: `height: 5px`, full-width, `background: var(--accent)`
- Body: `padding: 16px 22px 14px`
- Header row: name (17px 800 weight) + role badge (pill, `background: var(--accent)`)
- Pedigree line: 11px, `#9AA3B2`
- Section label: 9px 800 weight, 1.1px tracking, uppercase, `#B8BEC9`
- Credentials row: flex-wrap tags — primary cred in accent-soft bg, others in `#F0F3F7`
- Domains row: accent-tinted tags, `margin-top: auto` to push to bottom
- Footer: `border-top: 1px solid #F0F3F7`, `background: #FAFBFC`, 10.5px `#9AA3B2`

### Team Data
**Tanzim** `--accent: #3B82F6` | `--accent-soft: #EFF6FF` | `--accent-border: #BFDBFE`
- Role: Founder & CEO
- Pedigree: TIMBR · Google Data Analytics Certified · 50% Equity
- Credentials: Google Data Analytics (primary), Power BI, Tableau, SQL, n8n/MCP Automation, Python
- Domains: Fitness & Product, Analytics & DB, AI Automation, Business Strategy
- Footer: Top 10 District Producer · **255 → 87th nationally**

**Sagar** `--accent: #10B981` | `--accent-soft: #ECFDF5` | `--accent-border: #A7F3D0`
- Role: CTO & Co-Founder
- Pedigree: Amazon SDE II · L5 · Active · 50% Equity
- Credentials: Amazon L5 SDE II (primary), Distributed Systems, Backend Engineering, Data Engineering, Cloud Infrastructure
- Domains: Backend Eng, Cloud/Infra, Data Systems, Product
- Footer: Amazon SDE · **Active · L5** · Engineering Lead

**Waseem** `--accent: #F59E0B` | `--accent-soft: #FFFBEB` | `--accent-border: #FDE68A`
- Role: AI Engineer · Advisor
- Pedigree: ex-Meta Staff SWE → Nextdoor → Tribe AI · Sweat Equity
- Credentials: ex-Meta Staff SWE (primary), LLM/AI Systems, Voice AI, Mobile Engineering, Staff-Scale Systems
- Domains: Mobile, AI/ML, Voice AI, Infra at Scale
- Footer: ex-Meta Staff → **Tribe AI** · Top-5% engineering pedigree

## Scoping Rule

Tanzim explicitly said: **"I don't want the radar to be replaced, only our cards."**
When given a partial redesign instruction, touch only the specified element. Radar stays — cards rebuilt. Do not rebuild the whole composition.

## Playwright Render

```python
page = browser.new_page(viewport={"width": 1400, "height": 820})
page.goto("file:///home/hermes/timbr_team.html", wait_until="networkidle")
page.wait_for_timeout(1200)  # Chart.js needs time
page.screenshot(path="/home/hermes/timbr_team.png", full_page=False)
```

Verify Chart.js loaded: `page.evaluate("typeof Chart !== 'undefined'")`
