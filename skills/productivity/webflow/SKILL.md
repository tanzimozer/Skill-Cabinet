---
name: webflow
description: "Webflow REST API v2: manage sites, CMS collections, pages, assets, and publishing via Python urllib."
tags: [webflow, cms, website, api, publishing]
triggers:
  - User wants to update Webflow site content programmatically
  - User asks Friday to manage their Webflow site
  - User wants to add/edit/delete CMS collection items (magazines, plans, blog posts)
  - User wants to publish or deploy a Webflow site via API
  - User wants to audit or read Webflow site structure
---

## Critical Limitation: Visual Editor Has No API

**Webflow's visual designer is GUI-only.** You cannot programmatically:
- Build layouts (sections, containers, grids)
- Style components (colors, typography, spacing)
- Add interactions or animations
- Drag-drop elements or configure responsive breakpoints

The REST API **only** covers:
- CMS content (create/update/delete collection items)
- Publishing (push changes live)
- Pages (SEO metadata, not layout)
- Assets (upload images/files)

**When user asks to "build a Webflow site":**
1. **Clarify scope** — Do they want CMS content population (API can do) or visual design (API cannot)?
2. **If design is needed** — Offer alternatives:
   - Build in code (HTML/CSS/JS) and deploy elsewhere (Netlify, Vercel, GitHub Pages)
   - Provide step-by-step guide for them to execute manually in Webflow Designer
   - Hire a Webflow specialist to execute under their account

See `creative/popular-web-designs/references/design-analysis-workflow.md` for the full pattern
of replicating a site's design via code when the platform has no design API.

# Webflow API v2

## Auth Setup

1. Go to: webflow.com → Profile icon → Account Settings → Integrations → API Access
2. Generate a new token
3. Enable ALL these scopes or you'll get 403:
   - Sites — Read & Write
   - CMS — Read & Write
   - Pages — Read & Write
   - Assets — Read & Write
   - Publishing — Read & Write

**Token format:** starts with `ws-`

## API Base

```
https://api.webflow.com/v2
```

All requests require:
```
Authorization: Bearer ws-YOUR_TOKEN
Accept: application/json
Content-Type: application/json  # for POST/PATCH
```

## Python Helper (urllib — no extra libs needed)

```python
import urllib.request, json

TOKEN = "ws-your_token_here"

def webflow(method, path, data=None):
    url = f"https://api.webflow.com/v2{path}"
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Accept": "application/json"
    }
    if data:
        headers["Content-Type"] = "application/json"
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, data=body, method=method, headers=headers)
    r = urllib.request.urlopen(req, timeout=15)
    return json.loads(r.read())
```

## Common Operations

### List all sites
```python
sites = webflow("GET", "/sites")
for s in sites["sites"]:
    print(s["id"], s["displayName"], s["customDomains"])
```

### Get site details
```python
site = webflow("GET", f"/sites/{site_id}")
```

### List pages
```python
pages = webflow("GET", f"/sites/{site_id}/pages")
```

### List CMS collections
```python
collections = webflow("GET", f"/sites/{site_id}/collections")
for c in collections["collections"]:
    print(c["id"], c["displayName"], c["slug"])
```

### Get collection items
```python
items = webflow("GET", f"/collections/{collection_id}/items")
```

### Create a CMS item
```python
item = webflow("POST", f"/collections/{collection_id}/items", {
    "fieldData": {
        "name": "Magazine: Blair",
        "slug": "magazine-blair",
        "description": "Blair's transformation story...",
        # add other fields per collection schema
    }
})
```

### Update a CMS item
```python
webflow("PATCH", f"/collections/{collection_id}/items/{item_id}", {
    "fieldData": {
        "name": "Updated Name"
    }
})
```

### Delete a CMS item
```python
webflow("DELETE", f"/collections/{collection_id}/items/{item_id}")
```

### Publish site
```python
webflow("POST", f"/sites/{site_id}/publish", {
    "customDomains": ["timbr.fit"],
    "publishToWebflowSubdomain": False
})
```

### List assets
```python
assets = webflow("GET", f"/sites/{site_id}/assets")
```

## Token Types — Critical Distinction

Webflow has TWO token types. Use the wrong one and you'll get 403 on everything:

- **Workspace token** (`ws-...`)  — generated from Account Settings → Integrations → API Access. Only covers Cloud Apps, Code Components, Workspace Activity. CANNOT manage site content or CMS.
- **Site token** — generated from inside the Site Settings → API Access tab. This is what you need for CMS, pages, publishing, assets.

**Always use a site-level token for content management.**

To get the site token:
1. Go to webflow.com/dashboard
2. Click into your site
3. Site Settings (gear icon) → API Access tab
4. Generate token there — you'll see CMS, Pages, Publishing scopes

