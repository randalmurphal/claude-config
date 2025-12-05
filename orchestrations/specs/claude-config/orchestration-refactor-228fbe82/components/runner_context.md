# Component: Runner Context Enhancement

## Purpose
Enhance the AgentRunner to automatically inject context before prompts and update context after responses. This enables context accumulation across agent calls.

## Location
`~/.claude/orchestrations/core/runner.py` (modified from moved file)

## Dependencies
- `context.py` (ContextManager)
- Existing runner.py code

## Changes to AgentRunner

### New Constructor Parameter

```python
class AgentRunner:
    def __init__(
        self,
        config: Config,
        work_dir: Path,
        context_manager: ContextManager | None = None,  # NEW
    ):
        self.config = config
        self.work_dir = work_dir
        self.context_manager = context_manager  # NEW
```

### Modified _format_prompt

```python
def _format_prompt(
    self,
    agent_config: AgentConfig,
    prompt: str,
    context: dict[str, Any] | None,
    component_id: str | None = None,  # NEW
) -> str:
    """Format prompt with template, context, AND persistent context."""
    parts = []

    # 1. Persistent context from files (NEW)
    if self.context_manager:
        persistent_ctx = self.context_manager.get_context_for_prompt(component_id)
        if persistent_ctx:
            parts.append(f"## Context from Previous Work\n\n{persistent_ctx}")

    # 2. Template (existing)
    if agent_config.prompt_template:
        template = self._load_template(agent_config.prompt_template)
        if template:
            parts.append(template)

    # 3. Task-specific prompt (existing)
    parts.append(prompt)

    # 4. Runtime context (existing)
    if context:
        context_str = "\n".join(f"{k}: {v}" for k, v in context.items())
        parts.append(f"## Runtime Context\n\n{context_str}")

    # 5. Context update instructions (NEW)
    if self.context_manager:
        parts.append(self._get_context_update_instructions())

    return "\n\n---\n\n".join(parts)

def _get_context_update_instructions(self) -> str:
    """Instructions for agent to provide context updates."""
    return """## Context Updates Required

Before completing, provide updates for future agents:
- What did you accomplish? (summary)
- What did you learn? (discoveries)
- What's blocking progress? (blockers)
- Any architectural decisions? (decisions)
- What should the next agent know? (for_next_agent)

Include these in your JSON response."""
```

### New Method: Update Context After Result

```python
def _update_context_from_result(
    self,
    result: AgentResult,
    component_id: str | None = None,
) -> None:
    """Update context files from agent result."""
    if not self.context_manager:
        return

    update = ContextUpdate(
        summary=result.get("summary", ""),
        discoveries=result.get("discoveries", []),
        blockers=result.get("blockers", []),
        decisions=result.get("decisions", []),
        for_next_agent=result.get("for_next_agent", ""),
    )

    if any([update.summary, update.discoveries, update.blockers,
            update.decisions, update.for_next_agent]):
        self.context_manager.update_from_result(update, component_id)
```

### Modified run() Method

```python
def run(
    self,
    agent_name: str,
    prompt: str,
    context: dict[str, Any] | None = None,
    model_override: str | None = None,
    timeout: int | None = None,
    component_id: str | None = None,  # NEW
) -> AgentResult:
    # ... existing code ...

    # Format prompt with context
    full_prompt = self._format_prompt(
        agent_config,
        prompt,
        context,
        component_id,  # NEW
    )

    # ... execute agent ...

    # Update context after successful execution (NEW)
    if result.success:
        self._update_context_from_result(result, component_id)

    return result
```

## Backwards Compatibility

- `context_manager` defaults to None
- If None, behavior is unchanged (no context injection)
- Existing code continues to work without modification

## Schema Updates

Add context fields to all agent schemas in `schemas.py`:

```python
CONTEXT_OUTPUT_FIELDS = {
    "summary": {"type": "string"},
    "discoveries": {"type": "array", "items": {"type": "string"}},
    "blockers": {"type": "array", "items": {"type": "string"}},
    "decisions": {"type": "array", "items": {"type": "string"}},
    "for_next_agent": {"type": "string"},
}
```
