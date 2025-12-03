"""Tests for formatter selection."""

import pytest


def test_module_imports():
    """Test that module can be imported."""
    from mcp_guide.utils import formatter_selection

    assert formatter_selection is not None


def test_default_formatter_is_plain():
    """Test that default formatter is PlainFormatter."""
    from mcp_guide.utils.content_formatter_plain import PlainFormatter
    from mcp_guide.utils.formatter_selection import get_formatter

    formatter = get_formatter()
    assert isinstance(formatter, PlainFormatter)


def test_set_formatter_to_mime():
    """Test switching to MimeFormatter."""
    from mcp_guide.utils.content_formatter_mime import MimeFormatter
    from mcp_guide.utils.formatter_selection import get_formatter, set_formatter

    set_formatter("mime")
    formatter = get_formatter()
    assert isinstance(formatter, MimeFormatter)


def test_set_formatter_to_plain():
    """Test switching to PlainFormatter."""
    from mcp_guide.utils.content_formatter_plain import PlainFormatter
    from mcp_guide.utils.formatter_selection import get_formatter, set_formatter

    set_formatter("plain")
    formatter = get_formatter()
    assert isinstance(formatter, PlainFormatter)


def test_invalid_formatter_type_raises_error():
    """Test that invalid formatter type raises ValueError."""
    from mcp_guide.utils.formatter_selection import set_formatter

    with pytest.raises(ValueError, match="Invalid formatter type"):
        set_formatter("invalid")
