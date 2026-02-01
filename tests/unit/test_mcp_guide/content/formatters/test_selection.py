"""Tests for formatter selection with ContentFormat enum."""

from mcp_guide.content.formatters.base import BaseFormatter
from mcp_guide.content.formatters.mime import MimeFormatter
from mcp_guide.content.formatters.plain import PlainFormatter
from mcp_guide.content.formatters.selection import (
    ContentFormat,
    TemplateStyling,
    get_formatter_from_flag,
    get_styling_variables,
)


class TestContentFormat:
    """Test ContentFormat enum."""

    def test_enum_values(self):
        """Test ContentFormat enum has correct values."""
        assert ContentFormat.NONE.value == "none"
        assert ContentFormat.PLAIN.value == "plain"
        assert ContentFormat.MIME.value == "mime"

    def test_from_flag_value_valid_strings(self):
        """Test from_flag_value with valid string values."""
        assert ContentFormat.from_flag_value("none") == ContentFormat.NONE
        assert ContentFormat.from_flag_value("plain") == ContentFormat.PLAIN
        assert ContentFormat.from_flag_value("mime") == ContentFormat.MIME

    def test_from_flag_value_none(self):
        """Test from_flag_value with None defaults to NONE."""
        assert ContentFormat.from_flag_value(None) == ContentFormat.NONE

    def test_from_flag_value_invalid(self):
        """Test from_flag_value with invalid values defaults to NONE."""
        assert ContentFormat.from_flag_value("invalid") == ContentFormat.NONE
        assert ContentFormat.from_flag_value("") == ContentFormat.NONE
        assert ContentFormat.from_flag_value(123) == ContentFormat.NONE


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


class TestTemplateStyling:
    """Test TemplateStyling enum."""

    def test_enum_values(self):
        """Test TemplateStyling enum has correct values."""
        assert TemplateStyling.PLAIN.value == "plain"
        assert TemplateStyling.HEADINGS.value == "headings"
        assert TemplateStyling.FULL.value == "full"

    def test_from_flag_value_valid_strings(self):
        """Test from_flag_value with valid string values."""
        assert TemplateStyling.from_flag_value("plain") == TemplateStyling.PLAIN
        assert TemplateStyling.from_flag_value("headings") == TemplateStyling.HEADINGS
        assert TemplateStyling.from_flag_value("full") == TemplateStyling.FULL

    def test_from_flag_value_none(self):
        """Test from_flag_value with None defaults to PLAIN."""
        assert TemplateStyling.from_flag_value(None) == TemplateStyling.PLAIN

    def test_from_flag_value_invalid(self):
        """Test from_flag_value with invalid values defaults to PLAIN."""
        assert TemplateStyling.from_flag_value("invalid") == TemplateStyling.PLAIN
        assert TemplateStyling.from_flag_value("") == TemplateStyling.PLAIN
        assert TemplateStyling.from_flag_value(123) == TemplateStyling.PLAIN


class TestStylingVariables:
    """Test get_styling_variables function."""

    def test_plain_styling(self):
        """Test plain styling returns empty strings."""
        vars = get_styling_variables(TemplateStyling.PLAIN)
        expected = {f: "" for f in ["b", "i", "h1", "h2", "h3", "h4", "h5", "h6"]}
        assert vars == expected

    def test_headings_styling(self):
        """Test headings styling returns heading markers only."""
        vars = get_styling_variables(TemplateStyling.HEADINGS)
        expected = {
            "b": "",
            "i": "",
            "h1": "# ",
            "h2": "## ",
            "h3": "### ",
            "h4": "#### ",
            "h5": "##### ",
            "h6": "###### ",
        }
        assert vars == expected

    def test_full_styling(self):
        """Test full styling returns all formatting markers."""
        vars = get_styling_variables(TemplateStyling.FULL)
        expected = {
            "b": "**",
            "i": "*",
            "h1": "# ",
            "h2": "## ",
            "h3": "### ",
            "h4": "#### ",
            "h5": "##### ",
            "h6": "###### ",
        }
        assert vars == expected
