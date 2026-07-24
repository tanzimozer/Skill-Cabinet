# TIMBR Wix Site — Launch State Audit (May 30, 2026)

Source: `timbr3-handoff/07-health-audit.md` from `Vhandover.zip`

## Site Identity
- Live URL: https://timbrworkspace.wixsite.com/my-site-25
- Editor URL: https://editor.wix.com/html/editor/web/renderer/edit/ab465896-e5c3-4f5d-bc9d-7f495a6d6be1
- Plan: Free (no custom domain, Wix ads showing)
- siteDisplayName: "TIMBR" ✅
- businessName: "TIMBR" ✅
- description: "A Pacific Northwest fitness publication..." ✅

## Catalog State (26 total products, 11 visible)
- 3 magazines: Blair ✅, Shumon ✅, Taylor Crow ❌ (hidden — wrong PDF)
- 8 Foundation Series: all visible ✅
- 3 apparel: all visible, no product photos ⚠️
- 5 Workout Series: hidden, Physical type, PDFs uploaded to Media Manager but not attached

## Blocked on Tanzim
- Custom domain → needs Premium plan upgrade
- Product photography for: Taylor Crow, Complete Bundle, Hoodie, Cap, Performance Bra
- Wix Payments / Stripe test transaction
- GA4 + Meta Pixel wiring (Dashboard → Marketing → Analytics)
- Workout Series Physical→Digital toggle (API can't do it)
- Taylor Crow real PDF upload

## Blog State (19 published, 21 drafts)
- All 19 published posts: have descriptions, excerpts, SEO, tag assignments ✅
- All 3 categories: rewritten in TIMBR voice ✅
- Queen Anne draft: SEO + tags added; KeyArena in body text needs fix before publish
- U-District draft: SEO + tags added; UW IMA factual claims need verification before publish
- Seattle neighborhood post (7b0e3331): published but missing featured image ⚠️

## What API Can Fix (still pending)
- Workout Series PDF attach (after Tanzim does UI toggle)
- Taylor Crow PDF attach (after Tanzim uploads real PDF)
- Any product metadata, descriptions, SEO

## What Requires Editor UI (Wix MCP on Mac)
- Homepage (placeholder text throughout)
- About page ("Hi I'm Jane" template)
- /shop 404
- /contact 404
- /privacy, /terms, /refund-policy — pages don't exist
- Magazines collection editorial layout

## Handover Zip Location
`/home/hermes/.hermes/document_cache/doc_330d92336f16_Vhandover.zip`
Extracted folder: `timbr3-handoff/` (9 files, 01-homepage.md through 08-workout-series-listings.md)

To read any file:
```python
import zipfile
z = zipfile.ZipFile('/home/hermes/.hermes/document_cache/doc_330d92336f16_Vhandover.zip')
content = z.read('timbr3-handoff/01-homepage.md').decode('utf-8')
```
