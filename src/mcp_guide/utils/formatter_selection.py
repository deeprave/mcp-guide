"""Formatter selection using ContextVar."""

from contextvars import ContextVar
from typing import Literal

from mcp_guide.utils.content_formatter_mime import MimeFormatter
from mcp_guide.utils.content_formatter_plain import PlainFormatter

FormatterType = Literal["plain", "mime"]

_FORMATTER_TYPE: ContextVar[FormatterType] = ContextVar("formatter_type", default="plain")


def set_formatter(formatter_type: FormatterType) -> None:
    """Set active formatter type.

    Args:
        formatter_type: Either 'plain' or 'mime'

    Raises:
        ValueError: If formatter_type is not 'plain' or 'mime'
    """
    if formatter_type not in ("plain", "mime"):
        raise ValueError(f"Invalid formatter type: {formatter_type}")
    _FORMATTER_TYPE.set(formatter_type)


def get_formatter() -> PlainFormatter | MimeFormatter:
    """Get active formatter instance.

    Returns:
        PlainFormatter or MimeFormatter based on current context
    """
    formatter_type = _FORMATTER_TYPE.get()
    return MimeFormatter() if formatter_type == "mime" else PlainFormatter()
