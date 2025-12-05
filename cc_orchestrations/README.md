# cc_orchestrations

Claude Code orchestration system for multi-component workflows with external enforcement.

## Installation

```bash
pip install -e ~/.claude/cc_orchestrations
```

## Usage

```bash
# List specs
python -m cc_orchestrations list

# Create new spec
python -m cc_orchestrations new --project myproject --name myfeature

# Run spec
python -m cc_orchestrations run --spec myproject/myfeature-abc123

# Validate spec
python -m cc_orchestrations validate --spec myproject/myfeature-abc123
```

## Architecture

```
cc_orchestrations/
├── core/           # Generic infrastructure (config, state, runner, context)
├── workflow/       # Workflow primitives (engine, gates, loops)
├── spec/           # Spec creation (validator, formalizer)
├── workflows/      # Workflow implementations
│   ├── conduct/    # Full orchestration workflow
│   └── pr_review/  # PR review workflow
└── specs/          # Spec storage by project
```

## Extending

Projects can extend the generic workflows by adding project-specific agents, prompts, and patterns. See the workflow README files for extension documentation.
