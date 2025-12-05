# Generic PR Review Workflow

A risk-scaled, extensible PR review workflow based on the m32rimm PR review pattern.

## Overview

This workflow provides a foundation for automated PR reviews that:

- **Scales to risk**: Low, Medium, High risk levels with different agent sets and validation depth
- **Extensible**: Projects add domain-specific agents and classification rules
- **Multi-phase**: Triage → Investigation → Validation → Synthesis → Report
- **Parallel execution**: Reviewers run in parallel for speed
- **Voting-based validation**: Consensus-based finding validation with council for disputes

## Architecture

### Phases

1. **Triage** (`phase_triage`)
   - Setup worktree
   - Gather diff, requirements, test files
   - Assess blast radius and risk level
   - Determine which agents to run

2. **Investigation** (`phase_investigation`)
   - Run required agents (always)
   - Run conditional agents (based on triggers)
   - Optional second round for Medium+ risk (cross-pollination)
   - Collect findings from all agents

3. **Validation** (`phase_validation`)
   - Run validators on findings
   - Filter false positives
   - Confirm/upgrade/downgrade severity
   - Council vote for disputed findings (High risk)

4. **Synthesis** (`phase_synthesis`)
   - Deduplicate findings
   - Group by severity
   - Classify MR threads (ADDRESSED/DISMISSED/OUTSTANDING)

5. **Report** (`phase_report`)
   - Generate markdown report
   - Cleanup worktree

### Risk Levels

| Risk | Required Agents | Conditional Agents | Validation Depth | Second Round |
|------|-----------------|-------------------|------------------|--------------|
| **LOW** | ✓ | ✗ | Basic (finding-validator) | ✗ |
| **MEDIUM** | ✓ | ✓ | Standard (+ adversarial + severity-auditor) | ✓ |
| **HIGH** | ✓ | ✓ | Thorough (+ reinvestigator + council) | ✓ |

### Generic Agents

| Agent | Type | Model | Trigger |
|-------|------|-------|---------|
| **requirements-reviewer** | Required | Opus | Always |
| **side-effects-reviewer** | Required | Opus | Always |
| **test-coverage-reviewer** | Required | Opus | Always |
| **architecture-reviewer** | Conditional | Opus | 10+ files changed |

## Usage

### Basic Usage

```python
from pathlib import Path
from cc_orchestrations.workflows.pr_review import create_pr_review_workflow

# Create workflow with default generic agents
ctx, handlers = create_pr_review_workflow(
    ticket_id='PROJ-123',
    source_branch='feature/my-feature',
    target_branch='develop',
    work_dir=Path('/path/to/repo'),
)

# Run phases
for phase_name, handler in handlers.items():
    result = handler()
    if not result.success:
        print(f"Phase {phase_name} failed: {result.error}")
        break

print(f"Report: {ctx.work_dir / f'pr_review_{ctx.ticket_id}.md'}")
```

### Extended Usage

```python
from cc_orchestrations.workflows.pr_review import (
    PRReviewAgent,
    create_default_config,
    create_pr_review_workflow,
)

# Create config and add project-specific agents
config = create_default_config()

config.agents.append(
    PRReviewAgent(
        name='security-reviewer',
        trigger=lambda ctx: any('api/' in f for f in ctx.get('diff_files', [])),
        prompt_template="Review API changes for security issues...",
        model='opus',
        required=False,
    )
)

# Use custom config
ctx, handlers = create_pr_review_workflow(
    ticket_id='PROJ-123',
    source_branch='feature/my-feature',
    target_branch='develop',
    work_dir=Path('/path/to/repo'),
    config=config,
)
```

See [EXAMPLE_EXTENSION.md](./EXAMPLE_EXTENSION.md) for more extension patterns.

## Extension Points

### 1. Custom Agents

Add project-specific review agents:

```python
PRReviewAgent(
    name='my-custom-reviewer',
    trigger=lambda ctx: condition_met(ctx),
    prompt_template="Review for X, Y, Z...",
    model='opus',
    required=False,  # Conditional
    description='Check project-specific patterns',
)
```

