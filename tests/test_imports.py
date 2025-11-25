"""Test basic package imports."""


def test_mcp_core_import() -> None:
    """Test that mcp_core package can be imported."""
    import mcp_core

    assert mcp_core.__version__ == "0.5.0"


def test_mcp_guide_import() -> None:
    """Test that mcp_guide package can be imported."""
    import mcp_guide

    assert mcp_guide.__version__ == "0.5.0"
