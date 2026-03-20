"""Test underscore prefix validation for categories."""

import pytest

from mcp_guide.session import Session, remove_current_session, set_current_session
from mcp_guide.tools.tool_category import (
    CategoryAddArgs,
    CategoryChangeArgs,
    internal_category_add,
    internal_category_change,
)


@pytest.mark.anyio
async def test_category_add_rejects_underscore_prefix(tmp_path):
    """Test that category_add rejects names starting with underscore."""
    session = await Session.create_session("test", _config_dir_for_tests=str(tmp_path))
    await session.get_project()
    set_current_session(session)

    args = CategoryAddArgs(name="_commands")
    result = await internal_category_add(args)

    assert "Category names cannot start with underscore (reserved for system use)" in result.error
    await remove_current_session()


@pytest.mark.anyio
async def test_category_change_rejects_underscore_prefix(tmp_path):
    """Test that category_change rejects new names starting with underscore."""
    session = await Session.create_session("test", _config_dir_for_tests=str(tmp_path))
    await session.get_project()
    set_current_session(session)

    # First create a valid category
    add_args = CategoryAddArgs(name="docs")
    await internal_category_add(add_args)

    # Try to rename to underscore prefix
    change_args = CategoryChangeArgs(name="docs", new_name="_commands")
    result = await internal_category_change(change_args)

    assert "Category names cannot start with underscore (reserved for system use)" in result.error
    await remove_current_session()
