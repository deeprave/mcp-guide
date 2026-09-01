"""Test underscore prefix validation for categories."""

import pytest

from mcp_guide.tools.tool_category import (
    CategoryAddArgs,
    CategoryChangeArgs,
    internal_category_add,
    internal_category_change,
)
from tests.helpers import create_test_session


@pytest.mark.anyio
async def test_category_add_rejects_underscore_prefix(tmp_path, monkeypatch):
    """Test that category_add rejects names starting with underscore."""
    session = await create_test_session("test", _config_dir_for_tests=str(tmp_path))
    await session.get_project()

    async def get_bound_session_and_project(_ctx=None, *, session_id=None):
        return session, await session.get_project()

    monkeypatch.setattr(
        "mcp_guide.tools.tool_category.get_session_and_project",
        get_bound_session_and_project,
    )

    args = CategoryAddArgs(name="_commands")
    result = await internal_category_add(args)

    assert "Category names cannot start with underscore (reserved for system use)" in result.error


@pytest.mark.anyio
async def test_category_change_rejects_underscore_prefix(tmp_path, monkeypatch):
    """Test that category_change rejects new names starting with underscore."""
    session = await create_test_session("test", _config_dir_for_tests=str(tmp_path))
    await session.get_project()

    async def get_bound_session_and_project(_ctx=None, *, session_id=None):
        return session, await session.get_project()

    monkeypatch.setattr(
        "mcp_guide.tools.tool_category.get_session_and_project",
        get_bound_session_and_project,
    )

    # First create a valid category
    add_args = CategoryAddArgs(name="docs")
    await internal_category_add(add_args)

    # Try to rename to underscore prefix
    change_args = CategoryChangeArgs(name="docs", new_name="_commands")
    result = await internal_category_change(change_args)

    assert "Category names cannot start with underscore (reserved for system use)" in result.error
