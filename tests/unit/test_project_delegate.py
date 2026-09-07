"""Project binding exposes the selected data and rejects unbound access."""

import pytest

from mcp_guide.models.delegate import UNBOUND_PROJECT_NAME, ProjectDelegate
from mcp_guide.models.exceptions import NoProjectError
from mcp_guide.models.project import Project


def test_project_delegate_binding_lifecycle():
    delegate = ProjectDelegate()
    assert not delegate.is_bound
    assert delegate.name == UNBOUND_PROJECT_NAME
    with pytest.raises(NoProjectError):
        _ = delegate.project

    first = Project(name="first")
    delegate.bind(first)
    assert delegate.is_bound
    assert delegate.name == "first"
    assert delegate.project is first

    second = Project(name="second")
    delegate.bind(second)
    assert delegate.is_bound
    assert delegate.name == "second"
    assert delegate.project is second
