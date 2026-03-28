"""Tests for ProjectDelegate."""

import pytest

from mcp_guide.models.delegate import UNBOUND_PROJECT_NAME, ProjectDelegate
from mcp_guide.models.exceptions import NoProjectError
from mcp_guide.models.project import Project


def make_project(name: str = "test-project") -> Project:
    """Create a minimal Project for testing."""
    return Project(name=name)


class TestProjectDelegateUnbound:
    """Test ProjectDelegate in unbound state."""

    def test_is_bound_false(self):
        delegate = ProjectDelegate()
        assert delegate.is_bound is False

    def test_name_returns_placeholder(self):
        delegate = ProjectDelegate()
        assert delegate.name == UNBOUND_PROJECT_NAME

    def test_project_raises_no_project_error(self):
        delegate = ProjectDelegate()
        with pytest.raises(NoProjectError):
            _ = delegate.project


class TestProjectDelegateBound:
    """Test ProjectDelegate after binding."""

    def test_is_bound_true(self):
        delegate = ProjectDelegate()
        delegate.bind(make_project())
        assert delegate.is_bound is True

    def test_name_returns_project_name(self):
        delegate = ProjectDelegate()
        delegate.bind(make_project("my-project"))
        assert delegate.name == "my-project"

    def test_project_returns_real_project(self):
        delegate = ProjectDelegate()
        project = make_project()
        delegate.bind(project)
        assert delegate.project is project

    def test_rebind_replaces_project(self):
        delegate = ProjectDelegate()
        delegate.bind(make_project("first"))
        delegate.bind(make_project("second"))
        assert delegate.name == "second"
