"""Tests for server creation."""

from mcp.server import FastMCP


def test_create_server_returns_fastmcp() -> None:
    """Test that create_server returns a FastMCP instance."""
    from mcp_guide.server import create_server

    server = create_server()
    assert isinstance(server, FastMCP)


def test_server_has_correct_name() -> None:
    """Test that server has correct name."""
    from mcp_guide.server import create_server

    server = create_server()
    assert server.name == "mcp-guide"


def test_server_has_instructions() -> None:
    """Test that server has instructions."""
    from mcp_guide.server import create_server

    server = create_server()
    assert server.instructions is not None
    assert "project documentation" in server.instructions.lower()
