"""Tests for feature flag integration with data models."""

from dataclasses import fields

import pytest

from mcp_guide.feature_flags.types import FeatureValue
from mcp_guide.models import Category, Collection, GlobalConfig, Project


class TestGlobalConfigFeatureFlags:
    """Test GlobalConfig feature_flags field."""

    def test_global_config_has_feature_flags_field(self):
        """Test that GlobalConfig has feature_flags field."""
        # Check that feature_flags is a field
        field_names = [f.name for f in fields(GlobalConfig)]
        assert "feature_flags" in field_names

    def test_global_config_feature_flags_default_empty_dict(self):
        """Test that feature_flags defaults to empty dict."""
        config = GlobalConfig(docroot="/tmp", projects={})
        assert config.feature_flags == {}
        assert isinstance(config.feature_flags, dict)

    def test_global_config_feature_flags_accepts_valid_values(self):
        """Test that feature_flags accepts valid FeatureValue types."""
        feature_flags = {
            "bool_flag": True,
            "string_flag": "test",
            "list_flag": ["a", "b"],
            "dict_flag": {"key": "value"},
        }
        config = GlobalConfig(docroot="/tmp", projects={}, feature_flags=feature_flags)
        assert config.feature_flags == feature_flags


class TestProjectFeatureFlags:
    """Test Project project_flags field."""

    def test_project_has_project_flags_field(self):
        """Test that Project has project_flags field."""
        # Check that project_flags is a field
        field_names = [f.name for f in fields(Project)]
        assert "project_flags" in field_names

    def test_project_flags_default_empty_dict(self):
        """Test that project_flags defaults to empty dict."""
        project = Project(name="test", categories=[], collections=[])
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
        project = Project(name="test", categories=[], collections=[], project_flags=project_flags)
        assert project.project_flags == project_flags
