"""Tests for server-owned content limit configuration."""

import pytest

from mcp_guide.content_limits import DEFAULT_MAX_CONTENT_LIMIT, DEFAULT_MAX_DOCUMENTS_LIMIT, ContentLimits


def test_content_limits_use_documented_defaults() -> None:
    limits = ContentLimits.from_config({})

    assert limits.max_content_limit == DEFAULT_MAX_CONTENT_LIMIT == 500_000_000
    assert limits.max_document_limit == DEFAULT_MAX_DOCUMENTS_LIMIT == 100
    assert limits.http_session_rate_limit == 5
    assert limits.http_service_rate_limit == 100


@pytest.mark.parametrize(
    ("value", "expected"),
    [("500mb", 500_000_000), ("2KB", 2_000), ("1b", 1), (42, 42)],
)
def test_content_limit_accepts_decimal_human_readable_values(value: str | int, expected: int) -> None:
    assert ContentLimits.from_config({"max-content-limit": value}).max_content_limit == expected


@pytest.mark.parametrize("value", [0, -1, "0mb", "1mib", "unlimited", 1.5])
def test_content_limit_rejects_invalid_values(value: object) -> None:
    with pytest.raises(ValueError):
        ContentLimits.from_config({"max-content-limit": value})
