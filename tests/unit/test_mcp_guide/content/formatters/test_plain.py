"""Plain formatter output for empty, single and multiple documents."""

from datetime import datetime
from pathlib import Path

import pytest

from mcp_guide.content.formatters.plain import PlainFormatter
from mcp_guide.discovery.files import FileInfo


def _file(path, content):
    return FileInfo(
        path=Path(path),
        name=Path(path).name,
        size=len(content or ""),
        content_size=len(content or ""),
        mtime=datetime(2024, 1, 1),
        content=content,
    )


@pytest.mark.anyio
async def test_empty_list_has_no_output():
    assert await PlainFormatter().format([], Path("docs").joinpath) == ""


@pytest.mark.anyio
@pytest.mark.parametrize(
    "content", ["# Title\n  Leading\r\n\tTabs\nTrailing  ", "", None], ids=["whitespace", "empty", "none"]
)
async def test_single_document_preserves_content_without_headers(content):
    assert await PlainFormatter().format([_file("nested/file.md", content)], Path("docs").joinpath) == (content or "")


@pytest.mark.anyio
async def test_multiple_documents_preserve_content_and_use_basename_separators():
    files = [
        _file("docs/subdir/first.md", "# Title\n  Spaces  \r\n\tTabs\n"),
        _file("other/path/empty.md", None),
        _file("third.md", "Last"),
    ]
    assert await PlainFormatter().format(files, Path("docs").joinpath) == (
        "--- first.md ---\n# Title\n  Spaces  \r\n\tTabs\n\n--- empty.md ---\n\n--- third.md ---\nLast"
    )
