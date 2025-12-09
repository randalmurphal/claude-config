"""Unit tests for cc_orchestrations.core.runner.

Tests error classification, retry config, and command building
without making actual API calls.
"""

from cc_orchestrations.core.config import Config
from cc_orchestrations.core.runner import (
    DRY_RUN_WRAPPER,
    AgentResult,
    ErrorType,
    RetryConfig,
    classify_error,
)


class TestErrorClassification:
    """Tests for error classification logic."""

    def test_timeout_is_retryable(self):
        """Timeout errors should be retryable."""
        assert classify_error('Connection timeout') == ErrorType.RETRYABLE
        assert classify_error('Request timed out') == ErrorType.RETRYABLE

    def test_rate_limit_is_retryable(self):
        """Rate limit errors should be retryable."""
        assert classify_error('rate limit exceeded') == ErrorType.RETRYABLE
        assert (
            classify_error('HTTP 429 Too Many Requests') == ErrorType.RETRYABLE
        )

    def test_auth_is_not_retryable(self):
        """Auth errors should not be retried."""
        assert (
            classify_error('Authentication failed') == ErrorType.NON_RETRYABLE
        )
        assert classify_error('Invalid API key') == ErrorType.NON_RETRYABLE

    def test_error_type_enum_exists(self):
        """ErrorType enum should have expected values."""
        assert ErrorType.RETRYABLE
        assert ErrorType.NON_RETRYABLE
        assert ErrorType.UNKNOWN


class TestRetryConfig:
    """Tests for RetryConfig."""

    def test_default_config(self):
        """Test default retry configuration."""
        config = RetryConfig()
        assert config.max_attempts >= 1
        assert config.initial_delay > 0
        assert config.max_delay >= config.initial_delay

    def test_custom_config(self):
        """Test custom retry configuration."""
        config = RetryConfig(
            max_attempts=5,
            initial_delay=2.0,
            max_delay=60.0,
            exponential_base=3.0,
        )
        assert config.max_attempts == 5
        assert config.initial_delay == 2.0
        assert config.max_delay == 60.0

    def test_delay_calculation_no_jitter(self):
        """Test exponential backoff without jitter."""
        config = RetryConfig(
            initial_delay=1.0,
            max_delay=100.0,
            exponential_base=2.0,
            jitter=0.0,  # No randomness
        )

        # Delays should be exponential: 1, 2, 4, 8, 16...
        assert config.get_delay(0) == 1.0
        assert config.get_delay(1) == 2.0
        assert config.get_delay(2) == 4.0

    def test_delay_capped_at_max(self):
        """Test that delay is capped at max_delay."""
        config = RetryConfig(
            initial_delay=1.0,
            max_delay=10.0,
            exponential_base=2.0,
            jitter=0.0,
        )

        # After several attempts, should hit max
        delay = config.get_delay(10)  # Would be 1024 without cap
        assert delay == 10.0


class TestDryRunWrapper:
    """Tests for dry-run prompt wrapper."""

    def test_wrapper_has_placeholder(self):
        """Wrapper should have placeholder for original prompt."""
        assert '{original_prompt}' in DRY_RUN_WRAPPER

    def test_wrapper_format(self):
        """Test wrapper can be formatted with prompt."""
        prompt = 'Analyze this code and return findings'
        wrapped = DRY_RUN_WRAPPER.format(original_prompt=prompt)

        assert prompt in wrapped
        assert '{original_prompt}' not in wrapped


class TestAgentResult:
    """Tests for AgentResult dataclass."""

    def test_successful_result(self):
        """Test successful result creation."""
        result = AgentResult(
            success=True,
            data={'status': 'ok', 'findings': []},
            duration=5.5,
        )
        assert result.success is True
        assert result.data['status'] == 'ok'
        assert result.duration == 5.5

    def test_failed_result(self):
        """Test failed result creation."""
        result = AgentResult(
            success=False,
            error='Connection timeout',
            error_type=ErrorType.RETRYABLE,
            retry_attempts=3,
            duration=30.0,
        )
        assert result.success is False
        assert result.error == 'Connection timeout'
        assert result.error_type == ErrorType.RETRYABLE
        assert result.retry_attempts == 3

    def test_result_get_method(self):
        """Test get() method for accessing data."""
        result = AgentResult(
            success=True,
            data={'findings': [1, 2, 3], 'summary': 'test'},
        )

        assert result.get('findings') == [1, 2, 3]
        assert result.get('summary') == 'test'
        assert result.get('nonexistent') is None
        assert result.get('nonexistent', 'default') == 'default'


class TestConfigIntegration:
    """Tests for runner config integration."""

    def test_config_dry_run_flag(self):
        """Test config dry_run flag is accessible."""
        config = Config(name='test', dry_run=True)
        assert config.dry_run is True

    def test_config_model_setting(self):
        """Test default model can be set."""
        config = Config(name='test', default_model='haiku')
        assert config.default_model == 'haiku'
