---
name: wix-webflow-site-management
description: Managing, migrating, and building on Wix and Webflow sites via API and browser
category: web-platforms
tags: [wix, webflow, cms, migration, api]
---

## When to use

- Working with TIMBR's Wix site (`ab465896-e5c3-4f5d-bc9d-7f495a6d6be1`)
- Migrating content from Wix to Webflow
- Managing blog posts, products, collections via Wix/Webflow API
- Attempting Wix Editor automation
- References: `references/wix-api-patterns.md`, `references/webflow-api-patterns.md`, `references/migration-state.md`

---

## Wix API

### Credentials
- Stored at `~/.hermes/.wixcreds`
- Keys: `WIX_API_KEY`, `WIX_ACCOUNT_ID`, `WIX_SITE_ID`
- Keys expire — if you get 401/redirect-to-signin, regenerate at https://manage.wix.com/account/api-keys
- Headers required: `Authorization: <key>` + `wix-site-id: <site_id>` + `Content-Type: application/json`

### What the Wix API CAN do
- Blog posts: query, get, create — via `https://www.wixapis.com/blog/v3/posts/query`
- Blog categories: query, create — via `https://www.wixapis.com/blog/v3/categories/query`
- Store products: query, update descriptions, SEO, pricing — via `https://www.wixapis.com/stores/v1/products/query`
- Store collections: create, list — via `https://www.wixapis.com/stores/v1/collections/query`
- Site identity, business hours, consent policy

### What the Wix API CANNOT do
- Edit page content or layouts (static text, hero copy, section structure)
- Create new pages
- Access the Wix Editor canvas programmatically
- Toggle products from Physical to Digital (Catalog V1 limitation)
- Attach digital files to products

### Fieldsets for blog posts
Pass fieldsets inside the query object, not at top level:
```python
{"query": {"paging": {"limit": 100}, "fieldsets": ["CONTENT", "SEO", "COVER_MEDIA"]}}
```
NOT `{"query": {...}, "fieldsets": [...]}` — the latter returns 0 results silently.

### HTTP 202 from Wix = success (draft created)
HTTP 202 on item creation means the item was accepted and created as a draft — not an error. Items need to be published separately.

---

## Webflow API

### Credentials
- Stored at `~/.hermes/.webflowcreds`
- Keys: `WEBFLOW_API_TOKEN`, `WEBFLOW_SITE_ID`
- TIMBR site: `6a14beea52ec6555e6a69a41`
- Use v2 API: `https://api.webflow.com/v2/`
- Auth header: `Authorization: Bearer <token>`

### What Webflow API CAN do (on any plan)
- Read/write CMS collections and items
- Create new CMS collections with custom fields
- Read site info and existing pages
- Upload assets (with correct scopes)

### What Webflow API CANNOT do on Starter plan
- Create new static pages programmatically
- Edit page layouts or static content
- The `/v2/sites/{id}/pages` POST endpoint returns 404 on Starter

### Correct endpoint for listing pages
```
GET https://api.webflow.com/v2/sites/{siteId}/pages?siteId={siteId}
```
(siteId needed as both path AND query param)

### CMS item creation returns 202 = draft
Same as Wix — 202 means created as draft, not an error.

---

## Migration approach (Wix → Webflow)

### What transfers well via API
- Blog posts (title, slug, excerpt, category, date) ✅
- Blog categories ✅
- Products (name, description, price, type, category) ✅

### What does NOT transfer via API
- Page layouts and visual design (proprietary formats on both sides)
- Static text hardcoded in the Wix editor canvas
- Images/media (requires separate download + re-upload)
- Full blog post body content (Wix API returns metadata but not the rich text body via simple query — would need content node API)

### Migration state for TIMBR (as of May 2026)
See `references/migration-state.md` for full detail. Summary:
- 19 blog posts ✅ migrated to Webflow
- 3 categories ✅
- 12 products ✅ (Products collection created)
- Visual design: NOT migrated — Webflow is data-only, blank canvas

---

## Wix Editor automation

**The Wix Editor cannot be automated from the VM.** It's a heavy JS app that requires a logged-in browser session. The VM browser tool times out on it.

The only path to editor changes:
1. **Claude Desktop + Wix MCP** — the handoff session that created `timbr3-handoff/` docs used this. User runs Claude Desktop locally with Wix MCP connected.
2. **Manual editing** — user does it themselves in the Wix Editor browser UI.

When the user asks you to make editor changes, be honest about this immediately. Don't attempt browser navigation to `editor.wix.com` — it will time out.

### Prompt to send to Claude Desktop for editor work
```
I need you to execute the TIMBR-3 Wix handoff documents against the live Wix Editor. 
The site is ab465896-e5c3-4f5d-bc9d-7f495a6d6be1.
You have Wix MCP connected. Use it to make all the changes in the attached zip.
Work through one file at a time in order (01 → 08), confirm each section.
Voice spec: editorial-athletic, no hype words, no exclamation points, sentence-case all labels.
Screenshot each page after completing and send to me. Publish when all done.
```

---

## Pitfalls

- **Wix API key expiry** — Keys expire and return redirect-to-signin (HTTP 302 with Location to users.wix.com). Test with a simple blog query before assuming the key is valid.
- **"Boss" in Blair communications** — Never address Blair as "Boss" — that's Tanzim's term. Blair gets addressed by name.
- **Webflow Starter plan blocks page creation** — Upgrade to CMS plan (~$23/mo) to unlock programmatic page management via API.
- **Wix digital product limitation** — Catalog V1 API cannot create Digital product type. Workaround: create as Physical with weight 0, then manually toggle to Digital in Dashboard.
- **Product visibility** — `visible: false` products exist in catalog but don't appear in store. Don't confuse with deleted.
- **Taylor Crow magazine bug** — The digital file attached is `BELLA SKY.jpg` (wrong file). Needs manual fix in Wix Dashboard: upload correct PDF → attach to product.
