#!/opt/envs/py3.13/bin/python
"""
Unified Context Provider Hook
=============================
Consolidates context and memory features from:
- prism_context_injector.py
- prism_continuous_learner.py
- prism_memory_builder.py
- prism_read_memory.py

Key Features:
- Extracts intent from user messages and agent prompts
- Retrieves relevant memories from ALL tiers
- Accumulates project-specific knowledge
- Pulls from DECISION_MEMORY.json and INVARIANTS.md
- Formats context differently for agents vs solo work
- Learns patterns continuously from development
- Provides visible value through relevant context injection
"""

import json
import sys
import time
import logging
import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from collections import defaultdict
from datetime import datetime, timedelta

# Import PRISM client
sys.path.append(str(Path(__file__).parent))
from prism_client import get_prism_client

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
OPERATION_HISTORY_FILE = Path.home() / ".claude" / "operation_history.json"
PROJECT_KNOWLEDGE_FILE = Path.home() / ".claude" / "project_knowledge.json"
DECISION_MEMORY_FILE = Path.cwd() / ".symphony" / "DECISION_MEMORY.json"
INVARIANTS_FILE = Path.cwd() / "INVARIANTS.md"
MAX_OPERATIONS = 100
RELEVANCE_THRESHOLD = 0.15  # Reasonable threshold for PRISM scores
CONFIDENCE_THRESHOLD = 0.8
LEARNING_INTERVAL_OPS = 10
LEARNING_INTERVAL_SECONDS = 300

