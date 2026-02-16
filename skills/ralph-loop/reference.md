# Ralph Loop Reference

Heavy reference material for the ralph-loop skill. Templates, examples, and detailed specifications.

---

## PROMPT File Template

Use this structure for every PROMPT file. Replace `[bracketed]` placeholders with project-specific content.

```markdown
# [Loop Name] — Autonomous Agent Instructions

## Housekeeping

**Ignore these files — do not ask about them, do not treat them as uncommitted work, do not let them block you:**
- `ralph-[loop].log` — append-only log written by the ralph loop wrapper. Not your concern.
- [language-specific coverage artifacts, e.g. `coverage.out`, `.coverage`, `coverage/`]

These are not repo safety issues. They are disposable artifacts. Move on.

**Pre-existing uncommitted changes are not your problem.** If `git status` shows modified files you did not edit, ignore them. The human may have been editing files between iterations. Only commit files YOU changed. Do not stop, do not ask, do not treat other people's uncommitted work as a blocker. Just commit your own files and move on.

## Prime Directive

You are building [what this loop builds] for [project name] — [one-sentence project description]. [Dependency statement: "This loop has no dependencies" OR "This loop depends on Loop N ([name]) being complete."] [Key constraint: e.g., "No LLM calls in this loop" or "All LLM responses in tests are MOCKED."]

### Authority Hierarchy

1. **DESIGN.md** (`[path]`) — the whitepaper. Behavioral authority. Why things work the way they do.
2. **IMPLEMENTATION.md** (`[path]`) — schemas, interfaces, contracts. Implementation authority. How to build it.
3. **This PROMPT file** — work items, rules, and workflow.

If DESIGN.md and IMPLEMENTATION.md conflict on implementation details (schemas, types, configs), IMPLEMENTATION.md wins. DESIGN.md wins for conceptual behavior and architectural rationale.

### Your Mission

Build a **compiling, tested, working** [layer name] where:
- [3-5 bullet points describing what success looks like]

## Rules of Engagement

### Non-Negotiable

1. **Read `progress-[loop].md` first.** Every iteration starts by reading this file. It tells you what's done, what's next, and what patterns previous iterations discovered. If you skip this, you will duplicate work or break things.

2. **DO NOT modify [other loop] code** unless a genuine bug is found. [List packages owned by other loops.] If you discover a bug, fix it and document the change in progress file with the reason. Do not refactor, improve, or reorganize other loops' code. **Exception:** You MAY add new files to other loops' packages when IMPLEMENTATION.md places them there. Adding new files is not modifying existing files.

3. **Match types from IMPLEMENTATION.md exactly.** [List key types.] Use the exact types, field names, and signatures from IMPLEMENTATION.md. Do not rename, restructure, or "improve" them.

4. **Every test must be thorough.** No `// TODO`, no skipped tests, no empty test bodies. Every test asserts specific behavior covering happy path, error paths, edge cases, and invariant enforcement. Every assertion traces to DESIGN.md or IMPLEMENTATION.md.

5. **One work item per iteration.** Pick the next incomplete item from the work items list. Do that one thing well. Do not get ambitious.

[Add domain-specific rules as needed, e.g., "All LLM calls in tests use mock responses."]

### Prohibited

- [List 5-8 prohibited behaviors specific to this loop]
- **No modifying DESIGN.md or IMPLEMENTATION.md** (except during Spec Compliance review sweeps where code is better than spec).
- **No global mutable state.** Dependency injection only.
- **No blaming pre-existing issues.** If the quality gate fails, it is your problem. Do not say "not introduced by me", "existing repo issue", "pre-existing failure", "baseline failure", or any variant. Do not annotate failures as someone else's responsibility. Either fix it or explain the specific technical blocker preventing you from fixing it in this iteration. You are not an auditor documenting problems — you are a builder fixing them.
- **No dead code.** If you build something, wire it. If you create clients/components/adapters, use them. `_ = result` on something you just built is dead code — either wire it into the system or don't create it. A component that is implemented but not started/registered/connected in the running system does not exist.
- **No deferrals.** "Deferred to keep scope manageable," "available for future wiring," "can be added in a review iteration" — these phrases are PROHIBITED. If the PROMPT says to do it, do it NOW. If you discover something that needs doing, do it NOW. There is no future iteration — every iteration could be the last.
- **No rationalizing away findings.** "Beyond minimal wiring," "acceptable for [reason]," "by design per item X scope" — if the spec says to do something and it's not done, it's a defect. Fix it. The ONLY valid reason to skip something is that it requires infrastructure that literally does not exist yet AND is assigned to a specific later loop's work item (cite the loop and item number).
- **No unverified test assertions.** If a test sets up a mock server, recorder, spy, or call counter, it MUST assert on the results. `_ = recorder` or `_ = callCount` is a defect. Every test setup must have corresponding assertions. A test that creates verification infrastructure and then ignores it is worse than no test — it creates false confidence.
- [Language-specific: e.g., "No `fmt.Println`. Use zerolog." or "No `print()`. Use logging."]

