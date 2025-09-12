#!/usr/bin/env python3
"""
Orchestration tools for /conduct command.
Handles workspace setup, context creation, discovery sharing, and phase transitions.
"""

import json
import os
import subprocess
import shutil
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Any
import argparse
import sys


class OrchestrationTools:
    def __init__(self, working_directory: str):
        """Initialize with absolute working directory path."""
        self.working_dir = Path(working_directory).absolute()
        self.symphony_dir = self.working_dir / ".symphony"
        self.chambers_dir = self.symphony_dir / "chambers"  # Worker worktrees
        self.workspaces_dir = self.chambers_dir  # Alias for compatibility
        self.hooks_dir = self.symphony_dir / "hooks"
        
        # Ensure directories exist
        self.symphony_dir.mkdir(exist_ok=True)
        self.chambers_dir.mkdir(exist_ok=True)
        self.hooks_dir.mkdir(exist_ok=True)
        
        # Detect git environment
        self.use_git = self._detect_git_environment()
        
        # Validate environment on init
        self.validate_environment()
    
    def create_mission_context(self, original_request: str, success_criteria: str = "") -> str:
        """Create MISSION_CONTEXT.json for the entire task."""
        mission_file = self.symphony_dir / "MISSION_CONTEXT.json"
        
        context = {
            "original_request": original_request,
            "current_understanding": original_request,  # This evolves as we learn
            "success_criteria": success_criteria or "Task completed as requested",
            "discovered_requirements": [],
            "clarifications_made": [],
            "examples_found": [],
            "business_logic": {
                "validations": [],
                "calculations": [],
                "state_transitions": [],
                "error_conditions": []
            },
            "working_directory": str(self.working_dir),
            "timestamp": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat(),
            "created_by": "orchestration_tools"
        }
        
        with open(mission_file, 'w') as f:
            json.dump(context, f, indent=2)
        
        print(f"✓ Created MISSION_CONTEXT.json at {mission_file}")
        return str(mission_file)
    
    def setup_parallel_workspaces(self, workers: List[Dict], enable_interrupts: bool = True) -> Dict:
        """
        Set up git worktrees and contexts for parallel workers.
        
        Args:
            workers: List of dicts with keys: id, module, scope
            enable_interrupts: Whether to install interrupt hooks
        
        Returns:
            Dict mapping worker_id to workspace paths
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        workspace_paths = {}
        
        # Create worktrees for each worker
        for worker in workers:
            worker_id = worker['id']
            module = worker['module']
            scope = worker.get('scope', f"src/{module}/**")
            
            # Create worktree with unique branch
            workspace_path = self.workspaces_dir / worker_id
            branch_name = f"conduct-{module}-{timestamp}"
            
            try:
                # Remove if exists (cleanup from previous run)
                if workspace_path.exists():
                    subprocess.run(["git", "worktree", "remove", str(workspace_path), "--force"], 
                                 cwd=self.working_dir, capture_output=True)
                
                # Create new worktree
                result = subprocess.run(
                    ["git", "worktree", "add", str(workspace_path), "-b", branch_name],
                    cwd=self.working_dir,
                    capture_output=True,
                    text=True
                )
                
                if result.returncode != 0:
                    print(f"⚠️ Failed to create worktree for {worker_id}: {result.stderr}")
                    continue
                
                print(f"✓ Created worktree for {worker_id} at {workspace_path}")
                
                # Copy relevant skeleton files
                self._copy_skeleton_files(workspace_path, scope)
                
                # Create worker context with clear hierarchy
                worker_context = {
                    "CRITICAL_FOR_YOUR_TASK": {
                        "worker_id": worker_id,
                        "your_module": module,
                        "your_scope": scope,
                        "workspace_directory": str(workspace_path),
                        "task": f"Implement {module} module following skeleton",
                        "skeleton_location": f"{workspace_path}/{scope.split('/')[0]}",
                        "validation_command": self._get_validation_command(module)
                    },
                    "BIG_PICTURE_CONTEXT": {
                        "mission_file": str(self.symphony_dir / "MISSION_CONTEXT.json"),
                        "main_directory": str(self.working_dir),
                        "current_phase": self._get_current_phase(),
                        "total_phases": 7,
                        "other_workers": [w['module'] for w in workers if w['id'] != worker_id],
                        "why_this_matters": "Your module is part of the larger system"
                    },
                    "EXPLORE_AS_NEEDED": {
                        "for_interfaces": f"{self.working_dir}/src/interfaces/",
                        "for_shared_utilities": f"{self.working_dir}/src/common/",
                        "for_types": f"{self.working_dir}/src/types/",
                        "common_registry": f"{self.symphony_dir}/COMMON_REGISTRY.json",
                        "boundaries_file": f"{self.symphony_dir}/BOUNDARIES.json"
                    },
                    "interrupt_enabled": enable_interrupts,
                    "instructions": self._get_worker_instructions(module)
                }
                
                worker_context_file = workspace_path / ".chamber" / "WORKER_CONTEXT.json"
                worker_context_file.parent.mkdir(parents=True, exist_ok=True)
                
                with open(worker_context_file, 'w') as f:
                    json.dump(worker_context, f, indent=2)
                
                # Install interrupt hook if enabled
                if enable_interrupts:
                    self._install_interrupt_hook(workspace_path)
                
                workspace_paths[worker_id] = str(workspace_path)
                
            except Exception as e:
                print(f"❌ Error setting up {worker_id}: {e}")
                continue
        
        # Update PARALLEL_STATUS.json
        status_file = self.symphony_dir / "PARALLEL_STATUS.json"
        status = {
            "active_workspaces": workspace_paths,
            "workers": workers,
            "timestamp": datetime.now().isoformat(),
            "interrupts_enabled": enable_interrupts
        }
        
        with open(status_file, 'w') as f:
            json.dump(status, f, indent=2)
        
        print(f"\n✓ Set up {len(workspace_paths)} parallel workspaces")
        return workspace_paths
    
    def _copy_skeleton_files(self, workspace_path: Path, scope: str):
        """Copy relevant skeleton files to workspace."""
        # Parse scope pattern (e.g., "src/auth/**" -> "src/auth")
        scope_parts = scope.replace("**", "").replace("*", "").strip("/").split("/")
        source_dir = self.working_dir / Path(*scope_parts)
        
        if source_dir.exists():
            dest_dir = workspace_path / Path(*scope_parts)
            dest_dir.parent.mkdir(parents=True, exist_ok=True)
            
            if source_dir.is_dir():
                shutil.copytree(source_dir, dest_dir, dirs_exist_ok=True)
            else:
                shutil.copy2(source_dir, dest_dir)
            
            print(f"  Copied skeleton files from {source_dir}")
    
    def _install_interrupt_hook(self, workspace_path: Path):
        """Install interrupt monitoring hook in workspace."""
        hook_content = '''#!/usr/bin/env python3
"""Interrupt monitor hook for parallel workers."""

from pathlib import Path
import json

class InterruptMonitorHook:
    def __init__(self):
        self.interrupt_file = Path(".INTERRUPT")
        self.shown_interrupts = set()
    
    def pre_tool_use(self, tool_name, params):
        """Check for interrupts before each tool use."""
        if self.interrupt_file.exists():
            content = self.interrupt_file.read_text()
            interrupt_hash = hash(content)
            
            if interrupt_hash not in self.shown_interrupts:
                print(f"\\n⚠️ CRITICAL ARCHITECTURAL DISCOVERY:\\n{content}")
                print("Please adjust your approach accordingly.\\n")
                self.shown_interrupts.add(interrupt_hash)
            
            # Archive and clean up
            archive = Path(".chamber/.interrupt_history")
            archive.parent.mkdir(exist_ok=True)
            with open(archive, 'a') as f:
                f.write(f"\\n[{datetime.now().isoformat()}]\\n{content}\\n---\\n")
            
            self.interrupt_file.unlink()
        
        return True

# Hook registration
hook = InterruptMonitorHook()
'''
        
        hook_file = workspace_path / ".chamber" / "hooks" / "interrupt_monitor.py"
        hook_file.parent.mkdir(parents=True, exist_ok=True)
        hook_file.write_text(hook_content)
        hook_file.chmod(0o755)
        
        # Add to workspace settings
        settings_file = workspace_path / ".chamber" / "settings.local.json"
        settings = {
            "hooks": {
                "preToolUse": [str(hook_file.relative_to(workspace_path))]
            }
        }
        
        with open(settings_file, 'w') as f:
            json.dump(settings, f, indent=2)
        
        print(f"  Installed interrupt hook")
    
    def record_deviation(self, agent_id: str, module: str, deviation: Dict[str, Any]) -> bool:
        """
        Record an architectural deviation found during implementation.
        
        Args:
            agent_id: ID of the agent
            module: Module where deviation found
            deviation: Dict with:
                - expected: What skeleton/architecture specified
                - discovered: What was actually found
                - action_taken: What the agent did (stub/implement/skip)
                - reasoning: Why this approach
                - impact: Integration impact
                - severity: minor|major|fundamental
        """
        deviations_file = self.symphony_dir / "DEVIATIONS.json"
        
        if deviations_file.exists():
            with open(deviations_file) as f:
                deviations = json.load(f)
        else:
            deviations = {"deviations": [], "summary": {}}
        
        # Add timestamped deviation
        deviation_entry = {
            "timestamp": datetime.now().isoformat(),
            "agent_id": agent_id,
            "module": module,
            **deviation
        }
        deviations["deviations"].append(deviation_entry)
        
        # Update summary by severity
        severity = deviation.get("severity", "minor")
        if severity not in deviations["summary"]:
            deviations["summary"][severity] = 0
        deviations["summary"][severity] += 1
        
        with open(deviations_file, 'w') as f:
            json.dump(deviations, f, indent=2)
        
        print(f"✓ Recorded {severity} deviation from {agent_id}")
        return True
    
    def get_deviations(self) -> Dict:
        """Get all recorded deviations for orchestrator review."""
        deviations_file = self.symphony_dir / "DEVIATIONS.json"
        if not deviations_file.exists():
            return {"deviations": [], "summary": {}}
        
        with open(deviations_file) as f:
            return json.load(f)
    
    def share_discovery(self, agent_id: str, discovery: str, severity: str = "info", 
                       impact: str = "", affects: List[str] = None, 
                       requires_suspension: bool = False) -> bool:
        """
        Share a discovery from one agent.
        
        Args:
            agent_id: ID of discovering agent
            discovery: The discovery text
            severity: critical | important | info
            impact: Impact description
            affects: List of affected modules
        
        Returns:
            True if shared (critical only), False otherwise
        """
        # Only interrupt for critical discoveries
        if severity != "critical":
            # Log to discoveries file
            discoveries_file = self.symphony_dir / "DISCOVERIES.json"
            discoveries = []
            if discoveries_file.exists():
                with open(discoveries_file) as f:
                    discoveries = json.load(f)
            
            discoveries.append({
                "timestamp": datetime.now().isoformat(),
                "agent_id": agent_id,
                "severity": severity,
                "discovery": discovery,
                "impact": impact,
                "affects": affects or []
            })
            
            with open(discoveries_file, 'w') as f:
                json.dump(discoveries, f, indent=2)
            
            print(f"✓ Logged {severity} discovery from {agent_id}")
            return False
        
        # Critical discovery - interrupt other workers
        status_file = self.symphony_dir / "PARALLEL_STATUS.json"
        if not status_file.exists():
            print("⚠️ No active parallel workspaces to interrupt")
            return False
        
        with open(status_file) as f:
            status = json.load(f)
        
        interrupted = []
        for worker_id, workspace_path in status.get("active_workspaces", {}).items():
            if agent_id not in worker_id:  # Don't interrupt self
                interrupt_file = Path(workspace_path) / ".INTERRUPT"
                
                # Include suspension flag if architectural change
                action = "SUSPEND WORK - Await instructions" if requires_suspension else "Review and adjust your implementation approach"
                
                interrupt_content = f"""From: {agent_id}
