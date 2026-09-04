"""Tests for feature flag MCP tools."""

from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest

from mcp_guide.tools.tool_feature_flags import (
    GetFlagArgs,
    ListFlagsArgs,
    SetFlagArgs,
    internal_get_project_flag,
    internal_list_project_flags,
    internal_set_project_flag,
)


def _set_global_flags(monkeypatch: pytest.MonkeyPatch, proxy: Mock) -> None:
    runtime = Mock()
    runtime.feature_flags.return_value = proxy
    monkeypatch.setattr("mcp_guide.tools.tool_feature_flags.get_runtime", lambda: runtime)
    monkeypatch.setattr("mcp_guide.runtime.get_runtime", lambda: runtime)


_DEFAULT_PROJECT = object()


def request_context(session: Mock, *, project: object | None = _DEFAULT_PROJECT) -> SimpleNamespace:
    """Build the explicit application context required by direct handler tests."""
    return SimpleNamespace(session=session, project=project)


class TestListFlagsTool:
    """Test list_project_flags MCP tool."""

    @pytest.mark.anyio
    async def test_list_flags_current_project_active(self, monkeypatch):
        """Test listing current project flags with active=True (merged)."""
        args = ListFlagsArgs(active=True)

        mock_session = Mock()
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
        _set_global_flags(monkeypatch, mock_global_proxy)

        result = await internal_list_project_flags(args, request_context(mock_session))

        assert result.success is True
        # Should merge with project taking precedence
        expected = {"global_flag": True, "project_flag": False, "shared_flag": "project_override"}
        assert result.value == expected

    @pytest.mark.anyio
    async def test_list_flags_current_project_project_only(self):
        """Test listing current project flags with active=False (project only)."""
        args = ListFlagsArgs(active=False)

        mock_session = Mock()
        mock_session.project_name = "test-project"

        # Mock project flags proxy
        mock_project_proxy = Mock()
        mock_project_proxy.list = AsyncMock(return_value={"project_flag": False, "project_string": "value"})
        mock_session.project_flags.return_value = mock_project_proxy

        result = await internal_list_project_flags(args, request_context(mock_session))

        assert result.success is True
        assert result.value == {"project_flag": False, "project_string": "value"}

    @pytest.mark.anyio
    async def test_list_flags_specific_flag_name(self, monkeypatch):
        """Test listing specific flag by name."""
        args = ListFlagsArgs(feature_name="specific_flag")

        mock_session = Mock()

        # Mock project and global flags proxies for merged result
        mock_global_proxy = Mock()
        mock_global_proxy.list = AsyncMock(return_value={"other_flag": "ignored"})
        _set_global_flags(monkeypatch, mock_global_proxy)

        mock_project_proxy = Mock()
        mock_project_proxy.list = AsyncMock(return_value={"specific_flag": ["list", "value"]})
        mock_session.project_flags.return_value = mock_project_proxy

        result = await internal_list_project_flags(args, request_context(mock_session))

        assert result.success is True
        assert result.value == ["list", "value"]  # Single value, not dict

    @pytest.mark.anyio
    async def test_list_flags_no_current_project_error(self):
        """Test error when no current project and project=None."""
        args = ListFlagsArgs()

        result = await internal_list_project_flags(args, request_context(Mock(), project=None))

        assert result.success is False
        assert result.error_type == "no_project"
        assert "No project available" in result.error


class TestTestSetProjectFlagTool:
    """Test set_flag MCP tool."""

    @pytest.mark.anyio
    @pytest.mark.parametrize(
        "scenario,value,expected_msg,mock_method",
        [
            ("explicit_true", True, "Flag 'test_flag' set to True", "set"),
            ("explicit_value", "custom_value", "Flag 'test_flag' set to 'custom_value'", "set"),
            ("remove_none", None, "Flag 'test_flag' removed", "remove"),
        ],
        ids=["explicit_true", "explicit_value", "remove_none"],
    )
    async def test_set_flag_scenarios(self, scenario, value, expected_msg, mock_method):
        """Test setting flag with different values."""
        args = SetFlagArgs(feature_name="test_flag", value=value)

        mock_session = Mock()

        # Mock project flags proxy
        mock_flags_proxy = Mock()
        if mock_method == "set":
            mock_flags_proxy.set = AsyncMock()
        else:
            mock_flags_proxy.remove = AsyncMock()
        mock_session.project_flags.return_value = mock_flags_proxy

        result = await internal_set_project_flag(args, request_context(mock_session))

        assert result.success is True
        assert expected_msg in result.value

        if mock_method == "set":
            mock_flags_proxy.set.assert_called_once_with("test_flag", value)
        else:
            mock_flags_proxy.remove.assert_called_once_with("test_flag")

    @pytest.mark.anyio
    async def test_set_flag_defaults_to_true(self):
        """Test that value defaults to True when omitted."""
        # Construct without providing value parameter to test default
        args = SetFlagArgs(feature_name="test_flag")

        mock_session = Mock()

        mock_flags_proxy = Mock()
        mock_flags_proxy.set = AsyncMock()
        mock_session.project_flags.return_value = mock_flags_proxy

        result = await internal_set_project_flag(args, request_context(mock_session))

        assert result.success is True
        assert "Flag 'test_flag' set to True" in result.value
        mock_flags_proxy.set.assert_called_once_with("test_flag", True)

    @pytest.mark.anyio
    async def test_set_flag_validation_error(self):
        """Test validation error for invalid flag name."""
        args = SetFlagArgs(feature_name="invalid.flag", value=True)

        result = await internal_set_project_flag(args, request_context(Mock()))

        assert result.success is False
        assert result.error_type == "validation_error"
        assert "periods" in result.error.lower()


class TestTestGetProjectFlagTool:
    """Test get_flag MCP tool."""

    @pytest.mark.anyio
    async def test_get_flag_with_resolution(self, monkeypatch):
        """Test getting flag with project → global resolution."""
        args = GetFlagArgs(feature_name="test_flag")

        mock_session = Mock()
        mock_session.project_name = "test-project"

        # Mock project flags proxy
        mock_project_proxy = Mock()
        mock_project_proxy.list = AsyncMock(return_value={})  # Not in project
        mock_session.project_flags.return_value = mock_project_proxy

        # Mock global flags proxy
        mock_global_proxy = Mock()
        mock_global_proxy.list = AsyncMock(return_value={"test_flag": "global_value"})
        _set_global_flags(monkeypatch, mock_global_proxy)

        result = await internal_get_project_flag(args, request_context(mock_session))

        assert result.success is True
        assert result.value == "global_value"

    @pytest.mark.anyio
    async def test_get_flag_not_found(self, monkeypatch):
        """Test getting flag that doesn't exist."""
        args = GetFlagArgs(feature_name="nonexistent")

        mock_session = Mock()

        # Mock project and global flags proxies
        mock_project_proxy = Mock()
        mock_project_proxy.list = AsyncMock(return_value={})  # No project flags
        mock_session.project_flags.return_value = mock_project_proxy

        mock_global_proxy = Mock()
        mock_global_proxy.list = AsyncMock(return_value={})  # No global flags
        _set_global_flags(monkeypatch, mock_global_proxy)

        result = await internal_get_project_flag(args, request_context(mock_session))

        assert result.success is True
        assert result.value is None
