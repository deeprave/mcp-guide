"""Tests for server creation."""

from unittest.mock import patch

import pytest
from fastmcp import Client


def test_server_has_instructions() -> None:
    """Test that server has instructions."""
    from mcp_guide.cli import ServerConfig
    from mcp_guide.server import create_server

    config = ServerConfig()
    server = create_server(config)
    assert isinstance(server.instructions, str)
    assert server.name == "guide"
    assert server.instructions.strip()
    assert "project documentation" in server.instructions.lower()


def test_mcp_skills_capability_is_snapshotted_from_global_configuration(tmp_path) -> None:
    """The experimental capability is fixed when the server is constructed."""
    from mcp_guide.cli import ServerConfig
    from mcp_guide.server import create_application

    config_file = tmp_path / "config.yaml"
    config_file.write_text("feature_flags:\n  mcp-skills: true\n")

    application = create_application(ServerConfig(configdir=str(tmp_path)))
    capabilities = application.server._mcp_server.get_capabilities()

    assert capabilities.experimental == {"skills": {}}
    assert capabilities.model_dump(mode="json")["experimental"] == {"skills": {}}

    config_file.write_text("feature_flags:\n  mcp-skills: false\n")
    assert application.server._mcp_server.get_capabilities().experimental == {"skills": {}}


def test_mcp_skills_capability_is_absent_without_the_global_flag(tmp_path) -> None:
    """Skill resources remain available without advertising the experiment."""
    from mcp_guide.cli import ServerConfig
    from mcp_guide.server import create_application

    (tmp_path / "config.yaml").write_text("feature_flags: {}\n")

    application = create_application(ServerConfig(configdir=str(tmp_path)))

    assert application.server._mcp_server.get_capabilities().experimental is None


def test_runtime_factory_injects_one_config_manager_into_each_session(tmp_path) -> None:
    """Production Sessions receive the runtime-owned configuration service."""
    from mcp_guide.cli import ServerConfig
    from mcp_guide.runtime import OwnerKey
    from mcp_guide.server import create_application

    application = create_application(ServerConfig(configdir=str(tmp_path)))

    first = application.runtime.resolve_session(OwnerKey("first"))
    second = application.runtime.resolve_session(OwnerKey("second"))

    assert first._config() is application.runtime._config_manager
    assert second._config() is application.runtime._config_manager


@pytest.mark.anyio
async def test_application_construction_defers_guide_startup_to_runtime_lifecycle() -> None:
    """Building the FastMCP surface must not start Guide process services."""
    from mcp_guide.cli import ServerConfig
    from mcp_guide.server import create_application

    with (
        patch("mcp_guide.server._configure_logging_after_fastmcp") as configure_logging,
        patch("mcp_guide.server._initialize_runtime_tasks") as initialize_tasks,
    ):
        application = create_application(ServerConfig())

        configure_logging.assert_not_called()
        initialize_tasks.assert_not_called()

        await application.runtime.start()

    configure_logging.assert_called_once()
    initialize_tasks.assert_called_once()
    await application.runtime.stop()


@pytest.mark.anyio
@pytest.mark.parametrize("mode", ["legacy", "2026-07-28"])
async def test_fastmcp_surface_negotiates_retained_and_modern_client_eras(mode: str) -> None:
    """The stdio runner serves FastMCP's negotiated client eras from one surface."""
    from mcp_guide.cli import ServerConfig
    from mcp_guide.server import create_application

    application = create_application(ServerConfig())
    async with Client(application.server, mode=mode) as client:
        tools = await client.list_tools()

    tool_names = {tool.name for tool in tools}
    assert "set_project" in tool_names
    assert "switch_project" in tool_names
    assert "list_skills" in tool_names
