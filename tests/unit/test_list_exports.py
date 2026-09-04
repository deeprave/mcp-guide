"""Tests for list_exports tool."""

from dataclasses import replace as dc_replace
from pathlib import Path
from unittest.mock import AsyncMock

import pytest
from tests.helpers import create_unbound_test_session, request_context_for, tool_result_payload

from mcp_guide.runtime import get_runtime
from mcp_guide.tools.tool_content import ListExportsArgs
from mcp_guide.tools.tool_content import list_exports as _list_exports


async def list_exports(args, session):
    """Exercise list-export behaviour with the test's explicit Session."""
    return await _list_exports.__wrapped__(args, await request_context_for(session))


@pytest.mark.anyio
async def test_list_exports_empty(runtime, session_temp_dir):
    """Test list_exports returns empty array when no exports exist."""
    session = create_unbound_test_session(runtime)
    await session.bind_project_path(Path(session_temp_dir))
    args = ListExportsArgs(glob=None)
    result = await list_exports(args, session)

    assert tool_result_payload(result)["value"] == []


@pytest.mark.anyio
async def test_list_exports_single(runtime, session_temp_dir):
    """Test list_exports returns array with one export entry."""
    # Setup: Add export entry to project
    session = create_unbound_test_session(runtime)
    await session.bind_project_path(Path(session_temp_dir))
    project = await session.get_project()
    updated = project.upsert_export_entry("docs", None, "/export.md", "a3f5c8d1")
    await session.update_config(lambda _: updated)

    # Execute
    args = ListExportsArgs(glob=None)
    result = await list_exports(args, session)

    # Verify
    data = tool_result_payload(result)
    assert data["success"] is True
    exports = data["value"]
    assert len(exports) == 1
    assert exports[0]["expression"] == "docs"
    assert exports[0]["pattern"] is None
    assert exports[0]["file"] == "export.md"
    assert exports[0]["path"] == "/"


@pytest.mark.anyio
async def test_list_exports_with_timestamp(runtime, session_temp_dir, tmp_path, monkeypatch):
    """Test list_exports includes exported_at timestamp stored at export time."""
    import time

    # Setup: Add export entry with a known timestamp
    session = create_unbound_test_session(runtime)
    await session.bind_project_path(Path(session_temp_dir))
    project = await session.get_project()
    ts = time.time()
    updated = project.upsert_export_entry("docs", None, str(tmp_path / "export.md"), "a3f5c8d1", exported_at=ts)
    await session.update_config(lambda _: updated)

    monkeypatch.setattr("mcp_guide.tools.tool_content.gather_content", AsyncMock(return_value=[]))
    monkeypatch.setattr("mcp_guide.tools.tool_content.compute_metadata_hash", lambda files: "a3f5c8d1")

    # Execute
    args = ListExportsArgs(glob=None)
    result = await list_exports(args, session)

    # Verify
    data = tool_result_payload(result)
    exports = data["value"]
    assert len(exports) == 1
    assert exports[0]["exported_at"] == pytest.approx(ts)


@pytest.mark.anyio
async def test_list_exports_staleness(runtime, session_temp_dir, tmp_path):
    """Test list_exports computes staleness indicator."""
    # Create a category with a file
    from mcp_guide.models.project import Category

    session = create_unbound_test_session(runtime)
    await session.bind_project_path(Path(session_temp_dir))

    # Clear any existing exports
    project = await session.get_project()
    updated = dc_replace(project, exports={})
    await session.update_config(lambda _: updated)

    docroot = Path(await get_runtime().get_docroot())
    category_dir = docroot / "test-cat"
    category_dir.mkdir(parents=True, exist_ok=True)
    (category_dir / "test.md").write_text("original content")

    category = Category(name="test-cat", dir="test-cat", patterns=["*.md"])
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
    result = await list_exports(args, session)

    # Verify - should be stale (hash doesn't match)
    data = tool_result_payload(result)
    exports = data["value"]
    assert len(exports) == 1
    assert exports[0]["stale_state"] == "stale"


@pytest.mark.anyio
async def test_list_exports_glob_filter(runtime, session_temp_dir, tmp_path, monkeypatch):
    """Test list_exports filters by glob pattern."""
    session = create_unbound_test_session(runtime)
    await session.bind_project_path(Path(session_temp_dir))
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
    result = await list_exports(args, session)
    data = tool_result_payload(result)
    exports = data["value"]
    assert len(exports) == 1
    assert exports[0]["expression"] == "docs"

    # Test: filter by path glob
    args = ListExportsArgs(glob="*/other/*")
    result = await list_exports(args, session)
    data = tool_result_payload(result)
    exports = data["value"]
    assert len(exports) == 1
    assert exports[0]["expression"] == "tests"

    # Test: filter by pattern glob
    args = ListExportsArgs(glob="*.py")
    result = await list_exports(args, session)
    data = tool_result_payload(result)
    exports = data["value"]
    assert len(exports) == 1
    assert exports[0]["expression"] == "api"
