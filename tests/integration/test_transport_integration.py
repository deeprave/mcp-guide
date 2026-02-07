"""Integration tests for transport modes."""

import pytest

from mcp_guide.cli import parse_args


@pytest.mark.parametrize(
    "argv,expected_mode,expected_host,expected_port",
    [
        (["mcp-guide", "stdio"], "stdio", None, None),
        (["mcp-guide", "http://localhost:8080"], "http", "localhost", 8080),
        (["mcp-guide", "https://:8443"], "https", "0.0.0.0", 8443),
        (["mcp-guide"], "stdio", None, None),  # default
    ],
)
def test_transport_mode_integration(monkeypatch, argv, expected_mode, expected_host, expected_port):
    """Test transport mode end-to-end integration."""
    monkeypatch.setattr("sys.argv", argv)
    config = parse_args()

    assert config.transport_mode == expected_mode
    assert config.transport_host == expected_host
    assert config.transport_port == expected_port
    assert not config.cli_error
    assert not config.should_exit


def test_invalid_transport_mode(monkeypatch):
    """Test invalid transport mode handling."""
    monkeypatch.setattr("sys.argv", ["mcp-guide", "ftp://example.com"])
    config = parse_args()

    assert config.cli_error is not None
    assert "Invalid transport mode" in str(config.cli_error)
