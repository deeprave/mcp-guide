"""Tests for flag validation registration system."""

import pytest

from mcp_guide.feature_flags.constants import (
    FLAG_AUTOUPDATE,
    FLAG_COMMAND,
    FLAG_GUIDE_DEVELOPMENT,
    FLAG_ONBOARDED,
    FLAG_RESOURCE,
    FLAG_WORKFLOW,
    FLAG_WORKFLOW_FILE,
)
from mcp_guide.feature_flags.validators import (
    FlagValidationError,
    clear_validators,
    normalise_boolean_flag,
    normalise_flag,
    register_flag_validator,
    validate_boolean_flag,
    validate_flag_with_registered,
)


@pytest.mark.usefixtures("reset_flag_registry")
class TestValidationRegistration:
    """Test flag validation registration system."""

    @pytest.fixture(autouse=True)
    def _clear_validators(self):
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
        with pytest.raises(FlagValidationError, match="Invalid project flag `test-flag` value"):
            validate_flag_with_registered("test-flag", "invalid-value", is_project=True)

        with pytest.raises(FlagValidationError, match="Invalid feature flag `test-flag` value"):
            validate_flag_with_registered("test-flag", "invalid-value", is_project=False)

    def test_workflow_validators_registered(self):
        """Test that workflow validators are automatically registered."""
        # Re-import to ensure validators are registered after setup_method cleared them
        import importlib

        from mcp_guide.workflow import flags

        importlib.reload(flags)

        # Valid workflow flag values should not raise
        validate_flag_with_registered(FLAG_WORKFLOW, True, is_project=True)
        validate_flag_with_registered(FLAG_WORKFLOW, ["discussion", "implementation"], is_project=True)

        # Invalid workflow flag should raise (missing mandatory phases)
        with pytest.raises(FlagValidationError):
            validate_flag_with_registered(FLAG_WORKFLOW, ["discussion", "planning"], is_project=True)

        # Invalid workflow flag should raise (invalid phase name)
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


@pytest.mark.usefixtures("reset_flag_registry")
class TestBooleanValidator:
    """Test validate_boolean_flag function."""

    @pytest.mark.parametrize(
        "scenario,value,is_project,expected",
        [
            # Valid values
            ("bool_true", True, True, True),
            ("bool_false", False, False, True),
            ("none", None, True, True),
            ("truthy_true", "true", True, True),
            ("truthy_TRUE", "TRUE", True, True),
            ("truthy_on", "on", True, True),
            ("truthy_enabled", "enabled", True, True),
            ("falsy_false", "false", False, True),
            ("falsy_FALSE", "FALSE", False, True),
            ("falsy_off", "off", False, True),
            ("falsy_disabled", "disabled", False, True),
            ("falsy_empty", "", False, True),
            # Invalid values
            ("invalid_yes", "yes", True, False),
            ("invalid_no", "no", True, False),
            ("invalid_1", "1", True, False),
            ("invalid_0", "0", True, False),
            ("invalid_string", "invalid", True, False),
            ("invalid_number_1", 1, True, False),
            ("invalid_number_0", 0, False, False),
            ("invalid_list", ["true"], True, False),
            ("invalid_dict", {"value": True}, True, False),
        ],
        ids=lambda x: x if isinstance(x, str) else str(x),
    )
    def test_boolean_flag_validation(self, scenario, value, is_project, expected):
        """Test boolean flag validation with various inputs."""
        assert validate_boolean_flag(value, is_project=is_project) is expected
        assert validate_boolean_flag({"enabled": True}, is_project=False) is False

    @pytest.mark.parametrize(
        ("value", "expected"),
        [
            (True, True),
            (False, False),
            (None, None),
            ("true", True),
            ("enabled", True),
            ("on", True),
            ("false", False),
            ("disabled", False),
            ("off", False),
            ("", False),
        ],
    )
    def test_boolean_flag_normalisation(self, value, expected):
        assert normalise_boolean_flag(value) == expected

    def test_format_flags_use_boolean_normalisation(self):
        clear_validators()
        register_flag_validator(FLAG_RESOURCE, validate_boolean_flag, normaliser=normalise_boolean_flag)
        register_flag_validator(FLAG_COMMAND, validate_boolean_flag, normaliser=normalise_boolean_flag)
        register_flag_validator(FLAG_ONBOARDED, validate_boolean_flag, normaliser=normalise_boolean_flag)

        assert normalise_flag(FLAG_RESOURCE, "enabled") == True
        assert normalise_flag(FLAG_COMMAND, "off") == False
        assert normalise_flag(FLAG_ONBOARDED, "enabled") == True
        assert normalise_flag(FLAG_ONBOARDED, "off") == False


