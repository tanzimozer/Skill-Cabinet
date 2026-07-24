# Instagram Rate-Limiting & Quota Management

## Context
Instagram's public web interface (accessed via `requests` or Selenium) is heavily rate-limited. Fetching data for >500 handles requires careful quota management.

## Observed Behavior

### Rate Limits
- **Response code**: HTTP 429 (Too Many Requests)
- **Trigger threshold**: ~100–200 requests in quick succession (varies by IP, account age)
- **Reset window**: ~60 minutes (measured from first 429)
- **Retry-After header**: Instagram includes this, but not always accurate

### Safe Operating Parameters
- **Requests per batch**: 10–50 handles
- **Delay between requests**: 3–5 seconds (using `time.sleep()`)
- **Delay between batches**: 30 seconds
- **Parallelism**: None (single-threaded, sequential only)

**Safe speeds**:
- 50 handles: ~10 minutes (50 × 3 sec + 30 sec = 5 min request time + 5 min overhead)
- 500 handles: ~100 minutes (~1.5 hours)
- 2,000 handles: ~5 hours (too long; consider Option A/demo)

### What Triggers Rate-Limiting Faster
- Rapid requests to the same account (< 1 sec apart)
- Requests from rotating IPs (Instagram flags as bot activity)
- High request frequency without pauses
- Fetching multiple data points per account (bio, recent posts, follower trends)

## Mitigation Strategies

### Strategy 1: Reduce Scope
Instead of fetching full profile data:
- Fetch handle + follower count + bio only (1 request per handle)
- Skip recent posts, engagement metrics, posting frequency
- Reduces per-handle latency from ~2 sec to ~0.5 sec

### Strategy 2: Use Demo Mode for Validation
See `instagram-data-consolidation-pattern-analysis` skill:
- **Option A (Demo)**: Synthetic data, 50 handles, 5 minutes
  - Validates pattern framework end-to-end
  - No quota consumption
  - Good for testing prioritization logic before full analysis
- **Option B (Full)**: Real Instagram data, 1,975 handles, 2+ hours
  - Use after validating Option A
  - Accept quota limits as operational cost

### Strategy 3: Batch & Retry with Exponential Backoff
```python
import time

def fetch_with_backoff(url, max_retries=3):
    for attempt in range(max_retries):
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 429:
                wait_time = 60 * (2 ** attempt)  # 60s, 120s, 240s
                print(f"Rate limited. Waiting {wait_time}s...")
                time.sleep(wait_time)
                continue
            response.raise_for_status()
            return response
        except Exception as e:
            print(f"Attempt {attempt+1} failed: {e}")
            if attempt < max_retries - 1:
                time.sleep(5)
    return None
```

### Strategy 4: Cache Results
If re-running the same analysis:
- Save fetched data locally (JSON per batch)
- Resume from last completed batch, not from scratch
- Avoid re-fetching already-analyzed handles

## Decision: Demo vs Full Analysis

**Use Option A (Demo) if:**
- First time running this pattern analysis
- Want to validate the framework quickly
- Timeline is tight (<1 hour)
- Just testing crawl prioritization logic

**Use Option B (Full) if:**
- Pattern framework is validated
- Have 2+ hours available
- Need real data for final prioritization
- Plan to measure actual conversion rates (demo data won't predict real outcomes)

**Hybrid approach**:
1. Run Option A (demo, 5 min) to validate
2. Review pattern distribution and metrics
3. Run Option B (full, 2 hours) overnight
4. Compare demo distribution vs real distribution
5. Measure crawl performance against both

## Session-Specific Notes (Session: IG-1 Pattern Analysis)

**What happened:**
- Kicked off Option B (full 1,975 handles)
- After 30+ minutes, still at 0% completion
- Instagram rate-limiting kicked in
- User said "stop and proceed with A"

**Lesson**: Offer the demo first. Full analysis should be a conscious choice with time expectations. Don't auto-launch 2-hour jobs.

**What worked:**
- Demo mode (Option A) completed in ~60 sec
- Populated 50 handles with synthetic pattern data
- Framework validated without quota loss
- User could immediately see expected output and make informed decision
