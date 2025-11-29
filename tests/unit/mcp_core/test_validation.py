"""Tests for validation functions."""

import pytest

from mcp_core.validation import (
    DEFAULT_INSTRUCTION,
    ValidationError,
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

    def test_reject_absolute_path_unix(self):
        """Absolute Unix path should be rejected."""
        with pytest.raises(ValidationError) as exc_info:
            validate_directory_path("/absolute/path", "default")
        assert exc_info.value.error_type == "absolute_path"
        assert exc_info.value.instruction == DEFAULT_INSTRUCTION

    def test_reject_absolute_path_windows(self):
        """Absolute Windows path should be rejected."""
        with pytest.raises(ValidationError) as exc_info:
            validate_directory_path("C:\\absolute\\path", "default")
        assert exc_info.value.error_type == "absolute_path"

    def test_reject_unc_path(self):
        """UNC path should be rejected."""
        with pytest.raises(ValidationError) as exc_info:
            validate_directory_path("\\\\server\\share", "default")
        assert exc_info.value.error_type == "absolute_path"

    def test_reject_traversal(self):
        """Path with .. should be rejected."""
        with pytest.raises(ValidationError) as exc_info:
            validate_directory_path("../parent", "default")
        assert exc_info.value.error_type == "traversal_attempt"

    def test_reject_leading_double_underscore(self):
        """Path with leading __ should be rejected."""
        with pytest.raises(ValidationError) as exc_info:
            validate_directory_path("__invalid/path", "default")
        assert exc_info.value.error_type == "invalid_component"

    def test_reject_trailing_double_underscore(self):
        """Path with trailing __ should be rejected."""
        with pytest.raises(ValidationError) as exc_info:
            validate_directory_path("path/__invalid", "default")
        assert exc_info.value.error_type == "invalid_component"

    def test_default_when_none(self):
        """None should return default value."""
        result = validate_directory_path(None, "default_dir")
        assert result == "default_dir"

    def test_default_when_empty(self):
        """Empty string should return default value."""
        result = validate_directory_path("", "default_dir")
        assert result == "default_dir"


class TestValidateDescription:
    """Tests for description validation."""

    def test_valid_description(self):
        """Valid description under 500 chars should pass."""
        result = validate_description("A valid description")
        assert result == "A valid description"

    def test_reject_over_default_500_chars(self):
        """Description over 500 chars should be rejected by default."""
        long_desc = "x" * 501
        with pytest.raises(ValidationError) as exc_info:
            validate_description(long_desc)
        assert exc_info.value.error_type == "description_too_long"
        assert "500" in exc_info.value.message
        assert exc_info.value.instruction == DEFAULT_INSTRUCTION

    def test_custom_max_length(self):
        """Custom max_length should be respected."""
        with pytest.raises(ValidationError) as exc_info:
            validate_description("x" * 100, max_length=50)
        assert exc_info.value.error_type == "description_too_long"
        assert "50" in exc_info.value.message

    def test_custom_max_length_pass(self):
        """Description under custom max_length should pass."""
        result = validate_description("x" * 100, max_length=200)
        assert result == "x" * 100

    def test_reject_double_quotes(self):
        """Description with double quotes should be rejected."""
        with pytest.raises(ValidationError) as exc_info:
            validate_description('Has "quotes" in it')
        assert exc_info.value.error_type == "invalid_characters"
        assert exc_info.value.instruction == DEFAULT_INSTRUCTION

    def test_reject_single_quotes(self):
        """Description with single quotes should be rejected."""
        with pytest.raises(ValidationError) as exc_info:
            validate_description("Has 'quotes' in it")
        assert exc_info.value.error_type == "invalid_characters"

    def test_allow_none(self):
        """None should be allowed."""
        result = validate_description(None)
        assert result is None

    def test_allow_empty(self):
        """Empty string should be allowed."""
        result = validate_description("")
        assert result == ""


class TestValidatePattern:
    """Tests for pattern validation."""

    def test_valid_pattern_simple(self):
        """Simple pattern should pass."""
        result = validate_pattern("*.md")
        assert result == "*.md"

    def test_valid_pattern_with_path(self):
        """Pattern with path should pass."""
        result = validate_pattern("docs/*.md")
        assert result == "docs/*.md"

    def test_reject_traversal(self):
        """Pattern with .. should be rejected."""
        with pytest.raises(ValidationError) as exc_info:
            validate_pattern("../file.md")
        assert exc_info.value.error_type == "traversal_attempt"
        assert exc_info.value.instruction == DEFAULT_INSTRUCTION

    def test_reject_absolute_path(self):
        """Absolute path pattern should be rejected."""
        with pytest.raises(ValidationError) as exc_info:
            validate_pattern("/absolute/*.md")
        assert exc_info.value.error_type == "absolute_path"

    def test_reject_unc_path(self):
        """UNC path pattern should be rejected."""
        with pytest.raises(ValidationError) as exc_info:
            validate_pattern("\\\\server\\share\\*.md")
        assert exc_info.value.error_type == "absolute_path"

    def test_reject_double_underscore(self):
        """Pattern with __ should be rejected."""
        with pytest.raises(ValidationError) as exc_info:
            validate_pattern("__invalid/*.md")
        assert exc_info.value.error_type == "invalid_pattern"
