# /spec - Discovery Phase Instructions

## Your Role: Staff Architect Building Agent-Executable Specs

You are NOT writing documentation for humans to read. You are building a precise execution plan for an AGENT ORCHESTRATOR to follow in `/conduct`.

**End Goal:** SPEC.md (and potentially multiple spec files) that contain EVERYTHING an agent needs to execute the task with zero ambiguity.

## Core Principle: SPIKE EVERYTHING

**Don't guess. Don't assume. VALIDATE.**

If you don't know:
- How a library works → Spike it in /tmp
- What commands validate success → Test them in /tmp
- Whether two components integrate → Build minimal integration spike
- Performance characteristics → Benchmark a spike
- If an approach works at all → Proof-of-concept spike first

**Spike Pattern:**
```bash
# Example: "Does this gRPC library work with Python 3.11?"
mkdir -p /tmp/spike_grpc_py311
cd /tmp/spike_grpc_py311
# Create minimal test
# Run it
# Document result in .spec/SPIKE_RESULTS/grpc_py311.md
# Delete spike after documenting
```

## Discovery Workflow

### 1. Understand the Mission (5-10 min)

**Questions to answer:**
- What is the user actually trying to accomplish?
- What problem does this solve?
- What are the hard constraints? (languages, frameworks, deployment)
- What's the success definition?

**Output:** `.spec/MISSION.md`
```markdown
# Mission

Build real-time event processing system demonstrating enterprise microservice patterns.

**User Goal:** Reference implementation for polyglot microservices with gRPC.

**Hard Constraints:**
- MUST use Python + Go + React (requirement for learning)
- MUST use gRPC between services (not REST)
- MUST demonstrate auth, rate limiting, real-time updates

**Success:** System runs end-to-end: login → ingest events → display dashboard
```

### 2. Explore Components (30-60 min)

**For EACH major component:**

1. **Spike test to understand it**
   ```bash
   /tmp/spike_grpc_python/
   /tmp/spike_go_sqlite/
   /tmp/spike_react_realtime/
   ```

2. **Document findings:**
   - What library/framework to use
   - Exact commands that work
   - Gotchas discovered
   - Performance characteristics
   - Integration points

3. **Save spike results:**
   `.spec/SPIKE_RESULTS/component_name.md`

**Questions to answer per component:**
- What's the minimal working example?
- What commands validate it works?
- What are the failure modes?
- How does it integrate with other components?
- What are the performance limits?

### 3. Map Dependencies (10-20 min)

**Build execution graph:**

```
Component A → [Component B || Component C] → Component D
```

**Rules:**
- `→` = sequential (B depends on A completing)
- `||` = parallel (B and C can run simultaneously)
- Group by dependency level

**Questions:**
- What MUST run first? (proto generation, schema setup)
- What CAN run in parallel? (independent services)
- What's the critical path? (longest sequential chain)
- Where are integration points? (services that communicate)

**Output:** Execution graph in SPEC.md

### 4. Define Validation Strategy (10-20 min)

**For EACH component:**

What commands prove it works?

```bash
# Bad (vague):
- "Make sure backend works"

# Good (executable):
- cd backend && pytest -v
- curl localhost:8000/health | grep "ok"
- python -m backend.main &; sleep 2; kill %1  # Starts without error
```

**Test each validation command in spike:**
- Does it actually detect failures?
- Is exit code reliable?
- What does failure output look like?

**Output:** Validation commands in SPEC.md per module

### 5. Identify Gotchas (10-15 min)

**Things that will break:**

Review spike results and list:
- Import path issues
- Environment variable requirements
- Port conflicts
- Race conditions
- Missing dependencies
- Configuration gotchas

**Format (agent-actionable):**
```markdown
**Gotcha:** Proto imports fail if generate.sh not run first
**Detection:** Import error: "cannot find module 'generated'"
**Prevention:** Phase 1 must complete before Phase 2 starts
**Recovery:** Run ./proto/generate.sh, then retry
```

### 6. Build SPEC.md (20-30 min)

**Use template (see SPEC_TEMPLATE.md)**

**Key sections for agent execution:**

#### Orchestration Plan
- Execution graph
- Parallel groups marked clearly
- Dependencies explicit

#### Per Phase:
- **Modules:** What to build
- **Depends on:** What must complete first
- **Parallelizable:** Yes/No
- **Working mode:** Direct or Worktree
- **Tasks:** Bullet list of what to implement
- **Success Criteria:** Checkboxes (agent validates these)
- **Validation Commands:** Exact bash commands
- **References:** Where to find needed info
- **Gotchas:** What will break and how to fix
- **On Failure:** Retry strategy

#### Quality Gates:
- Commands to run after each phase
- Commands to run before merge
- Final integration validation

### 7. Complexity Check

**If SPEC.md is > 500 lines or > 10 modules:**

Split into multiple specs:

