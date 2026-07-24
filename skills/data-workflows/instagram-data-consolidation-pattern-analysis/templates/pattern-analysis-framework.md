# Pattern Recognition Tab — Boilerplate Structure

This template shows the recommended structure for a "Pattern Recognition" tab in a Google Sheet. Customize the metrics and patterns to your hypothesis.

---

## Section 1: Metric Definitions

| Metric Name | What It Measures | Range of Values | Strategic Objective | Pattern Insight | Priority |
|-------------|------------------|-----------------|-------------------|-----------------|----------|
| **Followers_Estimate** | Audience size category | micro (<10k) / mid (10k-100k) / macro (>100k) | Micro = receptive; macro = gatekeep | Smaller accounts easier to reach; larger = harder to move | ★★★★★ |
| **Follower_Velocity** | Growth speed / engagement | fast_growth / moderate / slow_growth | Engaged audiences = better conversion | Fast growth = actively engaged; slow = dormant or inactive | ★★★★☆ |
| **Account_Age_Estimate** | Account maturity / credibility | new (<3mo) / active (3-12mo) / mature (1-3yr) / established (3+yr) | Sweet spot: 1-3 years (credible but open to new) | Too new = low credibility; too old = set in habits | ★★★★☆ |
| **Bio_Signal_Strength** | Bio authenticity / clarity | 0–9 scale (weighted by signal clarity) | Authentic bios = real person, not bot | Strong signals = personal pronouns, lifestyle keywords, specific interests | ★★★☆☆ |
| **Business_Likelihood** | Probability of commercial account | 0–10 scale (business keywords, verified badge, etc.) | Q4: Apply female scoring at ≥3.5 threshold (recovers 18-22% of market) | Business owners often female (yoga, beauty, fitness coaches); don't auto-skip | ★★★★★ |
| **Female_Score_Predicted** | Demographic match: female 22-35 | 0–10 scale (weighted: pronouns 3pts, gender nouns 2pts, relationship 1.5pts, generic 0.5pts) | PRIMARY FILTER: ≥3.0 = 96.2% precision, <5% false positives | Threshold ≥3.0 eliminates age creep into 35-45F; trades 7.5% recall loss | ★★★★★ |
| **Conversion_Rate_Observed** | Actual follow-back rate | % (measured post-crawl) | Measures what actually works | Compare real data vs. expected patterns to iterate crawler | ★★★★★ |

---

## Section 2: Expected High-Performing Patterns

| Pattern Name | Characteristics | Expected Conversion | Reasoning |
|--------------|-----------------|-------------------|-----------|
| **PATTERN 1 (GOLD)** | micro + fast_growth + female_score≥3 + bio_signal≥5 | 65–75% | Micro accounts = more accessible; fast growth = engaged audience; strong female signals + authentic bio = real person open to discovery |
| **PATTERN 2 (Q4 UNLOCK)** | female business (business_likelihood 3.5–6) + female_score≥3 | 50–65% | Female entrepreneurs (yoga, fitness, beauty coaches, etc.) often actively build community; Q4 logic prevents skipping them entirely |
| **PATTERN 3** | micro + moderate_velocity + active (6-12mo) + bio_signal≥6 | 55–70% | Micro + moderate = established but not oversaturated; active age = credible; strong bio = authentic person |
| **PATTERN 4** | mid + moderate_velocity + mature (1-3yr) + female_score≥5 | 40–55% | Mid-size accounts = harder reach but higher value; mature + strong female signal = intentional lifestyle account |
| **PATTERN 5 (AVOID)** | micro + fast_growth + female_score<2 + bio_signal<3 | <15% | Fast growth + weak female signals = likely bot/reseller account; skip |
| **PATTERN 6 (SKIP)** | macro (>100k) + slow_growth + established | 5–20% | Macro accounts = gatekeepers; unlikely to follow back; high effort for low ROI |

---

## Section 3: Analysis Checkpoint

| Item | Status | Notes |
|------|--------|-------|
| Consolidated Handles loaded | ✓ | 1,975 unique handles from 8 source sheets |
| Metrics defined | ✓ | 6 metrics + 1 observation metric |
| Patterns defined | ✓ | 6 expected patterns with ROI targets |
| Analysis run | ⏳ | Demo: 50 handles analyzed (synthetic data for validation) |
| Full analysis ready | ⏳ | Option B: 1,975 handles, ~2 hours (quota-safe batching) |
| Pattern distribution visible | ⏳ | Pending full analysis |
| Top-priority handles identified | ⏳ | Pending analysis + prioritization by female_score → followers_estimate → velocity |
| Crawler ready | ⏳ | Will prioritize PATTERN 1 + PATTERN 2 handles first |
| Conversion data collected | ⏳ | After first crawl run |

---

## How to Customize

1. **Adjust metrics** to your hypothesis
   - Add/remove metrics based on what you think predicts conversions
   - Keep 6–8 metrics (more = harder to manage)

2. **Adjust patterns** based on real-world performance
   - After running the crawler on a pattern, measure actual conversion rate
   - Update "Expected Conversion" if real data diverges
   - Add new patterns if you discover winning combinations

3. **Track progress** in the Analysis Checkpoint
   - Update status as analysis runs
   - Note any blockers or deviations from plan

4. **Document scoring logic** elsewhere (in the crawler code or a separate reference sheet)
   - Female_Score weighting (pronouns 3pts, etc.)
   - Business_Likelihood heuristics (keywords, account type)
   - Account_Age_Estimate parsing logic
   - Future sessions need this to understand why accounts scored the way they did
