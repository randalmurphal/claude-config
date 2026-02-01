# Claude Code Skills Library

Personal skills organized by category. Skills activate automatically based on their descriptions - no manual invocation needed.

**Total Skills:** 33

---

## Git & Workflows (3 skills)

| Skill | Description | Use When |
|-------|-------------|----------|
| **git-workflows** | Advanced Git (rebase, bisect, worktrees, conflict resolution) | Complex git operations, history cleanup, managing branches |
| **test-driven-development** | TDD cycle (red-green-refactor, test-first) | Implementing features, refactoring, using tests to drive design |
| **code-review-patterns** | Code review best practices, constructive feedback | Reviewing PRs, providing/handling feedback |

## Python Development (6 skills)

| Skill | Description | Use When |
|-------|-------------|----------|
| **python-linting** | Ruff/pyright usage, fixing violations | Fixing linting errors, configuring tools |
| **python-style** | Code standards (80 chars, naming, type hints, logging) | Writing new Python code, reviewing code quality |
| **python-packaging** | Poetry, pip, uv dependency management | Managing dependencies, resolving conflicts, security audits |
| **async-python** | Async/await patterns, asyncio, concurrency | Writing async code, debugging async issues |
| **testing-standards** | Test organization (3-layer pyramid, 1:1 mapping, 95% coverage) | Writing tests, checking coverage, validating structure |
| **debugging-strategies** | Root-cause tracing, pdb, binary search debugging | Debugging errors, tracing bugs through call stacks |

## Debugging & Quality (4 skills)

| Skill | Description | Use When |
|-------|-------------|----------|
| **code-refactoring** | Complexity reduction, extract method patterns | Functions >50 lines, complexity warnings |
| **mutation-testing** | Test quality validation with mutmut/cosmic-ray | Validating test effectiveness, achieving high test quality |
| **vulnerability-triage** | Security assessment (CVSS, OWASP Top 10) | Analyzing vulnerabilities, calculating risk scores |
| **performance-profiling** | cProfile, memory_profiler, py-spy | Code is slow, debugging performance issues |

## DevOps & Infrastructure (3 skills)

| Skill | Description | Use When |
|-------|-------------|----------|
| **ci-cd-pipelines** | GitLab CI/CD patterns, testing stages, deployments | Creating .gitlab-ci.yml, optimizing CI, setting up pipelines |
| **docker-optimization** | Multi-stage builds (70%+ reduction), security scanning | Creating Dockerfiles, reducing image size, scanning for vulnerabilities |
| **kubernetes-patterns** | K8s deployments, services, ingress, kubectl | Deploying to Kubernetes, managing containers, troubleshooting pods |

## API & Database (3 skills)

| Skill | Description | Use When |
|-------|-------------|----------|
| **api-design-patterns** | REST API design, versioning, pagination, authentication | Designing APIs, documenting endpoints, implementing auth |
| **database-design-patterns** | Schema design, normalization, indexes, migrations | Designing schemas, optimizing queries, setting up migrations |
| **mongodb-aggregation-optimization** | MongoDB pipeline optimization | Writing aggregation queries, debugging slow pipelines |

## Frontend (1 skill)

| Skill | Description | Use When |
|-------|-------------|----------|
| **frontend-patterns** | React/Vue/TypeScript, state management, testing | Building frontend apps, managing state, optimizing performance |

## Collaboration & Automation (4 skills)

| Skill | Description | Use When |
|-------|-------------|----------|
| **gitlab-scripts** | GitLab automation scripts | Fetching MR data, automating GitLab workflows |
| **jira-scripts** | Jira integration scripts | Fetching issue data, automating Jira workflows |
| **mcp-integration** | MCP server setup (PRISM, Jira, MongoDB, etc.) | Setting up MCP servers, debugging MCP connections |
| **orchestration-workflow** | /solo, /spec, /conduct command patterns | Planning complex work, orchestrating multi-agent tasks |

## Development Discipline (6 skills, adapted from [superpowers](https://github.com/obra/superpowers))

| Skill | Description | Use When |
|-------|-------------|----------|
| **brainstorming** | Collaborative design exploration through focused questioning | Starting non-trivial features, design, behavior changes - before code |
| **systematic-debugging** | Root cause investigation before any fix attempt | Any failure, bug, unexpected behavior - before attempting fixes |
| **test-driven-development** | Strict RED-GREEN-REFACTOR enforcement | Implementing features, bug fixes, behavior changes - before writing code |
| **verification-before-completion** | Fresh evidence required before any completion claim | Before claiming tests pass, builds succeed, or fixes work |
| **receiving-code-review** | Technical evaluation of feedback, not performative agreement | Receiving review feedback, especially if unclear or questionable |
| **writing-skills** | TDD methodology applied to skill creation | Creating new skills, editing existing skills |

