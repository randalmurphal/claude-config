#!/usr/bin/env python3
"""
Parallel Execution Validator - Ensures true parallel execution when claimed
"""

import json
import sys
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Set, Tuple

class ParallelExecutionValidator:
    def __init__(self):
        self.workflow_state_file = Path('.claude/WORKFLOW_STATE.json')
        self.boundaries_file = Path('.claude/BOUNDARIES.json')
        self.parallel_status_file = Path('.claude/PARALLEL_STATUS.json')
        self.resource_locks_file = Path('.claude/RESOURCE_LOCKS.json')
        
    def validate_parallel_claim(self, message: str) -> Dict:
        """Check if message claims parallel execution"""
        parallel_indicators = [
            r"parallel",
            r"simultaneously", 
            r"concurrent",
            r"at the same time",
            r"multiple.*agents",
            r"parallel.*tasks?"
        ]
        
        claims_parallel = any(re.search(pattern, message, re.IGNORECASE) 
                             for pattern in parallel_indicators)
        
        if not claims_parallel:
            return {"status": "pass", "reason": "No parallel execution claimed"}
            
        # Check for actual parallel Task invocations
        task_pattern = r"\[Task.*?\]|\bTask\s+tool"
        task_mentions = re.findall(task_pattern, message)
        
        if len(task_mentions) < 2:
            return {
                "status": "warning",
                "reason": "Claims parallel but only one or no Task tools found",
                "suggestion": "Use multiple Task tools in single response for true parallel execution"
            }
            
        return {"status": "pass", "reason": f"Found {len(task_mentions)} parallel tasks"}
    
    def check_workflow_phase(self) -> Dict:
        """Check if current phase allows parallelization"""
        if not self.workflow_state_file.exists():
            return {"status": "pass", "reason": "No workflow state, parallel allowed"}
            
        state = json.loads(self.workflow_state_file.read_text())
        current_phase = state.get('current_phase', '')
        
        # Phases that MUST be serial
        serial_phases = ['architecture', 'test_definition', 'final_validation']
        
        if current_phase in serial_phases:
            return {
                "status": "block",
                "reason": f"Phase '{current_phase}' requires serial execution",
                "suggestion": f"Complete {current_phase} phase before parallel work"
            }
            
        return {"status": "pass", "reason": f"Phase '{current_phase}' allows parallel execution"}
    
    def check_resource_conflicts(self, planned_tasks: List[Dict]) -> Dict:
        """Check if planned parallel tasks would conflict"""
        if not self.boundaries_file.exists():
            return {"status": "pass", "reason": "No boundaries defined"}
            
        boundaries = json.loads(self.boundaries_file.read_text())
        conflicts = []
        
        # Check each task pair for conflicts
        for i, task1 in enumerate(planned_tasks):
            for task2 in planned_tasks[i+1:]:
                # Check path overlaps
                paths1 = set(task1.get('paths', []))
                paths2 = set(task2.get('paths', []))
                
                if paths1 & paths2:  # Intersection
                    conflicts.append({
                        "task1": task1.get('name'),
                        "task2": task2.get('name'),
                        "conflicting_paths": list(paths1 & paths2)
                    })
        
        if conflicts:
            return {
                "status": "block",
                "reason": "Resource conflicts detected",
                "conflicts": conflicts,
                "suggestion": "Adjust task boundaries to avoid overlapping paths"
            }
            
        return {"status": "pass", "reason": "No resource conflicts"}
    
    def check_dependency_order(self, planned_tasks: List[Dict]) -> Dict:
        """Ensure dependencies are respected in parallel execution"""
        if not self.boundaries_file.exists():
            return {"status": "pass", "reason": "No boundaries defined"}
            
        boundaries = json.loads(self.boundaries_file.read_text())
        violations = []
        
        for task in planned_tasks:
            task_boundary = task.get('boundary')
            if not task_boundary:
                continue
                
            boundary_info = boundaries.get('boundaries', {}).get(task_boundary, {})
            dependencies = boundary_info.get('dependencies', [])
            
            # Check if any dependency is being modified in parallel
            for dep in dependencies:
                for other_task in planned_tasks:
                    if other_task == task:
                        continue
                    if dep in other_task.get('paths', []):
                        violations.append({
                            "task": task.get('name'),
                            "dependency": dep,
                            "conflict_with": other_task.get('name')
                        })
        
        if violations:
            return {
                "status": "block", 
                "reason": "Dependency violations in parallel execution",
                "violations": violations,
                "suggestion": "Ensure dependencies are complete before parallel work"
            }
            
        return {"status": "pass", "reason": "Dependencies respected"}
    
    def enforce_lock_acquisition(self, agent_id: str, paths: List[str]) -> Dict:
        """Enforce exclusive locks on paths"""
        locks = {}
        if self.resource_locks_file.exists():
            locks = json.loads(self.resource_locks_file.read_text())
        
        current_locks = locks.get('locks', [])
        
        # Check if any path is already locked
        for path in paths:
            for lock in current_locks:
                if path in lock.get('locked_paths', []):
                    if lock.get('agent_id') != agent_id:
                        return {
                            "status": "block",
                            "reason": f"Path {path} locked by {lock.get('agent_id')}",
                            "suggestion": "Wait for lock release or choose different paths"
                        }
        
        # Acquire locks
        new_lock = {
            "agent_id": agent_id,
            "locked_paths": paths,
            "lock_time": datetime.now().isoformat()
        }
        current_locks.append(new_lock)
        
        locks['locks'] = current_locks
        self.resource_locks_file.write_text(json.dumps(locks, indent=2))
        
        return {"status": "pass", "reason": f"Locks acquired for {len(paths)} paths"}
    
    def generate_parallel_prompt(self, tasks: List[Dict]) -> str:
        """Generate proper parallel execution prompt"""
        prompt = "PARALLEL EXECUTION REQUIRED:\n\n"
        prompt += "You MUST use multiple Task tools in this SINGLE response:\n\n"
        
        for i, task in enumerate(tasks, 1):
            prompt += f"Task {i}: {task.get('name')}\n"
            prompt += f"  Agent: {task.get('agent', 'general-purpose')}\n"
            prompt += f"  Scope: {', '.join(task.get('paths', []))}\n"
            prompt += f"  Dependencies: {', '.join(task.get('dependencies', ['none']))}\n\n"
        
        prompt += "Remember: All Task tools must be invoked in THIS response for true parallel execution.\n"
        prompt += "Do NOT claim parallel then execute serially."
        
        return prompt

