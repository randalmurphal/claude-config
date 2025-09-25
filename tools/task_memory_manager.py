#!/usr/bin/env python3
"""
Task Memory Lifecycle Manager for PRISM-powered orchestration.
Prevents memory pollution by managing task-scoped namespaces with intelligent
pattern abstraction, promotion rules, and automatic cleanup.
"""

import json
import re
import hashlib
import time
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class TaskMemory:
    """Represents a memory item within a task namespace."""
    key: str
    content: str
    tier: str
    task_id: str
    created_at: float
    accessed_count: int = 0
    last_accessed: float = None
    importance_score: float = 0.0
    reusability_score: float = 0.0
    abstracted: bool = False
    metadata: Dict[str, Any] = None

    def to_dict(self) -> Dict:
        return asdict(self)


class PatternAbstractor:
    """Abstracts project-specific details from patterns before storage."""

    # Patterns to abstract
    PATH_PATTERNS = [
        (r'/home/[\w-]+/[\w/.-]+', '~/[project]'),  # User home paths
        (r'/Users/[\w-]+/[\w/.-]+', '~/[project]'),  # Mac paths
        (r'C:\\Users\\[\w-]+\\[\w\\.-]+', 'C:\\[project]'),  # Windows paths
        (r'/tmp/[\w/.-]+', '/tmp/[temp]'),  # Temp paths
        (r'/var/[\w/.-]+', '/var/[system]'),  # System paths
    ]

    PROJECT_SPECIFIC_PATTERNS = [
        # Variable/function names with specific entities
        (r'validate_(\w+)_(\w+)', 'validate_[entity]_[attribute]'),
        (r'process_(\w+)_data', 'process_[entity]_data'),
        (r'handle_(\w+)_error', 'handle_[type]_error'),
        (r'fetch_(\w+)_from_(\w+)', 'fetch_[entity]_from_[source]'),

        # Specific IDs and keys
        (r'[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}', '[uuid]'),
        (r'[A-Z0-9]{20,}', '[api_key]'),
        (r'\b\d{4,}\b', '[id]'),

        # Email addresses
        (r'[\w.-]+@[\w.-]+\.\w+', '[email]'),

        # URLs with specific domains
        (r'https?://[\w.-]+\.[\w]+/[\w/.-]*', '[url]'),

        # IP addresses
        (r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b', '[ip_address]'),
    ]

    BUSINESS_LOGIC_KEYWORDS = [
        'customer', 'user', 'order', 'product', 'invoice', 'payment',
        'subscription', 'tenant', 'organization', 'company', 'employee'
    ]

    def abstract_content(self, content: str, file_path: Optional[str] = None) -> Tuple[str, bool]:
        """
        Abstract project-specific details from content.
        Returns: (abstracted_content, was_abstracted)
        """
        original = content
        abstracted = content

        # Abstract file paths
        for pattern, replacement in self.PATH_PATTERNS:
            abstracted = re.sub(pattern, replacement, abstracted, flags=re.IGNORECASE)

        # Abstract project-specific patterns
        for pattern, replacement in self.PROJECT_SPECIFIC_PATTERNS:
            abstracted = re.sub(pattern, replacement, abstracted, flags=re.IGNORECASE)

        # Check for business logic that shouldn't be stored globally
        has_business_logic = any(
            keyword in abstracted.lower()
            for keyword in self.BUSINESS_LOGIC_KEYWORDS
        )

        if has_business_logic:
            # Replace business entities with generic placeholders
            for keyword in self.BUSINESS_LOGIC_KEYWORDS:
                abstracted = re.sub(
                    rf'\b{keyword}\b',
                    '[entity]',
                    abstracted,
                    flags=re.IGNORECASE
                )

        # Abstract the file path if provided
        if file_path:
            file_name = Path(file_path).name
            file_ext = Path(file_path).suffix
            abstracted_path = f"*/*/{file_name}" if '/' in file_path else file_name
            abstracted = abstracted.replace(file_path, abstracted_path)

        was_abstracted = abstracted != original
        return abstracted, was_abstracted

    def extract_pattern_type(self, content: str) -> str:
        """Identify the type of pattern from content."""
        content_lower = content.lower()

        # Security patterns
        if any(word in content_lower for word in ['auth', 'password', 'token', 'security', 'encrypt']):
            return 'security_pattern'

        # Validation patterns
        if any(word in content_lower for word in ['validate', 'verify', 'check', 'assert']):
            return 'validation_pattern'

        # Error handling patterns
        if any(word in content_lower for word in ['error', 'exception', 'catch', 'handle']):
            return 'error_handling_pattern'

        # Performance patterns
        if any(word in content_lower for word in ['cache', 'optimize', 'batch', 'async', 'pool']):
            return 'performance_pattern'

        # Architecture patterns
        if any(word in content_lower for word in ['factory', 'singleton', 'observer', 'decorator']):
            return 'design_pattern'

        return 'general_pattern'


class MemoryPromoter:
    """Handles promotion of task memories to global scope."""

    def __init__(self):
        self.promotion_threshold = {
            'usage_count': 2,  # Used at least twice
            'reusability_score': 0.7,  # High reusability
            'importance_score': 0.6,  # Moderate importance
            'abstraction_required': True  # Must be abstracted
        }

    def evaluate_for_promotion(self, memory: TaskMemory) -> Tuple[bool, str]:
        """
        Evaluate if a task memory should be promoted to global.
        Returns: (should_promote, reason)
        """
        # Check usage count
        if memory.accessed_count < self.promotion_threshold['usage_count']:
            return False, f"Insufficient usage ({memory.accessed_count} < {self.promotion_threshold['usage_count']})"

        # Check reusability
        if memory.reusability_score < self.promotion_threshold['reusability_score']:
            return False, f"Low reusability ({memory.reusability_score:.2f} < {self.promotion_threshold['reusability_score']})"

        # Check importance
        if memory.importance_score < self.promotion_threshold['importance_score']:
            return False, f"Low importance ({memory.importance_score:.2f} < {self.promotion_threshold['importance_score']})"

        # Must be abstracted (no project-specific details)
        if self.promotion_threshold['abstraction_required'] and not memory.abstracted:
            return False, "Not abstracted (contains project-specific details)"

        # Check for specific paths or IDs that shouldn't be global
        if self._contains_specific_data(memory.content):
            return False, "Contains specific data that cannot be generalized"

        return True, "Meets all promotion criteria"

    def _contains_specific_data(self, content: str) -> bool:
        """Check if content contains data that's too specific to be global."""
        # Check for absolute paths
        if re.search(r'^/home/|^/Users/|^C:\\Users', content):
            return True

        # Check for specific project names or IDs
        if re.search(r'project\d+|test\d+|temp\d+', content, re.IGNORECASE):
            return True

        # Check for hardcoded credentials or keys
        if re.search(r'password\s*=\s*["\'][^"\']+["\']', content, re.IGNORECASE):
            return True

        return False

    def calculate_reusability_score(self, memory: TaskMemory) -> float:
        """Calculate how reusable a memory pattern is."""
        score = 0.0

        # Abstract patterns are more reusable
        if memory.abstracted:
            score += 0.3

        # Frequently accessed patterns are likely reusable
        if memory.accessed_count > 1:
            score += min(0.2 * memory.accessed_count, 0.4)

        # Certain pattern types are inherently reusable
        pattern_type = PatternAbstractor().extract_pattern_type(memory.content)
        reusable_types = ['validation_pattern', 'error_handling_pattern',
                         'security_pattern', 'design_pattern']
        if pattern_type in reusable_types:
            score += 0.3

        return min(score, 1.0)


class SemanticDeduplicator:
    """Handles semantic deduplication of memories."""

    def __init__(self, similarity_threshold: float = 0.85):
        self.similarity_threshold = similarity_threshold

    def find_similar(self, content: str, existing_memories: List[TaskMemory]) -> Optional[TaskMemory]:
        """Find semantically similar memory if exists."""
        # Simple implementation using keyword matching
        # In production, this would use embeddings from PRISM
        content_keywords = self._extract_keywords(content)

        for memory in existing_memories:
            memory_keywords = self._extract_keywords(memory.content)
            similarity = self._calculate_similarity(content_keywords, memory_keywords)

            if similarity >= self.similarity_threshold:
                return memory

        return None

    def _extract_keywords(self, text: str) -> set:
        """Extract meaningful keywords from text."""
        # Remove common words and extract significant terms
        common_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at',
                       'to', 'for', 'of', 'with', 'by', 'from', 'as', 'is', 'was',
                       'are', 'were', 'been', 'be', 'have', 'has', 'had', 'do',
                       'does', 'did', 'will', 'would', 'could', 'should', 'may',
                       'might', 'must', 'can', 'this', 'that', 'these', 'those'}

        words = re.findall(r'\b\w+\b', text.lower())
        keywords = {word for word in words if word not in common_words and len(word) > 2}

        return keywords

    def _calculate_similarity(self, keywords1: set, keywords2: set) -> float:
        """Calculate Jaccard similarity between keyword sets."""
        if not keywords1 or not keywords2:
            return 0.0

        intersection = keywords1 & keywords2
        union = keywords1 | keywords2

        return len(intersection) / len(union) if union else 0.0


