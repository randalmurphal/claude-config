#!/usr/bin/env python3
"""
Sprint Review Command
====================
Command: /sprint-review [days=14]

Reviews patterns from the current sprint and allows team validation.
Automatically detects the main branch from git configuration.
"""

import json
import sys
import time
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta

# Import universal learner
sys.path.insert(0, str(Path(__file__).parent))
from universal_learner import get_learner


class SprintReviewer:
    """Review and validate patterns from sprint."""

    def __init__(self):
        self.learner = get_learner()
        self.main_branch = self.detect_main_branch()

    def detect_main_branch(self) -> str:
        """Detect the main branch from git configuration."""
        # Try multiple methods to detect main branch
        methods = [
            # Method 1: Check git config for default branch
            ["git", "config", "--get", "init.defaultBranch"],
            # Method 2: Check remote HEAD
            ["git", "symbolic-ref", "refs/remotes/origin/HEAD"],
            # Method 3: List branches and look for common names
            ["git", "branch", "-r"]
        ]

        for cmd in methods[:2]:
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
                if result.returncode == 0 and result.stdout.strip():
                    # Extract branch name
                    branch = result.stdout.strip()
                    if "origin/" in branch:
                        branch = branch.split("origin/")[-1]
                    if branch:
                        return branch
            except:
                continue

        # Method 3: Look for common main branch names
        try:
            result = subprocess.run(methods[2], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                branches = result.stdout.lower()
                for common_name in ['main', 'master', 'develop', 'development', 'trunk']:
                    if f"origin/{common_name}" in branches:
                        return common_name
        except:
            pass

        # Default fallback
        return "main"

    def get_git_survival_rate(self, pattern: Dict, days: int = 14) -> float:
        """Check if pattern's code survived in git history."""
        try:
            # Get files from pattern
            files = pattern.get('files', [])
            if not files:
                file = pattern.get('file')
                if file:
                    files = [file]

            if not files:
                return 0.5  # Unknown

            survival_scores = []
            for file_path in files[:5]:  # Check up to 5 files
                # Check if file exists in main branch
                cmd = ["git", "show", f"{self.main_branch}:{file_path}"]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)

                if result.returncode == 0:
                    # File exists in main branch
                    # Check if it was modified recently
                    log_cmd = ["git", "log", f"--since={days} days ago", "--oneline", "--", file_path]
                    log_result = subprocess.run(log_cmd, capture_output=True, text=True, timeout=5)

                    if log_result.stdout.strip():
                        # File was modified and kept
                        survival_scores.append(1.0)
                    else:
                        # File exists but wasn't changed
                        survival_scores.append(0.7)
                else:
                    # File doesn't exist in main branch
                    survival_scores.append(0.0)

            return sum(survival_scores) / len(survival_scores) if survival_scores else 0.5

        except Exception as e:
            print(f"Error checking git survival: {e}", file=sys.stderr)
            return 0.5  # Unknown

    def review_sprint_patterns(self, days: int = 14) -> Dict:
        """Review patterns from the last sprint period."""
        # Search for recent patterns - use a broader search
        recent_patterns = self.learner.search_patterns(
            "",  # Empty query to get all patterns
            mode='semantic',
            limit=100
        )

        # Categorize patterns
        review = {
            'survived_to_main': [],
            'high_confidence': [],
            'frequently_used': [],
            'violations': [],
            'experimental': [],
            'total_patterns': len(recent_patterns)
        }

        for pattern in recent_patterns:
            # Skip if no timestamp
            if not pattern.get('timestamp'):
                continue

            # Check age
            pattern_age = (time.time() - pattern['timestamp']) / 86400
            if pattern_age > days:
                continue

            # Check git survival
            survival_rate = self.get_git_survival_rate(pattern, days)

            # Categorize
            if survival_rate > 0.8:
                review['survived_to_main'].append({
                    'pattern': pattern,
                    'survival_rate': survival_rate,
                    'action': 'promote'
                })
            elif pattern.get('confidence', 0) > 0.9:
                review['high_confidence'].append({
                    'pattern': pattern,
                    'action': 'validate'
                })
            elif pattern.get('usage_count', 0) > 5:
                review['frequently_used'].append({
                    'pattern': pattern,
                    'usage': pattern['usage_count'],
                    'action': 'boost_confidence'
                })
            elif pattern.get('type') == 'architecture_violation':
                review['violations'].append({
                    'pattern': pattern,
                    'action': 'review_and_fix'
                })
            else:
                review['experimental'].append({
                    'pattern': pattern,
                    'action': 'evaluate'
                })

        return review

    def apply_review_decisions(self, review: Dict, auto_apply: bool = False) -> Dict:
        """Apply review decisions to patterns."""
        results = {
            'promoted': 0,
            'boosted': 0,
            'demoted': 0,
            'archived': 0
        }

        # Process survived patterns
        for item in review.get('survived_to_main', []):
            pattern = item['pattern']
            if auto_apply or self.confirm_action(pattern, "Promote to LONGTERM"):
                # Increase confidence and promote tier
                pattern['confidence'] = min(1.0, pattern.get('confidence', 0.7) * 1.2)
                self.learner.learn_pattern(pattern)  # Re-learn with higher confidence
                results['promoted'] += 1

        # Process high confidence patterns
        for item in review.get('high_confidence', []):
            pattern = item['pattern']
            if pattern.get('usage_count', 0) < 2:
                # High confidence but low usage - might be overconfident
                if auto_apply or self.confirm_action(pattern, "Reduce confidence (low usage)"):
                    pattern['confidence'] *= 0.9
                    self.learner.learn_pattern(pattern)
                    results['demoted'] += 1

        # Process frequently used patterns
        for item in review.get('frequently_used', []):
            pattern = item['pattern']
            if auto_apply or self.confirm_action(pattern, "Boost confidence (high usage)"):
                pattern['confidence'] = min(1.0, pattern.get('confidence', 0.5) * 1.1)
                pattern['usage_count'] = item['usage']
                self.learner.learn_pattern(pattern)
                results['boosted'] += 1

        # Process violations
        for item in review.get('violations', []):
            pattern = item['pattern']
            if auto_apply or self.confirm_action(pattern, "Archive violation (should be fixed)"):
                # Archive violations that should be fixed
                pattern['archived'] = True
                pattern['confidence'] = 0.1
                self.learner.learn_pattern(pattern)
                results['archived'] += 1

        return results

    def confirm_action(self, pattern: Dict, action: str) -> bool:
        """Ask for confirmation on pattern action."""
        # In automated mode, just return True
        # In interactive mode, would show pattern and ask for confirmation
        return True  # For now, auto-confirm

    def format_review_summary(self, review: Dict) -> str:
        """Format review summary for display."""
        lines = [
            f"🏃 Sprint Pattern Review (Main branch: {self.main_branch})",
            f"   Total patterns reviewed: {review['total_patterns']}",
            "",
            f"✅ Survived to {self.main_branch} ({len(review['survived_to_main'])}):",
        ]

        for item in review['survived_to_main'][:3]:
            pattern = item['pattern']
            lines.append(f"   - {pattern.get('type', 'unknown')}: {pattern.get('content', '')[:60]}")
            lines.append(f"     Survival rate: {item['survival_rate']:.0%}")

        lines.extend([
            "",
            f"⭐ High confidence ({len(review['high_confidence'])}):",
        ])

        for item in review['high_confidence'][:3]:
            pattern = item['pattern']
            lines.append(f"   - {pattern.get('type', 'unknown')}: {pattern.get('content', '')[:60]}")

        lines.extend([
            "",
            f"🔥 Frequently used ({len(review['frequently_used'])}):",
        ])

        for item in review['frequently_used'][:3]:
            pattern = item['pattern']
            lines.append(f"   - Used {item['usage']} times: {pattern.get('content', '')[:60]}")

        if review['violations']:
            lines.extend([
                "",
                f"⚠️ Architecture violations ({len(review['violations'])}):",
            ])

            for item in review['violations'][:3]:
                pattern = item['pattern']
                lines.append(f"   - {pattern.get('content', '')[:80]}")

        lines.extend([
            "",
            f"🧪 Experimental ({len(review['experimental'])})",
            "",
            "Recommended actions:",
            f"  → Promote {len(review['survived_to_main'])} patterns to LONGTERM",
            f"  → Boost confidence for {len(review['frequently_used'])} patterns",
            f"  → Review {len(review['violations'])} violations",
        ])

        return "\n".join(lines)


