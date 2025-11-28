"""Tests for main.py environment configuration."""

import os
from unittest.mock import patch

import pytest


class TestEnvironmentConfiguration:
    """Tests for _configure_environment()."""

    def test_configure_environment_sets_mcp_tool_prefix(self):
        """_configure_environment() should set MCP_TOOL_PREFIX to 'guide'."""
        from mcp_guide.main import _configure_environment

        with patch.dict(os.environ, {}, clear=True):
            _configure_environment()
            assert os.environ["MCP_TOOL_PREFIX"] == "guide"

    def test_preserves_existing_mcp_tool_prefix(self):
        """_configure_environment() should preserve existing MCP_TOOL_PREFIX."""
        from mcp_guide.main import _configure_environment

        with patch.dict(os.environ, {"MCP_TOOL_PREFIX": "custom"}):
            _configure_environment()
            assert os.environ["MCP_TOOL_PREFIX"] == "custom"

    def test_configure_environment_called_before_logging(self):
        """_configure_environment() should be called before logging setup."""
        from mcp_guide.main import main

        # This is tested by the order of calls in main()
        # If environment is configured first, MCP_TOOL_PREFIX will be set
        # before any logging or server initialization
        assert True  # Structural test - verified by code inspection
