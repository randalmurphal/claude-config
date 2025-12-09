"""Unit tests for cc_orchestrations.core.schemas.

Tests schema registration, validation logic, and agent output validation.
"""

import pytest

from cc_orchestrations.core.schemas import (
    SCHEMAS,
    AgentSchema,
    ValidationResult,
    get_schema,
    register_schema,
    validate_against_schema,
    validate_agent_output,
)


class TestValidationResult:
    """Tests for ValidationResult dataclass."""

    def test_valid_result_is_truthy(self):
        """Valid result should be truthy."""
        result = ValidationResult(valid=True)
        assert result
        assert bool(result) is True

    def test_invalid_result_is_falsy(self):
        """Invalid result should be falsy."""
        result = ValidationResult(valid=False, errors=['Something went wrong'])
        assert not result
        assert bool(result) is False

    def test_result_with_warnings_still_valid(self):
        """Result with warnings but no errors is still valid."""
        result = ValidationResult(
            valid=True,
            warnings=['Consider refactoring this'],
        )
        assert result
        assert len(result.warnings) == 1

    def test_result_with_errors_and_warnings(self):
        """Result with both errors and warnings."""
        result = ValidationResult(
            valid=False,
            errors=['Missing field X', 'Invalid type Y'],
            warnings=['Consider Z'],
        )
        assert not result
        assert len(result.errors) == 2
        assert len(result.warnings) == 1


class TestAgentSchema:
    """Tests for AgentSchema dataclass."""

    def test_schema_creation(self):
        """Test basic schema creation."""
        schema = AgentSchema(
            name='test-schema',
            schema={'type': 'object'},
            description='A test schema',
        )
        assert schema.name == 'test-schema'
        assert schema.description == 'A test schema'

    def test_to_json_string(self):
        """Test JSON serialization for CLI."""
        schema = AgentSchema(
            name='test',
            schema={
                'type': 'object',
                'properties': {'name': {'type': 'string'}},
            },
        )
        json_str = schema.to_json_string()
        assert '"type":"object"' in json_str
        assert '"properties"' in json_str
        # Should be compact (no spaces)
        assert ' ' not in json_str

    def test_validate_method(self):
        """Test the validate method on AgentSchema."""
        schema = AgentSchema(
            name='test',
            schema={
                'type': 'object',
                'properties': {'status': {'type': 'string'}},
                'required': ['status'],
            },
        )

        # Valid data
        result = schema.validate({'status': 'ok'})
        assert result.valid

        # Missing required field
        result = schema.validate({})
        assert not result.valid
        assert any('status' in e for e in result.errors)


class TestSchemaRegistry:
    """Tests for schema registration and retrieval."""

    def test_get_known_schema(self):
        """Test getting a registered schema."""
        # These are registered at module load time
        schema = get_schema('validator')
        assert schema is not None
        assert schema.name == 'validator'

    def test_get_unknown_schema_raises(self):
        """Test that unknown schema raises ValueError."""
        with pytest.raises(ValueError, match='Unknown schema'):
            get_schema('nonexistent_schema_xyz')

    def test_register_new_schema(self):
        """Test registering a new schema."""
        test_schema = AgentSchema(
            name='test_registration_schema',
            schema={'type': 'object'},
            description='Test schema for registration',
        )

        result = register_schema(test_schema)
        assert result is test_schema
        assert 'test_registration_schema' in SCHEMAS

        # Should be retrievable
        retrieved = get_schema('test_registration_schema')
        assert retrieved.name == 'test_registration_schema'

    def test_builtin_schemas_exist(self):
        """Test that expected built-in schemas exist."""
        expected_schemas = [
            'spec_parser',
            'impact_analysis',
            'skeleton_builder',
            'implementation',
            'validator',
            'fix_executor',
            'impact_vote',
            'fix_strategy_vote',
            'production_ready_vote',
            'test_runner',
        ]

        for name in expected_schemas:
            assert name in SCHEMAS, f'Missing built-in schema: {name}'


