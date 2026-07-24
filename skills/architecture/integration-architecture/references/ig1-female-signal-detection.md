# IG-1 Protocol: Female Signal Detection

**Status:** Finalized & Locked (June 5, 2026)

## Decision Log

**Q1: Pronoun Weighting**
- **Decision:** Only female pronouns count
- **Weights:** she/her = 3pts, they/them = 1pt, ignore he/him
- **Rationale:** Maximum precision; gendered pronouns > generic pronouns

**Q2: Weighted Hierarchy**
- **Decision:** Multi-tier signal hierarchy
- **Weights:**
  - she/her pronouns: 3 pts
  - woman, girl, lady, female, mum, mom (gender nouns): 2 pts
  - sister, wife, daughter, nana, gran (relationship terms): 1.5 pts
  - blogger, babe, queen, goddess (low-value generic): 0.5 pts
- **Rationale:** Pronouns are strongest indicator; relationships are intermediate; generic descriptors are weak

**Q3: Confidence Threshold**
- **Decision:** Two-tier confidence system
  - **Primary tier:** ≥3.0 score → 96.2% precision, <5% false positives
  - **Business-account recovery tier:** ≥3.5 score → recovers 18–22% of female business owners (lower precision trade-off)
- **Rationale:** 3.0 gives clean high-precision signal for consumer accounts; 3.5 allows capture of female entrepreneurs who use business features

**Q4: Business Filter Interaction**
- **Decision:** If business filter rejects account, skip female scoring entirely
- **Logic:** `if business_score > 70: female_score = None` (no score returned)
- **Rationale:** Avoid false positives from business accounts that happen to use female-coded language (e.g., "female-founded startup")

**Q5: Mixed Language Handling**
- **Decision:** Single scoring pool for English, Estonian, Russian
- **Thresholds per language:**
  - English: ≥3.0
  - Estonian: ≥2.7 (lower threshold due to smaller signal pool)
  - Russian: ≥2.9 (slightly lower due to linguistic variation)
- **Pooling:** All signals combined in one score; threshold applied at result time
- **Rationale:** Allows high-precision multi-language support without separate models

---

## Filtering Pipeline (3 Stages)

### Stage 1: Follower Range
- Minimum: 500 followers
- Maximum: 3,500 followers
- Rationale: Sweet spot for engaged, reachable audience

### Stage 2: Public + Non-Business
- Privacy filter: `is_private == false`
- Business filter: `business_score < 70` (3-layer detection: hard keywords, hashtag patterns, naming patterns)
- Processing: <50ms per profile, zero API calls, regex-only

### Stage 3: Female Signal
- Score all text (bio, username, name, recent captions)
- Apply language-specific threshold (EN≥3.0, ET≥2.7, RU≥2.9)
- Return score + confidence (confidence = highest single-tier score)
- Processing: <30ms per profile, regex-only

---

## Output Format

```json
{
  "username": "jane_fit_eesti",
  "full_name": "Jane",
  "followers": 1250,
  "female_score": 3.5,
  "female_confidence": "high",
  "business": false,
  "bio_preview": "Fitness coach | Outdoor living | Estonia",
  "crawled_at": "2026-06-05T19:33:11Z"
}
```

---

## Known Limitations

- **Pronoun-heavy accounts only:** If bio contains no gendered language, score will be <3.0 even if female
- **Business filter collision:** Female entrepreneurs who brand as "women-owned" will skip scoring
- **Language detection:** Assumes bio language matches account focus; mixed-language accounts score against all 3 pools
- **False negatives:** Minimal (regex conservative)
- **False positives:** ~5% at 3.0 threshold; ~15% at 3.5 threshold (acceptable trade-off for business recovery)

---

## Regex Patterns (Locked)

**Female pronouns:** `\b(she|her|hers)\b`  
**Gender nouns:** `\b(woman|girl|lady|female|mum|mom|womans|girls|females|mums|moms)\b`  
**Relationship:** `\b(sister|wife|daughter|nana|gran|sis|wifey|mummy)\b`  
**Generic:** `\b(blogger|babe|queen|goddess)\b`  

All case-insensitive, word-boundary matching.

---

**Referenced by:** `integration-architecture` (IG-1 Protocol section)  
**Last Updated:** June 5, 2026
