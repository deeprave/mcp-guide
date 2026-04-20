"""Tests for feature flag validation functions."""

import pytest

from mcp_guide.feature_flags.constants import FLAG_CONTENT_STYLE
from mcp_guide.feature_flags.validators import (
    FlagValidationError,
    clear_validators,
    coerce_boolean_like,
    is_value_false,
    is_value_true,
    make_string_choice_validator,
    normalise_boolean_or_string_flag,
    register_flag_validator,
    validate_boolean_or_string_flag,
    validate_content_format_mime,
    validate_flag_name,
    validate_flag_value,
    validate_flag_with_registered,
    validate_template_styling,
)


class TestFlagNameValidation:
    """Test flag name validation."""

    def test_flag_name_allows_alphanumeric(self):
        """Test that flag names allow alphanumeric characters."""
        assert validate_flag_name("flag") is True
        assert validate_flag_name("flag123") is True
        assert validate_flag_name("123flag") is True
        assert validate_flag_name("FLAG") is True

    def test_flag_name_allows_hyphens_underscores(self):
        """Test that flag names allow hyphens and underscores."""
        assert validate_flag_name("my-flag") is True
        assert validate_flag_name("my_flag") is True
        assert validate_flag_name("my-flag_name") is True
        assert validate_flag_name("-flag") is True
        assert validate_flag_name("flag-") is True

    def test_flag_name_rejects_periods(self):
        """Test that flag names reject periods."""
        assert validate_flag_name("my.flag") is False
        assert validate_flag_name("flag.name") is False
        assert validate_flag_name(".flag") is False
        assert validate_flag_name("flag.") is False

    def test_flag_name_rejects_spaces_special_chars(self):
        """Test that flag names reject spaces and special characters."""
        assert validate_flag_name("my flag") is False
        assert validate_flag_name("flag@name") is False
        assert validate_flag_name("flag#name") is False
        assert validate_flag_name("flag$name") is False
        assert validate_flag_name("flag%name") is False

    def test_flag_name_empty_string(self):
        """Test validation of empty flag names."""
        assert validate_flag_name("") is False


class TestFlagValueValidation:
    """Test flag value type validation."""

    def test_flag_value_accepts_boolean(self):
        """Test that flag values accept boolean types."""
        assert validate_flag_value(True) is True
        assert validate_flag_value(False) is True

    def test_flag_value_accepts_string(self):
        """Test that flag values accept string types."""
        assert validate_flag_value("test") is True
        assert validate_flag_value("") is True
        assert validate_flag_value("multi word string") is True

    def test_flag_value_accepts_list_of_strings(self):
        """Test that flag values accept list[str] types."""
        assert validate_flag_value(["a", "b", "c"]) is True
        assert validate_flag_value([]) is True
        assert validate_flag_value(["single"]) is True
        assert validate_flag_value(["", "empty", ""]) is True

    def test_flag_value_accepts_dict_str_str(self):
        """Test that flag values accept dict[str, str] types."""
        assert validate_flag_value({"key": "value"}) is True
        assert validate_flag_value({}) is True
        assert validate_flag_value({"k1": "v1", "k2": "v2"}) is True
        assert validate_flag_value({"": ""}) is True

    def test_flag_value_rejects_numeric_types(self):
        """Test that flag values reject numeric types."""
        assert validate_flag_value(123) is False
        assert validate_flag_value(12.34) is False
        assert validate_flag_value(0) is False
        assert validate_flag_value(-1) is False

    def test_flag_value_rejects_mixed_lists(self):
        """Test that flag values reject lists with non-string elements."""
        assert validate_flag_value([1, 2, 3]) is False
        assert validate_flag_value(["string", 123]) is False
        assert validate_flag_value([True, False]) is False
        assert validate_flag_value(["string", True, 123]) is False

    def test_flag_value_rejects_invalid_dict_types(self):
        """Test that flag values reject dicts with non-string keys/values."""
        assert validate_flag_value({1: "value"}) is False
        assert validate_flag_value({"key": 123}) is False
        assert validate_flag_value({1: 2}) is False
        assert validate_flag_value({"key": True}) is False

    def test_flag_value_rejects_other_types(self):
        """Test that flag values reject other types."""
        assert validate_flag_value(None) is False
        assert validate_flag_value(object()) is False
        assert validate_flag_value(set()) is False
        assert validate_flag_value(tuple()) is False


class TestContentFormatMimeValidator:
    """Test content-format flag validator."""

    def test_valid_values(self):
        """Test validator accepts valid values."""
        assert validate_content_format_mime(None, False) is True
        assert validate_content_format_mime("none", False) is True
        assert validate_content_format_mime("plain", False) is True
        assert validate_content_format_mime("mime", False) is True

    def test_invalid_values(self):
        """Test validator rejects invalid values."""
        assert validate_content_format_mime("invalid", False) is False
        assert validate_content_format_mime(True, False) is False
        assert validate_content_format_mime(123, False) is False
        assert validate_content_format_mime([], False) is False


