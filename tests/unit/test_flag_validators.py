"""Tests for flag validation registration system."""

import pytest

from mcp_guide.feature_flags.types import WORKFLOW_FILE_FLAG, WORKFLOW_FLAG
from mcp_guide.feature_flags.validators import (
    ValidationError,
    clear_validators,
    register_flag_validator,
    validate_flag_with_registered,
)


class TestValidationRegistration:
    """Test flag validation registration system."""

    def setup_method(self):
        """Clear validators before each test."""
        clear_validators()

    def test_no_validator_registered_allows_any_value(self):
        """Test that unregistered flags allow any value."""
        # Should not raise
        validate_flag_with_registered("unknown-flag", "any-value", is_project=True)
        validate_flag_with_registered("unknown-flag", ["list", "value"], is_project=False)

    def test_custom_validator_registration(self):
        """Test registering and using custom validator."""

        def custom_validator(value, is_project):
            return isinstance(value, str) and value.startswith("valid-")

        register_flag_validator("test-flag", custom_validator)

        # Valid value should not raise
        validate_flag_with_registered("test-flag", "valid-value", is_project=True)

        # Invalid value should raise
        with pytest.raises(ValidationError, match="Invalid project flag 'test-flag' value"):
            validate_flag_with_registered("test-flag", "invalid-value", is_project=True)

        with pytest.raises(ValidationError, match="Invalid global flag 'test-flag' value"):
            validate_flag_with_registered("test-flag", "invalid-value", is_project=False)

    def test_workflow_validators_registered(self):
        """Test that workflow validators are automatically registered."""
        # Re-import to ensure validators are registered after setup_method cleared them
        import importlib

        from mcp_guide.workflow import flags

        importlib.reload(flags)

        # Valid workflow flag values should not raise
        validate_flag_with_registered(WORKFLOW_FLAG, True, is_project=True)
        validate_flag_with_registered(WORKFLOW_FLAG, ["discussion", "planning"], is_project=True)

        # Invalid workflow flag should raise
        with pytest.raises(ValidationError):
            validate_flag_with_registered(WORKFLOW_FLAG, ["invalid-phase"], is_project=True)

        # Valid workflow-file flag should not raise
        validate_flag_with_registered(WORKFLOW_FILE_FLAG, ".guide.yaml", is_project=True)

        # Invalid workflow-file flag should raise
        with pytest.raises(ValidationError):
            validate_flag_with_registered(WORKFLOW_FILE_FLAG, "", is_project=True)

    def test_none_value_skips_validation(self):
        """Test that None values skip validation (used for deletion)."""

        def strict_validator(value, is_project):
            # This validator would reject everything
            return False

        register_flag_validator("strict-flag", strict_validator)

        # None should not trigger validation
        validate_flag_with_registered("strict-flag", None, is_project=True)
        validate_flag_with_registered("strict-flag", None, is_project=False)
