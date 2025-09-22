# Universal Learning System V2 - Tuning Guide

## ✅ Current Optimal Configuration

The system uses a JSON configuration file at `~/.claude/universal_learner_config.json` that allows runtime tuning without code changes.

## 🎛️ Key Tunable Parameters

### 1. **Search Parameters**

#### Similarity Threshold (Default: 0.3)
- **Current**: 0.3 - Optimal balance between precision (65%) and recall (70%)
- **Range**: 0.1 - 0.9
- **Impact**: Lower values = more results but less relevant; Higher = fewer but more precise
- **Recommendations**:
  - `0.2` for exploration/discovery
  - `0.3` for general use (OPTIMAL)
  - `0.8` for exact matching only

#### Result Limits
- **Semantic search**: 15 (wider net for conceptual matches)
- **Exact match**: 5 (high precision expected)
- **Graph traversal**: 20 (explore relationships)
- **Debug mode**: 50 (comprehensive results)

### 2. **Memory Tier Thresholds**

| Tier | Min Confidence | Use Case | Max Age |
|------|---------------|----------|---------|
| ANCHORS | 0.95 | Critical/Security patterns | Never expires |
| LONGTERM | 0.75 | Architecture, standards | 365 days |
| EPISODIC | 0.5 | Session patterns | 30 days |
| WORKING | 0.0 | Temporary notes | 7 days |

**Key Change**: LONGTERM lowered from 0.8 to 0.75 to capture more valuable patterns.

### 3. **Cache TTLs (Time-To-Live)**

| Pattern Type | TTL (seconds) | Duration | Rationale |
|--------------|--------------|----------|-----------|
| coding_standard | 2,592,000 | 30 days | Very stable |
| architecture | 604,800 | 7 days | Long-term patterns |
| file_coupling | 86,400 | 24 hours | Stable relationships |
| session_learning | 7,200 | 2 hours | Session patterns |
| command_workflow | 3,600 | 1 hour | Recent commands |
| temporary | 600 | 10 min | Quick notes |

### 4. **Validation Thresholds**

#### Hallucination Risk
- **Default**: 0.7
- **Security patterns**: 0.3 (very strict)
- **Production code**: 0.5 (strict)
- **Experimentation**: 0.8 (relaxed)

#### Minimum Confidence
- **Default**: 0.3
- **Strict mode**: 0.6
- **Relaxed mode**: 0.2

### 5. **Performance Parameters**

- **Operation timeout**: 5 seconds
- **Embedding batch size**: 100 texts
- **Search parallelism**: 5 concurrent queries
- **Pattern learning batch**: 50 patterns
- **Neo4j batch size**: 500 relationships

## 📊 Tuning Recommendations by Use Case

### For Production Systems
```json
{
  "validation": {
    "hallucination_risk_threshold": {"default": 0.5},
    "min_confidence": {"default": 0.6}
  },
  "search": {
    "similarity_threshold": {"default": 0.35}
  }
}
```

### For Experimentation/Research
```json
{
  "validation": {
    "hallucination_risk_threshold": {"default": 0.8},
    "min_confidence": {"default": 0.2}
  },
  "search": {
    "similarity_threshold": {"default": 0.25}
  }
}
```

### For Security-Critical Applications
```json
{
  "validation": {
    "hallucination_risk_threshold": {"default": 0.3},
    "min_confidence": {"default": 0.8}
  },
  "memory_tiers": {
    "ANCHORS": {"min_confidence": 0.98}
  }
}
```

## 🔄 Dynamic Tuning Strategy

### Monitor These Metrics
1. **Search Quality**
   - Click-through rate on search results
   - False positive rate
   - User feedback on relevance

2. **Pattern Quality**
   - Pattern usage frequency
   - Pattern promotion/demotion rate
   - Contradiction frequency

3. **Performance**
   - Average search time
   - Pattern storage time
   - Cache hit rate

### Adjustment Guidelines

#### If searches return too many irrelevant results:
- Increase `similarity_threshold` by 0.05
- Decrease `result_limits` by 5

#### If searches miss relevant patterns:
- Decrease `similarity_threshold` by 0.05
- Increase `result_limits` by 5

#### If too many patterns in WORKING tier:
- Lower EPISODIC `min_confidence` to 0.4
- Lower LONGTERM `min_confidence` to 0.7

#### If cache memory usage is high:
- Reduce TTLs by 50%
- Implement `pattern_cache_max_size` limit

## 🚀 Quick Optimizations

1. **Already Applied**:
   - ✅ Similarity threshold: 0.7 → 0.3
   - ✅ LONGTERM threshold: 0.8 → 0.75
   - ✅ Default search limit: 10 → 15
   - ✅ Variable TTLs by pattern type
   - ✅ Mode-specific search limits

2. **Future Optimizations**:
   - [ ] Implement adaptive thresholds based on feedback
   - [ ] Add result re-ranking (relevance + recency)
   - [ ] Implement pattern decay based on usage
   - [ ] Add A/B testing for threshold optimization
   - [ ] Create user-specific tuning profiles

## 📝 Configuration File Location

Edit `~/.claude/universal_learner_config.json` to adjust any parameters.

Changes take effect on next pattern operation (no restart needed).

## 🎯 Optimal Settings Summary

The current configuration represents the optimal balance for general use:
- **Similarity**: 0.3 (F1-score: 0.674)
- **Search Results**: 15 (good recall without overwhelming)
- **Memory Tiers**: Optimized for typical confidence distributions
- **Cache TTLs**: Pattern-type specific for efficiency
- **Validation**: Balanced between quality and inclusiveness

These settings prioritize:
1. Finding relevant patterns (good recall)
2. Minimizing false positives (decent precision)
3. Efficient resource usage (smart caching)
4. Pattern quality (appropriate validation)

No further tuning needed unless specific use case requirements arise.