class TestTemplateStylingValidator:
    """Test content-style flag validator."""

    def test_valid_values(self):
        """Test validator accepts valid values."""
        assert validate_template_styling(None, False) is True
        assert validate_template_styling("plain", False) is True
        assert validate_template_styling("headings", False) is True
        assert validate_template_styling("full", False) is True

    def test_invalid_values(self):
        """Test validator rejects invalid values."""
        assert validate_template_styling("invalid", False) is False
        assert validate_template_styling("none", False) is False  # "none" not valid for content-style
        assert validate_template_styling(True, False) is False
        assert validate_template_styling(123, False) is False


class TestStringChoiceValidatorFactory:
    """Test the shared enum/string-choice validator factory."""

    def test_factory_accepts_configured_values(self):
        validator = make_string_choice_validator(["alpha", "beta"])

        assert validator("alpha", False) is True
        assert validator("beta", True) is True
        assert validator(None, False) is True

    def test_factory_rejects_outside_values(self):
        validator = make_string_choice_validator(["alpha", "beta"])

        assert validator("gamma", False) is False
        assert validator(True, False) is False
        assert validator(["alpha"], False) is False

    def test_factory_can_disallow_none(self):
        validator = make_string_choice_validator(["alpha"], allow_none=False)

        assert validator(None, False) is False


@pytest.mark.usefixtures("reset_flag_registry")
class TestValidatorRegistration:
    """Test validator registration and usage."""

    @pytest.fixture(autouse=True)
    def _register_test_validators(self):
        """Register the validators used by this test class."""
        clear_validators()
        register_flag_validator("content-format", validate_content_format_mime)
        register_flag_validator(FLAG_CONTENT_STYLE, validate_template_styling)

    def test_registered_validators_work(self):
        """Test that registered validators are used."""
        # Should not raise for valid values
        validate_flag_with_registered("content-format", "plain", False)
        validate_flag_with_registered(FLAG_CONTENT_STYLE, "headings", False)

        # Should raise for invalid values
        with pytest.raises(FlagValidationError):
            validate_flag_with_registered("content-format", "invalid", False)

        with pytest.raises(FlagValidationError):
            validate_flag_with_registered(FLAG_CONTENT_STYLE, "invalid", False)


@pytest.mark.usefixtures("reset_flag_registry")
class TestDefaultGenericFlagBehavior:
    """Test default validator/normalizer behavior for unregistered flags."""

    @pytest.fixture(autouse=True)
    def _reset_registry(self):
        clear_validators()

    def test_default_validator_accepts_bool_and_string(self):
        assert validate_boolean_or_string_flag(True, False) is True
        assert validate_boolean_or_string_flag(False, False) is True
        assert validate_boolean_or_string_flag("custom", False) is True

    def test_default_validator_rejects_structured_values(self):
        assert validate_boolean_or_string_flag(["discussion"], False) is False
        assert validate_boolean_or_string_flag({"phase": "entry"}, False) is False

    def test_default_normaliser_coerces_boolean_strings(self):
        assert normalise_boolean_or_string_flag("true") == True
        assert normalise_boolean_or_string_flag("false") == False
        assert normalise_boolean_or_string_flag("enabled") == True
        assert normalise_boolean_or_string_flag("disabled") == False
        assert normalise_boolean_or_string_flag("yes") == True
        assert normalise_boolean_or_string_flag("no") == False
        assert normalise_boolean_or_string_flag("1") == True
        assert normalise_boolean_or_string_flag("0") == False
        assert normalise_boolean_or_string_flag("review") == "review"

    def test_unregistered_flag_rejects_structured_value(self):
        with pytest.raises(FlagValidationError):
            validate_flag_with_registered("custom-flag", ["discussion"], False)

    def test_unregistered_flag_accepts_scalar_value(self):
        validate_flag_with_registered("custom-flag", True, False)
        validate_flag_with_registered("custom-flag", "custom", False)


class TestBooleanLikeCoercion:
    """Test shared boolean-like coercion helpers."""

    @pytest.mark.parametrize(
        ("value", "expected"),
        [
            (True, True),
            (False, False),
            ("true", True),
            ("TRUE", True),
            ("on", True),
            ("enabled", True),
            ("yes", True),
            ("1", True),
            ("false", False),
            ("FALSE", False),
            ("off", False),
            ("disabled", False),
            ("no", False),
            ("0", False),
            (None, None),
            ("review", None),
        ],
    )
    def test_coerce_boolean_like(self, value, expected):
        assert coerce_boolean_like(value) is expected

    def test_is_value_true_false_helpers(self):
        assert is_value_true("enabled") is True
        assert is_value_true("0") is False
        assert is_value_false("disabled") is True
        assert is_value_false("1") is False
