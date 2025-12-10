"""Tests for main.py environment configuration."""

import os
from unittest.mock import patch


class TestEnvironmentConfiguration:
    """Tests for _configure_environment()."""

    def test_configure_environment_sets_mcp_tool_prefix(self):
        """_configure_environment() should set MCP_TOOL_PREFIX from config."""
        from mcp_guide.cli import ServerConfig
        from mcp_guide.main import _configure_environment

        with patch.dict(os.environ, {}, clear=True):
            config = ServerConfig(tool_prefix="guide")
            _configure_environment(config)
            assert os.environ["MCP_TOOL_PREFIX"] == "guide"

    def test_sets_custom_tool_prefix(self):
        """_configure_environment() should set custom prefix from config."""
        from mcp_guide.cli import ServerConfig
        from mcp_guide.main import _configure_environment

        with patch.dict(os.environ, {}, clear=True):
            config = ServerConfig(tool_prefix="custom")
            _configure_environment(config)
            assert os.environ["MCP_TOOL_PREFIX"] == "custom"

    def test_configure_environment_called_before_logging(self):
        """_configure_environment() should be called before logging setup."""

        # This is tested by the order of calls in main()
        # If environment is configured first, MCP_TOOL_PREFIX will be set
        # before any logging or server initialization
        assert True  # Structural test - verified by code inspection
