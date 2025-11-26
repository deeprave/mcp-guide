"""Tests for main entry point."""

import inspect
from enum import Enum

import pytest


def test_transport_mode_enum_exists() -> None:
    """Test that TransportMode enum can be imported."""
    from mcp_guide.main import TransportMode

    assert issubclass(TransportMode, Enum)


def test_transport_mode_has_stdio() -> None:
    """Test that TransportMode has STDIO value."""
    from mcp_guide.main import TransportMode

    assert hasattr(TransportMode, "STDIO")
    assert TransportMode.STDIO.value == "stdio"


@pytest.mark.asyncio
async def test_async_main_exists() -> None:
    """Test that async_main function exists and is callable."""
    from mcp_guide.main import async_main

    assert callable(async_main)


@pytest.mark.asyncio
async def test_async_main_has_no_parameters() -> None:
    """Test that async_main has no required parameters."""
    from mcp_guide.main import async_main

    sig = inspect.signature(async_main)
    assert len(sig.parameters) == 0


def test_main_exists() -> None:
    """Test that main function exists and is callable."""
    from mcp_guide.main import main

    assert callable(main)


def test_main_has_no_required_parameters() -> None:
    """Test that main function has no required parameters."""
    from mcp_guide.main import main

    sig = inspect.signature(main)
    required_params = [
        p for p in sig.parameters.values() if p.default == inspect.Parameter.empty
    ]

    assert len(required_params) == 0