Critical: {discovery}
Impact: {impact}
Affects: {', '.join(affects or [])}
Action Required: {action}
Suspension Required: {requires_suspension}
"""
                interrupt_file.write_text(interrupt_content)
                interrupted.append(worker_id)
                
                # If suspension required, create suspension marker
                if requires_suspension:
                    suspend_file = Path(workspace_path) / ".SUSPEND"
                    suspend_file.write_text(f"Suspended due to: {discovery}\nFrom: {agent_id}")
        
        if requires_suspension:
            print(f"🛑 CRITICAL discovery shared - SUSPENDED {len(interrupted)} workers")
        else:
            print(f"⚠️ CRITICAL discovery shared - interrupted {len(interrupted)} workers")
        return True
    
    def cleanup_workspaces(self, remove_branches: bool = True) -> int:
        """
        Clean up all parallel workspaces.
        
        Returns:
            Number of workspaces cleaned
        """
        cleaned = 0
        
        # Read active workspaces
        status_file = self.symphony_dir / "PARALLEL_STATUS.json"
        if not status_file.exists():
            print("No active workspaces to clean")
            return 0
        
        with open(status_file) as f:
            status = json.load(f)
        
        for worker_id, workspace_path in status.get("active_workspaces", {}).items():
            try:
                # Remove worktree (if using git)
                if self.use_git:
                    result = subprocess.run(
                        ["git", "worktree", "remove", workspace_path, "--force"],
                        cwd=self.working_dir,
                        capture_output=True,
                        text=True
                    )
                    
                    if result.returncode == 0:
                        print(f"✓ Removed worktree {worker_id}")
                        cleaned += 1
                else:
                    # Manual cleanup for non-git
                    print(f"✓ Ready to remove workspace {worker_id}")
                    cleaned += 1
                
                # Remove directory if still exists
                workspace_dir = Path(workspace_path)
                if workspace_dir.exists():
                    shutil.rmtree(workspace_dir)
                
            except Exception as e:
                print(f"⚠️ Error cleaning {worker_id}: {e}")
        
        # Clear status file
        status["active_workspaces"] = {}
        with open(status_file, 'w') as f:
            json.dump(status, f, indent=2)
        
        print(f"\n✓ Cleaned up {cleaned} workspaces")
        return cleaned
    
    def record_failure_analysis(self, phase: int, failure_type: str, 
                               analysis: Dict[str, Any]) -> bool:
        """
        Record why something failed and what to avoid/keep.
        
        Args:
            phase: Phase number where failure occurred
            failure_type: Type of failure (architecture|implementation|test|validation)
            analysis: Dict with keys:
                - what_failed: Brief description
                - why_failed: Root cause
                - avoid_next_time: List of things to avoid
                - keep_if_reworking: List of good parts to preserve
                - architectural_issues: Any design flaws found
        """
        failure_file = self.symphony_dir / "FAILURE_ANALYSIS.json"
        
        if failure_file.exists():
            with open(failure_file) as f:
                failures = json.load(f)
        else:
            failures = {"analyses": [], "patterns": {}}
        
        # Add new analysis
        analysis_entry = {
            "timestamp": datetime.now().isoformat(),
            "phase": phase,
            "failure_type": failure_type,
            **analysis
        }
        failures["analyses"].append(analysis_entry)
        
        # Extract patterns
        if failure_type not in failures["patterns"]:
            failures["patterns"][failure_type] = []
        
        # Add to patterns for quick reference
        pattern = {
            "avoid": analysis.get("avoid_next_time", []),
            "keep": analysis.get("keep_if_reworking", []),
            "architectural_issues": analysis.get("architectural_issues", [])
        }
        failures["patterns"][failure_type].append(pattern)
        
        with open(failure_file, 'w') as f:
            json.dump(failures, f, indent=2)
        
        print(f"✓ Recorded failure analysis for Phase {phase}")
        return True
    
    def get_failure_insights(self, phase: Optional[int] = None) -> Dict:
        """
        Get insights from previous failures.
        
        Returns:
            Dict with avoid/keep lists and architectural issues
        """
        failure_file = self.symphony_dir / "FAILURE_ANALYSIS.json"
        
        if not failure_file.exists():
            return {"avoid": [], "keep": [], "architectural_issues": []}
        
        with open(failure_file) as f:
            failures = json.load(f)
        
        # Aggregate insights
        insights = {
            "avoid": [],
            "keep": [],
            "architectural_issues": []
        }
        
        for analysis in failures.get("analyses", []):
            if phase is None or analysis["phase"] == phase:
                insights["avoid"].extend(analysis.get("avoid_next_time", []))
                insights["keep"].extend(analysis.get("keep_if_reworking", []))
                insights["architectural_issues"].extend(
                    analysis.get("architectural_issues", [])
                )
        
        # Deduplicate
        insights["avoid"] = list(set(insights["avoid"]))
        insights["keep"] = list(set(insights["keep"]))
        insights["architectural_issues"] = list(set(insights["architectural_issues"]))
        
        return insights
    
    def transition_phase(self, from_phase: int, to_phase: int, 
                        cleanup_workspaces: bool = False,
                        preserve: List[str] = None) -> bool:
        """
        Handle phase transition.
        
        Args:
            from_phase: Current phase number
            to_phase: Next phase number
            cleanup_workspaces: Whether to clean workspaces
            preserve: List of items to preserve
        
        Returns:
            Success boolean
        """
        # Update WORKFLOW_STATE.json
        workflow_file = self.symphony_dir / "WORKFLOW_STATE.json"
        if workflow_file.exists():
            with open(workflow_file) as f:
                workflow = json.load(f)
        else:
            workflow = {"completed_phases": []}
        
        workflow["current_phase"] = to_phase
        if from_phase not in workflow["completed_phases"]:
            workflow["completed_phases"].append(from_phase)
        workflow["last_transition"] = datetime.now().isoformat()
        
        with open(workflow_file, 'w') as f:
            json.dump(workflow, f, indent=2)
        
        # Update PHASE_PROGRESS.json
        progress_file = self.symphony_dir / "PHASE_PROGRESS.json"
        if progress_file.exists():
            with open(progress_file) as f:
                progress = json.load(f)
        else:
            progress = {}
        
        progress[f"phase_{from_phase}_completed"] = datetime.now().isoformat()
        progress[f"phase_{to_phase}_started"] = datetime.now().isoformat()
        progress["current_phase"] = to_phase
        
        with open(progress_file, 'w') as f:
            json.dump(progress, f, indent=2)
        
        # Clean workspaces if requested
        if cleanup_workspaces:
            self.cleanup_workspaces()
        
        print(f"✓ Transitioned from Phase {from_phase} to Phase {to_phase}")
        return True
    
    def get_mission(self) -> Dict:
        """Read and return mission context."""
        mission_file = self.symphony_dir / "MISSION_CONTEXT.json"
        if not mission_file.exists():
            return {}
        
        with open(mission_file) as f:
            return json.load(f)
    
    def update_mission(self, updates: Dict[str, Any], clarification_reason: str = None) -> bool:
        """Update the mission context as we learn.
        
        Args:
            updates: Dictionary of updates to apply
            clarification_reason: If mission understanding changed, why?
        """
        mission_file = self.symphony_dir / "MISSION_CONTEXT.json"
        
        if not mission_file.exists():
            print("⚠️ No mission context to update")
            return False
        
        with open(mission_file) as f:
            mission = json.load(f)
        
        # Update fields
        for key, value in updates.items():
            if key == "current_understanding" and value != mission.get("original_request"):
                # Mission understanding has changed
                if clarification_reason:
                    mission["clarifications_made"].append({
                        "timestamp": datetime.now().isoformat(),
                        "reason": clarification_reason,
                        "old": mission.get("current_understanding"),
                        "new": value
                    })
            
            if isinstance(mission.get(key), list) and isinstance(value, list):
                # Append to lists
                mission[key].extend(value)
            elif isinstance(mission.get(key), dict) and isinstance(value, dict):
                # Merge dicts
                mission[key].update(value)
            else:
                # Replace value
                mission[key] = value
        
        mission["last_updated"] = datetime.now().isoformat()
        
        with open(mission_file, 'w') as f:
            json.dump(mission, f, indent=2)
        
        print(f"✓ Updated MISSION_CONTEXT.json")
        return True
    
    def extract_business_logic(self, requirements_text: str) -> Dict:
        """Extract business logic from requirements.
        
        This would ideally call an agent, but for now provides structure.
        """
        business_logic = {
            "validations": [],
            "calculations": [],
            "state_transitions": [],
            "error_conditions": [],
            "examples": [],
            "edge_cases": [],
            "priorities": {
                "must_have": [],
                "should_have": [],
                "could_have": []
            }
        }
        
        # Store in separate file for reference
        logic_file = self.symphony_dir / "BUSINESS_LOGIC.json"
        with open(logic_file, 'w') as f:
            json.dump(business_logic, f, indent=2)
        
        # Also update mission context
        self.update_mission({"business_logic": business_logic})
        
        print(f"✓ Created BUSINESS_LOGIC.json")
        return business_logic
    
    def plan_integration_points(self, modules: List[str]) -> Dict:
        """Plan integration points before parallel work.
        
        Returns:
            Dictionary of shared interfaces and potential conflicts
        """
        integration_plan = {
            "shared_interfaces": [],
            "data_flow": [],
            "potential_conflicts": [],
            "shared_utilities_needed": [],
            "module_contracts": {}
        }
        
        # Store integration plan
        plan_file = self.symphony_dir / "INTEGRATION_PLAN.json"
        with open(plan_file, 'w') as f:
            json.dump(integration_plan, f, indent=2)
        
        print(f"✓ Created INTEGRATION_PLAN.json")
        return integration_plan
    
    def update_progress(self, key: str, value: Any) -> bool:
        """Update phase progress with a key-value pair."""
        progress_file = self.symphony_dir / "PHASE_PROGRESS.json"
        
        if progress_file.exists():
            with open(progress_file) as f:
                progress = json.load(f)
        else:
            progress = {}
        
        progress[key] = value
        progress["last_updated"] = datetime.now().isoformat()
        
        with open(progress_file, 'w') as f:
            json.dump(progress, f, indent=2)
        
        return True
    
    def _get_validation_command(self, module: str) -> str:
        """Get validation command for a module."""
        # Check for language-specific test commands
        if (self.working_dir / "package.json").exists():
            return f"npm test -- {module}"
        elif (self.working_dir / "requirements.txt").exists():
            return f"pytest tests/test_{module}.py"
        elif (self.working_dir / "go.mod").exists():
            return f"go test ./{module}/..."
        else:
            return "Run appropriate tests for your module"
    
    def _get_current_phase(self) -> str:
        """Get current phase from workflow state."""
        workflow_file = self.symphony_dir / "WORKFLOW_STATE.json"
        if workflow_file.exists():
            with open(workflow_file) as f:
                workflow = json.load(f)
                phase = workflow.get("current_phase", 1)
                phase_names = {
                    1: "Architecture",
                    2: "Implementation Skeleton", 
                    3: "Test Skeleton",
                    4: "Implementation",
                    5: "Test Implementation",
                    6: "Validation",
                    7: "Documentation"
                }
                return f"Phase {phase}: {phase_names.get(phase, 'Unknown')}"
        return "Phase 4: Implementation"  # Default
    
    def _get_worker_instructions(self, module: str) -> str:
        """Get specific instructions for a worker."""
        return f"""
