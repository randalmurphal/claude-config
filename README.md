# Claude Code Configuration

Personal `.claude` setup optimized for Opus 4.5 with judgment-based orchestration, automation scripts, and domain skills.

---

## Philosophy

**Investigation scales with blast radius, not task complexity.**

Changing a utility used in 50 places needs thorough investigation even if the change is "simple." Building a new standalone script needs minimal investigation even if it's complex.

**Model selection is about fit, not token cost.**

Use Opus when judgment matters (investigation, validation, risk assessment). Use Sonnet for mechanical implementation. Don't downgrade to save tokens.

**No ceremony for simple tasks.**

Just ask Claude to do it. Orchestration commands exist for genuinely complex work, not to add process to straightforward tasks.

---

## When to Use Commands

| Situation | What to Do |
|-----------|------------|
| Simple task, clear requirements | Just ask directly |
| Uncertain scope, need investigation | `/spec` |
| Multi-component with dependencies | `/spec` → `/conduct` |
| Review MR against Jira ticket | `/pr_review TICKET-123` |
| End session, need handoff summary | `/coda` |

That's it. No decision trees. Use your judgment.

---

## Commands

### `/spec` - Investigation & Planning

For uncertain scope where you need to investigate before committing.

```bash
/spec design event-driven system with gRPC
/spec investigate options for real-time notifications
```

Creates `.spec/SPEC.md` with findings, architecture decisions, and component breakdown.

### `/conduct` - Multi-Component Execution

For implementing complex features from a spec. Requires `.spec/SPEC.md` from `/spec`.

```bash
/conduct
```

Handles dependency ordering, per-component validation, and integration testing.

### `/pr_review` - MR Review

Reviews merge request against Jira ticket requirements.

```bash
/pr_review INT-3877
```

Fetches full Jira context, MR comments, spawns parallel reviewers, eliminates false positives.

### `/coda` - Session Handoff

Generates concise summary for context handoff.

```bash
/coda
```

---

## Scripts

### Global Scripts (any project)

| Script | Purpose |
|--------|---------|
| `python-code-quality` | Unified Python linting (ruff + pyright + bandit + semgrep) |
| `git-worktree` | Smart worktree manager for parallel development |
| `gitlab-list-discussions` | List MR discussion threads |
| `gitlab-reply-discussion` | Reply to MR discussions |

### Project Scripts

Full Jira/GitLab automation scripts live in project repos for team use:
- `m32rimm/.claude/scripts/` - Complete jira-* and gitlab-* suite with credentials

See [`scripts/README.md`](scripts/README.md) for global script details.

---

## Skills

~30 domain skills that load automatically based on context.

| Category | Skills |
|----------|--------|
| Python | python-style, python-linting, python-packaging, async-python |
| Testing | testing-standards, test-driven-development, mutation-testing |
| Git | git-workflows, code-review-patterns |
| DevOps | ci-cd-pipelines, docker-optimization, kubernetes-patterns |
| Data | database-design-patterns, mongodb-aggregation-optimization |
| Quality | code-refactoring, debugging-strategies, performance-profiling |
| Meta | agent-prompting, ai-documentation, skill-authoring |

See [`skills/README.md`](skills/README.md) for full catalog.

---

## Agents

19 specialized agents for orchestration:

**Building:** skeleton-builder, implementation-executor, general-builder, general-haiku-builder

**Testing:** test-skeleton-builder, test-implementer

**Review:** code-reviewer, security-auditor, performance-optimizer, code-beautifier

**Documentation:** documentation-writer, documentation-reviewer

**Utilities:** general-investigator, spike-tester, fix-executor, consolidation-analyzer, merge-coordinator, architecture-planner, dependency-analyzer

---

## Directory Structure

```
~/.claude/
├── CLAUDE.md              # Work contract (core principles)
├── README.md              # This file
├── settings.json          # Claude Code settings
│
├── commands/              # Orchestration commands
│   ├── spec.md           # /spec - investigation
│   ├── conduct.md        # /conduct - execution
│   ├── pr_review.md      # /pr_review - MR review
│   └── coda.md           # /coda - handoff
│
├── skills/                # ~30 domain skills
├── agents/                # 19 specialized agents
├── scripts/               # GitLab/Jira automation
├── templates/             # Spec and review templates
├── configs/               # Language tool configs
└── hooks/                 # Event-driven automation
```

---

## Configuration

### settings.json

```json
{
  "outputStyle": "daily_driver",
  "alwaysThinkingEnabled": true,
  "statusLine": { "command": "~/.claude/statusline-command.sh" },
  "permissions": { "defaultMode": "dontAsk" }
}
```

### CLAUDE.md

Core principles:
- **INVESTIGATE BEFORE MODIFYING** - Blast radius drives investigation depth
- **RUN HOT** - Use full token budget for thorough work
- **NO PARTIAL WORK** - Full implementation or explain why blocked
- **FAIL LOUD** - Errors surface with clear messages
- **Model selection is about fit** - Opus for judgment, Sonnet for implementation

See [`CLAUDE.md`](CLAUDE.md) for complete contract.

---

## Model Selection

| Activity | Model |
|----------|-------|
| Investigation / impact analysis | Opus |
| Validation / review (shared code) | Opus |
| Architecture decisions | Opus |
| Mechanical implementation | Sonnet |
| Review (isolated changes) | Sonnet |
| Simple searches | Haiku |

---

## Quick Start

1. Clone into home directory:
   ```bash
   cd ~ && git clone <repo> .claude
   ```

2. Set up credentials (in project repos):
   ```bash
   # Scripts and credentials are in each project's .claude/scripts/
   # Example for m32rimm:
   cd ~/repos/m32rimm
   cp .claude/scripts/.gitlab-credentials.example .claude/scripts/.gitlab-credentials
   cp .claude/scripts/.jira-credentials.example .claude/scripts/.jira-credentials
   # Edit with your tokens
   ```

3. Start using:
   ```bash
   # Simple tasks - just ask
   "Add rate limiting to the API endpoint"

   # Complex/uncertain - use commands
   /spec design new authentication system
   /pr_review INT-1234
   ```

---

## Troubleshooting

### Scripts failing

```bash
# Scripts are in project directories, not ~/.claude/scripts/
# Example for m32rimm:
cd ~/repos/m32rimm

# Check credentials exist
ls .claude/scripts/.gitlab-credentials
ls .claude/scripts/.jira-credentials

# Test script
.claude/scripts/jira-get-issue INT-1234
```

### Skills not loading

Skills load automatically based on description matching. Check skill exists:
```bash
ls ~/.claude/skills/
```

---

**Version**: 3.0 (November 2025)
**Model**: Opus 4.5
