---
name: trello
description: "Trello API via Python urllib: create boards, lists, cards from documents or task lists."
tags: [trello, project-management, boards, cards, api]
triggers:
  - User wants to create a Trello board
  - User shares a checklist, PDF, or task list and wants it in Trello
  - User wants to add/move/update Trello cards programmatically
  - User asks to connect Friday to Trello
  - User wants to add, remove, or correct a board member by email
---

# Trello API Integration

## Auth Setup

Requires API Key + Token. Guide user to:
1. https://trello.com/power-ups/admin → New Power-Up (name it "Friday")
2. API key tab → Generate a new API key
3. Click the "Token" link on that page to generate a token

**Credentials format:**
- API Key: 32-char hex string
- Token: starts with `ATTA...`

Save to memory once obtained.

## API Base

```
https://api.trello.com/1/
```

All requests require `?key=API_KEY&token=TOKEN` appended.

## Python Helper (use urllib — no requests lib needed)

```python
import urllib.request, json

API_KEY = "your_key"
TOKEN = "your_token"

def trello(method, path, data=None):
    base = f"https://api.trello.com/1{path}"
    sep = "&" if "?" in base else "?"
    url = f"{base}{sep}key={API_KEY}&token={TOKEN}"
    if method == "GET":
        r = urllib.request.urlopen(url, timeout=15)
    else:
        body = json.dumps(data).encode() if data else b""
        req = urllib.request.Request(url, data=body, method=method,
                                     headers={"Content-Type": "application/json"})
        r = urllib.request.urlopen(req, timeout=15)
    return json.loads(r.read())
```

## Common Operations

### Create a board
```python
board = trello("POST", "/boards/", {"name": "My Board", "defaultLists": False})
bid = board["id"]
url = board["shortUrl"]  # e.g. https://trello.com/b/uHZYfkAt
```

### Create a list
```python
lst = trello("POST", "/lists", {"name": "To Do", "idBoard": bid})
lid = lst["id"]
```

### Create a card
```python
card = trello("POST", "/cards", {
    "name": "Card title",
    "idList": lid,
    "desc": "Optional description with URL and steps"
})
```

### Get boards for current user
```python
boards = trello("GET", "/members/me/boards?fields=name,shortUrl")
```

### Get lists on a board
```python
lists = trello("GET", f"/boards/{bid}/lists")
```

### Move a card to another list
```python
trello("PUT", f"/cards/{card_id}", {"idList": new_list_id})
```

### Archive a card
```python
trello("PUT", f"/cards/{card_id}", {"closed": True})
```

## Member Management

### Add member by email (Trello sends invite if no account)
```python
import urllib.parse
email = "user@example.com"
path = f"/boards/{bid}/members?email={urllib.parse.quote(email)}&type=normal"
result = trello("PUT", path, {"fullName": "Display Name"})
# result["members"] contains the updated member list
# member["confirmed"] = False means invite sent; True means existing account added instantly
# member["memberType"] = "ghost" means pending invite
```

### Remove a member from a board
```python
# Need their member ID — get it from the members list first
members = trello("GET", f"/boards/{bid}/members")
member_id = next(m["id"] for m in members if m["username"] == "target_username")
trello("DELETE", f"/boards/{bid}/members/{member_id}")
```

### Correct a wrong email (remove + re-add pattern)
```python
# 1. Get current members to find the wrong one
members = trello("GET", f"/boards/{bid}/members")
wrong_id = next(m["id"] for m in members if m["fullName"] == "wrong name")
# 2. Remove
trello("DELETE", f"/boards/{bid}/members/{wrong_id}")
# 3. Re-add with correct email
path = f"/boards/{bid}/members?email={urllib.parse.quote(correct_email)}&type=normal"
trello("PUT", path, {"fullName": "Display Name"})
```

## PDF/Document → Trello Board Pattern

1. Extract text from PDF (`pdfplumber` works well)
2. Parse into sections/tasks
3. Create board with `defaultLists: False`
4. Create lists for each phase/category
5. Create cards with name + description (include URLs + steps in desc)

