"""Tests for transport abstraction layer."""

from mcp_guide.transports.base import Transport


def test_transport_protocol_has_required_methods():
    """Test that Transport protocol defines required methods."""
    # Check protocol has required methods
    assert hasattr(Transport, "start")
    assert hasattr(Transport, "stop")
    assert hasattr(Transport, "send")
    assert hasattr(Transport, "receive")


def test_transport_protocol_is_runtime_checkable():
    """Test that Transport protocol can be checked at runtime."""
    # Transport should be runtime_checkable
    assert hasattr(Transport, "__protocol_attrs__") or hasattr(Transport, "_is_protocol")