## Environment

- **Working directory**: `[project root]`
- **Language**: [language and version]
- **Module/package**: `[module path]`
- **Specs**: `[path to DESIGN.md]`, `[path to IMPLEMENTATION.md]`
- **Test framework**: [framework name]
- **Database**: [database for this loop, e.g., "SQLite (in-memory for tests)"]

## Quality Gate

Run this after EVERY change, before committing:

\`\`\`bash
[exact quality gate command for this language]
\`\`\`

[Coverage threshold statement, e.g., "Coverage must be >= 80% and increasing with every iteration."]

**Every command in the gate must succeed.** If any command fails, that is your problem to fix — not a "pre-existing issue" to document and move past. Do not commit code that fails the gate. Do not classify failures as outside your scope.

## Workflow Per Iteration

1. Read `progress-[loop].md` — understand current state
2. If work items remain: pick next incomplete work item (lowest number first)
   If all work items done: enter Review Phase (see below)
3. Read the referenced DESIGN.md and IMPLEMENTATION.md sections for that item
4. Implement the work item
5. Write thorough tests (see test list in work item)
6. Run quality gate — fix until it passes
7. Commit with descriptive message referencing the work item number
8. Update `progress-[loop].md`:
   - Move item to "Completed Work Items"
   - Add iteration log entry with: item number, what was done, any patterns discovered
   - Note any issues encountered or deviations from spec

## Progress Tracking

### Reading Progress

At the start of every iteration, read `progress-[loop].md`. Check:
- **Completed Work Items** — what's already done (don't redo it)
- **Codebase Patterns** — conventions discovered by previous iterations (follow them)
- **Iteration Log** — recent history, any warnings or blockers

### Writing Progress

After completing a work item and committing, update `progress-[loop].md`:
- Add the item number and title to "Completed Work Items"
- Add an iteration log entry
- If you discovered a pattern that future iterations should follow, add it to "Codebase Patterns"

**If you are the first iteration**, update the status from "NOT STARTED" to "IN PROGRESS".

## Work Items

### Phase 0: [Phase Name] (items 1-N)

#### 1. [Work item title]
**Spec sections**: DESIGN.md "[section name]", IMPLEMENTATION.md section N
**Package**: `[package path]`
**Files**: `[file1.ext]`, `[file1_test.ext]`
**Deliver**:
- [Bullet list of what the code must do]
**Tests**:
- [Happy path: specific scenario and expected result]
- [Error path: specific failure and expected behavior]
- [Edge case: boundary condition and expected behavior]
- [Invariant: thing that must never happen, verified]
- [Integration: interaction with adjacent component]
**Done when**: [One sentence completion condition]

[Repeat for all work items...]

---

## Review Phase

When all work items are complete, you enter the Review Phase. This is **NOT** optional. You do **NOT** declare the loop complete. You **NEVER** write "Loop Complete" or "Loop Done" in the progress file. The loop continues until the human Ctrl+C's ralph.

### Review Iteration Workflow

1. Read `progress-[loop].md` — check "Known Issues" and "Review Log"
2. If known issues exist, fix ALL known issues (highest severity first)
3. If no known issues, perform a FULL SWEEP of one category (see below):
   a. Scan thoroughly — search every relevant file, grep for patterns, compare against spec
   b. Collect ALL findings for this category before fixing anything
   c. Fix everything you found
   d. Write/fix tests for all changes
4. Run quality gate
5. Commit all fixes with descriptive message listing what was found and fixed
6. Update `progress-[loop].md`:
   - Move resolved issues from "Known Issues" to "Resolved Issues"
   - Add a review log entry: category, files checked, all findings, all fixes
   - Add any NEW issues discovered during review to "Known Issues"

### Review Categories (cycle through in order)

1. **Spec Compliance** — Open IMPLEMENTATION.md. For every interface, type, and method signature in the section you're reviewing, compare against the actual code. Every deviation is a bug to fix.
2. **Error Handling** — Find every discarded error, ignored return value, logged-but-not-returned error, and unchecked error return in production code. Every instance is a defect unless it matches one of these **specific acceptable patterns** (and ONLY these):
   - **Error unwind**: Already returning a more important error and this is cleanup/rollback
   - **Standard library idiom**: A well-known language idiom where ignoring the error is the documented correct usage (cite the documentation)
   - **Best-effort non-critical**: The operation is explicitly designated as non-critical in DESIGN.md or IMPLEMENTATION.md (cite the section)
   Anything not in this list is a defect. Fix it. "Common pattern" and "defensive code" are not justifications — cite the spec or cite language documentation, or fix the code.
3. **Test Coverage Gaps** — Find functions below 80% coverage. Write missing tests with specific assertions.
4. **Code Consistency** — Same patterns across all packages (ID generation, constructors, logging, error types).
5. **Dead Code & Dead Schema** — Unused exports, dead DB columns, unreferenced types, **implemented-but-unwired components**. **Remove or wire them.** If code exists that is "for a future loop," it must be referenced by a specific work item number in that loop's PROMPT file. Cite the loop name and item number, or delete the code. **Components that have implementations and tests but are never started/registered/connected in the running system are the most deceptive form of dead code** — they pass quality gates while providing zero runtime value. `_ = result` on a freshly created object is a dead code signal.
6. **Integration Wiring** — Every interface must have a real implementation, not just mocks. Every implemented component must be started, registered, or connected in the running system. Every adapter must be instantiated somewhere. If an implementation genuinely cannot exist yet (requires infrastructure from a later loop), add it to Known Issues with the specific loop and work item that will resolve it. "By design" and "deferred" are not valid — name the blocker.
7. **Security & Data Integrity** — Injection patterns, unsafe fallbacks, data corruption risks.

### Review Rules

- **Known Issues come first.** Before any category sweep, check `progress-[loop].md` Known Issues. If ANY exist, fix them (highest severity first) before doing category sweeps. Each fix is one iteration.
- **One category per iteration, but sweep it completely.** Check every file, every function, every pattern relevant to that category. Don't stop at the first finding.
- **Be adversarial.** Your job is to find defects, not to confirm the code is fine. If you find zero issues in a sweep, you probably didn't look hard enough.
- **No rubber stamps.** You do not get to decide something is "INTENTIONAL" or "by design" without citing the specific spec section (DESIGN.md section name or IMPLEMENTATION.md section number) that mandates the pattern. If you can't cite the spec, it's a defect.
- **"Noted but not fixed" IS a defect.** If you find something wrong, fix it. Do not log it as "noted" and move on. Do not rationalize it as "acceptable" unless the specific spec section says it's optional. Everything that can and should be done, MUST be done.
- **Dead code is a defect.** Building something and not wiring it is the same as not building it. If a component is implemented, it must be started/registered/connected in the running system.
- **No self-referencing.** Each review cycle evaluates the code independently against the spec. Your own previous review findings are not justification. "Same set as prior cycle" is not a valid assessment — re-evaluate each finding against the spec as if seeing it for the first time.
- **The spec is mandatory.** If the spec says something, the code must do it. The only valid reason to not implement something is that it is literally impossible in this loop (requires infrastructure, services, or code that doesn't exist yet AND is assigned to a specific later loop's work item). "Best practice," "common pattern," and "defensive" are not reasons to deviate from the spec.
- **After cycling through all 7 categories with zero findings, start over.** Previous fixes may have introduced new issues.
- **NEVER mark the loop as complete.** The human decides.

---

## Reminders

- [5-8 key architectural decisions the agent needs to keep in mind]
- [Things that are easy to forget or get wrong]
- [Domain-specific gotchas]
- **Read progress-[loop].md.** Every iteration. No exceptions.
- **Known Issues in progress-[loop].md are your #1 priority.** Fix them before doing category sweeps. Each Known Issue fix is one iteration. Move fixed issues to Resolved Issues.
- **If you build it, wire it.** Every component you implement must be started, registered, or connected in the running system. An implemented-but-unwired component is dead code.
- **100% completion means 100%.** Not "mostly done with some noted items." Not "complete except for deferrals." Every requirement fulfilled, every component wired, every test asserting real behavior. If it can and should be done, it MUST be done.
- **NEVER write "Loop Complete" in the progress file.** The human decides when the loop is done.
```

