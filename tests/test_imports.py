"""Test basic package imports."""

from packaging.version import Version


def test_mcp_core_import() -> None:
    """Test that mcp_guide.core package can be imported."""
    import mcp_guide.core

    # Verify __version__ exists and is a valid version string
    Version(mcp_guide.core.__version__)


def test_mcp_guide_import() -> None:
    """Test that mcp_guide package can be imported."""
    import mcp_guide

    # Verify __version__ exists and is a valid version string
    Version(mcp_guide.__version__)
