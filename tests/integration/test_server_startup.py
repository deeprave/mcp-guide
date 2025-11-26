"""Integration tests for server startup."""


def test_main_entry_point_exists():
    """Test that main entry point exists and is callable."""
    from mcp_guide.main import main

    assert callable(main), "Main entry point should be callable"
    assert main.__doc__ is not None, "Main entry point should have docstring"