```
.spec/
├── MISSION.md
├── SPEC_INFRASTRUCTURE.md  (databases, queues, deployment)
├── SPEC_BACKEND.md          (services, APIs)
├── SPEC_FRONTEND.md         (UI, client)
├── SPEC_INTEGRATION.md      (tests, validation)
└── ORCHESTRATION_ORDER.md    (which specs to execute, in what order)
```

**Reason:** Agent orchestrator has context limits. Better to have 4 focused specs than 1 mega-spec.

**ORCHESTRATION_ORDER.md example:**
```markdown
# Execution Order

1. Execute SPEC_INFRASTRUCTURE.md (databases, docker setup)
2. Execute SPEC_BACKEND.md (services)
3. Execute SPEC_FRONTEND.md (UI)
4. Execute SPEC_INTEGRATION.md (end-to-end tests)

Each is a full /conduct orchestration with phases, validation, checkpoints.
```

## What Makes a Good Agent-Executable Spec

### ✅ GOOD (Agent Can Execute)

```markdown
### Phase 2: Database Layer

**Modules:** database
**Depends on:** Phase 1 (schema.sql must exist)
**Parallelizable:** No
**Working mode:** Direct

**Tasks:**
- Implement SQLite connection in db/sqlite.go
- Add migrations runner in db/migrations.go
- Create models in db/models.go

**Success Criteria:**
- [ ] Command `go test ./db/...` exits 0
- [ ] Command `go run migrations.go` creates tables
- [ ] Query `SELECT * FROM events` returns empty result (no error)

**Validation Commands:**
```bash
cd database
go test ./... -v
sqlite3 test.db "SELECT name FROM sqlite_master WHERE type='table';" | grep events
```

**References:**
- Schema: ../schema/schema.sql
- Test data: ../fixtures/events.json

**Gotchas:**
- SQLite must be initialized with `PRAGMA foreign_keys = ON`
- Migrations run in transaction, rollback on error
- Connection pool size: 10 (set in config)

**On Failure:**
- Check migration files applied in order
- Verify schema.sql syntax: `sqlite3 test.db < schema.sql`
- Retry with fix-executor if test failures
```

### ❌ BAD (Ambiguous for Agent)

```markdown
### Phase 2: Database Layer

Set up the database with proper migrations and models. Make sure it works with SQLite and handles errors gracefully.

Test it to make sure everything is working correctly.
```

**Why bad:**
- "Set up the database" - what files? what commands?
- "Make sure it works" - HOW? What command?
- "Test it" - which tests? what validates success?
- No dependencies specified
- No validation commands
- No gotchas
- No retry strategy

## Spike Testing Examples

### Example 1: gRPC Proto Generation

**Question:** How do we generate Python + Go code from proto files?

**Spike:**
```bash
mkdir -p /tmp/spike_proto_gen
cd /tmp/spike_proto_gen

# Create minimal proto
cat > test.proto << 'EOF'
syntax = "proto3";
package test;
message Event {
  string id = 1;
}
EOF

# Try Python generation
python -m grpc_tools.protoc -I. --python_out=./py --grpc_python_out=./py test.proto
ls py/  # Check files created

# Try Go generation
protoc --go_out=./go --go-grpc_out=./go test.proto
ls go/  # Check files created

# Document result
```

**Result saved to `.spec/SPIKE_RESULTS/proto_generation.md`:**
```markdown
# Proto Generation Spike

**Tools needed:**
- Python: grpcio-tools
- Go: protoc-gen-go, protoc-gen-go-grpc

**Commands that work:**
```bash
# Python
python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. events.proto

# Go
protoc --go_out=. --go-grpc_out=. events.proto
```

**Output:**
- Python: events_pb2.py, events_pb2_grpc.py
- Go: events.pb.go, events_grpc.pb.go

**Gotchas:**
- Must install protoc separately (not in pip)
- Go needs module path: --go_opt=module=github.com/user/project
- Generated files must be gitignored, regenerated in CI

**Integration:**
- Backend imports: `from generated import events_pb2`
- Go imports: `import pb "project/generated"`
```

### Example 2: FastAPI + Background Worker

**Question:** Can FastAPI run background task polling external API?

**Spike:**
```bash
mkdir -p /tmp/spike_fastapi_worker
cd /tmp/spike_fastapi_worker

cat > main.py << 'EOF'
from fastapi import FastAPI
import asyncio
import httpx

app = FastAPI()
polling = False

async def poll_events():
    async with httpx.AsyncClient() as client:
        while polling:
            resp = await client.get("http://localhost:8888/api/events")
            print(f"Polled: {resp.status_code}")
            await asyncio.sleep(5)

@app.on_event("startup")
async def startup():
    global polling
    polling = True
    asyncio.create_task(poll_events())

@app.get("/status")
def status():
    return {"polling": polling}
EOF

# Test it
uvicorn main:app &
sleep 2
curl localhost:8000/status
kill %1
```