@pytest.mark.usefixtures("reset_flag_registry")
class TestGuideDevelopmentValidator:
    """Test guide-development flag validation."""

    @pytest.fixture(autouse=True)
    def _register_guide_development_validator(self):
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


@pytest.fixture
def autoupdate_validator(reset_flag_registry):
    """Clear and re-register autoupdate validator for each test."""
    clear_validators()
    from mcp_guide.feature_flags.validators import (
        FlagScope,
        normalise_boolean_flag,
        register_flag_validator,
        validate_autoupdate,
    )

    register_flag_validator(
        FLAG_AUTOUPDATE,
        validate_autoupdate,
        FlagScope.FEATURE_ONLY,
        normaliser=normalise_boolean_flag,
    )


class TestAutoupdateValidator:
    """Test autoupdate flag validator."""

    def test_autoupdate_accepts_boolean_global(self, autoupdate_validator):
        """Test that autoupdate accepts boolean values at global level."""
        validate_flag_with_registered(FLAG_AUTOUPDATE, True, is_project=False)
        validate_flag_with_registered(FLAG_AUTOUPDATE, False, is_project=False)

    def test_autoupdate_accepts_string_boolean_global(self, autoupdate_validator):
        """Test that autoupdate accepts string boolean values at global level."""
        validate_flag_with_registered(FLAG_AUTOUPDATE, "true", is_project=False)
        validate_flag_with_registered(FLAG_AUTOUPDATE, "false", is_project=False)
        validate_flag_with_registered(FLAG_AUTOUPDATE, "enabled", is_project=False)
        validate_flag_with_registered(FLAG_AUTOUPDATE, "disabled", is_project=False)

    def test_autoupdate_rejects_project_level(self, autoupdate_validator):
        """Test that autoupdate rejects project-level setting."""
        with pytest.raises(FlagValidationError, match="Cannot set project flag `autoupdate`, must be a feature flag"):
            validate_flag_with_registered(FLAG_AUTOUPDATE, True, is_project=True)
        with pytest.raises(FlagValidationError, match="Cannot set project flag `autoupdate`, must be a feature flag"):
            validate_flag_with_registered(FLAG_AUTOUPDATE, False, is_project=True)

    def test_autoupdate_rejects_invalid_values(self, autoupdate_validator):
        """Test that autoupdate rejects invalid values."""
        with pytest.raises(FlagValidationError):
            validate_flag_with_registered(FLAG_AUTOUPDATE, "invalid", is_project=False)
        with pytest.raises(FlagValidationError):
            validate_flag_with_registered(FLAG_AUTOUPDATE, 1, is_project=False)
        with pytest.raises(FlagValidationError):
            validate_flag_with_registered(FLAG_AUTOUPDATE, ["list"], is_project=False)

    def test_autoupdate_uses_boolean_normalisation(self, autoupdate_validator):
        """Test that autoupdate uses the shared boolean normaliser."""
        assert normalise_flag(FLAG_AUTOUPDATE, "enabled") == True
        assert normalise_flag(FLAG_AUTOUPDATE, "off") == False


class TestFlagScopeRestrictions:
    """Test flag scope restriction error messages."""

    def test_global_only_flag_error_message(self, reset_flag_registry):
        """Test that feature-only flags show correct error message when set as project flag."""
        clear_validators()
        from mcp_guide.feature_flags.validators import FlagScope, register_flag_validator

        def dummy_validator(value, is_project):
            return True

        register_flag_validator("test-feature-only", dummy_validator, FlagScope.FEATURE_ONLY)

        with pytest.raises(
            FlagValidationError, match=r"Cannot set project flag `test-feature-only`, must be a feature flag"
        ):
            validate_flag_with_registered("test-feature-only", "value", is_project=True)

    def test_project_only_flag_error_message(self, reset_flag_registry):
        """Test that project-only flags show correct error message when set as feature flag."""
        clear_validators()
        from mcp_guide.feature_flags.validators import FlagScope, register_flag_validator

        def dummy_validator(value, is_project):
            return True

        register_flag_validator("test-project-only", dummy_validator, FlagScope.PROJECT_ONLY)

        with pytest.raises(
            FlagValidationError, match=r"Cannot set feature flag `test-project-only`, must be a project flag"
        ):
            validate_flag_with_registered("test-project-only", "value", is_project=False)

    def test_both_scope_allows_either(self, reset_flag_registry):
        """Test that flags with BOTH scope can be set at either level."""
        clear_validators()
        from mcp_guide.feature_flags.validators import FlagScope, register_flag_validator

        def dummy_validator(value, is_project):
            return True

        register_flag_validator("test-both", dummy_validator, FlagScope.BOTH)

        # Should not raise for project level
        validate_flag_with_registered("test-both", "value", is_project=True)

        # Should not raise for global level
        validate_flag_with_registered("test-both", "value", is_project=False)
