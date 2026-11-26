"""Behavioural coverage for rendered Guide skill package exports."""

from datetime import datetime
from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast

import pytest

from mcp_guide.content_limits import ContentLimits
from mcp_guide.discovery.files import FileInfo
from mcp_guide.models.project import Category
from mcp_guide.result import Result
from mcp_guide.runtime import RequestContext
from mcp_guide.tools import tool_skill_export
from mcp_guide.tools.tool_skill_export import ExportSkillArgs


@pytest.mark.anyio
async def test_package_export_uses_configured_content_limit(monkeypatch):
    category = Category(dir="", patterns=["**/*"], name="skills")
    files = [
        FileInfo(
            path=Path("status-snapshot/SKILL.md"),
            name="status-snapshot/SKILL.md",
            size=4,
            content_size=4,
            mtime=datetime.now(),
            content="body",
            category=category,
        )
    ]

    async def package_files(*_args):
        return Result.ok(files)

    async def content_limits():
        return ContentLimits(max_content_limit=1)

    monkeypatch.setattr(tool_skill_export, "_package_files", package_files)
    monkeypatch.setattr(tool_skill_export, "get_content_limits", content_limits)
    request_context = cast(
        RequestContext,
        SimpleNamespace(is_bound=True, session=None, resolve_document_path=lambda path: Path(path)),
    )

    implementation = cast(Any, tool_skill_export.export_skill).__wrapped__
    result = await implementation(ExportSkillArgs(skill="status-snapshot"), request_context)

    assert result.is_error
    assert result.structured_content["error_type"] == "max_size_exceeded"
