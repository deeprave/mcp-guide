"""Tests for HTTP transport optional dependencies configuration."""

import sys
import tomllib
from pathlib import Path
from unittest.mock import patch

import pytest


def test_http_extra_defined_in_pyproject():
    """Test that [http] extra is defined in pyproject.toml."""
    pyproject_path = Path(__file__).parent.parent.parent / "pyproject.toml"

    with open(pyproject_path, "rb") as f:
        config = tomllib.load(f)

    # Check that optional-dependencies section exists
    assert "project" in config
    assert "optional-dependencies" in config["project"]

    # Check that http extra is defined
    assert "http" in config["project"]["optional-dependencies"]

    # Check that uvicorn is in the http extra
    http_deps = config["project"]["optional-dependencies"]["http"]
    assert any("uvicorn" in dep for dep in http_deps)


def test_http_mode_requires_uvicorn():
    """Test that HTTP mode fails with clear error when uvicorn is not installed."""
    import builtins

    from mcp_guide.transports import MissingDependencyError, validate_transport_dependencies

    # Mock uvicorn as not available by patching __import__
    original_import = builtins.__import__

    def mock_import(name, *args, **kwargs):
        if name == "uvicorn":
            raise ImportError("No module named 'uvicorn'")
        return original_import(name, *args, **kwargs)

    with patch("builtins.__import__", side_effect=mock_import):
        with pytest.raises(MissingDependencyError, match="uvicorn"):
            validate_transport_dependencies("http")


def test_stdio_mode_does_not_require_uvicorn():
    """Test that stdio mode works without uvicorn."""
    from mcp_guide.transports import validate_transport_dependencies

    # Mock uvicorn as not available
    with patch.dict(sys.modules, {"uvicorn": None}):
        # Should not raise
        validate_transport_dependencies("stdio")
