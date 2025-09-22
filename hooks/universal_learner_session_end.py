#!/usr/bin/env python3
"""
Universal Learner Session End Hook
Consolidates and promotes patterns at session end.
"""

import json
import sys
import time
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List

sys.path.insert(0, str(Path(__file__).parent))
from universal_learner import get_learner

def consolidate_patterns(learner) -> Dict:
    """Consolidate and analyze session patterns."""
    pattern_cache = learner.pattern_cache.get("patterns", {})

    stats = {
        "total_patterns": len(pattern_cache),
        "promoted": 0,
        "by_type": {},
        "high_usage": [],
        "high_confidence": []
    }

    # Analyze patterns by type
    for pattern_id, data in pattern_cache.items():
        pattern_data = data.get("data", {})
        pattern_type = pattern_data.get("type", "unknown")
        usage_count = data.get("usage_count", 0)
        confidence = pattern_data.get("confidence", 0.5)

        # Count by type
        if pattern_type not in stats["by_type"]:
            stats["by_type"][pattern_type] = {"count": 0, "promoted": 0}
        stats["by_type"][pattern_type]["count"] += 1

        # Track high usage patterns (3+ uses)
        if usage_count >= 3:
            stats["high_usage"].append({
                "id": pattern_id,
                "type": pattern_type,
                "usage": usage_count,
                "content": learner.extract_semantic_content(pattern_data)[:100]
            })

        # Track high confidence patterns
        if confidence >= 0.8:
            stats["high_confidence"].append({
                "id": pattern_id,
                "type": pattern_type,
                "confidence": confidence
            })

    return stats

def promote_valuable_patterns(learner, stats: Dict) -> int:
    """Promote patterns based on usage and confidence."""
    pattern_cache = learner.pattern_cache.get("patterns", {})
    promoted_count = 0

    # Create a list of items to avoid dictionary modification during iteration
    for pattern_id, data in list(pattern_cache.items()):
        pattern_data = data.get("data", {})
        usage_count = data.get("usage_count", 0)
        confidence = pattern_data.get("confidence", 0.5)
        pattern_type = pattern_data.get("type", "unknown")

        # Promotion criteria
        should_promote = False
        new_confidence = confidence

        # High usage promotion (3+ uses)
        if usage_count >= 3:
            # Boost confidence based on usage
            new_confidence = min(0.95, confidence + (usage_count * 0.1))
            should_promote = True

        # Security/critical patterns get promoted faster
        elif pattern_type in ["security", "critical", "architecture"] and usage_count >= 2:
            new_confidence = min(0.9, confidence + 0.2)
            should_promote = True

        # Best practices with good confidence
        elif pattern_type in ["best_practice", "coding_standard"] and confidence >= 0.7:
            new_confidence = min(0.85, confidence + 0.1)
            should_promote = True

        if should_promote:
            try:
                learner.promote_pattern(pattern_id, new_confidence)
                promoted_count += 1

                # Update type stats
                if pattern_type in stats["by_type"]:
                    stats["by_type"][pattern_type]["promoted"] += 1

            except Exception as e:
                print(f"Failed to promote pattern {pattern_id}: {e}", file=sys.stderr)

    return promoted_count

def save_session_insights(learner, stats: Dict):
    """Save session summary as a learning pattern."""

    # Build insight text
    insights = []

    # Most learned pattern types
    if stats["by_type"]:
        top_types = sorted(stats["by_type"].items(),
                          key=lambda x: x[1]["count"],
                          reverse=True)[:3]
        for ptype, counts in top_types:
            insights.append(f"{ptype}: {counts['count']} patterns ({counts['promoted']} promoted)")

    # High usage patterns
    if stats["high_usage"]:
        insights.append(f"Frequently used patterns: {len(stats['high_usage'])}")
        for pattern in stats["high_usage"][:3]:
            insights.append(f"  - {pattern['type']}: {pattern['content'][:50]}... (used {pattern['usage']}x)")

    # Create session summary pattern
    session_summary = {
        "type": "session_summary",
        "content": f"Session {learner.session_id} learned {stats['total_patterns']} patterns, promoted {stats['promoted']}. Key insights: " + "; ".join(insights),
        "patterns_learned": stats["total_patterns"],
        "patterns_promoted": stats["promoted"],
        "session_id": learner.session_id,
        "project": learner.project_name,
        "timestamp": time.time(),
        "confidence": 0.8,
        "insights": insights,
        "stats": stats
    }

    # Store in EPISODIC tier for session history
    learner.learn_pattern(session_summary)

