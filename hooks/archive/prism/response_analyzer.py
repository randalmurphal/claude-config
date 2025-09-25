#!/usr/bin/env python3
"""
Agent Response Analyzer - PRISM Integration Core
================================================
Analyzes agent responses using PRISM MCP exclusively.
NO FALLBACKS - System fails hard if PRISM unavailable.

This analyzer provides:
- Hallucination detection via PRISM MCP
- Semantic drift calculation via PRISM MCP
- Pattern analysis via PRISM MCP
- Response quality assessment via PRISM MCP
"""

import sys
import time
import json
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict

# Import our dependencies
sys.path.insert(0, str(Path(__file__).parent))
from prism_client import get_prism_client, PrismClient
from checkpoint_system import TranscriptEntry, CheckpointManager, TranscriptProcessor


class PrismUnavailableError(Exception):
    """Raised when PRISM MCP is unavailable and no fallback allowed."""
    pass


@dataclass
class AnalysisResult:
    """Result of analyzing an agent response."""

    entry_id: str                          # Transcript entry ID
    timestamp: float                       # When analysis was performed
    agent_type: str                        # Type of agent that generated response

    # PRISM Analysis Results
    hallucination_risk: Optional[Dict]     # Hallucination detection result
    semantic_drift: Optional[Dict]         # Semantic drift measurement
    prism_analysis: Optional[Dict]         # General PRISM analysis
    quality_score: float                   # Overall quality score (0-1)

    # Extracted Patterns
    detected_patterns: List[str]           # Patterns detected in response
    response_type: str                     # Type of response (implementation, debug, etc.)
    confidence: float                      # Confidence in analysis

    # Metadata
    analysis_duration: float               # Time taken for analysis
    prism_version: str                     # PRISM version used
    error_message: Optional[str] = None    # Any errors during analysis

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AnalysisResult':
        """Create from dictionary."""
        return cls(**data)


