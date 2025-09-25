#!/usr/bin/env python3
"""
Real-time Response Monitor Hook
Monitors agent thoughts and responses after EVERY tool use.
Uses checkpoint system to avoid reprocessing.
"""

import json
import sys
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Set
import traceback
import hashlib

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

# REQUIRED imports - NO FALLBACKS
from response_analyzer import ResponseAnalyzer
from checkpoint_system import CheckpointManager, TranscriptEntry
from pattern_detector import PatternDetectionEngine

class RealtimeMonitor:
    """Monitors responses incrementally after each tool use."""

    def __init__(self):
        # Initialize REQUIRED components - NO FALLBACKS
        self.analyzer = ResponseAnalyzer()
        self.checkpoint_mgr = CheckpointManager()
        self.pattern_detector = PatternDetectionEngine()

    def process_hook_input(self, input_data: Dict) -> Dict:
        """Process PostToolUse hook input."""

        event = input_data.get('hook_event_name', '')
        if event != 'PostToolUse':
            return {"action": "continue"}

        # Get transcript path
        transcript_path = input_data.get('transcript_path')
        if not transcript_path or not Path(transcript_path).exists():
            return {"action": "continue"}

        session_id = input_data.get('session_id', 'unknown')
        tool_name = input_data.get('tool_name', 'unknown')

        try:
            # Read and process new transcript entries
            new_entries = self._read_new_entries(transcript_path, session_id)

            if not new_entries:
                return {"action": "continue"}

            # Analyze new content
            issues_found = self._analyze_entries(new_entries, tool_name)

            # Mark entries as processed and save checkpoint
            for entry in new_entries:
                self.checkpoint_mgr.mark_processed(entry)
            self.checkpoint_mgr.save_checkpoint()

            # If critical issues found, potentially block
            if self._has_critical_issues(issues_found):
                return self._create_block_response(issues_found)

            return {"action": "continue"}

        except Exception as e:
            print(f"Error in realtime monitoring: {e}", file=sys.stderr)
            traceback.print_exc(file=sys.stderr)
            return {"action": "continue"}

    def _read_new_entries(self, transcript_path: str, session_id: str) -> List[TranscriptEntry]:
        """Read only new transcript entries since checkpoint."""

        new_entries = []

        # Get last checkpoint position for this session
        last_checkpoint_time = self.checkpoint_mgr.get_session_checkpoint(session_id)

        try:
            with open(transcript_path, 'r') as f:
                for line_num, line in enumerate(f, 1):
                    if not line.strip():
                        continue

                    try:
                        entry_data = json.loads(line)

                        # Only process assistant entries
                        if entry_data.get('type') != 'assistant':
                            continue

                        # Skip subagent entries (handled by agent_response_capture)
                        # We only monitor main agent in realtime
                        if entry_data.get('isSidechain', False):
                            continue

                        # Quick skip if before checkpoint (save processing)
                        entry_timestamp = entry_data.get('timestamp', '')
                        if entry_timestamp and isinstance(entry_timestamp, str):
                            try:
                                if float(entry_timestamp) <= last_checkpoint_time:
                                    continue  # Skip old entries
                            except:
                                pass

                        # Extract text content
                        text_content = self._extract_assistant_text(entry_data)
                        if not text_content:
                            continue

                        # Create TranscriptEntry
                        # Ensure timestamp is a float
                        timestamp_str = entry_data.get('timestamp', '')
                        try:
                            timestamp = float(timestamp_str) if timestamp_str else datetime.now().timestamp()
                        except (ValueError, TypeError):
                            timestamp = datetime.now().timestamp()

                        # Generate deterministic entry ID
                        entry_id = self._generate_entry_id(entry_data, line_num)

                        entry = TranscriptEntry(
                            entry_id=entry_id,
                            timestamp=timestamp,
                            agent_type='main',  # Could extract from entry_data if available
                            content=text_content,
                            session_id=session_id
                        )

                        # Check if already processed
                        if not self.checkpoint_mgr.is_processed(entry):
                            new_entries.append(entry)

                    except json.JSONDecodeError:
                        continue

        except Exception as e:
            print(f"Error reading transcript: {e}", file=sys.stderr)

        return new_entries

    def _generate_entry_id(self, entry_data: Dict, line_num: int) -> str:
        """Generate deterministic entry ID."""
        # Use UUID if available
        if 'uuid' in entry_data:
            return entry_data['uuid']

        # Otherwise create deterministic hash
        content_str = json.dumps(entry_data, sort_keys=True)
        entry_hash = hashlib.sha256(
            f"{content_str}{line_num}".encode()
        ).hexdigest()[:16]
        return f"entry_{line_num}_{entry_hash}"

    def _extract_assistant_text(self, entry: Dict) -> str:
        """Extract text from assistant entry with nested structure."""

        # Handle nested message structure
        if 'message' in entry and isinstance(entry['message'], dict):
            message = entry['message']
            if 'content' in message and isinstance(message['content'], list):
                # Collect all text items
                text_parts = []
                for item in message['content']:
                    if isinstance(item, dict) and item.get('type') == 'text':
                        if 'text' in item:
                            text_parts.append(item['text'])
                return '\n'.join(text_parts)

        # Fallback to direct content if no nested structure
        return entry.get('content', '')

    def _analyze_entries(self, entries: List[TranscriptEntry], tool_name: str) -> List[Dict]:
        """Analyze new transcript entries for issues."""

        issues = []

        for entry in entries:
            # Use PRISM to analyze (it expects the TranscriptEntry object)
            analysis = self.analyzer.analyze_response(entry)

            # Check for concerning patterns
            if analysis:
                # Hallucination detection - BLOCK even medium risk
                risk_level = analysis.hallucination_risk.get('risk_level', 'low') if analysis.hallucination_risk else 'low'
                if risk_level in ['high', 'medium']:
                    issues.append({
                        'type': 'hallucination',
                        'severity': 'critical',  # Always critical for hallucinations
                        'content': analysis.hallucination_risk.get('details', 'Claiming something exists that does not'),
                        'tool': tool_name,
                        'actionable': 'Check actual files/APIs before claiming they exist'
                    })

                # Drift detection - BLOCK high drift
                drift_score = analysis.semantic_drift.get('drift_score', 0) if analysis.semantic_drift else 0
                if drift_score > 0.6:  # Lowered threshold
                    issues.append({
                        'type': 'drift',
                        'severity': 'critical' if drift_score > 0.8 else 'warning',
                        'content': f"Drifting from established patterns (score: {drift_score:.2f})",
                        'tool': tool_name,
                        'actionable': 'Stay consistent with existing code patterns'
                    })

            # Pattern violations - BLOCK critical AND warning patterns
            if analysis:  # analyze_response_for_patterns expects AnalysisResult
                patterns = self.pattern_detector.analyze_response_for_patterns(analysis)
                for pattern in patterns:
                    if pattern.severity in ['critical', 'warning']:
                        issues.append({
                            'type': 'pattern_violation',
                            'severity': pattern.severity,
                            'content': pattern.description,
                            'tool': tool_name,
                            'actionable': 'Follow established code patterns'
                        })

            # Check user preference violations
            # Import preference manager if available
            try:
                from preference_manager import PreferenceManager
                pref_mgr = PreferenceManager()
                pref_violations = pref_mgr.check_violations(entry.content, "")
                for violation in pref_violations:
                    issues.append({
                        'type': 'preference_violation',
                        'severity': 'critical',  # User preferences are always critical
                        'content': violation.get('message', 'User preference violated'),
                        'tool': tool_name,
                        'actionable': violation.get('fix', 'Respect user preferences')
                    })
            except ImportError:
                pass  # Preference manager not available yet

        return issues

    def _has_critical_issues(self, issues: List[Dict]) -> bool:
        """Check if any issues require blocking (critical OR warning)."""
        # Block on both critical and warning issues
        return any(i.get('severity') in ['critical', 'warning'] for i in issues)

    def _create_block_response(self, issues: List[Dict]) -> Dict:
        """Create block response with actionable guidance."""

        # Include both critical and warning issues
        blocking_issues = [i for i in issues if i.get('severity') in ['critical', 'warning']]

        message_parts = ["❌ Code quality issues detected:\n"]

        # Group by type for clearer messaging
        by_type = {}
        for issue in blocking_issues:
            issue_type = issue.get('type', 'unknown')
            if issue_type not in by_type:
                by_type[issue_type] = []
            by_type[issue_type].append(issue)

        # Format each type of issue
        for issue_type, type_issues in by_type.items():
            if issue_type == 'hallucination':
                message_parts.append("\n🚫 HALLUCINATION DETECTED:")
            elif issue_type == 'preference_violation':
                message_parts.append("\n⚠️ USER PREFERENCE VIOLATED:")
            elif issue_type == 'drift':
                message_parts.append("\n📊 PATTERN DRIFT:")
            else:
                message_parts.append(f"\n⚠️ {issue_type.upper().replace('_', ' ')}:")

            for issue in type_issues:
                message_parts.append(f"  • {issue.get('content')}")
                if issue.get('actionable'):
                    message_parts.append(f"    → {issue.get('actionable')}")

        message_parts.append("\n\n🔧 Fix these issues and try again.")

        return {
            "action": "block",
            "message": "\n".join(message_parts)
        }

def main():
    """Main hook handler."""

    try:
        input_data = json.loads(sys.stdin.read())
        monitor = RealtimeMonitor()
        result = monitor.process_hook_input(input_data)
        print(json.dumps(result))
    except Exception as e:
        # On error, don't block
        print(json.dumps({"action": "continue"}))

if __name__ == "__main__":
    main()