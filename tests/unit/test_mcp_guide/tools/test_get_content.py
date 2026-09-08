"""Content formatting follows real global/project flags and rejects root escapes."""

from email import policy
from email.parser import Parser

import pytest
import yaml
from pydantic import ValidationError
from tests.helpers import create_bound_test_session, request_context_for, tool_result_payload

from mcp_guide.models import Category
from mcp_guide.tools.tool_content import ContentArgs, get_content, internal_get_content


def test_expression_field_is_required():
    with pytest.raises(ValidationError):
        ContentArgs()


@pytest.mark.anyio
@pytest.mark.parametrize(
    "project_format,global_format,expected",
    [
        (None, None, "none"),
        ("plain", None, "plain"),
        ("mime", None, "mime"),
        ("none", None, "none"),
        (None, "plain", "plain"),
        (None, "mime", "mime"),
        (None, "none", "none"),
        ("plain", "mime", "plain"),
        ("mime", "plain", "mime"),
        ("none", "plain", "none"),
    ],
)
async def test_content_format_resolution_uses_actual_headers_and_separators(
    runtime, tmp_path, project_format, global_format, expected
):
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "first.md").write_text("First content")
    (docs / "second.md").write_text("Second content")
    flags = {} if global_format is None else {"content-format": global_format}
    runtime.configuration_service().config_file.write_text(
        yaml.safe_dump({"docroot": str(tmp_path), "projects": {}, "feature_flags": flags})
    )
    session = await create_bound_test_session(runtime, "formatting")
    await session.update_config(lambda p: p.with_category("docs", Category(dir="docs", patterns=["*.md"])))
    if project_format is not None:
        await session.project_flags().set("content-format", project_format)
    result = await get_content.__wrapped__(ContentArgs(expression="docs"), await request_context_for(session))
    payload = tool_result_payload(result)
    assert payload["success"] is True
    content = payload["value"]
    if expected == "mime":
        message = Parser(policy=policy.default).parsestr(content)
        assert message.is_multipart()
        assert message.get_content_type() == "multipart/mixed"
        assert [part.get_payload() for part in message.iter_parts()] == ["First content", "Second content"]
    elif expected == "plain":
        assert content == "--- docs/first.md ---\nFirst content\n--- docs/second.md ---\nSecond content"
    else:
        assert content == "First content\nSecond content"


@pytest.mark.anyio
async def test_escaping_category_directory_returns_validation_error(runtime, tmp_path):
    docroot = tmp_path / "docs"
    docroot.mkdir()
    (tmp_path / "outside.md").write_text("Must not be read")
    runtime.configuration_service().config_file.write_text(yaml.safe_dump({"docroot": str(docroot), "projects": {}}))
    session = await create_bound_test_session(runtime, "escape")
    await session.update_config(lambda p: p.with_category("docs", Category(dir="../", patterns=["outside.md"])))
    result = await internal_get_content(ContentArgs(expression="docs"), await request_context_for(session))
    assert not result.success
    assert result.error_type == "validation_error"
    assert "document root" in result.error


@pytest.mark.anyio
async def test_get_content_exposes_declared_document_cache_policy(runtime, tmp_path):
    """Document frontmatter is adapted to the public Guide metadata contract."""
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "reference.md").write_text("---\ncache: long\n---\nReference content")
    runtime.configuration_service().config_file.write_text(yaml.safe_dump({"docroot": str(tmp_path), "projects": {}}))
    session = await create_bound_test_session(runtime, "content-cache")
    await session.update_config(lambda project: project.with_category("docs", Category(dir="docs", patterns=["*.md"])))

    response = await get_content.__wrapped__(ContentArgs(expression="docs"), await request_context_for(session))

    assert response.meta == {"mcp-guide": {"cache": {"ttl_ms": 86_400_000, "scope": "public"}}}


@pytest.mark.anyio
async def test_get_content_defaults_plain_markdown_to_long_public_cache(runtime, tmp_path):
    """Ordinary Markdown is exact static content unless it opts out."""
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "reference.md").write_text("Reference content")
    runtime.configuration_service().config_file.write_text(yaml.safe_dump({"docroot": str(tmp_path), "projects": {}}))
    session = await create_bound_test_session(runtime, "content-cache-default")
    await session.update_config(lambda project: project.with_category("docs", Category(dir="docs", patterns=["*.md"])))

    response = await get_content.__wrapped__(ContentArgs(expression="docs"), await request_context_for(session))

    assert response.meta == {"mcp-guide": {"cache": {"ttl_ms": 86_400_000, "scope": "public"}}}


@pytest.mark.anyio
async def test_get_content_logs_invalid_plain_markdown_cache_policy(runtime, tmp_path, caplog):
    """Unsupported cache tokens remain visible to content authors."""
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "reference.md").write_text("---\ncache: medium, unknown\n---\nReference content")
    runtime.configuration_service().config_file.write_text(yaml.safe_dump({"docroot": str(tmp_path), "projects": {}}))
    session = await create_bound_test_session(runtime, "content-cache-invalid")
    await session.update_config(lambda project: project.with_category("docs", Category(dir="docs", patterns=["*.md"])))

    response = await get_content.__wrapped__(ContentArgs(expression="docs"), await request_context_for(session))

    assert response.meta is None
    assert "Invalid cache policy" in caplog.text
