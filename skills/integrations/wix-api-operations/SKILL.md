---
name: wix-api-operations
description: "Wix REST API operations for TIMBR site — product catalog, blog posts, draft posts, site identity, and what is/isn't possible via API vs Wix Classic Editor."
version: 1.0.0
tags: [wix, timbr, api, ecommerce, blog, products, catalog]
related_skills: [timbr-magazine-production, magazine-production-system]
---

# Wix API Operations (TIMBR)

Direct REST API access to the TIMBR Wix site. Credentials live at `~/.hermes/.wix_credentials.json`.

## Credentials & Site

```python
import json, requests

creds = json.load(open('/home/hermes/.hermes/.wix_credentials.json'))
API_KEY = creds['api_key']       # IST.eyJ... long token
SITE_ID = creds['site_id']       # ab465896-e5c3-4f5d-bc9d-7f495a6d6be1
LIVE_URL = 'https://timbrworkspace.wixsite.com/my-site-25'
EDITOR_URL = 'https://editor.wix.com/html/editor/web/renderer/edit/ab465896-e5c3-4f5d-bc9d-7f495a6d6be1'

headers = {
    'Authorization': API_KEY,
    'wix-site-id': SITE_ID,
    'Content-Type': 'application/json'
}
```

## Hard API Boundary — What Can / Cannot Be Done

### ✅ Fully API-accessible
- Product catalog: create, update, hide/show, pricing, descriptions, media, SKU, collections
- Blog posts: query published posts, update metadata (tags, SEO, excerpts)
- Draft posts: query, create, update tags/SEO (NOT rich content body — see pitfall)
- Site identity: `siteDisplayName`, `businessName`, `description`
- Collections: create, rename, slug update
- `additionalInfoSections` on products
- Hiding/showing products (`visible` field)

### ❌ NOT accessible via Wix Catalog V1 API (must use Editor UI)
- **Converting a product from Physical → Digital** — the API simply ignores the `productType` field on PATCH; the product stays Physical
- Attaching a digital file to a product (can only do this after the Physical→Digital toggle is done in the UI)
- Page content (Homepage, About, Shop, Contact, Legal pages)
- Nav and footer copy
- Rich content body of blog posts/drafts — the `richContent.nodes` structure is read-only via the draft-posts API

### ⚠️ Workaround: Physical→Digital conversion
Must be done in Wix Dashboard UI:
1. Dashboard → Catalog → Products → open product
2. Change Product Type to Digital/File
3. Save
4. Then Friday can attach the PDF via API PATCH with `digitalFile` field

## Querying Products

```python
# Published/visible products only
r = requests.post('https://www.wixapis.com/stores/v1/products/query',
    headers=headers,
    json={"query": {"paging": {"limit": 50}}})

# Include hidden products (essential for working with draft/invisible items)
r = requests.post('https://www.wixapis.com/stores/v1/products/query',
    headers=headers,
    json={"query": {"paging": {"limit": 50}}, "includeHiddenProducts": True})

products = r.json().get('products', [])
```

**Pitfall:** Default query returns only `visible: true` products. Always pass `includeHiddenProducts: True` when working with newly created or staged products. The 5 Workout Series products (TIMBR-WS-01 through TIMBR-WS-05) are hidden until manually toggled.

## Hiding / Showing a Product

```python
product_id = '2ec416c2-5f97-947a-c44e-70a99a2f9d1d'
r = requests.patch(
    f'https://www.wixapis.com/stores/v1/products/{product_id}',
    headers=headers,
    json={"product": {"visible": False}}
)
# 200 = success
```

## Attaching a Digital File to a Product (after UI toggle)

```python
r = requests.patch(
    f'https://www.wixapis.com/stores/v1/products/{product_id}',
    headers=headers,
    json={"product": {
        "digitalFile": {
            "id": "<wix_media_id>.pdf",
            "fileName": "TIMBR-Workout-Series-Vol-01-Glutes-Hamstring.pdf",
            "fileType": "SECURE_PDF"
        }
    }}
)
```

## Blog Posts — Published

```python
# Query all published posts (no status filter needed — default is published)
r = requests.post('https://www.wixapis.com/blog/v3/posts/query',
    headers=headers,
    json={"query": {}})
posts = r.json().get('posts', [])
```

**Pitfall:** Passing `"filter": {"status": ...}` in the query body causes a 400 error. Query without filter for published posts; use the draft-posts endpoint for drafts.

## Blog Posts — Drafts

```python
# List all drafts
r = requests.post('https://www.wixapis.com/blog/v3/draft-posts/query',
    headers=headers,
    json={"query": {}})
drafts = r.json().get('draftPosts', [])

# Get single draft (no fieldsets in the URL params — causes 400)
r = requests.get(
    f'https://www.wixapis.com/blog/v3/draft-posts/{draft_id}',
    headers=headers)
post = r.json().get('draftPost', {})
```

**Pitfall:** Passing `fieldsets` as a query param to the single-draft GET endpoint returns 400. Omit it — the default response includes all fields except rich content body.

## Updating Draft Post Metadata (Tags, SEO)

```python
r = requests.patch(
    f'https://www.wixapis.com/blog/v3/draft-posts/{draft_id}',
    headers=headers,
    json={
        "draftPost": {
            "tagIds": ["tag-uuid-1", "tag-uuid-2"],
            "seoData": {
                "tags": [
                    {"type": "title", "children": "Page Title | TIMBR"},
                    {"type": "meta", "props": {"name": "description", "content": "..."}},
                    {"type": "meta", "props": {"property": "og:title", "content": "..."}},
                    {"type": "meta", "props": {"property": "og:description", "content": "..."}},
                    {"type": "meta", "props": {"property": "og:type", "content": "article"}}
                ]
            }
        },
        "fieldMask": "tagIds,seoData"
    }
)
```

