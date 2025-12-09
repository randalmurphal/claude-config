#!/usr/bin/env python3
"""Test runner for cc_orchestrations.

Usage:
    python run_tests.py              # Run all unit tests (fast, safe)
    python run_tests.py --all        # Run all tests including integration/e2e
    python run_tests.py --integration # Run integration tests (dry-run API calls)
    python run_tests.py --e2e        # Run E2E tests (full workflows)
    python run_tests.py --coverage   # Run with coverage report

Test Tiers:
    Unit (default):
        - No external dependencies
        - No API calls
        - Fast execution (~1-5 seconds)

    Integration:
        - Uses dry-run mode with haiku model
        - Makes actual API calls (cheap)
        - Tests component interaction
        - ~10-30 seconds

    E2E:
        - Full workflow execution
        - Dry-run mode to avoid real changes
        - Most comprehensive
        - ~1-5 minutes
"""

import argparse
import subprocess
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(
        description='Run cc_orchestrations tests',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    parser.add_argument(
        '--all',
        action='store_true',
        help='Run all tests (unit + integration + e2e)',
    )
    parser.add_argument(
        '--unit',
        action='store_true',
        help='Run unit tests only (default)',
    )
    parser.add_argument(
        '--integration',
        action='store_true',
        help='Run integration tests (dry-run API calls)',
    )
    parser.add_argument(
        '--e2e',
        action='store_true',
        help='Run E2E tests (full workflows)',
    )
    parser.add_argument(
        '--coverage',
        action='store_true',
        help='Run with coverage report',
    )
    parser.add_argument(
        '-v',
        '--verbose',
        action='store_true',
        help='Verbose output',
    )
    parser.add_argument(
        '-x',
        '--exitfirst',
        action='store_true',
        help='Exit on first failure',
    )
    parser.add_argument(
        '-k',
        metavar='EXPRESSION',
        help='Only run tests matching expression',
    )

    args = parser.parse_args()

    # Build pytest command
    cmd = ['python', '-m', 'pytest']

    # Determine which tests to run
    markers = []
    if args.all:
        pass  # No marker filter - run everything
    elif args.integration:
        markers.append('integration')
    elif args.e2e:
        markers.append('e2e')
    elif args.unit or (not args.integration and not args.e2e):
        markers.append('unit')

    if markers:
        cmd.extend(['-m', ' or '.join(markers)])

    # Add options
    if args.verbose:
        cmd.append('-v')
    else:
        cmd.append('-v')  # Always verbose for test names

    if args.exitfirst:
        cmd.append('-x')

    if args.k:
        cmd.extend(['-k', args.k])

    if args.coverage:
        cmd.extend(
            [
                '--cov=src/cc_orchestrations',
                '--cov-report=term-missing',
                '--cov-report=html:coverage_html',
            ]
        )

    # Show what we're running
    print('=' * 60)
    print('cc_orchestrations Test Runner')
    print('=' * 60)
    print()

    tier = (
        'all'
        if args.all
        else (
            'integration'
            if args.integration
            else ('e2e' if args.e2e else 'unit')
        )
    )
    print(f'Test tier: {tier}')
    print(f'Command: {" ".join(cmd)}')
    print()

    # Run tests
    result = subprocess.run(cmd, cwd=Path(__file__).parent)

    if result.returncode == 0:
        print()
        print('=' * 60)
        print('✓ All tests passed!')
        print('=' * 60)
    else:
        print()
        print('=' * 60)
        print('✗ Some tests failed')
        print('=' * 60)

    return result.returncode


if __name__ == '__main__':
    sys.exit(main())
