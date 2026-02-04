"""Integration test fixtures.

## MCP Server Factory Fixture

Tools are registered with the MCP server via decorators that execute ON MODULE IMPORT.
When pytest runs multiple test modules, Python's import system caches modules and does
NOT re-import them. This causes tool contamination between test modules.

The mcp_server_factory fixture solves this by providing a factory function that:
1. Resets the ToolsProxy singleton
2. Creates a fresh server instance
3. Reloads specified tool modules
4. Cleans up after tests complete

See README.md in this directory for usage examples and detailed explanation.
"""

import sys
from importlib import reload
from pathlib import Path

import pytest

from mcp_guide.server import _ToolsProxy, create_server


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
        # Reset proxy to clear any previously registered tools
        _ToolsProxy._instance = None

        # Clear tool registry
        from mcp_guide.core.tool_decorator import _TOOL_REGISTRY

        _TOOL_REGISTRY.clear()

        # Create new server instance
        from mcp_guide.cli import ServerConfig

        config = ServerConfig()
        server = create_server(config)

        # Reload tool modules to populate registry
        for module_name in tool_modules:
            full_module_path = f"mcp_guide.tools.{module_name}"
            if full_module_path in sys.modules:
                reload(sys.modules[full_module_path])

        # Register tools with MCP
        from mcp_guide.core.tool_decorator import register_tools

        register_tools(server)

        created_servers.append(server)
        return server

    yield _create_server

    # Clean up after module
    _ToolsProxy._instance = None
    from mcp_guide.core.tool_decorator import _TOOL_REGISTRY

    _TOOL_REGISTRY.clear()


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
