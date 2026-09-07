"""MIME formatting preserves document content, locations and byte lengths."""

from datetime import datetime
from email import policy
from email.parser import Parser
from pathlib import Path

import pytest

from mcp_guide.content.formatters.mime import MimeFormatter
from mcp_guide.discovery.files import FileInfo
from mcp_guide.models.project import Category


def document(path, content):
    # Stale source sizes must never leak into final rendered Content-Length.
    return FileInfo(
        path=Path(path),
        name=Path(path).name,
        size=200,
        content_size=50,
        mtime=datetime(2026, 1, 1),
        content=content,
        category=Category(dir="docs", patterns=["*"], name="docs"),
    )


@pytest.mark.anyio
async def test_format_empty_list(tmp_path):
    assert await MimeFormatter().format([], tmp_path.joinpath) == ""


@pytest.mark.anyio
@pytest.mark.parametrize(
    "path, content, content_type",
    [
        ("nested/test.md", "# Test\n\nMarkdown content", "text/markdown"),
        ("unicode.txt", "Hello 世界 🌍", "text/plain"),
        ("file.unknownext123", "Unknown file type", "text/plain"),
    ],
    ids=["markdown", "utf8-text", "unknown-extension"],
)
async def test_single_file_headers_and_exact_content(tmp_path, path, content, content_type):
    result = await MimeFormatter().format([document(path, content)], tmp_path.joinpath)
    headers, payload = result.split("\r\n\r\n", 1)
    assert headers.split("\r\n") == [
        f"Content-Type: {content_type}",
        f"Content-Location: guide://docs/{path}",
        f"Content-Length: {len(content.encode('utf-8'))}",
    ]
    assert payload == content


@pytest.mark.anyio
async def test_multipart_headers_framing_and_content(tmp_path):
    contents = ["# Title\n\nWith **formatting**", "  Spaces 世界  \n\tTabs\n"]
    files = [document("nested/file1.md", contents[0]), document("file2.txt", contents[1])]
    result = await MimeFormatter().format(files, tmp_path.joinpath)
    message = Parser(policy=policy.default).parsestr(result)
    assert message.get_content_type() == "multipart/mixed"
    assert message.defects == []
    boundary = message.get_boundary()
    assert boundary
    assert result.startswith(f'Content-Type: multipart/mixed; boundary="{boundary}"\r\n\r\n')
    assert result.endswith(f"--{boundary}--\r\n")
    parts = list(message.iter_parts())
    assert len(parts) == 2
    for part, file, content, content_type in zip(parts, files, contents, ["text/markdown", "text/plain"]):
        assert part.defects == []
        assert part.get_content_type() == content_type
        assert part["Content-Location"] == f"guide://docs/{file.path.as_posix()}"
        assert int(part["Content-Length"]) == len(content.encode("utf-8"))
        assert part.get_payload() == content
        assert f"--{boundary}\r\nContent-Type: {content_type}\r\n" in result
