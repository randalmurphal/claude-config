#!/usr/bin/env python3
"""
Memory MCP-based orchestration system for intelligent context management
"""

import json
import os
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import hashlib

@dataclass
class MemoryScope:
    """Represents a hierarchical memory scope"""
    project: str
    component: Optional[str] = None
    module: Optional[str] = None
    entity: Optional[str] = None

    def to_path(self) -> str:
        """Convert to dot-notation path"""
        parts = ["project", self.project]
        if self.component:
            parts.append(self.component)
            if self.module:
                parts.extend(["modules", self.module])
                if self.entity:
                    parts.append(self.entity)
        return ".".join(parts)

    def parent_scopes(self) -> List[str]:
        """Get all parent scopes for cascade loading"""
        scopes = []

        # Most specific to least specific
        if self.entity:
            scopes.append(f"project.{self.project}.{self.component}.modules.{self.module}.{self.entity}")
        if self.module:
            scopes.append(f"project.{self.project}.{self.component}.modules.{self.module}")
        if self.component:
            scopes.append(f"project.{self.project}.{self.component}")
        scopes.append(f"project.{self.project}.shared")
        scopes.append(f"project.{self.project}")

        return scopes


class MemoryOrchestrator:
    """Manages Memory MCP interactions for orchestration"""

    def __init__(self, project_root: str):
        self.project_root = project_root
        self.project_structure = self._detect_project_structure()
        self.current_component = None
        self.current_mission = None
        self.task_id = self._generate_task_id()

    def _detect_project_structure(self) -> Dict[str, Any]:
        """Detect if monorepo and identify components"""
        structure = {
            "type": "single",
            "components": [],
            "shared_paths": []
        }

        # Check for common monorepo indicators
        if os.path.exists(os.path.join(self.project_root, "services")):
            structure["type"] = "monorepo"
            structure["components"] = os.listdir(os.path.join(self.project_root, "services"))
        elif os.path.exists(os.path.join(self.project_root, "packages")):
            structure["type"] = "monorepo"
            structure["components"] = os.listdir(os.path.join(self.project_root, "packages"))
        elif os.path.exists(os.path.join(self.project_root, "apps")):
            structure["type"] = "monorepo"
            structure["components"] = os.listdir(os.path.join(self.project_root, "apps"))

        # Identify shared directories
        for shared_name in ["shared", "common", "lib", "core"]:
            shared_path = os.path.join(self.project_root, shared_name)
            if os.path.exists(shared_path):
                structure["shared_paths"].append(shared_name)

        return structure

    def _generate_task_id(self) -> str:
        """Generate unique task ID"""
        timestamp = datetime.now().isoformat()
        return hashlib.md5(timestamp.encode()).hexdigest()[:12]

    def determine_component(self, mission: str, file_path: Optional[str] = None) -> str:
        """Determine which component we're working in"""
        if self.project_structure["type"] == "single":
            return "main"

        # Try to detect from mission keywords
        mission_lower = mission.lower()
        for component in self.project_structure["components"]:
            if component.lower() in mission_lower:
                return component

        # Try to detect from file path
        if file_path:
            for component in self.project_structure["components"]:
                if component in file_path:
                    return component

        # Default to first component or shared
        return self.project_structure["components"][0] if self.project_structure["components"] else "shared"

    def build_agent_context(self,
                           agent_type: str,
                           mission: str,
                           component: str,
                           module: Optional[str] = None,
                           entity: Optional[str] = None) -> str:
        """Build context for an agent from Memory MCP"""

        context_parts = []

        # 1. Mission is always first and prominent
        context_parts.append(f"🎯 MISSION (Your North Star): {mission}")
        context_parts.append(f"📍 Component: {component}")
        if module:
            context_parts.append(f"📦 Module: {module}")
        context_parts.append("")  # Blank line

        # 2. Build scope cascade
        scope = MemoryScope(
            project=os.path.basename(self.project_root),
            component=component,
            module=module,
            entity=entity
        )
        scopes = scope.parent_scopes()

        # 3. Load ALL critical memories (no limit)
        critical_memories = self._load_critical_memories(scopes)
        if critical_memories:
            context_parts.append("⚠️ CRITICAL FACTS (ALL must be considered):")
            for memory in critical_memories:
                context_parts.append(f"  • {memory['observation']}")
                if memory.get('reasoning'):
                    context_parts.append(f"    WHY: {memory['reasoning']}")
            context_parts.append("")

        # 4. Load limited helpful memories
        helpful_memories = self._load_helpful_memories(scopes, limit=5)
        if helpful_memories:
            context_parts.append("📝 Helpful Context:")
            for memory in helpful_memories:
                context_parts.append(f"  • {memory['observation']}")
            context_parts.append("")

        # 5. Load preferences
        preferences = self._load_preferences(component)
        if preferences:
            context_parts.append("💼 Style Preferences (HOW to implement):")
            for pref in preferences[:3]:  # Limit preferences shown
                context_parts.append(f"  • {pref['rule']}")
            context_parts.append("")

        # 6. Add deviation prevention reminder
        context_parts.append("⚠️ ALIGNMENT REQUIREMENTS:")
        context_parts.append("  • Stay focused on the mission above")
        context_parts.append("  • Do NOT add unrequested features")
        context_parts.append("  • Ask questions instead of making assumptions")
        context_parts.append("  • Report factual discoveries you make")

        return "\n".join(context_parts)

    def _load_critical_memories(self, scopes: List[str]) -> List[Dict]:
        """Load ALL critical memories from scopes"""
        critical = []
        seen_ids = set()

        # This would actually call Memory MCP
        # For now, showing the structure
        for scope in scopes:
            # In reality: memories = memory_mcp.query({"scope": scope, "critical": True})
            memories = self._mock_memory_query(scope, critical=True)

            for memory in memories:
                if memory.get('id') not in seen_ids:
                    seen_ids.add(memory.get('id'))
                    critical.append(memory)

        return critical

    def _load_helpful_memories(self, scopes: List[str], limit: int = 5) -> List[Dict]:
        """Load limited helpful memories"""
        helpful = []

        for scope in scopes[:3]:  # Only check most specific scopes
            if len(helpful) >= limit:
                break

            # In reality: memories = memory_mcp.query({"scope": scope, "critical": False, "limit": limit - len(helpful)})
            memories = self._mock_memory_query(scope, critical=False, limit=limit - len(helpful))
            helpful.extend(memories)

        return helpful[:limit]

    def _load_preferences(self, component: str) -> List[Dict]:
        """Load style preferences"""
        scopes = [
            "preference.style.global",
            f"preference.language.python",  # Would detect language
            f"preference.project.{component}"
        ]

        preferences = []
        for scope in scopes:
            # In reality: prefs = memory_mcp.query({"type": "preference", "scope": scope})
            prefs = self._mock_preference_query(scope)
            preferences.extend(prefs)

        return preferences

    def _mock_memory_query(self, scope: str, critical: bool = False, limit: Optional[int] = None) -> List[Dict]:
        """Mock memory query for demonstration"""
        # This would be replaced with actual Memory MCP calls
        examples = {
            "critical": [
                {"id": "mem1", "observation": "OAuthClient.refresh() must be called before every API call - tokens expire in 1hr", "reasoning": "SDK assumes 24hr expiry but provider uses 1hr"},
                {"id": "mem2", "observation": "Database connection pool limited to 20 - will deadlock if exceeded", "reasoning": "PostgreSQL configuration hard limit"},
            ],
            "helpful": [
                {"id": "mem3", "observation": "Use exponential backoff for API retries", "reasoning": "Prevents rate limit issues"},
                {"id": "mem4", "observation": "Logging should use structured JSON format", "reasoning": "CloudWatch ingestion requirement"},
            ]
        }

        if critical:
            return examples["critical"][:limit] if limit else examples["critical"]
        else:
            return examples["helpful"][:limit] if limit else examples["helpful"]

    def _mock_preference_query(self, scope: str) -> List[Dict]:
        """Mock preference query for demonstration"""
        examples = [
            {"id": "pref1", "rule": "Use single quotes in Python", "scope": "preference.language.python"},
            {"id": "pref2", "rule": "Prefer early returns over nested ifs", "scope": "preference.style.global"},
            {"id": "pref3", "rule": "No obvious comments, only document WHY", "scope": "preference.style.global"},
        ]
        return examples[:2]

    def store_discovery(self, discovery: Dict, agent_id: str):
        """Store an agent's discovery in Memory MCP"""

        # Validate it's a fact, not a preference
        if self._is_preference(discovery['observation']):
            raise ValueError(f"Agent {agent_id} cannot add preferences - only facts")

        # Determine scope
        scope = self._determine_discovery_scope(discovery)

        memory = {
            "type": "fact",
            "scope": scope,
            "observation": discovery['observation'],
            "reasoning": discovery.get('reasoning'),
            "critical": self._is_critical(discovery),
            "discovered_by": agent_id,
            "task_id": self.task_id,
            "timestamp": datetime.now().isoformat()
        }

        # In reality: memory_mcp.store(memory)
        print(f"Storing discovery: {memory}")

        return memory

    def _is_preference(self, observation: str) -> bool:
        """Check if observation is a preference (not allowed from agents)"""
        preference_indicators = [
            "prefer", "should use", "style", "always use",
            "never use", "convention", "format with"
        ]
        return any(indicator in observation.lower() for indicator in preference_indicators)

    def _is_critical(self, discovery: Dict) -> bool:
        """Determine if a discovery is critical"""
        observation = discovery.get('observation', '').lower()
        critical_indicators = [
            "will break", "will fail", "causes crash",
            "security vulnerability", "data loss",
            "infinite loop", "deadlock", "race condition"
        ]
        return any(indicator in observation for indicator in critical_indicators)

    def _determine_discovery_scope(self, discovery: Dict) -> str:
        """Determine the scope for a discovery"""
        if discovery.get('entity'):
            # Code entity specific
            return f"project.{self.current_component}.entities.{discovery['entity']}"
        elif discovery.get('module'):
            # Module specific
            return f"project.{self.current_component}.modules.{discovery['module']}"
        elif discovery.get('tool'):
            # Tool specific
            language = discovery.get('language', 'python')
            return f"language.{language}.tools.{discovery['tool']}"
        else:
            # Component general
            return f"project.{self.current_component}.general"


