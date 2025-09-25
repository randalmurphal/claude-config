#!/usr/bin/env python3
"""
Unified Context Provider Hook - PRISM Memory Only
==================================================
Provides rich semantic context from PRISM memory to improve code quality.
NO file-based fallbacks - only uses PRISM for all memory storage.

Key Features:
- Extracts semantic intent from user messages
- Retrieves relevant memories from ALL PRISM tiers
- Injects context for both solo work and agent launches
- Learns patterns continuously from development
- Filters ephemeral files to reduce noise
"""

import json
import sys
import time
import logging
import os
import re
import difflib
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from collections import defaultdict
from datetime import datetime, timedelta

# Import PRISM client, universal learner, and preference manager
sys.path.append(str(Path(__file__).parent))
from prism_client import get_prism_client
from universal_learner import get_learner
from preference_manager import get_preference_manager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
RELEVANCE_THRESHOLD = 0.3  # Raised for less noise
CONFIDENCE_THRESHOLD = 0.8
LEARNING_INTERVAL_OPS = 10
LEARNING_INTERVAL_SECONDS = 300

# Ephemeral patterns to skip
EPHEMERAL_PATTERNS = [
    r'^/tmp/',
    r'^/var/',
    r'\.pyc$',
    r'__pycache__',
    r'^\.git/',
    r'node_modules/',
    r'venv/',
    r'\.venv/',
    r'build/',
    r'dist/',
    r'\.egg-info/',
    r'\.pytest_cache/',
    r'\.coverage',
    r'\.tox/'
]

