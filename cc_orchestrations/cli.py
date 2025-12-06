"""Unified orchestration CLI.

Provides a single entry point for all workflow types and spec management.
Specs are stored per-project in <git_root>/.claude/specs/<name>-<hash>/.
"""

import argparse
import logging
import sys
from pathlib import Path

from .core import (
    Manifest,
    expand_path,
    get_project_name,
    get_specs_dir,
)
from .core.state import StateManager
from .spec.validator import ManifestValidator

LOG = logging.getLogger(__name__)


def cmd_run(args: argparse.Namespace) -> int:
    """Run a spec.

    Args:
        args: Parsed command-line arguments with 'spec', 'fresh', and 'dry_run' fields.

    Returns:
        0 on success, 1 on failure.
    """
    spec_path = resolve_spec_path(args.spec)

    if not spec_path.exists():
        print(f'Error: Spec not found: {args.spec}')
        print(f'Expected path: {spec_path}')
        return 1

    # Check for manifest.json
    manifest_path = spec_path / 'manifest.json'
    if not manifest_path.exists():
        print(f'Error: No manifest.json found in {spec_path}')
        print('Run the /spec command to generate a manifest first.')
        return 1

    try:
        manifest = Manifest.load(spec_path)
    except (FileNotFoundError, ValueError) as e:
        print(f'Error loading manifest: {e}')
        return 1

    dry_run = getattr(args, 'dry_run', False)

    if dry_run:
        return _run_dry_run(manifest, spec_path)

    # Full execution
    return _run_workflow(manifest, spec_path, fresh=args.fresh)


def _run_dry_run(manifest: Manifest, spec_path: Path) -> int:
    """Execute a dry-run showing execution plan and testing infrastructure.

    Args:
        manifest: Loaded manifest
        spec_path: Path to spec directory

    Returns:
        0 on success, 1 on failure
    """
    print('=' * 60)
    print('DRY RUN - Execution Plan')
    print('=' * 60)
    print()

    # Basic info
    print(f'Spec: {manifest.name}')
    print(f'Project: {manifest.project}')
    print(f'Work dir: {manifest.work_dir}')
    print(f'Spec dir: {spec_path}')
    print()

    # Execution settings
    print('Execution Settings:')
    print(f'  Mode: {manifest.execution.mode}')
    print(f'  Parallel: {manifest.execution.parallel_components}')
    print(f'  Reviewers: {manifest.execution.reviewers}')
    print(f'  Tests required: {manifest.execution.require_tests}')
    print(f'  Complexity: {manifest.complexity}/10')
    print(f'  Risk: {manifest.risk_level}')
    print()

    # Components in dependency order
    print('Components (execution order):')
    try:
        order = manifest.get_dependency_order()
        for i, comp_id in enumerate(order, 1):
            comp = manifest.get_component(comp_id)
            deps = (
                f' (deps: {", ".join(comp.depends_on)})'
                if comp.depends_on
                else ''
            )
            print(f'  {i}. {comp_id}: {comp.file}{deps}')
            if comp.purpose:
                print(f'      Purpose: {comp.purpose}')
    except ValueError as e:
        print(f'  Error: {e}')
        return 1
    print()

    # Gotchas
    if manifest.gotchas:
        print('Gotchas to watch for:')
        for gotcha in manifest.gotchas:
            print(f'  - {gotcha}')
        print()

    # Quality requirements
    print('Quality Requirements:')
    print(f'  Coverage target: {manifest.quality.coverage_target}%')
    print(f'  Lint required: {manifest.quality.lint_required}')
    print(f'  Security scan: {manifest.quality.security_scan}')
    if manifest.validation_command:
        print(f'  Validation: {manifest.validation_command}')
    print()

    # Test runner infrastructure
    print('Testing runner infrastructure...')
    try:
        # Create minimal config for testing
        import os

        from .core.config import Config
        from .core.runner import AgentRunner

        claude_path = os.path.expanduser('~/.claude/local/claude')
        config = Config(
            name='dry-run-test',
            dry_run=True,
            claude_path=claude_path,
        )

        runner = AgentRunner(
            config=config,
            work_dir=manifest.resolve_work_dir(),
            dry_run=True,
        )

        # Test with a simple prompt
        print('  Running test agent (haiku, dry-run mode)...')
        result = runner.run(
            agent_name='test-agent',
            prompt='Return a JSON object with status="ok" and message="dry-run test successful"',
            dry_run=True,
        )

        if result.success:
            print(f'  ✓ Runner test passed ({result.duration:.1f}s)')
            print(f'    Response: {result.data}')
        else:
            print(f'  ✗ Runner test failed: {result.error}')
            return 1

    except Exception as e:
        print(f'  ✗ Runner infrastructure error: {e}')
        return 1

    print()
    print('=' * 60)
    print('DRY RUN COMPLETE - Ready to execute')
    print('=' * 60)
    print()
    print(
        f'To run for real: python -m cc_orchestrations run --spec {manifest.name}'
    )

    return 0