```python
# Write script to /home/hermes/trello_build.py and run it
# Don't inline long scripts in terminal — they get cut off
```

## Label Management

### Get board labels
```python
labels = trello("GET", f"/boards/{bid}/labels")
# Returns list of {id, color, name} — colors: green, yellow, orange, red, purple, blue, black, sky, lime, pink
green = next(l for l in labels if l["color"] == "green")
```

### Add a label to a card
```python
trello("POST", f"/cards/{card_id}/idLabels", {"value": label_id})
```

### Remove a label from a card
```python
trello("DELETE", f"/cards/{card_id}/idLabels/{label_id}")
```

### Create a new label on a board
```python
label = trello("POST", f"/boards/{bid}/labels", {"name": "Verified", "color": "green"})
```

## Audit → Trello Sync Pattern

When cross-checking a live system (website, app) against a Trello board and syncing results back:

1. Fetch the target list's cards: `trello("GET", f"/lists/{list_id}/cards")`
2. Run the audit externally (e.g. Playwright page checks)
3. For passing items → mark dueComplete (the green circle checkmark — NOT just a label)
4. For false positives (audit wrong, work actually done) → archive card: `trello("PUT", f"/cards/{card_id}", {"closed": True})`
5. For new real issues not yet tracked → create cards in To-Do (not In-Progress) with detailed desc
6. Match cards by substring of name (`.lower() in card["name"].lower()`) — exact match is fragile

```python
# Mark card complete (green circle checkmark)
trello("PUT", f"/cards/{card_id}", {"dueComplete": True})

# Archive a misclassified card
trello("PUT", f"/cards/{card_id}", {"closed": True})

# Bulk-mark all cards in a list as complete
cards = trello("GET", f"/lists/{list_id}/cards")
for card in cards:
    trello("PUT", f"/cards/{card['id']}", {"dueComplete": True})

# Add green label (cosmetic only — separate from dueComplete)
trello("POST", f"/cards/{card_id}/idLabels", {"value": green_label_id})
```

### Card description quality — make it executable
When creating audit-result cards, write descriptions detailed enough that the assignee never needs to ask questions:
- What the issue is (with exact observed value vs expected value)
- Exact navigation path to the fix location (dashboard URL if possible)
- Numbered step-by-step fix instructions
- Tip or context if the fix is non-obvious
- How to verify it's fixed (test URL or verification step)
- Time estimate

### Cards for non-technical team members (e.g. Towsif)
When cards will be executed by a non-technical person, use this format for every card:

```
WHAT TO DO:
<one sentence summary>

STEPS:
1. Go to <exact URL>
2. Click <exact label>
3. <do this>
4. Verify: <how to confirm it worked>

LINKS:
<label>: <direct URL for every place they need to go>

---
ACCESS — <SERVICE NAME>
Email: <login email>
Password: <password>
Login URL: <direct login link>
```

Key rules:
- Every card has its own ACCESS block — don't assume they have it memorized
- Every link is a direct deep link, not a homepage (e.g. webflow.com/design/timbr-1 not webflow.com)
- Steps are numbered, imperative, and specific — "Click Ecommerce" not "go to ecommerce"
- If an action has a prerequisite (e.g. "do this BEFORE X"), call it out explicitly in caps
- Add time estimate if known

### Wix site auditing — critical pitfall
Wix sites use the Thunderbolt JS framework — static HTTP requests return near-empty HTML.
**Always use Playwright with full JS rendering** for Wix audits:
```python
from playwright.sync_api import sync_playwright
import time
p = sync_playwright().start()
b = p.chromium.launch(executable_path='/snap/bin/chromium', args=['--no-sandbox','--disable-dev-shm-usage'])
page = b.new_page(viewport={'width':1280,'height':800})
page.goto(url, wait_until='domcontentloaded', timeout=35000)
time.sleep(7)  # Wix needs extra time to hydrate
text = page.inner_text('body')
```

