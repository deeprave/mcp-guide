"""Tests for GuideMCP class."""

from mcp_guide.guide import GuideMCP


def test_guide_mcp_initialization():
    """Test GuideMCP initializes with agent_info attribute."""
    mcp = GuideMCP(name="test-server")

    assert mcp.name == "test-server"
    assert hasattr(mcp, "agent_info")
    assert mcp.agent_info is None


def test_guide_mcp_extends_fastmcp():
    """Test GuideMCP is a FastMCP instance."""
    from mcp.server import FastMCP

    mcp = GuideMCP(name="test-server")
    assert isinstance(mcp, FastMCP)
