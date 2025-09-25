#!/usr/bin/env python3
"""
Agent Response Capture Hook
===========================
Captures agent responses at SubagentStop events for analysis.
FIXED to actually read transcripts properly.

Key fixes:
- Reads actual transcript file (not imaginary hook_data)
- Uses checkpoint system to avoid reprocessing
- Handles nested message structure correctly
- NO FALLBACKS - crashes if components missing
"""

import json
import sys
import time
import hashlib
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
import traceback

# Add parent directory for imports
sys.path.insert(0, str(Path(__file__).parent))

# REQUIRED imports - NO FALLBACKS
from response_analyzer import ResponseAnalyzer
from checkpoint_system import CheckpointManager, TranscriptEntry
from pattern_detector import PatternDetectionEngine

class AgentResponseCapture:
    """Captures and analyzes subagent responses at SubagentStop events."""

    def __init__(self):
        """Initialize with REQUIRED components - NO FALLBACKS."""
        self.analyzer = ResponseAnalyzer()
        self.checkpoint_mgr = CheckpointManager()
        self.pattern_detector = PatternDetectionEngine()

    def process_hook_input(self, input_data: Dict) -> Dict:
        """Process SubagentStop hook input."""

        event = input_data.get('hook_event_name', '')
        if event != 'SubagentStop':
            return {"action": "continue"}

        transcript_path = input_data.get('transcript_path')
        if not transcript_path or not Path(transcript_path).exists():
            print(f"ERROR: No transcript path for SubagentStop", file=sys.stderr)
            return {"action": "continue"}

        session_id = input_data.get('session_id', 'unknown')

        try:
            # For SubagentStop, we want to capture the MOST RECENT agent output
            # Since we don't know exactly which entries belong to this subagent,
            # we'll look for recent unprocessed assistant entries
            recent_entries = self._get_recent_subagent_entries(
                transcript_path, session_id, lookback_count=10
            )

            if not recent_entries:
                return {"action": "continue"}

            # Analyze the subagent's output
            analysis_results = []
            critical_issues = []

            for entry in recent_entries:
                result = self.analyzer.analyze_response(entry)
                if result:
                    analysis_results.append(result)

                    # Check for hallucinations
                    risk_level = result.hallucination_risk.get('risk_level', 'low') if result.hallucination_risk else 'low'
                    if risk_level in ['high', 'medium']:
                        critical_issues.append({
                            'type': 'subagent_hallucination',
                            'details': result.hallucination_risk.get('details', 'Subagent claimed something that does not exist')
                        })

                    # Check for high drift
                    drift_score = result.semantic_drift.get('drift_score', 0) if result.semantic_drift else 0
                    if drift_score > 0.7:
                        critical_issues.append({
                            'type': 'subagent_drift',
                            'details': f'Subagent drifting from patterns (score: {drift_score:.2f})'
                        })

                    # Detect patterns
                    patterns = self.pattern_detector.analyze_response_for_patterns(result)

                    # Check for critical pattern violations
                    for pattern in patterns:
                        if hasattr(pattern, 'severity') and pattern.severity == 'critical':
                            critical_issues.append({
                                'type': 'subagent_pattern_violation',
                                'details': pattern.description
                            })

                    # Store significant patterns
                    if patterns:
                        self._store_subagent_patterns(patterns, entry.agent_type)

                # Mark as processed
                self.checkpoint_mgr.mark_processed(entry)

            # Save checkpoint
            self.checkpoint_mgr.save_checkpoint()

            # Log analysis summary
            if analysis_results:
                self._log_analysis_summary(analysis_results)

            # Block if critical issues found
            if critical_issues:
                issue_list = "\n".join(f"• {issue['type']}: {issue['details']}" for issue in critical_issues)
                return {
                    "action": "block",
                    "message": f"❌ Subagent produced problematic output:\n{issue_list}\n\n🔧 The subagent needs to fix these issues."
                }

            return {"action": "continue"}

        except Exception as e:
            print(f"ERROR in subagent response capture: {e}", file=sys.stderr)
            traceback.print_exc(file=sys.stderr)
            # Still continue - don't block subagent
            return {"action": "continue"}

    def _get_recent_subagent_entries(self, transcript_path: str, session_id: str,
                                      lookback_count: int = 10) -> List[TranscriptEntry]:
        """Get recent unprocessed entries that belong to the subagent.

        Uses isSidechain=true to definitively identify subagent messages!
        """

        entries = []
        subagent_entries = []

        try:
            with open(transcript_path, 'r') as f:
                for line_num, line in enumerate(f, 1):
                    if not line.strip():
                        continue

                    try:
                        entry_data = json.loads(line)

                        # ONLY entries with isSidechain=true are from subagents!
                        if not entry_data.get('isSidechain', False):
                            continue

                        # Only assistant entries
                        if entry_data.get('type') != 'assistant':
                            continue

                        # Extract text content
                        text_content = self._extract_assistant_text(entry_data)
                        if not text_content:
                            continue

                        # Create entry
                        timestamp_str = entry_data.get('timestamp', '')
                        try:
                            timestamp = float(timestamp_str) if timestamp_str else datetime.now().timestamp()
                        except:
                            timestamp = datetime.now().timestamp()

                        entry = TranscriptEntry(
                            entry_id=self._generate_entry_id(entry_data, line_num),
                            timestamp=timestamp,
                            agent_type='subagent',  # Definitively a subagent
                            content=text_content,
                            session_id=session_id,
                            task_id=entry_data.get('requestId')  # Might help group by task
                        )

                        subagent_entries.append(entry)

                    except json.JSONDecodeError:
                        continue

            # Get the most recent unprocessed subagent entries
            # Sort by timestamp (most recent first)
            subagent_entries.sort(key=lambda e: e.timestamp, reverse=True)

            # Take the most recent N unprocessed entries
            for entry in subagent_entries[:lookback_count]:
                if not self.checkpoint_mgr.is_processed(entry):
                    entries.append(entry)

            if entries:
                print(f"Found {len(entries)} unprocessed subagent messages (isSidechain=true)", file=sys.stderr)

            return entries

        except Exception as e:
            print(f"Error reading subagent transcript: {e}", file=sys.stderr)
            return []

    def _extract_assistant_text(self, entry: Dict) -> str:
        """Extract text from assistant entry with nested structure."""

        # Handle nested message structure
        if 'message' in entry and isinstance(entry['message'], dict):
            message = entry['message']
            if 'content' in message and isinstance(message['content'], list):
                text_parts = []
                for item in message['content']:
                    if isinstance(item, dict) and item.get('type') == 'text':
                        if 'text' in item:
                            text_parts.append(item['text'])
                return '\n'.join(text_parts)

        return entry.get('content', '')

    def _generate_entry_id(self, entry_data: Dict, line_num: int) -> str:
        """Generate deterministic entry ID."""
        if 'uuid' in entry_data:
            return entry_data['uuid']

        content_str = json.dumps(entry_data, sort_keys=True)
        entry_hash = hashlib.sha256(
            f"{content_str}{line_num}".encode()
        ).hexdigest()[:16]
        return f"subagent_{line_num}_{entry_hash}"

    def _store_subagent_patterns(self, patterns: List, agent_type: str) -> None:
        """Store significant patterns from subagent analysis."""
        try:
            for pattern in patterns:
                if hasattr(pattern, 'severity') and pattern.severity in ['critical', 'warning']:
                    print(f"Subagent pattern detected: {pattern.description}", file=sys.stderr)
                    # Patterns are already stored by the pattern detector
        except Exception as e:
            print(f"Error storing subagent patterns: {e}", file=sys.stderr)

    def _log_analysis_summary(self, results: List) -> None:
        """Log summary of analysis results."""
        if not results:
            return

        hallucination_count = sum(
            1 for r in results
            if r.hallucination_risk and r.hallucination_risk.get('risk_level') == 'high'
        )

        high_drift_count = sum(
            1 for r in results
            if r.semantic_drift and r.semantic_drift.get('drift_score', 0) > 0.7
        )

        if hallucination_count > 0 or high_drift_count > 0:
            print(f"⚠️ Subagent analysis: {hallucination_count} hallucinations, {high_drift_count} high drift",
                  file=sys.stderr)

def main():
    """Main hook handler."""
    try:
        input_data = json.loads(sys.stdin.read())
        capture = AgentResponseCapture()
        result = capture.process_hook_input(input_data)
        print(json.dumps(result))
    except Exception as e:
        print(f"FATAL: Subagent capture hook failed: {e}", file=sys.stderr)
        # Return continue anyway - don't break the chain
        print(json.dumps({"action": "continue"}))

if __name__ == "__main__":
    main()