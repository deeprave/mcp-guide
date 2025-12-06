"""Test that get_category_content sets category field on FileInfo."""

import json
from pathlib import Path

import pytest
from _pytest.monkeypatch import MonkeyPatch

from mcp_guide.models import Category, Project
from mcp_guide.tools.tool_category import CategoryContentArgs, get_category_content


@pytest.mark.asyncio
async def test_category_field_set_on_fileinfo(tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
    """Test that category field is set on FileInfo objects."""
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
                collections=[],
            )

        def get_docroot(self):
            return str(tmp_path)

    async def mock_get_session(ctx=None):
        return MockSession()

    # Patch to capture FileInfo objects
    captured_files = []

    async def capture_read_contents(files, base_dir, category_prefix=None):
        nonlocal captured_files
        captured_files = list(files)  # Capture before processing
        from mcp_guide.utils.content_utils import read_file_contents

        return await read_file_contents(files, base_dir, category_prefix)

    monkeypatch.setattr("mcp_guide.tools.tool_category.get_or_create_session", mock_get_session)
    monkeypatch.setattr("mcp_guide.tools.tool_category.read_file_contents", capture_read_contents)

    # Call tool
    args = CategoryContentArgs(category="guide")
    result_json = await get_category_content(args)

    # Parse result
    result = json.loads(result_json)
    assert result["success"] is True

    # Verify category field was set
    assert len(captured_files) > 0, "Should have captured FileInfo objects"
    for file_info in captured_files:
        assert file_info.category == "guide", f"FileInfo.category should be 'guide', got {file_info.category}"
