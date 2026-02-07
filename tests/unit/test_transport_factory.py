"""Tests for transport factory."""

from unittest.mock import Mock, patch

import pytest

from mcp_guide.transports import MissingDependencyError, create_transport
from mcp_guide.transports.http import HttpTransport
from mcp_guide.transports.stdio import StdioTransport


def test_create_stdio_transport():
    """Test creating stdio transport."""
    mock_server = Mock()
    transport = create_transport("stdio", None, None, mock_server)
    assert isinstance(transport, StdioTransport)
    assert transport.mcp_server is mock_server


def test_create_http_transport():
    """Test creating HTTP transport with uvicorn available."""
    mock_server = Mock()
    transport = create_transport("http", "localhost", 8080, mock_server)
    assert isinstance(transport, HttpTransport)
    assert transport.scheme == "http"
    assert transport.host == "localhost"
    assert transport.port == 8080
    assert transport.mcp_server is mock_server


def test_create_https_transport():
    """Test creating HTTPS transport with uvicorn available."""
    mock_server = Mock()
    transport = create_transport("https", "0.0.0.0", 443, mock_server)
    assert isinstance(transport, HttpTransport)
    assert transport.scheme == "https"
    assert transport.host == "0.0.0.0"
    assert transport.port == 443
    assert transport.mcp_server is mock_server


def test_create_transport_without_mcp_server():
    """Test creating transport without mcp_server raises ValueError."""
    with pytest.raises(ValueError, match="mcp_server required"):
        create_transport("stdio", None, None, None)


def test_create_http_transport_without_uvicorn():
    """Test creating HTTP transport without uvicorn raises MissingDependencyError."""
    import builtins

    mock_server = Mock()
    original_import = builtins.__import__

    def mock_import(name, *args, **kwargs):
        if name == "uvicorn":
            raise ImportError("No module named 'uvicorn'")
        return original_import(name, *args, **kwargs)

    with patch("builtins.__import__", side_effect=mock_import):
        with pytest.raises(MissingDependencyError, match="uvicorn"):
            create_transport("http", "localhost", 8080, mock_server)


def test_create_invalid_transport_mode():
    """Test creating transport with invalid mode raises ValueError."""
    mock_server = Mock()
    with pytest.raises(ValueError, match="Unknown transport mode"):
        create_transport("ftp", None, None, mock_server)
