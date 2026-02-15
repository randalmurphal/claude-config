---
name: AI Documentation Standards
description: Write AI-readable documentation using context engineering principles, Claude Code's documentation hierarchy (.claude/rules/, CLAUDE.md inheritance), structured formats, and the litmus test. Use when writing documentation, updating docs, or optimizing existing docs.
allowed-tools: Read, Write, Edit, Grep, Glob
---

# AI Documentation Standards

Documentation is context for AI agents. Every token competes for attention. Write the minimum high-signal content that maximizes correct agent behavior.

**The Litmus Test**: For each line, ask: "Would removing this cause the agent to make mistakes?" If not, cut it.

---

## Context Engineering Foundation

From Anthropic's official guidance — these principles govern all documentation decisions:

### Core Principles

| Principle | Meaning | Implication |
|-----------|---------|-------------|
| **Minimize, don't maximize** | Smallest set of high-signal tokens that produce correct behavior | Shorter docs > longer docs. Cut aggressively |
| **Right altitude** | Specific enough to guide, flexible enough for heuristics | Not brittle hardcoded rules, not vague platitudes |
| **Examples over rules** | One good example > paragraph of explanation | Point to real code patterns in the codebase |
| **Just-in-time loading** | Essentials upfront, details on demand | CLAUDE.md = lean pointers. Detailed docs = separate files agents read when needed |

### Four Context Anti-Patterns

| Anti-Pattern | Description | Documentation Impact |
|---|---|---|
| **Context Poisoning** | Stale or incorrect information | Outdated file structures, removed features, old commands |
| **Context Distraction** | Irrelevant information loaded every session | Feature-specific guidance in global docs |
| **Context Confusion** | Similar but distinct information mixed together | Mixing architecture and implementation detail |
| **Context Clash** | Contradictory instructions | Duplicated rules that drift apart over time |

### Token Budget Reality

Auto-loaded docs (CLAUDE.md, rules/) consume context before any work begins. A typical project baseline is ~20K tokens. Bloated documentation eats into the agent's working memory for actual tasks.

---

## Claude Code Documentation Hierarchy

Claude Code loads documentation in layers. Understand the hierarchy to put information in the right place.

### The Layers (Most Global → Most Specific)

| Layer | Location | Scope | Loaded When |
|-------|----------|-------|-------------|
| **Managed policy** | `/etc/claude-code/CLAUDE.md` | Organization-wide | Always |
| **User global** | `~/.claude/CLAUDE.md` | All projects for this user | Always |
| **Project root** | `./CLAUDE.md` or `./.claude/CLAUDE.md` | Whole project | Always |
| **Project rules** | `./.claude/rules/*.md` | Topic-specific (can be path-scoped) | Always (filtered by path match) |
| **Subdirectory** | `subdir/CLAUDE.md` | That subtree only | When agent reads files in subtree |
| **Local override** | `./CLAUDE.local.md` | Personal, one project | Always (gitignored) |
| **Auto memory** | `~/.claude/projects/<id>/memory/` | Auto-generated per project | First 200 lines, always |

### Key Mechanisms

**`@import` syntax**: CLAUDE.md can reference other files: `@path/to/file.md`. Resolves relative to the containing file. Max depth 5. Use sparingly — every import adds to always-loaded context. Pitch the agent on *when* to consult a file rather than importing the whole thing:

```markdown
# Good: pointer with context
For complex error recovery patterns, see docs/ERROR_PATTERNS.md

# Bad: importing everything into always-loaded context
@docs/ERROR_PATTERNS.md
```

**Path-scoped rules**: Files in `.claude/rules/` support frontmatter that activates them only for matching files:

```markdown
---
paths:
  - "src/api/**/*.ts"
---
# API Development Rules
- All endpoints must include input validation
- Use zod schemas for request/response types
```

This is the primary mechanism for splitting documentation. Rules only load when the agent works on matching files — zero cost otherwise.

**Auto memory**: Claude writes session insights to `~/.claude/projects/<id>/memory/MEMORY.md`. First 200 lines load every session. Use `/memory` or tell Claude "remember that we use pnpm" to persist notes. This replaces manual session knowledge capture for project-specific patterns.

---

## What to Document (and What Not To)

### Include

- Commands the agent cannot guess (build, test, lint with project-specific flags)
- Code style rules that **differ from language defaults**
- Architecture decisions specific to your project
- Common gotchas and non-obvious behaviors
- Boundaries: what the agent should never touch

### Exclude

- Anything the agent can figure out by reading code
- Standard language conventions (the agent already knows these)
- Long explanations or tutorials (provide checklists instead)
- Information that changes frequently (it will become stale context poison)
- File-by-file descriptions (the agent has `grep` and `glob`)

### Hooks for Enforcement, Docs for Guidance

If something **must** happen every time (formatting, linting, test execution), use a hook — deterministic enforcement. If something is **advisory** (architecture preferences, patterns to prefer), use documentation. Don't ask documentation to do a linter's job.

---

## Formatting Principles

### Structure Over Prose

AI agents parse structured content faster. Prefer in this order:

1. **Tables** — for any information with consistent columns (rules, mappings, decisions)
2. **Bullet points** — for lists, steps, options
3. **Code snippets** — for patterns and examples
4. **Short paragraphs** — only when narrative context is truly needed

### Never Use Line Numbers as References

Line numbers become stale immediately when code changes. This is context poisoning.

```markdown
# Bad: becomes wrong after any edit to the file
See `auth.py:147` for the session validation logic

# Good: stable reference the agent can find
See `validate_session()` in `src/auth/session.py`

# Good: pattern reference
Follow the error handling pattern in `UserService`
```

Reference **files**, **function/class names**, **directories**, and **patterns** — never line numbers.