Known Wix patterns that static scans miss:
- Lightbox popups (e.g. Refund Policy as onClick popup — no URL, but works correctly)
- JS-rendered product grids, booking widgets, contact forms
- Branded 404 pages (rendered by JS, not in static HTML)
- OG tags — readable via `page.evaluate("Array.from(document.querySelectorAll('meta[property]'))...")`

### Dedup check before creating cards
Always check all lists (not just one) before creating new cards — duplicates accumulate across In-Progress/To-Do/Backlog:
```python
all_lists = trello("GET", f"/boards/{bid}/lists")
for l in all_lists:
    cards = trello("GET", f"/lists/{l['id']}/cards?fields=name,id")
    matches = [c for c in cards if "keyword" in c["name"].lower()]
```

## Wix SEO — Not API Accessible

Wix does NOT expose og:title, og:description, or other SEO/social share metadata via its REST API. These fields are set inside the Wix Editor/Dashboard only (SEO Tools → Social Share). No programmatic workaround exists — must be done manually.

What IS accessible via Wix API: store products, bookings, contacts, orders, CMS collections.

## Project Tracking Workflow Pattern

When managing a project board (e.g. Go-Live, Webflow migration):
- Create a Done column pre-populated with already-completed work — gives instant momentum visibility
- Add a comment to each card when moving it to Done explaining what was completed and by whom
- Cards Friday completes autonomously should say "Completed by Friday:" in the comment
- Use card descriptions as execution guides: what was done, how to verify, who it's assigned to

```python
# Move card to Done + leave a comment
trello("PUT", f"/cards/{card_id}", {"idList": done_list_id})
trello("POST", f"/cards/{card_id}/actions/comments", {
    "text": "Completed by Friday:\n<what was done and how to verify>"
})
```

## TIMBR Boards
- Go-Live: https://trello.com/b/uHZYfkAt (lists: Backlog, To-Do, In-Progress, Towsif Done, Friday Done)
- SITE 3: https://trello.com/b/U7StsSvp (lists: Backlog, To-Do, In-Progress, In-Review, Done) — Wix rebuild tasks

## Board Triage by Time Budget

When a user says "organize the board for X hours of work" or "what can be done in X hours":

1. Read all cards from the active list (To-Do or In-Progress)
2. Estimate effort per card from the description (look for time hints, step count, complexity)
3. Keep cards that fit within the time budget in To-Do — prioritize quick wins + blockers first
4. Create a Backlog list if one doesn't exist (position it after To-Do)
5. Move all remaining cards to Backlog in one script

```python
# Create Backlog at end of board
backlog = trello("POST", "/lists", {"name": "Backlog", "idBoard": bid, "pos": 32768})
backlog_id = backlog["id"]

KEEP_IN_TODO = {"card_id_1", "card_id_2"}  # IDs of cards that fit the time budget

cards = trello("GET", f"/lists/{todo_list_id}/cards?fields=name,id")
for card in cards:
    if card["id"] not in KEEP_IN_TODO:
        trello("PUT", f"/cards/{card['id']}", {"idList": backlog_id})
```

Typical time estimates (Webflow/CMS tasks):
- Publish CMS items: 20–30 min
- Delete template placeholders: 15–20 min
- CSV product import: 45–60 min
- QA full site review: 60–90 min
- Nav/footer cleanup: 30–45 min
- Full design section build: 2–4 hrs
- Domain cutover: 30 min (but high risk — defer to last)

## Summarize Board as Work Brief

When asked to brief a team member on what they should execute:
1. Read all To-Do cards + descriptions
2. Group by theme (quick admin tasks first, design/build tasks after)
3. Include time estimate per task and total
4. Reference Trello board link at the end
5. Write in plain language — numbered list, no jargon, each item has what/where/how

Adjust the brief if working hours are known — e.g. if team member is mid-shift, subtract elapsed time and lunch breaks from available window before assigning tasks.

## Bulk Card Enhancement for Delegation

When preparing a board for a non-technical team member to execute:

### Pattern
1. Fetch all cards from To-Do list
2. Categorize: which cards require the owner's expertise (design, decisions) vs which can be delegated (execution, admin)
3. For each delegatable card, update with:
   - Time estimate in description header
   - ACCESS block with login credentials
   - Step-by-step instructions
   - Programmatic checklist via API

