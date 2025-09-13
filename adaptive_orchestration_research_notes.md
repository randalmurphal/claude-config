# Adaptive Orchestration Research Notes

## Memory MCP Server Status
- **Current Issue**: Response format incompatibility - returns objects instead of JSON strings
- **Fix Applied**: Modified `/home/randy/repos/enhanced-memory-mcp/src/mcp-server.ts` to stringify responses
- **Status**: Fixed version running locally at `/home/randy/repos/enhanced-memory-mcp/dist/mcp-server.js`
- **Memory Usage**: ~120MB for Node.js implementation
- **Code Size**: 5,291 lines of TypeScript

## Performance Benchmarks

### Language/Runtime Comparison
- **Node.js (Current)**: 120MB memory, slower startup, event loop limitations
- **Go**: 10-50x lower memory (12MB), 5-10x faster startup, better concurrency
- **Rust**: 100x lower memory (1-2MB), zero GC, predictable performance
- **Zig**: Similar to Rust performance, simpler than Rust, manual memory management

### MCP Protocol Specifications
- **Architecture**: JSON-RPC 2.0 over STDIO/HTTP/WebSocket
- **Message Types**: Request/Response/Notification
- **Core Primitives**: Tools, Resources, Prompts
- **Performance**: Higher overhead than binary protocols but human-readable
- **Real-world latency**: 30-176ms depending on implementation

## AI Classification Models

### Task Classification (Local Deployment)
- **DistilBERT + ONNX**: 10-50ms inference, 85-93% accuracy
- **Size**: 66M parameters (40% smaller than BERT)
- **Memory**: <100MB when quantized
- **FastText Alternative**: <5ms inference, 75-85% accuracy

### Code Understanding Models
- **GraphCodeBERT**: Best for structural analysis, uses data flow graphs
- **CodeT5**: Superior for control/data dependencies
- **StarCoder2**: 3B/7B/15B versions, trained on 600+ languages
- **Local Requirements**: RTX 3060/M2+ for 7B models

### Intent Classification Performance
- **BERT-based**: 84.78% mean F1-score
- **Multi-label Support**: Tasks can be bug fix AND refactor
- **Production Systems**: Jira achieves 0.72 F-measure
- **Confidence Calibration**: Temperature scaling for uncertainty estimation

## Vector Databases for Pattern Matching

### Performance Rankings
1. **Qdrant**: 30.75ms p50 latency, 360 QPS at 50M vectors
2. **Chroma**: ~20ms for 100K vectors, easy prototyping
3. **DuckDB VSS**: SQL + vector search hybrid
4. **Postgres+pgvector**: 31ms latency, 1,589 QPS

### Storage Requirements
- **Raw**: 100M vectors × 768d × 4 bytes = 300GB
- **Compressed**: ~800MB with product quantization (97% reduction)
- **Memory**: 8.6GB RAM for 1M × 1536d dataset

## Search and Indexing Solutions

### Full-Text Search Alternatives
- **MeiliSearch**: 7x faster indexing, 290MB peak memory, sub-50ms queries
- **Sonic**: 30MB RAM usage, 30-40% disk savings
- **Tantivy**: Rust-based Lucene alternative, library not service

### Code-Specific Search
- **ast-grep**: Rust-based AST structural search
- **ripgrep**: 10x faster than alternatives for regex
- **Zoekt**: Powers Sourcegraph, good for large codebases

### Graph Databases
- **SurrealDB**: Multi-model (graph + document + vector), scaled to 700k users
- **Memgraph**: 8x faster reads, 50x faster writes than Neo4j
- **DGraph**: Distributed, GraphQL-like queries

## LLM Orchestration in Production

### Production Frameworks (2024-2025)
- **LangGraph**: 400 companies in production, parallelization + checkpointing
- **MARCO**: 94.48% accuracy, 44.91% latency improvement
- **Orq.ai**: SOC2 certified, multi-LLM orchestration
- **Microsoft Copilot Studio**: Multi-agent orchestration with deterministic workflows

### Enterprise Examples
- **Uber**: LangGraph for code migrations with specialized agents
- **Elastic**: Security threat detection with multi-agent systems
- **LinkedIn**: Hierarchical agent system for recruiting automation
- **Coinbase**: AgentKit for crypto wallet interactions

### Performance Patterns
- **Dynamic Task Decomposition**: Central LLM breaks down complex tasks
- **Parallel Processing**: Multiple agents handle tasks simultaneously
- **Context Engineering**: Optimizes information in LLM input
- **Multi-Model Routing**: Different models for different task complexities

## Existing Orchestration Systems

