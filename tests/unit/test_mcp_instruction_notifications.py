"""Contract coverage for Guide's negotiated instruction notification."""

from types import SimpleNamespace

import pytest

from mcp_guide.mcp_context import SessionProtocolType
from mcp_guide.result import Result


def test_instruction_notification_has_compact_typed_payload() -> None:
    """The notification carries only delivery text and an opaque tracking key."""
    from mcp_guide.mcp_instruction_notifications import (
        INSTRUCTION_DISPATCH_METHOD,
        InstructionDispatchNotification,
        InstructionDispatchParams,
    )

    notification = InstructionDispatchNotification(
        params=InstructionDispatchParams(instruction="Use the bound project only.", tracking_id="tracked-123")
    )

    assert notification.method == INSTRUCTION_DISPATCH_METHOD
    assert notification.params.instruction == "Use the bound project only."
    assert notification.params.tracking_id == "tracked-123"


@pytest.mark.anyio
async def test_instruction_extension_is_advertised_only_to_modern_clients(tmp_path) -> None:
    """The capability is hidden from legacy initialisation and available to 2026 discovery."""
    from mcp_guide.cli import ServerConfig
    from mcp_guide.mcp_instruction_notifications import MCP_INSTRUCTION_EXTENSION_ID
    from mcp_guide.server import create_application

    application = create_application(ServerConfig(configdir=str(tmp_path)))
    try:
        assert MCP_INSTRUCTION_EXTENSION_ID in application.server._extensions
        legacy_options = application.server._mcp_server.create_initialization_options()
        assert MCP_INSTRUCTION_EXTENSION_ID not in (legacy_options.capabilities.extensions or {})
        modern_capabilities = application.server._mcp_server.get_capabilities(protocol_version="2026-07-28")
        assert MCP_INSTRUCTION_EXTENSION_ID in (modern_capabilities.extensions or {})
    finally:
        await application.runtime.stop()


@pytest.mark.anyio
async def test_negotiated_request_dispatches_its_own_queued_instruction(task_manager, monkeypatch) -> None:
    """A negotiated request sends only its own session's queued instruction."""
    import mcp_guide.mcp_instruction_notifications as notification_module
    from mcp_guide.mcp_instruction_notifications import (
        MCP_INSTRUCTION_EXTENSION_ID,
        process_result_for_response,
    )

    class CurrentMcpContext:
        session_id = "session-123"

        def __init__(self) -> None:
            self.notifications = []

        def client_supports_extension(self, identifier: str) -> bool:
            raise AssertionError("Modern delivery must use request-level extension negotiation")

        def client_extension_settings(self, identifier: str) -> dict[str, str] | None:
            return {} if identifier == MCP_INSTRUCTION_EXTENSION_ID else None

        async def send_notification(self, notification) -> None:
            self.notifications.append(notification)

    current_context = CurrentMcpContext()
    monkeypatch.setattr(notification_module, "get_context", lambda: current_context)
    session = SimpleNamespace(
        session_id="session-123",
        protocol_type=SessionProtocolType.MCP_2026_07_28,
        task_manager=task_manager,
    )
    await task_manager.queue_instruction("Use the bound project only.")

    result, instruction_dispatched = await process_result_for_response(Result.ok("answer"), session=session)

    assert result.additional_agent_instructions is None
    assert instruction_dispatched is True
    assert task_manager.is_queue_empty()
    assert len(current_context.notifications) == 1
    assert current_context.notifications[0].params.instruction == "Use the bound project only."


