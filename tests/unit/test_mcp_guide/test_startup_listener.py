"""Tests for StartupInstructionListener."""

from unittest.mock import AsyncMock, MagicMock, call, patch

import pytest

from mcp_guide.startup_listener import StartupInstructionListener


def _make_session(project_name: str = "test-project") -> MagicMock:
    session = MagicMock()
    session.project_name = project_name
    return session


@pytest.mark.anyio
async def test_startup_instruction_queued_when_rendered() -> None:
    """Startup instruction is queued at high priority when template renders content."""
    session = _make_session()
    rendered = MagicMock()
    rendered.content = "Do the startup thing."

    task_manager = MagicMock()
    task_manager.queue_instruction = AsyncMock()

    with (
        patch("mcp_guide.startup_listener.render_content", new=AsyncMock(side_effect=[rendered, None])),
        patch("mcp_guide.startup_listener.get_task_manager", return_value=task_manager),
    ):
        listener = StartupInstructionListener()
        await listener.on_project_changed(session, "old", "test-project")

    task_manager.queue_instruction.assert_any_call(rendered.content, priority=True)


@pytest.mark.anyio
async def test_startup_instruction_not_queued_when_filtered() -> None:
    """No instruction queued when _startup template is filtered (requires-* not met)."""
    session = _make_session()

    task_manager = MagicMock()
    task_manager.queue_instruction = AsyncMock()

    with (
        patch("mcp_guide.startup_listener.render_content", new=AsyncMock(return_value=None)),
        patch("mcp_guide.startup_listener.get_task_manager", return_value=task_manager),
    ):
        listener = StartupInstructionListener()
        await listener.on_project_changed(session, "old", "test-project")

    # queue_instruction called only for onboard prompt (if at all), not for startup
    for c in task_manager.queue_instruction.call_args_list:
        assert c != call("Do the startup thing.", priority=True)


@pytest.mark.anyio
async def test_onboard_prompt_queued_at_low_priority_when_not_onboarded() -> None:
    """Onboard prompt instruction is queued at low priority when requires-onboarded: false passes."""
    session = _make_session()
    startup_rendered = None  # startup-instruction not set
    onboard_rendered = MagicMock()
    # _onboard_prompt is agent/instruction type; .instruction carries the display directive
    onboard_rendered.instruction = "Render guide://docs/onboard and display it to the user verbatim."

    task_manager = MagicMock()
    task_manager.queue_instruction = AsyncMock()

    with (
        patch(
            "mcp_guide.startup_listener.render_content", new=AsyncMock(side_effect=[startup_rendered, onboard_rendered])
        ),
        patch("mcp_guide.startup_listener.get_task_manager", return_value=task_manager),
    ):
        listener = StartupInstructionListener()
        await listener.on_project_changed(session, "old", "test-project")

    task_manager.queue_instruction.assert_called_once_with(onboard_rendered.instruction, priority=False)


@pytest.mark.anyio
async def test_onboard_prompt_suppressed_when_onboarded() -> None:
    """Onboard prompt is not queued when requires-onboarded: false is not satisfied (onboarded=true)."""
    session = _make_session()
    # Both templates return None — startup filtered, onboard filtered because onboarded=true
    task_manager = MagicMock()
    task_manager.queue_instruction = AsyncMock()

    with (
        patch("mcp_guide.startup_listener.render_content", new=AsyncMock(return_value=None)),
        patch("mcp_guide.startup_listener.get_task_manager", return_value=task_manager),
    ):
        listener = StartupInstructionListener()
        await listener.on_project_changed(session, "old", "test-project")

    task_manager.queue_instruction.assert_not_called()


@pytest.mark.anyio
async def test_both_queued_when_both_render() -> None:
    """Both startup instruction and onboard prompt are queued when both templates render."""
    session = _make_session()
    startup_rendered = MagicMock()
    startup_rendered.content = "Run startup init."
    onboard_rendered = MagicMock()
    onboard_rendered.instruction = "Render guide://docs/onboard and display it to the user verbatim."

    task_manager = MagicMock()
    task_manager.queue_instruction = AsyncMock()

    with (
        patch(
            "mcp_guide.startup_listener.render_content", new=AsyncMock(side_effect=[startup_rendered, onboard_rendered])
        ),
        patch("mcp_guide.startup_listener.get_task_manager", return_value=task_manager),
    ):
        listener = StartupInstructionListener()
        await listener.on_project_changed(session, "old", "test-project")

    assert task_manager.queue_instruction.call_count == 2
    task_manager.queue_instruction.assert_any_call(startup_rendered.content, priority=True)
    task_manager.queue_instruction.assert_any_call(onboard_rendered.instruction, priority=False)


@pytest.mark.anyio
async def test_startup_error_does_not_prevent_onboard_prompt() -> None:
    """An error rendering _startup does not prevent the onboard prompt from being queued."""
    session = _make_session()
    onboard_rendered = MagicMock()
    onboard_rendered.instruction = "Render guide://docs/onboard and display it to the user verbatim."

    task_manager = MagicMock()
    task_manager.queue_instruction = AsyncMock()

    async def render_side_effect(pattern, category_dir):
        if pattern == "_startup":
            raise Exception("unexpected render failure")
        return onboard_rendered

    with (
        patch("mcp_guide.startup_listener.render_content", new=AsyncMock(side_effect=render_side_effect)),
        patch("mcp_guide.startup_listener.get_task_manager", return_value=task_manager),
    ):
        listener = StartupInstructionListener()
        await listener.on_project_changed(session, "old", "test-project")

    task_manager.queue_instruction.assert_called_once_with(onboard_rendered.instruction, priority=False)


@pytest.mark.anyio
async def test_on_config_changed_is_noop() -> None:
    """on_config_changed does not queue any instructions."""
    session = _make_session()
    task_manager = MagicMock()
    task_manager.queue_instruction = AsyncMock()

    with patch("mcp_guide.startup_listener.get_task_manager", return_value=task_manager):
        listener = StartupInstructionListener()
        await listener.on_config_changed(session)

    task_manager.queue_instruction.assert_not_called()