class MissionDeviationDetector:
    """Detects when work deviates from the mission"""

    def __init__(self, mission: str):
        self.mission = mission
        self.mission_keywords = self._extract_keywords(mission)

    def _extract_keywords(self, mission: str) -> List[str]:
        """Extract key terms from mission"""
        # Simple keyword extraction - would be more sophisticated
        stop_words = {'add', 'create', 'build', 'make', 'with', 'for', 'the', 'a', 'an'}
        words = mission.lower().split()
        return [w for w in words if w not in stop_words]

    def check_alignment(self, agent_output: str) -> Dict[str, Any]:
        """Check if agent output aligns with mission"""

        alignment = {
            "aligned": True,
            "confidence": 1.0,
            "issues": []
        }

        # Check for scope creep
        scope_creep_indicators = [
            "while we're at it",
            "might as well",
            "bonus feature",
            "also adding",
            "user will probably want"
        ]

        for indicator in scope_creep_indicators:
            if indicator in agent_output.lower():
                alignment["aligned"] = False
                alignment["issues"].append(f"Scope creep detected: '{indicator}'")

        # Check for assumptions
        assumption_indicators = [
            "i'll assume",
            "assuming",
            "probably means",
            "typically",
            "best practice"
        ]

        for indicator in assumption_indicators:
            if indicator in agent_output.lower():
                alignment["aligned"] = False
                alignment["issues"].append(f"Assumption detected: '{indicator}'")

        # Check for over-engineering
        if "abstract" in agent_output.lower() and "abstract" not in self.mission.lower():
            alignment["aligned"] = False
            alignment["issues"].append("Possible over-engineering: unnecessary abstraction")

        return alignment

    def generate_clarification(self, issues: List[str]) -> str:
        """Generate clarifying questions based on issues"""
        questions = []

        for issue in issues:
            if "assumption" in issue:
                questions.append("I need clarification on the implementation approach. Should I proceed with the simplest solution or is there a specific pattern you prefer?")
            elif "scope creep" in issue:
                questions.append("I notice I might be adding features beyond the original request. Should I focus only on what was explicitly requested?")
            elif "over-engineering" in issue:
                questions.append("I'm considering a more complex architecture. Would you prefer the simplest solution that works?")

        return "\n".join(questions)


def main():
    """Example usage"""
    import sys

    if len(sys.argv) < 2:
        print("Usage: memory_orchestration.py <command> [args]")
        sys.exit(1)

    command = sys.argv[1]

    if command == "init":
        # Initialize orchestration with mission
        mission = sys.argv[2] if len(sys.argv) > 2 else "Add OAuth login"
        orchestrator = MemoryOrchestrator(os.getcwd())

        component = orchestrator.determine_component(mission)
        context = orchestrator.build_agent_context(
            agent_type="architecture-planner",
            mission=mission,
            component=component
        )

        print(context)

    elif command == "check-alignment":
        # Check if output aligns with mission
        mission = sys.argv[2]
        output = sys.argv[3]

        detector = MissionDeviationDetector(mission)
        alignment = detector.check_alignment(output)

        if alignment["aligned"]:
            print("✅ Output aligns with mission")
        else:
            print("⚠️ Deviation detected:")
            for issue in alignment["issues"]:
                print(f"  - {issue}")
            print("\nSuggested questions:")
            print(detector.generate_clarification(alignment["issues"]))


if __name__ == "__main__":
    main()