def _run_workflow(
    manifest: Manifest, spec_path: Path, fresh: bool = False
) -> int:
    """Execute the actual workflow.

    Args:
        manifest: Loaded manifest
        spec_path: Path to spec directory
        fresh: Start fresh, ignoring existing state

    Returns:
        0 on success, 1 on failure
    """
    print(f'Spec: {manifest.name}')
    print(f'Project: {manifest.project}')
    print(f'Work dir: {manifest.work_dir}')
    print(f'Components: {len(manifest.components)}')
    print()

    # TODO: Wire up to WorkflowEngine once Config/Manifest alignment is done
    print('Note: Full workflow execution not yet implemented.')
    print('Use --dry-run to test the infrastructure.')
    print()
    print('For now, the workflow can be run via the conduct CLI:')
    print(f'  cd {spec_path}')
    print('  # Run /conduct from Claude Code')

    return 0


def cmd_list(args: argparse.Namespace) -> int:
    """List all specs in the current project.

    Args:
        args: Parsed command-line arguments.

    Returns:
        0 on success, 1 on failure.
    """
    try:
        specs_dir = get_specs_dir()
        project_name = get_project_name()
    except RuntimeError as e:
        print(f'Error: {e}')
        print('Run this command from within a git repository.')
        return 1

    if not specs_dir.exists():
        print(f'No specs directory found for project: {project_name}')
        print(
            'Create a spec with: python -m cc_orchestrations new --name my-feature'
        )
        return 0

    spec_dirs = [d for d in specs_dir.iterdir() if d.is_dir()]

    if not spec_dirs:
        print(f'No specs found in {project_name}')
        print(f'Specs directory: {specs_dir}')
        return 0

    print(f'\nSpecs in {project_name}:\n')

    for spec_dir in sorted(spec_dirs):
        status = get_spec_status(spec_dir)
        print(f'  {spec_dir.name:50} [{status}]')

    print()
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    """Show detailed status of a spec.

    Args:
        args: Parsed command-line arguments with 'spec' field.

    Returns:
        0 on success, 1 on failure.
    """
    spec_path = resolve_spec_path(args.spec)

    if not spec_path.exists():
        print(f'Error: Spec not found: {args.spec}')
        print(f'Expected path: {spec_path}')
        return 1

    # Load manifest
    try:
        manifest = Manifest.load(spec_path)
    except (FileNotFoundError, ValueError) as e:
        print(f'Error loading manifest: {e}')
        return 1

    # Display manifest info
    print(f'Spec: {args.spec}')
    print(f'Name: {manifest.name}')
    print(f'Project: {manifest.project}')
    print(f'Work dir: {manifest.work_dir}')
    print(f'Components: {len(manifest.components)}')
    print(f'Complexity: {manifest.complexity}/10')
    print(f'Risk: {manifest.risk_level}')
    print(f'Mode: {manifest.execution.mode}')
    print(f'Reviewers: {manifest.execution.reviewers}')
    print(f'Tests required: {manifest.execution.require_tests}')

    # Check for execution state
    state_file = spec_path / 'STATE.json'
    if state_file.exists():
        try:
            state_mgr = StateManager(spec_path)
            state = state_mgr.load()

            print('\n--- Execution State ---')
            print(f'Phase: {state.current_phase}')
            print(f'Status: {state.phase_status.value}')

            if state.components:
                completed = sum(
                    1
                    for c in state.components.values()
                    if c.status.value == 'complete'
                )
                total = len(state.components)
                print(f'Progress: {completed}/{total} components complete')

                if state.current_component:
                    print(f'Current: {state.current_component}')

            if state.discoveries:
                print(f'\nDiscoveries: {len(state.discoveries)}')
                for i, discovery in enumerate(state.discoveries[-3:], 1):
                    print(f'  {i}. {discovery[:80]}...')

            if state.error:
                print(f'\nError: {state.error}')

        except Exception as e:
            print(f'\nWarning: Could not load execution state: {e}')
    else:
        print('\n(No execution state - spec has not been run)')

    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    """Validate a spec manifest without executing.

    Args:
        args: Parsed command-line arguments with 'spec' field.

    Returns:
        0 if valid, 1 if invalid or errors found.
    """
    spec_path = resolve_spec_path(args.spec)

    if not spec_path.exists():
        print(f'Error: Spec not found: {args.spec}')
        print(f'Expected path: {spec_path}')
        return 1

    # Load manifest
    try:
        manifest = Manifest.load(spec_path)
    except (FileNotFoundError, ValueError) as e:
        print(f'Error loading manifest: {e}')
        return 1

    # Validate
    validator = ManifestValidator()
    result = validator.validate(manifest)

    if result.valid:
        print('✓ Manifest is valid')

        if result.warnings:
            print(f'\nWarnings ({len(result.warnings)}):')
            for warning in result.warnings:
                print(f'  {warning.field}: {warning.error}')
                if warning.suggestion:
                    print(f'    → {warning.suggestion}')

        return 0
    print(f'✗ Validation failed ({len(result.errors)} errors)\n')

    for error in result.errors:
        print(f'  {error.field}:')
        print(f'    Error: {error.error}')
        if error.suggestion:
            print(f'    Fix: {error.suggestion}')
        print()

    return 1