class ResponseAnalyzer:
    """Analyzes agent responses using PRISM MCP exclusively."""

    def __init__(self, checkpoint_manager: Optional[CheckpointManager] = None):
        """Initialize response analyzer.

        Args:
            checkpoint_manager: Optional checkpoint manager for tracking processed entries

        Raises:
            PrismUnavailableError: If PRISM MCP is not available
        """
        # Get PRISM client - FAIL HARD if unavailable
        self.prism_client = get_prism_client()
        if not self.prism_client.is_available():
            raise PrismUnavailableError(
                "PRISM MCP is not available. This system has NO FALLBACKS and cannot operate without PRISM."
            )

        self.checkpoint_manager = checkpoint_manager or CheckpointManager()
        self.processor = TranscriptProcessor(self.checkpoint_manager)

        print("Response Analyzer initialized - PRISM MCP connection verified")

    def _ensure_prism_available(self) -> None:
        """Ensure PRISM is available before each operation.

        Raises:
            PrismUnavailableError: If PRISM becomes unavailable
        """
        if not self.prism_client.is_available():
            raise PrismUnavailableError(
                "PRISM MCP became unavailable during operation. NO FALLBACKS - operation terminated."
            )

    def analyze_response(self, entry: TranscriptEntry, ground_truth: Optional[str] = None) -> AnalysisResult:
        """Analyze a single agent response using PRISM MCP.

        Args:
            entry: Transcript entry to analyze
            ground_truth: Optional ground truth for semantic drift calculation

        Returns:
            AnalysisResult with complete PRISM-based analysis

        Raises:
            PrismUnavailableError: If PRISM MCP is unavailable
        """
        start_time = time.time()

        # FAIL HARD if PRISM unavailable
        self._ensure_prism_available()

        # Initialize result
        result = AnalysisResult(
            entry_id=entry.entry_id,
            timestamp=time.time(),
            agent_type=entry.agent_type,
            hallucination_risk=None,
            semantic_drift=None,
            prism_analysis=None,
            quality_score=0.0,
            detected_patterns=[],
            response_type="unknown",
            confidence=0.0,
            analysis_duration=0.0,
            prism_version="1.0"
        )

        try:
            # 1. PRISM Hallucination Detection (REQUIRED)
            result.hallucination_risk = self.prism_client.detect_hallucination(
                entry.content,
                confidence_threshold=0.7
            )
            if result.hallucination_risk is None:
                raise PrismUnavailableError("PRISM hallucination detection failed")

            # 2. PRISM Semantic Drift (if ground truth provided)
            if ground_truth:
                result.semantic_drift = self.prism_client.calculate_semantic_drift(
                    entry.content,
                    ground_truth
                )
                if result.semantic_drift is None:
                    raise PrismUnavailableError("PRISM semantic drift calculation failed")

            # 3. PRISM General Analysis (REQUIRED)
            result.prism_analysis = self.prism_client.analyze(entry.content)
            if result.prism_analysis is None:
                raise PrismUnavailableError("PRISM general analysis failed")

            # 4. Extract insights from PRISM results
            self._extract_analysis_insights(result, entry)

            # 5. Calculate overall quality score
            result.quality_score = self._calculate_quality_score(result)

            # 6. Detect patterns using PRISM analysis
            result.detected_patterns = self._detect_patterns_from_prism(result, entry)

            # 7. Determine response type
            result.response_type = self._classify_response_type(entry, result)

        except Exception as e:
            if isinstance(e, PrismUnavailableError):
                raise  # Re-raise PRISM unavailable errors
            else:
                # Convert other errors to PRISM unavailable since we have no fallbacks
                raise PrismUnavailableError(f"PRISM analysis failed: {e}")

        result.analysis_duration = time.time() - start_time
        return result

    def _extract_analysis_insights(self, result: AnalysisResult, entry: TranscriptEntry) -> None:
        """Extract insights from PRISM analysis results."""
        if not result.prism_analysis:
            return

        analysis = result.prism_analysis.get('analysis', {})

        # Extract confidence from PRISM
        result.confidence = analysis.get('confidence', 0.0)

        # Store PRISM reasoning zone
        reasoning = analysis.get('reasoning', {})
        zone = reasoning.get('zone', 'unknown')

        # Map PRISM zones to our patterns
        if zone == 'green':
            result.detected_patterns.append('high_confidence_response')
        elif zone == 'yellow':
            result.detected_patterns.append('moderate_confidence_response')
        elif zone == 'red':
            result.detected_patterns.append('low_confidence_response')

    def _calculate_quality_score(self, result: AnalysisResult) -> float:
        """Calculate overall quality score from PRISM results."""
        score = 0.0

        # Base score from PRISM confidence
        if result.prism_analysis:
            prism_confidence = result.prism_analysis.get('analysis', {}).get('confidence', 0.0)
            score += prism_confidence * 0.4

        # Hallucination penalty
        if result.hallucination_risk:
            hallucination_score = result.hallucination_risk.get('risk_score', 0.0)
            score += (1.0 - hallucination_score) * 0.3

        # Semantic drift penalty (if available)
        if result.semantic_drift:
            drift_score = result.semantic_drift.get('drift_score', 0.0)
            score += (1.0 - drift_score) * 0.3
        else:
            # No drift data available, use neutral score
            score += 0.3

        return min(max(score, 0.0), 1.0)

    def _detect_patterns_from_prism(self, result: AnalysisResult, entry: TranscriptEntry) -> List[str]:
        """Detect patterns using PRISM analysis results."""
        patterns = list(result.detected_patterns)  # Start with existing patterns

        # Hallucination patterns
        if result.hallucination_risk:
            risk_score = result.hallucination_risk.get('risk_score', 0.0)
            if risk_score > 0.8:
                patterns.append('high_hallucination_risk')
            elif risk_score > 0.5:
                patterns.append('moderate_hallucination_risk')

            # Check for specific hallucination types
            risk_type = result.hallucination_risk.get('risk_type', '')
            if risk_type:
                patterns.append(f'hallucination_{risk_type}')

        # Semantic drift patterns
        if result.semantic_drift:
            drift_score = result.semantic_drift.get('drift_score', 0.0)
            if drift_score > 0.7:
                patterns.append('high_semantic_drift')
            elif drift_score > 0.4:
                patterns.append('moderate_semantic_drift')

        # PRISM reasoning patterns
        if result.prism_analysis:
            reasoning = result.prism_analysis.get('analysis', {}).get('reasoning', {})
            method = reasoning.get('method', '')
            if method:
                patterns.append(f'reasoning_{method}')

            solutions = reasoning.get('solutions', [])
            if solutions:
                patterns.append('solution_provided')
                if len(solutions) > 1:
                    patterns.append('multiple_solutions')

        # Agent-specific patterns
        agent_type = entry.agent_type.lower()
        if 'test' in agent_type and result.quality_score > 0.8:
            patterns.append('high_quality_test_output')
        elif 'skeleton' in agent_type and result.confidence > 0.8:
            patterns.append('confident_architecture_design')
        elif 'implement' in agent_type and result.hallucination_risk and result.hallucination_risk.get('risk_score', 0) < 0.3:
            patterns.append('reliable_implementation')

        return patterns

    def _classify_response_type(self, entry: TranscriptEntry, result: AnalysisResult) -> str:
        """Classify the type of response based on content and PRISM analysis."""
        content = entry.content.lower()
        agent_type = entry.agent_type.lower()

        # Use PRISM analysis for classification hints
        prism_patterns = result.detected_patterns

        # Primary classification by agent type
        if 'skeleton' in agent_type:
            return 'architecture_design'
        elif 'test' in agent_type:
            return 'test_implementation'
        elif 'implement' in agent_type:
            return 'code_implementation'
        elif 'debug' in agent_type or 'fix' in agent_type:
            return 'debugging_solution'
        elif 'review' in agent_type or 'validator' in agent_type:
            return 'code_review'

        # Secondary classification by content patterns
        if any(pattern in content for pattern in ['error', 'exception', 'failed', 'bug']):
            return 'error_analysis'
        elif any(pattern in content for pattern in ['test', 'assert', 'expect']):
            return 'testing_output'
        elif any(pattern in content for pattern in ['class', 'function', 'def', 'import']):
            return 'code_generation'
        elif any(pattern in prism_patterns for pattern in ['solution_provided', 'reasoning']):
            return 'analytical_response'

        return 'general_response'

    def analyze_multiple_responses(self, entries: List[TranscriptEntry],
                                 ground_truths: Optional[List[str]] = None) -> List[AnalysisResult]:
        """Analyze multiple agent responses using checkpoint system.

        Args:
            entries: List of transcript entries to analyze
            ground_truths: Optional list of ground truths for semantic drift calculation

        Returns:
            List of AnalysisResult objects for successfully analyzed entries

        Raises:
            PrismUnavailableError: If PRISM MCP is unavailable
        """
        # FAIL HARD if PRISM unavailable
        self._ensure_prism_available()

        results = []

        def analyze_entry(entry: TranscriptEntry) -> AnalysisResult:
            """Processor function for checkpoint system."""
            ground_truth = None
            if ground_truths and len(ground_truths) > len(results):
                ground_truth = ground_truths[len(results)]

            return self.analyze_response(entry, ground_truth)

        # Use checkpoint system to process entries
        processing_results = self.processor.process_entries(entries, analyze_entry)

        # Extract the analysis results
        for proc_result in processing_results.get("processing_results", []):
            if "result" in proc_result:
                results.append(proc_result["result"])

        # Report any errors (which would be PRISM failures)
        if processing_results.get("errors"):
            error_count = len(processing_results["errors"])
            print(f"Warning: {error_count} entries failed analysis due to PRISM issues")
            for error in processing_results["errors"]:
                print(f"  Entry {error['entry_id']}: {error['error']}")

        return results

    def store_analysis_in_prism(self, analysis_result: AnalysisResult) -> bool:
        """Store analysis result in PRISM memory for future reference.

        Args:
            analysis_result: Analysis result to store

        Returns:
            True if stored successfully, False otherwise

        Raises:
            PrismUnavailableError: If PRISM MCP is unavailable
        """
        # FAIL HARD if PRISM unavailable
        self._ensure_prism_available()

        try:
            # Create memory content
            content = {
                "type": "agent_response_analysis",
                "entry_id": analysis_result.entry_id,
                "agent_type": analysis_result.agent_type,
                "response_type": analysis_result.response_type,
                "quality_score": analysis_result.quality_score,
                "confidence": analysis_result.confidence,
                "patterns": analysis_result.detected_patterns,
                "hallucination_risk": analysis_result.hallucination_risk,
                "semantic_drift": analysis_result.semantic_drift,
                "analysis_timestamp": analysis_result.timestamp
            }

            # Determine storage tier based on quality and patterns
            tier = "WORKING"
            if analysis_result.quality_score > 0.8:
                tier = "LONGTERM"
            elif any(pattern in analysis_result.detected_patterns
                    for pattern in ['high_hallucination_risk', 'high_semantic_drift']):
                tier = "LONGTERM"  # Store problematic patterns for learning

            # Store in PRISM
            success = self.prism_client.store_memory(
                content=json.dumps(content),
                tier=tier,
                metadata={
                    "type": "response_analysis",
                    "agent_type": analysis_result.agent_type,
                    "quality_tier": "high" if analysis_result.quality_score > 0.8 else "medium",
                    "patterns": analysis_result.detected_patterns[:5],  # Limit metadata size
                    "timestamp": str(analysis_result.timestamp)
                }
            )

            if not success:
                raise PrismUnavailableError("Failed to store analysis in PRISM memory")

            return True

        except Exception as e:
            if isinstance(e, PrismUnavailableError):
                raise
            else:
                raise PrismUnavailableError(f"PRISM storage failed: {e}")

    def search_historical_patterns(self, query: str, limit: int = 10) -> List[Dict]:
        """Search historical response analysis patterns in PRISM.

        Args:
            query: Search query for patterns
            limit: Maximum number of results

        Returns:
            List of historical analysis results

        Raises:
            PrismUnavailableError: If PRISM MCP is unavailable
        """
        # FAIL HARD if PRISM unavailable
        self._ensure_prism_available()

        try:
            results = self.prism_client.search_memory(
                query=f"agent_response_analysis {query}",
                limit=limit
            )

            if results is None:
                raise PrismUnavailableError("PRISM memory search failed")

            return results

        except Exception as e:
            if isinstance(e, PrismUnavailableError):
                raise
            else:
                raise PrismUnavailableError(f"PRISM search failed: {e}")

    def get_analysis_stats(self) -> Dict[str, Any]:
        """Get statistics about the analyzer state.

        Returns:
            Dictionary with analyzer statistics
        """
        checkpoint_stats = self.checkpoint_manager.get_stats()

        return {
            "prism_available": self.prism_client.is_available(),
            "checkpoint_stats": checkpoint_stats,
            "analyzer_mode": "NO_FALLBACKS",
            "last_check": time.time()
        }


