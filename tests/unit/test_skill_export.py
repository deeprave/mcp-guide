"""Behavioural coverage for rendered Guide skill package exports."""

from datetime import datetime
from pathlib import Path, PurePosixPath
from types import SimpleNamespace
from typing import Any, cast

import pytest
import yaml

from mcp_guide.config_constants import SKILLS_DIR
from mcp_guide.content_limits import ContentLimits
from mcp_guide.discovery.files import FileInfo
from mcp_guide.models.project import Category
from mcp_guide.result import Result
from mcp_guide.runtime import RequestContext
from mcp_guide.tools import tool_skill_export
from mcp_guide.tools.tool_resource import GuideSkill
from mcp_guide.tools.tool_skill_export import ExportSkillArgs


@pytest.mark.anyio
@pytest.mark.parametrize("requested_name", ["workflow-status", "$workflow-status"])
async def test_package_export_adds_portable_entrypoint_metadata(tmp_path, monkeypatch, requested_name):
    skills_root = tmp_path / "_skills"
    package_root = skills_root / "workflow-status"
    package_root.mkdir(parents=True)
    (package_root / "SKILL.md.mustache").write_text("Rendered body")
    skill = GuideSkill(
        name="workflow-status",
        description="Report workflow state.",
        usage="Check workflow.",
        frontmatter={},
        requirements={},
        package_root=PurePosixPath("workflow-status"),
    )

    async def discover_skills(*_args):
        return {skill.name: skill}

    async def read_skill(*_args, **_kwargs):
        return Result.ok("Rendered body")

    monkeypatch.setattr(tool_skill_export, "_discover_guide_skills", discover_skills)
    monkeypatch.setattr(tool_skill_export, "_read_guide_skill", read_skill)
    request_context = cast(
        RequestContext,
        SimpleNamespace(
            session=None, resolve_document_path=lambda path: skills_root if path == SKILLS_DIR else tmp_path / path
        ),
    )

    result = await tool_skill_export._package_files(requested_name, request_context, None)

    assert isinstance(result, Result)
    assert result.success
    assert result.value is not None
    assert len(result.value) == 1
    exported = result.value[0]
    frontmatter, body = cast(str, exported.content).removeprefix("---\n").split("\n---\n", 1)
    assert exported.path == Path("workflow-status/SKILL.md")
    assert yaml.safe_load(frontmatter) == {
        "name": "workflow-status",
        "description": "Report workflow state.",
        "usage": "Check workflow.",
    }
    assert body == "Rendered body"


@pytest.mark.anyio
async def test_package_export_uses_configured_content_limit(monkeypatch):
    category = Category(dir="", patterns=["**/*"], name="skills")
    files = [
        FileInfo(
            path=Path("workflow-status/SKILL.md"),
            name="workflow-status/SKILL.md",
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
    result = await implementation(ExportSkillArgs(skill="workflow-status"), request_context)

    assert result.is_error
    assert result.structured_content["error_type"] == "max_size_exceeded"