class TaskMemoryManager:
    """Main manager for task-scoped memory lifecycle."""

    def __init__(self, prism_client=None):
        self.prism_client = prism_client
        self.abstractor = PatternAbstractor()
        self.promoter = MemoryPromoter()
        self.deduplicator = SemanticDeduplicator()

        # Memory storage (in production, this would use PRISM/Redis)
        self.task_memories: Dict[str, List[TaskMemory]] = {}
        self.global_memories: List[TaskMemory] = []

        # Expiry rules by tier
        self.expiry_rules = {
            "WORKING": {"ttl": "task_complete", "description": "Expires when task completes"},
            "EPISODIC": {"ttl": 30, "unit": "days", "unless_accessed": True},
            "LONGTERM": {"ttl": 365, "unit": "days", "min_accesses": 3},
            "ANCHORS": {"ttl": None, "description": "Never expires"}
        }

    def create_task_namespace(self, task_id: str, description: str) -> Dict[str, Any]:
        """Create a new task namespace with automatic expiry."""
        namespace_key = f"task:{task_id}"

        # Initialize task memory list
        self.task_memories[task_id] = []

        # Store task mission as ANCHOR within task namespace
        mission_memory = TaskMemory(
            key=f"{namespace_key}:mission",
            content=description,
            tier="ANCHORS",
            task_id=task_id,
            created_at=time.time(),
            importance_score=1.0,
            reusability_score=0.0,  # Missions are task-specific
            abstracted=False,
            metadata={"type": "mission", "original": True}
        )

        self.task_memories[task_id].append(mission_memory)

        logger.info(f"Created namespace for task {task_id}")

        return {
            "namespace": namespace_key,
            "created_at": datetime.now().isoformat(),
            "expiry": "24 hours after task completion",
            "mission_stored": True
        }

    def store_task_memory(self, task_id: str, content: str, tier: str = "WORKING",
                          metadata: Optional[Dict] = None) -> Dict[str, Any]:
        """Store a memory in task namespace with abstraction."""
        if task_id not in self.task_memories:
            return {"error": f"Task {task_id} namespace not found"}

        # Abstract the content
        abstracted_content, was_abstracted = self.abstractor.abstract_content(content)

        # Check for semantic duplicates in task namespace
        existing_similar = self.deduplicator.find_similar(
            abstracted_content,
            self.task_memories[task_id]
        )

        if existing_similar:
            # Increment usage instead of creating duplicate
            existing_similar.accessed_count += 1
            existing_similar.last_accessed = time.time()

            return {
                "action": "incremented_existing",
                "memory_key": existing_similar.key,
                "accessed_count": existing_similar.accessed_count
            }

        # Create new memory
        memory_key = f"task:{task_id}:{hashlib.md5(abstracted_content.encode()).hexdigest()[:8]}"

        memory = TaskMemory(
            key=memory_key,
            content=abstracted_content,
            tier=tier,
            task_id=task_id,
            created_at=time.time(),
            abstracted=was_abstracted,
            importance_score=self._calculate_importance(abstracted_content, metadata),
            reusability_score=0.0,  # Will be calculated on access
            metadata=metadata or {}
        )

        # Calculate initial reusability
        memory.reusability_score = self.promoter.calculate_reusability_score(memory)

        self.task_memories[task_id].append(memory)

        logger.info(f"Stored memory {memory_key} in task {task_id} namespace")

        return {
            "action": "stored",
            "memory_key": memory_key,
            "abstracted": was_abstracted,
            "tier": tier,
            "importance_score": memory.importance_score,
            "reusability_score": memory.reusability_score
        }

    def access_task_memory(self, task_id: str, pattern: str) -> List[Dict[str, Any]]:
        """Access memories matching pattern, updating access counts."""
        if task_id not in self.task_memories:
            return []

        matches = []
        pattern_lower = pattern.lower()

        for memory in self.task_memories[task_id]:
            if pattern_lower in memory.content.lower():
                # Update access tracking
                memory.accessed_count += 1
                memory.last_accessed = time.time()

                # Recalculate reusability based on access pattern
                memory.reusability_score = self.promoter.calculate_reusability_score(memory)

                matches.append({
                    "key": memory.key,
                    "content": memory.content,
                    "tier": memory.tier,
                    "accessed_count": memory.accessed_count,
                    "importance": memory.importance_score,
                    "reusability": memory.reusability_score
                })

        return matches

    def complete_task(self, task_id: str) -> Dict[str, Any]:
        """Complete a task, promoting reusable patterns and purging the rest."""
        if task_id not in self.task_memories:
            return {"error": f"Task {task_id} not found"}

        task_memories = self.task_memories[task_id]
        promoted = []
        purged = []

        for memory in task_memories:
            # Skip mission memories (they're task-specific)
            if memory.metadata and memory.metadata.get("type") == "mission":
                purged.append(memory.key)
                continue

            # Evaluate for promotion
            should_promote, reason = self.promoter.evaluate_for_promotion(memory)

            if should_promote:
                # Check for duplicates in global memories
                existing_global = self.deduplicator.find_similar(
                    memory.content,
                    self.global_memories
                )

                if existing_global:
                    # Update existing global memory
                    existing_global.accessed_count += memory.accessed_count
                    existing_global.last_accessed = time.time()
                    promoted.append({
                        "action": "merged_with_existing",
                        "global_key": existing_global.key,
                        "original_key": memory.key
                    })
                else:
                    # Promote to global
                    global_memory = TaskMemory(
                        key=f"global:{memory.key.split(':')[-1]}",
                        content=memory.content,
                        tier="LONGTERM" if memory.importance_score > 0.7 else "EPISODIC",
                        task_id="global",
                        created_at=time.time(),
                        accessed_count=memory.accessed_count,
                        importance_score=memory.importance_score,
                        reusability_score=memory.reusability_score,
                        abstracted=True,
                        metadata={
                            **memory.metadata,
                            "promoted_from": task_id,
                            "promotion_reason": reason
                        }
                    )

                    self.global_memories.append(global_memory)
                    promoted.append({
                        "action": "promoted",
                        "global_key": global_memory.key,
                        "original_key": memory.key,
                        "reason": reason
                    })
            else:
                purged.append(memory.key)
                logger.debug(f"Not promoting {memory.key}: {reason}")

        # Clear task namespace
        del self.task_memories[task_id]

        logger.info(f"Completed task {task_id}: {len(promoted)} promoted, {len(purged)} purged")

        return {
            "task_id": task_id,
            "memories_processed": len(task_memories),
            "promoted_count": len(promoted),
            "purged_count": len(purged),
            "promoted_memories": promoted[:5],  # Show first 5
            "timestamp": datetime.now().isoformat()
        }

    def garbage_collect(self) -> Dict[str, Any]:
        """Run garbage collection on memories based on expiry rules."""
        current_time = time.time()
        expired = []
        retained = []

        # Check global memories for expiry
        remaining_memories = []

        for memory in self.global_memories:
            tier_rules = self.expiry_rules.get(memory.tier, {})

            # Check TTL
            if tier_rules.get("ttl") and isinstance(tier_rules["ttl"], int):
                ttl_seconds = tier_rules["ttl"] * 86400  # Convert days to seconds
                age = current_time - memory.created_at

                if age > ttl_seconds:
                    # Check minimum access requirement
                    min_accesses = tier_rules.get("min_accesses", 0)
                    if memory.accessed_count < min_accesses:
                        expired.append(memory.key)
                        continue

                    # Check if recently accessed (for EPISODIC tier)
                    if tier_rules.get("unless_accessed") and memory.last_accessed:
                        time_since_access = current_time - memory.last_accessed
                        if time_since_access < ttl_seconds / 2:  # Recently accessed
                            retained.append(memory.key)
                            remaining_memories.append(memory)
                            continue

                    expired.append(memory.key)
                    continue

            remaining_memories.append(memory)

        self.global_memories = remaining_memories

        logger.info(f"Garbage collection: {len(expired)} expired, {len(retained)} retained")

        return {
            "expired_count": len(expired),
            "retained_count": len(retained),
            "expired_keys": expired[:10],  # Show first 10
            "total_global_memories": len(self.global_memories),
            "timestamp": datetime.now().isoformat()
        }

    def _calculate_importance(self, content: str, metadata: Optional[Dict]) -> float:
        """Calculate importance score for a memory."""
        score = 0.0

        # Pattern type importance
        pattern_type = self.abstractor.extract_pattern_type(content)
        importance_by_type = {
            'security_pattern': 0.9,
            'error_handling_pattern': 0.7,
            'validation_pattern': 0.6,
            'performance_pattern': 0.7,
            'design_pattern': 0.8,
            'general_pattern': 0.4
        }
        score = importance_by_type.get(pattern_type, 0.4)

        # Metadata importance modifiers
        if metadata:
            if metadata.get("fixes_bug"):
                score += 0.2
            if metadata.get("prevents_error"):
                score += 0.2
            if metadata.get("improves_performance"):
                score += 0.15

        return min(score, 1.0)

    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about memory usage."""
        total_task_memories = sum(len(memories) for memories in self.task_memories.values())

        tier_distribution = {"WORKING": 0, "EPISODIC": 0, "LONGTERM": 0, "ANCHORS": 0}
        for memory in self.global_memories:
            tier_distribution[memory.tier] = tier_distribution.get(memory.tier, 0) + 1

        return {
            "active_tasks": len(self.task_memories),
            "total_task_memories": total_task_memories,
            "global_memories": len(self.global_memories),
            "tier_distribution": tier_distribution,
            "average_reusability": (
                sum(m.reusability_score for m in self.global_memories) / len(self.global_memories)
                if self.global_memories else 0.0
            ),
            "average_importance": (
                sum(m.importance_score for m in self.global_memories) / len(self.global_memories)
                if self.global_memories else 0.0
            )
        }


# Example usage and testing
def test_memory_manager():
    """Test the memory manager with example scenarios."""
    manager = TaskMemoryManager()

    # Create a task
    task_id = "task_001"
    manager.create_task_namespace(task_id, "Implement authentication system")

    # Store various memories
    memories_to_store = [
        ("Fixed bug in ~/project/auth/login.py line 47", "EPISODIC"),
        ("Password hashing pattern using bcrypt", "LONGTERM"),
        ("validate_user_email function for input validation", "WORKING"),
        ("JWT token validation pattern", "LONGTERM"),
        ("Fixed SQL injection in user query", "LONGTERM"),
    ]

    print("Storing memories...")
    for content, tier in memories_to_store:
        result = manager.store_task_memory(task_id, content, tier)
        print(f"  - {result}")

    # Access some memories (simulating usage)
    print("\nAccessing memories...")
    results = manager.access_task_memory(task_id, "validation")
    for result in results:
        print(f"  - Found: {result['key']}")

    # Access again to increase count
    manager.access_task_memory(task_id, "password")
    manager.access_task_memory(task_id, "JWT")

    # Complete the task
    print("\nCompleting task...")
    completion_result = manager.complete_task(task_id)
    print(f"Promoted: {completion_result['promoted_count']}")
    print(f"Purged: {completion_result['purged_count']}")

    # Check statistics
    print("\nFinal statistics:")
    stats = manager.get_statistics()
    for key, value in stats.items():
        print(f"  {key}: {value}")


if __name__ == "__main__":
    test_memory_manager()