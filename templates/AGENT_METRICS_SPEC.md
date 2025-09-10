# AGENT_METRICS.json Specification

## Purpose
Track agent performance to detect degradation patterns and optimize orchestration efficiency.

## Structure
```json
{
  "version": "1.0",
  "last_analysis": "2024-01-10T10:00:00Z",
  "degradation_threshold": 0.3,
  "agents": {
    "architecture-planner": {
      "performance_baseline": {
        "simple": {
          "p50_duration": 60,    // Median duration in seconds
          "p90_duration": 90,    // 90th percentile
          "expected_files": "1-5"
        },
        "medium": {
          "p50_duration": 120,
          "p90_duration": 180,
          "expected_files": "6-20"
        },
        "complex": {
          "p50_duration": 240,
          "p90_duration": 360,
          "expected_files": "20+"
        }
      },
      "recent_runs": [
        {
          "task_id": "auth_refactor_20240110",
          "timestamp": "2024-01-10T10:00:00Z",
          "complexity": "medium",
          "file_count": 12,
          "duration": 115,
          "success": true,
          "retries": 0,
          "normalized_score": 0.96,  // 115/120 = good
          "tokens_used": 15000
        }
      ],
      "degradation_indicators": {
        "consecutive_failures": 0,
        "retry_rate": 0.1,        // 10% of runs need retry
        "timeout_rate": 0.0,
        "incomplete_rate": 0.0,
        "performance_ratio": 0.95  // Current vs baseline
      },
      "degradation_score": 0.05,  // 0=healthy, 1=critical
      "status": "healthy"  // healthy|degrading|critical
    }
  },
  "alerts": []
}
```

## Degradation Detection

### Complexity Classification
```python
def classify_complexity(task):
    file_count = len(task.affected_files)
    
    if file_count <= 5:
        return "simple"
    elif file_count <= 20:
        return "medium"
    else:
        return "complex"
```

### Performance Normalization
```python
def calculate_normalized_score(agent, task_result):
    complexity = classify_complexity(task_result)
    baseline = agent.performance_baseline[complexity]
    
    # Normalize against p50 (median expected time)
    normalized = task_result.duration / baseline.p50_duration
    
    # Score interpretation:
    # < 0.8  = Excellent (20% faster than baseline)
    # 0.8-1.2 = Normal
    # 1.2-1.5 = Slow but acceptable
    # > 1.5  = Concerning (50% slower)
    
    return normalized
```

### Degradation Scoring
```python
def calculate_degradation_score(agent):
    score = 0.0
    
    # Check recent performance trend
    recent_3 = agent.recent_runs[-3:]
    if all(run.normalized_score > 1.5 for run in recent_3):
        score += 0.3  # Consistently slow
    
    # Check failure patterns
    if agent.degradation_indicators.consecutive_failures >= 3:
        score += 0.4  # Multiple failures
    
    # Check retry rate
    if agent.degradation_indicators.retry_rate > 0.3:
        score += 0.2  # High retry rate
    
    # Check timeout rate
    if agent.degradation_indicators.timeout_rate > 0.1:
        score += 0.1  # Timeouts occurring
    
    return min(score, 1.0)  # Cap at 1.0
```

## Alert Generation

Alerts are generated when:
- Degradation score > 0.3 (configurable threshold)
- 3+ consecutive failures
- Performance ratio > 2.0 (twice as slow as baseline)

Alert format:
```json
{
  "agent": "architecture-planner",
  "severity": "warning|critical",
  "message": "Agent showing degradation: 3 consecutive failures",
  "recommendation": "Check context overflow or agent prompts",
  "timestamp": "2024-01-10T10:00:00Z"
}
```

## Usage in Conductor

### Recording Metrics
After each agent completes:
```python
def record_agent_metrics(agent_name, task_result):
    metrics = load_json('.claude/AGENT_METRICS.json')
    
    agent = metrics['agents'].get(agent_name, create_new_agent())
    
    # Add run data
    agent['recent_runs'].append({
        'task_id': task_result.id,
        'timestamp': now(),
        'complexity': classify_complexity(task_result),
        'file_count': len(task_result.files),
        'duration': task_result.duration,
        'success': task_result.success,
        'retries': task_result.retries,
        'normalized_score': calculate_normalized_score(agent, task_result),
        'tokens_used': task_result.tokens
    })
    
    # Keep only last 20 runs
    agent['recent_runs'] = agent['recent_runs'][-20:]
    
    # Update indicators
    update_degradation_indicators(agent)
    
    # Calculate degradation score
    agent['degradation_score'] = calculate_degradation_score(agent)
    
    # Set status
    if agent['degradation_score'] > 0.7:
        agent['status'] = 'critical'
    elif agent['degradation_score'] > 0.3:
        agent['status'] = 'degrading'
    else:
        agent['status'] = 'healthy'
    
    save_json('.claude/AGENT_METRICS.json', metrics)
```

### Analyzing Performance (Phase 6)
```python
def analyze_agent_performance():
    metrics = load_json('.claude/AGENT_METRICS.json')
    
    alerts = []
    for agent_name, agent_data in metrics['agents'].items():
        if agent_data['status'] != 'healthy':
            alerts.append({
                'agent': agent_name,
                'status': agent_data['status'],
                'score': agent_data['degradation_score'],
                'recent_performance': agent_data['recent_runs'][-3:]
            })
    
    if alerts:
        print("WARNING: Agent degradation detected:")
        for alert in alerts:
            print(f"  - {alert['agent']}: {alert['status']} (score: {alert['score']})")
            print(f"    Recent runs slower by: {alert['recent_performance']}")
            print(f"    Recommendation: Check for context overflow or complex prompts")
    
    metrics['last_analysis'] = now()
    metrics['alerts'] = alerts
    save_json('.claude/AGENT_METRICS.json', metrics)
```

## Baseline Calibration

Initial baselines can be set manually or learned:
```python
def calibrate_baseline(agent_name):
    """Run after 10+ successful tasks to establish baseline"""
    
    agent = metrics['agents'][agent_name]
    runs_by_complexity = group_by_complexity(agent['recent_runs'])
    
    for complexity, runs in runs_by_complexity.items():
        if len(runs) >= 5:
            durations = [r['duration'] for r in runs if r['success']]
            agent['performance_baseline'][complexity] = {
                'p50_duration': percentile(durations, 50),
                'p90_duration': percentile(durations, 90)
            }
```

## Benefits

1. **Early Warning**: Detect degradation before complete failure
2. **Performance Optimization**: Identify slow agents for tuning
3. **Resource Management**: Track token usage patterns
4. **Quality Assurance**: Ensure consistent agent performance
5. **Debugging Aid**: Historical data for troubleshooting