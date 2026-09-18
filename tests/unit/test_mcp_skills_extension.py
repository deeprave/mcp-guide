"""MCP skills-extension contract tests."""

from typing import Any, cast

import pytest


@pytest.fixture
async def applications():
    """Stop every application constructed by a test in this module."""
    created = []
    try:
        yield created
    finally:
        for application in reversed(created):
            await application.runtime.stop()


def _write_skill(
    docroot,
    *,
    name: str = "workflow-status",
    content: str = "Read the workflow file.\n",
) -> None:
    """Create one package-shaped skill without relying on production templates."""
    skill_root = docroot / "_skills" / name
    skill_root.mkdir(parents=True)
    (skill_root / "SKILL.md.mustache").write_text(
        "---\n"
        f"name: {name}\n"
        "description: Report the configured workflow file.\n"
        "usage: Use when the user asks for workflow status.\n"
        "---\n"
        f"{content}",
        encoding="utf-8",
    )


@pytest.mark.anyio
async def test_mcp_skills_extension_is_registered_only_when_enabled(tmp_path) -> None:
    """The feature flag gates the complete negotiated extension surface."""
    from mcp_guide.cli import ServerConfig
    from mcp_guide.mcp_skills_extension import MCP_SKILLS_EXTENSION_ID
    from mcp_guide.server import create_application

    (tmp_path / "config.yaml").write_text("feature_flags:\n  mcp-skills: true\n", encoding="utf-8")
    enabled = create_application(ServerConfig(configdir=str(tmp_path)))

    assert MCP_SKILLS_EXTENSION_ID in enabled.server._extensions
    assert MCP_SKILLS_EXTENSION_ID in (enabled.server._mcp_server.get_capabilities().extensions or {})
    await enabled.runtime.stop()

    disabled_dir = tmp_path / "disabled"
    disabled_dir.mkdir()
    (disabled_dir / "config.yaml").write_text("feature_flags: {}\n", encoding="utf-8")
    disabled = create_application(ServerConfig(configdir=str(disabled_dir)))

    assert MCP_SKILLS_EXTENSION_ID not in disabled.server._extensions
    assert MCP_SKILLS_EXTENSION_ID not in (disabled.server._mcp_server.get_capabilities().extensions or {})
    await disabled.runtime.stop()


@pytest.mark.anyio
async def test_native_skill_resource_preserves_arbitrary_query_arguments(tmp_path, monkeypatch, applications) -> None:
    """A native resource read preserves every skill template keyword."""
    from fastmcp import Client

    from mcp_guide.cli import ServerConfig
    from mcp_guide.server import create_application

    monkeypatch.setenv("MCP_GUIDE_DISABLE_SERVER_TASKS", "1")
    config_dir = tmp_path / "config"
    docroot = tmp_path / "docs"
    project_root = tmp_path / "project"
    config_dir.mkdir()
    project_root.mkdir()
    _write_skill(
        docroot,
        name="query-test",
        content="Mode={{kwargs.mode}}; dry-run={{kwargs.dry_run}}\n",
    )
    application = create_application(ServerConfig(configdir=str(config_dir), docroot=str(docroot)))
    applications.append(application)

    async with Client(application.server, mode="2026-07-28") as client:
        bound = await client.call_tool("set_project", {"args": {"path": str(project_root)}})
        assert bound.structured_content is not None
        session_id = bound.structured_content["session_id"]
        resource = await client.read_resource(f"guide://$query-test?mode=summary&dry-run&session_id={session_id}")

    assert resource[0].text is not None
    assert "Mode=summary; dry-run=True" in resource[0].text


@pytest.mark.anyio
async def test_negotiated_skills_list_returns_only_bound_session_skills(tmp_path, monkeypatch, applications) -> None:
    """The formal extension reuses the project-aware Guide skill catalogue."""
    from fastmcp import Client
    from mcp.client.extension import ClientExtension

    from mcp_guide.cli import ServerConfig
    from mcp_guide.mcp_skills_extension import (
        MCP_SKILLS_EXTENSION_ID,
        SkillsListParams,
        SkillsListRequest,
        SkillsListResult,
    )
    from mcp_guide.server import create_application

    class SkillsClientExtension(ClientExtension):
        identifier = MCP_SKILLS_EXTENSION_ID

    monkeypatch.setenv("MCP_GUIDE_DISABLE_SERVER_TASKS", "1")
    config_dir = tmp_path / "config"
    docroot = tmp_path / "docs"
    project_root = tmp_path / "project"
    config_dir.mkdir()
    project_root.mkdir()
    (config_dir / "config.yaml").write_text("feature_flags:\n  mcp-skills: true\n", encoding="utf-8")
    _write_skill(docroot)
    application = create_application(ServerConfig(configdir=str(config_dir), docroot=str(docroot)))
    applications.append(application)

    async with Client(
        application.server,
        mode="2026-07-28",
        extensions=[SkillsClientExtension()],
    ) as client:
        bound = await client.call_tool("set_project", {"args": {"path": str(project_root)}})
        assert bound.structured_content is not None
        session_id = bound.structured_content["session_id"]
        result = await client.session.send_request(
            SkillsListRequest(params=SkillsListParams(session_id=session_id)),
            SkillsListResult,
        )

    assert [skill.identifier for skill in result.skills] == ["workflow-status"]
    assert result.skills[0].uri == "guide://$workflow-status"