class UnifiedContextProvider:
    """PRISM-only context provider with semantic learning."""

    def __init__(self):
        self.client = get_prism_client()
        self.learner = get_learner()
        self.preference_manager = get_preference_manager()
        self.last_learning_time = time.time()
        self.operation_count = 0
        self.current_session_id = f"session_{int(time.time())}"
        self.architecture_cache = {}
        self.recent_operations = []  # In-memory only for current session

    def should_skip_file(self, file_path: str) -> bool:
        """Check if file should be skipped from memory storage."""
        if not file_path:
            return True

        for pattern in EPHEMERAL_PATTERNS:
            if re.search(pattern, file_path):
                return True
        return False

    def extract_intent(self, text: str) -> Tuple[str, float]:
        """Extract semantic intent from user message or agent prompt."""
        text_lower = text.lower()

        # Intent patterns with confidence scores
        intent_patterns = [
            # High confidence patterns
            (r'\b(fix|repair|resolve|debug)\b.*\b(bug|issue|error|problem)\b', 'bug_fix', 0.95),
            (r'\b(implement|add|create)\b.*\b(feature|functionality|capability)\b', 'feature_implementation', 0.9),
            (r'\b(refactor|clean|improve|optimize)\b.*\b(code|function|class|module)\b', 'refactoring', 0.9),
            (r'\b(test|testing|unit test|integration test)\b', 'testing', 0.9),
            (r'\b(analyze|investigate|understand|explore)\b', 'analysis', 0.85),
            (r'\b(document|documentation|readme|comment)\b', 'documentation', 0.85),

            # Medium confidence patterns
            (r'\b(update|modify|change|edit)\b', 'modification', 0.7),
            (r'\b(review|check|verify|validate)\b', 'review', 0.7),
            (r'\b(deploy|build|compile|package)\b', 'deployment', 0.7),

            # Specific task patterns
            (r'\b(integration|integrate)\b.*\b(test|testing)\b', 'integration_testing', 0.95),
            (r'\btenable\b.*\b(test|integration|import)\b', 'tenable_integration', 0.95),
            (r'\b(performance|speed|slow|optimize)\b', 'performance', 0.85),
            (r'\b(security|vulnerability|auth|authentication)\b', 'security', 0.9),
        ]

        for pattern, intent, confidence in intent_patterns:
            if re.search(pattern, text_lower):
                return intent, confidence

        # Fallback intent
        if any(word in text_lower for word in ['help', 'assist', 'can you']):
            return 'assistance', 0.6

        return 'general', 0.5

    def retrieve_relevant_context(self, intent: str, query: str, is_agent: bool = False) -> List[Dict]:
        """Retrieve relevant context from PRISM memory."""
        if not self.client:
            return []

        relevant_context = []

        try:
            # Build semantic search query
            search_query = f"{intent} {query}"

            # Search across all tiers with different priorities
            tier_priorities = [
                ('ANCHORS', 1.0),    # Critical decisions and invariants
                ('LONGTERM', 0.9),   # Stable patterns and learnings
                ('WORKING', 0.8),    # Current session context
                ('EPISODIC', 0.7),   # Recent activities
            ]

            for tier, weight in tier_priorities:
                try:
                    results = self.client.search_memory(
                        query=search_query,
                        tier=tier,
                        limit=5
                    )

                    for result in results:
                        score = result.get('score', 0) * weight
                        if score > RELEVANCE_THRESHOLD:
                            result['tier'] = tier
                            result['weighted_score'] = score
                            relevant_context.append(result)
                except Exception as e:
                    logger.debug(f"Failed to search {tier}: {e}")

            # Sort by weighted score
            relevant_context.sort(key=lambda x: x.get('weighted_score', 0), reverse=True)

        except Exception as e:
            logger.debug(f"Failed to retrieve context: {e}")

        return relevant_context[:10]  # Return top 10 most relevant

    def extract_semantic_diff(self, old_content: str, new_content: str, file_path: str) -> Dict:
        """Extract semantic meaning from code changes."""
        diff_lines = list(difflib.unified_diff(
            old_content.splitlines(keepends=True),
            new_content.splitlines(keepends=True),
            fromfile=file_path,
            tofile=file_path,
            lineterm=''
        ))

        if not diff_lines:
            return None

        # Analyze what changed
        added_lines = [l[1:] for l in diff_lines if l.startswith('+') and not l.startswith('+++')]
        removed_lines = [l[1:] for l in diff_lines if l.startswith('-') and not l.startswith('---')]

        # Detect patterns in changes
        semantic_changes = []

        # Error handling additions
        if any('try:' in l or 'except' in l for l in added_lines):
            semantic_changes.append("added_error_handling")

        # Import changes
        added_imports = [l for l in added_lines if re.match(r'^\s*(import |from .* import)', l)]
        if added_imports:
            semantic_changes.append(f"added_imports: {', '.join([i.strip() for i in added_imports[:3]])}")

        # Function/method additions
        added_functions = [l for l in added_lines if re.match(r'^\s*def \w+', l)]
        if added_functions:
            func_names = [re.search(r'def (\w+)', f).group(1) for f in added_functions]
            semantic_changes.append(f"added_functions: {', '.join(func_names[:3])}")

        # Test additions
        if any('assert' in l or 'test_' in l for l in added_lines):
            semantic_changes.append("added_tests")

        # Bug fix patterns
        if removed_lines and added_lines:
            # Likely a fix if we're replacing code
            semantic_changes.append("code_fix")

        return {
            "type": "code_change",
            "semantic_changes": semantic_changes,
            "added_lines_count": len(added_lines),
            "removed_lines_count": len(removed_lines),
            "summary": " | ".join(semantic_changes[:3]) if semantic_changes else "minor_changes"
        }

    def store_semantic_memory(self, operation_data: Dict):
        """Store rich semantic memory in PRISM."""
        if not self.client:
            return

        try:
            file_path = operation_data.get('file_path', '')

            # Skip ephemeral files
            if self.should_skip_file(file_path):
                return

            # Determine memory tier based on content
            operation = operation_data.get('operation', '')
            tier = 'WORKING'  # Default tier

            # Critical operations go to ANCHORS
            if operation_data.get('is_critical') or 'security' in str(operation_data.get('semantic_changes', [])):
                tier = 'ANCHORS'
            # Stable patterns go to LONGTERM
            elif operation_data.get('confidence', 0) > 0.8:
                tier = 'LONGTERM'

            # Build rich semantic content
            content = {
                "type": operation_data.get('type', 'operation'),
                "content": operation_data.get('content', ''),
                "semantic": operation_data.get('semantic_changes', []),
                "entities": self.extract_entities(operation_data),
                "relationships": operation_data.get('relationships', []),
                "context": {
                    "file": file_path,
                    "operation": operation,
                    "timestamp": time.time(),
                    "session_id": self.current_session_id
                },
                "confidence": operation_data.get('confidence', 0.7)
            }

            # Store in PRISM
            self.client.store_memory(
                content=json.dumps(content),
                tier=tier,
                metadata={
                    "importance": operation_data.get('importance', 'medium'),
                    "tags": operation_data.get('tags', ['development', operation]),
                    "file_path": file_path
                }
            )

        except Exception as e:
            logger.debug(f"Failed to store semantic memory: {e}")

    def extract_entities(self, operation_data: Dict) -> List[str]:
        """Extract semantic entities from operation data."""
        entities = []

        # Extract from file path
        file_path = operation_data.get('file_path', '')
        if file_path:
            path = Path(file_path)
            entities.append(path.stem)  # File name without extension
            if 'test' in path.name:
                entities.append('test')

        # Extract from semantic changes
        for change in operation_data.get('semantic_changes', []):
            if isinstance(change, str):
                # Extract function names, imports, etc.
                if 'added_functions:' in change:
                    funcs = change.replace('added_functions:', '').strip().split(', ')
                    entities.extend(funcs[:3])
                elif 'added_imports:' in change:
                    imports = re.findall(r'import (\w+)', change)
                    entities.extend(imports[:3])

        return list(set(entities))  # Unique entities

    def format_context_for_injection(self, context: List[Dict], intent: str, confidence: float, is_agent: bool = False) -> str:
        """Format retrieved context for injection into prompts."""
        if not context:
            return ""

        sections = []

        # Header
        if is_agent:
            sections.append("## 🤖 Agent Memory Context from PRISM")
        else:
            sections.append("## 🧠 Relevant Context from Memory")

        sections.append(f"**Intent**: {intent.replace('_', ' ').title()} (confidence: {confidence:.0%})\n")

        # Group context by tier
        critical_context = [c for c in context if c.get('tier') == 'ANCHORS']
        pattern_context = [c for c in context if c.get('tier') in ['LONGTERM', 'WORKING']]
        recent_context = [c for c in context if c.get('tier') == 'EPISODIC']

        # Add critical context
        if critical_context:
            sections.append("### 🔴 Critical Knowledge")
            for ctx in critical_context[:3]:
                try:
                    content = json.loads(ctx.get('content', '{}'))
                    if isinstance(content, dict):
                        sections.append(f"- **{content.get('type', 'info')}**: {content.get('content', '')[:200]}")
                        if content.get('semantic'):
                            sections.append(f"  Changes: {', '.join(content['semantic'][:3])}")
                except:
                    sections.append(f"- {ctx.get('content', '')[:200]}")

        # Add learned patterns
        if pattern_context:
            sections.append("\n### 💡 Relevant Patterns")
            for ctx in pattern_context[:5]:
                try:
                    content = json.loads(ctx.get('content', '{}'))
                    if isinstance(content, dict):
                        if content.get('type') == 'bug_fix':
                            sections.append(f"- Bug Fix: {content.get('content', '')[:150]}")
                        elif content.get('type') == 'file_coupling':
                            sections.append(f"- Files often edited together: {content.get('content', '')[:150]}")
                        else:
                            sections.append(f"- {content.get('type', 'Pattern')}: {content.get('content', '')[:150]}")
                except:
                    pass

        # Add recent context for continuity
        if recent_context and not is_agent:  # Agents don't need recent noise
            sections.append("\n### 📝 Recent Related Work")
            for ctx in recent_context[:3]:
                try:
                    content = json.loads(ctx.get('content', '{}'))
                    if isinstance(content, dict) and content.get('context'):
                        file = Path(content['context'].get('file', '')).name
                        if file:
                            sections.append(f"- {file}: {content.get('summary', 'modified')}")
                except:
                    pass

        return "\n".join(sections) if len(sections) > 2 else ""  # Only return if we have real content

