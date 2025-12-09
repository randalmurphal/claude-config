# cc_orchestrations_m32rimm

m32rimm-specific extension for cc_orchestrations PR review and orchestration.

## Installation

```bash
pip install -e ~/repos/ai-devtools/cc_orchestrations/extensions/m32rimm
```

## What This Provides

**20 PR review agent prompts** - All self-contained, no external dependencies:
- Domain reviewers: mongo-ops, api-security, bo-structure, import-framework, schema-alignment, test-plan-validator
- Generic reviewers with m32rimm patterns: requirements, side-effects, test-coverage, architecture, performance
- Validation: finding-validator, adversarial-reviewer, severity-auditor, critical-reinvestigator, council-reviewer
- Second round: blind-spot-hunter, interaction-investigator, conclusion-validator
- Report: pr-report-synthesizer

**m32rimm-specific patterns** injected into prompts:
- `retry_run()` for MongoDB writes
- `DBOpsHelper.flush()` before aggregation
- `info.owner.subID` filtering on businessObjects
- `data.toolIDs` list structure: `[{toolName, id, url}]`
- Selectizer lookup order (sub_id first, then global)
- Activity auto-routing to activities collection

## Auto-Detection

Extension activates when working directory contains:
- `fisio/` directory
- `fortress_api/` directory
- Path contains "rimm"

## Usage

```bash
# Extension auto-loads when running from m32rimm project
cd ~/repos/m32rimm
cco pr-review INT-1234
```

Prompts load from extension first, fallback to base prompts if not found.
