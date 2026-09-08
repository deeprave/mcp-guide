"""Native resource responses from actual content and command routing."""

import json
from unittest.mock import AsyncMock, patch

import pytest

from mcp_guide.resources import guide_command_resource, guide_resource


@pytest.mark.anyio
async def test_content_resource_uses_bound_project_and_policy_subpaths(resource_project):
    async def read(category, document):
        result = await guide_resource.__wrapped__(
            category, document, request_context=resource_project, request_uri=None
        )
        payload = json.loads(result.contents[0].content)
        assert payload["success"] is True
        assert payload["session_id"] == "resource-session"
        return payload["value"]

    assert await read("docs", "readme") == "docs content"
    assert await read("docs", "") == "docs content"
    assert await read("policies", "git/ops") == "git policy"


@pytest.mark.anyio
async def test_command_resource_preserves_query_aliases_and_failure(resource_project):
    result = await guide_command_resource.__wrapped__(
        "project", request_context=resource_project, request_uri="guide://_project?table=true"
    )
    payload = json.loads(result.contents[0].content)
    assert payload["success"] is True
    assert payload["session_id"] == "resource-session"
    assert payload["value"] == "resource-project verbose table"

    missing = await guide_command_resource.__wrapped__("unknown", request_context=resource_project, request_uri=None)
    payload = json.loads(missing.contents[0].content)
    assert payload["success"] is False
    assert "unknown" in payload["error"]


@pytest.mark.anyio
async def test_document_resource_exposes_cache_metadata_but_command_resource_does_not(resource_project):
    """Only non-command Guide resources expose a document cache policy."""
    resource_project.resolve_document_path("docs/readme.md").write_text("---\ncache: long\n---\ndocs content")

    document = await guide_resource.__wrapped__("docs", "readme", request_context=resource_project, request_uri=None)
    command = await guide_command_resource.__wrapped__("project", request_context=resource_project, request_uri=None)

    assert document.meta == {"mcp-guide": {"cache": {"ttl_ms": 86_400_000, "scope": "public"}}}
    assert command.meta is None


@pytest.mark.anyio
@pytest.mark.parametrize(
    "exception,expected",
    [
        (ValueError("Invalid value"), "Invalid value"),
        (FileNotFoundError("File not found"), "File not found"),
        (PermissionError("Permission denied"), "Permission denied"),
        (Exception("Unexpected error"), "Unexpected error: Unexpected error"),
    ],
)
async def test_resource_serialises_propagated_errors(resource_project, exception, expected):
    # Inject propagated failures deterministically; normal content errors become Results before this boundary.
    with patch("mcp_guide.resources.internal_get_content", new=AsyncMock(side_effect=exception)):
        result = await guide_resource.__wrapped__("docs", "readme", request_context=resource_project, request_uri=None)
    payload = json.loads(result.contents[0].content)
    assert payload["success"] is False
    assert payload["error"] == expected
