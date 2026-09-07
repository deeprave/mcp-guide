"""Transport parser rejects invalid schemes and malformed ports."""

import pytest

from mcp_guide.cli import parse_transport_mode


@pytest.mark.parametrize(
    "value,message",
    [("ftp://example.com", "Invalid transport mode"), ("http://localhost:abc", "Invalid port|Port could not be cast")],
    ids=["scheme", "port"],
)
def test_parse_invalid_transport(value, message):
    with pytest.raises(ValueError, match=message):
        parse_transport_mode(value)