## Draft vs Live Endpoints

Webflow has two modes for CMS writes:

- `/collections/{id}/items` — writes to **draft** (staging). Use this when site is not yet published.
- `/collections/{id}/items/live` — writes directly to **live**. Requires site to already be published. Returns 409 Conflict if site has never been published.

**Pattern:** Use draft endpoints while building. Publish the site once in the designer, then switch to `/live` endpoints for ongoing content updates.

## TIMBR-Specific Setup

- Token: f6168ddabe107ed1a5cbe23a092b659be481c0652cfe65b5008d9c8346ea75ec (site-level)
- Site ID: 69ffdbc71bb5473aa1258e73 (TIMBR-1)
- Template: Kayo Studio (dark, editorial, portfolio style)
- CMS Collections: Works (magazines + training plans), Blog Posts, Products, Categories
- Work Categories: Magazines, Training, Nutrition
- Blog Categories: Fitness, Seattle, Athletes
- Domain: timbr.fit (migrating from Wix)
- Stack: Webflow + Stripe (payments) + Cal.com (booking)

## Inspect Collection Schema Before Writing

Always pull collection field schema before creating items — field slugs differ from display names:

```python
detail = webflow("GET", f"/collections/{collection_id}")
for field in detail.get('fields', []):
    print(f"  {field['displayName']} [{field['type']}] — slug: {field['slug']}")
```

Reference fields (type `Reference`) take an item ID string, not a name.
MultiReference fields take a list of IDs.

## Rename Existing Template Items Instead of Creating New

Templates come pre-loaded with placeholder categories (e.g. "Branding", "Design", "UI/UX").
Creating new ones with the same slug returns 409. Instead, PATCH the existing ones:

```python
webflow("PATCH", f"/collections/{cat_collection_id}/items/{existing_item_id}", {
    "fieldData": {"name": "Magazines", "slug": "magazines"}
})
```

Always GET existing items first to get their IDs before creating new ones.

## Page SEO Updates

Use PUT (not PATCH) on `/v2/pages/{pageId}` — PATCH returns errors on some Webflow plans:

```python
webflow("PUT", f"/pages/{page_id}", {
    "seo": {
        "title": "Page Title Here",
        "description": "Meta description here"
    }
})
```

Note: the pages endpoint is `/v2/pages/{pageId}` directly — NOT `/v2/sites/{siteId}/pages/{pageId}`.

## Parallel Content Population with delegate_task

For bulk content creation (blog posts, CMS items, copy writing), use `delegate_task` with 3 parallel agents (max_concurrent_children=3). Proven pattern for full site buildout:

- Agent 1: Write About page copy (brand story, philosophy, stats, CTA)
- Agent 2: Write Seattle page + FAQ (18 questions across 6 categories)
- Agent 3: Write 4 blog posts (300-400 words each, with excerpt + body)

Then in a single follow-up script, POST all blog posts to `/collections/{blog_id}/items`.

For SEO + setup docs in parallel:
- Agent 1: Homepage copy (hero, stats bar, services, pricing, CTA sections)
- Agent 2: Cal.com or integration setup guide (save to /home/hermes/timbr/)
- Agent 3: SEO meta titles + descriptions for all pages (apply via PUT /pages/{id})

Key: agents write copy, Friday loads it. Don't ask agents to call the API — they lack the token context. Always load results centrally after all agents complete.

## Ecommerce Products — API Blocked

Webflow blocks product creation via the REST API entirely. Products must be added manually:
- Webflow Designer → Ecommerce → Products → Import CSV
- Or manually via the Designer UI

Friday can generate a CSV with all product data (name, price, description, slug) ready to import. The import format is: Name, Description, SKU, Price, Category.

## Pitfalls

- **Ecommerce products** — cannot be created via API. Use CSV import in the Designer.
- **403 on first call** — using workspace token instead of site token. See Token Types section above.
- **409 Conflict on create** — either slug already exists (rename instead) or site not published yet (use draft endpoint `/items` not `/items/live`).
- **v1 vs v2** — always use v2 (`/v2/` prefix). v1 is deprecated.
- **CMS item fields** — field names in the API are the slug versions of display names. Always inspect schema first.
- **Publishing** — changes to CMS items don't go live until you call the publish endpoint OR publish from the designer.
- **Rate limits** — 60 requests/minute on standard plans. Add `time.sleep(1)` between bulk operations.
- **Site ID** — found in the Webflow dashboard URL or via `GET /sites`.
- **Page SEO** — use PUT not PATCH, and path is `/v2/pages/{id}` not nested under sites.
- **Template placeholder items** — always GET existing collection items before creating new ones. Rename with PATCH instead of creating fresh to avoid slug conflicts.
