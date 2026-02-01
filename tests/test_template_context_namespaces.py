"""Tests for enhanced template context namespaces."""

from unittest.mock import AsyncMock, MagicMock, patch

from mcp_guide.context.tasks import ClientContextTask
from mcp_guide.render.context import get_user_context


class TestUserContext:
    """Test user context collection."""

    def test_get_user_context_returns_basic_user_info(self):
        """Test that get_user_context returns basic user information structure."""
        result = get_user_context()

        # Should return expected structure with empty values (client data not yet implemented)
        assert "name" in result
        assert "fullname" in result
        assert "firstname" in result
        assert "lastname" in result
        assert "uid" in result
        assert "gids" in result
        assert "login_time" in result


class TestSystemNamespaceRename:
    """Test renaming system to server-system."""

    def test_system_context_renamed_to_server_system(self):
        """Test that existing system context is renamed to server-system."""
        import asyncio

        from mcp_guide.render.cache import TemplateContextCache

        cache = TemplateContextCache()

        # Get system context
        context = asyncio.run(cache._build_system_context())

        # Should have server instead of system
        assert "server" in context
        assert "system" not in context


class TestClientContextIntegration:
    """Test integration of client context data."""

    def test_build_template_context_includes_new_namespaces(self):
        """Test that build_template_context includes user, system, and repo namespaces."""
        from mcp_guide.render.context import build_template_context

        # Mock client data
        client_data = {
            "user": {"name": "testuser", "uid": 1000},
            "system": {"uptime": 3600, "uptime_human": "1 hour"},
            "repo": {"origin": {"fetch_url": "https://github.com/test/repo.git"}},
        }

        context = build_template_context(client_data=client_data)

        assert "user" in context
        assert "system" in context
        assert "repo" in context
        assert context["user"]["name"] == "testuser"


class TestClientContextTask:
    """Test client context task implementation."""

    def test_client_context_task_requests_basic_os_info(self):
        """Test that ClientContextTask can request basic OS info."""
        mock_task_manager = MagicMock()
        mock_task_manager.queue_instruction = AsyncMock()
        mock_task_manager.subscribe = MagicMock()

        # Mock session to enable the flag
        mock_session = MagicMock()
        mock_flags = AsyncMock()
        mock_flags.list = AsyncMock(return_value={"allow-client-info": True})
        mock_session.feature_flags.return_value = mock_flags

        with patch("mcp_guide.session.get_current_session", return_value=mock_session):
            task = ClientContextTask(task_manager=mock_task_manager)

            # Verify task was created and subscribed
            assert task.get_name() == "ClientContextTask"
            mock_task_manager.subscribe.assert_called_once()

    def test_client_context_task_handles_os_response(self):
        """Test that ClientContextTask has event handling capability."""
        mock_task_manager = MagicMock()
        mock_task_manager.subscribe = MagicMock()

        task = ClientContextTask(task_manager=mock_task_manager)

        # Verify task has handle_event method
        assert hasattr(task, "handle_event")
        assert callable(task.handle_event)
