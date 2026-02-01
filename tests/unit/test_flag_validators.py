"""Tests for flag validation registration system."""

import pytest

from mcp_guide.feature_flags.constants import (
    FLAG_GUIDE_DEVELOPMENT,
    FLAG_WORKFLOW,
    FLAG_WORKFLOW_FILE,
)
from mcp_guide.feature_flags.validators import (
    FlagValidationError,
    clear_validators,
    register_flag_validator,
    validate_boolean_flag,
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
        with pytest.raises(FlagValidationError, match="Invalid project flag 'test-flag' value"):
            validate_flag_with_registered("test-flag", "invalid-value", is_project=True)

        with pytest.raises(FlagValidationError, match="Invalid global flag 'test-flag' value"):
            validate_flag_with_registered("test-flag", "invalid-value", is_project=False)

    def test_workflow_validators_registered(self):
        """Test that workflow validators are automatically registered."""
        # Re-import to ensure validators are registered after setup_method cleared them
        import importlib

        from mcp_guide.workflow import flags

        importlib.reload(flags)

        # Valid workflow flag values should not raise
        validate_flag_with_registered(FLAG_WORKFLOW, True, is_project=True)
        validate_flag_with_registered(FLAG_WORKFLOW, ["discussion", "planning"], is_project=True)

        # Invalid workflow flag should raise
        with pytest.raises(FlagValidationError):
            validate_flag_with_registered(FLAG_WORKFLOW, ["invalid-phase"], is_project=True)

        # Valid workflow-file flag should not raise
        validate_flag_with_registered(FLAG_WORKFLOW_FILE, ".guide.yaml", is_project=True)

        # Invalid workflow-file flag should raise
        with pytest.raises(FlagValidationError):
            validate_flag_with_registered(FLAG_WORKFLOW_FILE, "", is_project=True)

    def test_none_value_skips_validation(self):
        """Test that None values skip validation (used for deletion)."""

        def strict_validator(value, is_project):
            # This validator would reject everything
            return False

        register_flag_validator("strict-flag", strict_validator)

        # None should not trigger validation
        validate_flag_with_registered("strict-flag", None, is_project=True)
        validate_flag_with_registered("strict-flag", None, is_project=False)


class TestBooleanValidator:
    """Test validate_boolean_flag function."""

    def test_accepts_boolean_true(self):
        """Test that boolean True is accepted."""
        assert validate_boolean_flag(True, is_project=True) is True

    def test_accepts_boolean_false(self):
        """Test that boolean False is accepted."""
        assert validate_boolean_flag(False, is_project=False) is True

    def test_accepts_none(self):
        """Test that None is accepted (for deletion)."""
        assert validate_boolean_flag(None, is_project=True) is True

    def test_accepts_truthy_strings(self):
        """Test that truthy string values are accepted."""
        for value in ["true", "True", "TRUE", "on", "ON", "enabled", "ENABLED"]:
            assert validate_boolean_flag(value, is_project=True) is True

    def test_accepts_falsy_strings(self):
        """Test that falsy string values are accepted."""
        for value in ["false", "False", "FALSE", "off", "OFF", "disabled", "DISABLED", ""]:
            assert validate_boolean_flag(value, is_project=False) is True

    def test_rejects_invalid_strings(self):
        """Test that invalid string values are rejected."""
        for value in ["yes", "no", "1", "0", "invalid"]:
            assert validate_boolean_flag(value, is_project=True) is False

    def test_rejects_numbers(self):
        """Test that numeric values are rejected."""
        assert validate_boolean_flag(1, is_project=True) is False
        assert validate_boolean_flag(0, is_project=False) is False

    def test_rejects_lists(self):
        """Test that list values are rejected."""
        assert validate_boolean_flag(["true"], is_project=True) is False

    def test_rejects_dicts(self):
        """Test that dict values are rejected."""
        assert validate_boolean_flag({"enabled": True}, is_project=False) is False


class TestGuideDevelopmentValidator:
    """Test guide-development flag validation."""

    def setup_method(self):
        """Ensure validator is registered (may have been cleared by other tests)."""
        from mcp_guide.feature_flags.constants import FLAG_GUIDE_DEVELOPMENT
        from mcp_guide.feature_flags.validators import register_flag_validator, validate_boolean_flag

        # Re-register in case it was cleared
        register_flag_validator(FLAG_GUIDE_DEVELOPMENT, validate_boolean_flag)

    def test_guide_development_accepts_boolean(self):
        """Test that guide-development accepts boolean values."""
        # Validator is registered at module import time
        validate_flag_with_registered(FLAG_GUIDE_DEVELOPMENT, True, is_project=True)
        validate_flag_with_registered(FLAG_GUIDE_DEVELOPMENT, False, is_project=False)

    def test_guide_development_accepts_string_boolean(self):
        """Test that guide-development accepts string boolean values."""
        validate_flag_with_registered(FLAG_GUIDE_DEVELOPMENT, "true", is_project=True)
        validate_flag_with_registered(FLAG_GUIDE_DEVELOPMENT, "false", is_project=False)

    def test_guide_development_rejects_invalid(self):
        """Test that guide-development rejects invalid values."""
        with pytest.raises(FlagValidationError):
            validate_flag_with_registered(FLAG_GUIDE_DEVELOPMENT, "invalid", is_project=True)
        with pytest.raises(FlagValidationError):
            validate_flag_with_registered(FLAG_GUIDE_DEVELOPMENT, 1, is_project=False)
