# MODULE_CACHE.json Specification

## Purpose
Cache module analysis to avoid re-analyzing unchanged files. Provides instant 95% confidence for unchanged modules.

## Structure
```json
{
  "version": "1.0",
  "modules": {
    "src/auth/auth.service.ts": {
      "hash": "sha256:abc123def456...",  // Content hash
      "analyzed_at": "2024-01-10T10:00:00Z",
      "analysis": {
        "imports": ["crypto", "jsonwebtoken", "./auth.repository"],
        "exports": ["AuthService", "authenticate", "validateToken"],
        "functions": ["authenticate", "validateToken", "refreshToken"],
        "classes": ["AuthService"],
        "complexity": 12,  // Cyclomatic complexity
        "lines": 245,
        "dependencies": {
          "internal": ["./auth.repository", "./auth.types"],
          "external": ["crypto", "jsonwebtoken"]
        }
      },
      "test_coverage": {
        "unit_tests": ["tests/auth.service.test.ts"],
        "integration_tests": ["tests/integration/auth.test.ts"],
        "e2e_tests": ["tests/e2e/login.test.ts"]
      }
    }
  }
}
```

## Usage in Conductor

### Phase 1A - Context Validation
```python
def validate_with_cache(file_path):
    current_hash = compute_hash(file_path)
    
    if file_path in cache['modules']:
        cached = cache['modules'][file_path]
        if cached['hash'] == current_hash:
            # Use cached analysis - instant confidence
            return {
                'confidence': 0.95,
                'source': 'cache',
                'analysis': cached['analysis']
            }
    
    # File changed or not cached - analyze fresh
    analysis = analyze_module(file_path)
    
    # Update cache
    cache['modules'][file_path] = {
        'hash': current_hash,
        'analyzed_at': now(),
        'analysis': analysis
    }
    
    return {
        'confidence': calculate_confidence(analysis),
        'source': 'fresh_analysis',
        'analysis': analysis
    }
```

### Cache Invalidation Rules
1. Hash mismatch → Re-analyze
2. File deleted → Remove from cache
3. Cache version change → Clear entire cache
4. Manual reset command → Clear cache

## Benefits
- **Speed**: 2-3 minutes saved per task on unchanged modules
- **Confidence**: Instant 95% confidence for cached modules  
- **Consistency**: Same analysis results for unchanged code
- **Transparency**: Can inspect cache to see what's analyzed

## Maintenance
- Cache file location: `.claude/MODULE_CACHE.json`
- Max size: 10MB (approximately 500 modules)
- Cleanup: Remove entries for non-existent files on each run
- Reset: Delete cache file to force fresh analysis