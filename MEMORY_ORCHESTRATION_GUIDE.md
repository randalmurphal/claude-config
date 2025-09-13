# Memory MCP Orchestration System Guide

## Overview

This document describes the comprehensive Memory MCP-based orchestration system that replaces file-based context with intelligent memory management, maintains mission focus, and learns from every task.

## Core Principles

### 1. Mission as North Star
- The user's request IS the mission - no interpretation
- No success criteria or validation steps added
- Any deviation from the mission triggers clarification
- Mission stays visible at all times to prevent drift

### 2. Memory Hierarchy

```
Universal Knowledge
    ↓
Language Patterns
    ↓
Language-Specific
    ├── General (Python, JavaScript, etc.)
    ├── Tools (pytest, mypy, eslint, etc.)
    ├── Frameworks (Django, React, etc.)
    └── Libraries (pandas, requests, etc.)
    ↓
Project-Specific
    ├── Component A (auth_service)
    │   ├── General
    │   ├── Modules
    │   │   ├── oauth
    │   │   ├── jwt
    │   │   └── session
    │   └── Entities (specific classes/functions)
    ├── Component B (payment_service)
    └── Shared
        ├── Libraries
        └── Patterns
```

### 3. Fact vs Preference Separation

**Facts (Agents CAN add):**
- API behaviors discovered
- Performance measurements
- Tool quirks found
- Constraint discoveries
- Critical gotchas

**Preferences (ONLY users can add):**
- Code style choices
- Complexity preferences
- Naming conventions
- Architectural patterns
- Tool preferences

## Memory Loading Strategy

### Critical Memories: NO LIMIT
```python
# ALL critical memories are loaded
critical_memories = memory_mcp.query({
    "scope": relevant_scopes,
    "critical": True
    # NO LIMIT - if it's critical, it must be shown
})
```

### Non-Critical Memories: LIMITED
```python
# Helpful memories have limits
helpful_memories = memory_mcp.query({
    "scope": relevant_scopes,
    "critical": False,
    "limit": 5  # Reasonable limit to prevent overwhelm
})
```

## Migration from File-Based System

### File → Memory MCP Mapping

| Old File | New Memory MCP Location | Type |
|----------|------------------------|------|
| GOTCHAS.md | `memory:project.{component}.gotchas` | Facts |
| DECISION_MEMORY.json | `memory:project.{component}.decisions` | Facts |
| MODULE_CACHE.json | `memory:project.{component}.module_analysis` | Facts |
| FAILURE_MEMORY.json | `memory:task.failures` | Facts |
| COMMON_REGISTRY.json | `memory:project.shared.utilities` | Facts |
| BUSINESS_LOGIC.json | `memory:project.{component}.business_rules` | Facts |
| TASK_CONTEXT.json | REMOVED - use mission + memories | - |
| BOUNDARIES.json | `memory:task.architecture.boundaries` | Facts |
| Preferences (new) | `memory:preference.{scope}` | Preferences |

### What Stays in Filesystem
- WORKFLOW_STATE.json (active orchestration state only)
- Current mission/task tracking
- Active parallel work coordination

## Component Detection for Monorepos

The system automatically detects project structure:

```python
# Monorepo detection
project_structure = {
    "type": "monorepo",  # or "single"
    "components": ["auth_service", "payment_service", "user_service"],
    "shared_paths": ["shared", "common", "lib"]
}

# Component determination from mission
"Add OAuth to auth" → component: "auth_service"
"Update payment processing" → component: "payment_service"
"Fix shared utility" → component: "shared"
```

## Agent Context Building

Every agent receives context in this structure:

```
🎯 MISSION (Your North Star): [User's exact request]
📍 Component: [auth_service]
📦 Module: [oauth] (if applicable)

⚠️ CRITICAL FACTS (ALL must be considered):
  • [Every critical fact - no limit]
  • [With reasoning why it's critical]

📝 Helpful Context:
  • [Limited to 5 helpful facts]

💼 Style Preferences (HOW to implement):
  • [Limited to 3 preferences]

⚠️ ALIGNMENT REQUIREMENTS:
  • Stay focused on the mission above
  • Do NOT add unrequested features
  • Ask questions instead of making assumptions
```

## Deviation Detection

The system actively detects and prevents:

### Scope Creep
- "While we're at it..."
- "Might as well add..."
- "Bonus feature..."

**Response**: Refocus on mission

### Assumptions
- "I'll assume..."
- "Typically..."
- "Best practice is..."

**Response**: Generate clarifying questions

### Over-Engineering
- Unnecessary abstractions
- Complex patterns not requested
- Premature optimization

**Response**: Simplify approach

## Memory Storage Examples

### Agent Discovery (Fact)
```python
memory = {
    "type": "fact",
    "scope": "project.auth_service.modules.oauth",
    "observation": "OAuth tokens expire in 1hr not 24hr",
    "reasoning": "Provider documentation shows 3600 second TTL",
    "critical": True,
    "entity": "OAuthClient.refresh",
    "discovered_by": "agent_123",
    "task_id": "task_abc"
}
```

### User Preference
```python
memory = {
    "type": "preference",
    "scope": "preference.language.python",
    "rule": "Use single quotes for strings",
    "source": "user_feedback",
    "confidence": 0.95,
    "examples": ["'hello'", "'world'"]
}
```

## Learning System

### From Agent Discoveries
- Agents discover facts during implementation
- Facts are stored with appropriate scope
- Critical facts are always shown in future tasks

### From User Feedback
- User corrections create preferences
- Preferences guide HOW things are done
- Confidence increases with consistent feedback

### Evolution Over Time
```
Day 1: No memories
Day 30: ~100 facts, ~20 preferences
Day 365: Deep knowledge of codebase, precise user preferences
Result: Code comes out right the first time
```

## Practical Usage

### Starting Orchestration
```bash
# Initialize with mission
python memory_orchestration.py init "Add OAuth login with Google"

# Check alignment
python memory_orchestration.py check-alignment "mission" "agent output"
```

### During Orchestration
1. Mission extracted (no interpretation)
2. Component detected (for monorepos)
3. Memories loaded (critical + limited helpful)
4. Agents work with focused context
5. Discoveries stored as facts
6. User feedback creates preferences
7. System learns and improves

## Key Commands

### /conduct with Memory MCP
```
/conduct "Add OAuth login"
- Uses Memory MCP for all context
- No file reading for gotchas/decisions
- Maintains mission focus
- Detects deviations
```

### Status Check
```
/conduct status
Shows:
- Current mission (north star)
- Active component/module
- Memory statistics
- Alignment score
```

## Benefits

1. **No Context Overflow**: Agents get focused, relevant memories
2. **Mission Focus**: Constant alignment checking prevents drift
3. **Learning System**: Gets better with each task
4. **Monorepo Support**: Understands complex project structures
5. **Clean Separation**: Facts vs preferences clearly distinguished
6. **No Critical Limits**: ALL critical information always provided
7. **User Control**: Only users can set preferences

## Migration Checklist

- [ ] Install Memory MCP server
- [ ] Run migration script for existing files
- [ ] Update conductor to use conduct_v2.md
- [ ] Configure memory scopes for your project
- [ ] Start capturing discoveries and preferences

The system is designed to start simple and grow more intelligent over time, always maintaining focus on exactly what the user requested while learning their preferences for HOW things should be done.