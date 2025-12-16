"""Tests for feature flag MCP tools."""

import json
from unittest.mock import AsyncMock, Mock, patch

import pytest

from mcp_core.result import Result
from mcp_guide.tools.tool_feature_flags import (
    GetFlagArgs,
    ListFlagsArgs,
    SetFlagArgs,
    get_project_flag,
    list_project_flags,
    set_project_flag,
)


def parse_result_json(json_str: str) -> Result:
    """Parse JSON string back to Result object for testing."""
    data = json.loads(json_str)
    if data["success"]:
        return Result.ok(data.get("value"), message=data.get("message"), instruction=data.get("instruction"))
    else:
        return Result.failure(
            data["error"],
            error_type=data["error_type"],
            message=data.get("message"),
            instruction=data.get("instruction"),
        )


class TestListFlagsTool:
    """Test list_project_flags MCP tool."""

    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_list_flags_current_project_active(self):
        """Test listing current project flags with active=True (merged)."""
        args = ListFlagsArgs(active=True)

        with patch("mcp_guide.session.get_or_create_session") as mock_session_func:
            mock_session = Mock()
            mock_session_func.return_value = mock_session
            mock_session.project_name = "test-project"

            # Mock project flags proxy
            mock_project_proxy = Mock()
            mock_project_proxy.list = AsyncMock(
                return_value={
                    "project_flag": False,
                    "shared_flag": "project_override",  # overrides global
                }
            )
            mock_session.project_flags.return_value = mock_project_proxy

            # Mock global flags proxy
            mock_global_proxy = Mock()
            mock_global_proxy.list = AsyncMock(return_value={"global_flag": True, "shared_flag": "global_value"})
            mock_session.feature_flags.return_value = mock_global_proxy

            result_json = await list_project_flags(args)
            result = parse_result_json(result_json)

            assert result.success is True
            # Should merge with project taking precedence
            expected = {"global_flag": True, "project_flag": False, "shared_flag": "project_override"}
            assert result.value == expected

    @pytest.mark.asyncio
    async def test_list_flags_current_project_project_only(self):
        """Test listing current project flags with active=False (project only)."""
        args = ListFlagsArgs(active=False)

        with patch("mcp_guide.session.get_or_create_session") as mock_session_func:
            mock_session = Mock()
            mock_session_func.return_value = mock_session
            mock_session.project_name = "test-project"

            # Mock project flags proxy
            mock_project_proxy = Mock()
            mock_project_proxy.list = AsyncMock(return_value={"project_flag": False, "project_string": "value"})
            mock_session.project_flags.return_value = mock_project_proxy

            result_json = await list_project_flags(args)
            result = parse_result_json(result_json)

            assert result.success is True
            assert result.value == {"project_flag": False, "project_string": "value"}

    @pytest.mark.asyncio
    async def test_list_flags_specific_flag_name(self):
        """Test listing specific flag by name."""
        args = ListFlagsArgs(feature_name="specific_flag")

        with patch("mcp_guide.session.get_or_create_session") as mock_session_func:
            mock_session = Mock()
            mock_session_func.return_value = mock_session

            # Mock project and global flags proxies for merged result
            mock_global_proxy = Mock()
            mock_global_proxy.list = AsyncMock(return_value={"other_flag": "ignored"})
            mock_session.feature_flags.return_value = mock_global_proxy

            mock_project_proxy = Mock()
            mock_project_proxy.list = AsyncMock(return_value={"specific_flag": ["list", "value"]})
            mock_session.project_flags.return_value = mock_project_proxy

            result_json = await list_project_flags(args)
            result = parse_result_json(result_json)

            assert result.success is True
            assert result.value == ["list", "value"]  # Single value, not dict

    @pytest.mark.asyncio
    async def test_list_flags_no_current_project_error(self):
        """Test error when no current project and project=None."""
        args = ListFlagsArgs()

        with patch("mcp_guide.session.get_or_create_session") as mock_session_func:
            mock_session_func.side_effect = ValueError("No current project available")

            result_json = await list_project_flags(args)
            result = parse_result_json(result_json)

            assert result.success is False
            assert result.error_type == "no_project"
            assert "No current project" in result.error