FOCUS ON CRITICAL ITEMS FIRST:
1. Check your workspace for skeleton files to implement
2. Implement all TODOs in your module scope
3. Validate your work with the provided command

CONTEXT IS FOR AWARENESS:
- Read mission if you need to understand 'why'
- Check other workers only if you have integration questions

EXPLORE ONLY WHEN NEEDED:
- Look for interfaces when implementing contracts
- Check common registry before creating utilities
- Read boundaries only for integration points
"""
    
    def cleanup_task(self, archive: bool = True) -> bool:
        """
        Clean up task-specific files, preserve persistent knowledge.
        
        Args:
            archive: Whether to archive task files before deletion
        """
        # Files to keep forever (project learning)
        PERSISTENT_FILES = [
            "GOTCHAS.md",
            "CLAUDE.md",
            "MODULE_CACHE.json",
            "FAILURE_ANALYSIS.json"
        ]
        
        # Files to archive (might be useful)
        ARCHIVE_FILES = [
            "BUSINESS_LOGIC.json",
            "INTEGRATION_PLAN.json"
        ]
        
        # Files to purge (task-specific)
        PURGE_FILES = [
            "MISSION_CONTEXT.json",
            "PHASE_PROGRESS.json",
            "PARALLEL_STATUS.json",
            "WORKFLOW_STATE.json",
            "DISCOVERIES.json",
            "TASK_CONTEXT.json"
        ]
        
        # Create archive directory if archiving
        if archive:
            archive_dir = self.symphony_dir / "archive" / datetime.now().strftime("%Y%m%d_%H%M%S")
            archive_dir.mkdir(parents=True, exist_ok=True)
            print(f"✓ Created archive at {archive_dir}")
        
        # Process files
        for filename in ARCHIVE_FILES:
            filepath = self.symphony_dir / filename
            if filepath.exists() and archive:
                shutil.copy2(filepath, archive_dir / filename)
                print(f"  Archived {filename}")
                filepath.unlink()
        
        for filename in PURGE_FILES:
            filepath = self.symphony_dir / filename
            if filepath.exists():
                if archive:
                    shutil.copy2(filepath, archive_dir / filename)
                filepath.unlink()
                print(f"  Purged {filename}")
        
        # Clean up chambers directory
        if self.chambers_dir.exists():
            shutil.rmtree(self.chambers_dir)
            self.chambers_dir.mkdir()
            print("✓ Cleaned chambers directory")
        
        print(f"\n✓ Task cleanup complete (persistent files preserved)")
        return True
    
    def get_relevant_context(self, module: str, phase: int) -> Dict:
        """
        Extract only relevant context for a specific module and phase.
        
        Args:
            module: Module name (e.g., 'auth', 'database')
            phase: Current phase number
            
        Returns:
            Condensed context dictionary
        """
        context = {}
        
        # Get business logic relevant to module
        logic_file = self.symphony_dir / "BUSINESS_LOGIC.json"
        if logic_file.exists():
            with open(logic_file) as f:
                full_logic = json.load(f)
                # Extract only rules mentioning this module
                context["business_rules"] = [
                    rule for rule in full_logic.get("validations", [])
                    if module.lower() in rule.lower()
                ]
                context["calculations"] = [
                    calc for calc in full_logic.get("calculations", [])
                    if module.lower() in calc.lower()
                ]
        
        # Get mission understanding (not full original)
        mission = self.get_mission()
        context["current_understanding"] = mission.get("current_understanding", "")
        context["success_criteria"] = mission.get("success_criteria", [])
        
        # Get phase-specific info
        if phase == 4:  # Implementation
            # Get integration points for this module
            plan_file = self.symphony_dir / "INTEGRATION_PLAN.json"
            if plan_file.exists():
                with open(plan_file) as f:
                    plan = json.load(f)
                    context["integration_points"] = plan.get("module_contracts", {}).get(module, [])
        
        return context
    
    def merge_and_purge(self, deviations: Dict, architectural_decisions: Dict) -> Dict:
        """
        Merge work from chambers and purge based on architectural decisions.
        
        Args:
            deviations: Deviations found during implementation
            architectural_decisions: Decisions made about each deviation
                e.g., {"api_async": "convert_all_to_async"}
        
        Returns:
            Dict with merge results and purge list
        """
        merge_results = {
            "merged_files": [],
            "purged_sections": [],
            "architectural_changes": [],
            "preserved_patterns": []
        }
        
        # Store merge plan
        merge_file = self.symphony_dir / "MERGE_PLAN.json"
        merge_plan = {
            "timestamp": datetime.now().isoformat(),
            "deviations_count": len(deviations.get("deviations", [])),
            "decisions": architectural_decisions,
            "results": merge_results
        }
        
        with open(merge_file, 'w') as f:
            json.dump(merge_plan, f, indent=2)
        
        print(f"✓ Created merge plan based on {len(architectural_decisions)} decisions")
        return merge_results
    
    def _detect_git_environment(self) -> bool:
        """Detect if we're in a git repository."""
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--git-dir"],
                cwd=self.working_dir,
                capture_output=True,
                text=True
            )
            return result.returncode == 0
        except Exception:
            return False
    
    def validate_environment(self) -> bool:
        """Validate the environment is ready for orchestration."""
        # Check basic directory structure
        if not self.working_dir.exists():
            print(f"❌ Working directory does not exist: {self.working_dir}")
            return False
        
        # Check if we can create symphony directory
        try:
            self.symphony_dir.mkdir(exist_ok=True)
            test_file = self.symphony_dir / ".test"
            test_file.write_text("test")
            test_file.unlink()
        except Exception as e:
            print(f"❌ Cannot write to symphony directory: {e}")
            return False
        
        # Check git if available
        if self.use_git:
            try:
                result = subprocess.run(
                    ["git", "status", "--porcelain"],
                    cwd=self.working_dir,
                    capture_output=True,
                    text=True
                )
                if result.returncode != 0:
                    print("⚠️ Git repository has issues but continuing")
            except Exception:
                print("⚠️ Git command failed but continuing in non-git mode")
                self.use_git = False
        
        return True
    
    def merge_chambers_to_working_branch(self) -> Dict[str, Any]:
        """
        Merge each chamber's git branch back to working branch (NOT main/master).
        Uses proper git commands when in git repo, falls back to manual copying otherwise.
        NEVER pushes automatically.
        
        Returns:
            Dict with merge results and any conflicts
        """
        merge_results = {
            "merged_chambers": [],
            "conflicts": [],
            "manual_copies": [],
            "errors": [],
            "working_branch": None
        }
        
        # Read active workspaces
        status_file = self.symphony_dir / "PARALLEL_STATUS.json"
        if not status_file.exists():
            print("No active chambers to merge")
            return merge_results
        
        with open(status_file) as f:
            status = json.load(f)
        
        active_chambers = status.get("active_workspaces", {})
        if not active_chambers:
            print("No active chambers found")
            return merge_results
        
        if self.use_git:
            # Git-based merge
            try:
                # Get current working branch (not main/master)
                result = subprocess.run(
                    ["git", "branch", "--show-current"],
                    cwd=self.working_dir,
                    capture_output=True,
                    text=True
                )
                
                if result.returncode != 0:
                    merge_results["errors"].append("Could not determine current branch")
                    return merge_results
                
                working_branch = result.stdout.strip()
                merge_results["working_branch"] = working_branch
                
                print(f"Merging chambers to working branch: {working_branch}")
                
                # Merge each chamber's branch
                for chamber_id, chamber_path in active_chambers.items():
                    try:
                        # Determine branch name for this chamber
                        chamber_branch = f"conduct-{chamber_id}-{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                        
                        # Check if branch exists
                        result = subprocess.run(
                            ["git", "branch", "--list", chamber_branch],
                            cwd=self.working_dir,
                            capture_output=True,
                            text=True
                        )
                        
                        if not result.stdout.strip():
                            print(f"⚠️ Branch {chamber_branch} not found, skipping {chamber_id}")
                            continue
                        
                        # Attempt merge
                        result = subprocess.run(
                            ["git", "merge", chamber_branch, "--no-ff", "-m", f"Merge {chamber_id} implementation"],
                            cwd=self.working_dir,
                            capture_output=True,
                            text=True
                        )
                        
                        if result.returncode == 0:
                            merge_results["merged_chambers"].append(chamber_id)
                            print(f"✓ Merged chamber {chamber_id}")
                        else:
                            # Check for conflicts
                            if "CONFLICT" in result.stdout or "CONFLICT" in result.stderr:
                                conflicts = self._parse_git_conflicts(result.stderr)
                                merge_results["conflicts"].extend(conflicts)
                                print(f"⚠️ Conflicts found merging {chamber_id}")
                            else:
                                merge_results["errors"].append(f"Failed to merge {chamber_id}: {result.stderr}")
                        
                    except Exception as e:
                        merge_results["errors"].append(f"Error merging {chamber_id}: {str(e)}")
                        
            except Exception as e:
                merge_results["errors"].append(f"Git merge process failed: {str(e)}")
                print(f"❌ Git merge failed, falling back to manual copy: {e}")
                # Fall through to manual copy
        
        # Manual file copying (fallback or non-git)
        if not self.use_git or merge_results["errors"]:
            print("Using manual file copying")
            
            for chamber_id, chamber_path in active_chambers.items():
                try:
                    chamber_dir = Path(chamber_path)
                    if not chamber_dir.exists():
                        print(f"⚠️ Chamber directory not found: {chamber_path}")
                        continue
                    
                    # Copy all files from chamber to working directory
                    copied_files = self._copy_chamber_files(chamber_dir, self.working_dir)
                    
                    merge_results["manual_copies"].append({
                        "chamber": chamber_id,
                        "files_copied": copied_files
                    })
                    
                    print(f"✓ Manually copied {len(copied_files)} files from {chamber_id}")
                    
                except Exception as e:
                    merge_results["errors"].append(f"Error copying from {chamber_id}: {str(e)}")
        
        # Save merge results
        merge_file = self.symphony_dir / "MERGE_RESULTS.json"
        merge_data = {
            "timestamp": datetime.now().isoformat(),
            "results": merge_results
        }
        
        with open(merge_file, 'w') as f:
            json.dump(merge_data, f, indent=2)
        
        print(f"\n✓ Merge complete. Results saved to {merge_file}")
        if merge_results["conflicts"]:
            print(f"⚠️ {len(merge_results['conflicts'])} conflicts need resolution")
        
        return merge_results
    
    def _parse_git_conflicts(self, git_output: str) -> List[Dict[str, str]]:
        """Parse git conflict output to extract conflict details."""
        conflicts = []
        lines = git_output.split('\n')
        
        for line in lines:
            if "CONFLICT" in line and "Merge conflict" in line:
                # Extract file path from conflict message
                parts = line.split()
                if len(parts) > 3:
                    file_path = parts[-1]
                    conflicts.append({
                        "file": file_path,
                        "type": "merge_conflict",
                        "message": line.strip()
                    })
        
        return conflicts
    
    def _copy_chamber_files(self, chamber_dir: Path, target_dir: Path) -> List[str]:
        """Copy files from chamber to target directory, preserving structure."""
        copied_files = []
        
        # Skip .git directories and .chamber metadata
        skip_dirs = {".git", ".chamber", "__pycache__", ".pytest_cache"}
        
        for item in chamber_dir.rglob("*"):
            # Skip hidden dirs and files we don't want
            if any(part.startswith('.') and part in skip_dirs for part in item.parts):
                continue
            
            if item.is_file():
                # Calculate relative path from chamber root
                rel_path = item.relative_to(chamber_dir)
                target_path = target_dir / rel_path
                
                # Create parent directories if needed
                target_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Copy file
                shutil.copy2(item, target_path)
                copied_files.append(str(rel_path))
        
        return copied_files
    
    def format_architectural_decisions(self, high_level_decisions: Dict[str, str]) -> Dict[str, str]:
        """
        Convert high-level architectural decisions into specific, actionable instructions.
        
        Args:
            high_level_decisions: Dict of general decisions like {"api_pattern": "make_async"}
        
        Returns:
            Dict of specific instructions like {"api_pattern": "Convert auth/*.py API calls to async/await"}
        """
        actionable_decisions = {}
        
        for decision_key, high_level_value in high_level_decisions.items():
            if decision_key == "api_pattern":
                if "async" in high_level_value.lower():
                    actionable_decisions[decision_key] = "Convert auth/*.py API calls to async/await pattern"
                elif "rest" in high_level_value.lower():
                    actionable_decisions[decision_key] = "Implement RESTful endpoints in api/*.py files"
                elif "graphql" in high_level_value.lower():
                    actionable_decisions[decision_key] = "Replace REST endpoints with GraphQL schema in api/schema.py"
                else:
                    actionable_decisions[decision_key] = f"Update API pattern: {high_level_value}"
            
            elif decision_key == "data_structure":
                if "json" in high_level_value.lower():
                    actionable_decisions[decision_key] = "Use JSON format for data/*.py serialization methods"
                elif "orm" in high_level_value.lower():
                    actionable_decisions[decision_key] = "Replace raw SQL with ORM models in database/*.py"
                elif "nosql" in high_level_value.lower():
                    actionable_decisions[decision_key] = "Convert database/*.py to use NoSQL document structure"
                else:
                    actionable_decisions[decision_key] = f"Update data structure: {high_level_value}"
            
            elif decision_key == "auth_approach":
                if "oauth" in high_level_value.lower():
                    actionable_decisions[decision_key] = "Implement OAuth2 flow in auth/oauth.py"
                elif "jwt" in high_level_value.lower():
                    actionable_decisions[decision_key] = "Add JWT token validation to auth/jwt.py"
                elif "session" in high_level_value.lower():
                    actionable_decisions[decision_key] = "Use session-based auth in auth/session.py"
                else:
                    actionable_decisions[decision_key] = f"Update authentication: {high_level_value}"
            
            elif decision_key == "testing_strategy":
                if "integration" in high_level_value.lower():
                    actionable_decisions[decision_key] = "Focus on integration tests in tests/integration/"
                elif "unit" in high_level_value.lower():
                    actionable_decisions[decision_key] = "Add unit tests for all functions in tests/unit/"
                elif "e2e" in high_level_value.lower():
                    actionable_decisions[decision_key] = "Create end-to-end tests in tests/e2e/"
                else:
                    actionable_decisions[decision_key] = f"Update testing approach: {high_level_value}"
            
            elif decision_key == "error_handling":
                if "exception" in high_level_value.lower():
                    actionable_decisions[decision_key] = "Add try/catch blocks with specific exceptions in all modules"
                elif "result" in high_level_value.lower():
                    actionable_decisions[decision_key] = "Use Result<T, E> pattern for error returns in core/*.py"
                elif "logging" in high_level_value.lower():
                    actionable_decisions[decision_key] = "Add structured logging to all error paths"
                else:
                    actionable_decisions[decision_key] = f"Update error handling: {high_level_value}"
            
            else:
                # Generic conversion for unknown decision types
                actionable_decisions[decision_key] = f"Apply {decision_key} change: {high_level_value}"
        
        # Store the formatted decisions
        decisions_file = self.symphony_dir / "ARCHITECTURAL_DECISIONS.json"
        decisions_data = {
            "timestamp": datetime.now().isoformat(),
            "high_level": high_level_decisions,
            "actionable": actionable_decisions
        }
        
        with open(decisions_file, 'w') as f:
            json.dump(decisions_data, f, indent=2)
        
        print(f"✓ Formatted {len(actionable_decisions)} architectural decisions")
        return actionable_decisions


