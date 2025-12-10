"""Tests for feature flag validation functions."""

import pytest

from mcp_guide.feature_flags.validation import validate_flag_name, validate_flag_value, validate_project_name


class TestProjectNameValidation:
    """Test project name validation for feature flag contexts."""

    def test_project_name_allows_utf8_characters(self):
        """Test that project names allow UTF-8 characters."""
        assert validate_project_name("my.project") is True
        assert validate_project_name("测试项目") is True  # Chinese characters
        assert validate_project_name("café") is True  # Accented characters
        assert validate_project_name("проект") is True  # Cyrillic characters
        assert validate_project_name("プロジェクト") is True  # Japanese characters

    def test_project_name_allows_periods(self):
        """Test that project names allow periods."""
        assert validate_project_name("com.example.project") is True
        assert validate_project_name("my.project.name") is True
        assert validate_project_name(".hidden") is True

    def test_project_name_allows_filesystem_safe_characters(self):
        """Test that project names allow filesystem-safe characters."""
        assert validate_project_name("project-name") is True
        assert validate_project_name("project_name") is True
        assert validate_project_name("project name") is True  # spaces
        assert validate_project_name("project(1)") is True  # parentheses
        assert validate_project_name("project[test]") is True  # brackets

    def test_project_name_rejects_control_characters(self):
        """Test that project names reject control characters."""
        assert validate_project_name("project\x00") is False  # null
        assert validate_project_name("project\x01") is False  # start of heading
        assert validate_project_name("project\x1f") is False  # unit separator
        assert validate_project_name("project\x7f") is False  # delete
        assert validate_project_name("project\n") is False  # newline
        assert validate_project_name("project\t") is False  # tab
        assert validate_project_name("project\r") is False  # carriage return

    def test_project_name_empty_string(self):
        """Test validation of empty project names."""
        assert validate_project_name("") is False
        assert validate_project_name("   ") is True  # spaces are allowed


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