class TestValidateAgainstSchema:
    """Tests for validate_against_schema function."""

    def test_validate_simple_object(self):
        """Test validating a simple object."""
        schema = {
            'type': 'object',
            'properties': {
                'name': {'type': 'string'},
                'count': {'type': 'integer'},
            },
            'required': ['name'],
        }

        # Valid
        result = validate_against_schema({'name': 'test', 'count': 5}, schema)
        assert result.valid

        # Missing required field
        result = validate_against_schema({'count': 5}, schema)
        assert not result.valid
        assert any('name' in e for e in result.errors)

    def test_validate_type_checking(self):
        """Test type validation."""
        schema = {
            'type': 'object',
            'properties': {
                'name': {'type': 'string'},
                'count': {'type': 'integer'},
                'rate': {'type': 'number'},
                'active': {'type': 'boolean'},
            },
        }

        # Correct types
        result = validate_against_schema(
            {'name': 'test', 'count': 5, 'rate': 3.14, 'active': True},
            schema,
        )
        assert result.valid

        # Wrong types
        result = validate_against_schema(
            {'name': 123, 'count': 'five'},
            schema,
        )
        assert not result.valid
        assert len(result.errors) >= 2

    def test_validate_enum(self):
        """Test enum validation."""
        schema = {
            'type': 'object',
            'properties': {
                'severity': {'enum': ['critical', 'major', 'minor']},
            },
        }

        # Valid enum value
        result = validate_against_schema({'severity': 'major'}, schema)
        assert result.valid

        # Invalid enum value
        result = validate_against_schema({'severity': 'high'}, schema)
        assert not result.valid
        assert any('enum' in e for e in result.errors)

    def test_validate_nested_object(self):
        """Test validation of nested objects."""
        schema = {
            'type': 'object',
            'properties': {
                'metadata': {
                    'type': 'object',
                    'properties': {
                        'version': {'type': 'string'},
                    },
                    'required': ['version'],
                },
            },
        }

        # Valid nested
        result = validate_against_schema(
            {'metadata': {'version': '1.0.0'}},
            schema,
        )
        assert result.valid

        # Invalid nested - missing required
        result = validate_against_schema(
            {'metadata': {}},
            schema,
        )
        assert not result.valid

    def test_validate_array(self):
        """Test validation of arrays."""
        schema = {
            'type': 'object',
            'properties': {
                'items': {
                    'type': 'array',
                    'items': {'type': 'string'},
                },
            },
        }

        # Valid array
        result = validate_against_schema(
            {'items': ['a', 'b', 'c']},
            schema,
        )
        assert result.valid

        # Wrong type (not an array)
        result = validate_against_schema(
            {'items': 'not-an-array'},
            schema,
        )
        assert not result.valid

    def test_validate_array_with_enum_items(self):
        """Test validation of array with enum items."""
        schema = {
            'type': 'object',
            'properties': {
                'levels': {
                    'type': 'array',
                    'items': {'enum': ['low', 'medium', 'high']},
                },
            },
        }

        # Valid
        result = validate_against_schema(
            {'levels': ['low', 'high']},
            schema,
        )
        assert result.valid

        # Invalid enum in array
        result = validate_against_schema(
            {'levels': ['low', 'extreme']},
            schema,
        )
        assert not result.valid

    def test_validate_array_with_object_items(self):
        """Test validation of array with object items."""
        schema = {
            'type': 'object',
            'properties': {
                'issues': {
                    'type': 'array',
                    'items': {
                        'type': 'object',
                        'properties': {
                            'severity': {
                                'enum': ['critical', 'major', 'minor']
                            },
                            'issue': {'type': 'string'},
                        },
                        'required': ['severity', 'issue'],
                    },
                },
            },
        }

        # Valid
        result = validate_against_schema(
            {'issues': [{'severity': 'major', 'issue': 'Test issue'}]},
            schema,
        )
        assert result.valid

        # Invalid - missing required in array item
        result = validate_against_schema(
            {'issues': [{'severity': 'major'}]},
            schema,
        )
        assert not result.valid

    def test_validate_non_dict_input(self):
        """Test validation with non-dict input."""
        schema = {'type': 'object'}

        # Non-dict should fail for object schema
        result = validate_against_schema('not a dict', schema)  # type: ignore
        assert not result.valid
        assert any('expected object' in e for e in result.errors)

    def test_validate_with_path_tracking(self):
        """Test that error paths are correctly tracked."""
        schema = {
            'type': 'object',
            'properties': {
                'outer': {
                    'type': 'object',
                    'properties': {
                        'inner': {'type': 'string'},
                    },
                },
            },
        }

        result = validate_against_schema(
            {'outer': {'inner': 123}},  # Wrong type for inner
            schema,
        )
        assert not result.valid
        # Should have path in error
        assert any('outer.inner' in e for e in result.errors)