class UnifiedContextProvider:
    """Unified context provider with learning and memory features."""

    def __init__(self):
        self.client = get_prism_client()
        self.operation_history = self.load_operation_history()
        self.project_knowledge = self.load_project_knowledge()
        self.last_learning_time = time.time()
        self.operation_count = 0
        self.current_session_id = f"session_{int(time.time())}"

    def load_operation_history(self) -> List[Dict]:
        """Load recent operation history."""
        try:
            if OPERATION_HISTORY_FILE.exists():
                with open(OPERATION_HISTORY_FILE, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.debug(f"Failed to load operation history: {e}")
        return []

    def save_operation_history(self):
        """Save operation history to file."""
        try:
            OPERATION_HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
            trimmed = self.operation_history[-MAX_OPERATIONS:]
            with open(OPERATION_HISTORY_FILE, 'w') as f:
                json.dump(trimmed, f, indent=2)
        except Exception as e:
            logger.debug(f"Failed to save operation history: {e}")

    def load_project_knowledge(self) -> Dict:
        """Load accumulated project knowledge."""
        try:
            if PROJECT_KNOWLEDGE_FILE.exists():
                with open(PROJECT_KNOWLEDGE_FILE, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.debug(f"Failed to load project knowledge: {e}")

        return {
            "patterns": {},
            "decisions": {},
            "gotchas": [],
            "file_relationships": {},
            "naming_conventions": {},
            "common_errors": {},
            "project_structure": {}
        }

    def save_project_knowledge(self):
        """Save project knowledge to file."""
        try:
            PROJECT_KNOWLEDGE_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(PROJECT_KNOWLEDGE_FILE, 'w') as f:
                json.dump(self.project_knowledge, f, indent=2)
        except Exception as e:
            logger.debug(f"Failed to save project knowledge: {e}")

    def extract_intent(self, message: str) -> Tuple[str, float]:
        """Extract user/agent intent from message."""
        message_lower = message.lower()

        # Intent patterns with confidence scores
        intent_patterns = [
            # Bug fixing
            (r'\b(fix|bug|error|issue|problem|broken|fail|crash)\b', 'bug_fix', 0.9),
            (r'\b(debug|troubleshoot|diagnose|investigate)\b', 'bug_fix', 0.85),

            # Feature development
            (r'\b(add|implement|create|build|feature|new)\b', 'feature', 0.85),
            (r'\b(enhance|extend|improve|upgrade)\b', 'feature', 0.8),

            # Refactoring
            (r'\b(refactor|clean|optimize|simplify|restructure)\b', 'refactor', 0.9),
            (r'\b(dry|consolidate|merge|combine)\b', 'refactor', 0.85),

            # Research/exploration
            (r'\b(find|search|look|explore|understand|analyze)\b', 'research', 0.85),
            (r'\b(how|what|where|why|when)\b.*\?', 'research', 0.8),

            # Testing
            (r'\b(test|testing|unittest|pytest|coverage)\b', 'testing', 0.9),
            (r'\b(validate|verify|check|ensure)\b', 'testing', 0.75),

            # Documentation
            (r'\b(document|docs|readme|comment|explain)\b', 'documentation', 0.9),

            # Performance
            (r'\b(performance|speed|slow|fast|optimize|latency)\b', 'performance', 0.9),

            # Security
            (r'\b(security|vulnerability|exploit|injection|auth)\b', 'security', 0.95),
        ]

        best_intent = 'general'
        best_confidence = 0.5

        for pattern, intent, confidence in intent_patterns:
            if re.search(pattern, message_lower):
                if confidence > best_confidence:
                    best_intent = intent
                    best_confidence = confidence

        return best_intent, best_confidence

    def load_decision_memory(self) -> Dict:
        """Load project decision memory if available."""
        try:
            if DECISION_MEMORY_FILE.exists():
                with open(DECISION_MEMORY_FILE, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.debug(f"No decision memory found: {e}")
        return {}

    def load_invariants(self) -> List[str]:
        """Load project invariants if available."""
        invariants = []
        try:
            if INVARIANTS_FILE.exists():
                with open(INVARIANTS_FILE, 'r') as f:
                    content = f.read()
                    # Extract invariant rules
                    for line in content.split('\n'):
                        if line.strip() and not line.startswith('#'):
                            invariants.append(line.strip())
        except Exception as e:
            logger.debug(f"No invariants file found: {e}")
        return invariants

    def retrieve_relevant_context(self, intent: str, message: str, is_agent: bool = False) -> List[Dict]:
        """Retrieve relevant context from all memory tiers."""
        if not self.client:
            return []

        relevant_context = []

        try:
            # Build search query based on intent and message keywords
            keywords = re.findall(r'\b[A-Za-z_]\w+\b', message)
            important_keywords = [k for k in keywords if len(k) > 3 and k.lower() not in
                                 ['this', 'that', 'with', 'from', 'have', 'what', 'when', 'where']]

            search_query = f"{intent} {' '.join(important_keywords[:5])}"

            # Search across all tiers with different priorities
            tier_priorities = [
                ('ANCHORS', 1.0),    # Most important - immutable truths
                ('LONGTERM', 0.9),   # Stable patterns
                ('WORKING', 0.8),    # Session context
                ('EPISODIC', 0.7),   # Recent activities
            ]

            for tier, weight in tier_priorities:
                try:
                    results = self.client.search_memory(
                        query=search_query,
                        tiers=[tier],  # Fixed: use 'tiers' parameter with list
                        limit=3
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

        return relevant_context[:5]  # Return top 5 most relevant

    def learn_patterns_from_operations(self):
        """Learn patterns from recent operations (continuous learning)."""
        if len(self.operation_history) < 3:
            return

        recent_ops = self.operation_history[-20:]

        # Learn file co-edit patterns
        file_pairs = defaultdict(int)
        for i in range(len(recent_ops) - 1):
            if recent_ops[i].get('file_path') and recent_ops[i+1].get('file_path'):
                pair = tuple(sorted([recent_ops[i]['file_path'], recent_ops[i+1]['file_path']]))
                if pair[0] != pair[1]:
                    file_pairs[pair] += 1

        # Store significant co-edit patterns
        for pair, count in file_pairs.items():
            if count >= 2:  # Files edited together at least twice
                self.project_knowledge['file_relationships'][str(pair)] = {
                    'count': count,
                    'type': 'co_edit',
                    'learned_at': time.time()
                }

        # Learn naming patterns
        for op in recent_ops:
            if op.get('operation') in ['Write', 'Edit'] and op.get('content'):
                # Extract function/class/variable names
                names = re.findall(r'(?:def|class|var|let|const)\s+([a-zA-Z_]\w+)', op['content'])
                for name in names:
                    # Detect naming convention
                    if '_' in name:
                        convention = 'snake_case'
                    elif name[0].isupper():
                        convention = 'PascalCase'
                    else:
                        convention = 'camelCase'

                    if op['file_path']:
                        ext = Path(op['file_path']).suffix
                        self.project_knowledge['naming_conventions'][ext] = convention

        # Learn error patterns
        error_ops = [op for op in recent_ops if op.get('error')]
        for i, error_op in enumerate(error_ops):
            # Find the fix (next successful operation on same file)
            for j in range(i+1, len(recent_ops)):
                if (recent_ops[j].get('file_path') == error_op.get('file_path') and
                    not recent_ops[j].get('error')):
                    error_key = self._extract_error_key(error_op.get('error', ''))
                    if error_key:
                        self.project_knowledge['common_errors'][error_key] = {
                            'error': error_op.get('error', '')[:200],
                            'fix_operation': recent_ops[j].get('operation'),
                            'learned_at': time.time()
                        }
                    break

        self.save_project_knowledge()

        # Store learned patterns in PRISM
        if self.client and self.project_knowledge:
            try:
                pattern_data = {
                    'type': 'learned_patterns',
                    'session_id': self.current_session_id,
                    'patterns': {
                        'file_relationships': dict(list(self.project_knowledge['file_relationships'].items())[-5:]),
                        'naming_conventions': self.project_knowledge['naming_conventions'],
                        'common_errors': dict(list(self.project_knowledge['common_errors'].items())[-5:])
                    },
                    'timestamp': time.time()
                }

                self.client.store_memory(
                    content=json.dumps(pattern_data),
                    tier='LONGTERM',
                    metadata={
                        'importance': 'medium',
                        'tags': ['patterns', 'learning', 'project_knowledge']
                    }
                )
            except Exception as e:
                logger.debug(f"Failed to store patterns: {e}")

    def _extract_error_key(self, error_message: str) -> str:
        """Extract a key identifier from error message."""
        # Common error patterns
        patterns = [
            r'(ImportError|ModuleNotFoundError): [^:]+',
            r'(TypeError|ValueError|AttributeError): [^:]+',
            r'(SyntaxError): [^:]+',
            r'(FileNotFoundError): [^:]+',
        ]

        for pattern in patterns:
            match = re.search(pattern, error_message)
            if match:
                return match.group(0)[:50]

        # Fallback to first line
        return error_message.split('\n')[0][:50] if error_message else ''

    def format_context_for_injection(self, intent: str, confidence: float,
                                    context: List[Dict], is_agent: bool = False) -> str:
        """Format retrieved context for injection."""
        if not context and confidence < CONFIDENCE_THRESHOLD:
            return ""

        sections = []

        # Header
        if is_agent:
            sections.append("## 🤖 Agent Context from PRISM\n")
        else:
            sections.append("## 🧠 PRISM Context\n")

        sections.append(f"**Intent**: {intent.replace('_', ' ').title()} (confidence: {confidence:.0%})")

        # Load decision memory and invariants
        decisions = self.load_decision_memory()
        invariants = self.load_invariants()

        # Add project invariants if any
        if invariants:
            sections.append("\n### ⚠️ Project Invariants")
            for inv in invariants[:3]:
                sections.append(f"- {inv}")

        # Add relevant decisions if any
        if decisions:
            relevant_decisions = []
            for key, decision in decisions.items():
                if intent in key.lower() or any(k in key.lower() for k in ['critical', 'important']):
                    relevant_decisions.append(decision)

            if relevant_decisions:
                sections.append("\n### 📋 Relevant Decisions")
                for dec in relevant_decisions[:3]:
                    sections.append(f"- {dec.get('decision', dec)[:100]}")

        # Add retrieved context
        if context:
            critical_context = [c for c in context if c.get('tier') == 'ANCHORS']
            pattern_context = [c for c in context if c.get('tier') in ['LONGTERM', 'WORKING']]
            recent_context = [c for c in context if c.get('tier') == 'EPISODIC']

            if critical_context:
                sections.append("\n### 🔥 Critical Context")
                for ctx in critical_context[:2]:
                    try:
                        content = json.loads(ctx.get('content', '{}'))
                        if 'reason' in content:
                            sections.append(f"- **{content.get('type', 'info')}**: {content['reason']}")
                        elif 'pattern' in content:
                            sections.append(f"- Pattern: {content['pattern'][:100]}")
                    except:
                        pass

            if pattern_context:
                sections.append("\n### 💡 Relevant Patterns")
                for ctx in pattern_context[:3]:
                    try:
                        content = json.loads(ctx.get('content', '{}'))
                        if content.get('type') == 'learned_patterns':
                            patterns = content.get('patterns', {})
                            if patterns.get('file_relationships'):
                                sections.append("- **File relationships**: " +
                                              str(list(patterns['file_relationships'].keys())[:2]))
                            if patterns.get('naming_conventions'):
                                sections.append("- **Naming**: " +
                                              ', '.join(f"{k}={v}" for k, v in patterns['naming_conventions'].items()))
                        elif 'commands' in content:
                            sections.append(f"- Workflow: {' → '.join(content['commands'][:3])}")
                    except:
                        pass

        # Add project knowledge insights
        if self.project_knowledge:
            if self.project_knowledge.get('gotchas'):
                sections.append("\n### ⚡ Known Gotchas")
                for gotcha in self.project_knowledge['gotchas'][:2]:
                    sections.append(f"- {gotcha}")

            if self.project_knowledge.get('common_errors'):
                sections.append("\n### 🔧 Common Errors & Fixes")
                for error_key, info in list(self.project_knowledge['common_errors'].items())[:2]:
                    sections.append(f"- {error_key}: Fixed with {info.get('fix_operation', 'unknown')}")

        return "\n".join(sections) if len(sections) > 2 else ""

    def track_operation(self, operation_data: Dict):
        """Track an operation for learning."""
        self.operation_history.append({
            'timestamp': time.time(),
            'session_id': self.current_session_id,
            'operation': operation_data.get('tool_name'),
            'file_path': operation_data.get('tool_input', {}).get('file_path'),
            'content': operation_data.get('tool_input', {}).get('content', '')[:200],
            'error': operation_data.get('tool_response', {}).get('error'),
            'success': not bool(operation_data.get('tool_response', {}).get('error'))
        })

        self.operation_count += 1

        # Trigger learning if threshold reached
        if (self.operation_count >= LEARNING_INTERVAL_OPS or
            time.time() - self.last_learning_time > LEARNING_INTERVAL_SECONDS):
            self.learn_patterns_from_operations()
            self.last_learning_time = time.time()
            self.operation_count = 0

        self.save_operation_history()

    def accumulate_project_knowledge(self, knowledge_type: str, knowledge_data: Any):
        """Accumulate project-specific knowledge."""
        if knowledge_type == 'gotcha':
            if knowledge_data not in self.project_knowledge['gotchas']:
                self.project_knowledge['gotchas'].append(knowledge_data)
                self.project_knowledge['gotchas'] = self.project_knowledge['gotchas'][-10:]

        elif knowledge_type == 'decision':
            key = knowledge_data.get('key', str(time.time()))
            self.project_knowledge['decisions'][key] = knowledge_data

        elif knowledge_type == 'structure':
            self.project_knowledge['project_structure'].update(knowledge_data)

        self.save_project_knowledge()

        # Store in PRISM for long-term retention
        if self.client:
            try:
                self.client.store_memory(
                    content=json.dumps({
                        'type': f'project_{knowledge_type}',
                        'data': knowledge_data,
                        'project': os.getcwd(),
                        'timestamp': time.time()
                    }),
                    tier='ANCHORS' if knowledge_type == 'decision' else 'LONGTERM',
                    metadata={
                        'importance': 'high' if knowledge_type in ['decision', 'gotcha'] else 'medium',
                        'tags': ['project_knowledge', knowledge_type]
                    }
                )
            except Exception as e:
                logger.debug(f"Failed to store project knowledge: {e}")

def main():
    """Main hook execution."""
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError:
        logger.error("Failed to parse JSON input")
        sys.exit(1)

    event_type = input_data.get("hook_event_name", "")

    # Initialize provider
    provider = UnifiedContextProvider()

    result = {"intervention": None}

    if event_type == "PreUserMessage":
        # Extract intent and inject context for user messages
        user_message = input_data.get("user_message", "")
        if user_message:
            intent, confidence = provider.extract_intent(user_message)

            if confidence >= CONFIDENCE_THRESHOLD:
                context = provider.retrieve_relevant_context(intent, user_message, is_agent=False)
                formatted_context = provider.format_context_for_injection(intent, confidence, context, is_agent=False)

                if formatted_context:
                    result = {
                        "intervention": {
                            "type": "context_injection",
                            "severity": "INFO",
                            "message": formatted_context
                        }
                    }

    elif event_type == "PostToolUse":
        # Track operations for learning
        provider.track_operation(input_data)

    elif event_type == "SessionStart":
        # Initialize session and load project knowledge
        provider.current_session_id = f"session_{int(time.time())}"

        # Check if we have project knowledge to share
        if provider.project_knowledge.get('gotchas') or provider.project_knowledge.get('decisions'):
            welcome_message = ["## 📚 Project Knowledge Available\n"]

            if provider.project_knowledge.get('gotchas'):
                welcome_message.append("**Known gotchas:** " + str(len(provider.project_knowledge['gotchas'])))

            if provider.project_knowledge.get('decisions'):
                welcome_message.append("**Recorded decisions:** " + str(len(provider.project_knowledge['decisions'])))

            if provider.project_knowledge.get('file_relationships'):
                welcome_message.append("**File relationships:** " + str(len(provider.project_knowledge['file_relationships'])))

            result = {
                "intervention": {
                    "type": "context_injection",
                    "severity": "INFO",
                    "message": "\n".join(welcome_message)
                }
            }

    elif event_type == "Timer" or event_type == "SessionEnd":
        # Trigger learning
        provider.learn_patterns_from_operations()

    # Output result
    print(json.dumps(result))

if __name__ == "__main__":
    main()