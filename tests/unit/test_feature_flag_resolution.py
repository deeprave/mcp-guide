"""Tests for feature flag resolution logic."""

from mcp_guide.feature_flags.resolution import resolve_flag


class TestFlagResolution:
    """Test flag resolution hierarchy."""

    def test_resolve_flag_project_takes_precedence(self):
        """Test that project flags take precedence over global flags."""
        global_flags = {"flag1": True, "flag2": "global"}
        project_flags = {"flag1": False}  # overrides global

        result = resolve_flag("flag1", project_flags, global_flags)
        assert result is False

    def test_resolve_flag_falls_back_to_global(self):
        """Test that resolution falls back to global flags."""
        global_flags = {"flag1": True, "flag2": "global"}
        project_flags = {"flag3": "project"}

        result = resolve_flag("flag2", project_flags, global_flags)
        assert result == "global"

    def test_resolve_flag_returns_none_when_not_found(self):
        """Test that resolution returns None when flag not found."""
        global_flags = {"flag1": True}
        project_flags = {"flag2": False}

        result = resolve_flag("flag3", project_flags, global_flags)
        assert result is None

    def test_resolve_flag_handles_empty_dicts(self):
        """Test that resolution handles empty flag dictionaries."""
        result = resolve_flag("flag1", {}, {})
        assert result is None

    def test_resolve_flag_with_complex_values(self):
        """Test resolution with complex FeatureValue types."""
        global_flags = {"list_flag": ["global", "values"], "dict_flag": {"global": "value"}}
        project_flags = {"list_flag": ["project", "override"], "string_flag": "project_string"}

        # Project list overrides global
        assert resolve_flag("list_flag", project_flags, global_flags) == ["project", "override"]

        # Global dict when not in project
        assert resolve_flag("dict_flag", project_flags, global_flags) == {"global": "value"}

        # Project string
        assert resolve_flag("string_flag", project_flags, global_flags) == "project_string"