@pytest.mark.anyio
async def test_failed_notification_keeps_instruction_pending(task_manager, monkeypatch) -> None:
    """A send failure leaves the instruction available to a later owning request."""
    import mcp_guide.mcp_instruction_notifications as notification_module
    from mcp_guide.mcp_instruction_notifications import (
        MCP_INSTRUCTION_EXTENSION_ID,
        process_result_for_response,
    )

    class FailingMcpContext:
        session_id = "session-123"

        def client_supports_extension(self, identifier: str) -> bool:
            return identifier == MCP_INSTRUCTION_EXTENSION_ID

        async def send_notification(self, notification) -> None:
            raise RuntimeError("stream closed")

    monkeypatch.setattr(notification_module, "get_context", FailingMcpContext)
    session = SimpleNamespace(
        session_id="session-123",
        protocol_type=SessionProtocolType.MCP_2026_07_28,
        task_manager=task_manager,
    )
    await task_manager.queue_instruction("Use the bound project only.")

    result, instruction_dispatched = await process_result_for_response(Result.ok("answer"), session=session)

    assert result.additional_agent_instructions is None
    assert instruction_dispatched is False
    assert not task_manager.is_queue_empty()

    class RetriedMcpContext:
        session_id = "session-123"

        def __init__(self) -> None:
            self.notifications = []

        def client_supports_extension(self, identifier: str) -> bool:
            return identifier == MCP_INSTRUCTION_EXTENSION_ID

        async def send_notification(self, notification) -> None:
            self.notifications.append(notification)

    retried_context = RetriedMcpContext()
    monkeypatch.setattr(notification_module, "get_context", lambda: retried_context)
    result, instruction_dispatched = await process_result_for_response(Result.ok("answer"), session=session)

    assert result.additional_agent_instructions is None
    assert instruction_dispatched is True
    assert task_manager.is_queue_empty()
    assert len(retried_context.notifications) == 1


@pytest.mark.anyio
async def test_missing_request_stream_defers_instruction_to_the_next_request(task_manager, monkeypatch) -> None:
    """A modern response without an active stream cannot consume its instruction."""
    import mcp_guide.mcp_instruction_notifications as notification_module
    from mcp_guide.mcp_instruction_notifications import process_result_for_response

    def no_request_context():
        raise RuntimeError("No active FastMCP request context")

    monkeypatch.setattr(notification_module, "get_context", no_request_context)
    session = SimpleNamespace(
        session_id="session-123",
        protocol_type=SessionProtocolType.MCP_2026_07_28,
        task_manager=task_manager,
    )
    await task_manager.queue_instruction("Use the bound project only.")

    result, instruction_dispatched = await process_result_for_response(Result.ok("answer"), session=session)

    assert result.additional_agent_instructions is None
    assert instruction_dispatched is False
    assert not task_manager.is_queue_empty()


@pytest.mark.anyio
async def test_one_session_cannot_consume_another_sessions_instruction(task_manager, monkeypatch) -> None:
    """Each resolved session consumes only its own task-manager queue."""
    import mcp_guide.mcp_instruction_notifications as notification_module
    from mcp_guide.mcp_instruction_notifications import (
        MCP_INSTRUCTION_EXTENSION_ID,
        process_result_for_response,
    )

    class CurrentMcpContext:
        session_id = "connection-123"

        def client_supports_extension(self, identifier: str) -> bool:
            return identifier == MCP_INSTRUCTION_EXTENSION_ID

        async def send_notification(self, notification) -> None:
            raise AssertionError("An empty session must not dispatch a notification")

    monkeypatch.setattr(notification_module, "get_context", CurrentMcpContext)
    other_task_manager = type(task_manager)()
    session = SimpleNamespace(
        session_id="session-b",
        protocol_type=SessionProtocolType.MCP_2026_07_28,
        task_manager=other_task_manager,
    )
    await task_manager.queue_instruction("Use the bound project only.")

    result, instruction_dispatched = await process_result_for_response(Result.ok("answer"), session=session)

    assert result.additional_agent_instructions is None
    assert instruction_dispatched is False
    assert not task_manager.is_queue_empty()


