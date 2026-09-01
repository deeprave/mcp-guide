"""Tests for remove_export tool."""

from dataclasses import replace as dc_replace

import pytest
from tests.helpers import create_test_session, tool_result_payload

from mcp_guide.tools.tool_content import RemoveExportArgs, remove_export


@pytest.fixture
async def bound_session(tmp_path, monkeypatch):
    """Provide each tool test with its own bound production-shaped Session."""
    session = await create_test_session("remove-export", _config_dir_for_tests=str(tmp_path))

    async def get_bound_session_and_project(_ctx=None, *, session_id=None):
        return session, await session.get_project()

    monkeypatch.setattr(
        "mcp_guide.tools.tool_content.get_session_and_project",
        get_bound_session_and_project,
    )
    yield session


@pytest.mark.anyio
async def test_remove_export_success(bound_session):
    """Test remove_export removes tracking entry."""
    session = bound_session
    project = await session.get_project()
    updated = project.upsert_export_entry("docs", None, "/export.md", "a3f5c8d1")
    await session.update_config(lambda _: updated)

    # Execute
    args = RemoveExportArgs(expression="docs", pattern=None)
    result = await remove_export(args)

    # Verify
    data = tool_result_payload(result)
    assert data["success"] is True

    # Verify entry removed
    project = await session.get_project()
    assert project.get_export_entry("docs", None) is None


@pytest.mark.anyio
async def test_remove_export_not_found(bound_session):
    """Test remove_export returns error when entry not found."""
    session = bound_session
    project = await session.get_project()
    updated = dc_replace(project, exports={})
    await session.update_config(lambda _: updated)

    # Execute
    args = RemoveExportArgs(expression="nonexistent", pattern=None)
    result = await remove_export(args)

    # Verify
    data = tool_result_payload(result)
    assert data["success"] is False


@pytest.mark.anyio
async def test_remove_export_with_pattern(bound_session):
    """Test remove_export with exact pattern match."""
    session = bound_session
    project = await session.get_project()
    updated = dc_replace(project, exports={})
    updated = updated.upsert_export_entry("docs", "*.md", "/export.md", "a3f5c8d1")
    updated = updated.upsert_export_entry("docs", None, "/export2.md", "b2e4f9a7")
    await session.update_config(lambda _: updated)

    # Remove only the one with pattern
    args = RemoveExportArgs(expression="docs", pattern="*.md")
    result = await remove_export(args)

    # Verify
    data = tool_result_payload(result)
    assert data["success"] is True

    # Verify only the pattern entry was removed
    project = await session.get_project()
    assert project.get_export_entry("docs", "*.md") is None
    assert project.get_export_entry("docs", None) is not None
