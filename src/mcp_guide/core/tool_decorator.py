"""Extended MCP tool decorator with logging and prefixing."""

import inspect
import json
import os
import weakref
from contextlib import asynccontextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from functools import cache, wraps
from typing import TYPE_CHECKING, Any, Callable, Coroutine, Optional

from fastmcp.tools.base import ToolResult
from mcp_types import TextContent

from mcp_guide.core.mcp_log import get_logger
from mcp_guide.core.result import Result as CoreResult
from mcp_guide.mcp_result_adapter import add_session_continuation, tool_response
from mcp_guide.result import Result
from mcp_guide.result_constants import (
    ERROR_INVALID_NAME,
    ERROR_VALIDATION,
    INSTRUCTION_VALIDATION_ERROR,
    RESULT_NO_PROJECT,
    make_invalid_session_result,
    make_no_project_result,
)
from mcp_guide.runtime import OwnerKey
from mcp_guide.session import InvalidGuideSessionError, get_session
from mcp_guide.validation import InvalidProjectNameError

if TYPE_CHECKING:
    from mcp_guide.session import Session

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
_REGISTERED_TOOL_SERVERS: dict[int, weakref.ReferenceType[Any]] = {}


@cache
def get_tool_prefix() -> str:
    """Get the tool prefix from environment variable.

    Returns:
        Tool prefix with trailing underscore if non-blank, empty string if blank.
        Uses empty string as default if MCP_TOOL_PREFIX is not set.
    """
    tool_prefix = os.environ.get("MCP_TOOL_PREFIX", "")
    return f"{tool_prefix}_" if tool_prefix else ""


def enable_test_mode() -> None:
    """Enable test mode (for testing only)."""
    _test_mode.set(True)


def disable_test_mode() -> None:
    """Disable test mode."""
    _test_mode.set(False)


async def _call_on_tool(tool_name: str, ctx: Optional[Any] = None, session_id: str | None = None) -> Any:
    """Call TaskManager.on_tool() at tool invocation start.

    Note: This handles tool START events. Tool END events and result processing
    are handled by tool_result() in tools/tool_result.py.

    Args:
        tool_name: Name of the tool being invoked
    """
    try:
        if session_id is None:
            session = await get_session(ctx)
        else:
            session = await get_session(ctx, session_id=session_id)
        task_manager = session.task_manager
        logger.trace(f"Calling on_tool at start of {tool_name}")
        await task_manager.on_tool()
        return session
    except InvalidGuideSessionError:
        raise
    except InvalidProjectNameError:
        raise
    except Exception as e:
        logger.error(f"on_tool execution failed at start of {tool_name}: {e}")
        return None


async def _check_project_bound(ctx: Optional[Any], session_id: str | None = None) -> Optional[object]:
    """Return a native no-project response if the session is unbound."""
    # In direct unit calls (no FastMCP context), bypass this boundary so tests can call
    # decorators without needing a synthetic active session.
    if ctx is None and session_id is None:
        return None

    try:
        if session_id is None:
            session = await get_session(ctx)
        else:
            session = await get_session(ctx, session_id=session_id)
    except InvalidGuideSessionError:
        return tool_response(make_invalid_session_result())
    except InvalidProjectNameError as error:
        return tool_response(Result.failure(str(error), error_type=ERROR_INVALID_NAME))
    except ValueError:
        return tool_response(RESULT_NO_PROJECT)

    if not session.project_is_bound:
        return tool_response(await make_no_project_result())

    return None


@asynccontextmanager
async def _request_session_lease(ctx: Optional[Any], session_id: str | None = None):
    """Protect a resolved runtime Session for the remainder of a tool call."""
    if ctx is None:
        yield
        return

    from mcp_guide.mcp_context import request_context_from_fastmcp, runtime_from_fastmcp

    runtime = runtime_from_fastmcp(ctx)
    if runtime is None:
        yield
        return
    request_context = request_context_from_fastmcp(ctx, session_id=session_id)
    owner: OwnerKey | None = request_context.owner if request_context.session_source is not None else None
    if (
        owner is None
        and request_context.protocol_revision == "2026-07-28"
        and getattr(ctx, "transport", None) == "stdio"
    ):
        connection_id = getattr(ctx, "session_id", None)
        if isinstance(connection_id, str) and connection_id:
            owner = OwnerKey(f"stdio:{connection_id}")
    if owner is None:
        yield
        return
    async with runtime.session_lease(owner):
        yield


