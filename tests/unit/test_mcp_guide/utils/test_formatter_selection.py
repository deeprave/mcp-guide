"""Tests for formatter selection with ContentFormat enum."""

from mcp_guide.utils.content_formatter_base import BaseFormatter
from mcp_guide.utils.content_formatter_mime import MimeFormatter
from mcp_guide.utils.content_formatter_plain import PlainFormatter
from mcp_guide.utils.formatter_selection import ContentFormat, get_formatter_from_flag


class TestContentFormat:
    """Test ContentFormat enum."""

    def test_enum_values(self):
        """Test ContentFormat enum has correct values."""
        assert ContentFormat.NONE.value == "none"
        assert ContentFormat.PLAIN.value == "plain"
        assert ContentFormat.MIME.value == "mime"


class TestFormatterSelection:
    """Test formatter selection with enum."""

    def test_get_formatter_from_flag_none(self):
        """Test get_formatter_from_flag returns BaseFormatter for NONE."""
        formatter = get_formatter_from_flag(ContentFormat.NONE)
        assert isinstance(formatter, BaseFormatter)

    def test_get_formatter_from_flag_plain(self):
        """Test get_formatter_from_flag returns PlainFormatter for PLAIN."""
        formatter = get_formatter_from_flag(ContentFormat.PLAIN)
        assert isinstance(formatter, PlainFormatter)

    def test_get_formatter_from_flag_mime(self):
        """Test get_formatter_from_flag returns MimeFormatter for MIME."""
        formatter = get_formatter_from_flag(ContentFormat.MIME)
        assert isinstance(formatter, MimeFormatter)
