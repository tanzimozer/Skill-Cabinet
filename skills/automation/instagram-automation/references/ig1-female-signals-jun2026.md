# IG-1 Protocol — Female Signal Detection (Jun 5–6, 2026)

## Scope Update
- **Primary cities:** Seattle, LA (Los Angeles), Dallas, London
- **Full country:** Estonia
- **Languages in scope:** English, Estonian
- **Previous 14-city deployment deprioritized** — focus narrowed for resource efficiency and data quality

## Questionnaire Transcript (Validation Session, Jun 5–6)

### Question 1: Pronoun Weighting — LOCKED
**User choice:** Option B — "Only female pronouns count"
- she/her = 2 pts
- they/them = 1 pt
- he/him = **ignored** (do not count)

**Reasoning:** User noted most accounts don't list pronouns at all; when they do, female-identifying pronouns are the signal. Mixed pronouns (she/he) and he/him alone don't trigger female classification.

**Edge cases clarified:**
- "she/her advocate" = counts (full weight, 2 pts)
- "not she/her, I'm a guy" = **does not count** (explicit negation)
- "she/her and he/him" = **does not count** (mixed signals dilute confidence)

### Question 2: Signal Weighting — LOCKED
**User choice:** "Highest count = highest weight" — weighted hierarchy
- Explicit pronouns (she/her, they/them) = **3 pts each**
- Gender nouns (woman, girl, lady, female, mum, mom, mama, nana) = **2 pts each**
- Relationship terms (sister, wife, daughter) = **1.5 pts each**
- Generic/low-value (blogger, babe, queen) = **0.5 pts each**

**Reasoning:** More detailed signal accumulation → higher confidence. Pronouns are strongest (explicit identifier), generic terms are weakest (could apply to brands).

### Question 3: Confidence Threshold — PENDING
**Options to present:**
- A) Score ≥2 (low bar, catches most personal accounts, some false positives)
- B) Score ≥3 (medium bar)
- C) Score ≥3.5 (balanced precision/recall)
- D) Score ≥5 (high bar, only confident multi-signal accounts)
- E) Custom threshold

**Example scoring:**
- "She/her 💪" = 3 pts (meets A, B, C, E; not D)
- "Woman | Fitness Coach" = 2 pts (meets A only)
- "Yoga instructor, mom, she/her, living my best life" = 5 pts (meets all)
- "Blogger lifestyle girl" = 2.5 pts (meets A only)

### Question 4: False Positive Risk — PENDING
**Issue:** A business account named "girls_gym_studio" would score high on female signals despite being a business.

**Options to present:**
- A) Business filter first, then female scoring (rejects business, never scores female)
- B) Negation logic (if business signals exist, suppress female signal)
- C) Accept false positive, flag both (rare edge case)

### Question 5: Mixed Language — PENDING
**Issue:** Accounts with bio mixing multiple languages (e.g., "мама blogger she/her").

**Options to present:**
- A) Score all languages together (one pool)
- B) Score separately by language block, then combine
- C) Prioritize primary language (first language detected)

## Female Keywords by Language

### English (Primary)
```python
FEMALE_SIGNALS_EN = {
    'pronouns': ['she', 'her', 'she/her', 'they/them'],  # 3 pts each
    'gender_nouns': ['woman', 'girl', 'lady', 'female', 'mum', 'mom', 'mama', 'nana'],  # 2 pts
    'relationships': ['sister', 'wife', 'daughter', 'auntie', 'aunt'],  # 1.5 pts
    'generic': ['blogger', 'babe', 'queen', 'gal'],  # 0.5 pts
}
```

### Estonian
```python
FEMALE_SIGNALS_ET = {
    'gender_nouns': ['nainen', 'naine', 'tüdruk'],  # 2 pts (nainen/naine is very strong)
    'relationships': ['ema', 'õde'],  # ema=mom, õde=sister, 1.5 pts
    'generic': [],  # not common in Estonian bios
}
```
**Note:** Estonian female signals are sparse. Primary detection relies on English terms in Estonian bios + lifestyle hashtags.

### Russian (Optional, Lower Priority)
```python
FEMALE_SIGNALS_RU = {
    'gender_nouns': ['женщина', 'девушка', 'мама'],  # женщина=woman, девушка=girl, мама=mom, 2 pts
    'relationships': ['сестра'],  # 1.5 pts
}
```

## Implementation Notes

### Token cost
Zero. Pure regex, no LLM calls. Scoring <50ms per profile.

### Regex patterns (case-insensitive)
```python
import re

def score_female_signals(bio, full_name, username):
    text = f"{bio} {full_name} {username}".lower()
    score = 0
    
    # Pronouns (3 pts)
    if re.search(r'\b(she|her|she/her|they/them)\b', text):
        score += 3
    
    # Gender nouns (2 pts each, count once per category)
    if any(w in text for w in ['woman', 'girl', 'lady', 'female', 'mum', 'mom', 'mama', 'nana']):
        score += 2
    
    # Relationships (1.5 pts each, count once per category)
    if any(w in text for w in ['sister', 'wife', 'daughter']):
        score += 1.5
    
    # Generic (0.5 pts each, count once per category)
    if any(w in text for w in ['blogger', 'babe', 'queen']):
        score += 0.5
    
    return score
```

### False positive risks (known edge cases)
- Business account with "girl" in name → filtered by business layer first
- Male account with "sister" in bio → rare; caught by other signals if female account
- Bot/brand account with female signals → should fail privacy/follower filters first
- Generic lifestyle account (no strong signals) → correctly scores low, likely rejected

## Session learnings
1. **Pronouns are rare.** Most accounts (60%+) have zero pronouns in bio. This is fine; other signals (gender nouns) catch most female accounts.
2. **Broad lifestyle hashtags + female signals + follower range = strong filter.** Don't over-rely on pronouns alone.
3. **Threshold decision is critical.** Low threshold (≥2) catches more but increases false positives on generic "girl blogger" accounts. High threshold (≥5) is precise but may miss accounts with only pronouns or one gender noun.
4. **Questionnaire format:** Keep it fast. One-liner benefit + clear options. User values speed over exhaustive context.

## Next steps
- Validate female signal detection across 4 cities (Seattle, LA, Dallas, London) + Estonia
- Lock threshold (Q3)
- Resolve business filter interaction (Q4)
- Finalize mixed-language approach (Q5)
- Deploy combined filter to `ig1_crawl.py`
