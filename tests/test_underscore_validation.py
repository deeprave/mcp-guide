"""Test underscore prefix validation for categories."""

import pytest

from mcp_guide.models import Category
from mcp_guide.tools.tool_category import (
    CategoryAddArgs,
    CategoryChangeArgs,
    internal_category_add,
    internal_category_change,
)
from tests.helpers import create_test_session, request_context_for


@pytest.mark.anyio
async def test_category_add_rejects_underscore_prefix(runtime, tmp_path):
    """Test that category_add rejects names starting with underscore."""
    session = await create_test_session(runtime, "test")
    await session.get_project()

    request_context = await request_context_for(session)

    args = CategoryAddArgs(name="_commands")
    result = await internal_category_add(args, request_context)

    assert "Category names cannot start with underscore (reserved for system use)" in result.error


@pytest.mark.anyio
async def test_category_change_rejects_underscore_prefix(runtime, tmp_path):
    """Test that category_change rejects new names starting with underscore."""
    session = await create_test_session(runtime, "test")
    await session.get_project()

    request_context = await request_context_for(session)

    # First create a valid category
    await session.update_config(lambda project: project.with_category("docs", Category(dir="docs", patterns=["*.md"])))
    request_context = await request_context_for(session)

    # Try to rename to underscore prefix
    change_args = CategoryChangeArgs(name="docs", new_name="_commands")
    result = await internal_category_change(change_args, request_context)

    assert "Category names cannot start with underscore (reserved for system use)" in result.error