```python
# Create checklist on a card
checklist = trello("POST", f"/cards/{card_id}/checklists", {"name": "Steps"})

# Add checklist items
for item in ["Step 1: Do X", "Step 2: Do Y", "Verify: Check Z"]:
    trello("POST", f"/checklists/{checklist['id']}/checkItems", {"name": item})
```

### Description template for execution cards
```
⏱️ TIME: X-Y minutes

WHAT TO DO:
<one sentence summary>

---
ACCESS — <SERVICE NAME>
Login: <URL>
Account: <email>

---
<any context or links needed>
```

### Categorization keywords
Design/owner cards (keep separate): "page design", "new section", "visual qa", "mobile responsiveness", "homepage design"
Execution cards (delegate): fixes, SEO, settings, uploads, polish tasks

### Pitfalls
- Always include ACCESS block per card — don't assume they remember credentials
- Time estimates help them plan their shift
- Checklist items should be imperative and specific
- Last item should always be a verification step

## Board Workspace Management

### Get all workspaces (organizations)
```python
orgs = trello("GET", "/members/me/organizations")
for org in orgs:
    print(f"{org['displayName']} (id: {org['id']})")
```

### Move a board to a different workspace
```python
trello("PUT", f"/boards/{board_id}", {"idOrganization": workspace_id})
```

### Delete a board (archive then delete)
```python
# First archive (close) the board
trello("PUT", f"/boards/{board_id}", {"closed": True})
# Then permanently delete
trello("DELETE", f"/boards/{board_id}")
```

### Get all boards with their workspace
```python
boards = trello("GET", "/members/me/boards?fields=name,shortUrl,idOrganization,closed")
for b in boards:
    if not b.get('closed'):
        print(f"{b['name']} - Org: {b.get('idOrganization', 'Personal')}")
```

## Sprint Board Pattern (Time-Boxed Projects)

When creating a board for a time-boxed project sprint (e.g. "7-day magazine launch", "2-week MVP build"):

### Structure
- **Phase-based lists with timeline labels** — e.g. "📝 CONTENT (Days 1-2)", "🎨 DESIGN (Days 3-4)", "🚀 LAUNCH (Day 7)", "✅ DONE"
- **Cards represent deliverables, not tasks** — each card = one shippable output (e.g. "Blair Magazine - Design & Layout")
- **Rich card descriptions** with Goal, Deliverable, Owner, Timeline, Dependencies sections
- **Programmatic checklists** for step-by-step execution on every card

### Card Description Template for Sprint Deliverables
```
**Goal:** <what we're achieving>

**Deliverable:** <concrete output>

**Owner:** <who's responsible>
**Timeline:** <when it's due>
**Dependencies:** <what must be done first>

<any credentials, links, or context>
```

### Implementation
```python
# Create board
board = trello("POST", "/boards", {
    "name": "7-Day Magazine Sprint (Blair, Shumon, Taylor)",
    "defaultLists": False
})
board_id = board['id']

# Create phase-based lists with emoji + timeline
lists = {}
for list_name in [
    "📝 CONTENT EXTRACTION (Days 1-2)",
    "🎨 DESIGN & LAYOUT (Days 3-4)",
    "🔧 WIX INTEGRATION (Days 5-6)",
    "🚀 LAUNCH PREP (Day 7)",
    "✅ DONE"
]:
    lst = trello("POST", "/lists", {"name": list_name, "idBoard": board_id})
    lists[list_name] = lst['id']

# Create cards with rich descriptions and checklists
for magazine in ['Blair', 'Shumon', 'Taylor']:
    card = trello("POST", "/cards", {
        "name": f"{magazine} Magazine - Content Extraction",
        "idList": lists["📝 CONTENT EXTRACTION (Days 1-2)"],
        "desc": f"""**Goal:** Extract all persona content for {magazine}'s magazine

**Deliverable:** Complete Q&A responses ready for editorial writing

**Owner:** TBD
**Timeline:** Days 1-2"""
    })
    
    # Add execution checklist
    checklist = trello("POST", f"/cards/{card['id']}/checklists", {"name": "Content Extraction Steps"})
    
    for item in [
        "Send persona question bank",
        "Collect Round 1 answers (basics, training, nutrition)",
        "Collect Round 2 answers (lifestyle, preferences, routines)",
        "Review answers for completeness",
        "Flag missing/unclear responses",
        "Get clarification on gaps",
        "Mark content extraction COMPLETE"
    ]:
        trello("POST", f"/checklists/{checklist['id']}/checkItems", {"name": item})
```