### 2. Finding Classification

Override classification logic:

```python
class MyProjectClassification(FindingClassification):
    def classify_finding(self, finding):
        # Custom logic here
        return finding

config.finding_classification = MyProjectClassification()
```

### 3. Risk Configuration

Adjust validation depth and thresholds:

```python
config.risk_config[RiskLevel.MEDIUM]['validation_depth'] = 'thorough'
config.risk_config[RiskLevel.HIGH]['second_round'] = True
```

### 4. Extension Hooks

Add custom logic at phase boundaries:

```python
config.extension_hooks = {
    'pre_investigation': my_hook,
    'post_validation': another_hook,
}
```

## Configuration

### PRReviewAgent

```python
@dataclass
class PRReviewAgent:
    name: str                              # Agent identifier
    trigger: Callable[[dict], bool]        # When to run agent
    prompt_template: str                   # Prompt for agent
    model: str = 'opus'                    # Model to use
    required: bool = False                 # Always run or conditional?
    description: str = ''                  # Human-readable description
```

### PRReviewConfig

```python
@dataclass
class PRReviewConfig:
    name: str = 'pr_review'
    version: str = '1.0.0'
    agents: list[PRReviewAgent]            # All agents
    phases: list[PRReviewPhaseConfig]      # Phase definitions
    risk_config: dict[RiskLevel, dict]     # Risk-based settings
    finding_classification: FindingClassification
    voting_threshold: float = 0.67         # Consensus threshold
    max_validation_rounds: int = 3
    report_template: str = 'pr_review_report.md'
    extension_hooks: dict[str, Callable]
```

## Integration

### With Agent Runner

```python
from cc_orchestrations.core.runner import AgentRunner

runner = AgentRunner(...)
ctx, handlers = create_pr_review_workflow(
    ...,
    runner=runner,
)
```

### With Workflow Engine

```python
from cc_orchestrations.workflow import WorkflowEngine

engine = WorkflowEngine(
    config=workflow_config,
    work_dir=work_dir,
    handlers={
        'triage': lambda ctx: phase_triage(pr_ctx),
        'investigation': lambda ctx: phase_investigation(pr_ctx),
        # ...
    },
)

engine.run()
```

## Files

```
pr_review/
├── __init__.py              # Exports
├── config.py                # PRReviewAgent, PRReviewConfig, GENERIC_AGENTS
├── phases.py                # Phase handlers (triage, investigation, validation, synthesis, report)
├── prompts/                 # Prompt templates (if needed)
├── README.md                # This file
└── EXAMPLE_EXTENSION.md     # Extension examples
```

## Design Principles

1. **Generic base, project extensions**: Core agents work everywhere, projects add specifics
2. **Risk-scaled validation**: More validation for higher risk, not one-size-fits-all
3. **Parallel by default**: Reviewers run in parallel unless sequential needed
4. **Voting for disputes**: Multiple validators vote, council for tie-breaks
5. **Extension points**: Projects customize without forking

## Comparison to m32rimm PR Review

| Aspect | m32rimm | Generic |
|--------|---------|---------|
| **Base agents** | 4 required + 7 conditional | 3 required + 1 conditional |
| **Risk levels** | 3 (Low, Medium, High) | Same |
| **Phases** | 6 (includes cross-pollination) | 5 (simplified) |
| **Validation** | finding-validator, adversarial, severity-auditor, reinvestigator, council | Same structure |
| **Extension** | Hardcoded | Extension points |

The generic workflow extracts the pattern from m32rimm and makes it reusable.

## Future Enhancements

- [ ] Prompt template file support (load from `prompts/`)
- [ ] MR thread integration (GitLab API)
- [ ] Test Plan integration (Jira API)
- [ ] Report template customization
- [ ] Metrics collection (findings per agent, false positive rate)
- [ ] Agent performance tracking
