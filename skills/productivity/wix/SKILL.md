---
name: wix
description: "Wix REST API: manage blog posts, products, categories, collections, and site content via Python urllib."
tags: [wix, cms, website, api, ecommerce, blog]
triggers:
  - User wants to manage Wix site content programmatically
  - User wants to migrate content between Wix sites
  - User asks about Wix API for blog, store, or CMS
  - User wants to query or compare Wix site content
  - User mentions TIMBR migration or My Site 25
---

# Wix REST API Integration

## Auth Setup

1. Go to: https://manage.wix.com/account/site-selector
2. Select the target site
3. Settings > Advanced > API Keys
4. Click "Generate API Key"
5. Give it a name (e.g. "Friday")
6. Select permissions: Blog, Store Products, CMS, Site Members (as needed)
7. Copy the API key

**Token format:** starts with `IST.eyJ...` (JWT format)

## API Base

```
https://www.wixapis.com/
```

All requests require:
```
Authorization: IST.eyJ...  (no "Bearer" prefix)
Content-Type: application/json
wix-site-id: <site-id>  (required for site-specific operations)
```

## Python Helper (urllib — no extra libs needed)

```python
import urllib.request, json

API_KEY = "IST.eyJ..."  # Your API key
SITE_ID = "ab465896-e5c3-4f5d-bc9d-7f495a6d6be1"  # Target site

def wix_request(method, url, data=None, site_id=None):
    headers = {
        "Authorization": API_KEY,
        "Content-Type": "application/json"
    }
    if site_id:
        headers["wix-site-id"] = site_id
    
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read()), r.status
    except urllib.error.HTTPError as e:
        return {"error": str(e), "body": e.read().decode()[:500]}, e.code
```

## Common Operations

### Query Blog Posts

```python
result, status = wix_request(
    "POST", 
    "https://www.wixapis.com/blog/v3/posts/query",
    data={"query": {"paging": {"limit": 100}}},
    site_id=SITE_ID
)
for post in result.get('posts', []):
    print(f"- {post['title']}")
```

### Get Blog Categories

```python
result, status = wix_request(
    "GET",
    "https://www.wixapis.com/blog/v3/categories",
    site_id=SITE_ID
)
for cat in result.get('categories', []):
    print(f"- {cat['label']} ({cat.get('postCount', 0)} posts)")
```

### Query Store Products

```python
result, status = wix_request(
    "POST",
    "https://www.wixapis.com/stores/v1/products/query",
    data={"query": {}},
    site_id=SITE_ID
)
for product in result.get('products', []):
    print(f"- {product['name']} | Type: {product.get('productType')} | ${product.get('price', {}).get('price')}")
```

### Query Store Collections

```python
result, status = wix_request(
    "POST",
    "https://www.wixapis.com/stores/v1/collections/query",
    data={},
    site_id=SITE_ID
)
for coll in result.get('collections', []):
    print(f"- {coll['name']}")
```

### Create a Blog Post

```python
result, status = wix_request(
    "POST",
    "https://www.wixapis.com/blog/v3/posts",
    data={
        "post": {
            "title": "My New Post",
            "richContent": {
                "nodes": [
                    {"type": "PARAGRAPH", "nodes": [{"type": "TEXT", "textData": {"text": "Post content here..."}}]}
                ]
            }
        }
    },
    site_id=SITE_ID
)
```

### Create a Product

```python
result, status = wix_request(
    "POST",
    "https://www.wixapis.com/stores/v1/products",
    data={
        "product": {
            "name": "Foundation Series: BUNDLE",
            "productType": "physical",  # API can only create physical, convert to digital manually
            "priceData": {"price": 69.99},
            "description": "Complete 5-guide bundle..."
        }
    },
    site_id=SITE_ID
)
```

## Site Migration Pattern

When migrating content between two Wix sites:

```python
OLD_SITE = "f916c8b1-134a-4691-9241-5a14bf849078"
NEW_SITE = "ab465896-e5c3-4f5d-bc9d-7f495a6d6be1"

# 1. Query all content from old site
old_posts, _ = wix_request("POST", "https://www.wixapis.com/blog/v3/posts/query",
    data={"query": {"paging": {"limit": 100}}}, site_id=OLD_SITE)

new_posts, _ = wix_request("POST", "https://www.wixapis.com/blog/v3/posts/query",
    data={"query": {"paging": {"limit": 100}}}, site_id=NEW_SITE)

# 2. Compare by title
old_titles = set(p['title'] for p in old_posts.get('posts', []))
new_titles = set(p['title'] for p in new_posts.get('posts', []))
missing = old_titles - new_titles

# 3. Transfer missing posts
for post in old_posts['posts']:
    if post['title'] in missing:
        # Create on new site
        wix_request("POST", "https://www.wixapis.com/blog/v3/posts",
            data={"post": post}, site_id=NEW_SITE)
```

