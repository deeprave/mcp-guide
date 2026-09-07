"""Export removal matches exact keys and changes tracking, not exported files."""

import pytest
from tests.helpers import create_bound_test_session, request_context_for, tool_result_payload

from mcp_guide.tools.tool_content import RemoveExportArgs, remove_export


@pytest.mark.anyio
async def test_remove_export_matches_pattern_and_preserves_file(runtime, tmp_path):
    session = await create_bound_test_session(runtime, "remove-export")
    exported = tmp_path / "export.md"
    exported.write_text("exported content")
    await session.update_config(
        lambda p: p.upsert_export_entry("docs", "*.md", str(exported), "a3f5c8d1").upsert_export_entry(
            "docs", None, "/export2.md", "b2e4f9a7"
        )
    )

    async def remove(pattern):
        result = await remove_export.__wrapped__(
            RemoveExportArgs(expression="docs", pattern=pattern), await request_context_for(session)
        )
        return tool_result_payload(result)

    assert (await remove("*.md"))["success"] is True
    project = await session.get_project()
    assert project.get_export_entry("docs", "*.md") is None
    assert project.get_export_entry("docs", None) is not None
    missing = await remove("*.md")
    assert missing["success"] is False
    assert missing["error_type"] == "not_found"
    assert (await remove(None))["success"] is True
    assert (await session.get_project()).get_export_entry("docs", None) is None
    assert exported.read_text() == "exported content"
