"""Tests for transport factory."""

import sys
from unittest.mock import patch

import pytest

from mcp_guide.transports import create_transport
from mcp_guide.transports.stdio import StdioTransport


def test_create_stdio_transport():
    """Test creating stdio transport."""
    transport = create_transport("stdio", None, None, None)
    assert isinstance(transport, StdioTransport)


def test_create_http_transport_without_uvicorn():
    """Test creating HTTP transport without uvicorn raises error."""
    with patch.dict(sys.modules, {"uvicorn": None}):
        with pytest.raises(SystemExit):
            create_transport("http", "localhost", 8080, None)


def test_create_https_transport_without_uvicorn():
    """Test creating HTTPS transport without uvicorn raises error."""
    with patch.dict(sys.modules, {"uvicorn": None}):
        with pytest.raises(SystemExit):
            create_transport("https", "0.0.0.0", 443, None)
