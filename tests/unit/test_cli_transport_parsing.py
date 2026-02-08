"""Tests for CLI transport mode parsing."""

import pytest

from mcp_guide.cli import parse_transport_mode


def test_parse_stdio_mode():
    """Test parsing stdio mode."""
    mode, host, port, path = parse_transport_mode("stdio")
    assert mode == "stdio"
    assert host is None
    assert port is None
    assert path is None


def test_parse_http_shorthand():
    """Test parsing http shorthand."""
    mode, host, port, path = parse_transport_mode("http")
    assert mode == "http"
    assert host == "localhost"
    assert port == 8080


def test_parse_https_shorthand():
    """Test parsing https shorthand."""
    mode, host, port, path = parse_transport_mode("https")
    assert mode == "https"
    assert host == "0.0.0.0"
    assert port == 443


def test_parse_http_with_host_and_port():
    """Test parsing http://host:port."""
    mode, host, port, path = parse_transport_mode("http://localhost:8080")
    assert mode == "http"
    assert host == "localhost"
    assert port == 8080


def test_parse_https_with_host_and_port():
    """Test parsing https://host:port."""
    mode, host, port, path = parse_transport_mode("https://example.com:8443")
    assert mode == "https"
    assert host == "example.com"
    assert port == 8443


def test_parse_http_with_port_only():
    """Test parsing http://:port defaults to localhost."""
    mode, host, port, path = parse_transport_mode("http://:8080")
    assert mode == "http"
    assert host == "localhost"
    assert port == 8080


def test_parse_https_with_port_only():
    """Test parsing https://:port defaults to 0.0.0.0."""
    mode, host, port, path = parse_transport_mode("https://:8443")
    assert mode == "https"
    assert host == "0.0.0.0"
    assert port == 8443


def test_parse_http_with_host_only():
    """Test parsing http://host defaults to port 8080."""
    mode, host, port, path = parse_transport_mode("http://example.com")
    assert mode == "http"
    assert host == "example.com"
    assert port == 8080


def test_parse_https_with_host_only():
    """Test parsing https://host defaults to port 443."""
    mode, host, port, path = parse_transport_mode("https://example.com")
    assert mode == "https"
    assert host == "example.com"
    assert port == 443


def test_parse_invalid_mode():
    """Test parsing invalid mode raises error."""
    with pytest.raises(ValueError, match="Invalid transport mode"):
        parse_transport_mode("ftp://example.com")


def test_parse_invalid_port():
    """Test parsing invalid port raises error."""
    with pytest.raises(ValueError, match="Invalid port|Port could not be cast"):
        parse_transport_mode("http://localhost:abc")


def test_parse_http_with_path():
    """Test parsing HTTP URL with path prefix."""
    mode, host, port, path = parse_transport_mode("http://localhost:8080/v1")
    assert mode == "http"
    assert host == "localhost"
    assert port == 8080
    assert path == "v1"


def test_parse_https_with_path():
    """Test parsing HTTPS URL with path prefix."""
    mode, host, port, path = parse_transport_mode("https://example.com:8443/api/v2")
    assert mode == "https"
    assert host == "example.com"
    assert port == 8443
    assert path == "api/v2"


def test_parse_http_with_trailing_slash():
    """Test parsing HTTP URL with trailing slash normalizes path."""
    mode, host, port, path = parse_transport_mode("http://localhost:8080/v1/")
    assert mode == "http"
    assert host == "localhost"
    assert port == 8080
    assert path == "v1"  # Trailing slash stripped
