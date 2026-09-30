"""Negotiated FastMCP delivery for session-owned Guide instructions."""

from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING, Any, Literal, TypeVar, cast

from fastmcp.server.dependencies import get_context
from fastmcp.server.extensions import MethodBinding, ServerExtension
from mcp.server.lowlevel.server import NotificationOptions
from mcp.server.models import InitializationOptions
from mcp_types import Notification, NotificationParams

from mcp_guide.core.mcp_log import get_logger
from mcp_guide.mcp_context import SessionProtocolType

if TYPE_CHECKING:
    from mcp_guide.result import Result
    from mcp_guide.session import Session

logger = get_logger(__name__)

T = TypeVar("T")

MCP_INSTRUCTION_EXTENSION_ID = "io.uniquode/mcp-guide-instructions"
INSTRUCTION_DISPATCH_METHOD = "notifications/instructions/dispatch"


class InstructionDispatchParams(NotificationParams):
    """The complete payload for one queued Guide instruction."""

    instruction: str
    tracking_id: str | None = None


class InstructionDispatchNotification(
    Notification[InstructionDispatchParams, Literal["notifications/instructions/dispatch"]]
):
    """Deliver one queued instruction outside the requested response."""

    method: Literal["notifications/instructions/dispatch"] = INSTRUCTION_DISPATCH_METHOD
    params: InstructionDispatchParams


class GuideInstructionExtension(ServerExtension):
    """Advertise Guide's notification-only modern instruction capability."""

    identifier = MCP_INSTRUCTION_EXTENSION_ID

    def methods(self) -> Sequence[MethodBinding]:
        """Expose no client requests; this extension delivers notifications only."""
        return ()


def limit_instruction_extension_to_modern_protocols(low_level_server: Any) -> None:
    """Hide the extension from retained handshake initialisation capabilities.

    FastMCP's capability builder advertises registered extensions unconditionally.
    Retained clients receive its static ``create_initialization_options()`` output,
    whereas 2026-07-28 clients negotiate through protocol-aware discovery. Filter
    only the former so the extension remains available to modern clients.
    """
    create_initialization_options = low_level_server.create_initialization_options

    def legacy_initialization_options(
        notification_options: NotificationOptions | None = None,
        experimental_capabilities: dict[str, dict[str, Any]] | None = None,
        extensions: dict[str, dict[str, Any]] | None = None,
    ) -> InitializationOptions:
        options = create_initialization_options(notification_options, experimental_capabilities, extensions)
        capability_extensions = dict(options.capabilities.extensions or {})
        capability_extensions.pop(MCP_INSTRUCTION_EXTENSION_ID, None)
        capabilities = options.capabilities.model_copy(update={"extensions": capability_extensions or None})
        return options.model_copy(update={"capabilities": capabilities})

    low_level_server.create_initialization_options = legacy_initialization_options


def _client_negotiated_instruction_delivery(fastmcp_context: Any) -> bool:
    """Return whether this request opted into the Guide notification extension."""
    extension_settings = getattr(fastmcp_context, "client_extension_settings", None)
    if callable(extension_settings) and extension_settings(MCP_INSTRUCTION_EXTENSION_ID) is not None:
        return True
    return fastmcp_context.client_supports_extension(MCP_INSTRUCTION_EXTENSION_ID)


async def process_result_for_response(
    result: "Result[T]",
    *,
    session: "Session",
    fastmcp_context: Any | None = None,
) -> tuple["Result[T]", bool]:
    """Process one response and dispatch its instruction only on the owning stream.

    Legacy and non-negotiating modern clients keep their established result
    delivery. A negotiated modern request reserves one instruction until
    FastMCP has accepted its notification; an unavailable or foreign stream
    leaves the instruction pending for the owning session's next request.
    """
    if session.protocol_type is not SessionProtocolType.MCP_2026_07_28:
        return await session.task_manager.process_result(result), False

    if fastmcp_context is None:
        try:
            fastmcp_context = get_context()
        except RuntimeError:
            return await session.task_manager.process_result(result, include_instruction=False), False

    if not _client_negotiated_instruction_delivery(fastmcp_context):
        return await session.task_manager.process_result(result), False

    result = await session.task_manager.process_result(result, include_instruction=False)
    instruction = await session.task_manager.reserve_instruction()
    if instruction is None:
        return result, False

    notification = InstructionDispatchNotification(
        params=InstructionDispatchParams(instruction=instruction.content, tracking_id=instruction.tracking_id)
    )
    try:
        await fastmcp_context.send_notification(cast(Any, notification))
    except Exception as error:
        await session.task_manager.release_instruction(instruction)
        logger.debug("Deferring failed instruction notification: %s", error, exc_info=True)
        return result, False

    await session.task_manager.confirm_instruction(instruction)
    return result, True
