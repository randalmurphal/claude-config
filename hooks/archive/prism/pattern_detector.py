#!/usr/bin/env python3
"""
Pattern Detector for Agent Response Analysis
============================================
Detects and analyzes patterns in agent responses including:
- Recurring issues and problems
- Successful strategies and approaches
- Hallucination patterns and types
- Semantic drift indicators
- Quality trends and improvements

Stores detected patterns in PRISM memory with rich metadata
for historical analysis and learning.
"""

import json
import time
import re
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, asdict
from collections import defaultdict, Counter
import hashlib
import logging

import sys
sys.path.insert(0, str(Path(__file__).parent))

try:
    from response_analyzer import AnalysisResult, ResponseAnalyzer, PrismUnavailableError
    from prism_client import get_prism_client, PrismClient
    PRISM_AVAILABLE = True
except ImportError as e:
    print(f"Warning: PRISM integration not available: {e}", file=sys.stderr)
    PRISM_AVAILABLE = False

# Import semantic analyzer for semantic pattern detection
try:
    from semantic_code_analyzer import get_semantic_analyzer
    SEMANTIC_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Semantic analyzer not available: {e}", file=sys.stderr)
    SEMANTIC_AVAILABLE = False

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class DetectedPattern:
    """Represents a detected pattern in agent responses."""

    pattern_id: str                    # Unique identifier for this pattern
    pattern_type: str                  # Type of pattern (issue, success, hallucination, etc.)
    pattern_name: str                  # Human-readable name
    description: str                   # Detailed description

    # Pattern characteristics
    frequency: int                     # How often this pattern occurs
    confidence: float                  # Confidence in pattern detection (0-1)
    severity: str                      # low, medium, high, critical

    # Context information
    agent_types: List[str]             # Which agent types exhibit this pattern
    response_types: List[str]          # Which response types show this pattern
    quality_impact: float              # Impact on quality score (-1 to 1)

    # Examples and evidence
    example_entries: List[str]         # Example entry IDs showing this pattern
    prism_evidence: Dict[str, Any]     # PRISM analysis supporting this pattern

    # Metadata
    first_detected: float              # When first detected
    last_detected: float               # When last seen
    detection_count: int               # Total detection count

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DetectedPattern':
        """Create from dictionary."""
        return cls(**data)


