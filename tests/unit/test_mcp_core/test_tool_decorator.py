"""Tests for tool decorator test mode control."""

import pytest

from mcp_guide.core.tool_decorator import disable_test_mode, enable_test_mode


@pytest.mark.anyio
async def test_invalid_session_returns_rebind_guidance(monkeypatch) -> None:
    """A rejected session ID is not presented as a normal unbound interaction."""
    from mcp_guide.core.tool_decorator import _check_project_bound
    from mcp_guide.session import InvalidGuideSessionError

    async def reject_session(*_args, **_kwargs):
        raise InvalidGuideSessionError("Invalid or unknown session ID")

    monkeypatch.setattr("mcp_guide.core.tool_decorator.get_session", reject_session)

    response = await _check_project_bound(object(), session_id="expired-session")

    assert response is not None
    assert response.structured_content["error_type"] == "invalid_session"
    assert "discard" in response.structured_content["instruction"].lower()
    assert "set_project" in response.structured_content["instruction"]


@pytest.mark.anyio
async def test_invalid_project_name_is_not_reported_as_no_project(monkeypatch) -> None:
    """A rejected PWD basename is an invalid name, not an unbound project."""
    from mcp_guide.core.tool_decorator import _check_project_bound
    from mcp_guide.validation import InvalidProjectNameError

    async def reject_name(*_args, **_kwargs):
        raise InvalidProjectNameError("Project path basename must contain only alphanumeric characters")

    monkeypatch.setattr("mcp_guide.core.tool_decorator.get_session", reject_name)

    response = await _check_project_bound(object(), session_id=None)

    assert response is not None
    assert response.structured_content["error_type"] == "invalid_name"


@pytest.fixture(autouse=True)
def reset_tool_decorator_mode():
    """Keep the decorator's test-only ContextVar local to each test."""
    disable_test_mode()
    yield
    disable_test_mode()


class TestTestModeControl:
    """Tests for test mode enable/disable functions."""

    def test_enable_test_mode_sets_context_var_to_true(self):
        """Test that enable_test_mode() sets ContextVar to True."""
        from mcp_guide.core.tool_decorator import _test_mode

        enable_test_mode()
        assert _test_mode.get() is True

    def test_disable_test_mode_sets_context_var_to_false(self):
        """Test that disable_test_mode() sets ContextVar to False."""
        from mcp_guide.core.tool_decorator import _test_mode

        enable_test_mode()  # First enable
        disable_test_mode()
        assert _test_mode.get() is False

    def test_default_value_is_false(self):
        """Test that ContextVar default value is False."""
        # Reset to default by creating new context
        import contextvars

        from mcp_guide.core.tool_decorator import _test_mode

        ctx = contextvars.copy_context()
        result = ctx.run(lambda: _test_mode.get())
        assert result is False

    def test_context_var_is_isolated_per_context(self):
        """Test that ContextVar changes don't affect parent context."""
        import contextvars

        from mcp_guide.core.tool_decorator import _test_mode

        # Set in current context
        enable_test_mode()
        assert _test_mode.get() is True

        # Create child context and modify there
        def modify_in_child():
            disable_test_mode()
            return _test_mode.get()

        ctx = contextvars.copy_context()
        result = ctx.run(modify_in_child)
        assert result is False

        # Parent context should still be True
        assert _test_mode.get() is True
