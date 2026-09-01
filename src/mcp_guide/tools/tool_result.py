"""Process Guide results before returning SDK-native MCP responses."""

from contextvars import ContextVar, Token
from typing import TYPE_CHECKING, TypeVar

from fastmcp.prompts import PromptResult
from fastmcp.tools.base import ToolResult

from mcp_guide.core.mcp_log import get_logger
from mcp_guide.mcp_result_adapter import prompt_response, tool_response

if TYPE_CHECKING:
    from fastmcp import Context

    from mcp_guide.result import Result
    from mcp_guide.session import Session

logger = get_logger(__name__)

T = TypeVar("T")

_resolved_tool_session: ContextVar["Session | None"] = ContextVar("guide_resolved_tool_session", default=None)


def bind_tool_session(session: "Session | None") -> Token["Session | None"]:
    """Record the Session already resolved for this tool invocation."""
    return _resolved_tool_session.set(session)


def reset_tool_session(token: Token["Session | None"]) -> None:
    """Clear the tool-invocation Session binding."""
    _resolved_tool_session.reset(token)


def parse_options(options: list[str]) -> dict[str, str | bool]:
    """Convert a list of display options into a template context dict.

    Supports truthy flags and key=value pairs for flexible template rendering.

    Args:
        options: List of option strings, e.g. ["verbose", "limit=10"]

    Returns:
        Dict mapping option names to True (flags) or string values (key=value pairs)
    """
    parsed: dict[str, str | bool] = {}
    for opt in options:
        if "=" in opt:
            key, value = opt.split("=", 1)
            parsed[key] = value
        else:
            parsed[opt] = True
    return parsed


async def tool_result(
    tool_name: str,
    result: "Result[T]",
    *,
    ctx: "Context | None" = None,
    session: "Session | None" = None,
    session_id: str | None = None,
) -> ToolResult:
    """Process and log a tool result before returning a native MCP response.

    This function handles result processing that must occur before FastMCP's
    SDK response adaptation. It:
    1. Processes the result through TaskManager
    2. Logs the result at TRACE level for debugging
    3. Preserves Guide fields in FastMCP structured content and MCP metadata

    Args:
        tool_name: Name of the tool that produced the result
        result: Result object to process and convert

    Returns:
        FastMCP-native structured tool result

    Example:
        >>> result = Result.ok(value={"data": "example"})
        >>> return await tool_result("my_tool", result)
    """
    resolved = session if session is not None else _resolved_tool_session.get()
    try:
        if resolved is None and ctx is not None and session_id is not None:
            from mcp_guide.session import get_session

            resolved = await get_session(ctx, session_id=session_id)
        if resolved is not None:
            result = await resolved.task_manager.process_result(result)
    except Exception as e:
        logger.error(f"TaskManager processing failed for tool {tool_name}: {e}")

    logger.trace(f"Tool '{tool_name}' result: {result.to_json()}")

    continuation_id = session_id if session_id is not None else (resolved.session_id if resolved is not None else None)
    return tool_response(result, session_id=continuation_id)


async def prompt_result(
    prompt_name: str,
    result: "Result[T]",
    *,
    session: "Session | None" = None,
    session_id: str | None = None,
) -> PromptResult:
    """Process and log a prompt result before returning a native MCP response.

    This function handles result processing that must occur before FastMCP's
    SDK response adaptation. It:
    1. Processes the result through TaskManager
    2. Logs the result at TRACE level for debugging
    3. Preserves the Guide payload in a native FastMCP prompt response

    Args:
        prompt_name: Name of the prompt that produced the result
        result: Result object to process and convert

    Returns:
        FastMCP-native prompt result

    Example:
        >>> result = Result.ok(value={"data": "example"})
        >>> return await prompt_result("my_prompt", result)
    """
    try:
        if session is not None:
            result = await session.task_manager.process_result(result)
    except Exception as e:
        logger.error(f"TaskManager processing failed for prompt {prompt_name}: {e}")

    logger.trace(f"Prompt '{prompt_name}' result: {result.to_json()}")

    return prompt_response(result, session_id=session_id)
