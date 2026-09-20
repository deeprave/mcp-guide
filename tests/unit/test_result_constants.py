"""Disposition constant values match the result-disposition specification."""

from mcp_guide.result_constants import AGENT_ERROR, USER_ERROR


def test_error_disposition_constants_match_spec():
    assert AGENT_ERROR == "agent/error"
    assert USER_ERROR == "user/error"
