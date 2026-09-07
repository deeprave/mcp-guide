"""Tests for validation functions."""

import pytest

from mcp_guide.core.validation import (
    DEFAULT_INSTRUCTION,
    ArgValidationError,
    is_absolute_path,
    validate_description,
    validate_directory_path,
    validate_pattern,
)


class TestIsAbsolutePath:
    """Tests for absolute path detection."""

    def test_unix_absolute(self):
        """Unix absolute path should be detected."""
        assert is_absolute_path("/absolute/path")

    def test_user_anchored_path_is_absolute(self):
        """A user-anchored path is absolute after LazyPath expansion."""
        assert is_absolute_path("~/documents")

    def test_windows_drive_letter(self):
        """Windows drive letter should be detected."""
        assert is_absolute_path("C:\\path")
        assert is_absolute_path("D:/path")

    def test_unc_path(self):
        """UNC path should be detected."""
        assert is_absolute_path("\\\\server\\share")

    def test_relative_path(self):
        """Relative path should not be detected as absolute."""
        assert not is_absolute_path("relative/path")
        assert not is_absolute_path("./relative")

    def test_empty_path(self):
        """Empty path should not be absolute."""
        assert not is_absolute_path("")


class TestValidateDirectoryPath:
    """Tests for directory path validation."""

    def test_valid_relative_path(self):
        """Valid relative path should pass."""
        result = validate_directory_path("docs/examples", "default")
        assert result == "docs/examples"

    @pytest.mark.parametrize(
        "path_value",
        [
            "/absolute/path",
            "C:\\absolute\\path",
            "\\\\server\\share",
            "../parent",
            "__invalid/path",
            "path/__invalid",
        ],
        ids=[
            "absolute_unix",
            "absolute_windows",
            "unc",
            "traversal",
            "leading_double_underscore",
            "trailing_double_underscore",
        ],
    )
    def test_reject_invalid_paths(self, path_value):
        """Invalid directory paths should be rejected consistently."""
        with pytest.raises(ArgValidationError) as exc_info:
            validate_directory_path(path_value, "default")
        assert len(exc_info.value.errors) == 1
        assert exc_info.value.errors[0]["field"] == "path"
        assert exc_info.value.instruction == DEFAULT_INSTRUCTION

    @pytest.mark.parametrize(
        "value,expected",
        [
            (None, "default_dir"),
            ("", "default_dir"),
        ],
        ids=["none", "empty"],
    )
    def test_default_values(self, value, expected):
        """Test that None and empty string return default value."""
        result = validate_directory_path(value, "default_dir")
        assert result == expected


class TestValidateDescription:
    """Tests for description validation."""

    def test_valid_description(self):
        """Valid description under 500 chars should pass."""
        result = validate_description("A valid description")
        assert result == "A valid description"

    def test_reject_over_default_500_chars(self):
        """Description over 500 chars should be rejected by default."""
        long_desc = "x" * 501
        with pytest.raises(ArgValidationError) as exc_info:
            validate_description(long_desc)
        assert len(exc_info.value.errors) == 1
        assert exc_info.value.errors[0]["field"] == "description"
        assert "500" in exc_info.value.errors[0]["message"]
        assert exc_info.value.instruction == DEFAULT_INSTRUCTION

    def test_custom_max_length(self):
        """Custom max_length should be respected."""
        with pytest.raises(ArgValidationError) as exc_info:
            validate_description("x" * 100, max_length=50)
        assert len(exc_info.value.errors) == 1
        assert exc_info.value.errors[0]["field"] == "description"
        assert "50" in exc_info.value.errors[0]["message"]

    @pytest.mark.parametrize(
        "description,quote_type",
        [
            ('Has "quotes" in it', "double"),
            ("Has 'quotes' in it", "single"),
        ],
        ids=["double_quotes", "single_quotes"],
    )
    def test_reject_quotes(self, description, quote_type):
        """Description with quotes should be rejected."""
        with pytest.raises(ArgValidationError) as exc_info:
            validate_description(description)
        assert len(exc_info.value.errors) == 1
        assert exc_info.value.errors[0]["field"] == "description"
        if quote_type == "double":
            assert exc_info.value.instruction == DEFAULT_INSTRUCTION

    @pytest.mark.parametrize(
        "value,expected",
        [
            (None, None),
            ("", ""),
        ],
        ids=["none", "empty"],
    )
    def test_allow_none_and_empty(self, value, expected):
        """None and empty string should be allowed."""
        result = validate_description(value)
        assert result == expected


class TestValidatePattern:
    """Tests for pattern validation."""

    def test_valid_pattern_simple(self):
        """Simple pattern should pass."""
        result = validate_pattern("*.md")
        assert result == "*.md"

    @pytest.mark.parametrize(
        "pattern",
        [
            "../file.md",
            "/absolute/*.md",
            "\\\\server\\share\\*.md",
            "__invalid/*.md",
        ],
        ids=["traversal", "absolute", "unc", "double_underscore"],
    )
    def test_reject_invalid_patterns(self, pattern):
        """Invalid patterns should be rejected consistently."""
        with pytest.raises(ArgValidationError) as exc_info:
            validate_pattern(pattern)
        assert len(exc_info.value.errors) == 1
        assert exc_info.value.errors[0]["field"] == "pattern"
        assert exc_info.value.instruction == DEFAULT_INSTRUCTION


class TestArgValidationError:
    """Validation errors preserve grouped details and explicit guidance."""

    @pytest.mark.parametrize(
        "errors,expected_message",
        [
            ([{"field": "name", "message": "Required field"}], "Validation error: Required field"),
            (
                [{"field": "name", "message": "Required field"}, {"field": "age", "message": "Must be positive"}],
                "2 validation errors occurred",
            ),
        ],
        ids=["single", "multiple"],
    )
    def test_error_details_survive_result_conversion(self, errors, expected_message):
        error = ArgValidationError(errors)
        assert str(error) == expected_message
        result = error.to_result()
        assert result.success is False
        assert result.error == expected_message
        assert result.error_type == "validation_error"
        assert result.error_data == {"validation_errors": errors}
        assert result.instruction == DEFAULT_INSTRUCTION

    def test_explicit_error_guidance_and_result_overrides(self):
        errors = [{"field": "name", "message": "Required"}]
        error = ArgValidationError(errors, message="Custom message", instruction="Custom instruction")
        initial = error.to_result()
        assert initial.error == "Custom message"
        assert initial.instruction == "Custom instruction"
        overridden = error.to_result(message="Override message", instruction="Override instruction")
        assert overridden.error == "Override message"
        assert overridden.instruction == "Override instruction"
        assert overridden.error_data == {"validation_errors": errors}
