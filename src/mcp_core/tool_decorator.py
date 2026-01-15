"""Extended MCP tool decorator with logging and prefixing."""

import inspect
import os
from contextvars import ContextVar
from functools import cache, wraps
from typing import TYPE_CHECKING, Any, Callable, Coroutine, Optional, Union

if TYPE_CHECKING:
    from mcp_guide.task_manager import TaskManager

from mcp_core.mcp_log import get_logger
from mcp_core.result import Result
from mcp_guide.result_constants import INSTRUCTION_VALIDATION_ERROR

try:
    from mcp.server.fastmcp import Context
except ImportError:
    Context = None  # type: ignore

logger = get_logger(__name__)


def _log_tool_result(tool_name: str, result: Any) -> None:
    """Log tool result for debugging."""
    if isinstance(result, Result):
        logger.trace(
            f"RESULT: Tool {tool_name} returning result",
            extra={"message": "Returning result", "result": result.to_json()},
        )


# Internal test mode control - not exposed to external manipulation
_test_mode: ContextVar[bool] = ContextVar("tool_test_mode", default=False)

# Global TaskManager instance for result processing
_task_manager: Optional["TaskManager"] = None


@cache
def get_tool_prefix() -> str:
    """Get the tool prefix from environment variable.

    Returns:
        Tool prefix with trailing underscore if non-blank, empty string if blank.
        Uses "guide" as default if MCP_TOOL_PREFIX is not set.
    """
    tool_prefix = os.environ.get("MCP_TOOL_PREFIX", "guide")
    return f"{tool_prefix}_" if tool_prefix else ""


def enable_test_mode() -> None:
    """Enable test mode (for testing only)."""
    _test_mode.set(True)


def disable_test_mode() -> None:
    """Disable test mode."""
    _test_mode.set(False)


def set_task_manager(task_manager: Optional["TaskManager"]) -> None:
    """Set the global TaskManager instance for result processing.

    Args:
        task_manager: TaskManager instance or None to clear
    """
    global _task_manager
    _task_manager = task_manager


async def _process_tool_result(result: Any, tool_name: str) -> Any:
    """Process tool result through TaskManager and convert to JSON."""
    # Call on_tool immediately
    if _task_manager is not None:
        try:
            logger.trace(f"Calling on_tool at start of {tool_name}")
            await _task_manager.on_tool()
        except Exception as e:
            logger.error(f"on_tool execution failed at start of {tool_name}: {e}")

    # If result is already a JSON string, return as-is
    if isinstance(result, str):
        return result

    # If result is a Result object, process it
    if isinstance(result, Result):
        # Process through TaskManager if available
        if _task_manager is not None:
            try:
                result = await _task_manager.process_result(result)
            except Exception as e:
                logger.error(f"TaskManager processing failed for tool {tool_name}: {e}")

        # Log final result and convert to JSON string
        _log_tool_result(tool_name, result)
        return result.to_json_str()

    # For other types, return as-is (shouldn't happen in normal operation)
    return result


class ExtMcpToolDecorator:
    """Extended MCP tool decorator with logging and prefix support.

    Features:
    - Reads MCP_TOOL_PREFIX from environment
    - Per-tool prefix override
    - TRACE/DEBUG/ERROR logging
    - Exception re-raising after logging
    """

    def __init__(self, mcp: Any):
        """Initialize decorator.

        Args:
            mcp: FastMCP instance
        """
        self.mcp = mcp

    def tool(
        self,
        args_class: Optional[type] = None,
        description: Optional[str] = None,
        prefix: Optional[str] = None,
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        """Decorate a tool function with logging and prefixing.

        Args:
            args_class: ToolArguments subclass (auto-generates description)
            description: Tool description (overrides auto-generation)
            prefix: Tool name prefix (overrides MCP_TOOL_PREFIX)

        Returns:
            Decorator function
        """

        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            # In test mode, return function unchanged
            if _test_mode.get():
                return func

            # Auto-generate description from args_class if provided
            final_description = description
            if args_class is not None and description is None and hasattr(args_class, "build_description"):
                final_description = args_class.build_description(func)

            # Determine prefix
            tool_prefix = prefix if prefix is not None else get_tool_prefix().rstrip("_")

            # Build tool name
            tool_name = f"{tool_prefix}_{func.__name__}" if tool_prefix else func.__name__

            # Create wrapper that FastMCP will register
            # FastMCP will create schema from wrapper's signature
            wrapped: Union[Callable[..., Coroutine[Any, Any, Any]], Callable[..., Any]]
            if inspect.iscoroutinefunction(func):
                if args_class is not None:
                    # Use Pydantic model as single parameter to preserve Field descriptions
                    @wraps(func)
                    async def async_wrapper(args: Any, ctx: Optional[Any] = None) -> str:  # Always str for FastMCP
                        logger.debug(f"Invoking async tool: {tool_name}")

                        try:
                            # FastMCP validates and constructs args, we just pass it through
                            result = await func(args, ctx)
                            logger.debug(f"Tool {tool_name} completed successfully")
                            return await _process_tool_result(result, tool_name)  # type: ignore[no-any-return]
                        except Exception as e:
                            # Defense-in-depth: catch validation errors that might slip through
                            from pydantic import ValidationError as PydanticValidationError

                            if isinstance(e, PydanticValidationError):
                                from mcp_core.result import Result

                                error_details = [
                                    {
                                        "field": str(err["loc"][0]) if err["loc"] else "unknown",
                                        "message": err["msg"],
                                    }
                                    for err in e.errors()
                                ]
                                error_result: Result[Any] = Result.failure(
                                    f"Invalid tool arguments: {len(error_details)} validation error(s)",
                                    error_type="validation_error",
                                    instruction=INSTRUCTION_VALIDATION_ERROR,
                                )
                                error_result.error_data = {"validation_errors": error_details}
                                logger.error(f"Tool {tool_name} argument validation failed: {error_details}")
                                return await _process_tool_result(error_result, tool_name)  # type: ignore[no-any-return]

                            logger.error(f"Tool {tool_name} failed: {e}")
                            raise
                else:
                    # No args_class - use explicit ctx parameter
                    @wraps(func)
                    async def async_wrapper(ctx: Optional[Any] = None) -> str:  # Always str for FastMCP
                        logger.debug(f"Invoking async tool: {tool_name}")
                        try:
                            result = await func(ctx=ctx)
                            logger.debug(f"Tool {tool_name} completed successfully")
                            return await _process_tool_result(result, tool_name)  # type: ignore[no-any-return]
                        except Exception as e:
                            logger.error(f"Tool {tool_name} failed: {e}")
                            raise

                wrapped = async_wrapper
            else:
                # Synchronous function - not supported in async-first architecture
                raise TypeError(
                    f"Tool {tool_name} must be async. Synchronous tools are not supported in async-first architecture."
                )

            # Register with FastMCP
            self.mcp.tool(name=tool_name, description=final_description)(wrapped)

            return wrapped

        return decorator
