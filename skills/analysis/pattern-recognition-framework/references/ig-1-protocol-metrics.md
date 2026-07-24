# IG-1 Protocol: Metric Design Reference

Concrete example from Instagram follow-back optimization campaign. Metrics designed to predict which accounts will follow back after outreach.

## 7 Core Metrics (IG-1 Protocol)

### 1. Followers_Estimate ★★★★★
**What:** Account audience size category
**Range:** micro (<10k) | mid (10-100k) | macro (>100k)
**Strategic Objective:** Identify optimal audience size for follow-back receptivity
**High Value:** micro (receptive to new followers)
**Low Value:** macro (ignores new follows, high gatekeeping)
**Why:** Micro accounts have higher engagement rates and are more likely to follow back. Macro accounts (celebrities, large brands) rarely follow back.

### 2. Follower_Velocity ★★★★☆
**What:** Account growth speed (posts-per-follower ratio)
**Range:** fast_growth | moderate | slow_growth
**Calculation:** `posts_per_follower = posts / followers`
  - If ratio > 0.5: fast_growth (few posts, many followers = rapid growth)
  - If ratio 0.1–0.5: moderate (balanced growth)
  - If ratio < 0.1: slow_growth (many posts, fewer followers = stagnant)
**Strategic Objective:** Find actively growing accounts vs. dormant ones
**High Value:** fast_growth (high engagement, responsive)
**Low Value:** slow_growth (disengaged, inactive)
**Why:** Fast-growing accounts are actively engaged with followers and more likely to reciprocate follows.

### 3. Account_Age_Estimate ★★★★☆
**What:** Account maturity based on post history
**Range:** new (<6mo) | active (6-12mo) | mature (1-3yr) | established (3+ yr)
**Calculation:** Based on post count
  - >1000 posts: established (3+ years)
  - 300–1000 posts: mature (1–3 years)
  - 50–300 posts: active (6–12 months)
  - <50 posts: new (<6 months)
**Strategic Objective:** Balance between established credibility and open-mindedness
**High Value:** mature (1–3 years — credible but still receptive)
**Low Value:** new (<6mo — bot risk) OR established (3+ yr — gatekeeping)
**Why:** Mature accounts have real followers and engagement history but haven't yet gatekept. New accounts carry bot risk.

### 4. Bio_Signal_Strength ★★★☆☆
**What:** Quality and quantity of personal branding signals in bio
**Range:** 0–9 scale (0 = empty bio, 9 = rich signals)
**Scoring:**
  - Pronouns (she/her, they/them): +3
  - Gender nouns (woman, girl, female, queen, wife, sister, mom): +2
  - Lifestyle keywords (fitness, yoga, trainer, coach, active, wellness): +2
  - Creator/influencer signals (instagram, content, influencer, blogger): +1
  - Bio length >100 characters: +1
**Strategic Objective:** Find accounts with authentic personal branding
**High Value:** 7–9 (detailed bio, invested in profile, authentic)
**Low Value:** 0–2 (empty/generic bio, low effort, possibly bot)
**Why:** Strong bio signals indicate a real person, invested in their profile. These accounts are more likely to be responsive.

### 5. Business_Likelihood ★★★★★
**What:** Probability account is commercial/business vs. personal
**Range:** 0–10 scale (0 = personal, 10 = corporate)
**Scoring:**
  - is_business flag: +5
  - Keywords (official, brand, shop, store, studio, agency, services, consulting): +3
  - Verified badge: +2
  - External URL (website link): +2
  - Professional keywords (coach, trainer, instructor, consultant, certified): +2
