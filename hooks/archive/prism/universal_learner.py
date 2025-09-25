#!/usr/bin/env python3
"""
Universal Learning Module V2 - Optimized for Semantic Search
Stores semantic content with rich metadata and relationships.
"""

import json
import time
import hashlib
import os
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from collections import defaultdict
from datetime import datetime, timezone
import subprocess
import requests

# Neo4j client for relationship storage
try:
    from neo4j import GraphDatabase
    HAS_NEO4J = True
except ImportError:
    HAS_NEO4J = False

# Redis client for temporal caching
try:
    import redis
    HAS_REDIS = True
except ImportError:
    HAS_REDIS = False


class PRISMHTTPClient:
    """HTTP client for PRISM MCP server with enhanced capabilities."""

    def __init__(self, host: str = "localhost", port: int = 8090):
        self.base_url = f"http://{host}:{port}"
        self.session = requests.Session()

    def analyze(self, text: str) -> Dict[str, Any]:
        """Analyze text for reasoning and hallucination detection."""
        try:
            response = self.session.post(
                f"{self.base_url}/analyze",
                json={"text": text}  # Send plain text, not JSON
            )
            if response.status_code == 200:
                return response.json()
        except:
            pass
        return {"confidence": 0.5, "hallucination_risk": 0.3, "reasoning": {}}

    def store_memory(self, content: str, tier: str, metadata: Optional[Dict] = None) -> Dict:
        """Store memory in PRISM with rich metadata."""
        try:
            response = self.session.post(
                f"{self.base_url}/store_memory",
                json={
                    "content": content,
                    "tier": tier,
                    "metadata": metadata or {}
                }
            )
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            return {"success": False, "error": str(e)}
        return {"success": False}

    def search_memory(self, query: str, tier: Optional[str] = None, limit: int = 10) -> List[Dict]:
        """Search memory in PRISM semantically."""
        try:
            json_data = {"query": query, "limit": limit}
            if tier:
                json_data["tier"] = tier
            response = self.session.post(
                f"{self.base_url}/search_memory",
                json=json_data
            )
            if response.status_code == 200:
                return response.json().get("results", [])
        except:
            pass
        return []

    def detect_hallucination(self, text: str, confidence_threshold: float = 0.8) -> Dict:
        """Detect hallucination risk."""
        try:
            response = self.session.post(
                f"{self.base_url}/detect_hallucination",
                json={
                    "text": text,
                    "confidence_threshold": confidence_threshold
                }
            )
            if response.status_code == 200:
                return response.json()
        except:
            pass
        return {"risk": 0.5, "confidence": 0.5}


class GraphRelationshipStore:
    """Neo4j interface for storing pattern relationships."""

    def __init__(self):
        self.driver = None
        if HAS_NEO4J:
            try:
                self.driver = GraphDatabase.driver(
                    "neo4j://localhost:7687",
                    auth=("neo4j", "password")
                )
                # Test connection
                with self.driver.session() as session:
                    session.run("RETURN 1")
            except:
                self.driver = None

    def store_relationships(self, relationships: List[Tuple]) -> bool:
        """Store relationships in Neo4j."""
        if not self.driver:
            return False

        try:
            with self.driver.session() as session:
                for rel in relationships:
                    if len(rel) == 3:
                        source, rel_type, target = rel
                        properties = {}
                    else:
                        source, rel_type, target, properties = rel

                    # Create nodes and relationship
                    session.run(
                        f"""
                        MERGE (a:Entity {{name: $source}})
                        MERGE (b:Entity {{name: $target}})
                        MERGE (a)-[r:{rel_type}]->(b)
                        SET r += $properties
                        """,
                        source=source, target=target, properties=properties
                    )
            return True
        except:
            return False

    def find_related(self, entity: str, rel_type: Optional[str] = None, depth: int = 1) -> List[Dict]:
        """Find related entities through graph traversal."""
        if not self.driver:
            return []

        try:
            with self.driver.session() as session:
                if rel_type:
                    query = f"""
                    MATCH (a:Entity {{name: $entity}})-[:{rel_type}*1..{depth}]-(b:Entity)
                    RETURN DISTINCT b.name as related
                    """
                else:
                    query = f"""
                    MATCH (a:Entity {{name: $entity}})-[*1..{depth}]-(b:Entity)
                    RETURN DISTINCT b.name as related
                    """

                result = session.run(query, entity=entity)
                return [{"related": record["related"]} for record in result]
        except:
            return []


