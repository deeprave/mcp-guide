"""Tests for allow-client-info feature flag."""

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
    """Test ClientContextTask conditional subscription.

    Note: Flag checking is now handled in on_init() at server startup.
    See tests/unit/test_on_init.py for on_init() behavior tests.
    """

    @pytest.mark.asyncio
    async def test_task_subscribes_on_creation(self):
        """Test that task subscribes when created."""
        from unittest.mock import Mock

        from mcp_guide.client_context.tasks import ClientContextTask

        mock_task_manager = Mock()
        mock_task_manager.subscribe = Mock()

        # Create task - it will subscribe in __init__
        task = ClientContextTask(task_manager=mock_task_manager)
        mock_task_manager.subscribe.assert_called_once()