### When to Use This Pattern
- User says "create a sprint board", "7-day project", "time-boxed build"
- Multiple deliverables with clear phase dependencies (content → design → integration → launch)
- Delegation-heavy projects where cards need to be self-documenting
- Cross-functional work where non-technical team members execute cards

### Phase List Naming Convention
- Use emoji for visual scanning (📝 🎨 🔧 🚀 ✅)
- Include timeline labels in list name — e.g. "(Days 1-2)", "(Day 7)"
- Order lists chronologically left-to-right (Trello default board view)
- Always include a DONE list at the end

### Launch-Critical vs Per-Deliverable Cards
Separate cards that apply to **all deliverables** (e.g. "Payment Gateway Verification", "Final QA") from cards that are **per-deliverable** (e.g. "Blair Magazine - Design"). Launch-critical cards go in the final phase list; per-deliverable cards go in their respective phase lists.

## Design Replication → Trello Workflow

When user says "scan [external site], break into Trello cards, then build it in [platform]":

**See `references/design-scan-analysis.md` for full Ultrahuman blog case study (May 2026).**

### Phase 1: Design Analysis
```python
# 1. Screenshot the target site
from playwright.sync_api import sync_playwright
import time

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={'width': 1920, 'height': 1080})
    page.goto(target_url, wait_until='networkidle', timeout=60000)
    time.sleep(3)
    page.screenshot(path='/tmp/target_fullpage.png', full_page=True)
    page.screenshot(path='/tmp/target_fold.png')
    browser.close()

# 2. Extract design structure programmatically
from PIL import Image
img = Image.open('/tmp/target_fullpage.png')
sections_estimate = img.height // 600  # Rough section count

# Sample colors from multiple Y positions
colors = []
for y in [100, 500, 1000, 2000]:
    if y < img.height:
        pixel = img.getpixel((img.width // 2, y))
        colors.append({"y": y, "rgb": pixel})

# 3. Parse HTML for component patterns
from bs4 import BeautifulSoup
soup = BeautifulSoup(html_content, 'html.parser')
cards = soup.find_all(class_=lambda x: x and ('card' in x.lower() or 'post' in x.lower()))
nav_items = soup.find('nav').find_all('a') if soup.find('nav') else []
```

### Phase 2: Design Breakdown Document
Create a structured JSON analysis:
```json
{
  "layout": {"viewport": 1920, "max_width": "1200-1400px"},
  "header": {"height": "80-100px", "components": ["Logo", "Nav", "CTA"]},
  "hero": {"height": "500-600px", "alignment": "left"},
  "content_grid": {"columns": 3, "gap": "20-30px", "card_style": "minimal dark"},
  "typography": {"h1": "48-64px", "h2": "32-40px", "body": "16-18px"},
  "colors": {"primary_bg": "#000000", "accent": "#dd9949", "text": "#ffffff"},
  "spacing": {"section_padding": "80-120px", "container_padding": "20-40px"}
}
```

### Phase 3: Trello Board Generation
Structure the build into **phase-based lists**:
- 🎨 Design Foundation (style guide, variables, global classes)
- 🧱 Structure & Layout (header, footer, containers)
- 🏠 Page Sections (hero, content grids, specific sections)
- 🎨 Components (buttons, cards, images)
- 📝 CMS Setup (collections, templates) — if applicable
- 🔧 Interactions (animations, hovers, mobile menu)
- 📱 Responsive & Polish (mobile/tablet optimization, performance)
- 🚀 Publishing (QA, domain setup)
- ✅ Done

