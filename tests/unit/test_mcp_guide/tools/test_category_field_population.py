"""Test that category_content sets category field on FileInfo."""

import json
from pathlib import Path

import pytest
from _pytest.monkeypatch import MonkeyPatch

from mcp_guide.models import Category, Project
from mcp_guide.tools.tool_category import CategoryContentArgs, category_content


def create_mock_session(tmp_path, project_data):
    """Create a mock session with required methods."""

    class MockSession:
        async def get_project(self):
            return project_data

        async def get_docroot(self):
            return str(tmp_path)

        def project_flags(self):
            class MockProjectFlags:
                async def list(self):
                    return {}

            return MockProjectFlags()

        def feature_flags(self):
            class MockFeatureFlags:
                async def list(self):
                    return {}

            return MockFeatureFlags()

    return MockSession()


@pytest.mark.asyncio
async def test_category_field_set_on_fileinfo(tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
    """Test that category field is set on FileInfo objects."""
    # Create test files
    category_dir = tmp_path / "guide"
    category_dir.mkdir()
    (category_dir / "README").write_text("# Test")

    # Project data
    project_data = Project(
        name="test",
        categories={"guide": Category(dir="guide", name="guide", patterns=["README"])},
        collections={},
    )

    async def mock_get_session(ctx=None):
        return create_mock_session(tmp_path, project_data)

    # Patch to capture FileInfo objects - must patch before module imports
    captured_files = []

    # Import and wrap the actual function
    from mcp_guide.content.utils import read_and_render_file_contents as original_read

    async def capture_read_contents(files, base_dir, docroot, template_context=None, category_prefix=None):
        nonlocal captured_files
        captured_files = list(files)  # Capture before processing
        return await original_read(files, base_dir, docroot, template_context, category_prefix)

    # Patch the imported reference in tool_category module
    import mcp_guide.tools.tool_category

    monkeypatch.setattr(mcp_guide.tools.tool_category, "read_and_render_file_contents", capture_read_contents)
    monkeypatch.setattr("mcp_guide.tools.tool_category.get_or_create_session", mock_get_session)

    # Call tool
    args = CategoryContentArgs(expression="guide")
    result_json = await category_content(args)

    # Parse result
    result = json.loads(result_json)
    assert result["success"] is True

    # Verify category field was set
    assert len(captured_files) > 0, "Should have captured FileInfo objects"
    for file_info in captured_files:
        assert file_info.category is not None, "FileInfo.category should be set"
        assert file_info.category.name == "guide", (
            f"FileInfo.category.name should be 'guide', got {file_info.category.name}"
        )
