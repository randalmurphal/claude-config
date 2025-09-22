#!/opt/envs/py3.13/bin/python
"""
Chamber Cleanup Hook
Automatically removes orphaned git worktrees from abandoned orchestrations.
"""

import sys
import json
import subprocess
import time
from pathlib import Path
from typing import List, Dict, Tuple
import redis

def get_git_worktrees() -> List[Dict]:
    """Get all git worktrees in the current repository."""
    result = subprocess.run(
        ['git', 'worktree', 'list', '--porcelain'],
        capture_output=True,
        text=True
    )

    worktrees = []
    current = {}

    for line in result.stdout.strip().split('\n'):
        if not line:
            if current:
                worktrees.append(current)
                current = {}
            continue

        if line.startswith('worktree '):
            current['path'] = line.replace('worktree ', '')
        elif line.startswith('branch '):
            current['branch'] = line.replace('branch ', '')
        elif line.startswith('HEAD '):
            current['head'] = line.replace('HEAD ', '')

    if current:
        worktrees.append(current)

    return worktrees

def get_chamber_metadata(redis_client: redis.Redis, chamber_path: str) -> Dict:
    """Get chamber metadata from Redis."""
    # Extract chamber name from path
    chamber_name = Path(chamber_path).name

    # Try to find chamber data in Redis
    pattern = f"chamber:*:{chamber_name}"
    keys = list(redis_client.scan_iter(match=pattern))

    if not keys:
        return {}

    # Get the most recent chamber data
    for key in keys:
        data = redis_client.hgetall(key)
        if data:
            # Convert bytes to strings
            return {k.decode(): v.decode() for k, v in data.items()}

    return {}

def is_chamber_active(redis_client: redis.Redis, task_id: str) -> bool:
    """Check if a task is still active."""
    task_key = f"task:{task_id}"
    task_data = redis_client.hgetall(task_key)

    if not task_data:
        return False

    status = task_data.get(b'state', b'').decode()
    return status in ['in_progress', 'pending']

def get_chamber_age_hours(chamber_path: str) -> float:
    """Get age of chamber in hours."""
    path = Path(chamber_path)
    if not path.exists():
        return 0

    # Check modification time of the directory
    mtime = path.stat().st_mtime
    age_seconds = time.time() - mtime
    return age_seconds / 3600

def has_uncommitted_changes(chamber_path: str) -> bool:
    """Check if chamber has uncommitted changes."""
    result = subprocess.run(
        ['git', 'status', '--porcelain'],
        cwd=chamber_path,
        capture_output=True,
        text=True
    )
    return bool(result.stdout.strip())

def remove_worktree(chamber_path: str, force: bool = False):
    """Remove a git worktree."""
    cmd = ['git', 'worktree', 'remove', chamber_path]
    if force:
        cmd.insert(3, '--force')

    subprocess.run(cmd, capture_output=True)

def main():
    """Main hook handler."""
    input_data = json.loads(sys.stdin.read())

    # Only run on session start
    if input_data.get('hook_event_name') != 'SessionStart':
        print(json.dumps({"action": "continue"}))
        return

    # Connect to Redis
    redis_url = 'redis://localhost:6379'
    try:
        redis_client = redis.from_url(redis_url, decode_responses=False)
        redis_client.ping()
    except:
        # Redis not available, skip cleanup
        print(json.dumps({"action": "continue"}))
        return

    # Get all worktrees
    worktrees = get_git_worktrees()

    # Filter for chamber worktrees (contain 'chamber' or 'worktree' in name)
    chamber_worktrees = [
        wt for wt in worktrees
        if 'chamber' in wt.get('branch', '').lower() or
           'chamber' in wt.get('path', '').lower() or
           'worktree' in wt.get('path', '').lower()
    ]

    if not chamber_worktrees:
        print(json.dumps({"action": "continue"}))
        return

    # Analyze each chamber
    to_remove = []
    preserved = []

    for worktree in chamber_worktrees:
        path = worktree['path']
        age_hours = get_chamber_age_hours(path)

        # Get metadata from Redis
        metadata = get_chamber_metadata(redis_client, path)
        task_id = metadata.get('task_id')

        # Determine if should remove
        should_remove = False
        reason = ""

        if age_hours > 48:
            should_remove = True
            reason = f"older than 48 hours ({age_hours:.1f}h)"
        elif age_hours > 24 and not task_id:
            should_remove = True
            reason = f"orphaned (no task ID) and {age_hours:.1f}h old"
        elif task_id and not is_chamber_active(redis_client, task_id):
            if age_hours > 12:
                should_remove = True
                reason = f"task {task_id} completed and {age_hours:.1f}h old"

        # Check for uncommitted changes
        if should_remove and has_uncommitted_changes(path):
            # Preserve chambers with uncommitted work
            preserved.append({
                'path': path,
                'reason': 'has uncommitted changes',
                'age_hours': age_hours
            })
            should_remove = False

        if should_remove:
            to_remove.append({
                'path': path,
                'reason': reason,
                'age_hours': age_hours,
                'task_id': task_id
            })

    # Remove orphaned chambers
    removed_count = 0
    for chamber in to_remove:
        try:
            remove_worktree(chamber['path'], force=True)
            removed_count += 1

            # Clean Redis metadata
            if chamber['task_id']:
                chamber_key = f"chamber:{chamber['task_id']}:*"
                for key in redis_client.scan_iter(match=chamber_key):
                    redis_client.delete(key)
        except Exception as e:
            # Log but don't crash
            print(f"Failed to remove {chamber['path']}: {e}", file=sys.stderr)

    # Report cleanup results
    if removed_count > 0 or preserved:
        report = []

        if removed_count > 0:
            report.append(f"🧹 Cleaned {removed_count} orphaned chambers:")
            for chamber in to_remove[:3]:
                report.append(f"  - {Path(chamber['path']).name} ({chamber['reason']})")
            if len(to_remove) > 3:
                report.append(f"  ... and {len(to_remove) - 3} more")

        if preserved:
            report.append(f"\n⚠️ Preserved {len(preserved)} chambers with uncommitted changes:")
            for chamber in preserved[:2]:
                report.append(f"  - {Path(chamber['path']).name} ({chamber['age_hours']:.1f}h old)")

        print("\n".join(report), file=sys.stderr)

    redis_client.close()
    print(json.dumps({"action": "continue"}))

if __name__ == "__main__":
    main()