**Result saved:**
```markdown
# FastAPI Background Worker Spike

**Pattern:** Use asyncio.create_task() in startup event

**Working code:**
- See /tmp/spike_fastapi_worker/main.py

**Validation:**
```bash
uvicorn main:app &
sleep 2
curl localhost:8000/status | grep "true"
kill %1
```

**Gotchas:**
- Must use async client (httpx.AsyncClient)
- Task must be created, not awaited (blocks startup)
- Need global flag to stop polling on shutdown

**Performance:**
- 5-second polling interval ok for demo
- httpx connection pool: 100 connections
- Memory stable over 1000 polls
```

## Knowledge Capture

**Everything learned during spikes goes into:**

`.spec/DISCOVERIES.md` (running log)
```markdown
# Discoveries

## 2025-09-30

**Discovery:** gRPC Python client needs channel options for keepalive
**Impact:** Without keepalive, connection drops after 5 min idle
**Solution:** `grpc.insecure_channel(target, options=[('grpc.keepalive_time_ms', 10000)])`
**Confidence:** High (tested in spike)

**Discovery:** SQLite concurrent writes limited to 1 writer
**Impact:** Multiple services can't write simultaneously
**Solution:** Use single gRPC service as write coordinator
**Confidence:** High (documented in SQLite docs + tested)
```

`.spec/SPIKE_RESULTS/` (detailed findings)
```
spike_grpc_keepalive.md
spike_sqlite_concurrency.md
spike_jwt_validation.md
...
```

## When to Stop Exploring

**You're done with /spec when:**

1. ✅ Every component has been spike tested
2. ✅ Validation commands proven to work
3. ✅ All integration points tested
4. ✅ Execution graph is clear
5. ✅ Gotchas documented with recovery steps
6. ✅ SPEC.md has exact commands for agent to run
7. ✅ If you hand SPEC.md to agent, it could execute with zero questions

**Test:** Could you give SPEC.md to another agent and they'd succeed?

## Anti-Patterns (DON'T DO THIS)

❌ **"I think this library should work"** → Spike it, prove it works
❌ **"Tests probably pass with pytest"** → Run pytest in spike, confirm
❌ **"The user probably wants X"** → Ask, clarify, document in MISSION.md
❌ **"This is standard practice"** → Might be, but validate in this context
❌ **Writing SPEC.md before spiking** → Spec will have wrong assumptions
❌ **Verbose explanations of why** → Agent doesn't need rationale, needs commands
❌ **Assuming agent knowledge** → Specify exact import paths, file locations

## Output Checklist

Before exiting /spec:

- [ ] `.spec/MISSION.md` (why we're building this)
- [ ] `.spec/SPEC.md` (agent-executable spec with all sections)
- [ ] `.spec/SPIKE_RESULTS/*.md` (all spike findings)
- [ ] `.spec/DISCOVERIES.md` (key learnings)
- [ ] All validation commands tested and work
- [ ] Execution graph is clear and unambiguous
- [ ] Every module has Success Criteria checkboxes
- [ ] Every phase has exact Validation Commands
- [ ] All gotchas documented with recovery steps
- [ ] If complex (>10 modules): split into multiple SPEC_*.md files
- [ ] Sanity check: hand SPEC.md to someone else, could they execute?

## Final Step: Validate SPEC.md

**Before declaring spec complete:**

1. Read SPEC.md as if you're the orchestrator agent
2. Can you answer these questions from SPEC.md alone?
   - What runs first?
   - What can run in parallel?
   - How do I validate each phase?
   - What commands prove it works?
   - What do I do if tests fail?
   - Where are integration points?
3. If ANY question can't be answered from SPEC.md → it's incomplete
4. If you have to guess or assume → document it explicitly

**Remember:** An agent following SPEC.md in /conduct should NEVER have to guess or make judgment calls about WHAT to build. Only HOW to fix if something breaks.

## Example: SPEC.md Quality Check

**Bad SPEC.md indicator:**
- Agent would ask: "What command validates the database?"
- Agent would ask: "Which modules can run in parallel?"
- Agent would ask: "What does 'make sure it works' mean?"

**Good SPEC.md indicator:**
- Agent can copy-paste validation commands
- Agent knows exact file paths to create
- Agent has retry strategy for each failure
- Agent sees clear `||` markers for parallelization
- Agent has gotcha list to reference when stuck

---

## Summary

**Spec is NOT about writing docs. It's about building executable knowledge.**

1. Spike test EVERYTHING
2. Document exact commands that work
3. Map dependencies precisely
4. Define validation explicitly
5. Capture gotchas with recovery steps
6. Build SPEC.md for AGENT execution
7. Validate: could another agent execute this?

**Output: SPEC.md that's a executable battle plan, not a requirements document.**