def cmd_pr_review(args: argparse.Namespace) -> int:
    """Run a PR review workflow.

    Args:
        args: Parsed arguments with ticket, target_branch, dry_run, branch

    Returns:
        0 on success, 1 on failure
    """
    import subprocess

    from .core.worktree import WORKTREES_BASE, WorktreeManager
    from .workflows.pr_review.config import (
        create_default_config,
    )
    from .workflows.pr_review.phases import (
        PRReviewContext,
        phase_investigation,
        phase_report,
        phase_synthesis,
        phase_triage,
        phase_validation,
    )

    ticket = args.ticket
    target_branch = args.target_branch or 'develop'
    dry_run = getattr(args, 'dry_run', False)
    source_branch = getattr(args, 'branch', None)

    print('=' * 60)
    print(f'PR REVIEW: {ticket}')
    print('=' * 60)
    print()

    # Find git root
    try:
        from .core.paths import get_git_root, get_project_name

        repo_root = get_git_root()
        project_name = get_project_name()
    except RuntimeError as e:
        print(f'Error: {e}')
        return 1

    print(f'Project: {project_name}')
    print(f'Repository: {repo_root}')
    print(f'Target branch: {target_branch}')

    # Check for project-specific PR review config
    project_agents = []
    project_config_path = (
        repo_root / '.claude' / 'cc_orchestrations' / 'pr_review' / 'config.py'
    )
    if project_config_path.exists():
        print(f'Loading project extensions from: {project_config_path.parent}')
        try:
            import importlib.util

            spec = importlib.util.spec_from_file_location(
                'project_pr_review_config',
                project_config_path,
            )
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                # Look for project-specific agents - prefer M32RIMM_AGENTS, etc.
                for pattern in ['M32RIMM_AGENTS', 'PROJECT_AGENTS']:
                    if hasattr(module, pattern):
                        project_agents = getattr(module, pattern)
                        print(
                            f'  Loaded {len(project_agents)} project-specific agents from {pattern}'
                        )
                        break
                # Fallback: look for any list ending with _AGENTS (not GENERIC)
                if not project_agents:
                    for attr in dir(module):
                        if (
                            attr.endswith('_AGENTS')
                            and attr != 'GENERIC_AGENTS'
                            and isinstance(getattr(module, attr), list)
                        ):
                            project_agents = getattr(module, attr)
                            print(
                                f'  Loaded {len(project_agents)} project-specific agents from {attr}'
                            )
                            break
        except Exception as e:
            print(f'  Warning: Could not load project config: {e}')

    # Find source branch if not specified
    if not source_branch:
        print(f'Finding branch for ticket: {ticket}')
        result = subprocess.run(
            ['git', 'fetch', 'origin', '--prune'],
            cwd=repo_root,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            print(f'Warning: git fetch failed: {result.stderr}')

        # Find branch matching ticket
        result = subprocess.run(
            ['git', 'branch', '-r'],
            cwd=repo_root,
            capture_output=True,
            text=True,
        )
        branches = result.stdout.strip().split('\n')
        matching = [
            b.strip().replace('origin/', '')
            for b in branches
            if ticket.lower() in b.lower() and 'pre-styling' not in b.lower()
        ]

        if not matching:
            print(f'Error: No branch found for ticket {ticket}')
            print('Use --branch to specify the source branch')
            return 1

        source_branch = matching[0]
        if len(matching) > 1:
            print(f'Multiple branches found: {matching}')
            print(f'Using: {source_branch}')

    print(f'Source branch: {source_branch}')
    print()

    if dry_run:
        print('[DRY RUN MODE]')
        print()

    # Step 1: Set up worktrees
    print('Setting up worktrees...')
    manager = WorktreeManager(repo_root)
    tool_dir = WORKTREES_BASE / project_name / 'pr-review'

    # Use branch name for PR-specific worktree (cleaned up after)
    # Base worktree is shared and reused across reviews
    pr_worktree_name = source_branch.replace(
        '/', '-'
    )  # Sanitize for directory name

    try:
        # Create base worktree (target branch) - shared, reused
        base_wt = manager.create_worktree(
            name='base',
            base_dir=tool_dir,
            checkout_branch=f'origin/{target_branch}',
        )
        print(f'  Base worktree: {base_wt}')

        # Create PR worktree (source branch) - branch-specific
        pr_wt = manager.create_worktree(
            name=pr_worktree_name,
            base_dir=tool_dir,
            checkout_branch=f'origin/{source_branch}',
        )
        print(f'  PR worktree: {pr_wt}')
        print()

        # Get diff files
        result = subprocess.run(
            ['git', 'diff', '--name-only', f'{target_branch}...HEAD'],
            cwd=pr_wt,
            capture_output=True,
            text=True,
        )
        diff_files = [f for f in result.stdout.strip().split('\n') if f]
        print(f'Changed files: {len(diff_files)}')
        for f in diff_files[:10]:
            print(f'  - {f}')
        if len(diff_files) > 10:
            print(f'  ... and {len(diff_files) - 10} more')
        print()

        # Get Jira context if script exists (check subdirectory first, then root)
        jira_script = (
            repo_root / '.claude' / 'scripts' / 'jira' / 'jira-get-issue'
        )
        if not jira_script.exists():
            jira_script = repo_root / '.claude' / 'scripts' / 'jira-get-issue'
        jira_context = None
        if jira_script.exists():
            print(f'Fetching Jira ticket: {ticket}')
            result = subprocess.run(
                [str(jira_script), ticket],
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                jira_context = result.stdout
                # Extract summary line
                for line in jira_context.split('\n'):
                    if line.startswith('# '):
                        print(f'  {line}')
                        break
            else:
                print(f'  Warning: Could not fetch Jira: {result.stderr[:100]}')
            print()

        # Get GitLab MR context if script exists (check subdirectory first, then root)
        gitlab_script = (
            repo_root / '.claude' / 'scripts' / 'gitlab' / 'gitlab-get-mr'
        )
        if not gitlab_script.exists():
            gitlab_script = repo_root / '.claude' / 'scripts' / 'gitlab-get-mr'
        mr_context = None
        if gitlab_script.exists():
            print(f'Fetching GitLab MR for: {ticket}')
            result = subprocess.run(
                [str(gitlab_script), ticket],
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                mr_context = result.stdout
                # Extract MR title for display
                for line in mr_context.split('\n'):
                    if line.startswith('# MR'):
                        print(f'  {line}')
                        break
                else:
                    print('  MR found')
            else:
                # Show the actual error
                error_msg = (
                    result.stderr.strip() if result.stderr else 'Unknown error'
                )
                print(f'  No MR found: {error_msg}')
            print()

        if dry_run:
            print('=' * 60)
            print('DRY RUN COMPLETE')
            print('=' * 60)
            print()
            print('Would run phases:')
            print('  1. Triage - Assess risk level')
            print('  2. Investigation - Run reviewers')
            print(
                '  3. Cross-Pollination - Second-round analysis (medium+ risk)'
            )
            print('  4. Validation - Validate findings, council votes')
            print('  5. Synthesis - Consolidate results')
            print('  6. Report - Generate report')
            print()
            print('To run for real:')
            print(f'  python -m cc_orchestrations pr-review {ticket}')
            return 0

        # Create review context
        import os

        claude_path = os.path.expanduser('~/.claude/local/claude')

        from .core.config import Config
        from .core.runner import AgentRunner

        config = Config(
            name='pr-review',
            dry_run=False,
            claude_path=claude_path,
            default_model='opus',  # PR review uses Opus for thoroughness
        )

        # Skills directory - check project first, then ~/.claude
        project_skills_dir = repo_root / '.claude' / 'skills'
        global_skills_dir = Path.home() / '.claude' / 'skills'
        skills_dir = (
            project_skills_dir
            if project_skills_dir.exists()
            else global_skills_dir
        )

        # Finding classification path (if exists)
        finding_classification = (
            repo_root
            / '.claude'
            / 'cc_orchestrations'
            / 'pr_review'
            / 'finding_classification.md'
        )

        runner = AgentRunner(
            config=config,
            work_dir=pr_wt,
            skills_dir=skills_dir if skills_dir.exists() else None,
            finding_classification_path=(
                finding_classification
                if finding_classification.exists()
                else None
            ),
            dry_run=False,
        )

        # Create config with project-specific agents if available
        review_config = create_default_config()
        if project_agents:
            # Merge project agents with generic agents
            review_config.agents.extend(project_agents)
            print(f'  Using {len(review_config.agents)} total agents')

        ctx = PRReviewContext(
            ticket_id=ticket,
            source_branch=source_branch,
            target_branch=target_branch,
            work_dir=repo_root,
            worktree_path=pr_wt,
            diff_files=diff_files,
            config=review_config,
            runner=runner,
        )

        # Add Jira context
        if jira_context:
            ctx.jira_context = jira_context

        # Phase 1: Triage
        print('Phase 1: Triage')
        result = phase_triage(ctx)
        if not result.success:
            print(f'  Triage failed: {result.error}')
            return 1
        print(f'  Risk level: {ctx.risk_level.value}')
        print()

        # Phase 2: Investigation
        print('Phase 2: Investigation')
        result = phase_investigation(ctx)
        if not result.success:
            print(f'  Investigation failed: {result.error}')
            return 1
        print(f'  Findings: {len(ctx.findings)}')
        print()

        # Phase 3: Validation
        print('Phase 3: Validation')
        result = phase_validation(ctx)
        if not result.success:
            print(f'  Validation failed: {result.error}')
            return 1
        print(f'  Validated findings: {len(ctx.validated_findings)}')
        print()

        # Phase 4: Synthesis
        print('Phase 4: Synthesis')
        result = phase_synthesis(ctx)
        if not result.success:
            print(f'  Synthesis failed: {result.error}')
            return 1
        print()

        # Phase 5: Report
        print('Phase 5: Report')
        result = phase_report(ctx)
        if not result.success:
            print(f'  Report failed: {result.error}')
            return 1
        print(f'  Report: {result.data.get("report_path", "N/A")}')
        print()

        print('=' * 60)
        print('PR REVIEW COMPLETE')
        print('=' * 60)
        return 0

    finally:
        # Cleanup only the branch-specific worktree (keep base for reuse)
        print()
        print('Cleaning up worktrees...')
        manager.cleanup_worktree(project_name, 'pr-review', pr_worktree_name)
        print('Done.')


def cmd_new(args: argparse.Namespace) -> int:
    """Create a new spec directory structure.

    Args:
        args: Parsed command-line arguments with 'name' field.

    Returns:
        0 on success, 1 on failure.
    """
    import secrets

    try:
        specs_dir = get_specs_dir()
        project_name = get_project_name()
    except RuntimeError as e:
        print(f'Error: {e}')
        print('Run this command from within a git repository.')
        return 1

    # Generate unique hash suffix
    hash_suffix = secrets.token_hex(4)
    spec_name = f'{args.name}-{hash_suffix}'
    spec_path = specs_dir / spec_name

    # Create directory structure
    try:
        spec_path.mkdir(parents=True, exist_ok=False)
        (spec_path / 'brainstorm').mkdir()
        (spec_path / 'components').mkdir()

        # Create placeholder files
        (spec_path / 'SPEC.md').write_text(
            f"""# {args.name}

## Context

[Describe the problem or feature this spec addresses]

## Approach

[Outline the solution approach]

## Components

[List components to create/modify]

## Success Criteria

[Define what success looks like]
"""
        )

        (spec_path / 'brainstorm' / 'README.md').write_text(
            """# Brainstorm

This directory contains working documents and notes from the /spec investigation phase.

These files are used to generate the formal manifest.json.
"""
        )

        print(f'✓ Created spec: {spec_name}')
        print(f'  Project: {project_name}')
        print(f'  Path: {spec_path}')
        print()
        print('Next steps:')
        print('  1. Edit SPEC.md with your requirements')
        print('  2. Run /spec to formalize into manifest.json')
        print(f'  3. Run: python -m cc_orchestrations run --spec {spec_name}')

        return 0

    except FileExistsError:
        print(f'Error: Spec directory already exists: {spec_path}')
        return 1
    except OSError as e:
        print(f'Error creating spec directory: {e}')
        return 1


def resolve_spec_path(spec_ref: str) -> Path:
    """Resolve a spec reference to an absolute path.

    Accepts either:
    - Spec name: "my-feature-abc123" (looks in current project)
    - Absolute path: "/home/user/project/.claude/specs/..."
    - Home-relative path: "~/.claude/specs/..."

    Args:
        spec_ref: Spec reference string.

    Returns:
        Absolute Path to the spec directory.
    """
    # If it starts with / or ~, treat as a path
    if spec_ref.startswith(('/', '~')):
        return expand_path(spec_ref)

    # Otherwise, look in current project's specs dir
    return get_specs_dir() / spec_ref


def get_spec_status(spec_dir: Path) -> str:
    """Get the status of a spec.

    Args:
        spec_dir: Path to the spec directory.

    Returns:
        Status string: "not_started", "in_progress", "complete", "error", or "no_manifest".
    """
    # Check for manifest
    manifest_path = spec_dir / 'manifest.json'
    if not manifest_path.exists():
        return 'no_manifest'

    # Check for state
    state_file = spec_dir / 'STATE.json'
    if not state_file.exists():
        return 'not_started'

    # Load state and check status
    try:
        state_mgr = StateManager(spec_dir)
        state = state_mgr.load()

        if state.error:
            return 'error'

        if state.completed_at:
            return 'complete'

        if state.current_phase != 'init':
            return 'in_progress'

        return 'not_started'

    except Exception:
        return 'error'


def main() -> int:
    """Main CLI entry point.

    Returns:
        Exit code: 0 on success, 1 on failure.
    """
    parser = argparse.ArgumentParser(
        description='Unified orchestration CLI',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # List specs in current project
  python -m cc_orchestrations list

  # Create new spec
  python -m cc_orchestrations new --name feature-name

  # Show spec status
  python -m cc_orchestrations status --spec my-feature-abc123

  # Validate a manifest
  python -m cc_orchestrations validate --spec my-feature-abc123

  # Run a spec
  python -m cc_orchestrations run --spec my-feature-abc123

  # Run PR review
  python -m cc_orchestrations pr-review INT-1234
  python -m cc_orchestrations pr-review INT-1234 --target main
  python -m cc_orchestrations pr-review INT-1234 --dry-run
""",
    )

    subparsers = parser.add_subparsers(dest='command', help='Command to run')

    # run command
    run_parser = subparsers.add_parser(
        'run', help='Run a spec', description='Execute a spec workflow'
    )
    run_parser.add_argument(
        '--spec',
        required=True,
        help='Spec name or absolute path',
    )
    run_parser.add_argument(
        '--fresh',
        action='store_true',
        help='Start fresh (ignore existing state)',
    )
    run_parser.add_argument(
        '--dry-run',
        action='store_true',
        dest='dry_run',
        help='Show execution plan and test infrastructure without running',
    )

    # list command
    subparsers.add_parser(
        'list',
        help='List specs',
        description='List all specs in current project',
    )

    # status command
    status_parser = subparsers.add_parser(
        'status',
        help='Show spec status',
        description='Display detailed status of a spec',
    )
    status_parser.add_argument(
        '--spec',
        required=True,
        help='Spec name or absolute path',
    )

    # validate command
    validate_parser = subparsers.add_parser(
        'validate',
        help='Validate spec',
        description='Validate a spec manifest without executing',
    )
    validate_parser.add_argument(
        '--spec',
        required=True,
        help='Spec name or absolute path',
    )

    # new command
    new_parser = subparsers.add_parser(
        'new',
        help='Create new spec',
        description='Create a new spec directory structure',
    )
    new_parser.add_argument(
        '--name',
        required=True,
        help='Spec name (hash will be appended)',
    )

    # pr-review command
    pr_review_parser = subparsers.add_parser(
        'pr-review',
        help='Run PR review workflow',
        description='Run a comprehensive PR review against a Jira ticket',
    )
    pr_review_parser.add_argument(
        'ticket',
        help='Jira ticket ID (e.g., INT-1234)',
    )
    pr_review_parser.add_argument(
        '--target',
        dest='target_branch',
        default='develop',
        help='Target branch (default: develop)',
    )
    pr_review_parser.add_argument(
        '--branch',
        help='Source branch (auto-detected from ticket if not specified)',
    )
    pr_review_parser.add_argument(
        '--dry-run',
        action='store_true',
        dest='dry_run',
        help='Show what would be done without running reviewers',
    )

    # Parse arguments
    args = parser.parse_args()

    # Dispatch to command handler
    commands = {
        'run': cmd_run,
        'list': cmd_list,
        'status': cmd_status,
        'validate': cmd_validate,
        'new': cmd_new,
        'pr-review': cmd_pr_review,
    }

    if args.command in commands:
        return commands[args.command](args)

    # No command specified
    parser.print_help()
    return 1


if __name__ == '__main__':
    sys.exit(main())
