"""Extended MCP tool decorator with logging and prefixing."""

import inspect
import os
from contextvars import ContextVar
from dataclasses import dataclass
from functools import cache, wraps
from typing import TYPE_CHECKING, Any, Callable, Coroutine, Optional, Union

from mcp_guide.core.mcp_log import get_logger
from mcp_guide.result_constants import INSTRUCTION_VALIDATION_ERROR
from mcp_guide.task_manager.manager import get_task_manager

if TYPE_CHECKING:
    pass

try:
    from mcp.server.fastmcp import Context
except ImportError:
    Context = None  # type: ignore

logger = get_logger(__name__)


# Internal test mode control - not exposed to external manipulation
_test_mode: ContextVar[bool] = ContextVar("tool_test_mode", default=False)


# Deferred registration infrastructure
@dataclass
class ToolMetadata:
    """Metadata for a tool function."""

    name: str
    func: Callable[..., Any]
    description: Optional[str]
    args_class: Optional[type]
    prefix: Optional[str]
    wrapped_func: Callable[..., Any]


@dataclass
class ToolRegistration:
    """Registration tracking for a tool."""

    metadata: ToolMetadata
    registered: bool = False


_TOOL_REGISTRY: dict[str, ToolRegistration] = {}


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


async def _call_on_tool(tool_name: str) -> None:
    """Call TaskManager.on_tool() at tool invocation start.

    Note: This handles tool START events. Tool END events and result processing
    are handled by tool_result() in tools/tool_result.py.

    Args:
        tool_name: Name of the tool being invoked
    """
    task_manager = get_task_manager()
    try:
        logger.trace(f"Calling on_tool at start of {tool_name}")
        await task_manager.on_tool()
    except Exception as e:
        logger.error(f"on_tool execution failed at start of {tool_name}: {e}")


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

                        # Call on_tool at start of tool invocation
                        await _call_on_tool(tool_name)

                        try:
                            # FastMCP validates and constructs args, we just pass it through
                            result = await func(args, ctx)
                            logger.debug(f"Tool {tool_name} completed successfully")
                            return result  # type: ignore[no-any-return]
                        except Exception as e:
                            # Defense-in-depth: catch validation errors that might slip through
                            from pydantic import ValidationError as PydanticValidationError

                            if isinstance(e, PydanticValidationError):
                                from mcp_guide.core.result import Result

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
                                return error_result.to_json_str()

                            logger.error(f"Tool {tool_name} failed: {e}")
                            raise
                else:
                    # No args_class - use explicit ctx parameter
                    @wraps(func)
                    async def async_wrapper(ctx: Optional[Any] = None) -> str:  # Always str for FastMCP
                        logger.debug(f"Invoking async tool: {tool_name}")

                        # Call on_tool at start of tool invocation
                        await _call_on_tool(tool_name)

                        try:
                            result = await func(ctx=ctx)
                            logger.debug(f"Tool {tool_name} completed successfully")
                            return result  # type: ignore[no-any-return]
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


def toolfunc(
    args_class: Optional[type] = None,
    description: Optional[str] = None,
    prefix: Optional[str] = None,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Decorator for deferred tool registration.

    Stores tool metadata without registering with MCP. Registration happens
    later via register_tools().

    Args:
        args_class: ToolArguments subclass
        description: Tool description
        prefix: Tool name prefix

    Returns:
        Decorator function
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        if _test_mode.get():
            return func

        if not inspect.iscoroutinefunction(func):
            raise TypeError(f"Tool {func.__name__} must be async")

        # Auto-generate description
        final_description = description
        if args_class is not None and description is None and hasattr(args_class, "build_description"):
            final_description = args_class.build_description(func)

        # Determine prefix and tool name
        tool_prefix = prefix if prefix is not None else get_tool_prefix().rstrip("_")
        tool_name = f"{tool_prefix}_{func.__name__}" if tool_prefix else func.__name__

        # Create wrapped function with logging/validation
        wrapped: Callable[..., Coroutine[Any, Any, str]]
        if args_class is not None:

            @wraps(func)
            async def async_wrapper(args: Any, ctx: Optional[Any] = None) -> str:
                logger.debug(f"Invoking async tool: {tool_name}")
                await _call_on_tool(tool_name)
                try:
                    result = await func(args, ctx)
                    logger.debug(f"Tool {tool_name} completed successfully")
                    return result  # type: ignore[no-any-return]
                except Exception as e:
                    from pydantic import ValidationError as PydanticValidationError

                    if isinstance(e, PydanticValidationError):
                        from mcp_guide.core.result import Result

                        error_details = [
                            {"field": str(err["loc"][0]) if err["loc"] else "unknown", "message": err["msg"]}
                            for err in e.errors()
                        ]
                        error_result: Result[Any] = Result.failure(
                            f"Invalid tool arguments: {len(error_details)} validation error(s)",
                            error_type="validation_error",
                            instruction=INSTRUCTION_VALIDATION_ERROR,
                        )
                        error_result.error_data = {"validation_errors": error_details}
                        logger.error(f"Tool {tool_name} argument validation failed: {error_details}")
                        return error_result.to_json_str()
                    logger.error(f"Tool {tool_name} failed: {e}")
                    raise

            wrapped = async_wrapper
        else:

            @wraps(func)
            async def async_wrapper_no_args(ctx: Optional[Any] = None) -> str:
                logger.debug(f"Invoking async tool: {tool_name}")
                await _call_on_tool(tool_name)
                try:
                    result = await func(ctx=ctx)
                    logger.debug(f"Tool {tool_name} completed successfully")
                    return result  # type: ignore[no-any-return]
                except Exception as e:
                    logger.error(f"Tool {tool_name} failed: {e}")
                    raise

            wrapped = async_wrapper_no_args

        # Store in registry
        metadata = ToolMetadata(
            name=tool_name,
            func=func,
            description=final_description,
            args_class=args_class,
            prefix=tool_prefix,
            wrapped_func=wrapped,
        )
        _TOOL_REGISTRY[tool_name] = ToolRegistration(metadata=metadata)
        logger.trace(f"Tool {tool_name} added to registry (not yet registered)")

        return func

    return decorator


def register_tools(mcp: Any) -> None:
    """Register all tools with MCP server (idempotent).

    Args:
        mcp: FastMCP instance
    """
    for tool_name, registration in _TOOL_REGISTRY.items():
        if not registration.registered:
            mcp.tool(name=tool_name, description=registration.metadata.description)(registration.metadata.wrapped_func)
            registration.registered = True
            logger.debug(f"Registered tool: {tool_name}")
        else:
            logger.trace(f"Tool {tool_name} already registered, skipping")


def get_tool_registry() -> dict[str, ToolRegistration]:
    """Get a copy of the tool registry.

    Returns:
        Frozen copy of tool registry for introspection
    """
    from copy import deepcopy

    return deepcopy(_TOOL_REGISTRY)


def clear_tool_registry() -> None:
    """Clear all tools from the registry.

    Used primarily for testing to reset registration state.
    """
    _TOOL_REGISTRY.clear()


def get_tool_registration(name: str) -> Optional[ToolRegistration]:
    """Get a specific tool registration by name.

    Args:
        name: Tool name to look up

    Returns:
        ToolRegistration if found, None otherwise
    """
    return _TOOL_REGISTRY.get(name)
