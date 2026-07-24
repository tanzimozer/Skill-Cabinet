# Webflow API Patterns — TIMBR

## Auth
```python
headers = {
    "Authorization": f"Bearer {WF_TOKEN}",
    "Content-Type": "application/json",
    "accept": "application/json"
}
```
Base URL: `https://api.webflow.com/v2/`

## List sites
```
GET /v2/sites
```

## List collections
```
GET /v2/sites/{siteId}/collections
```

## Get collection (with fields)
```
GET /v2/collections/{collectionId}
```
Returns full field schema — use this instead of the (404-returning) `/fields` endpoint.

## List pages
```
GET /v2/sites/{siteId}/pages?siteId={siteId}
```
Note: siteId needed in BOTH path and query params.

## Create CMS item
```
POST /v2/collections/{collectionId}/items
{"fieldData": {"name": "...", "slug": "...", ...}}
```
Returns 202 (draft) on success — not an error.

## Scopes needed for this token
- Site read: comes with site-level token
- CMS read/write: comes with site-level token
- Page creation: requires CMS plan (not Starter)
- workspace:read: requires workspace-level token (different token type)

## TIMBR Collection IDs
- Blog Categories: `6a14c2c24cd027a6509a1d10`
- Blog Posts: `6a14c2d2e02f3d5778d64a38`
- Products: `6a14c430c0fa15be28694dea`
