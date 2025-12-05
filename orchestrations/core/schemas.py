"""JSON schemas for structured agent responses.

Each agent type has a defined response schema that enforces parseable output.
"""

from dataclasses import dataclass
from typing import Any


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
