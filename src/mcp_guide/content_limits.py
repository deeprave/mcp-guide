"""Server-owned limits for content work."""

import re
from dataclasses import dataclass
from typing import Any

DEFAULT_MAX_CONTENT_LIMIT = 500_000_000
DEFAULT_MAX_DOCUMENTS_LIMIT = 100
DEFAULT_HTTP_SESSION_RATE_LIMIT = 5
DEFAULT_HTTP_SERVICE_RATE_LIMIT = 100

_BYTE_VALUE = re.compile(r"^(?P<value>[1-9][0-9]*)(?P<unit>b|kb|mb|gb)?$", re.IGNORECASE)
_DECIMAL_UNITS = {"b": 1, "kb": 1_000, "mb": 1_000_000, "gb": 1_000_000_000}


class ContentLimitExceeded(ValueError):
    """Raised when server-owned content capacity is exhausted."""

    def __init__(self, limit_name: str, limit: int) -> None:
        self.limit_name = limit_name
        self.limit = limit
        super().__init__(f"{limit_name} exceeds the configured limit of {limit}")


def ensure_within_limit(size: int, *, limit_name: str, limit: int) -> None:
    """Reject a byte or item count before it is materialised or returned."""
    if size > limit:
        raise ContentLimitExceeded(limit_name, limit)


class ContentBudget:
    """Accumulate UTF-8 text without exceeding one response budget."""

    def __init__(self, limit: int) -> None:
        self.limit = limit
        self.used = 0

    def add_text(self, content: str) -> None:
        """Reserve the exact UTF-8 byte size of one rendered fragment."""
        self.add_size(len(content.encode("utf-8")))

    def add_size(self, size: int) -> None:
        """Reserve a known byte size before retaining or serialising it."""
        ensure_within_limit(self.used + size, limit_name="max-content-limit", limit=self.limit)
        self.used += size


class BoundedTextAccumulator:
    """Build a final response only while its UTF-8 size remains within budget."""

    def __init__(self, limit: int) -> None:
        self._budget = ContentBudget(limit)
        self._parts: list[str] = []

    def append(self, content: str) -> None:
        """Append text after reserving its exact contribution."""
        self._budget.add_text(content)
        self._parts.append(content)

    def render(self) -> str:
        """Return the bounded response text."""
        return "".join(self._parts)


def _positive_integer(value: Any, *, field_name: str, allow_units: bool = False) -> int:
    if isinstance(value, bool):
        raise ValueError(f"{field_name} must be a positive integer")
    if isinstance(value, int) and value > 0:
        return value
    if allow_units and isinstance(value, str):
        match = _BYTE_VALUE.fullmatch(value.strip())
        if match is not None:
            unit = (match.group("unit") or "b").lower()
            return int(match.group("value")) * _DECIMAL_UNITS[unit]
    raise ValueError(f"{field_name} must be a positive integer")


@dataclass(frozen=True)
class ContentLimits:
    """Startup-snapshotted, globally configured content limits."""

    max_content_limit: int = DEFAULT_MAX_CONTENT_LIMIT
    max_document_limit: int = DEFAULT_MAX_DOCUMENTS_LIMIT
    http_session_rate_limit: int = DEFAULT_HTTP_SESSION_RATE_LIMIT
    http_service_rate_limit: int = DEFAULT_HTTP_SERVICE_RATE_LIMIT

    @classmethod
    def from_config(cls, config: dict[str, Any]) -> "ContentLimits":
        content = config.get("max-content-limit", DEFAULT_MAX_CONTENT_LIMIT)
        documents = config.get("max-document-limit", DEFAULT_MAX_DOCUMENTS_LIMIT)
        session_rate = config.get("http-session-rate-limit", DEFAULT_HTTP_SESSION_RATE_LIMIT)
        service_rate = config.get("http-service-rate-limit", DEFAULT_HTTP_SERVICE_RATE_LIMIT)
        return cls(
            max_content_limit=_positive_integer(content, field_name="max-content-limit", allow_units=True),
            max_document_limit=_positive_integer(documents, field_name="max-document-limit"),
            http_session_rate_limit=_positive_integer(session_rate, field_name="http-session-rate-limit"),
            http_service_rate_limit=_positive_integer(service_rate, field_name="http-service-rate-limit"),
        )


async def get_content_limits() -> ContentLimits:
    """Return the process snapshot, or defaults for isolated direct-unit calls."""
    from mcp_guide.runtime import get_runtime

    try:
        return await get_runtime().configuration_service().get_content_limits()
    except RuntimeError:
        return ContentLimits()
