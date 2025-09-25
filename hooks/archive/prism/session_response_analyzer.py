#!/usr/bin/env python3
"""
Session Response Analyzer Hook
==============================
Analyzes session-end responses at Stop/SessionEnd events.
FIXED to actually read transcripts properly.

Key fixes:
- Reads actual transcript file (not imaginary hook_data)
- Uses checkpoint system to avoid reprocessing
- Handles nested message structure correctly
- Focuses on final responses and session summary
- NO FALLBACKS - crashes if components missing
"""

import json
import sys
import time
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import traceback

# Add parent directory for imports
sys.path.insert(0, str(Path(__file__).parent))

# REQUIRED imports - NO FALLBACKS
from response_analyzer import ResponseAnalyzer
from checkpoint_system import CheckpointManager, TranscriptEntry
from pattern_detector import PatternDetectionEngine

class SessionResponseAnalyzer:
    """Analyzes session-level responses and patterns at Stop/SessionEnd."""

    def __init__(self):
        """Initialize with REQUIRED components - NO FALLBACKS."""
        self.analyzer = ResponseAnalyzer()
        self.checkpoint_mgr = CheckpointManager()
        self.pattern_detector = PatternDetectionEngine()

    def process_hook_input(self, input_data: Dict) -> Dict:
        """Process Stop/SessionEnd hook input."""

        event = input_data.get('hook_event_name', '')
        if event not in ['Stop', 'SessionEnd']:
            return {"action": "continue"}

        transcript_path = input_data.get('transcript_path')
        if not transcript_path or not Path(transcript_path).exists():
            print(f"ERROR: No transcript path for {event}", file=sys.stderr)
            return {"action": "continue"}

        session_id = input_data.get('session_id', 'unknown')

        try:
            # For Stop/SessionEnd, we want to:
            # 1. Analyze the final response(s)
            # 2. Generate session-wide metrics
            # 3. Store session patterns

            # Get all unprocessed entries for this session
            all_entries, new_entries = self._get_session_entries(transcript_path, session_id)

            # Analyze final response (last few assistant messages)
            final_analysis = self._analyze_final_response(new_entries)

            # Generate session metrics
            session_metrics = self._calculate_session_metrics(all_entries)

            # Detect session-wide patterns
            session_patterns = self._detect_session_patterns(all_entries, session_metrics)

            # Store analysis results
            if final_analysis or session_patterns:
                self._store_session_analysis(
                    session_id, final_analysis, session_metrics, session_patterns
                )

            # Mark all new entries as processed
            for entry in new_entries:
                self.checkpoint_mgr.mark_processed(entry)
            self.checkpoint_mgr.save_checkpoint()

            # Log session summary
            self._log_session_summary(session_metrics, final_analysis, session_patterns)

            # Check if we should block based on critical issues
            should_block = False
            block_reasons = []

            # Check final analysis for critical issues
            if final_analysis and final_analysis.get('issues'):
                critical_issues = [i for i in final_analysis['issues'] if i.get('severity') == 'critical']
                if critical_issues:
                    should_block = True
                    for issue in critical_issues:
                        block_reasons.append(f"{issue['type']}: {issue.get('details', issue.get('description', 'Issue in final response'))}")

            # Check session patterns for critical issues
            if session_patterns:
                critical_patterns = [p for p in session_patterns if p.get('severity') == 'critical']
                if critical_patterns:
                    should_block = True
                    for pattern in critical_patterns:
                        block_reasons.append(f"{pattern['type']}: {pattern.get('message', 'Pattern violation detected')}")

            if should_block:
                return {
                    "action": "block",
                    "message": f"❌ Session quality issues:\n" + "\n".join(f"• {reason}" for reason in block_reasons) + "\n\n🔧 Address these issues in future sessions."
                }

            return {"action": "continue"}

        except Exception as e:
            print(f"ERROR in session response analyzer: {e}", file=sys.stderr)
            traceback.print_exc(file=sys.stderr)
            return {"action": "continue"}

    def _get_session_entries(self, transcript_path: str, session_id: str) -> Tuple[List[TranscriptEntry], List[TranscriptEntry]]:
        """Get all entries and identify new unprocessed ones.

        Returns:
            Tuple of (all_entries, new_entries)
        """

        all_entries = []
        new_entries = []

        try:
            with open(transcript_path, 'r') as f:
                for line_num, line in enumerate(f, 1):
                    if not line.strip():
                        continue

                    try:
                        entry_data = json.loads(line)

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
                            agent_type='main',  # Main agent for session
                            content=text_content,
                            session_id=session_id
                        )

                        all_entries.append(entry)

                        # Check if it's new (unprocessed)
                        if not self.checkpoint_mgr.is_processed(entry):
                            new_entries.append(entry)

                    except json.JSONDecodeError:
                        continue

        except Exception as e:
            print(f"Error reading session transcript: {e}", file=sys.stderr)

        return all_entries, new_entries

    def _analyze_final_response(self, new_entries: List[TranscriptEntry]) -> Optional[Dict]:
        """Analyze the final response(s) of the session."""

        if not new_entries:
            return None

        # Focus on the last few responses (final summary/conclusion)
        final_entries = new_entries[-3:] if len(new_entries) > 3 else new_entries

        final_analysis = {
            'entry_count': len(final_entries),
            'total_length': sum(len(e.content) for e in final_entries),
            'issues': []
        }

        for entry in final_entries:
            # Analyze with PRISM
            result = self.analyzer.analyze_response(entry)

            if result:
                # Check for issues
                if result.hallucination_risk and result.hallucination_risk.get('risk_level') == 'high':
                    final_analysis['issues'].append({
                        'type': 'hallucination',
                        'severity': 'critical',
                        'details': result.hallucination_risk.get('details', 'Hallucination in final response')
                    })

                if result.semantic_drift and result.semantic_drift.get('drift_score', 0) > 0.8:
                    final_analysis['issues'].append({
                        'type': 'high_drift',
                        'severity': 'warning',
                        'score': result.semantic_drift.get('drift_score')
                    })

                # Check patterns
                patterns = self.pattern_detector.analyze_response_for_patterns(result)
                for pattern in patterns:
                    if hasattr(pattern, 'severity') and pattern.severity == 'critical':
                        final_analysis['issues'].append({
                            'type': 'pattern_violation',
                            'severity': pattern.severity,
                            'description': pattern.description
                        })

        return final_analysis

    def _calculate_session_metrics(self, all_entries: List[TranscriptEntry]) -> Dict:
        """Calculate session-wide metrics."""

        if not all_entries:
            return {}

        # Sort by timestamp
        all_entries.sort(key=lambda e: e.timestamp)

        metrics = {
            'total_responses': len(all_entries),
            'session_duration': all_entries[-1].timestamp - all_entries[0].timestamp if len(all_entries) > 1 else 0,
            'total_content_length': sum(len(e.content) for e in all_entries),
            'avg_response_length': sum(len(e.content) for e in all_entries) / len(all_entries),
            'response_timestamps': [e.timestamp for e in all_entries]
        }

        # Calculate response frequency (responses per minute)
        if metrics['session_duration'] > 0:
            metrics['responses_per_minute'] = (metrics['total_responses'] / metrics['session_duration']) * 60

        # Identify long pauses (potential issues)
        long_pauses = []
        for i in range(1, len(all_entries)):
            time_diff = all_entries[i].timestamp - all_entries[i-1].timestamp
            if time_diff > 30:  # More than 30 seconds between responses
                long_pauses.append({
                    'position': i,
                    'duration': time_diff
                })
        metrics['long_pauses'] = long_pauses

        return metrics

    def _detect_session_patterns(self, all_entries: List[TranscriptEntry], metrics: Dict) -> List[Dict]:
        """Detect session-wide patterns and issues."""

        patterns = []

        # Pattern: Very long session (info only, not blocking)
        if metrics.get('session_duration', 0) > 3600:  # Over 1 hour
            patterns.append({
                'type': 'long_session',
                'severity': 'info',
                'duration_minutes': metrics['session_duration'] / 60
            })

        # Pattern: Many responses (potential looping) - this could indicate a real problem
        if metrics.get('total_responses', 0) > 150:  # Raised threshold
            patterns.append({
                'type': 'potential_looping',
                'severity': 'critical',  # Make this critical to block
                'count': metrics['total_responses'],
                'message': 'Excessive responses detected - possible infinite loop or repetitive behavior'
            })

        # REMOVED: Verbose response check - user explicitly doesn't want this

        # Pattern: Multiple long pauses (potential issues/errors)
        if len(metrics.get('long_pauses', [])) > 5:  # Raised threshold
            patterns.append({
                'type': 'multiple_errors_detected',
                'severity': 'warning',
                'pause_count': len(metrics['long_pauses']),
                'message': 'Multiple long pauses suggest repeated errors'
            })

        return patterns

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
        return f"session_{line_num}_{entry_hash}"

    def _store_session_analysis(self, session_id: str, final_analysis: Optional[Dict],
                                 metrics: Dict, patterns: List[Dict]) -> None:
        """Store session analysis in PRISM memory."""
        try:
            # Create a session summary entry
            session_summary = {
                'session_id': session_id,
                'timestamp': datetime.now().isoformat(),
                'metrics': metrics,
                'patterns': patterns,
                'final_analysis': final_analysis
            }

            # Store in PRISM (would need PRISM MCP integration here)
            # For now, just log it
            summary_path = Path.home() / '.claude' / 'session_summaries' / f"{session_id}.json"
            summary_path.parent.mkdir(parents=True, exist_ok=True)
            with open(summary_path, 'w') as f:
                json.dump(session_summary, f, indent=2, default=str)

        except Exception as e:
            print(f"Error storing session analysis: {e}", file=sys.stderr)

    def _log_session_summary(self, metrics: Dict, final_analysis: Optional[Dict], patterns: List[Dict]) -> None:
        """Log session summary to stderr."""

        print(f"\n=== Session Analysis Summary ===", file=sys.stderr)
        print(f"Total responses: {metrics.get('total_responses', 0)}", file=sys.stderr)
        print(f"Duration: {metrics.get('session_duration', 0) / 60:.1f} minutes", file=sys.stderr)
        print(f"Avg response length: {metrics.get('avg_response_length', 0):.0f} chars", file=sys.stderr)

        if final_analysis and final_analysis.get('issues'):
            print(f"⚠️ Final response issues: {len(final_analysis['issues'])}", file=sys.stderr)
            for issue in final_analysis['issues'][:3]:  # Show first 3
                print(f"  - {issue['type']}: {issue.get('severity', 'unknown')}", file=sys.stderr)

        if patterns:
            print(f"Session patterns detected: {len(patterns)}", file=sys.stderr)
            for pattern in patterns:
                print(f"  - {pattern['type']}: {pattern.get('severity', 'info')}", file=sys.stderr)

def main():
    """Main hook handler."""
    try:
        input_data = json.loads(sys.stdin.read())
        analyzer = SessionResponseAnalyzer()
        result = analyzer.process_hook_input(input_data)
        print(json.dumps(result))
    except Exception as e:
        print(f"FATAL: Session analyzer hook failed: {e}", file=sys.stderr)
        # Return continue anyway - don't break the chain
        print(json.dumps({"action": "continue"}))

if __name__ == "__main__":
    main()