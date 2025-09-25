#!/usr/bin/env python3
"""
Semantic Code Analyzer - Central CodeT5+ Service
================================================
Provides semantic code analysis using PRISM's CodeT5+ capabilities.
NO FALLBACKS - all operations REQUIRE the HTTP server to be running.

Key Features:
- Analyzes code logic vs expected behavior
- Detects patterns and anti-patterns
- Compares implementation approaches
- Summarizes code semantics
- Caches results in Redis for performance
"""

import json
import sys
import time
import hashlib
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import requests
import redis

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
PRISM_HTTP_URL = "http://localhost:8090"
REDIS_HOST = "localhost"
REDIS_PORT = 6379
CACHE_TTL = 300  # 5 minutes for analysis cache
FILE_CACHE_TTL = 3600  # 1 hour for file content cache


class SemanticCodeAnalyzer:
    """Central service for all CodeT5+ semantic analysis operations."""

    def __init__(self):
        """Initialize analyzer with REQUIRED services."""
        # Initialize Redis - REQUIRED
        try:
            self.redis_client = redis.Redis(
                host=REDIS_HOST,
                port=REDIS_PORT,
                decode_responses=True
            )
            self.redis_client.ping()
            logger.info("✓ Redis connected")
        except Exception as e:
            logger.error(f"❌ Redis connection FAILED - REQUIRED for operation: {e}")
            raise RuntimeError("Redis is REQUIRED for semantic analysis caching")

        # Verify PRISM HTTP server - REQUIRED
        try:
            response = requests.get(f"{PRISM_HTTP_URL}/health", timeout=2)
            if response.status_code != 200:
                raise RuntimeError(f"PRISM HTTP server unhealthy: {response.status_code}")
            logger.info("✓ PRISM HTTP server connected")
        except Exception as e:
            logger.error(f"❌ PRISM HTTP server FAILED - REQUIRED for operation: {e}")
            raise RuntimeError("PRISM HTTP server is REQUIRED for semantic analysis")

    def analyze_code_logic(self, code: str, expected_behavior: str,
                          cache_key: Optional[str] = None) -> Dict[str, Any]:
        """
        Analyze if code logic matches expected behavior using CodeT5+.
        NO FALLBACKS - requires PRISM HTTP server.

        Args:
            code: Code to analyze
            expected_behavior: What the code should do
            cache_key: Optional cache key for results

        Returns:
            Analysis results with logical issues detected
        """
        # Check cache if key provided
        if cache_key:
            cached = self._get_cached_analysis(cache_key, "logic")
            if cached:
                logger.debug(f"Cache hit for logic analysis: {cache_key}")
                return cached

        # Call PRISM HTTP endpoint - NO FALLBACK
        try:
            response = requests.post(
                f"{PRISM_HTTP_URL}/analyze_code_logic",
                json={
                    "code": code,
                    "expected_behavior": expected_behavior
                },
                timeout=10
            )
            response.raise_for_status()

            result = response.json()
            if result["status"] != "success":
                raise RuntimeError(f"Analysis failed: {result['error']}")

            analysis = result["analysis"]

            # Cache if key provided
            if cache_key:
                self._cache_analysis(cache_key, "logic", analysis)

            return analysis

        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Code logic analysis FAILED: {e}")
            raise RuntimeError(f"Cannot analyze code logic - PRISM required: {e}")

    def detect_code_patterns(self, code: str,
                            cache_key: Optional[str] = None) -> Dict[str, Any]:
        """
        Detect patterns and anti-patterns in code using CodeT5+.
        NO FALLBACKS - requires PRISM HTTP server.

        Args:
            code: Code to analyze
            cache_key: Optional cache key for results

        Returns:
            Detected patterns, anti-patterns, and suggestions
        """
        # Check cache if key provided
        if cache_key:
            cached = self._get_cached_analysis(cache_key, "patterns")
            if cached:
                logger.debug(f"Cache hit for pattern detection: {cache_key}")
                return cached

        # Call PRISM HTTP endpoint - NO FALLBACK
        try:
            response = requests.post(
                f"{PRISM_HTTP_URL}/detect_code_patterns",
                json={"code": code},
                timeout=10
            )
            response.raise_for_status()

            result = response.json()
            if result["status"] != "success":
                raise RuntimeError(f"Pattern detection failed: {result['error']}")

            patterns = result["patterns"]

            # Cache if key provided
            if cache_key:
                self._cache_analysis(cache_key, "patterns", patterns)

            return patterns

        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Pattern detection FAILED: {e}")
            raise RuntimeError(f"Cannot detect patterns - PRISM required: {e}")

    def summarize_code(self, code: str,
                      cache_key: Optional[str] = None) -> Dict[str, Any]:
        """
        Summarize code semantics using CodeT5+.
        NO FALLBACKS - requires PRISM HTTP server.

        Args:
            code: Code to summarize
            cache_key: Optional cache key for results

        Returns:
            Code summary with semantic understanding
        """
        # Check cache if key provided
        if cache_key:
            cached = self._get_cached_analysis(cache_key, "summary")
            if cached:
                logger.debug(f"Cache hit for code summary: {cache_key}")
                return cached

        # Call PRISM HTTP endpoint - NO FALLBACK
        try:
            response = requests.post(
                f"{PRISM_HTTP_URL}/summarize_code",
                json={"code": code},
                timeout=10
            )
            response.raise_for_status()

            result = response.json()
            if result["status"] != "success":
                raise RuntimeError(f"Summarization failed: {result['error']}")

            summary = result["summary"]

            # Cache if key provided
            if cache_key:
                self._cache_analysis(cache_key, "summary", summary)

            return summary

        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Code summarization FAILED: {e}")
            raise RuntimeError(f"Cannot summarize code - PRISM required: {e}")

    def compare_implementations(self, code1: str, code2: str,
                               cache_key: Optional[str] = None) -> Dict[str, Any]:
        """
        Compare two implementations for functional equivalence.
        NO FALLBACKS - requires PRISM HTTP server.

        Args:
            code1: First implementation
            code2: Second implementation
            cache_key: Optional cache key for results

        Returns:
            Comparison results with differences identified
        """
        # Check cache if key provided
        if cache_key:
            cached = self._get_cached_analysis(cache_key, "comparison")
            if cached:
                logger.debug(f"Cache hit for implementation comparison: {cache_key}")
                return cached

        # Call PRISM HTTP endpoint - NO FALLBACK
        try:
            response = requests.post(
                f"{PRISM_HTTP_URL}/compare_implementations",
                json={
                    "code1": code1,
                    "code2": code2
                },
                timeout=10
            )
            response.raise_for_status()

            result = response.json()
            if result["status"] != "success":
                raise RuntimeError(f"Comparison failed: {result['error']}")

            comparison = result["comparison"]

            # Cache if key provided
            if cache_key:
                self._cache_analysis(cache_key, "comparison", comparison)

            return comparison

        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Implementation comparison FAILED: {e}")
            raise RuntimeError(f"Cannot compare implementations - PRISM required: {e}")

    def batch_analyze(self, analyses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Perform multiple analyses in batch for efficiency.

        Args:
            analyses: List of analysis requests, each with 'type' and parameters

        Returns:
            Dictionary mapping analysis IDs to results
        """
        results = {}

        for analysis in analyses:
            analysis_type = analysis["type"]
            analysis_id = analysis.get("id", hashlib.md5(str(analysis).encode()).hexdigest()[:8])

            try:
                if analysis_type == "logic":
                    result = self.analyze_code_logic(
                        analysis["code"],
                        analysis["expected_behavior"],
                        analysis.get("cache_key")  # cache_key is optional
                    )
                elif analysis_type == "patterns":
                    result = self.detect_code_patterns(
                        analysis["code"],
                        analysis.get("cache_key")  # cache_key is optional
                    )
                elif analysis_type == "summary":
                    result = self.summarize_code(
                        analysis["code"],
                        analysis.get("cache_key")  # cache_key is optional
                    )
                elif analysis_type == "comparison":
                    result = self.compare_implementations(
                        analysis["code1"],
                        analysis["code2"],
                        analysis.get("cache_key")  # cache_key is optional
                    )
                else:
                    result = {"error": f"Unknown analysis type: {analysis_type}"}

                results[analysis_id] = result

            except Exception as e:
                results[analysis_id] = {"error": str(e)}

        return results

    def cache_file_content(self, file_path: str, content: str) -> bool:
        """
        Cache file content in Redis for edit reconstruction.

        Args:
            file_path: Path to file
            content: File content to cache

        Returns:
            Success status
        """
        try:
            key = f"file:{file_path}"
            self.redis_client.setex(key, FILE_CACHE_TTL, content)
            logger.debug(f"Cached file content: {file_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to cache file content: {e}")
            return False

    def get_cached_file(self, file_path: str) -> Optional[str]:
        """
        Get cached file content from Redis.

        Args:
            file_path: Path to file

        Returns:
            Cached content or None
        """
        try:
            key = f"file:{file_path}"
            content = self.redis_client.get(key)
            if content:
                logger.debug(f"Retrieved cached file: {file_path}")
            return content
        except Exception as e:
            logger.error(f"Failed to get cached file: {e}")
            return None

    def reconstruct_with_edit(self, file_path: str, old_string: str,
                            new_string: str) -> Tuple[str, Dict[str, Any]]:
        """
        Reconstruct file with edit applied and analyze result.

        Args:
            file_path: Path to file being edited
            old_string: String to replace
            new_string: Replacement string

        Returns:
            Tuple of (new_content, analysis_results)
        """
        # Get cached content or read from disk
        content = self.get_cached_file(file_path)
        if not content:
            try:
                with open(file_path, 'r') as f:
                    content = f.read()
                self.cache_file_content(file_path, content)
            except Exception as e:
                logger.error(f"Failed to read file {file_path}: {e}")
                # Can't reconstruct without file content
                raise RuntimeError(f"Cannot reconstruct file for analysis: {e}")

        # Apply edit
        if old_string not in content:
            logger.warning(f"Old string not found in {file_path}")
            # Still try to analyze the new string alone
            new_content = new_string
        else:
            new_content = content.replace(old_string, new_string)

        # Cache the new content
        self.cache_file_content(file_path, new_content)

        # Analyze the full reconstructed file
        cache_key = f"{file_path}:{hashlib.md5(new_content.encode()).hexdigest()[:8]}"

        analysis = {
            "patterns": self.detect_code_patterns(new_content, cache_key),
            "summary": self.summarize_code(new_content, cache_key)
        }

        return new_content, analysis

    def _cache_analysis(self, cache_key: str, analysis_type: str,
                       data: Dict[str, Any]) -> bool:
        """Cache analysis results in Redis."""
        try:
            key = f"analysis:{analysis_type}:{cache_key}"
            self.redis_client.setex(key, CACHE_TTL, json.dumps(data))
            return True
        except Exception as e:
            logger.error(f"Failed to cache analysis: {e}")
            return False

    def _get_cached_analysis(self, cache_key: str, analysis_type: str) -> Optional[Dict[str, Any]]:
        """Get cached analysis from Redis."""
        try:
            key = f"analysis:{analysis_type}:{cache_key}"
            data = self.redis_client.get(key)
            if data:
                return json.loads(data)
        except Exception as e:
            logger.error(f"Failed to get cached analysis: {e}")
        return None

    def clear_file_cache(self, file_path: str) -> bool:
        """Clear cached content for a specific file."""
        try:
            key = f"file:{file_path}"
            self.redis_client.delete(key)
            logger.debug(f"Cleared cache for file: {file_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to clear file cache: {e}")
            return False

    def get_cache_stats(self) -> Dict[str, int]:
        """Get statistics about cached items."""
        try:
            file_keys = len(list(self.redis_client.scan_iter("file:*")))
            analysis_keys = len(list(self.redis_client.scan_iter("analysis:*")))

            return {
                "cached_files": file_keys,
                "cached_analyses": analysis_keys,
                "total_cached_items": file_keys + analysis_keys
            }
        except Exception as e:
            logger.error(f"Failed to get cache stats: {e}")
            return {"error": str(e)}


# Singleton instance
_analyzer_instance = None

def get_semantic_analyzer() -> SemanticCodeAnalyzer:
    """Get singleton instance of semantic analyzer."""
    global _analyzer_instance
    if _analyzer_instance is None:
        _analyzer_instance = SemanticCodeAnalyzer()
    return _analyzer_instance


# Export for use by other hooks
__all__ = ['SemanticCodeAnalyzer', 'get_semantic_analyzer']