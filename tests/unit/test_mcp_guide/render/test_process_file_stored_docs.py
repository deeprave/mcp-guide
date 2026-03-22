"""Tests for rendering stored documents via content_loader."""

from pathlib import Path
from unittest.mock import AsyncMock

import pytest

from mcp_guide.render.frontmatter import process_file


class _FakeFileInfo:
    """Minimal FileInfo-like object for testing process_file behaviour."""

    def __init__(
        self,
        content: str | None = None,
        path: Path = Path("/nonexistent/path.md"),
        has_loader: bool = True,
    ):
        self.path = path
        self.content_loader = AsyncMock(return_value=content) if has_loader else None


@pytest.mark.anyio
async def test_process_file_uses_content_loader_for_stored_docs():
    """process_file uses content_loader when present (stored document path)."""
    file_info = _FakeFileInfo("# Stored content\nHello from store")
    result = await process_file(file_info, requirements_context=None, render_context=None)

    assert result is not None
    assert "Stored content" in (result.content or "")
    file_info.content_loader.assert_called_once()


@pytest.mark.anyio
async def test_process_file_reads_filesystem_when_no_loader(tmp_path):
    """process_file falls back to filesystem when content_loader is None."""
    test_file = tmp_path / "doc.md"
    test_file.write_text("# Filesystem content")

    file_info = _FakeFileInfo(path=test_file, has_loader=False)
    result = await process_file(file_info, requirements_context=None, render_context=None)

    assert result is not None
    assert "Filesystem content" in (result.content or "")


@pytest.mark.anyio
async def test_process_file_content_loader_returns_empty_on_none():
    """process_file treats None from content_loader as empty string."""
    file_info = _FakeFileInfo(content=None)
    # Should not raise; empty content returns a result with empty content
    result = await process_file(file_info, requirements_context=None, render_context=None)
    assert result is not None


@pytest.mark.anyio
async def test_process_file_content_loader_with_frontmatter():
    """process_file parses frontmatter from content_loader output."""
    content_with_fm = "---\ntitle: Test Doc\n---\nBody text here"
    file_info = _FakeFileInfo(content_with_fm)
    result = await process_file(file_info, requirements_context=None, render_context=None)

    assert result is not None
    assert result.frontmatter.get("title") == "Test Doc"
    assert result.content == "Body text here"