class TemporalCache:
    """Redis-based temporal cache for session patterns."""

    def __init__(self):
        self.redis_client = None
        if HAS_REDIS:
            try:
                self.redis_client = redis.Redis(
                    host='localhost',
                    port=6379,
                    decode_responses=True
                )
                self.redis_client.ping()
            except:
                self.redis_client = None

    def cache_pattern(self, pattern_id: str, pattern_data: Dict, ttl: int = 3600):
        """Cache pattern with TTL."""
        if not self.redis_client:
            return False

        try:
            key = f"pattern:{pattern_id}"
            self.redis_client.setex(
                key,
                ttl,
                json.dumps(pattern_data)
            )
            return True
        except:
            return False

    def get_cached(self, pattern_id: str) -> Optional[Dict]:
        """Get cached pattern."""
        if not self.redis_client:
            return None

        try:
            key = f"pattern:{pattern_id}"
            data = self.redis_client.get(key)
            if data:
                return json.loads(data)
        except:
            pass
        return None


class UniversalLearner:
    """Universal learning system with semantic content extraction."""

    def __init__(self):
        self.prism = PRISMHTTPClient()
        self.graph_store = GraphRelationshipStore()
        self.temporal_cache = TemporalCache()

        self.cache_dir = Path.home() / ".claude" / "universal_cache"
        self.cache_dir.mkdir(exist_ok=True)

        # Load configuration
        self.config = self.load_config()

        self.pattern_cache = self.load_pattern_cache()
        self.session_id = self.get_session_id()
        self.project_name = self.get_current_project()

    def load_config(self) -> Dict:
        """Load configuration from file or use defaults."""
        config_file = Path.home() / ".claude" / "universal_learner_config.json"
        if config_file.exists():
            try:
                with open(config_file) as f:
                    return json.load(f)
            except:
                pass

        # Default configuration
        return {
            "search": {
                "similarity_threshold": {"default": 0.3},
                "result_limits": {"default": 15}
            },
            "validation": {
                "hallucination_risk_threshold": {"default": 0.7},
                "min_confidence": {"default": 0.3}
            },
            "memory_tiers": {},
            "caching": {
                "redis_ttl_by_type": {"default": 3600}
            }
        }

    def extract_semantic_content(self, pattern: Dict) -> str:
        """Extract human-readable semantic content from pattern."""
        pattern_type = pattern.get("type", "")

        # File coupling patterns
        if pattern_type == "file_coupling":
            files = pattern.get("files", [])
            reason = pattern.get("reason", "frequently edited together")
            return f"Files {', '.join(files)} are {reason}"

        # Command patterns
        elif pattern_type in ["command_error", "command_workflow"]:
            error = pattern.get("error", "")
            fix = pattern.get("fix", "")
            command = pattern.get("command", "")
            if error and fix:
                return f"Error '{error}' can be fixed with '{fix}'"
            elif command:
                return f"Command workflow: {command} - {pattern.get('description', '')}"

        # Test coverage patterns
        elif pattern_type == "test_coverage":
            file = pattern.get("file", "unknown")
            coverage = pattern.get("coverage", 0)
            insight = pattern.get("insight", "")
            return f"Test coverage for {file}: {coverage}% coverage. {insight}"

        # Validation patterns
        elif pattern_type == "validation_error":
            file = pattern.get("file", "")
            issue = pattern.get("issue", "")
            return f"Code quality issue in {file}: {issue}"

        # Code patterns
        elif pattern_type in ["coding_standard", "best_practice", "code_pattern"]:
            # These usually have good semantic content already
            return pattern.get("content", str(pattern))

        # Architecture patterns
        elif pattern_type == "architecture":
            return pattern.get("content", f"Architectural decision: {pattern.get('decision', '')}")

        # Session patterns
        elif pattern_type == "session_learning":
            return pattern.get("content", f"Session insight: {pattern}")

        # Workflow patterns
        elif pattern_type == "workflow":
            steps = pattern.get("steps", [])
            return f"Workflow: {' -> '.join(steps)}"

        # Default: try to extract content or create description
        if "content" in pattern and pattern["content"]:
            return str(pattern["content"])
        elif "description" in pattern:
            return pattern["description"]
        else:
            # Build semantic description from available fields
            parts = []
            for key in ["action", "target", "result", "insight", "learning"]:
                if key in pattern:
                    parts.append(f"{key}: {pattern[key]}")
            if parts:
                return f"{pattern_type} - {', '.join(parts)}"
            return f"{pattern_type} pattern: {json.dumps(pattern, default=str)[:200]}"

    def extract_relationships(self, pattern: Dict) -> List[Tuple]:
        """Extract graph relationships from pattern."""
        relationships = []
        pattern_type = pattern.get("type", "")

        # Explicit relationships
        if "relationships" in pattern:
            return pattern["relationships"]

        # File coupling
        if pattern_type == "file_coupling":
            files = pattern.get("files", [])
            for i, file1 in enumerate(files):
                for file2 in files[i+1:]:
                    relationships.append((
                        file1,
                        "COUPLED_WITH",
                        file2,
                        {"frequency": pattern.get("frequency", 1)}
                    ))

        # Command workflows
        elif pattern_type == "command_workflow":
            commands = pattern.get("sequence", [])
            for i in range(len(commands) - 1):
                relationships.append((
                    commands[i],
                    "FOLLOWED_BY",
                    commands[i+1]
                ))

        # Error fixes
        elif pattern_type == "command_error":
            if pattern.get("error") and pattern.get("fix"):
                relationships.append((
                    pattern["error"],
                    "FIXED_BY",
                    pattern["fix"]
                ))

        # Test coverage
        elif pattern_type == "test_coverage":
            if pattern.get("file") and pattern.get("test_file"):
                relationships.append((
                    pattern["file"],
                    "TESTED_BY",
                    pattern["test_file"]
                ))

        # Pattern evolution
        if pattern.get("evolves_from"):
            relationships.append((
                pattern["evolves_from"],
                "EVOLVES_TO",
                pattern.get("pattern_id", "")
            ))

        return relationships

    def build_metadata(self, pattern: Dict) -> Dict:
        """Build rich metadata for pattern storage."""
        # Core metadata
        metadata = {
            "type": pattern.get("type", "unknown"),
            "pattern_id": pattern.get("pattern_id"),
            "project": self.project_name,
            "session": self.session_id,
            "timestamp": pattern.get("timestamp", time.time()),
            "confidence": pattern.get("confidence", 0.5)
        }

        # Type-specific metadata
        pattern_type = pattern.get("type", "")

        if pattern_type == "file_coupling":
            metadata["files"] = pattern.get("files", [])
            metadata["frequency"] = pattern.get("frequency", 1)

        elif pattern_type == "test_coverage":
            metadata["file"] = pattern.get("file")
            metadata["coverage"] = pattern.get("coverage")
            metadata["line_coverage"] = pattern.get("line_coverage")

        elif pattern_type == "command_error":
            metadata["command"] = pattern.get("command")
            metadata["exit_code"] = pattern.get("exit_code")

        # Include context if provided
        if "context" in pattern:
            metadata["context"] = pattern["context"]

        # Store full pattern for recovery if needed
        metadata["full_pattern"] = pattern

        return metadata

    def learn_pattern(self, pattern_data: Dict) -> bool:
        """Learn pattern with semantic content extraction."""
        # Enrich pattern with context
        pattern_data["session_id"] = self.session_id
        pattern_data["project"] = self.project_name
        pattern_data["timestamp"] = time.time()
        pattern_data["pattern_id"] = self.generate_pattern_id(pattern_data)

        # Validate pattern
        if not self.is_valid_pattern(pattern_data):
            return False

        # Check for contradictions
        contradiction = self.check_contradictions(pattern_data)
        if contradiction:
            pattern_data = self.resolve_contradiction(pattern_data, contradiction)

        # Extract semantic content
        semantic_content = self.extract_semantic_content(pattern_data)

        # Build metadata
        metadata = self.build_metadata(pattern_data)

        # Determine memory tier
        tier = self.determine_memory_tier(pattern_data)

        # Store in PRISM with semantic content
        result = self.prism.store_memory(
            content=semantic_content,  # <-- Semantic content, not JSON!
            tier=tier,
            metadata=metadata
        )

        success = result.get("success", False)

        if success:
            # Store relationships in Neo4j
            relationships = self.extract_relationships(pattern_data)
            if relationships:
                self.graph_store.store_relationships(relationships)

            # Cache in Redis with type-specific TTL
            pattern_type = pattern_data.get("type", "")
            ttl_config = self.config["caching"]["redis_ttl_by_type"]
            ttl = ttl_config.get(pattern_type, ttl_config.get("default", 3600))

            self.temporal_cache.cache_pattern(
                pattern_data["pattern_id"],
                pattern_data,
                ttl=ttl
            )

            # Update local cache
            self.update_pattern_cache(pattern_data["pattern_id"], pattern_data)

        return success

    def search_patterns(self, query: str, mode: str = "hybrid", limit: int = None) -> List[Dict]:
        """Multi-mode pattern search."""
        # Use configured limits
        if limit is None:
            limit = self.config["search"]["result_limits"].get(mode,
                    self.config["search"]["result_limits"]["default"])

        results = []
        seen_ids = set()

        if mode in ["semantic", "hybrid"]:
            # Semantic search via PRISM
            semantic_results = self.prism.search_memory(query, limit=limit)
            for result in semantic_results:
                if result.get("key") not in seen_ids:
                    results.append(result)
                    seen_ids.add(result.get("key"))

        if mode in ["graph", "hybrid"]:
            # Graph traversal for relationships
            related = self.graph_store.find_related(query, depth=2)
            for rel in related:
                # Search for patterns related to these entities
                entity_patterns = self.prism.search_memory(
                    rel.get("related", ""),
                    limit=5
                )
                for pattern in entity_patterns:
                    if pattern.get("key") not in seen_ids:
                        results.append(pattern)
                        seen_ids.add(pattern.get("key"))

        if mode in ["cache", "hybrid"]:
            # Check temporal cache for recent patterns
            # This would need to track pattern IDs in session
            pass

        # Rank and merge results
        return self.rank_results(results, query)[:limit]

    def rank_results(self, results: List[Dict], query: str) -> List[Dict]:
        """Rank search results by relevance."""
        # Simple ranking by score if available
        for result in results:
            if "score" not in result:
                result["score"] = 0.5

        return sorted(results, key=lambda x: x.get("score", 0), reverse=True)

    def get_relevant_memories(self, context: Dict, limit: int = 5) -> List[Dict]:
        """Get relevant memories using multi-mode search."""
        # Primary query from context
        if context.get("query"):
            # Use the query directly for semantic search
            return self.search_patterns(context["query"], mode="hybrid", limit=limit)

        # Build queries from context
        queries = []

        if context.get("file"):
            # Find patterns related to this file
            file_patterns = self.search_patterns(context["file"], mode="hybrid", limit=limit)

            # Also find coupled files through graph
            related_files = self.graph_store.find_related(
                context["file"],
                rel_type="COUPLED_WITH",
                depth=1
            )
            for rel in related_files:
                file_patterns.extend(
                    self.search_patterns(rel["related"], mode="semantic", limit=3)
                )

            return file_patterns[:limit]

        if context.get("error"):
            # Find error fixes through graph
            fixes = self.graph_store.find_related(
                context["error"],
                rel_type="FIXED_BY",
                depth=1
            )
            if fixes:
                return self.search_patterns(fixes[0]["related"], mode="semantic", limit=limit)

        # Fallback to type-based search
        if context.get("type"):
            type_query = f"{context['type']} patterns in {self.project_name}"
            return self.search_patterns(type_query, mode="semantic", limit=limit)

        return []

    # Keep existing helper methods
    def generate_pattern_id(self, pattern_data: Dict) -> str:
        """Generate deterministic pattern ID."""
        key_parts = [
            str(pattern_data.get("type", "")),
            str(pattern_data.get("content", ""))[:100],
            str(pattern_data.get("project", ""))
        ]
        key_string = "|".join(key_parts)
        return hashlib.sha256(key_string.encode()).hexdigest()[:12]

    def get_session_id(self) -> str:
        """Get or create session ID."""
        session_file = self.cache_dir / "session_id"
        if session_file.exists():
            session_data = json.loads(session_file.read_text())
            # Check if session is still valid (within 24 hours)
            if time.time() - session_data.get("timestamp", 0) < 86400:
                return session_data["id"]

        # Create new session
        session_id = f"session_{int(time.time())}"
        session_file.write_text(json.dumps({
            "id": session_id,
            "timestamp": time.time()
        }))
        return session_id

    def get_current_project(self) -> str:
        """Detect current project from git or directory."""
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--show-toplevel"],
                capture_output=True,
                text=True,
                timeout=1
            )
            if result.returncode == 0:
                return Path(result.stdout.strip()).name
        except:
            pass

        return Path.cwd().name

    def load_pattern_cache(self) -> Dict:
        """Load local pattern cache."""
        cache_file = self.cache_dir / "pattern_cache.json"
        if cache_file.exists():
            try:
                return json.loads(cache_file.read_text())
            except:
                pass
        return {"patterns": {}, "validations": {}}

    def update_pattern_cache(self, pattern_id: str, pattern_data: Dict):
        """Update local pattern cache."""
        self.pattern_cache["patterns"][pattern_id] = {
            "data": pattern_data,
            "timestamp": time.time(),
            "usage_count": self.pattern_cache["patterns"].get(pattern_id, {}).get("usage_count", 0) + 1
        }
        self.save_pattern_cache()

    def save_pattern_cache(self):
        """Save pattern cache to disk."""
        cache_file = self.cache_dir / "pattern_cache.json"
        cache_file.write_text(json.dumps(self.pattern_cache, default=str))

    def is_valid_pattern(self, pattern_data: Dict) -> bool:
        """Validate if pattern is worth learning."""
        # Check required fields
        if not pattern_data.get("type"):
            return False

        # Check if content can be extracted
        semantic_content = self.extract_semantic_content(pattern_data)
        min_length = self.config["validation"]["content_quality"]["min_length"]
        if not semantic_content or len(semantic_content) < min_length:
            return False

        # Check for hallucination based on pattern type
        pattern_type = pattern_data.get("type", "")
        risk_config = self.config["validation"]["hallucination_risk_threshold"]

        # Use stricter thresholds for security patterns
        if pattern_type in ["security", "critical"]:
            risk_threshold = risk_config.get("security", risk_config["default"])
        else:
            risk_threshold = risk_config.get("default", 0.7)

        analysis = self.prism.analyze(semantic_content)
        if analysis.get("hallucination_risk", 1.0) > risk_threshold:
            return False

        # Check confidence threshold
        min_conf_config = self.config["validation"]["min_confidence"]
        min_confidence = min_conf_config.get("default", 0.3)
        if pattern_data.get("confidence", 0) < min_confidence:
            return False

        return True

    def check_contradictions(self, pattern_data: Dict) -> Optional[Dict]:
        """Check for contradictory patterns."""
        # Search for similar patterns
        semantic_content = self.extract_semantic_content(pattern_data)
        similar = self.search_patterns(semantic_content, mode="semantic", limit=5)

        # Check for contradictions in metadata
        for existing in similar:
            if existing.get("score", 0) > 0.8:  # High similarity
                existing_meta = existing.get("metadata", {})
                if existing_meta.get("type") == pattern_data.get("type"):
                    # Check for conflicting values
                    # This would need domain-specific logic
                    pass

        return None

    def resolve_contradiction(self, pattern_data: Dict, contradiction: Dict) -> Dict:
        """Resolve contradictions between patterns."""
        # For now, just mark as evolution
        pattern_data["evolves_from"] = contradiction.get("pattern_id")
        return pattern_data

    def determine_memory_tier(self, pattern_data: Dict) -> str:
        """Determine appropriate memory tier using optimized thresholds."""
        confidence = pattern_data.get("confidence", 0.5)
        pattern_type = pattern_data.get("type", "")

        # Use configured tier settings
        tier_config = self.config.get("memory_tiers", {})

        # Check each tier from highest to lowest priority
        if tier_config.get("ANCHORS"):
            anchors_conf = tier_config["ANCHORS"]["min_confidence"]
            anchors_types = tier_config["ANCHORS"]["types"]
            if pattern_type in anchors_types and confidence >= anchors_conf:
                return "ANCHORS"

        if tier_config.get("LONGTERM"):
            longterm_conf = tier_config["LONGTERM"]["min_confidence"]
            longterm_types = tier_config["LONGTERM"]["types"]
            if pattern_type in longterm_types and confidence >= longterm_conf:
                return "LONGTERM"

        if tier_config.get("EPISODIC"):
            episodic_conf = tier_config["EPISODIC"]["min_confidence"]
            episodic_types = tier_config["EPISODIC"]["types"]
            if (pattern_type in episodic_types or "session" in pattern_data) and confidence >= episodic_conf:
                return "EPISODIC"

        # Default to WORKING for everything else
        return "WORKING"

    def promote_pattern(self, pattern_id: str, new_confidence: float = None):
        """Promote pattern to higher tier based on usage."""
        # Get cached pattern
        cached = self.pattern_cache["patterns"].get(pattern_id, {})
        if not cached:
            return

        pattern_data = cached.get("data", {})
        usage_count = cached.get("usage_count", 0)

        # Update confidence based on usage
        if new_confidence is None:
            new_confidence = min(0.95, pattern_data.get("confidence", 0.5) + (usage_count * 0.05))

        pattern_data["confidence"] = new_confidence

        # Re-learn with new confidence (will update tier)
        self.learn_pattern(pattern_data)


# Singleton instance
_learner_instance = None

def get_learner() -> UniversalLearner:
    """Get or create universal learner instance."""
    global _learner_instance
    if _learner_instance is None:
        _learner_instance = UniversalLearner()
    return _learner_instance