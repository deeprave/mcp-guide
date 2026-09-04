"""Simple test for feature flag tools."""

from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest

from mcp_guide.tools.tool_feature_flags import ListFlagsArgs, internal_list_project_flags


class TestSimple:
    """Simple test to verify basic functionality."""

    @pytest.mark.anyio
    async def test_list_flags_basic(self, monkeypatch):
        """Basic test for list_project_flags function."""
        args = ListFlagsArgs()

        # Mock the explicit Session supplied by the application boundary.
        mock_session = Mock()

        # Mock the project and global flags proxies for merged result
        mock_project_proxy = Mock()
        mock_project_proxy.list = AsyncMock(return_value={"project_flag": True})
        mock_session.project_flags.return_value = mock_project_proxy

        mock_global_proxy = Mock()
        mock_global_proxy.list = AsyncMock(return_value={"global_flag": False})
        runtime = Mock()
        runtime.feature_flags.return_value = mock_global_proxy
        monkeypatch.setattr("mcp_guide.tools.tool_feature_flags.get_runtime", lambda: runtime)

        result = await internal_list_project_flags(
            args,
            SimpleNamespace(session=mock_session, project=object()),
        )

        # Basic assertion - project flags override global
        assert result.success is True
        assert result.value == {"global_flag": False, "project_flag": True}