**Card structure per task:**
```python
card_desc = f"""**Specs:**
- Height/Width: {measurements}
- Background: {color/gradient}
- Layout: {flexbox/grid details}

**Components:**
- {list of child elements}

**Implementation:**
{step-by-step instructions}"""

# Add programmatic checklist
checklist = trello("POST", f"/cards/{card_id}/checklists", {"name": "Build Steps"})
for step in build_steps:
    trello("POST", f"/checklists/{checklist['id']}/checkItems", {"name": step})
```

### Phase 4: Reference Materials
Save analysis artifacts for execution phase:
- `/tmp/target_fullpage.png` — full page screenshot
- `/tmp/target_fold.png` — above-fold reference
- `/tmp/design_analysis.json` — structured breakdown
- Include these as Trello card attachments or save to shared location

### When to Use This Pattern
- User provides external site as design reference (e.g. "replicate blog.ultrahuman.com")
- User wants task breakdown BEFORE starting build
- Platform is Webflow, Framer, or any visual builder (not applicable for pure code)
- User will execute cards themselves OR delegate to team

### Pitfall
**Don't just list generic tasks** — every card needs measurements, color codes, exact component specs from the analysis. "Build header" is useless; "Build header (80px height, dark bg #0a0a0a, flex layout: logo left / nav right, sticky position)" is actionable.

## Board Merge / Archive Pattern

When merging boards (moving cards from board A → board B, then archiving A):

**CRITICAL: Move cards BEFORE closing the board.** Trello returns HTTP 409 "Closed boards cannot be edited" the moment `closed: True` is set — even if you reopen it, there's a race/cache window where subsequent requests still 409. Order matters:

```python
# CORRECT order
# 1. Move/archive all cards first
for card in source_cards:
    trello("PUT", f"/cards/{card['id']}", {"idList": target_list_id, "idBoard": target_board_id})

# 2. THEN close the source board
trello("PUT", f"/boards/{source_board_id}", {"closed": True})
```

If you hit 409 mid-run (source board was accidentally closed early), reopen it with `{"closed": False}`, wait 2 seconds, then retry. If cards are genuinely unreachable, recreate them directly on the target board — they're typically just title + optional desc, so no data loss.

**Dedup logic for merges:** Don't assume card names are unique across boards. Before moving, fetch all open cards from ALL lists on the target board and check by name. Skip creation if already present.

```python
existing_names = set()
for lid in target_board_list_ids:
    cards = trello("GET", f"/lists/{lid}/cards?fields=name")
    existing_names.update(c['name'] for c in cards)

# Only create/move if not already there
if card_name not in existing_names:
    trello("POST", "/cards", {"name": card_name, "idList": target_list_id})
```

## Pitfalls
- **Tokens expire** — If API returns "invalid key" or 401, the embedded credentials are stale. Ask user to generate fresh ones at https://trello.com/power-ups/admin (don't retry with expired tokens). Token expiry is a recurring issue across sessions.
- **Trello API times out from inline terminal heredocs** — write script to a file, run with `python3 /path/to/script.py` instead
- **`defaultLists: False`** — always pass this when creating boards or Trello auto-creates To Do / Doing / Done lists you don't want
- **curl times out** — use Python urllib instead, curl hangs on this machine
- **Token vs API Key** — Key is for the app, Token authorizes on behalf of the user. Both required on every request.
- **Board URL** — `board["shortUrl"]` gives the sharable link (e.g. `https://trello.com/b/XXXXXXXX`)
- **Sprint boards need rich card descriptions** — don't create bare cards with just a title. Every card should have Goal, Deliverable, Owner, Timeline, and a checklist. Delegation-ready from the start.
- **Design replication cards must include exact specs** — measurements, colors, layout details from the analysis phase. Generic task names without context are not actionable.

## Tanzim's Credentials
- API Key: <TRELLO_KEY — see ~/.hermes/.trello_credentials>
- Token: <TRELLO_TOKEN — see ~/.hermes/.trello_credentials>
- Power-Up name: Friday
