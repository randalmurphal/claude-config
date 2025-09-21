#!/opt/envs/py3.13/bin/python
"""
PRISM HTTP Client for Claude Code Hooks
Uses HTTP API to communicate with PRISM server.
"""

import json
import logging
import requests
from typing import Dict, List, Optional, Tuple, Any
from urllib.parse import urljoin

logger = logging.getLogger(__name__)

class PrismHTTPClient:
    """PRISM client that uses HTTP API."""

    def __init__(self, base_url: str = "http://localhost:8090"):
        """Initialize HTTP client.

        Args:
            base_url: Base URL for PRISM HTTP server
        """
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})

    def is_available(self) -> bool:
        """Check if PRISM HTTP server is available."""
        try:
            response = self.session.get(urljoin(self.base_url, "/health"), timeout=2)
            if response.status_code == 200:
                health = response.json()
                return all(health.get("services", {}).values())
            return False
        except:
            return False

    def store_memory(self, content: str, tier: str = "LONGTERM", metadata: Optional[Dict] = None) -> bool:
        """Store memory in PRISM."""
        try:
            response = self.session.post(
                urljoin(self.base_url, "/store_memory"),
                json={
                    "content": content,
                    "tier": tier.upper(),
                    "metadata": metadata or {}
                },
                timeout=5
            )
            if response.status_code == 200:
                result = response.json()
                return result.get("success", False)
            return False
        except Exception as e:
            logger.error(f"Failed to store memory: {e}")
            return False

    def search_memory(self, query: str, limit: int = 10, tiers: Optional[List[str]] = None) -> List[Dict]:
        """Search PRISM memory."""
        try:
            # HTTP API expects single tier or None for all
            tier = tiers[0] if tiers and len(tiers) == 1 else None

            response = self.session.post(
                urljoin(self.base_url, "/search_memory"),
                json={
                    "query": query,
                    "limit": limit,
                    "tier": tier
                },
                timeout=5
            )
            if response.status_code == 200:
                result = response.json()
                return result.get("results", [])
            return []
        except Exception as e:
            logger.error(f"Failed to search memory: {e}")
            return []

    def retrieve_memory(self, key: str, tier: str = "LONGTERM") -> Optional[Dict]:
        """Retrieve specific memory by key."""
        results = self.search_memory(key, limit=1, tiers=[tier])
        if results and results[0].get('key') == key:
            return results[0]
        return None

    def analyze(self, text: str) -> Optional[Dict]:
        """Analyze text using PRISM reasoning."""
        try:
            response = self.session.post(
                urljoin(self.base_url, "/analyze"),
                json={"text": text},
                timeout=10
            )
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            logger.error(f"Failed to analyze text: {e}")
            return None

    def detect_hallucination(self, text: str, confidence_threshold: float = 0.8) -> Optional[Dict]:
        """Detect hallucination risk in text."""
        try:
            response = self.session.post(
                urljoin(self.base_url, "/detect_hallucination"),
                json={
                    "text": text,
                    "confidence_threshold": confidence_threshold
                },
                timeout=10
            )
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            logger.error(f"Failed to detect hallucination: {e}")
            return None

    def calculate_semantic_drift(self, input_text: str, ground_truth: str) -> Optional[Dict]:
        """Calculate semantic drift between texts."""
        try:
            response = self.session.post(
                urljoin(self.base_url, "/semantic_residue"),
                json={
                    "input_text": input_text,
                    "ground_truth": ground_truth
                },
                timeout=10
            )
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            logger.error(f"Failed to calculate semantic drift: {e}")
            return None

    def generate_embedding(self, text: str) -> Optional[List[float]]:
        """Generate embedding for text (not exposed via HTTP yet)."""
        # Could add this endpoint if needed
        return None

    def extract_intent(self, text: str) -> Tuple[str, float]:
        """Extract intent from text (local implementation)."""
        text_lower = text.lower()

        patterns = [
            (['fix', 'bug', 'error', 'issue', 'broken', 'crash'], 'bug_fix', 0.9),
            (['add', 'implement', 'feature', 'create', 'new'], 'feature', 0.85),
            (['refactor', 'clean', 'optimize', 'improve', 'restructure'], 'refactor', 0.8),
            (['test', 'verify', 'check', 'validate', 'ensure'], 'testing', 0.75),
            (['document', 'docs', 'readme', 'comment'], 'documentation', 0.7),
            (['search', 'find', 'locate', 'where', 'discover'], 'research', 0.65),
            (['analyze', 'investigate', 'understand', 'study'], 'analysis', 0.7)
        ]

        for keywords, intent, confidence in patterns:
            if any(word in text_lower for word in keywords):
                return (intent, confidence)

        return ('general', 0.5)

    def calculate_relevance(self, query: str, content: str) -> float:
        """Calculate relevance between query and content."""
        if not query or not content:
            return 0.0

        query_words = set(query.lower().split())
        content_words = set(content.lower().split())

        if not query_words:
            return 0.0

        # Check exact phrase match
        if query.lower() in content.lower():
            return 1.0

        # Check word overlap
        overlap = len(query_words & content_words)
        relevance = overlap / len(query_words)

        # Boost if all query words present
        if query_words.issubset(content_words):
            relevance = min(relevance * 1.5, 1.0)

        return relevance

    def detect_dangerous_command(self, command: str) -> Tuple[bool, str]:
        """Detect dangerous bash commands."""
        dangerous_patterns = [
            ('rm -rf /', 'Deletes entire filesystem'),
            ('rm -rf *', 'Deletes all files in directory'),
            ('rm -rf ~', 'Deletes home directory'),
            ('chmod 777', 'Makes files world-writable'),
            ('chmod -R 777', 'Recursively makes files world-writable'),
            ('curl | sh', 'Executes remote code'),
            ('wget | bash', 'Executes remote code'),
            ('curl | sudo', 'Executes remote code with privileges'),
            ('DROP DATABASE', 'Deletes database'),
            ('DROP TABLE', 'Deletes table'),
            ('DELETE FROM', 'Deletes data from table'),
            ('TRUNCATE', 'Removes all data from table'),
            ('sudo rm', 'Privileged deletion'),
            ('dd if=/dev/zero', 'Can overwrite disk'),
            ('dd of=/dev/', 'Can overwrite device'),
            (':(){ :|:& };:', 'Fork bomb'),
            ('> /dev/sda', 'Overwrites disk'),
            ('mkfs', 'Formats filesystem'),
            ('format c:', 'Formats drive (Windows)')
        ]

        cmd_lower = command.lower()
        for pattern, reason in dangerous_patterns:
            if pattern.lower() in cmd_lower:
                return (True, reason)

        return (False, '')

    def learn_workflow_pattern(self, commands: List[str], success: bool) -> bool:
        """Learn workflow patterns from command sequences."""
        if not commands:
            return False

        # Store workflow as episodic memory
        workflow_content = f"Workflow pattern: {' -> '.join(commands[:10])}"
        metadata = {
            'type': 'workflow',
            'success': str(success),
            'command_count': str(len(commands))
        }

        return self.store_memory(workflow_content, 'EPISODIC', metadata)

    def hybrid_search(self, query: str, limit: int = 10) -> List[Dict]:
        """Hybrid search across all memory tiers."""
        return self.search_memory(query, limit, None)

    def close(self):
        """Close the HTTP session."""
        self.session.close()

# Singleton instance management
_client_instance = None

def get_prism_client() -> PrismHTTPClient:
    """Get or create PRISM client instance."""
    global _client_instance
    if _client_instance is None:
        _client_instance = PrismHTTPClient()
    return _client_instance

def prism_context():
    """Context manager for PRISM client."""
    class PrismContext:
        def __enter__(self):
            return get_prism_client()
        def __exit__(self, exc_type, exc_val, exc_tb):
            # Keep connection alive - don't close
            pass
    return PrismContext()

# Export for compatibility
__all__ = ['PrismHTTPClient', 'get_prism_client', 'prism_context']