@pytest.mark.anyio
async def test_skills_list_change_notification_requires_an_effective_change(
    tmp_path, monkeypatch, applications
) -> None:
    """A tracked session receives one payload-free refresh notification per list change."""
    from fastmcp import Client
    from mcp.client.extension import ClientExtension

    import mcp_guide.mcp_skills_extension as extension_module
    from mcp_guide.cli import ServerConfig
    from mcp_guide.mcp_skills_extension import (
        MCP_SKILLS_EXTENSION_ID,
        SKILLS_LIST_CHANGED_METHOD,
        GuideSkillsExtension,
        SkillsListParams,
        SkillsListRequest,
        SkillsListResult,
    )
    from mcp_guide.server import create_application

    class SkillsClientExtension(ClientExtension):
        identifier = MCP_SKILLS_EXTENSION_ID

    class CurrentMcpContext:
        def __init__(self, session_id: str) -> None:
            self.session_id = session_id
            self.notifications = []

        def client_supports_extension(self, identifier: str) -> bool:
            return identifier == MCP_SKILLS_EXTENSION_ID

        async def send_notification(self, notification) -> None:
            self.notifications.append(notification)

    monkeypatch.setenv("MCP_GUIDE_DISABLE_SERVER_TASKS", "1")
    config_dir = tmp_path / "config"
    docroot = tmp_path / "docs"
    project_root = tmp_path / "project"
    config_dir.mkdir()
    project_root.mkdir()
    (config_dir / "config.yaml").write_text("feature_flags:\n  mcp-skills: true\n", encoding="utf-8")
    _write_skill(docroot)
    application = create_application(ServerConfig(configdir=str(config_dir), docroot=str(docroot)))
    applications.append(application)

    async with Client(
        application.server,
        mode="2026-07-28",
        extensions=[SkillsClientExtension()],
    ) as client:
        bound = await client.call_tool("set_project", {"args": {"path": str(project_root)}})
        assert bound.structured_content is not None
        session_id = bound.structured_content["session_id"]
        await client.session.send_request(
            SkillsListRequest(params=SkillsListParams(session_id=session_id)),
            SkillsListResult,
        )

        extension = cast(GuideSkillsExtension, application.server._extensions[MCP_SKILLS_EXTENSION_ID])
        session = next(iter(extension._effective_skills))
        current_context = CurrentMcpContext(session_id)
        monkeypatch.setattr(extension_module, "get_context", lambda: current_context)

        update = cast(Any, object())
        await extension.on_configuration_changed(session, update)
        _write_skill(docroot, name="workflow-check")
        await extension.on_configuration_changed(session, update)
        await extension.on_configuration_changed(session, update)

    assert len(current_context.notifications) == 1
    assert current_context.notifications[0].method == SKILLS_LIST_CHANGED_METHOD
    assert current_context.notifications[0].params is None