def main():
    """Main command handler."""
    # Parse arguments from stdin
    try:
        args = sys.argv[1:] if len(sys.argv) > 1 else []
    except:
        args = []

    # Parse days parameter
    days = 14
    for arg in args:
        if arg.isdigit():
            days = int(arg)
        elif "=" in arg and arg.split("=")[0] == "days":
            days = int(arg.split("=")[1])

    # Initialize reviewer
    reviewer = SprintReviewer()

    print(f"Detected main branch: {reviewer.main_branch}", file=sys.stderr)

    # Review patterns
    review = reviewer.review_sprint_patterns(days)

    # Format and display summary
    summary = reviewer.format_review_summary(review)
    print(summary)

    # Ask for confirmation
    print("\nApply recommended actions? [Y/n]: ", end='')
    sys.stdout.flush()

    try:
        # In non-interactive mode, auto-apply
        response = input().strip().lower()
        if response in ['', 'y', 'yes']:
            results = reviewer.apply_review_decisions(review, auto_apply=True)
            print(f"\n✅ Applied changes:")
            print(f"   Promoted: {results['promoted']}")
            print(f"   Boosted: {results['boosted']}")
            print(f"   Demoted: {results['demoted']}")
            print(f"   Archived: {results['archived']}")
    except:
        # Non-interactive mode
        results = reviewer.apply_review_decisions(review, auto_apply=True)
        print(f"\n✅ Auto-applied changes: {sum(results.values())} patterns updated")


if __name__ == "__main__":
    main()