class TestValidateAgentOutput:
    """Tests for validate_agent_output function."""

    def test_validate_with_registered_schema(self):
        """Test validation against a registered schema."""
        # Use the 'validator' schema which requires status, issues, summary
        result = validate_agent_output(
            'validator',
            {
                'status': 'pass',
                'issues': [],
                'summary': 'All good',
            },
        )
        assert result.valid

    def test_validate_with_invalid_output(self):
        """Test validation with invalid output."""
        # Missing required fields for validator schema
        result = validate_agent_output(
            'validator',
            {'status': 'pass'},  # Missing issues and summary
        )
        assert not result.valid

    def test_validate_unknown_agent(self):
        """Test validation with unknown agent (no schema)."""
        result = validate_agent_output(
            'unknown_agent_xyz',
            {'anything': 'goes'},
        )
        # Should return valid=True with warning (no schema to validate against)
        assert result.valid
        assert len(result.warnings) > 0

    def test_validate_with_schema_override(self):
        """Test validation with explicit schema name."""
        result = validate_agent_output(
            'some-custom-agent',
            {
                'status': 'pass',
                'issues': [],
                'summary': 'Done',
            },
            schema_name='validator',  # Use validator schema
        )
        assert result.valid


class TestBuiltinSchemas:
    """Tests for built-in schema definitions."""

    def test_validator_schema_structure(self):
        """Test the validator schema structure."""
        schema = get_schema('validator')
        assert 'status' in schema.schema['properties']
        assert 'issues' in schema.schema['properties']
        assert 'summary' in schema.schema['properties']
        assert 'status' in schema.schema['required']

    def test_skeleton_builder_schema(self):
        """Test skeleton_builder schema."""
        schema = get_schema('skeleton_builder')
        assert 'status' in schema.schema['properties']
        assert 'files_created' in schema.schema['properties']

    def test_implementation_schema(self):
        """Test implementation schema."""
        schema = get_schema('implementation')
        assert 'status' in schema.schema['properties']
        assert 'files_modified' in schema.schema['properties']
        assert 'stubs_filled' in schema.schema['properties']

    def test_vote_schemas_have_required_fields(self):
        """Test that vote schemas have vote, confidence, reasoning."""
        vote_schemas = [
            'impact_vote',
            'fix_strategy_vote',
            'production_ready_vote',
        ]

        for name in vote_schemas:
            schema = get_schema(name)
            assert 'vote' in schema.schema['properties'], f'{name} missing vote'
            assert 'confidence' in schema.schema['properties'], (
                f'{name} missing confidence'
            )
            assert 'reasoning' in schema.schema['properties'], (
                f'{name} missing reasoning'
            )
            assert 'vote' in schema.schema['required'], (
                f'{name} vote not required'
            )
            assert 'confidence' in schema.schema['required']
            assert 'reasoning' in schema.schema['required']

    def test_spec_parser_schema(self):
        """Test spec_parser schema structure."""
        schema = get_schema('spec_parser')
        assert 'status' in schema.schema['properties']
        assert 'components' in schema.schema['properties']
        # Components should be an array
        assert schema.schema['properties']['components']['type'] == 'array'

    def test_test_runner_schema(self):
        """Test test_runner schema."""
        schema = get_schema('test_runner')
        assert 'status' in schema.schema['properties']
        assert 'tests_run' in schema.schema['properties']
        assert 'tests_passed' in schema.schema['properties']
        assert 'failures' in schema.schema['properties']
