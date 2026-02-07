"""Tests for server transport integration."""

from mcp_guide.cli import ServerConfig, parse_args


def test_server_config_has_transport_fields():
    """Test that ServerConfig has transport-related fields."""
    config = ServerConfig()
    assert hasattr(config, "transport_mode")
    assert hasattr(config, "transport_host")
    assert hasattr(config, "transport_port")


def test_server_config_defaults_to_stdio():
    """Test that ServerConfig defaults to stdio transport."""
    config = ServerConfig()
    assert config.transport_mode == "stdio"
    assert config.transport_host is None
    assert config.transport_port is None


def test_parse_args_with_stdio_mode(monkeypatch):
    """Test parsing args with stdio mode."""
    monkeypatch.setattr("sys.argv", ["mcp-guide", "stdio"])
    config = parse_args()
    assert config.transport_mode == "stdio"
    assert config.transport_host is None
    assert config.transport_port is None


def test_parse_args_with_http_mode(monkeypatch):
    """Test parsing args with http mode."""
    monkeypatch.setattr("sys.argv", ["mcp-guide", "http"])
    config = parse_args()
    assert config.transport_mode == "http"
    assert config.transport_host == "localhost"
    assert config.transport_port == 8080


def test_parse_args_with_https_url(monkeypatch):
    """Test parsing args with https URL."""
    monkeypatch.setattr("sys.argv", ["mcp-guide", "https://0.0.0.0:8443"])
    config = parse_args()
    assert config.transport_mode == "https"
    assert config.transport_host == "0.0.0.0"
    assert config.transport_port == 8443
