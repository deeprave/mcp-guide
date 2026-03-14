"""Tests for parse_options utility."""

import pytest

from mcp_guide.tools.tool_result import parse_options


@pytest.mark.parametrize(
    "options, expected",
    [
        ([], {}),
        (["verbose"], {"verbose": True}),
        (["limit=10"], {"limit": "10"}),
        (["verbose", "limit=10", "table"], {"verbose": True, "limit": "10", "table": True}),
        (["filter=a=b"], {"filter": "a=b"}),
    ],
    ids=["empty", "truthy_flag", "key_value", "mixed", "value_with_equals"],
)
def test_parse_options(options, expected):
    assert parse_options(options) == expected
