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
        args = ListFlagsArgs()

        # Mock the session and config manager
        with patch("mcp_guide.session.get_or_create_session") as mock_session_func:
            mock_session = Mock()
            mock_session_func.return_value = mock_session

            # Mock the project and global flags proxies for merged result
            mock_project_proxy = Mock()
            mock_project_proxy.list = AsyncMock(return_value={"project_flag": True})
            mock_session.project_flags.return_value = mock_project_proxy

            mock_global_proxy = Mock()
            mock_global_proxy.list = AsyncMock(return_value={"global_flag": False})
            mock_session.feature_flags.return_value = mock_global_proxy

            result_str = await list_flags(args)
            result = json.loads(result_str)

            # Basic assertion - project flags override global
            assert result["success"] is True
            assert result["value"] == {"global_flag": False, "project_flag": True}
