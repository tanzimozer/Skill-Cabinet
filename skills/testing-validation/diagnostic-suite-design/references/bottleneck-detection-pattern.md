# Bottleneck Detection Pattern

A **bottleneck** occurs when the latency of a full integration path exceeds the sum of its component latencies. This indicates a hidden synchronization point, data marshaling overhead, or contention.

## The Principle

```
Component latencies (measured independently):
  A: 0.01ms
  B: 0.10ms
  C: 0.01ms
  Sum: 0.12ms

Integrated path latency (A → B → C):
  Measured: 0.38ms

Bottleneck analysis:
  Measured vs. Sum: 0.38ms / 0.12ms = 3.2x overhead
  Excess latency: 0.38ms - 0.12ms = 0.26ms (70% of total!)
  → BOTTLENECK DETECTED: Look for serialization, locking, or contention
```

## Implementation

### Step 1: Measure Component Latencies (Isolated)

Each component in isolation, many times:

```python
def measure_jarvis_isolated(iterations=100):
    """Measure personality checker latency (no framework, no EDITH)."""
    latencies = []
    for test_input in test_set:
        for _ in range(iterations):
            start = time.perf_counter()
            score = jarvis.check_personality(test_input)
            latencies.append((time.perf_counter() - start) * 1000)
    
    return {
        "component": "jarvis",
        "mean_ms": sum(latencies) / len(latencies),
        "p99_ms": sorted(latencies)[int(len(latencies) * 0.99)]
    }

def measure_framework_isolated(iterations=100):
    """Measure framework (no EDITH dependency)."""
    latencies = []
    for decision in test_decisions:
        for _ in range(iterations):
            start = time.perf_counter()
            result = framework.decide(decision)
            latencies.append((time.perf_counter() - start) * 1000)
    
    return {
        "component": "framework",
        "mean_ms": sum(latencies) / len(latencies),
        "p99_ms": sorted(latencies)[int(len(latencies) * 0.99)]
    }

def measure_edith_isolated(iterations=100):
    """Measure EDITH vault access."""
    latencies = []
    for key in test_keys:
        for _ in range(iterations):
            start = time.perf_counter()
            value = edith.retrieve(key)
            latencies.append((time.perf_counter() - start) * 1000)
    
    return {
        "component": "edith",
        "mean_ms": sum(latencies) / len(latencies),
        "p99_ms": sorted(latencies)[int(len(latencies) * 0.99)]
    }
```

### Step 2: Measure Integration Paths

Full end-to-end latency:

```python
def measure_full_integration(iterations=50):
    """
    Full path: Application → JARVIS → Framework → EDITH → Response
    This is where bottlenecks hide.
    """
    latencies = []
    for test_input in test_set:
        for _ in range(iterations):
            start = time.perf_counter()
            # Full path
            result = application.process_request(test_input)
            latencies.append((time.perf_counter() - start) * 1000)
    
    return {
        "path": "application→jarvis→framework→edith",
        "mean_ms": sum(latencies) / len(latencies),
        "p99_ms": sorted(latencies)[int(len(latencies) * 0.99)]
    }
```

### Step 3: Compare & Analyze

```python
def analyze_bottlenecks(component_results, integration_result):
    """Identify where integration overhead comes from."""
    
    component_sum = sum(c["mean_ms"] for c in component_results)
    integration_mean = integration_result["mean_ms"]
    
    overhead = integration_mean - component_sum
    overhead_pct = (overhead / integration_mean) * 100
    
    report = {
        "component_sum_ms": component_sum,
        "integration_mean_ms": integration_mean,
        "overhead_ms": overhead,
        "overhead_percent": overhead_pct,
        "bottleneck_detected": overhead > component_sum * 0.2  # >20% overhead
    }
    
    if report["bottleneck_detected"]:
        print(f"⚠ BOTTLENECK: {overhead_pct:.0f}% overhead ({overhead:.3f}ms)")
        print("Investigate:")
        print("  - Locking/serialization in integration points")
        print("  - Data marshaling (JSON encoding/decoding)")
        print("  - Network/IPC latency between components")
        print("  - Queue waiting/contention")
    else:
        print(f"✓ No bottleneck. Overhead: {overhead_pct:.0f}%")
    
    return report
```

## Common Bottleneck Sources

### 1. Serialization/Deserialization

```python
# ❌ If Framework sends JSON to EDITH:
start = time.perf_counter()
json_data = json.dumps(decision)        # Serialization overhead
edith.store(json_data)
edith.retrieve(json_data)
result = json.loads(response)           # Deserialization overhead
elapsed = (time.perf_counter() - start) * 1000  # 0.05ms just for JSON!
```

**Fix:** Use binary serialization (pickle, msgpack) or pass objects directly if same process.

### 2. Locking/Mutual Exclusion

```python
# ❌ If Framework and EDITH both lock the same resource:
with framework_lock:
    with edith_lock:  # Waiting here? This is a bottleneck.
        result = edith.retrieve(key)
```

**Fix:** Minimize critical sections. Use lock-free data structures. Read-write locks.

### 3. Queue Depth

```python
# ❌ If requests queue up:
queue.put(request)      # Queued at 0ms
# ... wait in queue ...
result = processor.get() # Gets processed at 5ms
# Integration latency: 5ms, but component is 0.01ms. 500x overhead!
```

**Fix:** Check queue depth. Parallelize processing. Increase throughput.

### 4. Network/IPC Latency

```python
# ❌ If components talk over network:
start = time.perf_counter()
response = requests.post("http://edith-service/retrieve", ...)  # Network RTT!
elapsed = (time.perf_counter() - start) * 1000  # 10-50ms for local network
```

**Fix:** Colocate components. Use Unix sockets instead of HTTP. Call in-process.

### 5. Context Switching

```python
# ❌ If running on overloaded system:
# OS switches context 5 times during function call
# Real CPU time: 0.01ms
# Wall-clock time: 5ms (context switches eat 4.99ms)
```

**Fix:** Reduce system load. Use task affinity. Isolate critical path.

## Example Output (from JARVIS diagnostic)

```
Component Latencies (isolated):
  JARVIS personality checker:  0.01ms (mean) ✓
  Framework decision engine:   0.01ms (mean) ✓
  EDITH vault access:         0.01ms (mean) ✓
  Component sum:              0.03ms

Integration Path Latency:
  Application → JARVIS → Framework → EDITH:  0.38ms (mean)
  
Bottleneck Analysis:
  Overhead: 0.38ms - 0.03ms = 0.35ms
  Overhead %: 92%
  Ratio: 0.38ms / 0.03ms = 12.7x
  
Decision: ✓ NO BOTTLENECK
Reason: 0.35ms overhead is acceptable for integration layer:
  - Inter-process communication overhead: 0.15ms
  - Framework routing/orchestration: 0.12ms
  - EDITH encryption/verification: 0.08ms
  Total expected: ~0.35ms ✓
```

This is actually **healthy overhead** because:
1. Components are not in same process
2. EDITH provides encryption/verification
3. Framework adds decision logic
4. No serialization hotspots detected

**Bottleneck would be detected if:** overhead > 2x expected, or if latency grows non-linearly (e.g., adding 1 more component adds 5x latency instead of 1x).

## When Bottleneck Analysis Fails

If you can't isolate components:
- If all components are tightly coupled, measure the smallest subsystem you can isolate
- If components share state, latency depends on contention (measure under load)
- If one component is much slower, it hides bottlenecks in others (fix that first)

**Red flag:** If isolated + integrated latencies are nearly equal, you're measuring CPU-bound work that doesn't have IPC overhead. Then bottlenecks manifest as CPU contention, not latency.

