"""JSON schemas for structured agent responses.

Each agent type has a defined response schema that enforces parseable output.
Includes validation functions for schema enforcement at phase boundaries.
"""

import logging
from dataclasses import dataclass, field
from typing import Any

LOG = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Result of schema validation."""

    valid: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def __bool__(self) -> bool:
        """Allow using result in boolean context."""
        return self.valid


@dataclass
class AgentSchema:
    """Schema definition for an agent response."""

    name: str
    schema: dict[str, Any]
    description: str = ''

    def to_json_string(self) -> str:
        """Return schema as JSON string for CLI."""
        import json

        return json.dumps(self.schema, separators=(',', ':'))

    def validate(self, data: dict[str, Any]) -> ValidationResult:
        """Validate data against this schema.

        Args:
            data: Dictionary to validate

        Returns:
            ValidationResult with errors if any
        """
        return validate_against_schema(data, self.schema)


# Core issue structure used across validators
ISSUE_SCHEMA = {
    'type': 'object',
    'properties': {
        'severity': {'enum': ['critical', 'major', 'minor']},
        'file': {'type': 'string'},
        'line': {'type': 'integer'},
        'issue': {'type': 'string'},
        'fix': {'type': 'string'},
    },
    'required': ['severity', 'issue'],
}


# Registry of all schemas
SCHEMAS: dict[str, AgentSchema] = {}


def register_schema(schema: AgentSchema) -> AgentSchema:
    """Register a schema in the global registry."""
    SCHEMAS[schema.name] = schema
    return schema


def get_schema(name: str) -> AgentSchema:
    """Get a schema by name."""
    if name not in SCHEMAS:
        raise ValueError(
            f'Unknown schema: {name}. Available: {list(SCHEMAS.keys())}'
        )
    return SCHEMAS[name]


def validate_against_schema(
    data: dict[str, Any],
    schema: dict[str, Any],
    path: str = '',
) -> ValidationResult:
    """Validate data against a JSON schema.

    This is a lightweight validator for common patterns.
    For full JSON Schema Draft 7 support, use jsonschema library.

    Args:
        data: Dictionary to validate
        schema: JSON schema definition
        path: Current path for error messages

    Returns:
        ValidationResult with any errors/warnings
    """
    errors: list[str] = []
    warnings: list[str] = []

    if not isinstance(data, dict):
        if schema.get('type') == 'object':
            return ValidationResult(
                valid=False,
                errors=[
                    f'{path or "root"}: expected object, got {type(data).__name__}'
                ],
            )
        return ValidationResult(valid=True)

    schema.get('type', 'object')
    properties = schema.get('properties', {})
    required = schema.get('required', [])

    # Check required fields
    for req_field in required:
        if req_field not in data:
            errors.append(
                f'{path or "root"}: missing required field "{req_field}"'
            )

    # Validate each property
    for prop_name, prop_schema in properties.items():
        if prop_name not in data:
            continue

        value = data[prop_name]
        prop_path = f'{path}.{prop_name}' if path else prop_name
        prop_type = prop_schema.get('type')

        # Type validation
        if prop_type == 'string' and not isinstance(value, str):
            errors.append(
                f'{prop_path}: expected string, got {type(value).__name__}'
            )
        elif prop_type == 'integer' and not isinstance(value, int):
            errors.append(
                f'{prop_path}: expected integer, got {type(value).__name__}'
            )
        elif prop_type == 'number' and not isinstance(value, (int, float)):
            errors.append(
                f'{prop_path}: expected number, got {type(value).__name__}'
            )
        elif prop_type == 'boolean' and not isinstance(value, bool):
            errors.append(
                f'{prop_path}: expected boolean, got {type(value).__name__}'
            )
        elif prop_type == 'array' and not isinstance(value, list):
            errors.append(
                f'{prop_path}: expected array, got {type(value).__name__}'
            )
        elif prop_type == 'object' and not isinstance(value, dict):
            errors.append(
                f'{prop_path}: expected object, got {type(value).__name__}'
            )

        # Enum validation
        if 'enum' in prop_schema and value not in prop_schema['enum']:
            errors.append(
                f'{prop_path}: value "{value}" not in enum {prop_schema["enum"]}'
            )

        # Nested object validation
        if prop_type == 'object' and isinstance(value, dict):
            nested_result = validate_against_schema(
                value, prop_schema, prop_path
            )
            errors.extend(nested_result.errors)
            warnings.extend(nested_result.warnings)

        # Array item validation
        if prop_type == 'array' and isinstance(value, list):
            item_schema = prop_schema.get('items', {})
            for i, item in enumerate(value):
                item_path = f'{prop_path}[{i}]'
                if item_schema.get('type') == 'object':
                    item_result = validate_against_schema(
                        item, item_schema, item_path
                    )
                    errors.extend(item_result.errors)
                    warnings.extend(item_result.warnings)
                elif 'enum' in item_schema and item not in item_schema['enum']:
                    errors.append(
                        f'{item_path}: value "{item}" not in enum {item_schema["enum"]}'
                    )

    return ValidationResult(
        valid=len(errors) == 0,
        errors=errors,
        warnings=warnings,
    )


def validate_agent_output(
    agent_name: str,
    output: dict[str, Any],
    schema_name: str | None = None,
) -> ValidationResult:
    """Validate agent output against its registered schema.

    Args:
        agent_name: Name of the agent
        output: Agent's output data
        schema_name: Optional override schema name (defaults to agent_name)

    Returns:
        ValidationResult

    Raises:
        ValueError: If no schema is registered for this agent
    """
    schema_key = schema_name or agent_name

    if schema_key not in SCHEMAS:
        # No schema registered - can't validate
        LOG.warning(f'No schema registered for agent: {agent_name}')
        return ValidationResult(
            valid=True,
            warnings=[f'No schema registered for agent: {agent_name}'],
        )

    schema = SCHEMAS[schema_key]
    result = schema.validate(output)

    if not result.valid:
        LOG.warning(
            f'Agent {agent_name} output validation failed: {result.errors}'
        )
    else:
        LOG.debug(f'Agent {agent_name} output validated successfully')

    return result


# =============================================================================
# SPEC PARSING SCHEMAS
# =============================================================================

register_schema(
    AgentSchema(
        name='spec_parser',
        description='Parse SPEC.md and extract components with dependencies',
        schema={
            'type': 'object',
            'properties': {
                'status': {'enum': ['success', 'error']},
                'components': {
                    'type': 'array',
                    'items': {
                        'type': 'object',
                        'properties': {
                            'file': {'type': 'string'},
                            'purpose': {'type': 'string'},
                            'depends_on': {
                                'type': 'array',
                                'items': {'type': 'string'},
                            },
                            'complexity': {'enum': ['low', 'medium', 'high']},
                        },
                        'required': ['file', 'depends_on'],
                    },
                },
                'quality_requirements': {
                    'type': 'array',
                    'items': {'type': 'string'},
                },
                'success_criteria': {
                    'type': 'array',
                    'items': {'type': 'string'},
                },
                'error': {'type': 'string'},
            },
            'required': ['status'],
        },
    )
)


# =============================================================================
# IMPACT ANALYSIS SCHEMAS
# =============================================================================

register_schema(
    AgentSchema(
        name='impact_analysis',
        description='Analyze blast radius of changes',
        schema={
            'type': 'object',
            'properties': {
                'status': {'enum': ['success', 'error']},
                'files_to_modify': {'type': 'integer'},
                'direct_dependents': {'type': 'integer'},
                'transitive_dependents': {'type': 'integer'},
                'critical_dependencies': {
                    'type': 'array',
                    'items': {
                        'type': 'object',
                        'properties': {
                            'file': {'type': 'string'},
                            'imported_by': {'type': 'integer'},
                            'risk': {'type': 'string'},
                        },
                    },
                },
                'recommendations': {
                    'type': 'array',
                    'items': {'type': 'string'},
                },
                'risk_level': {'enum': ['low', 'medium', 'high', 'critical']},
                'error': {'type': 'string'},
            },
            'required': ['status'],
        },
    )
)


# =============================================================================
# BUILDER SCHEMAS
# =============================================================================

register_schema(
    AgentSchema(
        name='skeleton_builder',
        description='Create file structure with signatures but no implementation',
        schema={
            'type': 'object',
            'properties': {
                'status': {'enum': ['complete', 'blocked']},
                'files_created': {
                    'type': 'array',
                    'items': {'type': 'string'},
                },
                'files_modified': {
                    'type': 'array',
                    'items': {'type': 'string'},
                },
                'blockers': {
                    'type': 'array',
                    'items': {'type': 'string'},
                },
                'summary': {'type': 'string'},
            },
            'required': ['status', 'summary'],
        },
    )
)

register_schema(
    AgentSchema(
        name='implementation',
        description='Fill skeleton stubs with production code',
        schema={
            'type': 'object',
            'properties': {
                'status': {'enum': ['complete', 'partial', 'blocked']},
                'files_modified': {
                    'type': 'array',
                    'items': {'type': 'string'},
                },
                'stubs_filled': {'type': 'integer'},
                'stubs_remaining': {'type': 'integer'},
                'blockers': {
                    'type': 'array',
                    'items': {'type': 'string'},
                },
                'discoveries': {
                    'type': 'array',
                    'items': {'type': 'string'},
                },
                'summary': {'type': 'string'},
            },
            'required': ['status', 'summary'],
        },
    )
)


# =============================================================================
# VALIDATION SCHEMAS
# =============================================================================

register_schema(
    AgentSchema(
        name='validator',
        description='Review code and report issues',
        schema={
            'type': 'object',
            'properties': {
                'status': {'enum': ['pass', 'fail']},
                'issues': {
                    'type': 'array',
                    'items': ISSUE_SCHEMA,
                },
                'summary': {'type': 'string'},
                'focus_area': {'type': 'string'},
            },
            'required': ['status', 'issues', 'summary'],
        },
    )
)

register_schema(
    AgentSchema(
        name='fix_executor',
        description='Fix reported issues',
        schema={
            'type': 'object',
            'properties': {
                'status': {'enum': ['fixed', 'partial', 'blocked']},
                'fixed_issues': {
                    'type': 'array',
                    'items': {'type': 'string'},
                },
                'remaining_issues': {
                    'type': 'array',
                    'items': {'type': 'string'},
                },
                'blockers': {
                    'type': 'array',
                    'items': {'type': 'string'},
                },
                'files_modified': {
                    'type': 'array',
                    'items': {'type': 'string'},
                },
                'summary': {'type': 'string'},
            },
            'required': ['status', 'summary'],
        },
    )
)


# =============================================================================
# VOTING SCHEMAS
# =============================================================================

register_schema(
    AgentSchema(
        name='impact_vote',
        description='Vote on mitigation strategy for high-impact changes',
        schema={
            'type': 'object',
            'properties': {
                'vote': {
                    'enum': [
                        'BACKWARD_COMPATIBLE',
                        'COORDINATED_ROLLOUT',
                        'INCREMENTAL_MIGRATION',
                        'REDESIGN_NEEDED',
                    ]
                },
                'confidence': {'type': 'number', 'minimum': 0, 'maximum': 1},
                'risk_level': {'enum': ['low', 'medium', 'high', 'critical']},
                'reasoning': {'type': 'string'},
                'concerns': {
                    'type': 'array',
                    'items': {'type': 'string'},
                },
                'mitigation_steps': {
                    'type': 'array',
                    'items': {'type': 'string'},
                },
            },
            'required': ['vote', 'confidence', 'reasoning'],
        },
    )
)

register_schema(
    AgentSchema(
        name='fix_strategy_vote',
        description='Vote on fix strategy when same issue repeats',
        schema={
            'type': 'object',
            'properties': {
                'vote': {'enum': ['FIX_IN_PLACE', 'REFACTOR', 'ESCALATE']},
                'confidence': {'type': 'number', 'minimum': 0, 'maximum': 1},
                'reasoning': {'type': 'string'},
                'issue_type': {'type': 'string'},
                'root_cause': {'type': 'string'},
                'recommended_action': {'type': 'string'},
                'spec_change_needed': {'type': 'boolean'},
            },
            'required': ['vote', 'confidence', 'reasoning', 'root_cause'],
        },
    )
)

register_schema(
    AgentSchema(
        name='production_ready_vote',
        description='Vote on production readiness',
        schema={
            'type': 'object',
            'properties': {
                'vote': {'enum': ['READY', 'NEEDS_WORK', 'RISKY']},
                'confidence': {'type': 'number', 'minimum': 0, 'maximum': 1},
                'reasoning': {'type': 'string'},
                'blockers': {
                    'type': 'array',
                    'items': {'type': 'string'},
                },
                'concerns': {
                    'type': 'array',
                    'items': {'type': 'string'},
                },
                'suggestions': {
                    'type': 'array',
                    'items': {'type': 'string'},
                },
            },
            'required': ['vote', 'confidence', 'reasoning'],
        },
    )
)


# =============================================================================
# TEST SCHEMAS
# =============================================================================

register_schema(
    AgentSchema(
        name='test_runner',
        description='Run tests and report results',
        schema={
            'type': 'object',
            'properties': {
                'status': {'enum': ['pass', 'fail', 'error']},
                'tests_run': {'type': 'integer'},
                'tests_passed': {'type': 'integer'},
                'tests_failed': {'type': 'integer'},
                'failures': {
                    'type': 'array',
                    'items': {
                        'type': 'object',
                        'properties': {
                            'test': {'type': 'string'},
                            'error': {'type': 'string'},
                            'file': {'type': 'string'},
                        },
                    },
                },
                'coverage': {'type': 'number'},
                'summary': {'type': 'string'},
            },
            'required': ['status', 'summary'],
        },
    )
)