# Utility functions
def create_response_analyzer(checkpoint_file: Optional[str] = None) -> ResponseAnalyzer:
    """Create a response analyzer with optional custom checkpoint file.

    Args:
        checkpoint_file: Optional path to checkpoint file

    Returns:
        ResponseAnalyzer instance

    Raises:
        PrismUnavailableError: If PRISM MCP is unavailable
    """
    checkpoint_manager = None
    if checkpoint_file:
        checkpoint_manager = CheckpointManager(Path(checkpoint_file))

    return ResponseAnalyzer(checkpoint_manager)


def analyze_agent_response(agent_type: str, content: str, session_id: str,
                         ground_truth: Optional[str] = None) -> AnalysisResult:
    """Convenience function to analyze a single agent response.

    Args:
        agent_type: Type of agent that generated the response
        content: Response content to analyze
        session_id: Session identifier
        ground_truth: Optional ground truth for semantic drift

    Returns:
        AnalysisResult with complete analysis

    Raises:
        PrismUnavailableError: If PRISM MCP is unavailable
    """
    from checkpoint_system import create_transcript_entry

    entry = create_transcript_entry(agent_type, content, session_id)
    analyzer = create_response_analyzer()

    return analyzer.analyze_response(entry, ground_truth)


# Export key classes and functions
__all__ = [
    'ResponseAnalyzer',
    'AnalysisResult',
    'PrismUnavailableError',
    'create_response_analyzer',
    'analyze_agent_response'
]