@pytest.mark.anyio
async def test_skills_list_change_detects_a_delayed_skill_tree_update(tmp_path, monkeypatch, applications) -> None:
    """The next owning request notices a package update without a config event."""
    from fastmcp import Client
    from mcp.client.extension import ClientExtension

    import mcp_guide.mcp_skills_extension as extension_module
    from mcp_guide.cli import ServerConfig
    from mcp_guide.mcp_skills_extension import (
        MCP_SKILLS_EXTENSION_ID,
        SKILLS_LIST_CHANGED_METHOD,
        GuideSkillsExtension,
        SkillsListParams,
        SkillsListRequest,
        SkillsListResult,
    )
    from mcp_guide.server import create_application

    class SkillsClientExtension(ClientExtension):
        identifier = MCP_SKILLS_EXTENSION_ID

    class CurrentMcpContext:
        def __init__(self, session_id: str) -> None:
            self.session_id = session_id
            self.notifications = []

        def client_supports_extension(self, identifier: str) -> bool:
            return identifier == MCP_SKILLS_EXTENSION_ID

        async def send_notification(self, notification) -> None:
            self.notifications.append(notification)

    monkeypatch.setenv("MCP_GUIDE_DISABLE_SERVER_TASKS", "1")
    config_dir = tmp_path / "config"
    docroot = tmp_path / "docs"
    project_root = tmp_path / "project"
    config_dir.mkdir()
    project_root.mkdir()
    (config_dir / "config.yaml").write_text("feature_flags:\n  mcp-skills: true\n", encoding="utf-8")
    _write_skill(docroot)
    application = create_application(ServerConfig(configdir=str(config_dir), docroot=str(docroot)))
    applications.append(application)

    async with Client(
        application.server,
        mode="2026-07-28",
        extensions=[SkillsClientExtension()],
    ) as client:
        bound = await client.call_tool("set_project", {"args": {"path": str(project_root)}})
        assert bound.structured_content is not None
        session_id = bound.structured_content["session_id"]
        await client.session.send_request(
            SkillsListRequest(params=SkillsListParams(session_id=session_id)),
            SkillsListResult,
        )

        extension = cast(GuideSkillsExtension, application.server._extensions[MCP_SKILLS_EXTENSION_ID])
        session = next(iter(extension._effective_skills))
        current_context = CurrentMcpContext(session_id)
        monkeypatch.setattr(extension_module, "get_context", lambda: current_context)
        _write_skill(docroot, name="workflow-check")

        await extension.on_request_started(session)

    assert len(current_context.notifications) == 1
    assert current_context.notifications[0].method == SKILLS_LIST_CHANGED_METHOD


@pytest.mark.anyio
async def test_skills_list_change_waits_for_the_owning_sessions_request_context(
    tmp_path, monkeypatch, applications
) -> None:
    """A contextless configuration callback remains pending until its own client requests again."""
    from fastmcp import Client
    from mcp.client.extension import ClientExtension

    import mcp_guide.mcp_skills_extension as extension_module
    from mcp_guide.cli import ServerConfig
    from mcp_guide.mcp_skills_extension import (
        MCP_SKILLS_EXTENSION_ID,
        SKILLS_LIST_CHANGED_METHOD,
        GuideSkillsExtension,
        SkillsListParams,
        SkillsListRequest,
        SkillsListResult,
    )
    from mcp_guide.server import create_application

    class SkillsClientExtension(ClientExtension):
        identifier = MCP_SKILLS_EXTENSION_ID

    class CurrentMcpContext:
        def __init__(self, session_id: str) -> None:
            self.session_id = session_id
            self.notifications = []

        def client_supports_extension(self, identifier: str) -> bool:
            return identifier == MCP_SKILLS_EXTENSION_ID

        async def send_notification(self, notification) -> None:
            self.notifications.append(notification)

    monkeypatch.setenv("MCP_GUIDE_DISABLE_SERVER_TASKS", "1")
    config_dir = tmp_path / "config"
    docroot = tmp_path / "docs"
    project_root = tmp_path / "project"
    config_dir.mkdir()
    project_root.mkdir()
    (config_dir / "config.yaml").write_text("feature_flags:\n  mcp-skills: true\n", encoding="utf-8")
    _write_skill(docroot)
    application = create_application(ServerConfig(configdir=str(config_dir), docroot=str(docroot)))
    applications.append(application)

    async with Client(
        application.server,
        mode="2026-07-28",
        extensions=[SkillsClientExtension()],
    ) as client:
        bound = await client.call_tool("set_project", {"args": {"path": str(project_root)}})
        assert bound.structured_content is not None
        session_id = bound.structured_content["session_id"]
        await client.session.send_request(
            SkillsListRequest(params=SkillsListParams(session_id=session_id)),
            SkillsListResult,
        )

        extension = cast(GuideSkillsExtension, application.server._extensions[MCP_SKILLS_EXTENSION_ID])
        session = next(iter(extension._effective_skills))
        before = extension._effective_skills[session]
        _write_skill(docroot, name="workflow-check")
        update = cast(Any, object())

        monkeypatch.setattr(extension_module, "get_context", lambda: (_ for _ in ()).throw(RuntimeError()))
        await extension.on_configuration_changed(session, update)
        assert extension._effective_skills[session] == before

        other_context = CurrentMcpContext("another-session")
        monkeypatch.setattr(extension_module, "get_context", lambda: other_context)
        await extension.on_request_started(session)
        assert not other_context.notifications
        assert extension._effective_skills[session] == before

        owning_context = CurrentMcpContext(session_id)
        monkeypatch.setattr(extension_module, "get_context", lambda: owning_context)
        await extension.on_request_started(session)

    assert len(owning_context.notifications) == 1
    assert owning_context.notifications[0].method == SKILLS_LIST_CHANGED_METHOD
    assert extension._effective_skills[session] != before


