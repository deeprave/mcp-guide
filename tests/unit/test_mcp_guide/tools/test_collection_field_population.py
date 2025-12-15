"""Test that get_collection_content sets category and collection fields on FileInfo."""

import json
from pathlib import Path

import pytest
from _pytest.monkeypatch import MonkeyPatch

from mcp_guide.models import Category, Collection, Project
from mcp_guide.tools.tool_collection import CollectionContentArgs, get_collection_content


@pytest.mark.asyncio
async def test_collection_content_sets_both_fields(tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
    """Test that collection content sets both category and collection fields."""
    # Create test files
    category_dir = tmp_path / "guide"
    category_dir.mkdir()
    (category_dir / "test.md").write_text("# Test")

    # Mock session
    class MockSession:
        async def get_project(self):
            return Project(
                name="test",
                categories=[Category(name="guide", dir="guide", patterns=["*.md"])],
                collections=[Collection(name="all", categories=["guide"])],
            )

        def get_docroot(self):
            return str(tmp_path)

    async def mock_get_session(ctx=None):
        return MockSession()

    # Patch to capture FileInfo objects
    captured_files = []

    async def capture_read_contents(files, base_dir, template_context=None, category_prefix=None):
        nonlocal captured_files
        captured_files = list(files)
        from mcp_guide.utils.content_utils import read_and_render_file_contents

        return await read_and_render_file_contents(files, base_dir, template_context, category_prefix)

    monkeypatch.setattr("mcp_guide.tools.tool_collection.get_or_create_session", mock_get_session)
    monkeypatch.setattr("mcp_guide.tools.tool_collection.read_and_render_file_contents", capture_read_contents)

    # Call tool
    args = CollectionContentArgs(collection="all")
    result_json = await get_collection_content(args)

    # Parse result
    result = json.loads(result_json)
    assert result["success"] is True

    # Verify both fields were set
    assert len(captured_files) > 0, "Should have captured FileInfo objects"
    for file_info in captured_files:
        assert file_info.category == "guide", f"FileInfo.category should be 'guide', got {file_info.category}"
        assert file_info.collection == "all", f"FileInfo.collection should be 'all', got {file_info.collection}"


@pytest.mark.asyncio
async def test_collection_content_empty_result_has_instruction(tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
    """Test that empty collection result includes instruction field."""
    # Create empty category
    category_dir = tmp_path / "guide"
    category_dir.mkdir()

    # Mock session
    class MockSession:
        async def get_project(self):
            return Project(
                name="test",
                categories=[Category(name="guide", dir="guide", patterns=["*.md"])],
                collections=[Collection(name="all", categories=["guide"])],
            )

        def get_docroot(self):
            return str(tmp_path)

    async def mock_get_session(ctx=None):
        return MockSession()

    monkeypatch.setattr("mcp_guide.tools.tool_collection.get_or_create_session", mock_get_session)

    # Call tool
    args = CollectionContentArgs(collection="all")
    result_json = await get_collection_content(args)

    # Parse result
    result = json.loads(result_json)
    assert result["success"] is True
    assert "instruction" in result, "Empty result should have instruction field"
    assert result["instruction"] is not None, "Instruction should not be None"