def main():
    """Main hook execution."""
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError:
        print(json.dumps({"action": "continue"}))
        sys.exit(0)

    event_type = input_data.get("hook_event_name", "")
    provider = UnifiedContextProvider()

    # UserPromptSubmit - Inject context for user messages and detect preferences
    if event_type == "UserPromptSubmit":
        user_message = input_data.get("user_message", "")
        if user_message:
            # Detect and store user preferences
            preference = provider.preference_manager.detect_preference_in_message(user_message)
            if preference:
                # Store the preference
                stored = provider.preference_manager.store_preference(preference)
                if stored and preference.get('confidence', 0) >= 0.85:
                    # Notify user that preference was stored
                    print(json.dumps({
                        "action": "assistant_message",
                        "assistant_message": f"📝 Preference noted: {provider.preference_manager.build_rule_description(preference)}"
                    }), file=sys.stderr)

            # Extract intent and inject context
            intent, confidence = provider.extract_intent(user_message)

            if confidence >= 0.6:  # Lower threshold for context injection
                context = provider.retrieve_relevant_context(intent, user_message, is_agent=False)
                formatted = provider.format_context_for_injection(context, intent, confidence, is_agent=False)

                if formatted:
                    print(json.dumps({
                        "action": "assistant_message",
                        "assistant_message": formatted
                    }), file=sys.stderr)

    # PreToolUse - Inject context for Task (agents) and track operations
    elif event_type == "PreToolUse":
        tool_name = input_data.get("tool_name", "")

        if tool_name == "Task":
            # Agent launch - inject relevant memories
            tool_input = input_data.get("tool_input", {})
            agent_prompt = tool_input.get("prompt", "")
            agent_type = tool_input.get("subagent_type", "")

            if agent_prompt:
                intent, confidence = provider.extract_intent(agent_prompt)
                search_query = f"{agent_type} {agent_prompt}"
                context = provider.retrieve_relevant_context(intent, search_query, is_agent=True)

                if context:
                    formatted = provider.format_context_for_injection(context, intent, confidence, is_agent=True)
                    if formatted:
                        # Inject context into agent prompt
                        enhanced_prompt = f"{formatted}\n\n---\nOriginal Task:\n{agent_prompt}"
                        input_data["tool_input"]["prompt"] = enhanced_prompt
                        print(json.dumps({
                            "action": "continue",
                            "tool_input": input_data["tool_input"]
                        }))
                        return

    # PostToolUse - Learn from operations
    elif event_type == "PostToolUse":
        tool_name = input_data.get("tool_name", "")

        if tool_name in ["Write", "Edit", "MultiEdit"]:
            tool_input = input_data.get("tool_input", {})
            file_path = tool_input.get("file_path", "")

            # Skip ephemeral files
            if not provider.should_skip_file(file_path):
                # Extract semantic changes
                operation_data = {
                    "type": "code_change",
                    "operation": tool_name,
                    "file_path": file_path,
                    "content": f"{tool_name} operation on {Path(file_path).name}",
                    "semantic_changes": [],
                    "confidence": 0.7
                }

                # For Edit operations, try to extract semantic diff
                if tool_name == "Edit" and "old_string" in tool_input and "new_string" in tool_input:
                    diff_data = provider.extract_semantic_diff(
                        tool_input["old_string"],
                        tool_input["new_string"],
                        file_path
                    )
                    if diff_data:
                        operation_data.update(diff_data)

                # Store the semantic memory
                provider.store_semantic_memory(operation_data)

    # SubagentStop - Capture agent learnings
    elif event_type == "SubagentStop":
        # This will be implemented in a separate agent_learner.py hook
        pass

    # Always continue
    print(json.dumps({"action": "continue"}))

if __name__ == "__main__":
    main()