@pytest.mark.anyio
async def test_skills_list_subscription_survives_project_switch(tmp_path, monkeypatch, applications) -> None:
    """A replacement Session keeps the negotiated skills-list subscription."""
    from fastmcp import Client
    from mcp.client.extension import ClientExtension

    import mcp_guide.mcp_skills_extension as extension_module
    from mcp_guide.cli import ServerConfig
    from mcp_guide.mcp_skills_extension import (
        MCP_SKILLS_EXTENSION_ID,
        SKILLS_LIST_CHANGED_METHOD,
        GuideSkillsExtension,
        SkillsListParams,
        SkillsListRequest,
        SkillsListResult,
    )
    from mcp_guide.server import create_application

    class SkillsClientExtension(ClientExtension):
        identifier = MCP_SKILLS_EXTENSION_ID

    class CurrentMcpContext:
        def __init__(self, session_id: str) -> None:
            self.session_id = session_id
            self.notifications = []

        def client_supports_extension(self, identifier: str) -> bool:
            return identifier == MCP_SKILLS_EXTENSION_ID

        async def send_notification(self, notification) -> None:
            self.notifications.append(notification)

    monkeypatch.setenv("MCP_GUIDE_DISABLE_SERVER_TASKS", "1")
    config_dir = tmp_path / "config"
    docroot = tmp_path / "docs"
    first_root = tmp_path / "first"
    second_root = tmp_path / "second"
    config_dir.mkdir()
    first_root.mkdir()
    second_root.mkdir()
    (config_dir / "config.yaml").write_text("feature_flags:\n  mcp-skills: true\n", encoding="utf-8")
    _write_skill(docroot)
    application = create_application(ServerConfig(configdir=str(config_dir), docroot=str(docroot)))
    applications.append(application)

    async with Client(
        application.server,
        mode="2026-07-28",
        extensions=[SkillsClientExtension()],
    ) as client:
        bound = await client.call_tool("set_project", {"args": {"path": str(first_root)}})
        assert bound.structured_content is not None
        session_id = bound.structured_content["session_id"]
        await client.session.send_request(
            SkillsListRequest(params=SkillsListParams(session_id=session_id)),
            SkillsListResult,
        )

        extension = cast(GuideSkillsExtension, application.server._extensions[MCP_SKILLS_EXTENSION_ID])
        original = next(iter(extension._effective_skills))
        current_context = CurrentMcpContext(session_id)
        monkeypatch.setattr(extension_module, "get_context", lambda: current_context)
        _write_skill(docroot, name="workflow-check")

        replacement = await original.switch_project(path=second_root)

        assert original not in extension._effective_skills
        assert replacement in extension._effective_skills
        assert extension in replacement._listeners
        assert len(current_context.notifications) == 1
        assert current_context.notifications[0].method == SKILLS_LIST_CHANGED_METHOD


@pytest.mark.anyio
async def test_skills_list_rejects_a_client_that_did_not_negotiate(tmp_path, monkeypatch, applications) -> None:
    """The extension method is not an alternative route to the ordinary catalogue."""
    from fastmcp import Client
    from mcp import MCPError

    from mcp_guide.cli import ServerConfig
    from mcp_guide.mcp_skills_extension import SkillsListParams, SkillsListRequest, SkillsListResult
    from mcp_guide.server import create_application

    monkeypatch.setenv("MCP_GUIDE_DISABLE_SERVER_TASKS", "1")
    config_dir = tmp_path / "config"
    docroot = tmp_path / "docs"
    project_root = tmp_path / "project"
    config_dir.mkdir()
    project_root.mkdir()
    (config_dir / "config.yaml").write_text("feature_flags:\n  mcp-skills: true\n", encoding="utf-8")
    _write_skill(docroot)
    application = create_application(ServerConfig(configdir=str(config_dir), docroot=str(docroot)))
    applications.append(application)

    async with Client(application.server, mode="2026-07-28") as client:
        bound = await client.call_tool("set_project", {"args": {"path": str(project_root)}})
        assert bound.structured_content is not None
        with pytest.raises(MCPError, match=r"requires the io\.uniquode/mcp-guide-skills extension"):
            await client.session.send_request(
                SkillsListRequest(params=SkillsListParams(session_id=bound.structured_content["session_id"])),
                SkillsListResult,
            )
