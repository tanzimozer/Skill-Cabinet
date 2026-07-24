# Wix → Webflow Migration

## Context
TIMBR Site 3 (Blair, Shumon, Taylor fitness magazine sales site) was built on Wix.
Decision made May 2026 to evaluate migrating to Webflow for programmatic content control.
Migration executed May 25 2026 — see "What Actually Happened" section below.

## Why Webflow Wins for This Use Case

| Factor | Wix | Webflow |
|--------|-----|---------| 
| API content editing | CMS collections only; static text locked | CMS collections fully editable via REST API |
| Static page text edits | Impossible via API — editor only | Impossible via API — but Webflow devs CMS-first by convention |
| SEO tooling | Adequate | Better: clean semantic HTML, meta/OG fields, auto-sitemap, faster loads |
| Hosting cost | Lower | Higher (worth it for API control) |
| Programmatic control | Poor | Good (with CMS-structured content) |

## Migration Scope (Friday can handle solo ~95%)

**Friday handles:**
- Scrape full Wix site (layout, content, colours, fonts, assets)
- Rebuild structure in Webflow
- Set up CMS collections, migrate copy and images
- Configure pages, nav, responsive breakpoints
- SEO foundations (meta, OG, sitemap)
- Publish

**Tanzim reviews:**
- Final visual sign-off (~10 min walkthrough)
- Pixel-perfect subjective design calls

## When SEO Loss Is Not a Risk
If the current Wix site has **no existing traffic or organic rankings**, the SEO downside of migration disappears entirely. Starting fresh on Webflow is actually better — SEO tooling is superior, and you're building right from day one.

**Check before migrating:** Does the Wix site have any organic traffic? (Google Search Console, Wix Analytics). If zero — proceed without concern.

## Credentials Needed to Start

### Wix API Key
- Found at: https://manage.wix.com/account/api-keys
- Click Generate API Key → name it → **All site permissions** → copy
- Keys expire/invalidate frequently — test before assuming it's valid
- Test with: `curl -H "Authorization: $WIX_KEY" -H "wix-site-id: $SITE_ID" -X POST "https://www.wixapis.com/blog/v3/posts/query" -d '{"query":{"paging":{"limit":1}}}'`
- Store at `~/.hermes/.wixcreds` (chmod 600)

### Webflow API Token — CRITICAL: Get the RIGHT type
There are TWO token types in Webflow and they are **not interchangeable**:

| Token Type | Where to Generate | Scopes Available | Use For |
|-----------|------------------|-----------------|---------|
| **Workspace token** | webflow.com → Account avatar → Account Settings → Integrations → "Workspace API access" | Cloud Apps, Code components, Workspace activity only — **NO site access** | Workspace-level ops only |
| **Site token** ✅ | Webflow Designer → W logo → Site Settings → Apps & Integrations → "API access" → Generate | Sites, CMS, Pages, Assets — **what you actually need** | Everything — use this |

The workspace token returns 403 on all site endpoints. Always get the **site-level token** from within the Designer.

- Store at `~/.hermes/.webflowcreds` (chmod 600) alongside WEBFLOW_SITE_ID

## What Actually Happened (May 2026 execution)

### Content successfully migrated via API
- **19 blog posts** — titles, slugs, excerpts, categories, published dates
- **3 blog categories** — The Guide (8 posts), Training (6 posts), Culture (5 posts)
- **12 visible products** — 3 Magazines ($19.99), 6 Foundation Series ($19.99-$69), 3 Apparel ($39.99-$49.99)
- **Products collection** — created in Webflow with Description, Price, Product Type, Category, Image URL, Buy Link fields

### Content NOT extractable from Wix API
- **Full article body text** — Wix blog API returns title, slug, excerpt, dates, category IDs, and a `contentId` but NOT the actual body text. The body lives in a separate content service not accessible via the standard API key.
- **Homepage static design** — hero text, slideshow, section layout — all locked in Wix's proprietary editor format
- **About page** — placeholder text only ("I am a movie blogger" — was never properly filled in)

### Page creation blocked by Webflow plan tier
- `POST /v2/sites/{id}/pages` returns 404 on Starter plan
- Programmatic page creation requires **CMS plan or above** (~$23/mo)
- On Starter: pages must be created manually in Webflow Designer
- **Workaround:** Upgrade to CMS plan → then full API-driven page build becomes possible

### API behaviour notes
- Webflow CMS item creation returns **HTTP 202 (Accepted)** for draft items — this is SUCCESS, not failure. Item is created in draft state.
- Items are not published until you explicitly call the publish endpoint or publish via Designer
- Wix blog v3 API returns empty `posts[]` if fieldsets are inside `query` object — move them outside: `{"query": {...}, "fieldsets": ["CONTENT", "SEO"]}`... actually this also fails. Full post body text is not accessible via API key auth.
- Wix site-list API (`/site-list/v2/sites`) requires different auth than content APIs — often redirects to login page even with valid key. Content APIs (blog, store) work fine with standard IST key + `wix-site-id` header.

## API Limitations to Know

### Wix
- API only touches **dynamic/CMS content** (collections, product listings)
- Static text on design pages cannot be edited via API — locked in Wix editor format
- Blog post BODY TEXT is not in the API response — only excerpt, metadata, category IDs
- Primary use here: scraping existing content before migration

### Webflow
- CMS API: full read/write on collection items (v2)
- Static text hardcoded in Designer: still not API-editable
- **Page creation via API: Starter plan only** — requires CMS plan+
- Best practice: structure everything as CMS collections → enables ongoing programmatic updates post-migration
- Friday can then update Blair/Shumon/Taylor magazine content, pricing, etc. via API without touching Webflow Designer

## Pitfalls
- Don't migrate if significant organic traffic exists — needs 301 redirect plan first
- Confirm all Wix apps in use (booking, payments, forms) have Webflow equivalents before cutting over
- Plan a switchover window — brief period where site is in transition
- Structure new Webflow site CMS-first, not static-first, to unlock future programmatic control
- **Don't spawn one massive subagent for the full migration** — it times out at 600s. Execute phase by phase directly.
- **Wix API keys expire frequently** — always test the key before starting migration work; don't assume yesterday's key still works
- **Always get site-level Webflow token**, not workspace-level. They look identical but workspace tokens have no site scopes.
- **Codeword must arrive in the SAME message as the credential** — if Tanzim sends a token without codeword, ask him to resend both together. Do not store partial-auth credentials.