@pytest.mark.anyio
@pytest.mark.parametrize("surface", ["tool", "prompt"], ids=["tool", "prompt"])
async def test_negotiated_tool_and_prompt_responses_omit_dispatched_metadata(
    task_manager, monkeypatch, surface
) -> None:
    """Negotiated non-resource responses send guidance without response metadata."""
    import mcp_guide.mcp_instruction_notifications as notification_module
    from mcp_guide.mcp_instruction_notifications import MCP_INSTRUCTION_EXTENSION_ID
    from mcp_guide.tools.tool_result import prompt_result, tool_result

    class CurrentMcpContext:
        session_id = "connection-123"

        def __init__(self) -> None:
            self.notifications = []

        def client_extension_settings(self, identifier: str) -> dict[str, str] | None:
            return {} if identifier == MCP_INSTRUCTION_EXTENSION_ID else None

        def client_supports_extension(self, identifier: str) -> bool:
            raise AssertionError("Request-level extension negotiation must be preferred")

        async def send_notification(self, notification) -> None:
            self.notifications.append(notification)

    current_context = CurrentMcpContext()
    monkeypatch.setattr(notification_module, "get_context", lambda: current_context)
    session = SimpleNamespace(
        session_id="session-123",
        protocol_type=SessionProtocolType.MCP_2026_07_28,
        task_manager=task_manager,
    )
    await task_manager.queue_instruction("Use the bound project only.")

    if surface == "tool":
        response = await tool_result("example", Result.ok("answer"), session=session)
    else:
        response = await prompt_result("example", Result.ok("answer"), session=session)

    assert response.meta is None
    assert len(current_context.notifications) == 1


@pytest.mark.anyio
async def test_negotiated_failure_response_still_dispatches_instruction(task_manager, monkeypatch) -> None:
    """Notification delivery is independent of whether the requested operation failed."""
    import mcp_guide.mcp_instruction_notifications as notification_module
    from mcp_guide.mcp_instruction_notifications import MCP_INSTRUCTION_EXTENSION_ID
    from mcp_guide.tools.tool_result import tool_result

    class CurrentMcpContext:
        def __init__(self) -> None:
            self.notifications = []

        def client_extension_settings(self, identifier: str) -> dict[str, str] | None:
            return {} if identifier == MCP_INSTRUCTION_EXTENSION_ID else None

        async def send_notification(self, notification) -> None:
            self.notifications.append(notification)

    current_context = CurrentMcpContext()
    monkeypatch.setattr(notification_module, "get_context", lambda: current_context)
    session = SimpleNamespace(
        session_id="session-123",
        protocol_type=SessionProtocolType.MCP_2026_07_28,
        task_manager=task_manager,
    )
    await task_manager.queue_instruction("Use the bound project only.")

    response = await tool_result("example", Result.failure("not available"), session=session)

    assert response.is_error is True
    assert response.meta is None
    assert len(current_context.notifications) == 1


@pytest.mark.anyio
async def test_negotiated_resource_response_omits_dispatched_metadata(task_manager) -> None:
    """A negotiated resource response uses the same request-bound notification path."""
    from mcp_guide.mcp_instruction_notifications import MCP_INSTRUCTION_EXTENSION_ID
    from mcp_guide.resources import _process_and_serialize

    class CurrentMcpContext:
        session_id = "connection-123"

        def __init__(self) -> None:
            self.notifications = []

        def client_extension_settings(self, identifier: str) -> dict[str, str] | None:
            return {} if identifier == MCP_INSTRUCTION_EXTENSION_ID else None

        def client_supports_extension(self, identifier: str) -> bool:
            raise AssertionError("Request-level extension negotiation must be preferred")

        async def send_notification(self, notification) -> None:
            self.notifications.append(notification)

    current_context = CurrentMcpContext()
    session = SimpleNamespace(
        session_id="session-123",
        protocol_type=SessionProtocolType.MCP_2026_07_28,
        task_manager=task_manager,
    )
    request_context = SimpleNamespace(session=session, session_id="session-123")
    await task_manager.queue_instruction("Use the bound project only.")

    response = await _process_and_serialize(Result.ok("answer"), request_context, mcp_context=current_context)

    assert response.meta is None
    assert len(current_context.notifications) == 1
