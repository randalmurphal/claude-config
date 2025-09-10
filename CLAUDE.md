# Claude Work Contract

## Available MCP Servers

### Current MCP Servers
1. **Filesystem** - Safe file operations across allowed directories
2. **Playwright** - Browser automation and UI testing  
3. **Postgres** - When configured in project `.mcp.json`

Note: Each project may have its own `.mcp.json` with additional servers.

### Using MCP Servers

To check the status of all MCP servers at any time, use:
```
/mcp
```

To refresh or reconnect servers if needed:
```bash
claude mcp list
```

## Core Principle: Complete Implementation Only
NEVER leave placeholder code, mock data, or partial implementations.
If you cannot fully implement something, STOP and explain why with:
- What's blocking completion
- What information/access you need
- Estimated complexity if you had the requirements

## Quality Gates (Run Before Claiming Completion)
After implementing ANY code changes:
1. Run all existing tests - they must pass
2. Run linters/formatters for the language:
   - JS/TS: `npm run lint` or `eslint` + `prettier`
   - Python: `ruff check` or `pylint` + `black`
   - Go: `go fmt` + `go vet` + `golangci-lint`
3. If any fail, fix them before proceeding
4. If you can't determine the project's lint command, ASK

## Communication Protocol
When you MUST leave something incomplete:
```
⚠️ INCOMPLETE: [Component Name]
Reason: [Why it cannot be completed]
Needs: [What's required to complete]
Impact: [What won't work without this]
```

## Decision Framework
PROCEED without asking when:
- Implementation path is clear
- Tests exist to validate approach
- No destructive operations required
- Within scope of current task

STOP and ask when:
- Multiple valid approaches with significant tradeoffs
- Destructive operations needed (data deletion, force push)
- External service credentials required
- Architectural decisions that affect entire codebase

## Task Completion Checklist
Before considering ANY task complete:
- [ ] All code is fully functional (no TODOs, stubs, or mocks in production code)
- [ ] Existing tests pass
- [ ] Test coverage meets requirements (95% lines, 100% functions)
- [ ] Linting/formatting passes
- [ ] Error handling is SPECIFIC and actionable:
  - Handle expected errors explicitly (FileNotFoundError, ValidationError, etc.)
  - Never use bare except or catch Exception without re-raising
  - Error messages must indicate what went wrong AND what the user can do
  - Let unexpected errors bubble up - crash loud and clear vs silent failure
- [ ] No commented-out code remains
- [ ] Complex code has comments explaining WHY (not what):
  - Non-obvious algorithms explain the approach chosen
  - Workarounds explain what issue they address
  - Performance optimizations explain what was slow
  - Security checks explain what threats they prevent
- [ ] NO magic numbers in code - use named constants:
  - Shared across files: Use constants file (config.py, constants.js, etc.)
  - Shared within class: Use class constants (MAX_RETRIES = 3)
  - Used in one function: Use named variable (max_retry_count = 3)
  - Even "obvious" numbers: Use names (MONTHS_PER_YEAR = 12)
  - Include units in name when relevant (TIMEOUT_SECONDS = 30)

## Integration with Hooks
- PreCompact hook tracks context - focus on the current task
- Failed attempts are preserved - don't explain past failures unless asked
- Working solutions are tracked - build on what works

## Test Standards
1. **Unit Tests**: One test class per function, mock ALL dependencies
2. **Integration Tests**: Use REAL APIs when available (especially Tenable)
3. **Coverage**: 95% line coverage, 100% function coverage required
4. **Structure**: Follow existing patterns in fisio/tests/
5. **Every Case**: Integration tests must cover ALL possible API responses

## Documentation Standards
1. **Two-Document Approach** in project_notes/:
   - README.md: Current technical state only (replace outdated content)
   - REVIEW_NOTES.md: Historical insights (append only)
2. **Location**: Mirror implementation structure (project_notes/imports/tenable_sc/)
3. **Updates**: Use `/update_docs` command to maintain documentation
4. **No Bloat**: README.md stays current, not historical

## Non-Negotiable Standards
1. Security: Never log/commit secrets, always validate input
2. Completeness: Full implementation or clear communication why not
3. Quality: Code must pass all automated checks
4. Testing: Meet coverage requirements with proper test structure
5. Documentation: Keep project_notes current with two-document approach
6. Honesty: If unsure, say so. If it's bad, say why.