---

## IMPLEMENTATION.md Section Template

Every IMPLEMENTATION.md must include these sections. Adapt numbering and content to the project.

| Section | Contents | Specificity Standard |
|---------|----------|---------------------|
| Authority hierarchy | DESIGN.md > IMPLEMENTATION.md > PROMPTs | Same for every project |
| Module/directory layout | Every file path in the project | Agent can `mkdir -p` the entire tree |
| Dependencies | Table of all external libraries with versions | Agent can write `go.mod` / `requirements.txt` / `Cargo.toml` |
| Database schema | Full DDL (CREATE TABLE, indexes, constraints) | Agent can run the SQL verbatim |
| Shared types | All enums, constants, common structs | Agent can write the types file verbatim |
| Package interfaces | Every public method signature, Store interfaces | Agent can write the interface verbatim |
| External library integration | Exact constructor calls, option patterns, return types | Agent can write the integration code verbatim |
| State machines | Valid transitions listed, invalid = error | Agent can write the transition table |
| Configuration | Config struct with field types and defaults | Agent can write the config loader |
| Error handling | Error types, user-facing format | Agent can write the error constructors |
| Testing strategy | Per-component: what to mock, coverage target | Agent knows what to test and how |
| Deterministic logic | Any business rules expressed as code, not LLM | Agent writes if/else, not prompts |
| Security / limits | Compiled-in invariants, deploy-time limits | Agent can write the limits struct |
| v1 constraints | What's explicitly NOT in scope | Agent doesn't build v2 features |

