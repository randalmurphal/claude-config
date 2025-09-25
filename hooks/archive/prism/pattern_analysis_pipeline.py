#!/usr/bin/env python3
"""
Pattern Analysis Pipeline
=========================
Integrates pattern detection with response analysis to provide
comprehensive agent response analysis and learning.

This pipeline:
- Analyzes agent responses for quality and content
- Detects patterns across multiple responses
- Stores patterns and analysis in PRISM
- Provides pattern-based insights and recommendations
- Feeds learning back into the system for improvement
"""

import json
import time
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict, deque
from dataclasses import dataclass

# Import our components
sys.path.insert(0, str(Path(__file__).parent))

try:
    from response_analyzer import ResponseAnalyzer, AnalysisResult, PrismUnavailableError
    from pattern_detector import PatternDetectionEngine, DetectedPattern
    from checkpoint_system import TranscriptEntry, CheckpointManager, TranscriptProcessor
    from prism_client import get_prism_client, PrismClient
    COMPONENTS_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Pipeline components not available: {e}", file=sys.stderr)
    COMPONENTS_AVAILABLE = False


@dataclass
class PatternInsight:
    """Insight derived from pattern analysis."""

    insight_type: str                  # recommendation, warning, optimization
    title: str                         # Brief insight title
    description: str                   # Detailed description
    confidence: float                  # Confidence in insight (0-1)
    priority: str                      # low, medium, high, critical
    related_patterns: List[str]        # Pattern IDs that support this insight
    actionable_steps: List[str]        # Recommended actions
    impact_estimate: str               # Expected impact if acted upon


