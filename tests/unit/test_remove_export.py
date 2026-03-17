"""Tests for remove_export tool."""

import json
from dataclasses import replace as dc_replace

import pytest

from mcp_guide.session import get_session
from mcp_guide.tools.tool_content import RemoveExportArgs, remove_export


@pytest.mark.asyncio
async def test_remove_export_success(session_temp_dir):
    """Test remove_export removes tracking entry."""
    session = await get_session()
    project = await session.get_project()
    updated = project.upsert_export_entry("docs", None, "/export.md", "a3f5c8d1")
    await session.update_config(lambda _: updated)

    # Execute
    args = RemoveExportArgs(expression="docs", pattern=None)
    result = await remove_export(args)

    # Verify
    data = json.loads(result)
    assert data["success"] is True

    # Verify entry removed
    project = await session.get_project()
    assert project.get_export_entry("docs", None) is None


@pytest.mark.asyncio
async def test_remove_export_not_found(session_temp_dir):
    """Test remove_export returns error when entry not found."""
    session = await get_session()
    project = await session.get_project()
    updated = dc_replace(project, exports={})
    await session.update_config(lambda _: updated)

    # Execute
    args = RemoveExportArgs(expression="nonexistent", pattern=None)
    result = await remove_export(args)

    # Verify
    data = json.loads(result)
    assert data["success"] is False


@pytest.mark.asyncio
async def test_remove_export_with_pattern(session_temp_dir):
    """Test remove_export with exact pattern match."""
    session = await get_session()
    project = await session.get_project()
    updated = dc_replace(project, exports={})
    updated = updated.upsert_export_entry("docs", "*.md", "/export.md", "a3f5c8d1")
    updated = updated.upsert_export_entry("docs", None, "/export2.md", "b2e4f9a7")
    await session.update_config(lambda _: updated)

    # Remove only the one with pattern
    args = RemoveExportArgs(expression="docs", pattern="*.md")
    result = await remove_export(args)

    # Verify
    data = json.loads(result)
    assert data["success"] is True

    # Verify only the pattern entry was removed
    project = await session.get_project()
    assert project.get_export_entry("docs", "*.md") is None
    assert project.get_export_entry("docs", None) is not None
