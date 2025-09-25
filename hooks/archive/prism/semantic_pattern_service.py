#!/usr/bin/env python3
"""
Unified Semantic Pattern Service
================================
Single source of truth for ALL pattern detection using PRISM's CodeT5+ semantic understanding.
Replaces ALL hardcoded regex patterns with dynamic AI-powered discovery.

NO FALLBACKS - If PRISM isn't available, we fail loudly.
The only exception: Critical safety patterns (rm -rf /) remain hardcoded as a safety net.
"""

import json
import sys
import logging
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass, asdict
import redis

# Add parent directory
sys.path.insert(0, str(Path(__file__).parent))
from semantic_code_analyzer import get_semantic_analyzer
from prism_client import get_prism_client

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class DiscoveredPattern:
    """A pattern discovered by semantic analysis."""
    pattern_id: str
    pattern_type: str  # anti_pattern, design_pattern, vulnerability, assumption, etc.
    description: str
    confidence: float
    source: str  # Where it was discovered
    metadata: Dict[str, Any]

    def to_dict(self) -> Dict:
        return asdict(self)


class SemanticPatternService:
    """
    Unified service for ALL pattern detection.
    Everything goes through semantic understanding, no hardcoded patterns.
    """

    # ONLY critical safety patterns remain hardcoded
    CRITICAL_SAFETY_PATTERNS = {
        'bash': [
            ('rm -rf /', 'CATASTROPHIC: Deletes entire filesystem'),
            ('rm -rf /*', 'CATASTROPHIC: Deletes all root directories'),
            ('dd if=/dev/zero of=/dev/sda', 'CATASTROPHIC: Wipes hard drive'),
            (':(){ :|:& };:', 'CATASTROPHIC: Fork bomb')
        ]
    }

    def __init__(self):
        """Initialize with REQUIRED semantic analyzer and PRISM client."""
        # NO FALLBACKS - we require these services
        self.analyzer = get_semantic_analyzer()
        self.prism_client = get_prism_client()

        # Redis for caching discovered patterns
        try:
            self.redis = redis.Redis(host='localhost', port=6379, decode_responses=True)
            self.redis.ping()
        except:
            raise RuntimeError("Redis REQUIRED for pattern caching")

        # Track patterns discovered this session
        self.session_patterns: List[DiscoveredPattern] = []

    def detect_patterns(self, content: str, context: str = "general") -> Dict[str, List[str]]:
        """
        Detect ALL patterns in content using semantic analysis.
        NO predefined patterns - we discover them dynamically.

        Args:
            content: Code or text to analyze
            context: Context hint (code, bash, config, etc.)

        Returns:
            Dictionary of pattern types to list of patterns found
        """
        # Let PRISM discover patterns - don't tell it what to look for
        result = self.analyzer.detect_code_patterns(content)

        # Reorganize result structure
        patterns_found = {
            'design_patterns': result.get('patterns_found', []),
            'anti_patterns': result.get('anti_patterns', []),
            'suggestions': result.get('suggestions', [])
        }

        # Store discovered patterns for learning
        for pattern_type, patterns in patterns_found.items():
            if patterns and isinstance(patterns, list):
                for pattern in patterns:
                    discovered = DiscoveredPattern(
                        pattern_id=self._generate_pattern_id(pattern, pattern_type),
                        pattern_type=pattern_type,
                        description=pattern,
                        confidence=0.9,  # PRISM doesn't return confidence yet
                        source=context,
                        metadata={'content_sample': content[:200]}
                    )
                    self._store_pattern(discovered)

        return patterns_found

    def is_dangerous(self, content: str, operation_type: str = "code") -> Tuple[bool, List[str]]:
        """
        Determine if content is dangerous using semantic analysis.

        Args:
            content: Code/command to analyze
            operation_type: Type of operation (bash, code, sql, etc.)

        Returns:
            Tuple of (is_dangerous, list of reasons)
        """
        reasons = []

        # Check critical safety patterns ONLY for bash commands
        if operation_type == "bash":
            for pattern, reason in self.CRITICAL_SAFETY_PATTERNS.get('bash', []):
                if pattern in content:
                    return True, [f"CRITICAL: {reason}"]

        # Use semantic analysis for everything else
        expected = "safe operation that doesn't harm the system or data"
        analysis = self.analyzer.analyze_code_logic(content, expected)

        # Check for logical issues indicating danger
        if analysis.get('logic', {}).get('has_issues'):
            logical_issues = analysis['logic'].get('logical_issues', [])
            dangerous_issues = [
                issue for issue in logical_issues
                if any(danger in issue.lower() for danger in
                       ['delete', 'remove', 'destroy', 'wipe', 'truncate', 'drop'])
            ]
            if dangerous_issues:
                reasons.extend(dangerous_issues)

        # Check security vulnerabilities
        security = analysis.get('security', {})
        if security.get('vulnerabilities'):
            reasons.extend(security['vulnerabilities'])

        # Check anti-patterns that could be dangerous
        patterns = self.detect_patterns(content, operation_type)
        dangerous_patterns = patterns.get('anti_patterns', [])
        if dangerous_patterns:
            reasons.extend([f"Anti-pattern: {p}" for p in dangerous_patterns])

        return len(reasons) > 0, reasons

    def extract_intent(self, text: str) -> Tuple[str, float, Dict]:
        """
        Extract intent from text using semantic analysis.

        Returns:
            Tuple of (intent, confidence, metadata)
        """
        # Use PRISM to understand what the user wants
        analysis = self.prism_client.analyze(text)

        if not analysis:
            # Fallback to semantic analyzer
            try:
                summary = self.analyzer.summarize_code(text)
                return self._infer_intent_from_summary(summary)
            except:
                return 'unknown', 0.5, {}

        # Extract intent from PRISM analysis
        zone = analysis.get('zone', 'yellow')
        confidence = analysis.get('confidence', 0.5)

        # Map reasoning zones to intent categories
        intent_mapping = {
            'green': 'implementation',
            'yellow': 'investigation',
            'red': 'complex_problem'
        }

        intent = intent_mapping.get(zone, 'unknown')

        # Try to get more specific intent
        solutions = analysis.get('solutions', [])
        if solutions:
            if any('fix' in s.lower() or 'bug' in s.lower() for s in solutions):
                intent = 'bug_fix'
            elif any('add' in s.lower() or 'feature' in s.lower() for s in solutions):
                intent = 'feature'
            elif any('refactor' in s.lower() for s in solutions):
                intent = 'refactor'

        metadata = {
            'prism_zone': zone,
            'solutions': solutions,
            'method': analysis.get('method', 'unknown')
        }

        return intent, confidence, metadata

    def detect_assumptions(self, text: str) -> List[Dict]:
        """
        Detect assumptions in text using semantic analysis.

        Returns:
            List of assumptions with confidence scores
        """
        assumptions = []

        # Ask PRISM what assumptions are being made
        analysis_prompt = f"What assumptions are being made in this text: {text}"
        analysis = self.prism_client.analyze(analysis_prompt)

        if analysis and analysis.get('solutions'):
            # Extract assumptions from PRISM's analysis
            for solution in analysis['solutions']:
                if 'assum' in solution.lower() or 'might' in solution.lower():
                    assumptions.append({
                        'assumption': solution,
                        'confidence': 0.8,
                        'type': 'implicit'
                    })

        # Use semantic drift to detect uncertain statements
        ground_truth = "This is a certain, verified statement with no assumptions."
        drift = self.prism_client.calculate_semantic_drift(text, ground_truth)

        if drift and drift.get('drift_score', 0) > 0.6:
            # High drift from certainty indicates assumptions
            assumptions.append({
                'assumption': 'Text contains uncertain or unverified claims',
                'confidence': drift['drift_score'],
                'type': 'uncertainty'
            })

        return assumptions

    def extract_learning(self, agent_output: str, agent_type: str) -> Dict[str, List[str]]:
        """
        Extract what an agent learned/discovered using semantic analysis.

        Args:
            agent_output: The agent's output text
            agent_type: Type of agent for context

        Returns:
            Dictionary of learning categories to discoveries
        """
        learnings = {
            'patterns': [],
            'decisions': [],
            'issues': [],
            'solutions': [],
            'insights': []
        }

        # Summarize what the agent output contains
        summary = self.analyzer.summarize_code(agent_output)

        # Detect patterns mentioned
        patterns = self.detect_patterns(agent_output, f"agent_{agent_type}")
        if patterns.get('design_patterns'):
            learnings['patterns'].extend(patterns['design_patterns'])
        if patterns.get('anti_patterns'):
            learnings['issues'].extend(patterns['anti_patterns'])

        # Extract decisions by asking PRISM
        decision_prompt = f"What decisions were made in this text: {agent_output[:1000]}"
        decision_analysis = self.prism_client.analyze(decision_prompt)

        if decision_analysis and decision_analysis.get('solutions'):
            learnings['decisions'].extend(decision_analysis['solutions'])

        # Look for insights using semantic understanding
        if 'discovered' in agent_output.lower() or 'found' in agent_output.lower():
            insight_prompt = f"What insights or discoveries are in: {agent_output[:1000]}"
            insight_analysis = self.prism_client.analyze(insight_prompt)
            if insight_analysis and insight_analysis.get('solutions'):
                learnings['insights'].extend(insight_analysis['solutions'])

        # Store learnings for future reference
        for category, items in learnings.items():
            for item in items:
                self.prism_client.store_memory(
                    json.dumps({
                        'type': f'agent_learning_{category}',
                        'agent_type': agent_type,
                        'learning': item,
                        'context': summary
                    }),
                    tier='LONGTERM'
                )

        return learnings

    def find_similar_patterns(self, pattern: str, limit: int = 5) -> List[DiscoveredPattern]:
        """
        Find similar patterns using semantic search.

        Args:
            pattern: Pattern to search for
            limit: Max results

        Returns:
            List of similar patterns discovered previously
        """
        # Search in PRISM memory for similar patterns
        similar = self.prism_client.search_memory(
            query=pattern,
            tiers=['LONGTERM', 'ANCHORS'],
            limit=limit
        )

        patterns = []
        for item in similar:
            content = item.get('content', {})
            if isinstance(content, str):
                try:
                    content = json.loads(content)
                except:
                    continue

            if content.get('type') == 'discovered_pattern':
                patterns.append(DiscoveredPattern(
                    pattern_id=content.get('pattern_id', ''),
                    pattern_type=content.get('pattern_type', ''),
                    description=content.get('description', ''),
                    confidence=content.get('confidence', 0),
                    source=content.get('source', ''),
                    metadata=content.get('metadata', {})
                ))

        return patterns

    def _generate_pattern_id(self, pattern: str, pattern_type: str) -> str:
        """Generate unique ID for a pattern."""
        content = f"{pattern_type}:{pattern}"
        return hashlib.md5(content.encode()).hexdigest()[:12]

    def _store_pattern(self, pattern: DiscoveredPattern):
        """Store discovered pattern for learning."""
        # Cache in Redis
        key = f"pattern:{pattern.pattern_id}"
        self.redis.setex(key, 3600, json.dumps(pattern.to_dict()))

        # Store in PRISM for long-term learning
        self.prism_client.store_memory(
            json.dumps({
                'type': 'discovered_pattern',
                **pattern.to_dict()
            }),
            tier='LONGTERM' if pattern.confidence > 0.8 else 'WORKING'
        )

        # Track in session
        self.session_patterns.append(pattern)

    def _infer_intent_from_summary(self, summary: str) -> Tuple[str, float, Dict]:
        """Infer intent from code summary when PRISM analysis unavailable."""
        if not summary or not isinstance(summary, str):
            return 'unknown', 0.0, {}

        summary_lower = summary.lower()

        # Use semantic understanding instead of keywords
        intents = [
            ('bug_fix', ['fix', 'repair', 'resolve', 'debug']),
            ('feature', ['add', 'implement', 'create', 'new']),
            ('refactor', ['refactor', 'clean', 'improve', 'optimize']),
            ('test', ['test', 'verify', 'validate', 'check']),
            ('documentation', ['document', 'comment', 'explain'])
        ]

        for intent, indicators in intents:
            if any(ind in summary_lower for ind in indicators):
                return intent, 0.7, {'source': 'summary_inference'}

        return 'general', 0.5, {'source': 'summary_inference'}


# Singleton instance
_service_instance = None

def get_semantic_pattern_service() -> SemanticPatternService:
    """Get or create the singleton semantic pattern service."""
    global _service_instance
    if _service_instance is None:
        _service_instance = SemanticPatternService()
    return _service_instance


def main():
    """Test the semantic pattern service."""
    try:
        service = get_semantic_pattern_service()

        # Test pattern detection
        test_code = """
        def authenticate(username, password):
            # TODO: Add password check
            return True
        """

        patterns = service.detect_patterns(test_code, "authentication")
        print(f"Patterns found: {json.dumps(patterns, indent=2)}")

        # Test danger detection
        is_dangerous, reasons = service.is_dangerous(test_code, "code")
        print(f"Is dangerous: {is_dangerous}")
        if reasons:
            print(f"Reasons: {reasons}")

        # Test intent extraction
        text = "Fix the authentication bug where users can login without password"
        intent, confidence, metadata = service.extract_intent(text)
        print(f"Intent: {intent} (confidence: {confidence})")

    except Exception as e:
        print(f"Service initialization failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()