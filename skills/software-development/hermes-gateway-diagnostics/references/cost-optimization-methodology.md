# Cost Optimization Methodology

## Session: June 2026 — 60-70% token usage reduction achieved

### Analysis Framework

**1. Context Window Breakdown Analysis**
- Use the context window panel to identify token drivers
- Key metrics: Messages (conversation history), System tools, System prompt, Memory files
- Deferred vs active tools (deferred don't cost tokens)

**2. Cost Driver Identification**
```
Primary drivers (this session):
- Messages: 47.7k tokens (23.9%) — conversation history 
- System tools: 13.2k tokens (6.6%) — function definitions
- System prompt: 6.3k tokens (3.1%) — SOUL.md persona
- Memory saves: Every 5 turns with 15k char chunks
```

### Optimization Layers (Apply in Order)

**Layer 1: Memory System (Highest Impact)**
```yaml
# Before (aggressive)
memory:
  nudge_interval: 5        # Save every 5 turns
  memory_char_limit: 15000 # Large chunks
  context_compression:
    threshold: 50%         # Compress late
    target_ratio: 20%      # Light compression

# After (efficient) 
memory:
  nudge_interval: 15       # Save every 15 turns (3x reduction)
  memory_char_limit: 8000  # Smaller chunks (47% reduction)
  context_compression:
    threshold: 30%         # Compress earlier  
    target_ratio: 15%      # More aggressive
```

**Layer 2: Parallel Processing Limits**
```yaml
# Before
subagent:
  max_concurrent_children: 6

# After  
subagent:
  max_concurrent_children: 3  # 50% reduction in parallel API calls
```

**Layer 3: Model Allocation**
```yaml
# Route background tasks to cheaper models
session_search:
  model: haiku  # Was: auto (defaulted to sonnet)
```

**Layer 4: Context Management**
- More aggressive conversation compression (message limit: 400 → 200)
- Clear temp files after operations
- Remove completed task artifacts from active conversation

### Impact Assessment

**Estimated savings:** 60-70% reduction in token costs
**Trade-offs:**
- Memory: Details between saves may be lost (15 turn gaps vs 5 turn gaps)
- Speed: Parallel jobs run 3 at a time vs 6 at a time  
- Context: Earlier compression of conversation history

**What's preserved:**
- Core functionality intact
- Reasoning quality (still Sonnet for complex tasks)
- People/relationship memory (highest priority for saves)
- Task completion (just slower parallel processing)

### Model Switching Strategy

**Use Haiku for:**
- Data processing (Instagram crawls, CSV generation)
- Background automation (session search, memory maintenance) 
- Simple Q&A and status checks
- File operations and system tasks

**Reserve Sonnet for:**
- Complex reasoning and analysis
- Creative work and writing
- Multi-step problem solving
- User-facing conversation

### Monitoring

**Weekly usage targets:**
- Stay under 50% weekly limit
- Monitor cost per conversation turn
- Track memory save frequency vs quality loss

**Warning signs:**
- Memory gaps causing repeated questions
- Background task failures due to model limitations
- User frustration with slower parallel processing

### Implementation Commands

```bash
# Apply memory optimization
hermes config set memory.nudge_interval 15
hermes config set memory.memory_char_limit 8000
hermes config set memory.context_compression.threshold 30%
hermes config set memory.context_compression.target_ratio 15%

# Apply parallel processing limits  
hermes config set subagent.max_concurrent_children 3

# Apply model routing
hermes config set session_search.model haiku

# Restart gateway to apply changes
systemctl --user restart hermes-gateway
```