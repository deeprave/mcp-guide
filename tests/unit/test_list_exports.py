"""Tests for list_exports tool."""

import json
from dataclasses import replace as dc_replace
from unittest.mock import AsyncMock

import pytest

from mcp_guide.session import get_session
from mcp_guide.tools.tool_content import ListExportsArgs, list_exports


@pytest.mark.anyio
async def test_list_exports_empty(session_temp_dir):
    """Test list_exports returns empty array when no exports exist."""
    args = ListExportsArgs(glob=None)
    result = await list_exports(args)

    assert "[]" in result or '"value": []' in result


@pytest.mark.anyio
async def test_list_exports_single(session_temp_dir):
    """Test list_exports returns array with one export entry."""
    # Setup: Add export entry to project
    session = await get_session()
    project = await session.get_project()
    updated = project.upsert_export_entry("docs", None, "/export.md", "a3f5c8d1")
    await session.update_config(lambda _: updated)

    # Execute
    args = ListExportsArgs(glob=None)
    result = await list_exports(args)

    # Verify
    data = json.loads(result)
    assert data["success"] is True
    exports = data["value"]
    assert len(exports) == 1
    assert exports[0]["expression"] == "docs"
    assert exports[0]["pattern"] is None
    assert exports[0]["file"] == "export.md"
    assert exports[0]["path"] == "/"


@pytest.mark.anyio
async def test_list_exports_with_timestamp(session_temp_dir, tmp_path, monkeypatch):
    """Test list_exports includes exported_at timestamp stored at export time."""
    import time

    # Setup: Add export entry with a known timestamp
    session = await get_session()
    project = await session.get_project()
    ts = time.time()
    updated = project.upsert_export_entry("docs", None, str(tmp_path / "export.md"), "a3f5c8d1", exported_at=ts)
    await session.update_config(lambda _: updated)

    monkeypatch.setattr("mcp_guide.tools.tool_content.gather_content", AsyncMock(return_value=[]))
    monkeypatch.setattr("mcp_guide.tools.tool_content.compute_metadata_hash", lambda files: "a3f5c8d1")

    # Execute
    args = ListExportsArgs(glob=None)
    result = await list_exports(args)

    # Verify
    data = json.loads(result)
    exports = data["value"]
    assert len(exports) == 1
    assert exports[0]["exported_at"] == pytest.approx(ts)


@pytest.mark.anyio
async def test_list_exports_staleness(session_temp_dir, tmp_path):
    """Test list_exports computes staleness indicator."""
    # Create a category with a file
    from mcp_guide.models.project import Category

    session = await get_session()

    # Clear any existing exports
    project = await session.get_project()
    updated = dc_replace(project, exports={})
    await session.update_config(lambda _: updated)

    # Create test file
    test_file = tmp_path / "test.md"
    test_file.write_text("original content")

    # Add category
    category = Category(name="test-cat", dir=str(tmp_path), patterns=["*.md"])
    project = await session.get_project()
    updated = dc_replace(project, categories={"test-cat": category})
    await session.update_config(lambda _: updated)

    # Export with a fake hash that won't match
    export_file = tmp_path / "export.md"
    export_file.write_text("exported content")

    # Add export entry with fake hash (will be stale)
    project = await session.get_project()
    updated = project.upsert_export_entry("test-cat", None, str(export_file), "fakehash")
    await session.update_config(lambda _: updated)

    # Execute
    args = ListExportsArgs(glob=None)
    result = await list_exports(args)

    # Verify - should be stale (hash doesn't match)
    data = json.loads(result)
    exports = data["value"]
    assert len(exports) == 1
    assert exports[0]["stale_state"] == "stale"


@pytest.mark.anyio
async def test_list_exports_glob_filter(session_temp_dir, tmp_path, monkeypatch):
    """Test list_exports filters by glob pattern."""
    session = await get_session()
    monkeypatch.setattr("mcp_guide.tools.tool_content.gather_content", AsyncMock(return_value=[]))
    monkeypatch.setattr("mcp_guide.tools.tool_content.compute_metadata_hash", lambda files: "unchanged")

    # Clear exports and add multiple
    project = await session.get_project()
    updated = dc_replace(project, exports={})
    updated = updated.upsert_export_entry("docs", None, "/path/docs.md", "hash1")
    updated = updated.upsert_export_entry("api", "*.py", "/path/api.md", "hash2")
    updated = updated.upsert_export_entry("tests", None, "/other/tests.md", "hash3")
    await session.update_config(lambda _: updated)

    # Test: filter by expression glob
    args = ListExportsArgs(glob="doc*")
    result = await list_exports(args)
    data = json.loads(result)
    exports = data["value"]
    assert len(exports) == 1
    assert exports[0]["expression"] == "docs"

    # Test: filter by path glob
    args = ListExportsArgs(glob="*/other/*")
    result = await list_exports(args)
    data = json.loads(result)
    exports = data["value"]
    assert len(exports) == 1
    assert exports[0]["expression"] == "tests"

    # Test: filter by pattern glob
    args = ListExportsArgs(glob="*.py")
    result = await list_exports(args)
    data = json.loads(result)
    exports = data["value"]
    assert len(exports) == 1
    assert exports[0]["expression"] == "api"
