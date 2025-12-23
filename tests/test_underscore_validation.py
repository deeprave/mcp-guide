"""Test underscore prefix validation for categories."""

import pytest

from mcp_guide.tools.tool_category import CategoryAddArgs, CategoryChangeArgs, category_add, category_change


@pytest.mark.asyncio
async def test_category_add_rejects_underscore_prefix(tmp_path):
    """Test that category_add rejects names starting with underscore."""
    args = CategoryAddArgs(name="_commands")

    result = await category_add(args)

    assert "Category names cannot start with underscore (reserved for system use)" in result


@pytest.mark.asyncio
async def test_category_change_rejects_underscore_prefix(tmp_path):
    """Test that category_change rejects new names starting with underscore."""
    # First create a valid category
    add_args = CategoryAddArgs(name="docs")
    await category_add(add_args)

    # Try to rename to underscore prefix
    change_args = CategoryChangeArgs(name="docs", new_name="_commands")

    result = await category_change(change_args)

    assert "Category names cannot start with underscore (reserved for system use)" in result
