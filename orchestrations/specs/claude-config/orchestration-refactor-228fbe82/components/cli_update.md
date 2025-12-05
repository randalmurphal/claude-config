# Component: Unified CLI

## Purpose
A unified CLI that can run any workflow type and manage specs. Replaces the conduct-specific CLI.

## Location
`~/.claude/orchestrations/cli.py`

## Commands

```bash
# Run a spec
python -m orchestrations run --spec <project>/<name>
python -m orchestrations run --spec claude-config/orchestration-refactor-228fbe82

# List specs
python -m orchestrations list
python -m orchestrations list --project claude-config

# Show spec status
python -m orchestrations status --spec <project>/<name>

# Resume interrupted execution
python -m orchestrations resume --spec <project>/<name>

# Validate a spec (without executing)
python -m orchestrations validate --spec <project>/<name>

# Create new spec directory
python -m orchestrations new --project <project> --name <name>

# Legacy: run conduct directly
python -m orchestrations conduct [args]  # Forwards to workflows/conduct
```

## Implementation

```python
"""Unified orchestration CLI."""

import argparse
import logging
import sys
from pathlib import Path

from .core import get_specs_dir, expand_path, Manifest
from .spec import ManifestValidator, SpecFormalizer
from .workflows.conduct import create_conduct_workflow

LOG = logging.getLogger(__name__)


def cmd_run(args: argparse.Namespace) -> int:
    """Run a spec."""
    spec_path = resolve_spec_path(args.spec)

    if not spec_path.exists():
        print(f"Spec not found: {args.spec}")
        return 1

    manifest = Manifest.load(spec_path)

    # Determine workflow type (for now, always conduct)
    workflow = create_conduct_workflow(
        work_dir=expand_path(manifest.work_dir),
        spec_path=spec_path / "SPEC.md",
    )

    success = workflow.run(resume=not args.fresh)
    return 0 if success else 1


def cmd_list(args: argparse.Namespace) -> int:
    """List specs."""
    specs_dir = get_specs_dir()

    if args.project:
        projects = [args.project]
    else:
        projects = [d.name for d in specs_dir.iterdir() if d.is_dir()]

    for project in sorted(projects):
        project_dir = specs_dir / project
        if not project_dir.exists():
            continue

        specs = [d.name for d in project_dir.iterdir() if d.is_dir()]
        if specs:
            print(f"\n{project}/")
            for spec in sorted(specs):
                status = get_spec_status(project_dir / spec)
                print(f"  {spec} [{status}]")

    return 0


def cmd_status(args: argparse.Namespace) -> int:
    """Show spec status."""
    spec_path = resolve_spec_path(args.spec)

    if not spec_path.exists():
        print(f"Spec not found: {args.spec}")
        return 1

    manifest = Manifest.load(spec_path)
    state_file = spec_path / "state.json"

    print(f"Spec: {args.spec}")
    print(f"Work dir: {manifest.work_dir}")
    print(f"Components: {len(manifest.components)}")
    print(f"Complexity: {manifest.complexity}/10")
    print(f"Risk: {manifest.risk_level}")

    if state_file.exists():
        # Show execution state
        state = load_state(state_file)
        print(f"\nExecution Status: {state.phase_status}")
        print(f"Current Phase: {state.current_phase}")

        completed = sum(1 for c in state.components.values()
                       if c.status == "complete")
        print(f"Components: {completed}/{len(manifest.components)} complete")

    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    """Validate a spec without executing."""
    spec_path = resolve_spec_path(args.spec)

    if not spec_path.exists():
        print(f"Spec not found: {args.spec}")
        return 1

    manifest = Manifest.load(spec_path)
    validator = ManifestValidator()
    result = validator.validate(manifest)

    if result.valid:
        print("Spec is valid")
        if result.warnings:
            print("\nWarnings:")
            for w in result.warnings:
                print(f"  - {w.field}: {w.error}")
        return 0
    else:
        print("Validation failed:\n")
        for e in result.errors:
            print(f"  {e.field}: {e.error}")
            if e.suggestion:
                print(f"    Suggestion: {e.suggestion}")
        return 1


def cmd_new(args: argparse.Namespace) -> int:
    """Create new spec directory."""
    import secrets

    hash_suffix = secrets.token_hex(4)
    spec_name = f"{args.name}-{hash_suffix}"
    spec_path = get_specs_dir() / args.project / spec_name

    spec_path.mkdir(parents=True)
    (spec_path / "brainstorm").mkdir()
    (spec_path / "components").mkdir()

    print(f"Created: {args.project}/{spec_name}")
    print(f"Path: {spec_path}")

    return 0


def resolve_spec_path(spec_ref: str) -> Path:
    """Resolve spec reference to path."""
    # Accept: project/name or full path
    if "/" in spec_ref and not spec_ref.startswith("/"):
        return get_specs_dir() / spec_ref
    return expand_path(spec_ref)


def main() -> int:
    parser = argparse.ArgumentParser(description="Orchestration CLI")
    subparsers = parser.add_subparsers(dest="command")

    # run
    run_parser = subparsers.add_parser("run", help="Run a spec")
    run_parser.add_argument("--spec", required=True, help="Spec path (project/name)")
    run_parser.add_argument("--fresh", action="store_true", help="Start fresh")

    # list
    list_parser = subparsers.add_parser("list", help="List specs")
    list_parser.add_argument("--project", help="Filter by project")

    # status
    status_parser = subparsers.add_parser("status", help="Show spec status")
    status_parser.add_argument("--spec", required=True)

    # validate
    validate_parser = subparsers.add_parser("validate", help="Validate spec")
    validate_parser.add_argument("--spec", required=True)

    # new
    new_parser = subparsers.add_parser("new", help="Create new spec")
    new_parser.add_argument("--project", required=True)
    new_parser.add_argument("--name", required=True)

    args = parser.parse_args()

    commands = {
        "run": cmd_run,
        "list": cmd_list,
        "status": cmd_status,
        "validate": cmd_validate,
        "new": cmd_new,
    }

    if args.command in commands:
        return commands[args.command](args)

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
```
