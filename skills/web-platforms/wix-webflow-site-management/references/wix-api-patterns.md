# Wix API Patterns — TIMBR

## Auth headers (required on every request)
```python
headers = {
    "Authorization": WIX_API_KEY,
    "Content-Type": "application/json",
    "wix-site-id": WIX_SITE_ID
}
```

## Blog posts — query with fieldsets
```python
# CORRECT — fieldsets inside query object
data = {"query": {"paging": {"limit": 100}, "fieldsets": ["CONTENT", "SEO", "COVER_MEDIA"]}}
# WRONG — fieldsets at top level (returns 0 results silently)
data = {"query": {"paging": {"limit": 100}}, "fieldsets": ["CONTENT", "SEO", "COVER_MEDIA"]}
```

## Blog categories
```
POST https://www.wixapis.com/blog/v3/categories/query
{"query": {"paging": {"limit": 50}}}
```

## Store products — query
```
POST https://www.wixapis.com/stores/v1/products/query
{"query": {"paging": {"limit": 100}}}
```

## Site list (account level — no site-id header)
```
GET https://www.wixapis.com/site-list/v2/sites
```
Note: returns redirect-to-signin if key is expired.

## Key expiry detection
HTTP 302 redirecting to `users.wix.com/signin` = key is expired or invalid.
Regenerate at https://manage.wix.com/account/api-keys → "All site permissions".

## HTTP 202 = success (draft)
Wix returns 202 (not 201) for successful item creation. Item is in draft state.
