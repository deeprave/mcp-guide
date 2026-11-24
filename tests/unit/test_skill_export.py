"""Local skill export produces portable package metadata."""

from types import SimpleNamespace
from typing import cast

import pytest
import yaml

from mcp_guide.result import Result
from mcp_guide.runtime import RequestContext
from mcp_guide.tools import tool_skill_export
from mcp_guide.tools.tool_skill_export import _entrypoint_content


def test_exported_entrypoint_has_portable_skill_metadata():
    content = _entrypoint_content("workflow-status", "Report workflow state.", "Check workflow.", "Body")
    frontmatter, body = content.removeprefix("---\n").split("\n---\n", 1)

    assert yaml.safe_load(frontmatter) == {
        "name": "workflow-status",
        "description": "Report workflow state.",
        "usage": "Check workflow.",
    }
    assert body == "Body"


@pytest.mark.anyio
async def test_package_lookup_accepts_a_dollar_prefixed_skill_name(monkeypatch):
    observed_names: list[str] = []

    class Skills:
        def get(self, key: str):
            observed_names.append(key)
            return None

    async def discover_skills(*_args):
        return Skills()

    monkeypatch.setattr(tool_skill_export, "_discover_guide_skills", discover_skills)
    request_context = cast(RequestContext, SimpleNamespace(session=None, resolve_document_path=lambda _path: None))

    result = await tool_skill_export._package_files("$workflow-status", request_context, None)

    assert observed_names == ["workflow-status"]
    assert isinstance(result, Result)
    assert not result.success
