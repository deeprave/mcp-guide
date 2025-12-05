"""Shared fixtures for integration tests."""

from pathlib import Path

import pytest


@pytest.fixture
def anyio_backend():
    """Use asyncio for async tests."""
    return "asyncio"


@pytest.fixture(scope="session")
def mcp_server():
    """Create single MCP server for entire test session."""
    from mcp_guide.server import _ToolsProxy, create_server

    # Reset proxy to ensure tools register properly
    _ToolsProxy._instance = None

    return create_server()
