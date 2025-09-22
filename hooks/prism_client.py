#!/usr/bin/env python3
"""
PRISM Client for Claude Code Hooks
Simple wrapper around HTTP client.
"""

from prism_http_client import PrismHTTPClient
from typing import Dict, List, Optional, Tuple, Any

class PrismClient:
    """PRISM client that uses HTTP interface."""

    def __init__(self):
        self._client = PrismHTTPClient()

    def is_available(self) -> bool:
        """Check if PRISM MCP is available."""
        return self._client.is_available()

    def store_memory(self, content: str, tier: str = "LONGTERM", metadata: Optional[Dict] = None) -> bool:
        """Store memory in PRISM."""
        return self._client.store_memory(content, tier, metadata)

    def search_memory(self, query: str, limit: int = 10, tiers: Optional[List[str]] = None) -> List[Dict]:
        """Search PRISM memory."""
        # MCP interface only supports searching one tier at a time or all
        if tiers and len(tiers) == 1:
            return self._client.search_memory(query, limit, tiers[0])
        else:
            # Search all tiers
            return self._client.search_memory(query, limit, None)

    def retrieve_memory(self, key: str, tier: str = "LONGTERM") -> Optional[Dict]:
        """Retrieve specific memory by key (search for exact key)."""
        results = self.search_memory(key, limit=1, tiers=[tier])
        if results and results[0].get('key') == key:
            return results[0]
        return None

    def analyze(self, text: str) -> Optional[Dict]:
        """Analyze text using PRISM reasoning."""
        result = self._client.analyze(text)
        if result:
            # Extract key fields from analysis result
            analysis = result.get('analysis', {})
            return {
                'confidence': analysis.get('confidence', 0),
                'zone': analysis.get('reasoning', {}).get('zone', 'yellow'),
                'method': analysis.get('reasoning', {}).get('method', 'unknown'),
                'solutions': analysis.get('reasoning', {}).get('solutions', []),
                'info': analysis
            }
        return None

    def detect_hallucination(self, text: str, confidence_threshold: float = 0.8) -> Optional[Dict]:
        """Detect hallucination risk in text."""
        return self._client.detect_hallucination(text, confidence_threshold)

    def calculate_semantic_drift(self, input_text: str, ground_truth: str) -> Optional[Dict]:
        """Calculate semantic drift between texts."""
        return self._client.calculate_semantic_drift(input_text, ground_truth)

    def generate_embedding(self, text: str) -> Optional[List[float]]:
        """Generate embedding for text (not available via MCP)."""
        # MCP doesn't expose embedding generation directly
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
        # MCP searches all tiers by default when tier is not specified
        return self.search_memory(query, limit, None)

    def close(self):
        """Close the MCP connection."""
        self._client.close()

# Singleton instance management
_client_instance = None

def get_prism_client() -> PrismClient:
    """Get or create PRISM client instance."""
    global _client_instance
    if _client_instance is None:
        _client_instance = PrismClient()
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
__all__ = ['PrismClient', 'get_prism_client', 'prism_context']