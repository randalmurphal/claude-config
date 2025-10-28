# Claude Code Personal Configuration

> **Advanced Claude Code setup with intelligent orchestration, cross-session learning, and AI-optimized workflows**

This repository contains a production-grade configuration for [Claude Code](https://docs.claude.com/claude-code) with multi-agent orchestration, semantic memory, automation scripts, and 32 domain-specific skills.

---

## 🎯 What This Is

A comprehensive `.claude` configuration that transforms Claude Code into an intelligent development partner with:

- **Smart Orchestration**: Three-tier command system (`/solo`, `/spec`, `/conduct`) for tasks of any complexity
- **Cross-Session Learning**: PRISM semantic memory system that remembers patterns and decisions
- **32 Domain Skills**: Pre-loaded expertise (Python, Git, testing, DevOps, API design, etc.)
- **Automation Scripts**: GitLab/Jira integration without token-heavy MCP servers (97.7% token savings)
- **Quality Gates**: Multi-agent validation (security, performance, code quality) on every build
- **Hook System**: Event-driven automation for formatting, validation, and learning

**Token Efficiency**: Scripts save 119,550 tokens per PR review workflow vs. MCP servers (99.6% reduction)

---

## 🚀 Quick Start

### Installation

1. **Clone into your home directory:**
   ```bash
   cd ~
   git clone <your-repo-url> .claude
   ```

2. **Set up credentials:**
   ```bash
   # GitLab credentials (optional, for GitLab scripts)
   cp ~/.claude/scripts/.gitlab-credentials.example ~/.claude/scripts/.gitlab-credentials
   # Edit with your token: vim ~/.claude/scripts/.gitlab-credentials

   # Jira credentials (optional, for Jira scripts)
   cp ~/.claude/scripts/.jira-credentials.example ~/.claude/scripts/.jira-credentials
   # Edit with your token: vim ~/.claude/scripts/.jira-credentials
   ```

3. **Configure settings (already tracked):**
   - Settings are in `~/.claude/settings.json`
   - Hooks enabled by default (auto-format on Edit/Write)
   - Custom status line configured
   - Output style: `daily_driver` (witty, direct)

4. **Start using orchestration commands:**
   ```bash
   # In any project directory
   /solo add rate limiting to API endpoint
   /spec design real-time event processing system
   /pr_review INT-1234
   ```

---

## 📋 Slash Commands (Orchestration)

Choose the right command for your task complexity:

| Command | When to Use | Prerequisites | Token Budget |
|---------|-------------|---------------|--------------|
| **`/solo`** | Simple tasks, 1-3 files, clear requirements | None | 10-20k |
| **`/spec`** | Need investigation, architecture unclear | None | 15-30k |
| **`/conduct`** | Complex multi-component features | SPEC.md from /spec | 50k+ |
| **`/pr_review`** | Review merge request against Jira ticket | Jira ticket ID | 30-60k |
| **`/update_docs`** | Update all docs to match current code | None | 20-40k |
| **`/coda`** | End session with summary and handoff | None | 5-10k |

### Command Decision Tree

```
                        User Task
                            │
                            ▼
                    ┌───────────────┐
                    │ Is it clear   │
                    │ what to do?   │
                    └───────┬───────┘
                            │
                ┌───────────┴───────────┐
                │                       │
               YES                     NO
                │                       │
                ▼                       ▼
        ┌───────────────┐      ┌──────────────┐
        │ Simple task?  │      │ Need to      │
        │ (1-3 files)   │      │ investigate? │
        └───────┬───────┘      └──────┬───────┘
                │                     │
        ┌───────┴──────┐              │
        │              │              ▼
       YES            NO         ┌─────────┐
        │              │         │ /spec   │──┐
        ▼              ▼         └─────────┘  │
    ┌────────┐   ┌──────────┐                 │
    │ /solo  │   │ /conduct │                 │
    └────────┘   └──────────┘                 │
        │              ▲                      │
        │              │                      │
        └──────────────┴──────────────────────┘
                       │
                       ▼
                  ┌─────────┐
                  │  Done   │
                  └─────────┘

Special Cases:
    PR Review?  ──→  /pr_review
    Update Docs? ──→ /update_docs
    Session End? ──→ /coda
```

---

### `/solo` - Streamlined Implementation

**Best for**: Straightforward tasks with clear scope

```bash
/solo add rate limiting middleware
/solo fix authentication bug in login endpoint
/solo implement CSV export for reports
```

**What it does**:
1. Creates minimal spec (`.spec/BUILD_*.md`)
2. Implements via specialized agents
3. Validates with 6 reviewers (security, performance, code quality)
4. Runs tests (if requested)
5. Merges learnings into permanent docs
6. Cleans up `.spec/`

**Validation Loop**: Fix → Validate → Repeat (max 3 attempts, 95%+ test coverage)

#### `/solo` Workflow

```
┌─────────────────────────────────────────────────────────────┐
│                      /solo Command                          │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
                ┌───────────────────────┐
                │ Load agent-prompting  │
                │ skill (MANDATORY)     │
                └───────────┬───────────┘
                            │
                            ▼
                ┌───────────────────────┐
                │ Generate minimal spec │
                │ .spec/BUILD_*.md      │
                └───────────┬───────────┘
                            │
                            ▼
                ┌───────────────────────┐
                │ Spawn implementation  │
                │ & test agents         │
                └───────────┬───────────┘
                            │
                            ▼
        ┌───────────────────────────────────────┐
        │          Validation Loop              │
        │  ┌─────────────────────────────────┐  │
        │  │ Run linting (ruff/pyright)      │  │
        │  └─────────────┬───────────────────┘  │
        │                ▼                       │
        │  ┌─────────────────────────────────┐  │
        │  │ Spawn 6 reviewers in parallel:  │  │
        │  │ • Security                      │  │
        │  │ • Performance                   │  │
        │  │ • Code Quality (3x)             │  │
        │  │ • Style                         │  │
        │  └─────────────┬───────────────────┘  │
        │                ▼                       │
        │         ┌─────────────┐                │
        │         │ Issues?     │                │
        │         └──────┬──────┘                │
        │                │                       │
        │      ┌─────────┴─────────┐             │
        │     YES                  NO            │
        │      │                    │            │
        │      ▼                    │            │
        │  ┌────────────┐           │            │
        │  │ Spawn fix- │           │            │
        │  │ executor   │           │            │
        │  └─────┬──────┘           │            │
        │        │                  │            │
        │        └──────────────────┘            │
        │  (Repeat max 3 times)                  │
        └───────────────────────────────────────┘
                            │
                            ▼
                ┌───────────────────────┐
                │ Run tests (pytest)    │
                │ Coverage: 95%+        │
                └───────────┬───────────┘
                            │
                            ▼
                ┌───────────────────────┐
                │ Merge learnings into  │
                │ permanent docs        │
                └───────────┬───────────┘
                            │
                            ▼
                ┌───────────────────────┐
                │ Cleanup .spec/        │
                └───────────┬───────────┘
                            │
                            ▼
                        ┌───────┐
                        │ Done  │
                        └───────┘
```

---

### `/spec` - Discovery & Planning

**Best for**: Complex features needing investigation

```bash
/spec design event-driven architecture with gRPC
/spec investigate options for real-time notifications
```

**What it does**:
1. **Assessment**: Asks 3-5 clarifying questions
2. **Investigation**: Auto-reads existing code
3. **Challenge Mode**: Identifies ≥3 concerns/risks
4. **Spike Testing**: Validates approaches in `/tmp/spike_*`
5. **Spec Creation**: Writes `SPEC.md` with 10 required sections
6. **Component Breakdown**: Creates phase specs (`SPEC_1_*.md`, etc.)

**Output**: `.spec/SPEC.md` ready for `/conduct`

#### `/spec` Workflow

```
┌─────────────────────────────────────────────────────────────┐
│                      /spec Command                          │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
                ┌───────────────────────┐
                │ Initial Assessment    │
                │ Ask 3-5 questions     │
                └───────────┬───────────┘
                            │
                            ▼
                ┌───────────────────────┐
                │ Auto-Investigation    │
                │ Read existing code    │
                │ Understand context    │
                └───────────┬───────────┘
                            │
                            ▼
                ┌───────────────────────┐
                │ Challenge Mode        │
                │ Find ≥3 concerns:     │
                │ • Performance risks   │
                │ • Security issues     │
                │ • Integration points  │
                │ • Complexity traps    │
                └───────────┬───────────┘
                            │
                            ▼
        ┌───────────────────────────────────────┐
        │         Spike Testing Phase           │
        │  ┌─────────────────────────────────┐  │
        │  │ For each approach option:       │  │
        │  │                                 │  │
        │  │ 1. Create /tmp/spike_NAME/      │  │
        │  │ 2. Write throwaway code         │  │
        │  │ 3. Run & validate               │  │
        │  │ 4. Document exact commands      │  │
        │  │ 5. Capture gotchas + recovery   │  │
        │  └─────────────────────────────────┘  │
        │                                        │
        │  Test in parallel:                     │
        │  • gRPC spike                          │
        │  • Database spike                      │
        │  • UI integration spike                │
        └───────────────────────────────────────┘
                            │
                            ▼
                ┌───────────────────────┐
                │ Create SPEC.md with:  │
                │ • Overview            │
                │ • User Stories        │
                │ • Acceptance Criteria │
                │ • Technical Design    │
                │ • API Contracts       │
                │ • Data Models         │
                │ • Dependencies        │
                │ • Testing Strategy    │
                │ • Rollout Plan        │
                │ • Spike Findings      │
                └───────────┬───────────┘
                            │
                            ▼
                ┌───────────────────────┐
                │ Create Component      │
                │ Phase Specs:          │
                │ • SPEC_1_auth.md      │
                │ • SPEC_2_api.md       │
                │ • SPEC_3_db.md        │
                └───────────┬───────────┘
                            │
                            ▼
                ┌───────────────────────┐
                │ Ready for /conduct    │
                └───────────────────────┘
```

---

### `/conduct` - Multi-Component Orchestration

**Best for**: Implementing complex features from SPEC.md

```bash
/conduct   # Requires .spec/SPEC.md from /spec
```

**What it does**:
1. Parses SPEC.md → extracts components + dependencies
2. Builds dependency graph → topological sort
3. **For each component** (in dependency order):
   - Skeleton → Implementation → Validate → Test → Document → Checkpoint
4. Integration testing across all components
5. Final documentation validation
6. Cleanup `.spec/`

**Key Features**:
- Dependency-aware execution (no broken imports)
- Per-component validation (catch issues early)
- Parallel agent execution where possible
- Checkpoints after each component

#### `/conduct` Workflow

```
┌─────────────────────────────────────────────────────────────┐
│                    /conduct Command                         │
│              (Requires .spec/SPEC.md)                       │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
                ┌───────────────────────┐
                │ Parse SPEC.md         │
                │ Extract components    │
                │ Extract dependencies  │
                └───────────┬───────────┘
                            │
                            ▼
                ┌───────────────────────┐
                │ Build dependency      │
                │ graph                 │
                │ Topological sort      │
                └───────────┬───────────┘
                            │
                            ▼
        ┌───────────────────────────────────────┐
        │     For Each Component (in order)     │
        │                                        │
        │  ┌─────────────────────────────────┐  │
        │  │ 1. Skeleton Phase               │  │
        │  │    • Create file structure      │  │
        │  │    • Define interfaces          │  │
        │  │    • Add NotImplementedError    │  │
        │  └──────────────┬──────────────────┘  │
        │                 ▼                      │
        │  ┌─────────────────────────────────┐  │
        │  │ 2. Implementation Phase         │  │
        │  │    • Fill in logic              │  │
        │  │    • Working code (no TODOs)    │  │
        │  └──────────────┬──────────────────┘  │
        │                 ▼                      │
        │  ┌─────────────────────────────────┐  │
        │  │ 3. Validation Phase             │  │
        │  │    • Run linting                │  │
        │  │    • Spawn 6 reviewers          │  │
        │  │    • Fix issues (max 3 loops)   │  │
        │  └──────────────┬──────────────────┘  │
        │                 ▼                      │
        │  ┌─────────────────────────────────┐  │
        │  │ 4. Testing Phase                │  │
        │  │    • Write tests (95%+ cov)     │  │
        │  │    • Run tests                  │  │
        │  │    • Fix failures               │  │
        │  └──────────────┬──────────────────┘  │
        │                 ▼                      │
        │  ┌─────────────────────────────────┐  │
        │  │ 5. Documentation Phase          │  │
        │  │    • Update CLAUDE.md           │  │
        │  │    • Update README              │  │
        │  └──────────────┬──────────────────┘  │
        │                 ▼                      │
        │  ┌─────────────────────────────────┐  │
        │  │ 6. Checkpoint                   │  │
        │  │    • Git commit                 │  │
        │  │    • Mark complete              │  │
        │  └─────────────────────────────────┘  │
        │                                        │
        │  Next component has access to          │
        │  working APIs from previous phases     │
        └───────────────────────────────────────┘
                            │
                            ▼
                ┌───────────────────────┐
                │ Integration Testing   │
                │ All components        │
                │ together              │
                └───────────┬───────────┘
                            │
                            ▼
                ┌───────────────────────┐
                │ Final Documentation   │
                │ Validation            │
                └───────────┬───────────┘
                            │
                            ▼
                ┌───────────────────────┐
                │ Cleanup .spec/        │
                └───────────┬───────────┘
                            │
                            ▼
                        ┌───────┐
                        │ Done  │
                        └───────┘
```

---

### `/pr_review` - Comprehensive PR Review

**Best for**: Reviewing merge requests against Jira requirements

```bash
/pr_review INT-3877
/pr_review PLAT-54
```

**What it does**:
1. Fetches **full Jira ticket context** (description, acceptance criteria, developer checklist, test plan, comments, related tickets)
2. Fetches **all MR comments** (resolved/unresolved)
3. Spawns **8 specialized reviewers** in parallel:
   - Requirements compliance
   - Security (OWASP Top 10)
   - Performance (N+1 queries, inefficiencies)
   - Code quality (patterns, maintainability)
   - Tests (coverage, edge cases)
   - Breaking changes
   - Database impacts
   - Integration impacts
4. **7-layer voting system** (eliminates false positives)
5. Outputs structured markdown report with severity levels

**Token Savings**: Uses lightweight scripts instead of MCP (119,550 tokens saved per review)

#### `/pr_review` Workflow

```
┌─────────────────────────────────────────────────────────────┐
│                /pr_review <TICKET_ID>                       │
└─────────────────────────────────────────────────────────────┘
                            │
            ┌───────────────┴───────────────┐
            │                               │
            ▼                               ▼
┌───────────────────────┐       ┌───────────────────────┐
│ jira-get-issue        │       │ gitlab-mr-comments    │
│ Fetch FULL context:   │       │ Fetch ALL comments:   │
│ • Description         │       │ • Resolved            │
│ • Acceptance Criteria │       │ • Unresolved          │
│ • Developer Checklist │       │ • Inline comments     │
│ • Test Plan           │       └───────────┬───────────┘
│ • ALL Comments        │                   │
│ • Related Tickets     │                   │
└───────────┬───────────┘                   │
            │                               │
            └───────────────┬───────────────┘
                            │
                            ▼
        ┌───────────────────────────────────────┐
        │   Spawn 8 Reviewers in Parallel       │
        │                                        │
        │  ┌─────────────────────────────────┐  │
        │  │ 1. Requirements Reviewer        │  │
        │  │    • Matches acceptance criteria│  │
        │  │    • Fulfills user stories      │  │
        │  └─────────────────────────────────┘  │
        │                                        │
        │  ┌─────────────────────────────────┐  │
        │  │ 2. Security Reviewer            │  │
        │  │    • OWASP Top 10 check         │  │
        │  │    • SQL injection, XSS, etc.   │  │
        │  └─────────────────────────────────┘  │
        │                                        │
        │  ┌─────────────────────────────────┐  │
        │  │ 3. Performance Reviewer         │  │
        │  │    • N+1 queries                │  │
        │  │    • Inefficient algorithms     │  │
        │  └─────────────────────────────────┘  │
        │                                        │
        │  ┌─────────────────────────────────┐  │
        │  │ 4. Code Quality Reviewer        │  │
        │  │    • Patterns, maintainability  │  │
        │  └─────────────────────────────────┘  │
        │                                        │
        │  ┌─────────────────────────────────┐  │
        │  │ 5. Test Reviewer                │  │
        │  │    • Coverage, edge cases       │  │
        │  └─────────────────────────────────┘  │
        │                                        │
        │  ┌─────────────────────────────────┐  │
        │  │ 6. Breaking Changes Reviewer    │  │
        │  │    • API changes, deprecations  │  │
        │  └─────────────────────────────────┘  │
        │                                        │
        │  ┌─────────────────────────────────┐  │
        │  │ 7. Database Reviewer            │  │
        │  │    • Schema changes, migrations │  │
        │  └─────────────────────────────────┘  │
        │                                        │
        │  ┌─────────────────────────────────┐  │
        │  │ 8. Integration Reviewer         │  │
        │  │    • Service boundaries         │  │
        │  └─────────────────────────────────┘  │
        └───────────────────────────────────────┘
                            │
                            ▼
        ┌───────────────────────────────────────┐
        │      7-Layer Voting System            │
        │  (Eliminates false positives)         │
        │                                        │
        │  Each finding must pass:               │
        │  1. Evidence exists in code            │
        │  2. Severity justified                 │
        │  3. Not a false positive               │
        │  4. Actionable recommendation          │
        │  5. Aligned with ticket requirements   │
        │  6. Not already addressed in comments  │
        │  7. Actually matters for this PR       │
        └───────────────────────────────────────┘
                            │
                            ▼
                ┌───────────────────────┐
                │ Generate Markdown     │
                │ Report:               │
                │ • Summary             │
                │ • High severity       │
                │ • Medium severity     │
                │ • Low severity        │
                │ • Positive findings   │
                └───────────┬───────────┘
                            │
                            ▼
                        ┌───────┐
                        │ Done  │
                        └───────┘
```

---

### `/update_docs` - Documentation Sync

**Best for**: Keeping docs aligned with code

```bash
/update_docs
```

**What it does**:
1. Spawns multiple documentation-writer agents in parallel
2. Updates CLAUDE.md, README.md, QUICKREF.md, skills
3. Validates accuracy against actual code
4. Follows AI documentation best practices (tables over prose, concise, scannable)

---

## 🧠 Skills Library (32 Skills)

Skills are AI expertise modules that load automatically based on task context. No manual invocation needed.

### Quick Reference

| Category | Skills | Use When |
|----------|--------|----------|
| **Python** (6) | python-style, python-linting, python-packaging, async-python, testing-standards, debugging-strategies | Writing/debugging Python code |
| **Git & Workflows** (3) | git-workflows, test-driven-development, code-review-patterns | Git operations, TDD, PR reviews |
| **DevOps** (3) | ci-cd-pipelines, docker-optimization, kubernetes-patterns | CI/CD setup, containerization |
| **API & Database** (3) | api-design-patterns, database-design-patterns, mongodb-aggregation-optimization | API design, schema design |
| **Quality** (4) | code-refactoring, mutation-testing, vulnerability-triage, performance-profiling | Code quality, security, performance |
| **Automation** (4) | gitlab-scripts, jira-scripts, mcp-integration, orchestration-workflow | GitLab/Jira automation |
| **Meta** (3) | agent-prompting, ai-documentation, skill-authoring | Creating docs, skills, agents |
| **Frontend** (1) | frontend-patterns | React/Vue/TypeScript |

### How Skills Work

1. **Automatic Discovery**: Claude loads skills based on their descriptions when relevant
2. **Progressive Disclosure**: Core patterns in SKILL.md, details in reference.md
3. **Token Efficient**: ~30-50 tokens until fully loaded
4. **Composable**: Skills work together (see `~/.claude/skills/README.md` for synergies)

### Example Usage

Skills load automatically when you work on relevant tasks:

```bash
# Writing Python code → Loads: python-style, python-linting
# Writing tests → Loads: testing-standards, test-driven-development
# PR review → Loads: code-review-patterns, gitlab-scripts, jira-scripts
# Spawning agents → Loads: agent-prompting (MANDATORY before sub-agents)
```

See [`skills/README.md`](skills/README.md) for complete skill catalog and synergies.

---

## 🔧 Scripts (GitLab & Jira Automation)

Lightweight bash scripts that replace token-heavy MCP servers.

### Token Savings

| Tool | Functions | Tokens | Scripts | Script Tokens | Savings |
|------|-----------|--------|---------|---------------|---------|
| GitLab MCP | 82 | 80,000 | 6 | ~1,000 | **98.75%** |
| Jira MCP | 30 | 40,000 | 7 | ~1,750 | **95.6%** |
| **Combined** | 112 | **120,000** | **13** | **~2,750** | **97.7%** |

### GitLab Scripts

Located in `~/.claude/scripts/`:

- **`gitlab-mr-comments`** - Fetch all MR discussions (formatted markdown)
- **`gitlab-list-mrs`** - List merge requests with filters
- **`gitlab-create-mr`** - Create new merge request
- **`gitlab-comment-mr`** - Add MR comment
- **`gitlab-update-mr`** - Update MR metadata (title, description, labels)
- **`gitlab-inline-comment`** - Add inline code review comments
- **`git-worktree`** - Smart worktree manager for parallel development

### Jira Scripts

- **`jira-get-issue`** - Fetch **comprehensive** ticket context (description, acceptance criteria, developer checklist, test plan, ALL comments, related ticket details)
- **`jira-list-tickets`** - List tickets with filters
- **`jira-list-sprint`** - Show current sprint
- **`jira-create-ticket`** - Create new ticket
- **`jira-comment-ticket`** - Add comment
- **`jira-update-ticket`** - Update ticket fields
- **`jira-log-work`** - Log time (supports `2h 30m`, `1d 4h` format)
- **`jira-link-tickets`** - Link tickets with relationships

### Setup Credentials

```bash
# GitLab
cp ~/.claude/scripts/.gitlab-credentials.example ~/.claude/scripts/.gitlab-credentials
vim ~/.claude/scripts/.gitlab-credentials
# Add: GITLAB_PERSONAL_ACCESS_TOKEN, GITLAB_API_URL, GITLAB_PROJECT_ID

# Jira
cp ~/.claude/scripts/.jira-credentials.example ~/.claude/scripts/.jira-credentials
vim ~/.claude/scripts/.jira-credentials
# Add: ATLASSIAN_API_TOKEN, ATLASSIAN_SITE_NAME, ATLASSIAN_USER_EMAIL
```

See [`scripts/README.md`](scripts/README.md) for complete documentation.

---

## 🪝 Hooks System

Event-driven automation that runs at specific points in the workflow.

### Active Hooks

**PostToolUse Hooks** (in `settings.json`):
- **Edit/MultiEdit/Write** → `auto-format.sh`
  - Runs `ruff format` on Python files
  - Runs `prettier` on JS/TS files
  - Auto-formats on every code change

**PreCommit Hook** (Git):
- `hooks/pre-commit-validation.sh`
  - Validates code against anti-patterns
  - Checks security patterns
  - Blocks commits with issues

### Hook Development

Hooks in `~/.claude/hooks/`:

- `auto-format.sh` - Auto-formatting for Python/JS/TS
- `pre-commit-validation.sh` - Git pre-commit quality gates
- `patterns/` - Pattern definitions (anti-patterns, security, complexity)
- `archive/` - Deprecated hooks (PRISM integration, old validators)
- `transcript_parsing/` - Session analysis tools

---

## 📄 Templates

Reusable formats for specs, reviews, and documentation.

Located in `~/.claude/templates/`:

### Spec Templates
- **`spec-minimal.md`** - For `/solo` (BUILD spec)
- **`spec-full.md`** - For `/conduct` (SPEC.md with 10 sections)

### Review Templates
- **`pr-review-requirements.md`** - Requirements compliance
- **`pr-review-security.md`** - OWASP Top 10 security review
- **`pr-review-performance.md`** - Performance analysis
- **`pr-review-code-analysis.md`** - Code quality patterns
- **`pr-review-tests.md`** - Test coverage and quality
- **`pr-review-ripple-*.md`** - Breaking changes, DB impacts, integration impacts
- **`pr-review-verification.md`** - Evidence-based verification

### Operational Templates
- **`operational.md`** - Algorithms (fix-validate loops, dependency resolution)
- **`agent-responses.md`** - Structured agent output formats (NO prose)

### Pattern Templates
- **`INVARIANTS.md`** - Project invariants documentation
- **`GOTCHAS_TEMPLATE.md`** - Gotcha documentation pattern

---

## 📁 Directory Structure

```
~/.claude/
├── CLAUDE.md                    # Core work contract (principles, quality gates)
├── README.md                    # This file (human documentation)
├── settings.json                # Claude Code settings (hooks, output style)
│
├── commands/                    # Slash commands (orchestration)
│   ├── solo.md                 # /solo - streamlined implementation
│   ├── spec.md                 # /spec - discovery & planning
│   ├── conduct.md              # /conduct - multi-component orchestration
│   ├── pr_review.md            # /pr_review - comprehensive PR review
│   ├── update_docs.md          # /update_docs - documentation sync
│   └── coda.md                 # /coda - session summary
│
├── skills/                      # 32 domain skills (auto-loaded)
│   ├── README.md               # Skill catalog and synergies
│   ├── python-style/           # Python coding standards
│   ├── python-linting/         # Ruff/pyright usage
│   ├── testing-standards/      # Test organization (3-layer pyramid)
│   ├── agent-prompting/        # Sub-agent delegation (MANDATORY)
│   ├── git-workflows/          # Advanced Git (rebase, bisect, worktrees)
│   ├── gitlab-scripts/         # GitLab automation
│   ├── jira-scripts/           # Jira integration
│   └── [27 more skills...]
│
├── scripts/                     # Automation scripts (GitLab/Jira)
│   ├── README.md               # Script documentation
│   ├── gitlab-mr-comments      # Fetch MR comments
│   ├── gitlab-inline-comment   # Add inline code review
│   ├── jira-get-issue          # Fetch full ticket context
│   ├── [10 more scripts...]
│   ├── .gitlab-credentials     # GitLab API credentials (gitignored)
│   └── .jira-credentials       # Jira API credentials (gitignored)
│
├── hooks/                       # Event-driven automation
│   ├── auto-format.sh          # Auto-format on Edit/Write
│   ├── pre-commit-validation.sh # Git pre-commit quality gates
│   └── patterns/               # Pattern definitions
│
├── templates/                   # Reusable formats
│   ├── spec-*.md               # Spec templates (minimal/full)
│   ├── pr-review-*.md          # Review templates (8 reviewers)
│   ├── operational.md          # Algorithms
│   └── agent-responses.md      # Structured outputs
│
├── docs/                        # Core documentation
│   ├── OVERVIEW.md             # System architecture (this file context)
│   ├── ORCHESTRATION_GUIDE.md  # Command decision tree
│   ├── TESTING_STANDARDS.md    # Test requirements (95% coverage)
│   ├── AI_DOCUMENTATION_STANDARDS.md
│   ├── MCP_SETUP_INSTRUCTIONS.md
│   └── llms.txt                # Documentation index for AI
│
├── orchestration/               # Orchestration instructions
│   ├── SPEC_INSTRUCTIONS.md    # Discovery phase (for /spec)
│   ├── CONDUCT_INSTRUCTIONS.md # Execution phase (for /conduct)
│   └── ORCHESTRATOR_PATTERN.md # General orchestration principles
│
├── configs/                     # Language tool configs (fallbacks)
│   ├── ruff.toml               # Python linting
│   ├── .prettierrc             # JS/TS formatting
│   └── .golangci.yml           # Go linting
│
├── .claude/settings.local.json  # Local Claude Code settings
├── statusline-command.sh        # Custom status line
└── [session data...]            # History, todos, debug logs
```

---

## ⚙️ Configuration & Customization

### Global Settings (`~/.claude/settings.json`)

```json
{
  "hooks": {
    "PostToolUse": [
      { "matcher": "Edit", "hooks": [{ "command": "~/.claude/hooks/auto-format.sh" }] },
      { "matcher": "Write", "hooks": [{ "command": "~/.claude/hooks/auto-format.sh" }] }
    ]
  },
  "statusLine": { "command": "~/.claude/statusline-command.sh" },
  "outputStyle": "daily_driver",
  "alwaysThinkingEnabled": true,
  "permissions": { "defaultMode": "bypassPermissions" }
}
```

### Work Contract (`~/.claude/CLAUDE.md`)

Core principles that override default behavior:

- **RUN HOT**: Use full 200K token budget for thorough work
- **NO PARTIAL WORK**: Full implementation or explain why blocked
- **FAIL LOUD**: Errors surface with clear messages (never silent failures)
- **QUALITY GATES**: Tests + linting pass before claiming done
- **MULTIEDIT FOR SAME FILE**: Avoid parallel Edit race conditions
- **NO MASS UPDATES**: Use sub-agents, not scripts (manual = eyes on each change)

See [`CLAUDE.md`](CLAUDE.md) for complete work contract.

### Project-Specific Overrides

Create `CLAUDE.md` in any project root to override global settings:

```bash
cd ~/my-project
cat > CLAUDE.md <<EOF
# Project-Specific Rules

## Override Global Settings
- Use 100 char line length (not 80)
- Use Jest (not pytest)
- Never use TypeScript `any` type

## Project Context
- Monorepo with 15 packages
- Nx build system
- GraphQL + REST hybrid API
EOF
```

---

## 🧪 PRISM Semantic Memory (Optional)

Cross-session learning system that remembers patterns and decisions.

### What PRISM Does

- **Stores semantic code changes** (added_error_handling, bug_fix, refactoring)
- **Captures agent discoveries** (patterns, decisions, gotchas)
- **Detects user preferences** (repeated corrections → enforced rules)
- **Injects relevant context** into prompts and agent launches
- **Promotes patterns across tiers** (WORKING → LONGTERM → ANCHORS)

### Memory Tiers

- **ANCHORS**: Critical rules (violations block execution)
- **LONGTERM**: Stable patterns (3+ uses or 85%+ confidence)
- **WORKING**: Session-specific (cleared between sessions)
- **EPISODIC**: Recent events (time-based decay)

### Setup PRISM (Optional)

PRISM requires separate MCP server setup:

```bash
# Clone PRISM MCP
git clone <prism-mcp-repo> ~/repos/claude_mcp/prism_mcp

# Start PRISM services (Redis, Neo4j, Qdrant)
cd ~/repos/claude_mcp/prism_mcp
nerdctl compose up -d

# Verify PRISM running
curl http://localhost:8090/health
```

See [`docs/MCP_SETUP_INSTRUCTIONS.md`](docs/MCP_SETUP_INSTRUCTIONS.md) for complete setup.

**Note**: PRISM is optional. All orchestration commands work without it.

---

## 🎨 Output Styles

### Daily Driver (Default)

Configured in `settings.json`: `"outputStyle": "daily_driver"`

**Personality**: Witty companion who gets shit done
- Brutally honest and direct
- Casual tone with humor
- Concise explanations (no fluff)
- No code snippets (describes what code does verbally)
- Validates before claiming things work

**Example Output**:
```
Found 47 TODO comments from 2019. Someone was optimistic.

Spawning 6 reviewers in parallel. Code review by committee, but they can't argue.

This variable is called `data2_final_ACTUAL_final`. I have questions.
```

---

## 📚 Documentation Standards

### AI-Optimized Documentation

This configuration follows AI documentation best practices:

- **Concise over comprehensive** (agents can read code)
- **Structure over prose** (tables/bullets over paragraphs)
- **Location over explanation** (file:line references)
- **Hierarchical CLAUDE.md** (100-200 line rule, no duplication)

### Documentation Hierarchy

1. **CLAUDE.md** - Core patterns and rules (100-200 lines)
2. **OVERVIEW.md** - System architecture and navigation
3. **QUICKREF.md** - Deep-dive examples and code snippets
4. **BUSINESS_RULES.md** - Authoritative business logic catalog
5. **llms.txt** - Documentation index for AI agents

See [`docs/AI_DOCUMENTATION_STANDARDS.md`](docs/AI_DOCUMENTATION_STANDARDS.md) for complete guide.

---

## 🧩 Key Workflows

### Overall Orchestration Pattern

```
┌─────────────────────────────────────────────────────────────────┐
│                   Claude Code Orchestration                     │
│                  (Multi-Agent Architecture)                     │
└─────────────────────────────────────────────────────────────────┘

                         User Request
                              │
                              ▼
        ┌─────────────────────────────────────┐
        │   Main Orchestrator (Sonnet 4.5)    │
        │   • Analyzes task complexity         │
        │   • Chooses orchestration command    │
        │   • Loads agent-prompting skill      │
        │   • Delegates to specialized agents  │
        └───────────────┬─────────────────────┘
                        │
        ┌───────────────┼───────────────┐
        │               │               │
        ▼               ▼               ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│   /solo      │  │   /spec      │  │  /conduct    │
│              │  │              │  │              │
│ • 1-3 files  │  │ • Discovery  │  │ • Multi-     │
│ • Clear req  │  │ • Spike test │  │   component  │
│ • Standard   │  │ • Create     │  │ • Dependency │
│   patterns   │  │   SPEC.md    │  │   aware      │
└──────┬───────┘  └──────┬───────┘  └──────┬───────┘
       │                 │                 │
       │                 └────────┬────────┘
       │                          │
       ▼                          ▼
┌──────────────────────────────────────────┐
│      Specialized Agents (Parallel)       │
│                                           │
│  ┌────────────────────────────────────┐  │
│  │ Implementation Agents              │  │
│  │ • skeleton-builder                 │  │
│  │ • implementation-executor          │  │
│  │ • test-implementer                 │  │
│  └────────────────────────────────────┘  │
│                                           │
│  ┌────────────────────────────────────┐  │
│  │ Validation Agents (6 in parallel)  │  │
│  │ • security-auditor                 │  │
│  │ • performance-optimizer            │  │
│  │ • code-reviewer (3x)               │  │
│  └────────────────────────────────────┘  │
│                                           │
│  ┌────────────────────────────────────┐  │
│  │ Utility Agents                     │  │
│  │ • fix-executor (for failures)      │  │
│  │ • spike-tester (validation)        │  │
│  │ • documentation-writer             │  │
│  └────────────────────────────────────┘  │
└──────────────────┬───────────────────────┘
                   │
                   ▼
        ┌──────────────────────┐
        │   Quality Gates      │
        │                      │
        │ • Linting: ruff      │
        │ • Type check: pyright│
        │ • Tests: 95%+ cov    │
        │ • Security: OWASP    │
        │ • Performance: N+1   │
        └──────────┬───────────┘
                   │
            ┌──────┴──────┐
            │             │
           PASS          FAIL
            │             │
            │             ▼
            │    ┌──────────────┐
            │    │ fix-executor │
            │    │ (max 3 loops)│
            │    └──────┬───────┘
            │           │
            └───────────┘
                   │
                   ▼
        ┌──────────────────────┐
        │   Documentation      │
        │   • Update CLAUDE.md │
        │   • Update README    │
        │   • Update skills    │
        └──────────┬───────────┘
                   │
                   ▼
        ┌──────────────────────┐
        │   Cleanup & Commit   │
        │   • Remove .spec/    │
        │   • Git commit       │
        │   • Claude co-author │
        └──────────┬───────────┘
                   │
                   ▼
               ┌────────┐
               │  Done  │
               └────────┘

Parallel Execution Example:
┌──────────────────────────────────────────────────────────────┐
│  Main Orchestrator sends single message with 6 Task calls:  │
│                                                              │
│  Task(security-auditor, ...) ────┐                          │
│  Task(performance-optimizer, ...)│ All execute              │
│  Task(code-reviewer, ...)────────┤ simultaneously           │
│  Task(code-reviewer, ...)────────┤ (token efficient)        │
│  Task(code-reviewer, ...)────────┤                          │
│  Task(style-reviewer, ...) ──────┘                          │
│                                                              │
│  Results aggregated → single validation report              │
└──────────────────────────────────────────────────────────────┘
```

---

### Simple Feature Implementation

```bash
/solo add rate limiting middleware to API

# What happens:
# 1. Creates .spec/BUILD_rate-limit.md (minimal spec)
# 2. Spawns implementation-executor agent
# 3. Spawns test-implementer agent
# 4. Validates with 6 reviewers (security, performance, code quality)
# 5. Runs pytest with coverage (95%+ required)
# 6. Merges learnings into permanent docs
# 7. Cleans up .spec/
```

### Complex Feature with Planning

```bash
/spec design event-driven system with gRPC

# Discovery phase:
# 1. Asks clarifying questions
# 2. Investigates existing code
# 3. Identifies concerns/risks
# 4. Spike tests approaches in /tmp
# 5. Creates .spec/SPEC.md

/conduct

# Execution phase:
# 1. Parses SPEC.md → dependency graph
# 2. Implements components in order
# 3. Per-component validation
# 4. Integration testing
# 5. Final documentation
```

### PR Review Against Jira Ticket

```bash
/pr_review INT-3877

# What happens:
# 1. Fetches full Jira context (ticket + related tickets + comments)
# 2. Fetches all MR comments
# 3. Spawns 8 reviewers in parallel
# 4. Applies 7-layer voting system (eliminates false positives)
# 5. Outputs structured markdown report
```

### Documentation Update

```bash
/update_docs

# What happens:
# 1. Spawns parallel documentation-writer agents
# 2. Updates CLAUDE.md, README.md, skills
# 3. Validates against actual code
# 4. Follows AI documentation standards
```

---

## 🔍 Troubleshooting

### Hooks Not Running

```bash
# Check hook configuration
cat ~/.claude/settings.json | jq '.hooks'

# Check hook permissions
ls -la ~/.claude/hooks/*.sh

# Test hook manually
~/.claude/hooks/auto-format.sh Edit test.py
```

### Scripts Failing

```bash
# Missing credentials
# Error: "❌ Credentials file not found"
cp ~/.claude/scripts/.gitlab-credentials.example ~/.claude/scripts/.gitlab-credentials
vim ~/.claude/scripts/.gitlab-credentials

# Test script
~/.claude/scripts/gitlab-mr-comments INT-3877
echo $?  # Should be 0
```

### Orchestration Stuck

```bash
# Check progress
cat .spec/PROGRESS.md

# Check agent output
# Look for ESCALATE or BLOCKED messages in response
```

### PRISM Not Working (Optional)

```bash
# Verify PRISM running
curl http://localhost:8090/health

# Restart PRISM
cd ~/repos/claude_mcp/prism_mcp
nerdctl compose restart
```

---

## 📖 Further Reading

- **For Users**:
  - [`docs/ORCHESTRATION_GUIDE.md`](docs/ORCHESTRATION_GUIDE.md) - Command decision tree
  - [`skills/README.md`](skills/README.md) - Skill catalog and synergies
  - [`scripts/README.md`](scripts/README.md) - Script documentation
  - [`docs/TESTING_STANDARDS.md`](docs/TESTING_STANDARDS.md) - Test requirements

- **For AI Agents**:
  - [`docs/OVERVIEW.md`](docs/OVERVIEW.md) - System architecture
  - [`docs/llms.txt`](docs/llms.txt) - Documentation index
  - [`orchestration/`](orchestration/) - Orchestration instructions
  - [`templates/`](templates/) - Spec and response formats

- **For Developers**:
  - [`docs/AI_DOCUMENTATION_STANDARDS.md`](docs/AI_DOCUMENTATION_STANDARDS.md) - Writing AI-friendly docs
  - [`docs/MCP_SETUP_INSTRUCTIONS.md`](docs/MCP_SETUP_INSTRUCTIONS.md) - MCP server setup
  - [`hooks/HOOKS_IDEAS.md`](hooks/HOOKS_IDEAS.md) - Hook development ideas

---

## 🤝 Contributing

### Adding New Skills

```bash
cd ~/.claude/skills
mkdir my-new-skill
cd my-new-skill

cat > SKILL.md <<EOF
---
name: my-new-skill
description: Brief description (includes "Use when...")
---

# My New Skill

[Skill content following skill-authoring guidelines]
EOF
```

See `skill-authoring` skill for complete guidelines.

### Adding New Scripts

```bash
cd ~/.claude/scripts

# Use template from scripts/README.md
# Follow exit code conventions: 0=success, 1=args, 2=not found, 3=API error, 4=creds
```

### Customizing Orchestration

Edit command files in `~/.claude/commands/`:
- `solo.md` - Streamlined implementation
- `spec.md` - Discovery & planning
- `conduct.md` - Multi-component orchestration

---

## 📊 Metrics

**Token Efficiency**:
- Scripts vs MCP: **97.7% token savings** (120,000 → 2,750 tokens)
- PR Review workflow: **119,550 tokens saved** per review

**Quality Gates**:
- 6 parallel reviewers: security, performance, code quality (3x), style, docs
- 7-layer voting system eliminates false positives
- 95%+ test coverage required
- Zero linting errors before completion

**Productivity**:
- `/solo`: 10-20k tokens, 5-15 min for simple features
- `/spec` + `/conduct`: 50k+ tokens, 30-60 min for complex features
- `/pr_review`: 30-60k tokens, 10-20 min for comprehensive review

---

## 📝 License

Personal configuration - use and modify as you see fit.

---

## 🙏 Acknowledgments

Built on top of [Claude Code](https://docs.claude.com/claude-code) by Anthropic.

Inspired by:
- AI documentation best practices
- Multi-agent orchestration patterns
- Semantic memory systems (PRISM)
- GitLab/Jira API efficiency

---

**Version**: 2.0 (October 2025)
**Last Updated**: 2025-10-27
**Claude Model**: Sonnet 4.5
