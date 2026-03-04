"""Tests for feature flag integration with data models."""

from mcp_guide.models import Project


class TestProjectFeatureFlags:
    """Test Project project_flags field."""

    def test_project_flags_accepts_valid_values(self):
        """Test that project_flags accepts valid FeatureValue types."""
        project_flags = {
            "bool_flag": False,
            "string_flag": "project-specific",
            "list_flag": ["x", "y"],
            "dict_flag": {"project": "value"},
        }
        project = Project(name="test", project_flags=project_flags)
        assert project.project_flags == project_flags