### Examples Over Rules

One concrete example from the actual codebase is worth more than a paragraph of rules:

```markdown
# Bad: abstract rule
Use consistent error handling with proper logging and user-facing messages.

# Good: point to a real example
Error handling pattern: see `handleApiError()` in `src/api/client.ts`
```

---

## When and How to Split Documentation

### Decision Framework

| Signal | Action |
|--------|--------|
| CLAUDE.md exceeds ~300 lines | Extract topic-specific content to `.claude/rules/` |
| Guidance only applies to certain files | Use path-scoped rules in `.claude/rules/` |
| Detailed reference material (templates, schemas) | Put in `docs/` — agents read on demand |
| Multiple AI tools need the same instructions | Create `AGENTS.md`, reference from tool-specific files |
| Same information appears in multiple docs | Extract to single source, reference from others |

### The Progressive Disclosure Pattern

Keep auto-loaded docs (CLAUDE.md, rules/) lean with pointers. Detailed docs live in `docs/` or alongside code — agents load them on demand when they read files in those directories.

```markdown
# In CLAUDE.md (auto-loaded, keep lean)
## Architecture
Key directories: src/api/, src/services/, src/stores/
For detailed architecture decisions, see docs/ARCHITECTURE.md

# In docs/ARCHITECTURE.md (loaded on demand)
[Detailed architecture documentation here — can be comprehensive]
```

**Rule**: Auto-loaded files should be concise. On-demand files can be thorough.

### Monorepo Pattern

For monorepos, use subdirectory CLAUDE.md files. Running Claude from `foo/bar/` loads both `foo/CLAUDE.md` and `foo/bar/CLAUDE.md`. More specific instructions take precedence.

```
monorepo/
├── CLAUDE.md                    # Universal: build commands, code style, git conventions
├── .claude/rules/
│   ├── testing.md               # Testing conventions (all files)
│   └── api-standards.md         # API rules (paths: src/api/**)
├── frontend/
│   └── CLAUDE.md                # React patterns, component conventions
├── backend/
│   └── CLAUDE.md                # Service patterns, DB conventions
└── docs/                        # On-demand detailed references
    ├── ARCHITECTURE.md
    └── BUSINESS_RULES.md
```

---

## Cross-Tool Considerations (AGENTS.md)

AGENTS.md is a vendor-neutral standard (Linux Foundation, 60K+ repos, 25+ tools including OpenAI Codex, Cursor, Google Jules).

If your team uses multiple AI coding tools, maintain AGENTS.md as the canonical source:

```markdown
# In CLAUDE.md
@AGENTS.md
# Plus any Claude-specific additions (hooks, skills, slash commands)
```

| Aspect | CLAUDE.md | AGENTS.md |
|--------|-----------|-----------|
| **Audience** | Claude Code specifically | All AI coding tools |
| **Special features** | `@import`, `.claude/rules/`, path-scoping | Standard markdown, no special syntax |
| **Recommendation** | Use both if multi-tool team; CLAUDE.md-only if Claude-only |

---

## Content Optimization Strategies

When documentation is too long, apply these in order:

| Strategy | When to Use | Typical Savings |
|----------|-------------|-----------------|
| **Table-ify prose** | Paragraphs explaining logic with consistent structure | 70-85% |
| **Bullet points over paragraphs** | Narrative descriptions of features or benefits | 60-75% |
| **Condense file trees** | Full directory listings with every file | 50-67% |
| **Extract-consolidate-reference** | Same information duplicated across files | Variable (eliminates duplication) |
| **Split large monoliths** | Single file >500 lines with distinct sections | Better navigation, not fewer lines |

For before/after examples of each strategy, see reference.md.

---

## Anti-Patterns

| Anti-Pattern | Why It's Bad | Do This Instead |
|---|---|---|
| **Tutorials and walkthroughs** | Agents need reference, not teaching | Checklists with pattern references |
| **Explaining obvious code** | Agents can read code directly | Document the WHY, point to the WHERE |
| **Mixing abstraction levels** | Architecture overview with implementation details | Separate files: OVERVIEW vs detailed docs |
| **Deep directory nesting** | Agents struggle past 3 levels | Max 2-3 levels for doc directories |
| **Duplicating across hierarchy** | Wastes tokens, causes drift when copies diverge | Define once, reference elsewhere |
| **Negative-only constraints** | "Never use X" without alternative confuses agents | Always provide what TO do alongside what not to |
| **`@`-importing everything** | Bloats always-loaded context | Pointer with context on *when* to consult |
| **Documenting for linters** | Formatting rules the agent can't enforce | Use hooks and CI for enforcement |

For detailed examples of each anti-pattern with bad/good comparisons, see reference.md.

---

## Living Documentation

Treat docs like code — they need maintenance:

- **When you repeatedly correct the agent on something**, add it to CLAUDE.md or rules/
- **When the agent follows a rule without being told**, consider removing it (it's wasting tokens)
- **When code changes**, check if docs reference removed features, old paths, or changed behavior
- **Version control everything** — docs should go through the same review process as code
- **Audit regularly** — stale docs actively poison agent reasoning

---

## Validation Checklist

Before committing documentation changes:

- [ ] Every line passes the litmus test (removing it would cause mistakes)
- [ ] No duplication across hierarchy levels
- [ ] No line number references (use function/class names, file paths)
- [ ] Auto-loaded files (CLAUDE.md, rules/) are concise
- [ ] Detailed content lives in on-demand files (docs/)
- [ ] Tables and bullets used over prose where possible
- [ ] Negative constraints include the positive alternative
- [ ] No stale references (removed features, old paths, changed commands)
- [ ] Path-scoped rules used for file-type-specific guidance

---

For templates and detailed examples: see reference.md
