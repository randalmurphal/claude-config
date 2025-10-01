# /index Slash Command

## Overview
Comprehensive codebase indexing command that leverages PRISM MCP for intelligent pattern recognition and memory storage.

## Command Structure
```
/index <codebase_path> [options]
```

## Parameters
- `<codebase_path>` (REQUIRED): Absolute path to the codebase to index
- `--resume` (OPTIONAL): Resume a previously interrupted indexing process
- `--auto-accept` (OPTIONAL): Automatically accept default indexing settings
- `--modules` (OPTIONAL): Specify specific modules to index (comma-separated)

## Indexing Workflow (5 Phases)

### Phase 1: Codebase Discovery
- Scan directory structure
- Identify programming languages
- Map dependency trees
- Generate initial file inventory

### Phase 2: Semantic Analysis
- Extract semantic tokens
- Generate embeddings for code segments
- Create graph representations
- Detect architectural patterns

### Phase 3: Memory Mapping
- Store semantic tokens in Qdrant vector database
- Create relationship graph in Neo4j
- Tag code segments with contextual metadata
- Prepare for intelligent retrieval

### Phase 4: Pattern Recognition
- Detect coding conventions
- Identify recurring architectural patterns
- Learn project-specific style guidelines
- Extract implicit design rules

### Phase 5: Validation & Optimization
- Cross-validate semantic mappings
- Optimize memory storage
- Generate indexing report
- Prepare for future intelligent retrieval

## Usage Examples
```bash
# Basic indexing
/index /home/user/project/my_repository

# Resume interrupted indexing
/index /home/user/project/my_repository --resume

# Auto-accept defaults
/index /home/user/project/my_repository --auto-accept

# Index specific modules
/index /home/user/project/my_repository --modules backend,frontend
```

## Success Criteria
- ✅ Complete codebase scan
- ✅ Semantic tokens generated
- ✅ Memory storage populated
- ✅ Architectural patterns detected
- ✅ Indexing report generated

## Performance Expectations
- Typical repositories (<50K LOC): 2-10 seconds
- Large repositories (50K-500K LOC): 10-60 seconds
- Massive repositories (>500K LOC): 1-5 minutes

## Output
- Detailed indexing report
- Semantic token count
- Detected architectural patterns
- Storage utilization
- Estimated retrieval performance

## Integration
- Directly integrated with PRISM MCP
- Uses Tier 0 (Voyage AI + Jina AI) embeddings
- Zero GPU required
- Persistent, updatable memory storage

## Limitations
- Requires PRISM MCP services running
- Best performance with Python, TypeScript, Rust codebases
- Large binary files or complex multi-language projects may require manual tuning

## Troubleshooting
- Ensure PRISM services are running: `nerdctl compose up -d`
- Check system health: `curl http://localhost:8090/health`
- Review logs: `nerdctl logs prism-api`