**The specificity test:** Can an agent write the code from reading only this section, without guessing? If no, add more detail.

---

## Quality Gate Examples

### Go
```bash
go build ./... && go vet ./... && go test -coverprofile=coverage.out ./... -count=1
# Check coverage >= threshold
go tool cover -func=coverage.out | grep total | awk '{print $3}' | sed 's/%//' | \
  awk '{if ($1 < 80) {print "Coverage " $1 "% < 80%"; exit 1}}'
```

### Python
```bash
ruff check . && ruff format --check . && pyright . && \
  pytest --cov=src --cov-report=term-missing --cov-fail-under=80
```

### Rust
```bash
cargo build && cargo clippy -- -D warnings && cargo test && \
  cargo tarpaulin --fail-under 80
```

### TypeScript/Node
```bash
npm run build && npm run lint && npm test -- --coverage --coverageThreshold='{"global":{"lines":80}}'
```

---

## ralph.sh

The canonical ralph.sh script lives at `~/.claude/scripts/ralph.sh`. Copy it into project roots when setting up loops.

### Usage

```bash
./ralph.sh [loop_name] [agent]

# loop_name   Which PROMPT to use (optional). No arg or "-" = PROMPT.md, with arg = PROMPT-{name}.md
# agent       Which AI CLI: claude (default), codex

# Environment override:
#   RALPH_AGENT_CMD   Full command override
```

### Agent Commands

| Agent | Command |
|-------|---------|
| Claude | `$HOME/.claude/local/claude -p --dangerously-skip-permissions` |
| Codex | `codex exec --full-auto -` |
| Custom | Set `RALPH_AGENT_CMD` environment variable |

### Features

- **Two-tier Ctrl+C**: 1st = stop after current iteration, 2nd = kill immediately
- **Per-loop logging**: `ralph-{loop_name}.log`
- **Background process groups**: Ctrl+C doesn't kill the agent mid-work
- **Agent-agnostic**: Claude, Codex, or any CLI that reads stdin

---

## Cross-Validation Checklist (Detailed)

When launching the Reviewer agent at Phase 3 checkpoint, include these specific checks:

### Import Cycle Detection
- For each interface that returns a type from another package, verify the other package doesn't need to import the first to implement it
- Common pattern: define response types in a shared/root package, adapters in a wiring layer (e.g., `cmd/` or `internal/wire/`)
- Fix: introduce adapter types in root package, converters in wiring layer

### Type Consistency
- Search for the same concept name across all PROMPT files and IMPLEMENTATION.md
- Verify field names, field types, and JSON tags match everywhere
- Watch for: string vs struct, different field names for same concept, type defined in two packages

### Interface Completeness
- Every method referenced in a PROMPT work item must exist in IMPLEMENTATION.md
- Every interface in IMPLEMENTATION.md must have all methods that any consumer needs
- Watch for: Store interfaces missing query methods needed by tests

### Work Item Coverage
- List every package from IMPLEMENTATION.md directory layout
- Verify each package has at least one work item across all loops
- Flag packages with zero work items as orphans

### Loop Boundary Violations
- Each PROMPT's "don't modify Loop N" rule must be consistent with where work items place files
- Adding NEW files to another loop's package is OK if IMPLEMENTATION.md's directory layout puts them there
- The PROMPT rule should explicitly carve out this exception

### Test Specificity Audit
- Sample 5+ work items across loops
- Each test description should be specific enough to write the test from
- Flag any "test error handling", "add tests", "verify it works" as too vague
