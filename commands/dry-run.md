---
name: dry-run
description: Test orchestration system on DataFlow project (must be in orchestration_mcp/dry_run directory)
---

# /dry-run - Orchestration System Testing

**Purpose:** Run comprehensive test of orchestration system on multi-language DataFlow project.

## What It Does

1. **Verify Location** - Must be in `orchestration_mcp/dry_run` directory
2. **Check Infrastructure** - Ensure mock API is running
3. **Run Orchestration** - Execute `/conduct` on test_project with full MCP workflow
4. **Evaluate Results** - Check production readiness (tests, linting, coverage, security)
5. **Generate Report** - Detailed scorecard with pass/fail and recommendations

## Prerequisites

```bash
# From orchestration_mcp/dry_run directory:
cd infrastructure
./setup.sh     # Start mock API

# Verify
./verify.sh    # Should show "All infrastructure checks passed"
```

## Execution

Must be in `orchestration_mcp/dry_run` directory:

```bash
cd /path/to/orchestration_mcp/dry_run
# Then in Claude Code:
/dry-run
```

## What Gets Built

Orchestration will build:
- **Python Backend** - FastAPI + JWT auth + gRPC client + background workers
- **Go gRPC Service** - Event processor + SQLite database layer
- **React Frontend** - Dashboard with real-time updates
- **Proto Definitions** - gRPC contracts
- **Docker Setup** - Full docker-compose orchestration
- **Tests** - Unit + integration tests for all services

## Evaluation Criteria

**Building & Starting** (20 points)
- Docker compose builds without errors
- All services start and become healthy

**Testing** (25 points)
- Python tests pass (pytest)
- Go tests pass (go test ./...)
- Frontend tests pass (npm test)
- Integration test passes

**Coverage** (15 points)
- Python coverage > 90%
- Go coverage > 90%
- Frontend coverage > 90%

**Code Quality** (20 points)
- Linting passes (ruff, golangci-lint, eslint)
- No TODO/NotImplementedError
- Proper error handling at boundaries
- Structured logging

**Security** (10 points)
- JWT authentication implemented
- Rate limiting configured
- Input validation present
- SQL injection protection (parameterized queries)

**Architecture** (10 points)
- Files match READY.md spec
- gRPC contracts valid
- Data flow works (Mock API → SQLite → UI)
- Frontend updates reflect backend changes

**Total: 100 points**

Pass threshold: 85/100

## Output

Results saved to `results/run_XXX/`:
```
results/run_001/
  evaluation.json       # Structured scores
  report.md             # Human-readable report
  output.log            # Full orchestration log
  test_project/         # Snapshot of built code
```

## Example Report

```
================== DRY-RUN EVALUATION ==================
Run ID: run_001
Date: 2025-09-30 10:30:00

SCORE: 92/100 (PASS)

Building & Starting: 20/20 ✅
  ✅ Docker compose builds
  ✅ All services healthy

Testing: 23/25 ✅
  ✅ Python tests pass
  ✅ Go tests pass
  ❌ Frontend tests: 2 failures

Coverage: 14/15 ✅
  ✅ Python: 94%
  ✅ Go: 91%
  ⚠️  Frontend: 88% (need 90%)

Code Quality: 18/20 ✅
  ✅ Linting passes
  ✅ No TODOs
  ⚠️  Missing error handling in 2 endpoints

Security: 10/10 ✅
  ✅ JWT authentication
  ✅ Rate limiting
  ✅ Input validation
  ✅ SQL injection protection

Architecture: 10/10 ✅
  ✅ All files present
  ✅ gRPC contracts valid
  ✅ Data flow works

RECOMMENDATIONS:
1. Fix 2 failing frontend tests in Controls.test.jsx
2. Add tests to increase frontend coverage to 90%
3. Add error handling for /api/events endpoint (404 case)
4. Add error handling for /api/metrics endpoint (DB error case)

NEXT STEPS:
Review failures, fix issues in agent prompts or READY.md,
then run /dry-run again to validate improvements.
========================================================
```

## Iteration Loop

1. Run `/dry-run`
2. Review report in `results/run_XXX/report.md`
3. Analyze failures - which agent? which phase? why?
4. Fix root cause (agent prompt, READY.md clarification, tool description)
5. Run `/dry-run` again
6. Repeat until 100/100

## Troubleshooting

**"Infrastructure not running"**
```bash
cd infrastructure
./setup.sh
./verify.sh
```

**"Must be in dry_run directory"**
```bash
cd /path/to/orchestration_mcp/dry_run
# Then run /dry-run again
```

**"Orchestration MCP not configured"**
Check `~/.config/claude-code/mcp.json` has orchestration-mcp configured.

**View detailed logs**
```bash
cat results/run_XXX/output.log
```