def cleanup_stale_patterns(learner):
    """Remove very old, unused patterns from cache."""
    pattern_cache = learner.pattern_cache.get("patterns", {})
    current_time = time.time()
    removed_count = 0

    # Create a copy of keys to avoid modifying dict during iteration
    pattern_ids = list(pattern_cache.keys())

    for pattern_id in pattern_ids:
        data = pattern_cache[pattern_id]
        pattern_data = data.get("data", {})
        timestamp = data.get("timestamp", current_time)
        usage_count = data.get("usage_count", 0)

        # Remove patterns older than 7 days with no usage
        age_days = (current_time - timestamp) / 86400
        if age_days > 7 and usage_count == 0:
            del pattern_cache[pattern_id]
            removed_count += 1

        # Remove low-confidence patterns older than 3 days
        elif age_days > 3 and pattern_data.get("confidence", 0) < 0.3 and usage_count < 2:
            del pattern_cache[pattern_id]
            removed_count += 1

    if removed_count > 0:
        print(f"Cleaned up {removed_count} stale patterns", file=sys.stderr)

    return removed_count

def main():
    """Main hook handler for SessionEnd event."""
    # Read the hook input
    try:
        input_data = json.loads(sys.stdin.read())
        event_name = input_data.get("hook_event_name")

        # Only run on SessionEnd
        if event_name != "SessionEnd":
            print(json.dumps({"action": "continue"}))
            return

    except Exception as e:
        # If we can't parse input, just pass through
        print(f"Error parsing input: {e}", file=sys.stderr)
        print(json.dumps({"action": "continue"}))
        return

    try:
        learner = get_learner()

        # Consolidate patterns from session
        stats = consolidate_patterns(learner)

        # Promote valuable patterns
        promoted_count = promote_valuable_patterns(learner, stats)
        stats["promoted"] = promoted_count

        # Save session insights
        save_session_insights(learner, stats)

        # Cleanup stale patterns
        removed_count = cleanup_stale_patterns(learner)

        # Save updated cache
        learner.save_pattern_cache()

        # Report results
        print(f"═══════════════════════════════════════════════", file=sys.stderr)
        print(f"📚 Universal Learner Session Summary", file=sys.stderr)
        print(f"═══════════════════════════════════════════════", file=sys.stderr)
        print(f"✓ Patterns learned: {stats['total_patterns']}", file=sys.stderr)
        print(f"✓ Patterns promoted: {promoted_count}", file=sys.stderr)
        print(f"✓ High-usage patterns: {len(stats['high_usage'])}", file=sys.stderr)
        print(f"✓ High-confidence patterns: {len(stats['high_confidence'])}", file=sys.stderr)

        if removed_count > 0:
            print(f"✓ Stale patterns removed: {removed_count}", file=sys.stderr)

        # Show pattern types
        if stats["by_type"]:
            print(f"\nPattern types learned:", file=sys.stderr)
            for ptype, counts in sorted(stats["by_type"].items(),
                                       key=lambda x: x[1]["count"],
                                       reverse=True)[:5]:
                promoted_str = f" ({counts['promoted']} promoted)" if counts['promoted'] > 0 else ""
                print(f"  • {ptype}: {counts['count']}{promoted_str}", file=sys.stderr)

        print(f"═══════════════════════════════════════════════", file=sys.stderr)

    except Exception as e:
        print(f"Error in universal learner session end: {e}", file=sys.stderr)

    # Always allow session to continue
    print(json.dumps({"action": "continue"}))

if __name__ == "__main__":
    main()