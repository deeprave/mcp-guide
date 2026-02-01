"""Formatter selection using ContentFormat enum."""

from enum import Enum
from typing import TYPE_CHECKING, Optional, Protocol

if TYPE_CHECKING:
    from mcp_guide.discovery.files import FileInfo

from mcp_guide.content.formatters.base import BaseFormatter
from mcp_guide.content.formatters.mime import MimeFormatter
from mcp_guide.content.formatters.plain import PlainFormatter
from mcp_guide.feature_flags.types import FeatureValue


class ContentFormatter(Protocol):
    """Protocol for content formatters."""

    async def format(self, files: list["FileInfo"], context_name: str) -> str:
        """Format files into a string representation."""
        ...


class ContentFormat(Enum):
    """Content format options."""

    NONE = "none"
    PLAIN = "plain"
    MIME = "mime"

    @classmethod
    def from_flag_value(cls, value: Optional[FeatureValue]) -> "ContentFormat":
        """Convert feature flag value to ContentFormat enum.

        Args:
            value: Feature flag value (string or None)

        Returns:
            ContentFormat enum value, defaults to NONE for invalid values
        """
        for format_type in cls:
            if format_type.value == value:
                return format_type
        return cls.NONE


class TemplateStyling(Enum):
    """Template styling options."""

    PLAIN = "plain"
    HEADINGS = "headings"
    FULL = "full"

    @classmethod
    def from_flag_value(cls, value: Optional[FeatureValue]) -> "TemplateStyling":
        """Convert feature flag value to TemplateStyling enum.

        Args:
            value: Feature flag value (string or None)

        Returns:
            TemplateStyling enum value, defaults to PLAIN for invalid values
        """
        for styling_type in cls:
            if styling_type.value == value:
                return styling_type
        return cls.PLAIN


def get_formatter_from_flag(format_type: ContentFormat) -> ContentFormatter:
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


def get_styling_variables(styling: TemplateStyling) -> dict[str, str]:
    """Get template styling variables based on TemplateStyling enum.

    Args:
        styling: TemplateStyling enum value

    Returns:
        Dictionary of formatting variables
    """
    styles = {f: "" for f in ["b", "i", "h1", "h2", "h3", "h4", "h5", "h6"]}

    match styling:
        case TemplateStyling.FULL:
            styles |= {
                "b": "**",
                "i": "*",
                "h1": "# ",
                "h2": "## ",
                "h3": "### ",
                "h4": "#### ",
                "h5": "##### ",
                "h6": "###### ",
            }
        case TemplateStyling.HEADINGS:
            styles |= {"h1": "# ", "h2": "## ", "h3": "### ", "h4": "#### ", "h5": "##### ", "h6": "###### "}
        case TemplateStyling.PLAIN:
            pass  # All styles remain empty strings

    return styles
