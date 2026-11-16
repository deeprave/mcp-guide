"""Standard MCP Skills integration tests."""

import pytest
from fastmcp import Client
from mcp.client.extension import ClientExtension
from mcp.shared.exceptions import MCPError

from mcp_guide.cli import ServerConfig
from mcp_guide.server import create_application


@pytest.fixture
async def applications():
    """Stop every application constructed by a test in this module."""
    created = []
    try:
        yield created
    finally:
        for application in reversed(created):
            await application.runtime.stop()


def _write_skill(docroot, *, name: str = "unbound-status") -> None:
    skill_root = docroot / "_skills" / name
    skill_root.mkdir(parents=True)
    (skill_root / "SKILL.md.mustache").write_text(
        "---\n"
        f"name: {name}\n"
        "description: Report workflow status.\n"
        "usage: Use when status is needed.\n"
        "project-bind: true\n"
        "---\n"
        "{{#unbound}}Bind a project first.{{/unbound}}\n",
        encoding="utf-8",
    )
    resources = skill_root / "resources"
    resources.mkdir()
    (resources / "guide.md.mustache").write_text("Use the rendered guide.\n", encoding="utf-8")


@pytest.mark.anyio
async def test_standard_skills_are_discoverable_and_readable_unbound(tmp_path, monkeypatch, applications) -> None:
    """FastMCP exposes an unbound Guide catalogue via standard Skills methods."""
    monkeypatch.setenv("MCP_GUIDE_DISABLE_SERVER_TASKS", "1")
    config_dir = tmp_path / "config"
    docroot = tmp_path / "docs"
    config_dir.mkdir()
    _write_skill(docroot)
    application = create_application(ServerConfig(configdir=str(config_dir), docroot=str(docroot)))
    applications.append(application)

    class SkillsClientExtension(ClientExtension):
        identifier = "io.modelcontextprotocol/skills"

    async with Client(application.server, mode="auto", extensions=[SkillsClientExtension()]) as client:
        skills = await client.list_skills()
        with pytest.raises(MCPError, match="No project available"):
            await client.read_resource("skill://unbound-status/SKILL.md")

    assert "skill://unbound-status/SKILL.md" in [entry.uri for entry in skills]
