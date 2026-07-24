# Latency Instrumentation for Submillisecond Precision

## Why Submillisecond Matters

Production systems care about latency percentiles, not just means. A 0.01ms average looks good until you realize the P99 is 10ms — that's 1-in-100 requests taking 1000x longer.

**Submillisecond precision** means:
- Measuring in **microseconds** (µs) internally, then converting to **milliseconds** (ms) for reporting
- Capturing **P95, P99, min, max** alongside mean
- Understanding **tail latency** (what the slowest 1% see)

## Collection Method

Use Python's `time.perf_counter()` — it gives wall-clock precision with minimal overhead:

```python
import time
import json

def measure_latency(func, args, iterations=100):
    """Measure latency with submillisecond precision."""
    latencies_ms = []
    
    for _ in range(iterations):
        start = time.perf_counter()
        result = func(*args)
        elapsed_us = (time.perf_counter() - start) * 1_000_000  # convert to microseconds
        latencies_ms.append(elapsed_us / 1000)  # convert to milliseconds
    
    return {
        "mean_ms": sum(latencies_ms) / len(latencies_ms),
        "min_ms": min(latencies_ms),
        "max_ms": max(latencies_ms),
        "p95_ms": sorted(latencies_ms)[int(len(latencies_ms) * 0.95)],
        "p99_ms": sorted(latencies_ms)[int(len(latencies_ms) * 0.99)],
        "stddev_ms": (sum((x - sum(latencies_ms)/len(latencies_ms))**2 for x in latencies_ms) / len(latencies_ms)) ** 0.5
    }
```

## Avoiding Common Mistakes

### ❌ Mistake 1: Using `time.time()` instead of `time.perf_counter()`

```python
# BAD: system clock adjustments cause errors
start = time.time()
result = function()
elapsed = time.time() - start  # can go negative if clock adjusts!
```

**FIX:**
```python
# GOOD: monotonic clock, immune to system clock adjustments
start = time.perf_counter()
result = function()
elapsed = (time.perf_counter() - start) * 1000  # ms
```

### ❌ Mistake 2: Too few samples (N < 30)

With N=10 samples, standard error dominates — P99 estimate is unreliable.

**FIX:** Run at least 100 iterations per measured function. For integration tests, run 50+ end-to-end cycles.

### ❌ Mistake 3: Not warming up the function

First call may include JIT compilation, cache misses, I/O delays. Results are outliers.

**FIX:**
```python
# Warm up (not measured)
for _ in range(10):
    func(*args)

# Now measure (N=100 iterations)
latencies = [measure_one_call(func, args) for _ in range(100)]
```

### ❌ Mistake 4: Measuring wall-clock latency in a multi-threaded system

Thread context switches introduce artificial variance.

**FIX:** For CPU-bound tests, run serially. For I/O-bound or concurrent tests, measure per-call latency, not wall-clock per-batch.

## Reporting Latency Metrics

**For executives/operations:**
```
Personality Checker Latency:  0.01ms (mean) ✓ Production-grade
Integration Pipeline:          0.38ms (end-to-end) ✓ Excellent
Framework ↔ JARVIS:           0.19ms ✓
EDITH ↔ Framework:            0.11ms ✓
```

**For developers/debugging:**
```
Personality Checker:
  Mean:    0.01ms
  P95:     0.02ms
  P99:     0.03ms
  Min:     0.005ms
  Max:     0.15ms
  Samples: 10,000
```

**As JSON (for dashboards):**
```json
{
  "metric": "personality_checker_latency",
  "timestamp": "2026-06-09T23:45:01Z",
  "unit": "ms",
  "mean": 0.01,
  "p95": 0.02,
  "p99": 0.03,
  "min": 0.005,
  "max": 0.15,
  "sample_count": 10000
}
```

## Interpreting Results

| P99 Latency | Implication | Action |
|-----------|-----------|--------|
| <1ms | Excellent. Production-ready. | No action. Monitor for regressions. |
| 1-10ms | Good. Acceptable for most systems. | Monitor tail. Set alert at 2x current. |
| 10-100ms | Acceptable if rare (only P99). Check P95. | Investigate. May indicate bottleneck. |
| 100ms+ | Poor. User-facing requests affected. | Find bottleneck. Refactor critical path. |

## Integration Test Latency

For end-to-end (EDITH ↔ Framework ↔ JARVIS) tests:

```python
def measure_integration_latency(input_data, iterations=50):
    """Measure full pipeline latency."""
    latencies = []
    
    for _ in range(iterations):
        start = time.perf_counter()
        # Full path: Application → JARVIS → Framework → EDITH → response
        result = application.process(input_data)
        elapsed_ms = (time.perf_counter() - start) * 1000
        latencies.append(elapsed_ms)
    
    return {
        "integration_latency_ms": {
            "mean": sum(latencies) / len(latencies),
            "p99": sorted(latencies)[int(len(latencies) * 0.99)]
        }
    }
```

**Expected baseline for JARVIS+Framework+EDITH:** <1ms mean, <5ms P99

If you see:
- Mean 0.38ms, P99 1.2ms → ✓ Excellent
- Mean 5ms, P99 50ms → ⚠ Bottleneck likely
- Mean 100ms, P99 500ms → ❌ Critical issue

## Tracking Regressions

Store baseline metrics in JSON with timestamp:

```json
{
  "test_run": "2026-06-09T23:45:01Z",
  "personality_checker": {
    "mean_ms": 0.01,
    "p99_ms": 0.03
  },
  "integration": {
    "mean_ms": 0.38,
    "p99_ms": 1.2
  }
}
```

Future runs compare against baseline:
```python
new_p99 = 0.04  # current
old_p99 = 0.03  # baseline
regression = (new_p99 - old_p99) / old_p99 * 100  # 33% regression

if regression > 10:  # alert if >10% degradation
    alert(f"P99 latency degraded {regression:.0f}%")
```

## Quick Validation

To verify your instrumentation is working:
```python
# Should take ~1 second
start = time.perf_counter()
time.sleep(1)
elapsed_ms = (time.perf_counter() - start) * 1000
assert 990 < elapsed_ms < 1010, f"Got {elapsed_ms}ms, expected ~1000ms"
print(f"✓ Instrumentation working. Precision: ±{abs(elapsed_ms - 1000)}ms")
```

If precision is ±10-50ms, you're on a slow system or there's background noise. That's okay for systems with >10ms baselines; not okay for submillisecond measurements.
