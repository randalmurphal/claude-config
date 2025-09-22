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

# Import PRISM client and universal learner
sys.path.append(str(Path(__file__).parent))
from prism_client import get_prism_client
from universal_learner import get_learner

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
        self.learner = get_learner()
        self.operation_history = self.load_operation_history()
        self.project_knowledge = self.load_project_knowledge()
        self.last_learning_time = time.time()
        self.operation_count = 0
        self.current_session_id = f"session_{int(time.time())}"
        self.architecture_cache = {}  # Cache for layer detection

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

    def detect_layer(self, file_path: str) -> str:
        """Detect architectural layer from file path and content."""
        if file_path in self.architecture_cache:
            return self.architecture_cache[file_path]

        path_parts = Path(file_path).parts
        file_name = Path(file_path).name.lower()

        # Common layer patterns
        layer_patterns = {
            'presentation': ['ui', 'view', 'controller', 'handler', 'route', 'api', 'endpoint'],
            'business': ['service', 'manager', 'processor', 'business', 'logic', 'use_case'],
            'data': ['repository', 'dao', 'model', 'entity', 'database', 'db', 'storage'],
            'infrastructure': ['config', 'util', 'helper', 'common', 'shared'],
            'test': ['test', 'spec', 'tests']
        }

        # Check path and filename
        for layer, patterns in layer_patterns.items():
            for pattern in patterns:
                if pattern in file_name or any(pattern in part.lower() for part in path_parts):
                    self.architecture_cache[file_path] = layer
                    return layer

        # Default to infrastructure
        self.architecture_cache[file_path] = 'infrastructure'
        return 'infrastructure'

    def extract_imports(self, content: str, language: str = 'python') -> List[str]:
        """Extract import statements from code."""
        imports = []

        if language == 'python':
            # Python imports
            import_patterns = [
                r'^import\s+([\w.]+)',
                r'^from\s+([\w.]+)\s+import'
            ]
            for pattern in import_patterns:
                matches = re.findall(pattern, content, re.MULTILINE)
                imports.extend(matches)

        elif language in ['javascript', 'typescript']:
            # JS/TS imports
            import_patterns = [
                r"import\s+.*\s+from\s+['\"]([^'\"]+)['\"]",
                r"require\(['\"]([^'\"]+)['\"]\)"
            ]
            for pattern in import_patterns:
                matches = re.findall(pattern, content)
                imports.extend(matches)

        return imports

    def check_architecture_violations(self, file_path: str, imports: List[str]) -> List[Dict]:
        """Check for architecture boundary violations."""
        violations = []
        source_layer = self.detect_layer(file_path)

        # Define allowed dependencies (higher layers can depend on lower)
        layer_hierarchy = {
            'presentation': ['business', 'infrastructure'],
            'business': ['data', 'infrastructure'],
            'data': ['infrastructure'],
            'infrastructure': [],
            'test': ['presentation', 'business', 'data', 'infrastructure']
        }

        allowed_layers = layer_hierarchy.get(source_layer, [])

        for import_path in imports:
            # Try to resolve the import to a layer
            if '.' in import_path:
                # Likely a module path
                target_layer = self.detect_layer(import_path.replace('.', '/') + '.py')
            else:
                target_layer = self.detect_layer(import_path)

            # Check if this violates hierarchy
            if target_layer not in allowed_layers and target_layer != source_layer:
                if target_layer != 'infrastructure':  # Infrastructure is always allowed
                    violations.append({
                        'source': file_path,
                        'source_layer': source_layer,
                        'import': import_path,
                        'target_layer': target_layer,
                        'message': f"{source_layer} layer should not import from {target_layer} layer"
                    })

        return violations

    def get_bug_prevention_context(self, file_path: str, operation: str) -> List[Dict]:
        """Get relevant bug fixes and patterns to prevent issues."""
        bug_context = []

        if not self.learner:
            return bug_context

        # Search for bug fixes related to this file
        search_query = f"bug fix {Path(file_path).name} {operation}"

        # Query Neo4j for FIXED_BY relationships
        try:
            results = self.learner.search_patterns(
                search_query,
                mode='graph',
                limit=5
            )

            for result in results:
                if result.get('relationships'):
                    for rel in result['relationships']:
                        if rel[1] == 'FIXED_BY':
                            bug_context.append({
                                'type': 'bug_fix',
                                'pattern': rel[0],
                                'fix': rel[2],
                                'confidence': result.get('confidence', 0.8)
                            })
        except Exception as e:
            logger.debug(f"Failed to get bug prevention context: {e}")

        return bug_context

    def inject_architecture_context(self, file_path: str) -> Dict:
        """Inject architectural rules and constraints for a file."""
        layer = self.detect_layer(file_path)

        # Get layer-specific rules
        rules = self.learner.search_patterns(
            f"architecture rules {layer}",
            mode='exact',
            limit=3
        ) if self.learner else []

        # Get known violations to avoid
        violations = self.learner.search_patterns(
            f"architecture violation {layer}",
            mode='semantic',
            limit=3
        ) if self.learner else []

        return {
            'layer': layer,
            'rules': rules,
            'violations_to_avoid': violations,
            'allowed_imports': self.get_allowed_imports(layer)
        }

    def get_allowed_imports(self, layer: str) -> List[str]:
        """Get allowed import layers for a given layer."""
        layer_hierarchy = {
            'presentation': ['business', 'infrastructure'],
            'business': ['data', 'infrastructure'],
            'data': ['infrastructure'],
            'infrastructure': [],
            'test': ['presentation', 'business', 'data', 'infrastructure']
        }
        return layer_hierarchy.get(layer, [])

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

    elif event_type == "PreToolUse":
        # Inject architecture and bug prevention context before writes
        tool_name = input_data.get("tool_name", "")
        if tool_name in ["Write", "Edit", "MultiEdit"]:
            file_path = input_data.get("tool_input", {}).get("file_path", "")
            if file_path:
                # Get architecture context
                arch_context = provider.inject_architecture_context(file_path)

                # Get bug prevention context
                bug_context = provider.get_bug_prevention_context(file_path, tool_name)

                # Format context message
                context_messages = []

                if arch_context:
                    context_messages.append(f"📋 Architecture: {arch_context['layer']} layer")
                    if arch_context['allowed_imports']:
                        context_messages.append(f"   Can import from: {', '.join(arch_context['allowed_imports'])}")
                    if arch_context['rules']:
                        context_messages.append("   Rules to follow:")
                        for rule in arch_context['rules'][:2]:
                            context_messages.append(f"   - {rule.get('content', '')[:100]}")

                if bug_context:
                    context_messages.append("\n⚠️ Previous bugs to avoid:")
                    for bug in bug_context[:2]:
                        context_messages.append(f"   - {bug['pattern'][:50]} → Fix: {bug['fix'][:50]}")

                if context_messages:
                    result = {
                        "intervention": {
                            "type": "context_injection",
                            "severity": "INFO",
                            "message": "\n".join(context_messages)
                        }
                    }

    elif event_type == "PostToolUse":
        # Track operations for learning
        provider.track_operation(input_data)

        # Check for architecture violations after writes
        tool_name = input_data.get("tool_name", "")
        if tool_name in ["Write", "Edit", "MultiEdit"]:
            file_path = input_data.get("tool_input", {}).get("file_path", "")
            content = input_data.get("tool_input", {}).get("content", "")
            if not content and tool_name == "Edit":
                content = input_data.get("tool_input", {}).get("new_string", "")

            if file_path and content:
                # Extract imports and check violations
                language = 'python' if file_path.endswith('.py') else 'javascript'
                imports = provider.extract_imports(content, language)
                violations = provider.check_architecture_violations(file_path, imports)

                if violations:
                    # Store violation patterns for learning
                    for violation in violations:
                        provider.learner.learn_pattern({
                            'type': 'architecture_violation',
                            'content': violation['message'],
                            'file': violation['source'],
                            'confidence': 0.9
                        })

                    # Only warn, don't block
                    result = {
                        "intervention": {
                            "type": "context_injection",
                            "severity": "WARNING",
                            "message": f"⚠️ Architecture violations detected:\n" +
                                     "\n".join([v['message'] for v in violations[:3]])
                        }
                    }

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