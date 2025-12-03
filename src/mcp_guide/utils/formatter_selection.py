"""Formatter selection using ContextVar."""

from contextvars import ContextVar

from mcp_guide.utils.content_formatter_mime import MimeFormatter
from mcp_guide.utils.content_formatter_plain import PlainFormatter

_FORMATTER_TYPE: ContextVar[str] = ContextVar("formatter_type", default="plain")


def set_formatter(formatter_type: str) -> None:
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
    if formatter_type == "mime":
        return MimeFormatter()
    return PlainFormatter()
