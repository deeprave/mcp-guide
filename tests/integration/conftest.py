"""Integration test fixtures.

## MCP Server Factory Fixture

Tools are registered on server creation via deferred registration and require
fresh registration state between modules.

The mcp_server_factory fixture resets registration state and creates a fresh
server per module.
"""

from importlib import import_module
from pathlib import Path

import pytest

from mcp_guide.server import create_server


@pytest.fixture(scope="module")
def mcp_server_factory():
    """Factory to create MCP server with specified tool modules reloaded.

    Usage:
        @pytest.fixture(scope="module")
        def mcp_server(mcp_server_factory):
            return mcp_server_factory(["tool_category"])
    """
    created_servers = []

    def _create_server(tool_modules: list[str]):
        # Clear tool registration state before bootstrap so each fixture has
        # a deterministic, isolated set of registered tools.
        from mcp_guide.core.tool_decorator import clear_tool_registry

        clear_tool_registry()

        # Import (or reload) tool modules to repopulate decorator metadata after
        # the registry clear. Modules remain in memory once imported, so a
        # direct import is insufficient on subsequent invocations.
        import importlib
        import sys

        for module_name in tool_modules:
            full_name = f"mcp_guide.tools.{module_name}"
            if full_name in sys.modules:
                importlib.reload(sys.modules[full_name])
            else:
                import_module(full_name)

        # Create new server instance
        from mcp_guide.cli import ServerConfig

        config = ServerConfig()
        server = create_server(config)

        created_servers.append(server)
        return server

    yield _create_server

    # Clean up after module
    from mcp_guide.core.tool_decorator import clear_tool_registry

    clear_tool_registry()


@pytest.fixture
def installer_config(tmp_path: Path) -> Path:
    """Create installer config to skip first-run installation.

    Returns:
        Path to config directory
    """
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    (config_dir / "installer.yaml").write_text("docroot: /tmp/test\n")
    return config_dir
