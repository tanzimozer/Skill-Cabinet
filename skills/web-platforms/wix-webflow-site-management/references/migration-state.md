# TIMBR Wix → Webflow Migration State
_Last updated: 25 May 2026_

## Credentials on VM
- Wix: `~/.hermes/.wixcreds` — WIX_API_KEY, WIX_ACCOUNT_ID, WIX_SITE_ID
- Webflow: `~/.hermes/.webflowcreds` — WEBFLOW_API_TOKEN, WEBFLOW_SITE_ID

## Wix Site
- Site ID: `ab465896-e5c3-4f5d-bc9d-7f495a6d6be1`
- Live URL: https://timbrworkspace.wixsite.com/my-site-25
- Editor URL: https://editor.wix.com/html/editor/web/renderer/edit/ab465896-e5c3-4f5d-bc9d-7f495a6d6be1
- Account ID: `626360fa-569c-4810-bd3a-0cdf93ecba76`

## Webflow Site
- Site ID: `6a14beea52ec6555e6a69a41`
- Site name: TIMBR-3 TRANSFER
- Plan: Starter (blocks programmatic page creation)

## Migrated to Webflow ✅
| Content | Count | WF Collection ID |
|---|---|---|
| Blog Categories | 3 | `6a14c2c24cd027a6509a1d10` |
| Blog Posts | 19 | `6a14c2d2e02f3d5778d64a38` |
| Products | 12 | `6a14c430c0fa15be28694dea` |

## Blog Categories (Wix ID → WF ID)
- The Guide: `8c5800da...` → `6a14c3e7aeea36a2defb3320`
- Training: `2126a2c5...` → `6a14c3e84824ae7b0083fbb6`
- Culture: `6d28fb40...` → `6a14c3e9adca1013f3832fa8`

## Wix Store Collections
- Magazines (`magazines`) — Blair, Shumon, Taylor Crow
- Foundation Series (`foundation-series`) — 6 training PDFs
- Apparel (`apparel`) — Hoodie, Cap, Performance Bra
- Workout Series (`workout-series`) — 5 vols created via API, hidden, need PDF attachment

## Known Issues on Wix
1. **CRITICAL**: Magazine: Taylor Crow has wrong digital file (`BELLA SKY.jpg` instead of PDF)
2. `/shop` returns 404 — page not created in editor yet
3. `/contact` returns 404 — page not created in editor yet
4. `/privacy`, `/terms`, `/refund-policy` don't exist yet
5. Homepage hero still has Wix placeholder text
6. About page still has "Hi I'm Jane" template content
7. 2 blog posts in draft state (Queen Anne gym guide, U-District gym guide) — Queen Anne has KeyArena → should be Climate Pledge Arena

## Handoff Docs
Claude Desktop session produced `timbr3-handoff.zip` with 8 docs for editor work.
These require Wix MCP + Claude Desktop to execute — not doable from VM.