class TestTestSetProjectFlagTool:
    """Test set_flag MCP tool."""

    @pytest.mark.asyncio
    async def test_set_flag_default_value_true(self):
        """Test setting flag with default value (True)."""
        args = SetFlagArgs(feature_name="new_flag")

        with patch("mcp_guide.session.get_or_create_session") as mock_session_func:
            mock_session = Mock()
            mock_session_func.return_value = mock_session

            # Mock project flags proxy
            mock_flags_proxy = Mock()
            mock_flags_proxy.set = AsyncMock()
            mock_session.project_flags.return_value = mock_flags_proxy

            result_json = await set_project_flag(args)
            result = parse_result_json(result_json)

            assert result.success is True
            assert "Flag 'new_flag' set to True" in result.value
            mock_flags_proxy.set.assert_called_once_with("new_flag", True)

    @pytest.mark.asyncio
    async def test_set_flag_explicit_value(self):
        """Test setting flag with explicit value."""
        args = SetFlagArgs(feature_name="test_flag", value="custom_value")

        with patch("mcp_guide.session.get_or_create_session") as mock_session_func:
            mock_session = Mock()
            mock_session_func.return_value = mock_session
            mock_session.project_name = "test-project"

            # Mock project flags proxy
            mock_project_proxy = Mock()
            mock_project_proxy.set = AsyncMock()
            mock_session.project_flags.return_value = mock_project_proxy

            result_json = await set_project_flag(args)
            result = parse_result_json(result_json)

            assert result.success is True
            assert "Flag 'test_flag' set to 'custom_value'" in result.value
            mock_project_proxy.set.assert_called_once_with("test_flag", "custom_value")

    @pytest.mark.asyncio
    async def test_set_flag_remove_with_none(self):
        """Test removing flag with value=None."""
        args = SetFlagArgs(feature_name="remove_flag", value=None)

        with patch("mcp_guide.session.get_or_create_session") as mock_session_func:
            mock_session = Mock()
            mock_session_func.return_value = mock_session

            # Mock global flags proxy
            mock_flags_proxy = Mock()
            mock_flags_proxy.remove = AsyncMock()
            mock_session.project_flags.return_value = mock_flags_proxy

            result_json = await set_project_flag(args)
            result = parse_result_json(result_json)

            assert result.success is True
            assert "Flag 'remove_flag' removed" in result.value
            mock_flags_proxy.remove.assert_called_once_with("remove_flag")

    @pytest.mark.asyncio
    async def test_set_flag_validation_error(self):
        """Test validation error for invalid flag name."""
        args = SetFlagArgs(feature_name="invalid.flag", value=True)

        result_json = await set_project_flag(args)
        result = parse_result_json(result_json)

        assert result.success is False
        assert result.error_type == "validation_error"
        assert "periods" in result.error.lower()


class TestTestGetProjectFlagTool:
    """Test get_flag MCP tool."""

    @pytest.mark.asyncio
    async def test_get_flag_with_resolution(self):
        """Test getting flag with project → global resolution."""
        args = GetFlagArgs(feature_name="test_flag")

        with patch("mcp_guide.session.get_or_create_session") as mock_session_func:
            mock_session = Mock()
            mock_session_func.return_value = mock_session
            mock_session.project_name = "test-project"

            # Mock project flags proxy
            mock_project_proxy = Mock()
            mock_project_proxy.list = AsyncMock(return_value={})  # Not in project
            mock_session.project_flags.return_value = mock_project_proxy

            # Mock global flags proxy
            mock_global_proxy = Mock()
            mock_global_proxy.list = AsyncMock(return_value={"test_flag": "global_value"})
            mock_session.feature_flags.return_value = mock_global_proxy

            result_json = await get_project_flag(args)
            result = parse_result_json(result_json)

            assert result.success is True
            assert result.value == "global_value"

    @pytest.mark.asyncio
    async def test_get_flag_not_found(self):
        """Test getting flag that doesn't exist."""
        args = GetFlagArgs(feature_name="nonexistent")

        with patch("mcp_guide.session.get_or_create_session") as mock_session_func:
            mock_session = Mock()
            mock_session_func.return_value = mock_session

            # Mock project and global flags proxies
            mock_project_proxy = Mock()
            mock_project_proxy.list = AsyncMock(return_value={})  # No project flags
            mock_session.project_flags.return_value = mock_project_proxy

            mock_global_proxy = Mock()
            mock_global_proxy.list = AsyncMock(return_value={})  # No global flags
            mock_session.feature_flags.return_value = mock_global_proxy

            result_json = await get_project_flag(args)
            result = parse_result_json(result_json)

            assert result.success is True
            assert result.value is None