## API Limitations — Critical

1. **Products can only be created as "physical"** — The Wix Stores V1 API cannot create digital products. You must create as physical, then manually convert to digital in the dashboard.

2. **Site-level SEO not accessible** — Homepage meta title/description, social share defaults, and robots settings must be configured in the dashboard.

3. **Editor pages cannot be built via API** — Page layout, design sections, and navigation are manual Editor work.

4. **Online Programs endpoints return 404** — Not available via REST API.

5. **Member accounts cannot be bulk migrated** — Login/auth is tied to the original site.

6. **Collection assignment silently fails** — The `/stores/v1/collections/{id}/productIds` and `/stores/v1/collections/{id}/addProducts` endpoints return 200 but do NOT actually assign products to collections. This is dashboard-only. The API lies about success.

## TIMBR-Specific Setup

**Old Site (read-only source):**
- Name: timbr.fit (Wix Studio)
- Site ID: f916c8b1-134a-4691-9241-5a14bf849078

**New Site (all work here):**
- Name: My Site 25
- Site ID: ab465896-e5c3-4f5d-bc9d-7f495a6d6be1

**Account ID:** 626360fa-569c-4810-bd3a-0cdf93ecba76

**Content Status (as of May 2026):**
- Posts: 19/19 published
- Categories: 3 (The Guide: 8, Training: 6, Culture: 5)
- Products: 12 (9 digital content as physical, 3 merch)
- Collections: EBOOKS, Magazines (must assign in dashboard)

## Publishing Draft Posts

Posts created via API or imported are stored as drafts. To publish them:

```python
# 1. Query all drafts
drafts, _ = wix_request('POST', 'https://www.wixapis.com/blog/v3/draft-posts/query',
    data={'query': {'paging': {'limit': 100}}}, site_id=SITE_ID)

# 2. Publish each draft
for draft in drafts.get('draftPosts', []):
    draft_id = draft.get('id')
    result, status = wix_request('POST',
        f'https://www.wixapis.com/blog/v3/draft-posts/{draft_id}/publish',
        data={}, site_id=SITE_ID)
    # status 200 = published successfully
```

**Note:** The `/blog/v3/posts/{id}/publish` endpoint returns 404 — use the draft-posts endpoint above instead.

## Transferring Posts Between Sites

When creating a draft post on a new site from old site content, you MUST include `memberId`:

```python
# Get memberId from an existing post on the target site
posts, _ = wix_request('POST', 'https://www.wixapis.com/blog/v3/posts/query',
    data={'query': {'paging': {'limit': 1}}}, site_id=NEW_SITE)
member_id = posts['posts'][0].get('memberId')

# Create draft with memberId (required!)
new_draft = {
    'draftPost': {
        'title': source_draft.get('title'),
        'richContent': source_draft.get('richContent'),
        'memberId': member_id,  # Without this: 400 INVALID_ARGUMENT
        'categoryIds': [target_category_id]  # Optional
    }
}
result, status = wix_request('POST', 'https://www.wixapis.com/blog/v3/draft-posts',
    data=new_draft, site_id=NEW_SITE)
```

## Pitfalls

- **Blog post creation often fails (404)** — The `/blog/v3/posts` POST endpoint frequently returns 404 even with valid auth. Use the draft-posts workflow: create via `/blog/v3/draft-posts`, then publish via `/blog/v3/draft-posts/{id}/publish`.
- **No "Bearer" prefix** — Unlike most APIs, Wix wants just `Authorization: IST.eyJ...` not `Bearer IST.eyJ...`
- **wix-site-id header required** — Every site-specific request needs this header
- **Account-level vs Site-level tokens** — Account tokens (generated from dev.wix.com) may not work for site content. Use site-specific API keys.
- **Query endpoints use POST** — Blog posts and products use POST with a query body, not GET with params
- **Rate limits** — Be mindful of bulk operations, add delays if hitting limits
- **Physical vs Digital products** — API creates physical only; manual dashboard conversion required