### Temporal.io Patterns
- **Workflow as State Machine**: Engine provides state, workflow returns commands
- **Dynamic Dispatch**: Based on parameters and metadata
- **Durable Execution**: Multi-year workflows with automatic recovery
- **Transactional Consistency**: Across database, queues, timers, workflow state

### AWS Step Functions
- **Map State**: Dynamic parallelism for dataset items
- **Choice State**: Conditional branching based on runtime
- **Distributed Map**: Massive scale with child workflow isolation
- **Error Handling**: Retry and catch mechanisms adapt to failures

### CI/CD Dynamic Workflows
- **GitHub Actions Matrix**: Dynamic generation based on code changes
- **CircleCI Setup+Continuation**: Two-phase dynamic workflow assembly
- **Buildkite**: Runtime pipeline generation with Bazel integration
- **Performance**: 30% productivity gains through selective execution

### Kubernetes Operators
- **Reconciliation Model**: Continuous observation of current vs desired state
- **Event-Driven**: Responds to create/update/delete events
- **Self-Healing**: Automatically corrects drift
- **Custom Resources**: Domain-specific adaptation logic

## Relevance and Pattern Detection

### Attention-Based Models
- **LSTM + Attention**: 95%+ accuracy for task context similarity
- **Dynamic Attention**: Variable-length input handling
- **Production**: <20ms latency for pattern detection

### Hybrid Approaches
- **BM25 + Neural Reranking**: 8-15% performance improvement
- **LLM Zero-Shot**: Reasoning capabilities for relevance
- **Cross-Modal**: Vision-language models with 63% improvement

### Production Systems
- **GitHub Copilot**: Vector embeddings with CodeBERT/UniXCoder
- **Multi-Model Architecture**: GPT-4.1 baseline with model selection
- **Agent Mode**: Autonomous operation with GitHub Actions
- **Infrastructure**: MCP server connections, Azure AI Foundry

## Anomaly Detection for Orchestration

### Complexity Indicators
- **Task Duration**: <4 min = ~100% AI success, >4 hours = <10% success
- **Token Consumption**: 4x for agents, 15x for multi-agent systems
- **Resource Patterns**: Direct correlation with task complexity

### Detection Systems
- **Netflix Maestro**: Handles DAG and cyclic workflows
- **80-90 Rule**: Structured workflows for common cases, routing for unusual
- **Threshold-Independent**: AUC-ROC, AUC-PR, VUS measures preferred

### Production Patterns
- **Duration-Based Routing**: Flag tasks exceeding thresholds
- **Hierarchical Decomposition**: Break complex tasks into subtasks
- **Context-Preserved Escalation**: Full context maintained
- **Continuous Learning**: Human feedback improves detection

## Obsidian MCP Integration

### Available Servers (24 implementations)
- **cyanheads/obsidian-mcp-server**: Most comprehensive
- **Core Functions**: Read, update, search, manage frontmatter/tags
- **Advanced**: Semantic search via Smart Connections plugin
- **Architecture**: REST API bridge or direct vault access

### Capabilities
- CRUD operations on notes
- Global vault search
- Template integration
- JWT/OAuth authentication
- Case-insensitive operations

## Small Language Models for Local Deployment

### Microsoft Phi Series
- **Phi-3-mini**: 3.8B parameters, 128K context
- **Performance**: Outperforms larger models on reasoning
- **Deployment**: Optimized for local execution

### Google Gemma
- **Sizes**: 2B/7B parameters
- **Features**: 140+ languages, 128K context
- **Architecture**: Built from Gemini technology

### Hardware Requirements
- **7B Models**: Single RTX 4090 (24GB)
- **Deployment Tools**: Ollama, local inference frameworks
- **Performance**: Real-time classification with minimal latency

## Key Architecture Patterns

### Temporal's Approach
- Workflows operate as state machines
- Dynamic dispatch based on context
- Transactional consistency guarantees
- Code-first workflow definition

### Dagster's Asset-Centric Model
- Data assets as first-class citizens
- Dynamic workflow generation
- Modular pipeline components
- Versioning and caching built-in

### CircleCI's Two-Phase Pattern
- Setup phase analyzes context
- Continuation phase generates workflow
- Path filtering for selective execution
- Dynamic configuration based on discoveries

## Critical Metrics

### Classification Speed
- DistilBERT: 10-50ms
- FastText: <5ms
- Vector search: 20-30ms
- Total decision time target: <100ms

### Storage Efficiency
- Vector compression: 97% reduction possible
- Markdown notes: Git-trackable, human-readable
- DuckDB: Efficient for execution history

### Success Rates
- Intent classification: 84-93% accuracy
- Bug/feature detection: 85.7% F1-score
- Production routing: 72% (Jira benchmark)