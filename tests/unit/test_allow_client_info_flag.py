"""Tests for allow-client-info feature flag."""

from unittest.mock import patch

import pytest


class TestAllowClientInfoValidator:
    """Test allow-client-info flag validation."""

    def test_validator_accepts_enable_values(self):
        """Test that validator accepts all enable values and normalizes to True."""
        from mcp_guide.feature_flags.validators import validate_allow_client_info

        # All these should be accepted
        assert validate_allow_client_info(True, is_project=False)
        assert validate_allow_client_info("true", is_project=False)
        assert validate_allow_client_info("enabled", is_project=False)
        assert validate_allow_client_info("on", is_project=False)

    def test_validator_accepts_disable_values(self):
        """Test that validator accepts all disable values."""
        from mcp_guide.feature_flags.validators import validate_allow_client_info

        # All these should be accepted (will be normalized to None)
        assert validate_allow_client_info(False, is_project=False)
        assert validate_allow_client_info("false", is_project=False)
        assert validate_allow_client_info("disabled", is_project=False)
        assert validate_allow_client_info("off", is_project=False)
        assert validate_allow_client_info(None, is_project=False)

    def test_validator_rejects_invalid_values(self):
        """Test that validator rejects invalid values."""
        from mcp_guide.feature_flags.validators import validate_allow_client_info

        # These should be rejected
        assert not validate_allow_client_info("invalid", is_project=False)
        assert not validate_allow_client_info("yes", is_project=False)
        assert not validate_allow_client_info("no", is_project=False)
        assert not validate_allow_client_info(1, is_project=False)
        assert not validate_allow_client_info(0, is_project=False)

    def test_validator_rejects_project_level(self):
        """Test that validator rejects project-level setting."""
        from mcp_guide.feature_flags.validators import validate_allow_client_info

        # Should reject all values when is_project=True
        assert not validate_allow_client_info(True, is_project=True)
        assert not validate_allow_client_info("enabled", is_project=True)
        assert not validate_allow_client_info(False, is_project=True)
        assert not validate_allow_client_info(None, is_project=True)


class TestClientContextTaskConditional:
    """Test ClientContextTask conditional subscription."""

    @pytest.mark.asyncio
    async def test_task_unsubscribes_when_flag_disabled(self):
        """Test that task unsubscribes when allow-client-info is disabled."""
        from unittest.mock import AsyncMock, Mock

        from mcp_guide.client_context.tasks import ClientContextTask

        mock_task_manager = Mock()
        mock_task_manager.subscribe = Mock()
        mock_task_manager.unsubscribe = AsyncMock()

        mock_flags_proxy = Mock()
        mock_flags_proxy.list = AsyncMock(return_value={})  # Flag not set

        mock_session = AsyncMock()
        mock_session.feature_flags = Mock(return_value=mock_flags_proxy)

        # Create task - it will subscribe in __init__
        task = ClientContextTask(task_manager=mock_task_manager)
        mock_task_manager.subscribe.assert_called_once()

        # Patch get_or_create_session for on_tool call
        with patch("mcp_guide.session.get_or_create_session", return_value=mock_session):
            # Call on_tool - should check flag and unsubscribe
            await task.on_tool()

        # Should have unsubscribed
        mock_task_manager.unsubscribe.assert_called_once_with(task)

    @pytest.mark.asyncio
    async def test_task_stays_subscribed_when_flag_enabled(self):
        """Test that task stays subscribed when allow-client-info is enabled."""
        from unittest.mock import AsyncMock, Mock

        from mcp_guide.client_context.tasks import ClientContextTask

        mock_task_manager = Mock()
        mock_task_manager.subscribe = Mock()
        mock_task_manager.unsubscribe = AsyncMock()

        mock_flags_proxy = Mock()
        mock_flags_proxy.list = AsyncMock(return_value={"allow-client-info": True})

        mock_session = AsyncMock()
        mock_session.feature_flags = Mock(return_value=mock_flags_proxy)

        # Create task - it will subscribe in __init__
        task = ClientContextTask(task_manager=mock_task_manager)
        mock_task_manager.subscribe.assert_called_once()

        # Patch get_or_create_session for on_tool call
        with patch("mcp_guide.session.get_or_create_session", return_value=mock_session):
            # Call on_tool - should check flag and stay subscribed
            await task.on_tool()

        # Should NOT have unsubscribed
        mock_task_manager.unsubscribe.assert_not_called()

    @pytest.mark.asyncio
    async def test_task_unsubscribes_on_session_error(self):
        """Test that task unsubscribes when session access fails."""
        from unittest.mock import AsyncMock, Mock

        from mcp_guide.client_context.tasks import ClientContextTask

        mock_task_manager = Mock()
        mock_task_manager.subscribe = Mock()
        mock_task_manager.unsubscribe = AsyncMock()

        # Create task - it will subscribe in __init__
        task = ClientContextTask(task_manager=mock_task_manager)

        # Patch get_or_create_session to raise exception
        with patch("mcp_guide.session.get_or_create_session", side_effect=RuntimeError("No session")):
            # Call on_tool - should catch exception and unsubscribe
            await task.on_tool()

        # Should have unsubscribed due to error
        mock_task_manager.unsubscribe.assert_called_once_with(task)