class PatternDetectionEngine:
    """Detects patterns in agent responses and analysis results."""

    def __init__(self, prism_client: Optional[PrismClient] = None):
        """Initialize pattern detection engine.

        Args:
            prism_client: Optional PRISM client for storage
        """
        self.prism_client = prism_client or (get_prism_client() if PRISM_AVAILABLE else None)
        self.detected_patterns: Dict[str, DetectedPattern] = {}
        self.analysis_history: List[AnalysisResult] = []

        # Initialize semantic analyzer if available - NO FALLBACK
        self.semantic_analyzer = None
        if SEMANTIC_AVAILABLE:
            try:
                self.semantic_analyzer = get_semantic_analyzer()
                logger.info("Semantic pattern detection enabled")
            except Exception as e:
                logger.error(f"Failed to initialize semantic analyzer: {e}")
                # Don't fallback - we want semantic or nothing
                raise RuntimeError(f"Semantic analyzer required but unavailable: {e}")

        # Pattern detection rules (enhanced with semantic patterns)
        self.pattern_rules = self._initialize_pattern_rules()

    def _initialize_pattern_rules(self) -> Dict[str, Dict]:
        """Initialize pattern detection rules."""
        return {
            # Issue patterns (enhanced with semantic understanding)
            "recurring_errors": {
                "type": "issue",
                "keywords": ["error", "failed", "exception", "crash", "bug"],  # Fallback keywords
                "semantic_patterns": [
                    {"type": "logic_issue", "name": "exception handling"},
                    {"type": "anti_pattern", "name": "error swallowing"},
                    {"type": "vulnerability", "name": "unhandled exception"}
                ],
                "min_frequency": 3,
                "severity": "high"
            },
            "import_failures": {
                "type": "issue",
                "keywords": ["import error", "module not found", "cannot import"],  # Fallback
                "semantic_patterns": [
                    {"type": "logic_issue", "name": "missing dependency"},
                    {"type": "anti_pattern", "name": "circular import"},
                    {"type": "logic_issue", "name": "incorrect import path"}
                ],
                "min_frequency": 2,
                "severity": "medium"
            },
            "syntax_errors": {
                "type": "issue",
                "keywords": ["syntax error", "invalid syntax", "unexpected token"],  # Fallback
                "semantic_patterns": [
                    {"type": "logic_issue", "name": "malformed syntax"},
                    {"type": "logic_issue", "name": "type mismatch"},
                    {"type": "anti_pattern", "name": "ambiguous syntax"}
                ],
                "min_frequency": 2,
                "severity": "medium"
            },

            # Success patterns
            "clean_implementation": {
                "type": "success",
                "indicators": ["quality_score > 0.8", "confidence > 0.85", "no_hallucination"],
                "semantic_patterns": [
                    {"type": "design_pattern", "name": "single responsibility"},
                    {"type": "design_pattern", "name": "dependency injection"},
                    {"type": "design_pattern", "name": "clean code principles"}
                ],
                "min_frequency": 3,
                "severity": "low"
            },
            "comprehensive_testing": {
                "type": "success",
                "keywords": ["test", "coverage", "assertion", "validate"],  # Fallback
                "indicators": ["quality_score > 0.7"],
                "semantic_patterns": [
                    {"type": "design_pattern", "name": "test-driven development"},
                    {"type": "design_pattern", "name": "unit testing"},
                    {"type": "design_pattern", "name": "test coverage"}
                ],
                "min_frequency": 2,
                "severity": "low"
            },
            "efficient_solutions": {
                "type": "success",
                "indicators": ["analysis_duration < 2.0", "quality_score > 0.75"],
                "min_frequency": 3,
                "severity": "low"
            },

            # Hallucination patterns
            "factual_hallucination": {
                "type": "hallucination",
                "indicators": ["hallucination_risk.risk_type == 'factual'", "hallucination_risk.risk_score > 0.6"],
                "min_frequency": 2,
                "severity": "high"
            },
            "code_hallucination": {
                "type": "hallucination",
                "indicators": ["hallucination_risk.risk_type == 'code'", "hallucination_risk.risk_score > 0.5"],
                "min_frequency": 2,
                "severity": "critical"
            },
            "api_hallucination": {
                "type": "hallucination",
                "keywords": ["nonexistent function", "invalid method", "not found"],  # Fallback
                "indicators": ["hallucination_risk.risk_score > 0.4"],
                "semantic_patterns": [
                    {"type": "logic_issue", "name": "undefined method"},
                    {"type": "logic_issue", "name": "api mismatch"},
                    {"type": "vulnerability", "name": "invalid API usage"}
                ],
                "min_frequency": 2,
                "severity": "high"
            },

            # Drift patterns
            "semantic_drift": {
                "type": "drift",
                "indicators": ["semantic_drift.drift_score > 0.5"],
                "min_frequency": 2,
                "severity": "medium"
            },
            "requirement_drift": {
                "type": "drift",
                "keywords": ["requirement", "specification", "expected"],
                "indicators": ["semantic_drift.drift_score > 0.3"],
                "min_frequency": 3,
                "severity": "high"
            },

            # Quality patterns
            "declining_quality": {
                "type": "quality_trend",
                "indicators": ["quality_decline_trend"],
                "min_frequency": 4,
                "severity": "medium"
            },
            "improving_quality": {
                "type": "quality_trend",
                "indicators": ["quality_improvement_trend"],
                "min_frequency": 3,
                "severity": "low"
            }
        }

    def analyze_response_for_patterns(self, analysis_result: AnalysisResult) -> List[DetectedPattern]:
        """Analyze a single response for patterns.

        Args:
            analysis_result: Result from response analyzer

        Returns:
            List of detected patterns
        """
        detected = []

        # Add to history for trend analysis
        self.analysis_history.append(analysis_result)

        # Keep only recent history (last 100 entries)
        if len(self.analysis_history) > 100:
            self.analysis_history = self.analysis_history[-100:]

        # Check each pattern rule
        for pattern_name, rule in self.pattern_rules.items():
            if self._matches_pattern_rule(analysis_result, rule):
                pattern = self._create_or_update_pattern(pattern_name, rule, analysis_result)
                if pattern:
                    detected.append(pattern)

        # Check for trend patterns
        trend_patterns = self._detect_trend_patterns()
        detected.extend(trend_patterns)

        return detected

    def _matches_pattern_rule(self, result: AnalysisResult, rule: Dict) -> bool:
        """Check if analysis result matches a pattern rule using semantic analysis."""

        content = getattr(result, 'content', '')
        if not content:
            return False

        # Use semantic analysis if available (NO FALLBACK)
        if self.semantic_analyzer and rule.get("semantic_patterns"):
            try:
                # Detect semantic patterns in the content
                detected_patterns = self.semantic_analyzer.detect_code_patterns(content)
                semantic_patterns = rule.get("semantic_patterns", [])

                # Check if any required semantic patterns are present
                for required_pattern in semantic_patterns:
                    pattern_type = required_pattern.get("type", "")
                    pattern_name = required_pattern.get("name", "")

                    if pattern_type == "anti_pattern":
                        anti_patterns = detected_patterns.get("anti_patterns", [])
                        # Check semantic understanding of anti-patterns
                        for anti_pattern in anti_patterns:
                            # Use semantic similarity instead of exact match
                            if self._semantically_similar(pattern_name, anti_pattern):
                                logger.debug(f"Semantic anti-pattern match: {pattern_name} ~ {anti_pattern}")
                                return True

                    elif pattern_type == "design_pattern":
                        design_patterns = detected_patterns.get("design_patterns", [])
                        for design_pattern in design_patterns:
                            if self._semantically_similar(pattern_name, design_pattern):
                                logger.debug(f"Semantic design pattern match: {pattern_name} ~ {design_pattern}")
                                return True

                    elif pattern_type == "vulnerability":
                        # Use semantic analyzer to detect security vulnerabilities
                        analysis = self.semantic_analyzer.analyze_code_logic(content)
                        vulnerabilities = analysis.get("security", {}).get("vulnerabilities", [])
                        if any(pattern_name.lower() in vuln.lower() for vuln in vulnerabilities):
                            logger.debug(f"Semantic vulnerability detected: {pattern_name}")
                            return True

                    elif pattern_type == "logic_issue":
                        # Detect logical issues semantically
                        analysis = self.semantic_analyzer.analyze_code_logic(content)
                        if analysis.get("logic", {}).get("has_issues"):
                            logical_issues = analysis["logic"].get("logical_issues", [])
                            if any(pattern_name.lower() in issue.lower() for issue in logical_issues):
                                logger.debug(f"Semantic logic issue detected: {pattern_name}")
                                return True

            except Exception as e:
                # NO FALLBACK - if semantic analysis fails, we fail
                logger.error(f"Semantic pattern detection failed: {e}")
                raise RuntimeError(f"Semantic analysis required but failed: {e}")

        # Fall back to keyword matching ONLY if no semantic patterns defined
        # This maintains backward compatibility for rules without semantic patterns
        keywords = rule.get("keywords", [])
        if keywords and not rule.get("semantic_patterns"):
            content_lower = content.lower()
            if not any(keyword.lower() in content_lower for keyword in keywords):
                return False

        # Check indicator conditions
        indicators = rule.get("indicators", [])
        for indicator in indicators:
            if not self._evaluate_indicator(result, indicator):
                return False

        return True

    def _semantically_similar(self, pattern1: str, pattern2: str) -> bool:
        """Check if two patterns are semantically similar.

        Uses CodeT5+ to understand if patterns mean the same thing,
        even if worded differently.
        """
        if not self.semantic_analyzer:
            return pattern1.lower() == pattern2.lower()

        try:
            # Use semantic comparison to check similarity
            comparison = self.semantic_analyzer.compare_implementations(
                pattern1, pattern2, context="pattern_matching"
            )

            # Check semantic drift score (lower is more similar)
            drift_score = comparison.get("semantic_drift", {}).get("drift_score", 1.0)
            return drift_score < 0.3  # Similar if drift is low

        except Exception as e:
            logger.warning(f"Semantic similarity check failed: {e}")
            # NO FALLBACK - we require semantic understanding
            raise RuntimeError(f"Semantic similarity check failed: {e}")

    def _evaluate_indicator(self, result: AnalysisResult, indicator: str) -> bool:
        """Evaluate an indicator condition against analysis result."""
        try:
            # Handle special indicators
            if indicator == "no_hallucination":
                if result.hallucination_risk:
                    return result.hallucination_risk.get('risk_score', 0) < 0.3
                return True

            if indicator == "quality_decline_trend":
                return self._detect_quality_decline()

            if indicator == "quality_improvement_trend":
                return self._detect_quality_improvement()

            # Handle simple comparisons
            if ">" in indicator:
                field, threshold = indicator.split(" > ")
                value = self._get_nested_value(result, field.strip())
                return value is not None and float(value) > float(threshold)

            if "<" in indicator:
                field, threshold = indicator.split(" < ")
                value = self._get_nested_value(result, field.strip())
                return value is not None and float(value) < float(threshold)

            if "==" in indicator:
                field, expected = indicator.split(" == ")
                value = self._get_nested_value(result, field.strip())
                expected = expected.strip().strip("'\"")
                return str(value) == expected

            return False
        except:
            return False

    def _get_nested_value(self, obj: Any, path: str) -> Any:
        """Get nested value from object using dot notation."""
        parts = path.split('.')
        current = obj

        for part in parts:
            if hasattr(current, part):
                current = getattr(current, part)
            elif isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return None

        return current

    def _detect_quality_decline(self) -> bool:
        """Detect declining quality trend."""
        if len(self.analysis_history) < 5:
            return False

        recent_scores = [r.quality_score for r in self.analysis_history[-5:]]

        # Check if there's a declining trend
        declines = 0
        for i in range(1, len(recent_scores)):
            if recent_scores[i] < recent_scores[i-1]:
                declines += 1

        return declines >= 3  # At least 3 out of 4 comparisons show decline

    def _detect_quality_improvement(self) -> bool:
        """Detect improving quality trend."""
        if len(self.analysis_history) < 5:
            return False

        recent_scores = [r.quality_score for r in self.analysis_history[-5:]]

        # Check if there's an improving trend
        improvements = 0
        for i in range(1, len(recent_scores)):
            if recent_scores[i] > recent_scores[i-1]:
                improvements += 1

        return improvements >= 3  # At least 3 out of 4 comparisons show improvement

    def _detect_trend_patterns(self) -> List[DetectedPattern]:
        """Detect trend-based patterns."""
        patterns = []

        if len(self.analysis_history) < 10:
            return patterns

        # Analyze agent type performance trends
        agent_performance = defaultdict(list)
        for result in self.analysis_history[-20:]:  # Last 20 entries
            agent_performance[result.agent_type].append(result.quality_score)

        for agent_type, scores in agent_performance.items():
            if len(scores) >= 5:
                avg_score = sum(scores) / len(scores)
                if avg_score < 0.6:
                    pattern = self._create_trend_pattern(
                        f"low_performance_{agent_type}",
                        "quality_issue",
                        f"Agent type {agent_type} shows consistently low performance",
                        {"average_score": avg_score, "agent_type": agent_type}
                    )
                    if pattern:
                        patterns.append(pattern)

        return patterns

    def _create_or_update_pattern(self, pattern_name: str, rule: Dict,
                                 result: AnalysisResult) -> Optional[DetectedPattern]:
        """Create new pattern or update existing one."""
        pattern_id = self._generate_pattern_id(pattern_name, rule, result)

        current_time = time.time()

        if pattern_id in self.detected_patterns:
            # Update existing pattern
            pattern = self.detected_patterns[pattern_id]
            pattern.frequency += 1
            pattern.detection_count += 1
            pattern.last_detected = current_time

            # Add example if not already included
            if result.entry_id not in pattern.example_entries:
                pattern.example_entries.append(result.entry_id)
                # Keep only recent examples
                if len(pattern.example_entries) > 10:
                    pattern.example_entries = pattern.example_entries[-10:]

            # Update agent types and response types
            if result.agent_type not in pattern.agent_types:
                pattern.agent_types.append(result.agent_type)
            if result.response_type not in pattern.response_types:
                pattern.response_types.append(result.response_type)

        else:
            # Create new pattern
            pattern = DetectedPattern(
                pattern_id=pattern_id,
                pattern_type=rule["type"],
                pattern_name=pattern_name,
                description=self._generate_pattern_description(pattern_name, rule, result),
                frequency=1,
                confidence=self._calculate_pattern_confidence(rule, result),
                severity=rule.get("severity", "medium"),
                agent_types=[result.agent_type],
                response_types=[result.response_type],
                quality_impact=self._calculate_quality_impact(rule, result),
                example_entries=[result.entry_id],
                prism_evidence=self._extract_prism_evidence(result),
                first_detected=current_time,
                last_detected=current_time,
                detection_count=1
            )

            self.detected_patterns[pattern_id] = pattern

        # Only return patterns that meet minimum frequency
        min_freq = rule.get("min_frequency", 1)
        if self.detected_patterns[pattern_id].frequency >= min_freq:
            return self.detected_patterns[pattern_id]

        return None

    def _create_trend_pattern(self, pattern_name: str, pattern_type: str,
                             description: str, evidence: Dict) -> DetectedPattern:
        """Create a trend-based pattern."""
        pattern_id = hashlib.md5(f"{pattern_name}_{pattern_type}".encode()).hexdigest()[:16]

        return DetectedPattern(
            pattern_id=pattern_id,
            pattern_type=pattern_type,
            pattern_name=pattern_name,
            description=description,
            frequency=1,
            confidence=0.7,
            severity="medium",
            agent_types=[evidence.get("agent_type", "multiple")],
            response_types=["trend_analysis"],
            quality_impact=evidence.get("quality_impact", 0.0),
            example_entries=[],
            prism_evidence=evidence,
            first_detected=time.time(),
            last_detected=time.time(),
            detection_count=1
        )

    def _generate_pattern_id(self, pattern_name: str, rule: Dict, result: AnalysisResult) -> str:
        """Generate unique pattern ID."""
        # Include agent type for agent-specific patterns
        key = f"{pattern_name}_{rule['type']}_{result.agent_type}"
        return hashlib.md5(key.encode()).hexdigest()[:16]

    def _generate_pattern_description(self, pattern_name: str, rule: Dict,
                                    result: AnalysisResult) -> str:
        """Generate human-readable pattern description."""
        descriptions = {
            "recurring_errors": f"Recurring errors in {result.agent_type} agent responses",
            "clean_implementation": f"High-quality implementation patterns in {result.agent_type}",
            "factual_hallucination": f"Factual hallucination patterns detected in {result.agent_type}",
            "semantic_drift": f"Semantic drift from requirements in {result.agent_type}",
            "declining_quality": "Quality decline trend detected across responses"
        }

        return descriptions.get(pattern_name, f"Pattern: {pattern_name} in {result.agent_type}")

    def _calculate_pattern_confidence(self, rule: Dict, result: AnalysisResult) -> float:
        """Calculate confidence in pattern detection."""
        base_confidence = 0.6

        # Boost confidence based on evidence strength
        if result.hallucination_risk and result.hallucination_risk.get('risk_score', 0) > 0.8:
            base_confidence += 0.2

        if result.quality_score < 0.4:
            base_confidence += 0.15

        if result.confidence > 0.8:
            base_confidence += 0.1

        return min(base_confidence, 1.0)

    def _calculate_quality_impact(self, rule: Dict, result: AnalysisResult) -> float:
        """Calculate impact on quality score."""
        if rule["type"] == "issue":
            return -0.3  # Issues negatively impact quality
        elif rule["type"] == "success":
            return 0.2   # Successes positively impact quality
        elif rule["type"] == "hallucination":
            return -0.5  # Hallucinations severely impact quality
        elif rule["type"] == "drift":
            return -0.2  # Drift moderately impacts quality
        else:
            return 0.0

    def _extract_prism_evidence(self, result: AnalysisResult) -> Dict[str, Any]:
        """Extract PRISM evidence supporting the pattern."""
        evidence = {}

        if result.prism_analysis:
            analysis = result.prism_analysis.get('analysis', {})
            evidence['prism_confidence'] = analysis.get('confidence', 0)
            evidence['prism_zone'] = analysis.get('reasoning', {}).get('zone', 'unknown')
            evidence['prism_method'] = analysis.get('reasoning', {}).get('method', 'unknown')

        if result.hallucination_risk:
            evidence['hallucination_score'] = result.hallucination_risk.get('risk_score', 0)
            evidence['hallucination_type'] = result.hallucination_risk.get('risk_type', 'unknown')

        if result.semantic_drift:
            evidence['drift_score'] = result.semantic_drift.get('drift_score', 0)

        evidence['quality_score'] = result.quality_score
        evidence['analysis_confidence'] = result.confidence

        return evidence

    def store_patterns_in_prism(self, patterns: List[DetectedPattern]) -> Dict[str, bool]:
        """Store detected patterns in PRISM memory.

        Args:
            patterns: List of patterns to store

        Returns:
            Dictionary mapping pattern IDs to storage success
        """
        results = {}

        if not self.prism_client:
            print("PRISM client not available for pattern storage", file=sys.stderr)
            return results

        for pattern in patterns:
            try:
                # Create pattern content for PRISM
                pattern_content = {
                    "type": "detected_pattern",
                    "pattern_id": pattern.pattern_id,
                    "pattern_name": pattern.pattern_name,
                    "pattern_type": pattern.pattern_type,
                    "description": pattern.description,
                    "frequency": pattern.frequency,
                    "confidence": pattern.confidence,
                    "severity": pattern.severity,
                    "agent_types": pattern.agent_types,
                    "response_types": pattern.response_types,
                    "quality_impact": pattern.quality_impact,
                    "evidence": pattern.prism_evidence,
                    "detection_metadata": {
                        "first_detected": pattern.first_detected,
                        "last_detected": pattern.last_detected,
                        "detection_count": pattern.detection_count
                    }
                }

                # Determine storage tier based on pattern severity and type
                tier = "WORKING"
                if pattern.severity in ["high", "critical"]:
                    tier = "LONGTERM"
                elif pattern.pattern_type in ["success", "quality_trend"]:
                    tier = "LONGTERM"

                # Store in PRISM
                success = self.prism_client.store_memory(
                    content=json.dumps(pattern_content),
                    tier=tier,
                    metadata={
                        "type": "pattern",
                        "pattern_type": pattern.pattern_type,
                        "severity": pattern.severity,
                        "frequency": str(pattern.frequency),
                        "confidence": f"{pattern.confidence:.2f}",
                        "agent_types": pattern.agent_types[:3],  # Limit for metadata
                        "timestamp": str(pattern.last_detected)
                    }
                )

                results[pattern.pattern_id] = success

                if success:
                    print(f"Stored pattern '{pattern.pattern_name}' in PRISM ({tier})", file=sys.stderr)
                else:
                    print(f"Failed to store pattern '{pattern.pattern_name}' in PRISM", file=sys.stderr)

            except Exception as e:
                print(f"Error storing pattern {pattern.pattern_id}: {e}", file=sys.stderr)
                results[pattern.pattern_id] = False

        return results

    def search_historical_patterns(self, pattern_type: Optional[str] = None,
                                 agent_type: Optional[str] = None,
                                 limit: int = 20) -> List[Dict]:
        """Search for historical patterns in PRISM.

        Args:
            pattern_type: Filter by pattern type
            agent_type: Filter by agent type
            limit: Maximum results

        Returns:
            List of historical pattern data
        """
        if not self.prism_client:
            return []

        # Build search query
        query_parts = ["detected_pattern"]
        if pattern_type:
            query_parts.append(pattern_type)
        if agent_type:
            query_parts.append(agent_type)

        query = " ".join(query_parts)

        try:
            results = self.prism_client.search_memory(query, limit=limit)
            return results if results else []
        except Exception as e:
            print(f"Error searching historical patterns: {e}", file=sys.stderr)
            return []

    def get_pattern_statistics(self) -> Dict[str, Any]:
        """Get statistics about detected patterns."""
        if not self.detected_patterns:
            return {"total_patterns": 0}

        patterns = list(self.detected_patterns.values())

        stats = {
            "total_patterns": len(patterns),
            "by_type": Counter(p.pattern_type for p in patterns),
            "by_severity": Counter(p.severity for p in patterns),
            "by_agent_type": Counter(agent for p in patterns for agent in p.agent_types),
            "average_frequency": sum(p.frequency for p in patterns) / len(patterns),
            "high_confidence_patterns": len([p for p in patterns if p.confidence > 0.8]),
            "recent_patterns": len([p for p in patterns if (time.time() - p.last_detected) < 3600])
        }

        return stats


# Export key classes
__all__ = ['PatternDetectionEngine', 'DetectedPattern']