## Meta / Framework (3 skills)

| Skill | Description | Use When |
|-------|-------------|----------|
| **agent-prompting** | Sub-agent delegation, prompt engineering | Spawning sub-agents (MUST USE PROACTIVELY) |
| **ai-documentation** | CLAUDE.md writing (hierarchical inheritance, 100-200 line rule) | Writing documentation, optimizing existing docs |
| **skill-authoring** | Creating/updating skills (YAML frontmatter, <500 lines, progressive disclosure) | Creating new skills, updating existing skills |

---

## Skill Synergies (Common Workflows)

### Feature Workflow (Discipline-First)
1. `brainstorming` → explore design before coding
2. `test-driven-development` → write tests first, always
3. `python-style` / language skill → write implementation
4. `verification-before-completion` → prove it works
5. `git-workflows` → manage branches

### Testing Workflow
1. `testing-standards` → write tests (structure)
2. `test-driven-development` → follow TDD cycle (workflow)
3. `mutation-testing` → validate test quality
4. `python-linting` → check code quality
5. `systematic-debugging` → debug failing tests

### Code Review Workflow
1. `gitlab-scripts` → fetch MR comments
2. `jira-scripts` → fetch requirements
3. `code-review-patterns` → review process
4. `receiving-code-review` → handle feedback properly
5. `vulnerability-triage` → security review

### Bug Fix Workflow
1. `systematic-debugging` → investigate root cause first
2. `test-driven-development` → write failing test reproducing bug
3. Implementation → minimal fix
4. `verification-before-completion` → prove fix works

### Implementation Workflow
1. `orchestration-workflow` → plan work (/solo, /spec, /conduct)
2. `agent-prompting` → delegate to sub-agents
3. `python-style` → write code
4. `testing-standards` → write tests
5. `git-workflows` → manage branches

### DevOps Workflow
1. `docker-optimization` → build images
2. `ci-cd-pipelines` → automate builds
3. `kubernetes-patterns` → deploy containers

### Documentation Workflow
1. `ai-documentation` → write CLAUDE.md
2. `skill-authoring` → write skills
3. `api-design-patterns` → document APIs

---

## Usage Notes

- **Skills activate automatically** - Claude discovers skills based on descriptions
- **No manual invocation needed** - Skills load when relevant to your task
- **Token-efficient** - Each skill uses only 30-50 tokens until fully loaded
- **Progressive disclosure** - Core patterns in SKILL.md, details in reference.md
- **Composable** - Skills work together (see synergies above)

---

## Adding New Skills

1. Create directory: `~/.claude/skills/my-skill/`
2. Create `SKILL.md` with YAML frontmatter
3. Follow `skill-authoring` skill guidelines:
   - Name ≤64 chars (lowercase, hyphens)
   - Description ≤1024 chars (third-person, includes "Use when...")
   - SKILL.md <500 lines (extract details to reference.md)
   - Tables over prose
   - Before/after examples
   - Quick reference section
4. Test with realistic prompts

See `skill-authoring` skill for complete guidance.

---

## Skill Categories

```
Development (6)       Testing (4)           DevOps (3)
├─ python-linting     ├─ testing-standards  ├─ ci-cd-pipelines
├─ python-style       ├─ tdd                ├─ docker-optimization
├─ python-packaging   ├─ mutation-testing   └─ kubernetes-patterns
├─ async-python       └─ debugging-strategies
├─ api-design-patterns
└─ database-design

Git (1)               Quality (3)           Frontend (1)
└─ git-workflows      ├─ code-refactoring   └─ frontend-patterns
                      ├─ vulnerability-triage
                      └─ code-review-patterns

Automation (2)        Meta (3)              Performance (1)
├─ gitlab-scripts     ├─ agent-prompting    └─ performance-profiling
└─ jira-scripts       ├─ ai-documentation
                      └─ skill-authoring

Discipline (6)        Integration (2)
├─ brainstorming      ├─ mcp-integration
├─ systematic-debug   └─ orchestration-workflow
├─ tdd
├─ verification
├─ receiving-review
└─ writing-skills
```

---

**Last Updated:** 2026-02-01
**Skills Version:** 3.0 (added discipline skills from superpowers)