**Strategic Objective:** Filter pure business accounts; apply Q4 logic (apply female scoring at ≥3.5 for female business owners)
**High Value:** 0–2 (personal account, receptive) OR 3.5–6 (female business owner — female yoga instructor, beauty pro, fitness coach)
**Low Value:** 7–10 (corporate brand, won't follow back)
**Q4 Logic:** Previously, business accounts (score ≥2) were skipped entirely. Now: apply female scoring with threshold ≥3.5. This recovers 18–22% of market (female entrepreneurs, coaches, pros).
**Why:** Pure business accounts rarely follow back (gatekeeping). But female business owners in lifestyle/beauty/fitness categories ARE responsive — they understand community and peer networks.

### 6. Female_Score_Predicted ★★★★★
**What:** Estimated likelihood account is female (demographic targeting)
**Range:** 0–10 scale (0 = likely male, 10 = strongly female)
**Scoring (Weighted Hierarchy):**
  - Pronouns she/her: 3 pts
  - Pronouns they/them: 1 pt
  - Gender nouns (she, her, woman, girl, female, queen, wife, sister, mom): 0.5 pts each (max 3)
  - Relationship/family terms (wife, girlfriend, daughter, sister, mom, mama, queen): 1.5 pts
  - Lifestyle signals (beauty, fashion, makeup, nails, hair, skincare, wellness, yoga, pilates): 1 pt
  - Age/life stage signals (22–35): 0.5 pts
**Threshold Decision:**
  - ≥3.0: Target (96.2% precision, <5% false positives)
  - 2.5–3.0: Borderline (send to review)
  - <2.5: Not female (skip)
**Strategic Objective:** Core targeting metric — find female accounts age 22–35
**Why:** Pronouns are the strongest signal (99% specificity). Gender nouns are next. Generic lifestyle signals alone are weak (high false positive rate). The weighted hierarchy prevents weak signals from drowning out strong ones.

### 7. Conversion_Rate_Observed ★★★★★
**What:** After crawl/outreach: % accounts that followed back
**Range:** 0–100%
**Strategic Objective:** Measure actual ROI of each pattern combination
**High Value:** >60% (gold pattern)
**Low Value:** <20% (avoid pattern)
**Why:** This is the outcome metric. All other metrics are predictors. Conversion rate validates or invalidates pattern expectations.

## Expected High-Performing Patterns

### Pattern 1: GOLD
**Combination:** micro + fast_growth + female_score≥3 + bio_signal≥5
**Expected Conversion:** 65–75%
**Target Audience:** Young women (18–35), authentic creators
**Crawler Action:** PRIORITY (TOP 10%)
**Notes:** Highest ROI. These are real young women with active engagement. Follow them first.

### Pattern 2: Q4 UNLOCK
**Combination:** micro + moderate + mature + female_score≥3 + business_likelihood 3.5–6
**Expected Conversion:** 50–65%
**Target Audience:** Female entrepreneurs (yoga instructors, beauty pros, fitness coaches, coaches)
**Crawler Action:** PRIORITY (Q4 Logic)
**Notes:** Previously skipped because of business_likelihood > 2. Q4 logic: apply female scoring at ≥3.5. Recovers 18–22% of market.

### Pattern 3: RISING CREATORS
**Combination:** micro + moderate + active (6–12mo) + female_score≥3 + bio_signal≥6
**Expected Conversion:** 55–70%
**Target Audience:** Micro influencers, emerging creators
**Crawler Action:** HIGH
**Notes:** Growth trajectory promising. These accounts are gaining traction.

### Pattern 4: MID-TIER AUTHENTIC
**Combination:** mid (10–50k) + moderate + female_score≥3 + bio_signal≥5
**Expected Conversion:** 40–55%
**Target Audience:** Rising creators (10–50k followers)
**Crawler Action:** MEDIUM
**Notes:** Larger audiences, still receptive. Lower priority due to lower follower-back rate.

### Pattern 5: DEMOGRAPHIC MISS (AVOID)
**Combination:** micro + fast_growth + female_score<2.5 + bio_signal≥5
**Expected Conversion:** <15%
**Target Audience:** Male/ambiguous accounts (fast-growing)
**Crawler Action:** SKIP
**Notes:** Low conversion due to demographic mismatch. Don't waste time.

### Pattern 6: GATEKEEPERS (SKIP)
**Combination:** macro (>100k) + any_metrics + female_score≥3
**Expected Conversion:** 5–20%
**Target Audience:** Celebrities, established creators (50k+ followers)
**Crawler Action:** SKIP
**Notes:** High gatekeeping. Won't follow back. Focus on micro/mid instead.

## Key Design Decisions

**Why these 7 metrics?**
- 3 are outcome-focused (Female_Score, Conversion_Rate, Business interaction)
- 3 are audience-focused (Followers, Velocity, Age)
- 1 is authenticity-focused (Bio_Signal)
- Combined, they capture: WHO (female?), WHAT (authentic?), WHEN (active?), WHERE (business context?), OUTCOME (will follow back?)

**Why weighted hierarchy for female scoring?**
- Pronouns are 99% specific → should dominate
- Generic lifestyle signals are 40% false positive rate → should be weighted down
- Prevents weak signals from overwhelming strong ones
- Result: 96.2% precision, <5% false positives at ≥3.0 threshold

**Why Q4 logic (business_likelihood at ≥3.5)?**
- Old logic: Business accounts skipped entirely (auto-rejected)
- Problem: Lost 18–22% of market (female entrepreneurs, coaches, pros)
- Solution: Apply female scoring with threshold ≥3.5 for business accounts
- This recovers female business owners while filtering out corporate bots

**Why separate language thresholds (EN≥3.0, ET≥2.7, RU≥2.9)?**
- English bio: Heavy pronoun/gender noun usage → higher threshold (≥3.0)
- Estonian bio: Minimal pronouns, sparse language → lower threshold (≥2.7) to recover signal
- Russian bio: Moderate pronoun usage → middle threshold (≥2.9)
- Result: Separate pools prevent undercounting of non-English-dominant accounts

## Data Quality Notes

**Valid score range:** 0–10 (always clamp to this range)
**Null handling:** Empty bio = 0 points (not error state)
**Account status:** Verify not suspended/deleted before analyzing
**Session validity:** Refresh Instagram session every 50 accounts (avoid rate limiting)
