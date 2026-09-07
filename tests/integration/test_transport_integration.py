"""Transport settings flow through the complete CLI parser."""

import pytest

from mcp_guide.cli import parse_args


@pytest.mark.parametrize(
    "argument,expected",
    [
        (None, ("stdio", None, None, None)),
        ("stdio", ("stdio", None, None, None)),
        ("http", ("http", "localhost", 8080, None)),
        ("https", ("https", "0.0.0.0", 443, None)),
        ("http://localhost:8080", ("http", "localhost", 8080, None)),
        ("https://example.com:8443", ("https", "example.com", 8443, None)),
        ("https://0.0.0.0:8443", ("https", "0.0.0.0", 8443, None)),
        ("http://:8080", ("http", "localhost", 8080, None)),
        ("https://:8443", ("https", "0.0.0.0", 8443, None)),
        ("http://example.com", ("http", "example.com", 8080, None)),
        ("https://example.com", ("https", "example.com", 443, None)),
        ("http://localhost:8080/v1", ("http", "localhost", 8080, "v1")),
        ("https://example.com:8443/api/v2", ("https", "example.com", 8443, "api/v2")),
        ("http://localhost:8080/v1/", ("http", "localhost", 8080, "v1")),
    ],
)
def test_transport_settings_from_cli(monkeypatch, argument, expected):
    monkeypatch.setattr("sys.argv", ["mcp-guide"] + ([argument] if argument is not None else []))
    config = parse_args()
    assert (config.transport_mode, config.transport_host, config.transport_port, config.transport_path) == expected
    assert config.cli_error is None
    assert config.should_exit is False


def test_invalid_transport_mode_is_reported_without_exiting(monkeypatch):
    monkeypatch.setattr("sys.argv", ["mcp-guide", "ftp://example.com"])
    config = parse_args()
    assert config.cli_error is not None
    assert "Invalid transport mode" in str(config.cli_error)
    assert config.should_exit is False
