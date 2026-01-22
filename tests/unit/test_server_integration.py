"""Tests for server integration."""

from unittest.mock import patch


class TestServerCLIOptions:
    """Tests for server CLI options."""

    def test_parse_docroot_option(self) -> None:
        """Test that server accepts -d/--docroot option."""
        # Arrange
        from mcp_guide.cli import parse_args

        # Act
        with patch("sys.argv", ["mcp-guide", "--docroot", "/custom/path"]):
            config = parse_args()

        # Assert
        assert config.docroot == "/custom/path"

    def test_parse_configdir_option(self) -> None:
        """Test that server accepts -c/--configdir option."""
        # Arrange
        from mcp_guide.cli import parse_args

        # Act
        with patch("sys.argv", ["mcp-guide", "--configdir", "/custom/config"]):
            config = parse_args()

        # Assert
        assert config.configdir == "/custom/config"
