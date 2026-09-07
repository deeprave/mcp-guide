"""Reserved system category names cannot be added or renamed into."""

import pytest

from mcp_guide.models import Category
from mcp_guide.tools.tool_category import (
    CategoryAddArgs,
    CategoryChangeArgs,
    internal_category_add,
    internal_category_change,
)
from tests.helpers import create_bound_test_session, request_context_for


@pytest.mark.anyio
async def test_reserved_category_names_leave_project_configuration_unchanged(runtime):
    runtime.configuration_service().config_file.write_text("projects: {}\nfeature_flags: {}\n")
    session = await create_bound_test_session(runtime, "test")
    await session.update_config(lambda p: p.with_category("docs", Category(dir="docs", patterns=["*.md"])))
    original = session.project
    for handler, args in (
        (internal_category_add, CategoryAddArgs(name="_commands")),
        (internal_category_change, CategoryChangeArgs(name="docs", new_name="_commands")),
    ):
        result = await handler(args, await request_context_for(session))
        assert not result.success
        assert "Category names cannot start with underscore (reserved for system use)" in result.error
        assert session.project == original
