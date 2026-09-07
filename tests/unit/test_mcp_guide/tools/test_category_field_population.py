"""Category content resolves each file through its own configured category."""

from dataclasses import replace

import pytest
import yaml
from tests.helpers import create_bound_test_session, request_context_for

from mcp_guide.models import Category
from mcp_guide.tools.tool_category import CategoryContentArgs, internal_category_content


@pytest.mark.anyio
async def test_category_content_reads_same_named_files_from_the_correct_categories(runtime, tmp_path):
    docroot = tmp_path / "docs"
    for name in ("first", "second"):
        directory = docroot / name
        directory.mkdir(parents=True)
        (directory / "README").write_text(f"{name} category content")
    config = runtime.configuration_service().config_file
    config.parent.mkdir(parents=True, exist_ok=True)
    config.write_text(yaml.safe_dump({"docroot": str(docroot), "projects": {}}))
    session = await create_bound_test_session(runtime, "categories")
    await session.update_config(
        lambda project: replace(
            project,
            categories={name: Category(name=name, dir=name, patterns=["README"]) for name in ("first", "second")},
        )
    )
    result = await internal_category_content(
        CategoryContentArgs(expression="first,second"), await request_context_for(session)
    )
    assert result.success, result
    assert result.value == "first category content\nsecond category content"
