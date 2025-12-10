"""Simple test for feature flag tools."""

import json
from unittest.mock import AsyncMock, Mock, patch

import pytest

from mcp_guide.tools.tool_feature_flags import ListFlagsArgs, list_flags


class TestSimple:
    """Simple test to verify basic functionality."""

    @pytest.mark.asyncio
    async def test_list_flags_basic(self):
        """Basic test for list_flags function."""
        args = ListFlagsArgs(project="*")

        # Mock the session and config manager
        with patch("mcp_guide.session.get_or_create_session") as mock_session_func:
            mock_session = Mock()
            mock_session_func.return_value = mock_session

            # Mock the feature flags proxy
            mock_flags_proxy = Mock()
            mock_flags_proxy.list = AsyncMock(return_value={"global_flag": True})
            mock_session.feature_flags.return_value = mock_flags_proxy

            result_str = await list_flags(args)
            result = json.loads(result_str)

            # Basic assertion
            assert result["success"] is True
            assert result["value"] == {"global_flag": True}