def main():
    """CLI interface for orchestration tools."""
    parser = argparse.ArgumentParser(description="Orchestration tools for /conduct")
    parser.add_argument("--working-dir", default=".", help="Working directory (default: current)")
    
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # create-mission command
    mission_parser = subparsers.add_parser("create-mission", help="Create mission context")
    mission_parser.add_argument("request", help="Original user request")
    mission_parser.add_argument("--criteria", help="Success criteria")
    
    # setup-workspaces command
    workspace_parser = subparsers.add_parser("setup-workspaces", help="Set up parallel workspaces")
    workspace_parser.add_argument("--workers", required=True, help="JSON string of workers")
    workspace_parser.add_argument("--no-interrupts", action="store_true", help="Disable interrupts")
    
    # setup-chambers command (alias for setup-workspaces)
    chambers_parser = subparsers.add_parser("setup-chambers", help="Set up parallel chamber workspaces")
    chambers_parser.add_argument("--workers", required=True, help="JSON string of workers")
    chambers_parser.add_argument("--no-interrupts", action="store_true", help="Disable interrupts")
    
    # share-discovery command
    discovery_parser = subparsers.add_parser("share-discovery", help="Share a discovery")
    discovery_parser.add_argument("--agent", required=True, help="Agent ID")
    discovery_parser.add_argument("--discovery", required=True, help="Discovery text")
    discovery_parser.add_argument("--severity", choices=["critical", "important", "info"], 
                                 default="info", help="Severity level")
    discovery_parser.add_argument("--impact", default="", help="Impact description")
    discovery_parser.add_argument("--affects", nargs="*", help="Affected modules")
    
    # cleanup command
    cleanup_parser = subparsers.add_parser("cleanup", help="Clean up workspaces")
    
    # transition command
    transition_parser = subparsers.add_parser("transition", help="Transition phases")
    transition_parser.add_argument("from_phase", type=int, help="Current phase")
    transition_parser.add_argument("to_phase", type=int, help="Next phase")
    transition_parser.add_argument("--cleanup", action="store_true", help="Clean workspaces")
    
    # record-failure command
    failure_parser = subparsers.add_parser("record-failure", help="Record failure analysis")
    failure_parser.add_argument("--phase", type=int, required=True, help="Phase where failure occurred")
    failure_parser.add_argument("--type", required=True, 
                               choices=["architecture", "implementation", "test", "validation"],
                               help="Type of failure")
    failure_parser.add_argument("--what", required=True, help="What failed")
    failure_parser.add_argument("--why", required=True, help="Why it failed")
    failure_parser.add_argument("--avoid", nargs="*", help="Things to avoid next time")
    failure_parser.add_argument("--keep", nargs="*", help="Good parts to preserve")
    failure_parser.add_argument("--architectural-issues", nargs="*", help="Design flaws found")
    
    # get-insights command
    insights_parser = subparsers.add_parser("get-insights", help="Get failure insights")
    insights_parser.add_argument("--phase", type=int, help="Specific phase (optional)")
    
    # update-mission command
    update_parser = subparsers.add_parser("update-mission", help="Update mission context")
    update_parser.add_argument("--key", required=True, help="Key to update")
    update_parser.add_argument("--value", required=True, help="New value")
    update_parser.add_argument("--reason", help="Reason for change (if changing understanding)")
    
    # extract-logic command
    logic_parser = subparsers.add_parser("extract-logic", help="Extract business logic")
    logic_parser.add_argument("--text", help="Requirements text (optional)")
    
    # plan-integration command
    integration_parser = subparsers.add_parser("plan-integration", help="Plan integration points")
    integration_parser.add_argument("--modules", nargs="*", help="Module names")
    
    # cleanup-task command
    cleanup_task_parser = subparsers.add_parser("cleanup-task", help="Clean up task-specific files")
    cleanup_task_parser.add_argument("--no-archive", action="store_true", help="Don't archive files")
    
    # record-deviation command
    deviation_parser = subparsers.add_parser("record-deviation", help="Record architectural deviation")
    deviation_parser.add_argument("--agent", required=True, help="Agent ID")
    deviation_parser.add_argument("--module", required=True, help="Module name")
    deviation_parser.add_argument("--severity", choices=["minor", "major", "fundamental"], 
                                 default="minor", help="Deviation severity")
    deviation_parser.add_argument("--expected", required=True, help="What was expected")
    deviation_parser.add_argument("--discovered", required=True, help="What was discovered")
    deviation_parser.add_argument("--action", help="Action taken")
    deviation_parser.add_argument("--reasoning", help="Why this approach")
    deviation_parser.add_argument("--impact", help="Integration impact")
    
    # get-deviations command
    get_deviations_parser = subparsers.add_parser("get-deviations", help="Get all deviations")
    
    # merge-chambers command
    merge_parser = subparsers.add_parser("merge-chambers", help="Merge chamber branches to working branch")
    
    # format-decisions command
    format_parser = subparsers.add_parser("format-decisions", help="Format architectural decisions")
    format_parser.add_argument("--decisions", required=True, help="JSON string of high-level decisions")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    # Initialize tools
    working_dir = Path(args.working_dir).absolute()
    tools = OrchestrationTools(str(working_dir))
    
    # Execute command
    if args.command == "create-mission":
        tools.create_mission_context(args.request, args.criteria or "")
    
    elif args.command == "setup-workspaces" or args.command == "setup-chambers":
        workers = json.loads(args.workers)
        tools.setup_parallel_workspaces(workers, enable_interrupts=not args.no_interrupts)
    
    elif args.command == "share-discovery":
        tools.share_discovery(
            args.agent, 
            args.discovery, 
            args.severity,
            args.impact,
            args.affects
        )
    
    elif args.command == "cleanup":
        tools.cleanup_workspaces()
    
    elif args.command == "transition":
        tools.transition_phase(args.from_phase, args.to_phase, args.cleanup)
    
    elif args.command == "record-failure":
        analysis = {
            "what_failed": args.what,
            "why_failed": args.why,
            "avoid_next_time": args.avoid or [],
            "keep_if_reworking": args.keep or [],
            "architectural_issues": args.architectural_issues or []
        }
        tools.record_failure_analysis(args.phase, args.type, analysis)
    
    elif args.command == "get-insights":
        insights = tools.get_failure_insights(args.phase)
        print(json.dumps(insights, indent=2))
    
    elif args.command == "update-mission":
        # Parse value as JSON if possible
        try:
            value = json.loads(args.value)
        except:
            value = args.value
        
        updates = {args.key: value}
        tools.update_mission(updates, args.reason)
    
    elif args.command == "extract-logic":
        tools.extract_business_logic(args.text or "")
    
    elif args.command == "plan-integration":
        tools.plan_integration_points(args.modules or [])
    
    elif args.command == "cleanup-task":
        tools.cleanup_task(archive=not args.no_archive)
    
    elif args.command == "record-deviation":
        deviation = {
            "expected": args.expected,
            "discovered": args.discovered,
            "action_taken": args.action or "documented",
            "reasoning": args.reasoning or "See code comments",
            "impact": args.impact or "Unknown",
            "severity": args.severity
        }
        tools.record_deviation(args.agent, args.module, deviation)
    
    elif args.command == "get-deviations":
        deviations = tools.get_deviations()
        print(json.dumps(deviations, indent=2))
    
    elif args.command == "merge-chambers":
        results = tools.merge_chambers_to_working_branch()
        print(json.dumps(results, indent=2))
    
    elif args.command == "format-decisions":
        decisions = json.loads(args.decisions)
        formatted = tools.format_architectural_decisions(decisions)
        print(json.dumps(formatted, indent=2))
    
    return 0


if __name__ == "__main__":
    sys.exit(main())