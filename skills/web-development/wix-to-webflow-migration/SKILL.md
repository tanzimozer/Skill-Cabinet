---
name: wix-to-webflow-migration
description: Migrating a Wix site to Webflow — scraping, rebuilding, CMS setup, publishing
category: web-development
---

# Wix → Webflow Migration

## When to use
Tanzim wants to migrate a TIMBR/Blair site from Wix to Webflow for programmatic control and clean SEO setup.

## Key decisions / context
- Wix API only controls **CMS/dynamic content** — static hardcoded design text cannot be edited via API
- Webflow CMS API is the right target — structure content as collections from the start
- If no existing traffic: SEO downside is eliminated — start fresh on Webflow with proper meta, OG, sitemap
- Webflow is faster and gives Friday programmatic write access; Wix does not

## Credentials location
- **Wix**: `~/.hermes/.wixcreds` — WIX_API_KEY, WIX_ACCOUNT_ID, WIX_SITE_ID
  - Wix keys expire/rotate regularly — test before using, re-auth if 401/redirect
  - Test: `curl -H "Authorization: $WIX_API_KEY" -H "wix-site-id: $WIX_SITE_ID" -X POST https://www.wixapis.com/blog/v3/posts/query -d '{"query":{"paging":{"limit":1}}}'`
- **Webflow**: not yet stored — get token from Tanzim (see below)

## Getting Webflow API token (correct path)
**DO NOT use** `/dashboard/account/authorizations` — that link is wrong/stale.

Correct path:
1. Go to webflow.com
2. Click account avatar (top right) → **Account Settings**
3. Click **Integrations** tab
4. Scroll to **API Access** → Generate token
5. Also grab **Site ID**: Site Settings → General → Site ID

## Migration approach (95% autonomous)
1. **Scrape Wix** — pull all pages, blog posts, products, images via Wix REST API + browser scraping for static design elements
2. **Audit site structure** — map pages, nav, CMS collections, assets
3. **Build in Webflow** — recreate structure, set up CMS collections, push content via API
4. **Assets** — download from Wix, re-upload to Webflow
5. **SEO** — set meta titles, descriptions, Open Graph, enable sitemap
6. **Publish** — push live
7. **Visual QA** — Tanzim does a 10-min walkthrough (the 5% he handles)

## Known pitfalls
- Wix `site-list/v2/sites` endpoint redirects to login — use site-specific endpoints with `wix-site-id` header instead
- Static text on Wix pages is not accessible via API — scrape via browser/HTTP for those
- Wix API keys are short-lived; always test connection before starting a migration run
- Webflow free tier limits CMS items — check plan before bulk import

## References
- `references/blair-site-audit.md` — Blair Magazine Wix site details once audit is run
