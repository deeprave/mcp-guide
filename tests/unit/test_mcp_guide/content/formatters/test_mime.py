"""MIME formatting preserves document content, locations and byte lengths."""

from datetime import datetime
from email import policy
from email.parser import Parser
from pathlib import Path

import pytest

from mcp_guide.content.formatters.mime import MimeFormatter
from mcp_guide.content_limits import ContentLimitExceeded
from mcp_guide.discovery.files import FileInfo
from mcp_guide.models.project import Category
from mcp_guide.render.cache_policy import CachePolicy


def document(path, content, cache: str | None = None):
    # Stale source sizes must never leak into final rendered Content-Length.
    file_info = FileInfo(
        path=Path(path),
        name=Path(path).name,
        size=200,
        content_size=50,
        mtime=datetime(2026, 1, 1),
        content=content,
        category=Category(dir="docs", patterns=["*"], name="docs"),
    )
    file_info.cache_policy = CachePolicy.parse_with_diagnostic(cache)[0]
    return file_info


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
        "Cache-Control: no-cache",
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
        assert part["Cache-Control"] == "no-cache"
        assert part.get_payload() == content
        assert f"--{boundary}\r\nContent-Type: {content_type}\r\n" in result


@pytest.mark.anyio
async def test_multipart_headers_preserve_each_documents_cache_policy(tmp_path):
    files = [document("public.md", "Public", "long"), document("dynamic.md", "Dynamic")]

    result = await MimeFormatter().format(files, tmp_path.joinpath)
    parts = list(Parser(policy=policy.default).parsestr(result).iter_parts())

    assert [part["Cache-Control"] for part in parts] == ["public, max-age=86400", "no-cache"]


@pytest.mark.anyio
@pytest.mark.parametrize(
    ("path", "location"),
    [
        ("nested/space name.md", "guide://docs/nested/space%20name.md"),
        ("nested/100%#?.md", "guide://docs/nested/100%25%23%3F.md"),
        ("nested/日本語.md", "guide://docs/nested/%E6%97%A5%E6%9C%AC%E8%AA%9E.md"),
    ],
)
async def test_mime_content_location_encodes_each_path_segment(tmp_path, path, location):
    result = await MimeFormatter().format([document(path, "content")], tmp_path.joinpath)

    assert f"Content-Location: {location}\r\n" in result


@pytest.mark.anyio
async def test_multipart_legacy_control_character_name_cannot_inject_headers(tmp_path):
    result = await MimeFormatter().format(
        [document("safe.md", "safe"), document("unsafe\r\nInjected: value.md", "unsafe")],
        tmp_path.joinpath,
    )

    message = Parser(policy=policy.default).parsestr(result)
    parts = list(message.iter_parts())
    assert message.defects == []
    assert len(parts) == 2
    assert parts[1].defects == []
    assert parts[1]["Injected"] is None
    assert parts[1]["Content-Location"] == "guide://docs/unsafe%0D%0AInjected%3A%20value.md"


@pytest.mark.anyio
async def test_mime_headers_count_towards_aggregate_limit(tmp_path):
    with pytest.raises(ContentLimitExceeded, match="max-content-limit"):
        await MimeFormatter().format([document("test.md", "body")], tmp_path.joinpath, max_content_limit=4)