class PatternAnalysisPipeline:
    """Complete pipeline for pattern-based response analysis."""

    def __init__(self, checkpoint_manager: Optional[CheckpointManager] = None):
        """Initialize the pattern analysis pipeline.

        Args:
            checkpoint_manager: Optional checkpoint manager

        Raises:
            PrismUnavailableError: If PRISM is unavailable and required
        """
        if not COMPONENTS_AVAILABLE:
            raise ImportError("Pipeline components not available")

        # Initialize components
        self.prism_client = get_prism_client()
        if not self.prism_client.is_available():
            raise PrismUnavailableError("PRISM MCP required for pattern analysis pipeline")

        self.response_analyzer = ResponseAnalyzer(checkpoint_manager)
        self.pattern_detector = PatternDetectionEngine(self.prism_client)
        self.checkpoint_manager = checkpoint_manager or CheckpointManager()

        # Analysis history and metrics
        self.analysis_history: deque = deque(maxlen=1000)  # Keep last 1000 analyses
        self.pattern_history: deque = deque(maxlen=500)    # Keep last 500 patterns
        self.session_stats = self._initialize_session_stats()

        print("Pattern Analysis Pipeline initialized - PRISM integration active", file=sys.stderr)

    def _initialize_session_stats(self) -> Dict[str, Any]:
        """Initialize session statistics tracking."""
        return {
            "session_start": time.time(),
            "total_analyzed": 0,
            "patterns_detected": 0,
            "insights_generated": 0,
            "quality_scores": [],
            "agent_performance": defaultdict(list),
            "pattern_types": defaultdict(int)
        }

    def analyze_response_with_patterns(self, entry: TranscriptEntry,
                                     ground_truth: Optional[str] = None) -> Tuple[AnalysisResult, List[DetectedPattern]]:
        """Analyze response and detect patterns.

        Args:
            entry: Transcript entry to analyze
            ground_truth: Optional ground truth for semantic drift

        Returns:
            Tuple of (analysis result, detected patterns)
        """
        # Perform response analysis
        analysis_result = self.response_analyzer.analyze_response(entry, ground_truth)

        # Detect patterns in the analysis
        detected_patterns = self.pattern_detector.analyze_response_for_patterns(analysis_result)

        # Update session statistics
        self._update_session_stats(analysis_result, detected_patterns)

        # Store in history
        self.analysis_history.append(analysis_result)
        self.pattern_history.extend(detected_patterns)

        # Store analysis and patterns in PRISM
        self._store_analysis_and_patterns(analysis_result, detected_patterns)

        return analysis_result, detected_patterns

    def analyze_multiple_responses(self, entries: List[TranscriptEntry],
                                 ground_truths: Optional[List[str]] = None) -> Dict[str, Any]:
        """Analyze multiple responses and detect cross-response patterns.

        Args:
            entries: List of transcript entries
            ground_truths: Optional ground truths for semantic drift

        Returns:
            Comprehensive analysis results
        """
        results = {
            "individual_analyses": [],
            "detected_patterns": [],
            "cross_response_patterns": [],
            "session_insights": [],
            "summary_statistics": {}
        }

        # Analyze each response individually
        for i, entry in enumerate(entries):
            ground_truth = ground_truths[i] if ground_truths and i < len(ground_truths) else None

            try:
                analysis, patterns = self.analyze_response_with_patterns(entry, ground_truth)

                results["individual_analyses"].append({
                    "entry_id": analysis.entry_id,
                    "quality_score": analysis.quality_score,
                    "response_type": analysis.response_type,
                    "patterns": [p.pattern_name for p in patterns]
                })

                results["detected_patterns"].extend(patterns)

            except Exception as e:
                print(f"Error analyzing entry {entry.entry_id}: {e}", file=sys.stderr)

        # Analyze cross-response patterns
        if len(self.analysis_history) >= 5:
            cross_patterns = self._detect_cross_response_patterns()
            results["cross_response_patterns"] = cross_patterns

        # Generate insights
        insights = self.generate_insights()
        results["session_insights"] = insights

        # Calculate summary statistics
        results["summary_statistics"] = self._calculate_summary_statistics()

        return results

    def _detect_cross_response_patterns(self) -> List[DetectedPattern]:
        """Detect patterns across multiple responses."""
        cross_patterns = []

        # Analyze quality trends
        recent_analyses = list(self.analysis_history)[-20:]
        if len(recent_analyses) >= 10:
            quality_trend = self._analyze_quality_trend(recent_analyses)
            if quality_trend:
                cross_patterns.append(quality_trend)

        # Analyze agent type performance patterns
        agent_patterns = self._analyze_agent_performance_patterns(recent_analyses)
        cross_patterns.extend(agent_patterns)

        # Analyze hallucination clustering
        hallucination_patterns = self._analyze_hallucination_clustering(recent_analyses)
        cross_patterns.extend(hallucination_patterns)

        return cross_patterns

    def _analyze_quality_trend(self, analyses: List[AnalysisResult]) -> Optional[DetectedPattern]:
        """Analyze quality trends across responses."""
        if len(analyses) < 10:
            return None

        scores = [a.quality_score for a in analyses]

        # Calculate trend slope
        x_vals = list(range(len(scores)))
        n = len(scores)
        sum_x = sum(x_vals)
        sum_y = sum(scores)
        sum_xy = sum(x * y for x, y in zip(x_vals, scores))
        sum_x2 = sum(x * x for x in x_vals)

        # Linear regression slope
        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)

        # Determine trend significance
        if abs(slope) > 0.01:  # Significant trend
            trend_type = "improving" if slope > 0 else "declining"
            severity = "high" if abs(slope) > 0.05 else "medium"

            return DetectedPattern(
                pattern_id=f"quality_trend_{trend_type}_{int(time.time())}",
                pattern_type="quality_trend",
                pattern_name=f"{trend_type}_quality_trend",
                description=f"Quality scores show {trend_type} trend over recent responses",
                frequency=len(analyses),
                confidence=min(abs(slope) * 10, 1.0),
                severity=severity,
                agent_types=list(set(a.agent_type for a in analyses)),
                response_types=list(set(a.response_type for a in analyses)),
                quality_impact=slope * 5,  # Scale impact
                example_entries=[a.entry_id for a in analyses[-3:]],
                prism_evidence={
                    "trend_slope": slope,
                    "score_range": [min(scores), max(scores)],
                    "sample_size": len(analyses)
                },
                first_detected=time.time(),
                last_detected=time.time(),
                detection_count=1
            )

        return None

    def _analyze_agent_performance_patterns(self, analyses: List[AnalysisResult]) -> List[DetectedPattern]:
        """Analyze agent-specific performance patterns."""
        patterns = []

        # Group by agent type
        agent_performance = defaultdict(list)
        for analysis in analyses:
            agent_performance[analysis.agent_type].append(analysis.quality_score)

        for agent_type, scores in agent_performance.items():
            if len(scores) >= 5:  # Minimum samples for pattern
                avg_score = sum(scores) / len(scores)
                score_variance = sum((s - avg_score) ** 2 for s in scores) / len(scores)

                # Detect low performance pattern
                if avg_score < 0.6:
                    patterns.append(DetectedPattern(
                        pattern_id=f"low_performance_{agent_type}_{int(time.time())}",
                        pattern_type="performance_issue",
                        pattern_name=f"low_performance_{agent_type}",
                        description=f"Agent type {agent_type} shows consistently low performance",
                        frequency=len(scores),
                        confidence=0.8,
                        severity="high" if avg_score < 0.4 else "medium",
                        agent_types=[agent_type],
                        response_types=["multiple"],
                        quality_impact=-0.4,
                        example_entries=[],
                        prism_evidence={
                            "average_score": avg_score,
                            "score_variance": score_variance,
                            "sample_count": len(scores)
                        },
                        first_detected=time.time(),
                        last_detected=time.time(),
                        detection_count=1
                    ))

                # Detect high variance pattern
                if score_variance > 0.1:
                    patterns.append(DetectedPattern(
                        pattern_id=f"inconsistent_performance_{agent_type}_{int(time.time())}",
                        pattern_type="consistency_issue",
                        pattern_name=f"inconsistent_performance_{agent_type}",
                        description=f"Agent type {agent_type} shows inconsistent performance",
                        frequency=len(scores),
                        confidence=0.7,
                        severity="medium",
                        agent_types=[agent_type],
                        response_types=["multiple"],
                        quality_impact=-0.2,
                        example_entries=[],
                        prism_evidence={
                            "score_variance": score_variance,
                            "score_range": [min(scores), max(scores)]
                        },
                        first_detected=time.time(),
                        last_detected=time.time(),
                        detection_count=1
                    ))

        return patterns

    def _analyze_hallucination_clustering(self, analyses: List[AnalysisResult]) -> List[DetectedPattern]:
        """Analyze hallucination clustering patterns."""
        patterns = []

        # Find analyses with hallucination risk
        hallucination_analyses = [
            a for a in analyses
            if a.hallucination_risk and a.hallucination_risk.get('risk_score', 0) > 0.5
        ]

        if len(hallucination_analyses) >= 3:
            # Check for clustering by agent type
            agent_hallucinations = defaultdict(list)
            for analysis in hallucination_analyses:
                agent_hallucinations[analysis.agent_type].append(analysis)

            for agent_type, agent_analyses in agent_hallucinations.items():
                if len(agent_analyses) >= 2:
                    avg_risk = sum(
                        a.hallucination_risk.get('risk_score', 0)
                        for a in agent_analyses
                    ) / len(agent_analyses)

                    patterns.append(DetectedPattern(
                        pattern_id=f"hallucination_cluster_{agent_type}_{int(time.time())}",
                        pattern_type="hallucination_cluster",
                        pattern_name=f"hallucination_cluster_{agent_type}",
                        description=f"Clustering of hallucination risk in {agent_type} responses",
                        frequency=len(agent_analyses),
                        confidence=0.8,
                        severity="critical" if avg_risk > 0.8 else "high",
                        agent_types=[agent_type],
                        response_types=["multiple"],
                        quality_impact=-0.6,
                        example_entries=[a.entry_id for a in agent_analyses],
                        prism_evidence={
                            "average_risk_score": avg_risk,
                            "cluster_size": len(agent_analyses),
                            "risk_types": [
                                a.hallucination_risk.get('risk_type', 'unknown')
                                for a in agent_analyses
                            ]
                        },
                        first_detected=time.time(),
                        last_detected=time.time(),
                        detection_count=1
                    ))

        return patterns

    def generate_insights(self) -> List[PatternInsight]:
        """Generate actionable insights from detected patterns."""
        insights = []

        # Get recent patterns
        recent_patterns = list(self.pattern_history)[-50:]  # Last 50 patterns

        # Group patterns by type
        pattern_groups = defaultdict(list)
        for pattern in recent_patterns:
            pattern_groups[pattern.pattern_type].append(pattern)

        # Generate insights for each pattern type
        for pattern_type, patterns in pattern_groups.items():
            if pattern_type == "issue":
                insights.extend(self._generate_issue_insights(patterns))
            elif pattern_type == "hallucination":
                insights.extend(self._generate_hallucination_insights(patterns))
            elif pattern_type == "quality_trend":
                insights.extend(self._generate_quality_insights(patterns))
            elif pattern_type == "success":
                insights.extend(self._generate_success_insights(patterns))

        return insights

    def _generate_issue_insights(self, patterns: List[DetectedPattern]) -> List[PatternInsight]:
        """Generate insights for issue patterns."""
        insights = []

        # Find most frequent issues
        issue_freq = defaultdict(int)
        for pattern in patterns:
            issue_freq[pattern.pattern_name] += pattern.frequency

        for issue_name, total_freq in issue_freq.items():
            if total_freq >= 3:
                insights.append(PatternInsight(
                    insight_type="warning",
                    title=f"Recurring Issue: {issue_name}",
                    description=f"The issue '{issue_name}' has occurred {total_freq} times recently",
                    confidence=0.8,
                    priority="high" if total_freq >= 5 else "medium",
                    related_patterns=[p.pattern_id for p in patterns if p.pattern_name == issue_name],
                    actionable_steps=[
                        f"Review and fix root cause of {issue_name}",
                        "Consider adding validation to prevent recurrence",
                        "Update documentation if needed"
                    ],
                    impact_estimate="Medium to High - Resolving this could improve quality by 10-20%"
                ))

        return insights

    def _generate_hallucination_insights(self, patterns: List[DetectedPattern]) -> List[PatternInsight]:
        """Generate insights for hallucination patterns."""
        insights = []

        hallucination_count = sum(p.frequency for p in patterns)
        if hallucination_count >= 2:
            insights.append(PatternInsight(
                insight_type="warning",
                title="Hallucination Risk Detected",
                description=f"Found {hallucination_count} instances of potential hallucination",
                confidence=0.9,
                priority="critical",
                related_patterns=[p.pattern_id for p in patterns],
                actionable_steps=[
                    "Review model configuration and parameters",
                    "Implement stronger validation checks",
                    "Consider using retrieval-augmented generation",
                    "Add fact-checking mechanisms"
                ],
                impact_estimate="High - Addressing hallucinations could improve reliability by 25-40%"
            ))

        return insights

    def _generate_quality_insights(self, patterns: List[DetectedPattern]) -> List[PatternInsight]:
        """Generate insights for quality trend patterns."""
        insights = []

        for pattern in patterns:
            if "declining" in pattern.pattern_name:
                insights.append(PatternInsight(
                    insight_type="warning",
                    title="Quality Decline Detected",
                    description="Recent responses show declining quality scores",
                    confidence=pattern.confidence,
                    priority="high",
                    related_patterns=[pattern.pattern_id],
                    actionable_steps=[
                        "Review recent changes to prompts or configuration",
                        "Check for environmental factors affecting performance",
                        "Consider retraining or parameter adjustment"
                    ],
                    impact_estimate="High - Stopping quality decline could prevent 15-30% performance loss"
                ))
            elif "improving" in pattern.pattern_name:
                insights.append(PatternInsight(
                    insight_type="optimization",
                    title="Quality Improvement Trend",
                    description="Recent responses show improving quality scores",
                    confidence=pattern.confidence,
                    priority="low",
                    related_patterns=[pattern.pattern_id],
                    actionable_steps=[
                        "Analyze what changes led to improvement",
                        "Document successful strategies",
                        "Consider applying improvements to other components"
                    ],
                    impact_estimate="Medium - Leveraging improvements could boost quality by 10-20%"
                ))

        return insights

    def _generate_success_insights(self, patterns: List[DetectedPattern]) -> List[PatternInsight]:
        """Generate insights for success patterns."""
        insights = []

        success_count = sum(p.frequency for p in patterns)
        if success_count >= 3:
            insights.append(PatternInsight(
                insight_type="recommendation",
                title="Successful Patterns Identified",
                description=f"Found {success_count} instances of successful response patterns",
                confidence=0.8,
                priority="medium",
                related_patterns=[p.pattern_id for p in patterns],
                actionable_steps=[
                    "Analyze common elements of successful responses",
                    "Document best practices",
                    "Train other agents on successful strategies",
                    "Consider creating templates based on successes"
                ],
                impact_estimate="Medium - Replicating successes could improve overall quality by 15-25%"
            ))

        return insights

    def _update_session_stats(self, analysis: AnalysisResult, patterns: List[DetectedPattern]):
        """Update session statistics."""
        self.session_stats["total_analyzed"] += 1
        self.session_stats["patterns_detected"] += len(patterns)
        self.session_stats["quality_scores"].append(analysis.quality_score)
        self.session_stats["agent_performance"][analysis.agent_type].append(analysis.quality_score)

        for pattern in patterns:
            self.session_stats["pattern_types"][pattern.pattern_type] += 1

    def _store_analysis_and_patterns(self, analysis: AnalysisResult, patterns: List[DetectedPattern]):
        """Store analysis and patterns in PRISM."""
        try:
            # Store analysis result
            self.response_analyzer.store_analysis_in_prism(analysis)

            # Store detected patterns
            if patterns:
                self.pattern_detector.store_patterns_in_prism(patterns)

        except Exception as e:
            print(f"Warning: Could not store analysis/patterns in PRISM: {e}", file=sys.stderr)

    def _calculate_summary_statistics(self) -> Dict[str, Any]:
        """Calculate comprehensive summary statistics."""
        return {
            "session_duration": time.time() - self.session_stats["session_start"],
            "total_analyses": self.session_stats["total_analyzed"],
            "total_patterns": self.session_stats["patterns_detected"],
            "average_quality": (
                sum(self.session_stats["quality_scores"]) / len(self.session_stats["quality_scores"])
                if self.session_stats["quality_scores"] else 0
            ),
            "quality_range": (
                [min(self.session_stats["quality_scores"]), max(self.session_stats["quality_scores"])]
                if self.session_stats["quality_scores"] else [0, 0]
            ),
            "agent_performance": {
                agent: sum(scores) / len(scores)
                for agent, scores in self.session_stats["agent_performance"].items()
                if scores
            },
            "pattern_distribution": dict(self.session_stats["pattern_types"]),
            "pipeline_stats": self.get_pipeline_statistics()
        }

    def get_pipeline_statistics(self) -> Dict[str, Any]:
        """Get pipeline performance statistics."""
        return {
            "analysis_history_size": len(self.analysis_history),
            "pattern_history_size": len(self.pattern_history),
            "pattern_detector_stats": self.pattern_detector.get_pattern_statistics(),
            "analyzer_stats": self.response_analyzer.get_analysis_stats()
        }


# Export key classes
__all__ = ['PatternAnalysisPipeline', 'PatternInsight']