"""Tests for feature flag integration with data models."""

from dataclasses import fields

from mcp_guide.models import Project


class TestProjectFeatureFlags:
    """Test Project project_flags field."""

    def test_project_has_project_flags_field(self):
        """Test that Project has project_flags field."""
        # Check that project_flags is a field
        field_names = [f.name for f in fields(Project)]
        assert "project_flags" in field_names

    def test_project_flags_default_empty_dict(self):
        """Test that project_flags defaults to empty dict."""
        project = Project(name="test")
        assert project.project_flags == {}
        assert isinstance(project.project_flags, dict)

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
