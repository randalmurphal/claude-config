# Index Project Command

Index a project using Anthropic's contextual retrieval technique.

## Usage

```
/index <project_path>
```

## What This Does

Implements batched two-phase indexing based on Anthropic's research (-49% retrieval failures):

**Phase 1: Generate CLAUDE.md Documents**
- Spawn investigator agents (via Task tool) to analyze each directory
- Generate CLAUDE.md files explaining concepts, patterns, gotchas
- These serve dual purpose: human navigation + embedding context

**Phase 2: Extract & Contextualize Memories**
- Extract knowledge from code/docs (decisions, patterns, gotchas)
- Add 50-100 token context to each memory using CLAUDE.md as "document"
- Store contextualized memories in PRISM

**Batched Processing (for large codebases)**
- Processes 30 directories at a time to avoid token limits
- Tracks batch progress in PRISM (resumable if interrupted)
- Clears intermediate results between batches
- Full project context preserved for background enrichment

**Incremental Updates**
- Tracks last indexed commit in PRISM
- Uses git diff to find changed directories
- Re-indexes only affected directories
- Supersedes old memories, creates new ones

## Arguments

- `<project_path>`: Path to project root (default: current directory)

## Examples

```bash
# Index current project
/index

# Index specific project
/index /path/to/my-project

# Index with specific scope
/index /path/to/project --scope=user
```

## Implementation Steps

You should:

1. **Validate project path** - ensure it's a git repository
2. **Initialize components** (REQUIRED):
   ```python
   from prism_mcp.indexing import (
       ProjectIndexer, GitTracker, DirectoryAnalyzer,
       MemoryExtractor, Contextualizer
   )
   from prism_mcp.indexing.claude_code_client import ClaudeCodePrismClient

   # Create PRISM client
   prism_client = ClaudeCodePrismClient(...)

   # Create GitTracker (CRITICAL for resume capability)
   git_tracker = GitTracker(prism_client)

   # Create other components
   directory_analyzer = DirectoryAnalyzer(...)
   memory_extractor = MemoryExtractor(...)
   contextualizer = Contextualizer(...)
   indexer = ProjectIndexer(
       directory_analyzer, memory_extractor, contextualizer, prism_client
   )
   ```

3. **Check if already indexed**:
   - Use `git_tracker.get_last_indexed_commit(project_id, user_id)`
   - Compare to current commit: `git_tracker.get_current_commit(project_root)`
   - If same commit → skip entirely (already indexed, no changes)
   - If different or never indexed → proceed to step 4

4. **Call ProjectIndexer.index_project()**:
   ```python
   result = indexer.index_project(
       project_root=Path(project_path),
       scope=MemoryScope.GLOBAL,  # or USER/TEAM
       user_id=user_id,
       project_id=project_id,
       batch_size=30,  # Good for large codebases
       git_tracker=git_tracker,  # CRITICAL - enables resume
   )
   ```

   **What happens:**
   - Checks `git_tracker.get_batch_progress()` for interrupted batches
   - Resumes from last completed batch (if found)
   - Processes batches sequentially until done OR token limit hit
   - Saves progress after each batch
   - Clears `claude_md_map` between batches (prevents accumulation)

   **Token limit behavior:**
   - Large codebases (500+ dirs) will hit limits after ~5-10 batches
   - When hit: progress saved, execution stops (gracefully or error)
   - Just run `/index` again → automatically resumes

5. **Background enrichment** (automatic):
   - ProjectIndexer spawns enrichment agent at end
   - Agent queries ALL memories for project_id (not per-batch)
   - Extracts cross-directory relationships
   - Full project context preserved despite batching

6. **Store final metadata**:
   - GitTracker.store_indexed_commit() supersedes batch progress
   - Stores current commit SHA for future incremental updates

## Key Principles

- **Fail loud**: Don't store bad memories - fix issues first
- **Concept-focused**: CLAUDE.md explains WHY, not just WHAT
- **Task tool for sub-agents**: Spawn in-session agents for analysis
- **Neo4j relationships**: Link related but separate memories
- **Backup CLAUDE.md**: Always backup existing files before replacing

## MCP Tools Used

- `mcp__prism__store_memory` - Store contextualized memories
- `mcp__prism__retrieve_memories` - Check for existing index metadata
- `mcp__prism__supersede_memory` - Update memories from changed directories

## Expected Output

Report indexing progress (with batching for large codebases):
```
🔍 Indexing project: /path/to/project

📊 Status Check:
  ✓ Git repository detected
  ✓ Found 886 directories to index
  ✓ Processing in 30 batches (30 dirs/batch)
  ✓ Last indexed: commit abc123 (2 days ago)

=== Batch 1/30: Processing directories 1-30/886 ===
Phase 1: Generating CLAUDE.md files
  📝 Analyzing prism_mcp/indexing/
  📝 Analyzing prism_mcp/storage/
  ...
  ✓ Batch 1 Phase 1 complete: 28 CLAUDE.md files created

Phase 2: Extracting and contextualizing memories
  🧠 Extracting from prism_mcp/indexing/ (3 memories)
  🧠 Extracting from prism_mcp/storage/ (5 memories)
  ...
  ✓ Batch 1/30 complete: 87 total memories stored, 12 relationships

=== Batch 2/30: Processing directories 31-60/886 ===
...

=== Batch 30/30: Processing directories 871-886/886 ===
...

📈 Final Results:
  Directories analyzed: 886
  CLAUDE.md files: 832 created
  Memories: 2,341 extracted, 2,341 stored
  Relationships: 847 created
  Failed directories: 3

✅ Indexing complete
🔄 Spawning background enrichment agent for m32rimm
✅ Enrichment job queued: enrich_m32rimm_20250106_143022
```

## Notes

**Performance:**
- Large codebases (500+ dirs): expect 3-5 runs of `/index` to complete
- Each run processes ~5-10 batches before hitting token limits
- Total time: 30-60 minutes for 1000+ directories
- Progress auto-saves after each batch

**Resume behavior:**
- If interrupted (timeout/error/limit): just run `/index` again
- Automatically resumes from last completed batch
- Requires GitTracker to be created and passed (see implementation steps)

**How batching prevents token limits:**
- Processes 30 directories per batch
- `claude_md_map` cleared after each batch
- Only batch logs accumulate in main agent context
- Each batch: ~15-20K tokens, so 5-10 batches before limit

**Other notes:**
- Uses investigator agents (via Task tool) for directory analysis
- All CLAUDE.md files are backed up before replacement
- Background enrichment preserves full project context despite batching
- Incremental updates are much faster (only changed directories)

## Example: 886-Directory Codebase

```bash
# Run 1: Processes batches 1-8, hits token limit
/index ~/repos/m32rimm
# ✓ Batch 8/30 complete: 347 total memories stored

# Run 2: Resumes automatically
/index ~/repos/m32rimm
# ✓ Resuming from batch 9 (previously completed 8 batches)
# ✓ Batch 16/30 complete: 724 total memories stored

# Run 3: Continues...
/index ~/repos/m32rimm
# ✓ Resuming from batch 17
# ✓ Batch 24/30 complete: 1,089 total memories stored

# Run 4: Completes
/index ~/repos/m32rimm
# ✓ Resuming from batch 25
# ✓ Batch 30/30 complete: 2,341 total memories stored
# ✅ Indexing complete
# 🔄 Spawning background enrichment agent
```
