# TIMBR Founding Team — Credential Reference

## Tanzim Ozer — CEO & Co-Founder

- **Full name:** Tanzim Ozer
- **Pedigree:** 8 years operations
- **Certifications:** PMP (Jul 2026), Google PM, IBM Product, Microsoft Power BI, Google Data Analytics
- **Companies:** TIMBR (founder), US Bank, 24 Hour Fitness
- **Equity:** Founder
- **Radar colour:** Cyan `#00c8f0`
- **Badge:** "8 YRS OPS"
- **Hook:** "Product-first founder."
- **Claim:** "Built TIMBR from zero."
- **Domains/Tags:** Product Strategy, Operations, Fitness Domain, **Analytics / Database** ← include this
- **Peak skills:** Fitness Domain 10 · Leadership 9 · Product Strategy 9
- **Credential lines (card):**
  - "PMP  ·  Google PM  ·  IBM Product"
  - "Microsoft Power BI  ·  Google Data Analytics"
  - "US Bank  ·  24 Hour Fitness  ·  TIMBR Founder"

## Sagar Giri — CTO & Co-Founder

- **Full name:** Sagar Giri (NOT just "Sagar" — always use full name on visuals)
- **Pedigree:** Amazon SDE — CURRENT EMPLOYEE (NOT ex-Amazon — he is still there)
- **Skills:** Backend systems, AWS cloud architecture, data engineering, full-stack mobile
- **Companies:** Amazon (current), TIMBR (Co-Founder)
- **Equity:** Founder
- **Radar colour:** Green `#00d96b`
- **Badge:** "AMAZON SDE"
- **Hook:** "Systems that scale."
- **Claim:** "Owns the full tech roadmap."
- **Domains/Tags:** Backend, Mobile Dev, Data & Analytics, AWS Cloud
- **Peak skills:** Backend 9 · Data & Analytics 7 · AI/ML 6
- **Credential lines (card):**
  - "Amazon — Backend Systems Engineering"
  - "AWS Cloud Architecture  ·  Data Engineering"
  - "Mobile Development  ·  TIMBR Co-Founder"

## Waseem Ahmad — Strategic Advisor

- **Full name:** Waseem Ahmad
- **Pedigree:** ex-Meta Staff SWE · ex-Google (NOT current — these are past roles)
- **Experience:** 14 years industry
- **Credentials:** US Patent Holder, Android @Scale Speaker (Meta), Rice University (Comp. Science)
- **Companies:** Meta (7 yrs, Staff SWE), Google, Nextdoor
- **Equity:** 2.5–6% (non-diluted, not yet finalised) · 5-year advisory engagement
- **Radar colour:** Orange `#f56500`
- **Badge:** "ex-META STAFF SWE"
- **Hook:** "Billions served. Equity-aligned."
- **Claim:** "2.5–6% equity stake."
- **Domains/Tags:** Mobile Dev, AI / ML, Voice AI, Android
- **Peak skills:** Mobile Dev 10 · AI/ML 9 · Voice AI 8
- **Credential lines (card):**
  - "US Patent Holder  ·  Android @Scale Speaker"
  - "Meta  ·  Google  ·  Nextdoor  ·  14 Yrs"
  - "Rice University CS  ·  2.5–6% Equity"

## Radar Scores (/10)

| Dimension        | Tanzim | Sagar | Waseem |
|------------------|--------|-------|--------|
| AI / ML          | 5      | 6     | 9      |
| Backend          | 4      | 9     | 5      |
| Mobile Dev       | 3      | 7     | 10     |
| Fitness Domain   | 10     | 3     | 2      |
| Leadership       | 9      | 5     | 6      |
| Product Strategy | 9      | 5     | 4      |
| Data & Analytics | 8      | 7     | 5      |
| Frontend         | 2      | 6     | 3      |

## Layout preferences (from user feedback)

- **Landscape A4 only** — user rejected portrait layout
- **No footer** — user explicitly removed it
- **Uniform card template** — all 3 cards same structure, user rejected mixed styles
- **Sagar is CURRENT Amazon** — never write "ex-Amazon"
- **Sagar's name is Sagar Giri** — full name on all visuals

## WhatsApp send command (working)

```bash
TOKEN=$(grep WHATSAPP_BRIDGE_TOKEN /home/hermes/.hermes/.env | cut -d= -f2)
curl -s -X POST http://localhost:3000/send-media \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d "{\"chatId\":\"160799431606497@lid\",\"filePath\":\"/path/to/file.png\",\"mediaType\":\"image\",\"caption\":\"\"}"
```

**Note:** Use `/send-media` endpoint, NOT `/send`. The `/send` endpoint only handles text (requires `message` field). `/send-media` requires `chatId` + `filePath`.

## Notes

- Waseem bootstrapping-minded — prefers lean builds, not over-staffed early
- Waseem's equity stake not yet finalised — use "2.5–6%" range until confirmed
- All three have complementary domains with minimal overlap — this is the radar's core story
