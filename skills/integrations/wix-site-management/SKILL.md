---
name: wix-site-management
description: Wix API integration for listing sites, querying properties, and analyzing site content
category: integrations
tags: [wix, website, api, analysis, e-commerce]
---

# Wix Site Management

Connect to Wix accounts via API to list sites, inspect properties, and analyze content.

## Credentials

Stored at `~/.hermes/.wixcreds`:
```
WIX_API_KEY=IST.xxxxx...
WIX_ACCOUNT_ID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
```

The API key is a JWT prefixed with `IST.` — issued by Wix Dev Center.

## Key API Endpoints

### List All Sites
```bash
WIX_API_KEY=$(grep WIX_API_KEY ~/.hermes/.wixcreds | cut -d'=' -f2-)
curl -s --max-time 30 \
  -H "Authorization: $WIX_API_KEY" \
  -H "Content-Type: application/json" \
  -X POST \
  -d '{"query": {}}' \
  "https://www.wixapis.com/site-list/v2/sites/query"
```

Response includes: `id`, `displayName`, `viewUrl`, `editUrl`, `published`, `premium`, `domainConnected`.

### Get Site Properties
```bash
curl -s --max-time 30 \
  -H "Authorization: $WIX_API_KEY" \
  -H "wix-site-id: SITE_ID_HERE" \
  "https://www.wixapis.com/site-properties/v4/properties"
```

Response includes: business name, email, phone, address, timezone, payment currency.

## When Browser Tools Fail

Wix sites are JavaScript-heavy and often timeout in browser tools. Fallback pattern:

```bash
# Pull raw HTML via curl
curl -sL --max-time 45 "https://[site-url]" > /tmp/wix_site.html

# Extract key elements
grep -i -E "<title|<meta|<h1|<h2|<nav|<header|<footer" /tmp/wix_site.html
```

This gives enough for SEO analysis, navigation structure, and meta tags.

## Site Gap Analysis Framework

When auditing a Wix site, check:

**Branding & Credibility**
- Wix free banner visible? (needs premium to remove)
- Professional domain connected vs wixsite.com URL?
- Favicon set?

**SEO**
- Title, meta description present?
- OG tags (og:title, og:description, og:image)?
- Canonical URL set?

**Content Structure**
- Clear hero / value proposition?
- Navigation labels professional (not "My Blog")?
- CTAs above the fold?

**Mobile Responsiveness**
- Wix handles basics, but check for:
  - Fixed-width containers
  - Navigation hamburger menu
  - Gallery/card stacking on small screens

**E-commerce** (if applicable)
- Products categorized?
- Cart integration working?
- Shop link in navigation?

## API Key Troubleshooting

**500 errors or redirects to signin:** Key expired or malformed. Regenerate from:
`manage.wix.com/account/api-keys`

**Key requirements:**
- Account-level permissions
- "Site List" scope minimum
- Regenerate if older than ~30 days (Wix tokens can expire)

## Related Files

- `references/wix-api-endpoints.md` — full endpoint reference (to be added)
