# Orchestration System Improvements

## Core Problems Identified

### 1. Orchestration Overhead Dominates Mission
- Conductor manages 1500+ lines of mechanics instead of goals
- Main priority (#1 PRIORITY) buried under 48 lines of rules
- Agents receive 20+ context files when they need 2-3
- Lost signal-to-noise ratio

### 2. Template Explosion
- ~50 repetitive agent prompts with slight variations
- Each phase repeats similar context blocks
- Massive inline prompts throughout

### 3. Rigid Success Metrics Problem
- Setting validate/success stages creates checkbox mentality
- Agents optimize for passing tests, not achieving intent
- Misses the actual user intent and creative solutions

## Proposed Solutions

### 1. Intent-Driven Orchestration (Not Checklist)

```python
# .symphony/MISSION_INTENT.json
{
  "user_request": "Build auth system with OAuth2",  # Verbatim
  "intent": {
    "what": "Authentication system",
    "why": "Users need secure login",  # The REAL goal
    "how": "OAuth2 with provider flexibility",
    "constraints": ["Must support Google", "Extensible to other providers"],
    "non_goals": ["Don't over-engineer for providers not requested"]
  },
  "understanding": {
    "core_need": "Secure user authentication",
    "flexibility_points": ["Provider choice", "Token storage"],
    "quality_indicators": [  # Not pass/fail, but qualities
      "Clean separation of concerns",
      "Secure token handling",
      "Graceful error states",
      "Clear user feedback"
    ]
  },
  "evolution": []  # Track how understanding deepens
}
```

### 2. Progressive Understanding Model

Each phase deepens understanding rather than completing checkboxes:

```python
class EvolvingMission:
    def __init__(self, user_request):
        self.original = user_request
        self.current_understanding = extract_initial_intent(user_request)
        self.discoveries = []
    
    def deepen_understanding(self, phase, findings):
        """Each phase adds nuance, doesn't just check boxes"""
        # Building understanding, not just checking off tasks
        self.evolution.append({
            "phase": phase,
            "learned": findings["key_insights"],
            "adjusted": findings["changed_approach"]
        })
```

### 3. Context Layers with Purpose

Instead of pushing all context, create purposeful layers:

```python
# .symphony/CONTEXT_MAP.json
{
  "intent_layer": {  # WHY we're building (always visible)
    "files": ["MISSION_INTENT.json"],
    "purpose": "Understand the real goal"
  },
  "working_layer": {  # WHAT we're building (phase-specific)
    "architecture": ["BOUNDARIES.json", "DECISIONS.json"],
    "implementation": ["SKELETON.json", "CONTRACTS.json"],
    "validation": ["BEHAVIORS.json", "QUALITY.json"]
  },
  "reference_layer": {  # HOW to build well (on-demand)
    "standards": ["CLAUDE.md", "INVARIANTS.md"],
    "patterns": ["GOTCHAS.md", "COMMON_REGISTRY.json"]
  }
}
```

### 4. Agent Self-Direction

Agents discover what they need rather than being pushed everything:

```python
# .symphony/agents/{agent_id}/FOCUS.json
{
  "your_intent": "Enable secure Google login",  # Simplified from mission
  "your_contribution": "OAuth2 token management",  # Specific part
  "explore_for_context": {  # Self-directed discovery
    "must_understand": ["MISSION_INTENT.json"],
    "probably_need": ["BOUNDARIES.json"],
    "might_help": ["GOTCHAS.md"]
  }
}
```

### 5. Simplified Phase Structure

Reduce from 7 phases to 4 core phases:

```yaml
SIMPLIFIED_PHASES:
  1_UNDERSTAND:  # Combines old Phase 1A-1D
    - Extract requirements
    - Validate context (95% confidence gate)
    - Design architecture
    - Output: PLAN.json with clear deliverables
    
  2_BUILD:  # Combines old Phase 2-4
    - Create skeleton (auto-reviewed inline)
    - Implement code
    - Self-validate while building
    - Output: Working code
    
  3_VERIFY:  # Combines old Phase 5-6
    - Write tests against implementation
    - Run all validation
    - Fix issues immediately
    - Output: Validated, tested code
    
  4_COMPLETE:  # Old Phase 7
    - Update docs if needed
    - Report success
```

### 6. Intent Guardian Conductor

```python
class IntentGuardianConductor:
    def orchestrate(self):
        """Guard intent while allowing evolution"""
        
        for phase in PHASES:
            # 1. Remind everyone of intent (not tasks)
            phase_focus = self.create_phase_focus(phase, self.intent)
            
            # 2. Launch agents with focus + freedom
            agents = self.launch_with_intent(phase, phase_focus)
            
            # 3. Gather insights (not just completions)
            insights = self.collect_insights(agents)
            
            # 4. Check alignment with intent (not checklist)
            if self.drifting_from_intent(insights):
                self.realign_with_discussion()  # Not just "fix it"
            
            # 5. Evolve understanding
            self.understanding[phase] = insights
```

### 7. Template Extraction Strategy

Create `~/.claude/tools/prompt_factory.py` to centralize templates:

```python
INTENT_PRESERVING_TEMPLATES = {
    'architecture': """
        INTENT: {core_intent}
        
        Your goal is to design an architecture that achieves: {why}
        
        Consider:
        - What would make this excellent (not just functional)?
        - What patterns best serve the intent?
        - Where might complexity hide?
        
        You're not just completing a task - you're solving for {core_need}
        """
}
```

### 8. Continuous Alignment (Not Gates)

```python
# .symphony/ALIGNMENT_PULSE.json
{
  "checks": [
    {
      "phase": "architecture",
      "alignment": {
        "intent_served": "Designed extensible OAuth system",
        "concerns": "Might be over-engineering provider abstraction",
        "discussion": "Simplified to support 1-3 providers max"
      }
    }
  ],
  "drift_signals": [  # Not failures, but signals to discuss
    "complexity_growing",
    "original_constraint_challenged",
    "better_approach_found"
  ]
}
```

### 9. Orchestration Tool Intelligence

Move complexity from conductor to tool:

```python
class OrchestrationIntelligence:
    def suggest_next_action(self, current_state):
        """Tool suggests what makes sense next"""
        # Instead of rigid phase progression
        if self.needs_clarification():
            return "ask_user", self.generate_clarifying_questions()
        
        if self.ready_for_parallel():
            return "parallel_work", self.identify_parallel_opportunities()
    
    def generate_agent_context(self, agent_type, scope):
        """Tool generates minimal, focused context"""
        # Smart compression - include only what matters
        return {
            "intent": self.compress_intent_for(agent_type),
            "context": self.select_minimal_context(essential, relevant),
            "freedom": self.define_creative_freedom(agent_type)
        }
```

## Key Improvements

1. **Intent Over Tasks**: Agents understand WHY, not just WHAT
2. **Evolution Over Checkboxes**: Understanding deepens vs tasks complete  
3. **Pull Over Push**: Agents discover what they need
4. **Alignment Over Gates**: Continuous discussion vs pass/fail
5. **Compression Over Bloat**: Smart context selection
6. **Freedom with Focus**: Creative solutions within intent bounds

## Implementation Priority

1. **Start with Intent Extraction** (Immediate impact)
   - Simple JSON with intent/understanding/evolution
   - Every agent reads this first
   - Instant clarity improvement

2. **Extract Templates** (1-2 hours work)
   - Create prompt_factory.py
   - Move all inline prompts to templates
   - Reduces conduct.md by 60%

3. **Simplify Phases** (Breaking change but worth it)
   - Merge skeleton+review
   - Combine test skeleton+implementation
   - Reduce cognitive load by 50%

4. **Smart Context Discovery** (Gradual rollout)
   - Agents pull what they need
   - Reduce context passing by 75%
   - Better performance

## Results

**Before**: 
- Conductor juggles 1500 lines of orchestration
- Agents receive 20+ context files
- Goal buried in orchestration details
- Checkbox mentality

**After**: 
- Conductor follows simple 4-phase state machine
- Agents get mission intent + focus (2 files)
- Intent at top of every interaction
- Creative problem-solving within intent

## Next Steps

1. Explore Memory MCP integration for context persistence
2. Design intelligent context compression
3. Build feedback loops for continuous improvement
4. Create smart caching for repeated patterns