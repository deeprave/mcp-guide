"""Tests for feature flag resolution logic."""

from unittest.mock import Mock, PropertyMock

import pytest

from mcp_guide.feature_flags.resolution import get_target_project, resolve_flag


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


class TestProjectParameterHandling:
    """Test project parameter handling for MCP tools."""

    def test_get_target_project_none_returns_current(self):
        """Test that None parameter returns current project from session."""
        mock_session = Mock()
        mock_session.project_name = "current-project"

        result = get_target_project(None, mock_session)
        assert result == "current-project"

    def test_get_target_project_star_returns_global_marker(self):
        """Test that '*' parameter returns global marker."""
        mock_session = Mock()

        result = get_target_project("*", mock_session)
        assert result == "*"
        # Should not call session methods for global
        assert not hasattr(mock_session, "get_current_project_name") or not mock_session.get_current_project_name.called

    def test_get_target_project_specific_name_returns_name(self):
        """Test that specific project name is returned as-is."""
        mock_session = Mock()

        result = get_target_project("specific-project", mock_session)
        assert result == "specific-project"
        # Should not call session methods for specific names
        mock_session.get_current_project_name.assert_not_called()

    def test_get_target_project_handles_session_without_current(self):
        """Test handling when session has no current project."""
        mock_session = Mock()
        mock_session.project_name = None

        result = get_target_project(None, mock_session)
        assert result is None

    def test_get_target_project_handles_session_error(self):
        """Test handling when session raises error."""
        mock_session = Mock()
        # Create a property that raises an error when accessed
        type(mock_session).project_name = PropertyMock(side_effect=RuntimeError("No session"))

        with pytest.raises(RuntimeError, match="No session"):
            get_target_project(None, mock_session)