def main():
    """Main validation logic"""
    validator = ParallelExecutionValidator()
    
    # Read from stdin if available (for hook integration)
    if not sys.stdin.isatty():
        message = sys.stdin.read()
        
        # Validate parallel claim
        result = validator.validate_parallel_claim(message)
        if result['status'] == 'warning':
            print(f"⚠️ PARALLEL EXECUTION WARNING: {result['reason']}")
            print(f"   Suggestion: {result.get('suggestion', '')}")
    
    # Check workflow phase
    phase_check = validator.check_workflow_phase()
    if phase_check['status'] == 'block':
        print(f"❌ BLOCKED: {phase_check['reason']}")
        sys.exit(1)
    
    # Example of generating parallel prompt
    example_tasks = [
        {
            "name": "Implement Trading Feature",
            "agent": "general-purpose",
            "paths": ["/src/features/trading/"],
            "dependencies": ["/common/types"]
        },
        {
            "name": "Implement Analysis Feature", 
            "agent": "general-purpose",
            "paths": ["/src/features/analysis/"],
            "dependencies": ["/common/types"]
        }
    ]
    
    # Check for conflicts
    conflict_check = validator.check_resource_conflicts(example_tasks)
    if conflict_check['status'] == 'block':
        print(f"❌ CONFLICTS: {conflict_check['reason']}")
        for conflict in conflict_check.get('conflicts', []):
            print(f"   {conflict}")
    
    print("✅ Parallel execution validation complete")

if __name__ == "__main__":
    main()