Use `fieldMask` to avoid overwriting other fields (excerpt, categoryIds, etc).

## Blog Tags

```python
# Get all tags
r = requests.post('https://www.wixapis.com/blog/v3/tags/query',
    headers=headers, json={"query": {}})
tags = r.json().get('tags', [])
```

**Known TIMBR tags (as of May 2026):**

| Label | ID |
|---|---|
| seattle | `f41a4a81-8366-493c-b0e6-b4c5efb01529` |
| gym-guide | `b402f560-df36-484e-a5d0-969a6a79781d` |
| training | `5649b20c-b61c-493f-9ea5-a4f22431e575` |
| culture | `9abe59d2-5c83-4a46-a549-dce8fd47cf94` |
| recovery | `a25d6f87-a47b-46e5-bf6b-08a626535846` |

## Known Product IDs (May 2026)

### Active / Visible
| Product | ID | SKU |
|---|---|---|
| Magazine: Blair | `2ae60c59-0483-26cf-c8fe-74c2a1c8f162` | TIMBR-MAG-BLAIR |
| Magazine: Shumon | `0b47fd03-d814-5ecb-4904-dde29b1333c7` | TIMBR-MAG-SHUMON |
| Foundation Series: Complete Bundle | `9953f4b6-e78a-47e1-24af-442c4e480142` | TIMBR-FS-BUNDLE |
| Foundation Series: Deltoid | `1a850e56-ad62-5ab3-84d1-9a84b8e88ce2` | TIMBR-FS-DELTOID |
| Foundation Series: Back | `040d2580-19a1-bd6b-098c-3d8fe86d533b` | TIMBR-FS-BACK |
| Foundation Series: Chest | `ad3cd9f1-e515-a28f-22bf-c96ed272d7c1` | TIMBR-FS-CHEST |
| Foundation Series: Tricep | `e93155fb-bd39-99a9-b632-423d170b0f16` | TIMBR-FS-TRICEP |
| Foundation Series: Bicep | `96d7c160-5117-ac80-a0bc-5c135416f4d0` | TIMBR-FS-BICEP |
| TIMBR Essential Hoodie | `d881ef14-864d-4b86-8670-00a36060d8cc` | TIMBR-APP-HOODIE |
| TIMBR Cap | `cc06601e-5065-414f-9211-46f283e20e79` | TIMBR-APP-CAP |
| TIMBR Performance Bra | `2fd3758b-e41b-4747-a7ab-2fdc3e3469ce` | TIMBR-APP-BRA |

### Hidden / Staged
| Product | ID | SKU | Status |
|---|---|---|---|
| Magazine: Taylor Crow | `2ec416c2-5f97-947a-c44e-70a99a2f9d1d` | TIMBR-MAG-TCROW | Hidden — wrong PDF attached (BELLA SKY.jpg) |
| Workout Series Vol 01: Glutes & Hamstring | `0dd369c2-35b1-4a6d-b803-6254ff369b55` | TIMBR-WS-01 | Hidden — needs Physical→Digital toggle + PDF attach |
| Workout Series Vol 02: Chest & Tricep | `c4dbadce-aa44-4f99-a2db-c28ea0c69c12` | TIMBR-WS-02 | Hidden — needs Physical→Digital toggle + PDF attach |
| Workout Series Vol 03: Back & Bicep | `b21006af-197c-4af9-8ac2-664cc3c55b43` | TIMBR-WS-03 | Hidden — needs Physical→Digital toggle + PDF attach |
| Workout Series Vol 04: Shoulder & Core | `c4e622a8-80c1-4eed-bed5-48a9342c06de` | TIMBR-WS-04 | Hidden — needs Physical→Digital toggle + PDF attach |
| Workout Series Vol 05: Quads & Calf | `58d031a7-e0c4-4ee2-914a-0ee9e61ab3c8` | TIMBR-WS-05 | Hidden — needs Physical→Digital toggle + PDF attach |

Note: there are also older hidden duplicates (ALL CAPS SKUs, physical type) from the pre-rebrand catalog — ignore these, they are legacy.

## Known Draft Post IDs (May 2026)

| Title | ID | Status |
|---|---|---|
| The Queen Anne Gym Guide | `fe0f0e35-ec3c-4a89-807a-9d000b4ea776` | DRAFT — tags + SEO added; KeyArena ref in body needs manual fix before publish |
| The U-District Gym Guide | `52ceb12e-cfe3-4847-a1fc-049220e265cc` | DRAFT — tags + SEO added; factual claims need verification before publish |

## Editor-Only Work (cannot do via API)

These require Wix MCP on Tanzim's Mac or manual Editor UI:

| Issue | Fix doc |
|---|---|
| Homepage hero says "I'm a paragraph" | `01-homepage.md` in handover zip |
| About page says "Hi! I'm Jane" | `02-about.md` |
| `/shop` returns 404 | `04-shop-page.md` |
| `/contact` returns 404 | `06-contact-page.md` |
| Legal pages don't exist | `03-legal-pages.md` |
| Magazines collection editorial layout | `05-magazines-collection.md` |

Handover zip: `/home/hermes/.hermes/document_cache/doc_330d92336f16_Vhandover.zip` (extracted folder: `timbr3-handoff/`).

## References

- `references/wix-timbr-launch-state.md` — full site state audit as of May 30, 2026
