"""Formatter selection using ContentFormat enum."""

from enum import Enum

from mcp_guide.utils.content_formatter_base import BaseFormatter
from mcp_guide.utils.content_formatter_mime import MimeFormatter
from mcp_guide.utils.content_formatter_plain import PlainFormatter


class ContentFormat(Enum):
    """Content format options."""

    NONE = "none"
    PLAIN = "plain"
    MIME = "mime"


def get_formatter_from_flag(format_type: ContentFormat) -> BaseFormatter | PlainFormatter | MimeFormatter:
    """Get formatter instance based on ContentFormat enum.

    Args:
        format_type: ContentFormat enum value

    Returns:
        Appropriate formatter instance
    """
    if format_type == ContentFormat.PLAIN:
        return PlainFormatter()
    elif format_type == ContentFormat.MIME:
        return MimeFormatter()
    else:
        return BaseFormatter()