async def _normalize_tool_output(
    result: object,
    tool_name: str,
    session_id: str | None = None,
    *,
    session: "Session | None" = None,
) -> ToolResult:
    """Return a native FastMCP tool result without flattening its semantics."""
    if isinstance(result, Result):
        from mcp_guide.tools.tool_result import tool_result

        return await tool_result(tool_name, result, session=session, session_id=session_id)

    if isinstance(result, ToolResult):
        payload = result.structured_content
        if session_id is not None and not result.is_error and isinstance(payload, dict):
            payload = add_session_continuation(payload, session_id)
            return ToolResult(
                content=[TextContent(type="text", text=json.dumps(payload))],
                structured_content=payload,
                meta=result.meta,
                is_error=False,
            )
        return result

    raise TypeError(f"Tool {tool_name} returned unsupported result type: {type(result).__name__}")


def toolfunc(
    args_class: Optional[type] = None,
    description: Optional[str] = None,
    prefix: Optional[str] = None,
    requires_project: bool = True,
    binds_project: bool = False,
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
            raise TypeError(f"Tool {func.__name__} must be async")  # ty: ignore[unresolved-attribute]

        # Auto-generate description
        final_description = description
        if args_class is not None and description is None and hasattr(args_class, "build_description"):
            final_description = args_class.build_description(func)  # ty: ignore[call-non-callable]

        # Determine prefix and tool name
        tool_prefix = prefix if prefix is not None else get_tool_prefix().rstrip("_")
        tool_name = f"{tool_prefix}_{func.__name__}" if tool_prefix else func.__name__  # ty: ignore[unresolved-attribute]

        # Create wrapped function with logging/validation
        wrapped: Callable[..., Coroutine[Any, Any, object]]
        if args_class is not None:

            @wraps(func)
            async def async_wrapper(args: Any, ctx: Optional[Any] = None) -> object:
                logger.debug(f"Invoking async tool: {tool_name}")
                # Project binding mints its modern FastMCP session inside the
                # implementation.  Starting task interception here would
                # otherwise allocate a transient unbound Guide Session first.
                session = None
                if not binds_project:
                    try:
                        session = await _call_on_tool(tool_name, ctx, getattr(args, "session_id", None))
                    except InvalidGuideSessionError:
                        return tool_response(make_invalid_session_result())
                    except InvalidProjectNameError as error:
                        return tool_response(Result.failure(str(error), error_type=ERROR_INVALID_NAME))
                    if (
                        hasattr(args, "session_id")
                        and getattr(args, "session_id", None) is None
                        and session is not None
                    ):
                        args.session_id = getattr(session, "session_id", None)
                if requires_project:
                    unbound = await _check_project_bound(ctx, getattr(args, "session_id", None))
                    if unbound is not None:
                        return unbound
                from mcp_guide.tools.tool_result import bind_tool_session, reset_tool_session

                session_token = bind_tool_session(session)
                try:
                    async with _request_session_lease(ctx, getattr(args, "session_id", None)):
                        result = await func(args, ctx)
                    # Existing Guide tools use ``tool_result`` themselves.
                    # Accepting an internal Result here lets newly migrated
                    # tools use the same native SDK boundary without a second
                    # serialization convention.

                    return await _normalize_tool_output(
                        result, tool_name, getattr(args, "session_id", None), session=session
                    )
                except Exception as e:
                    from pydantic import ValidationError as PydanticValidationError

                    if isinstance(e, PydanticValidationError):
                        error_details = [
                            {"field": str(err["loc"][0]) if err["loc"] else "unknown", "message": err["msg"]}
                            for err in e.errors()
                        ]
                        error_result: CoreResult[Any] = CoreResult.failure(
                            f"Invalid tool arguments: {len(error_details)} validation error(s)",
                            error_type=ERROR_VALIDATION,
                            instruction=INSTRUCTION_VALIDATION_ERROR,
                        )
                        error_result.error_data = {"validation_errors": error_details}
                        logger.error(f"Tool {tool_name} argument validation failed: {error_details}")
                        return tool_response(error_result)
                    logger.error(f"Tool {tool_name} failed: {e}")
                    raise
                finally:
                    reset_tool_session(session_token)

            wrapped = async_wrapper
        else:

            @wraps(func)
            async def async_wrapper_no_args(ctx: Optional[Any] = None) -> object:
                logger.debug(f"Invoking async tool: {tool_name}")
                session = None
                try:
                    session = await _call_on_tool(tool_name, ctx)
                except InvalidGuideSessionError:
                    return tool_response(make_invalid_session_result())
                except InvalidProjectNameError as error:
                    return tool_response(Result.failure(str(error), error_type=ERROR_INVALID_NAME))
                if requires_project:
                    unbound = await _check_project_bound(ctx)
                    if unbound is not None:
                        return unbound
                from mcp_guide.tools.tool_result import bind_tool_session, reset_tool_session

                session_token = bind_tool_session(session)
                try:
                    async with _request_session_lease(ctx):
                        result = await func(ctx=ctx)
                    return await _normalize_tool_output(result, tool_name, session=session)
                except Exception as e:
                    logger.error(f"Tool {tool_name} failed: {e}")
                    raise
                finally:
                    reset_tool_session(session_token)

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

        return wrapped

    return decorator


def register_tools(mcp: Any) -> None:
    """Register all tools with MCP server (idempotent).

    Imports tool modules to trigger decorators, then registers all tools.

    Args:
        mcp: FastMCP instance
    """
    # Import tools package to trigger all @toolfunc decorators.  A cleared
    # registry can coexist with already-imported child modules (for example,
    # after an isolated test reset), so reload those children rather than only
    # the package facade: importing an already-loaded child would not run its
    # decorators again.
    # A partially populated registry is just as unsafe as an empty one.  Test
    # isolation and import ordering can leave early tool modules registered
    # while later ones have been cleared; a production server must still expose
    # the complete built-in surface, including the required project-binding
    # tool.
    if "set_project" not in _TOOL_REGISTRY:
        import importlib
        import sys

        import mcp_guide.tools  # noqa: F401

        for module_name in (
            "tool_category",
            "tool_collection",
            "tool_content",
            "tool_discovery",
            "tool_document",
            "tool_document_update",
            "tool_feature_flags",
            "tool_filesystem",
            "tool_project",
            "tool_resource",
            "tool_update",
            "tool_utility",
        ):
            qualified_name = f"mcp_guide.tools.{module_name}"
            if module := sys.modules.get(qualified_name):
                importlib.reload(module)

    import mcp_guide.tools  # noqa: F401

    server_id = id(mcp)
    registered_server = _REGISTERED_TOOL_SERVERS.get(server_id)
    if registered_server is not None and registered_server() is mcp:
        logger.trace("Tools already registered for this server, skipping")
        return

    for tool_name, registration in _TOOL_REGISTRY.items():
        mcp.tool(name=tool_name, description=registration.metadata.description)(registration.metadata.wrapped_func)
        registration.registered = True
        logger.debug(f"Registered tool: {tool_name}")

    def remove_released_server(reference: weakref.ReferenceType[Any]) -> None:
        if _REGISTERED_TOOL_SERVERS.get(server_id) is reference:
            _REGISTERED_TOOL_SERVERS.pop(server_id, None)

    _REGISTERED_TOOL_SERVERS[server_id] = weakref.ref(mcp, remove_released_server)


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
    _REGISTERED_TOOL_SERVERS.clear()


def clear_registered_tool_servers(server: Any | None = None) -> None:
    """Clear registration state for one or all runtime servers.

    Args:
        server: If provided, clear only this server's registration marker. If None,
            clear all server registration markers.
    """
    if server is None:
        _REGISTERED_TOOL_SERVERS.clear()
        return

    server_id = server if isinstance(server, int) else id(server)
    _REGISTERED_TOOL_SERVERS.pop(server_id, None)


def get_tool_registration(name: str) -> Optional[ToolRegistration]:
    """Get a specific tool registration by name.

    Args:
        name: Tool name to look up

    Returns:
        ToolRegistration if found, None otherwise
    """
    return _TOOL_REGISTRY.get(name)
