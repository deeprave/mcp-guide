"""Extended MCP tool decorator with logging and prefixing."""

import inspect
import logging
import os
from contextvars import ContextVar
from functools import wraps
from typing import Any, Callable, Optional

from mcp_guide.tools.tool_constants import INSTRUCTION_VALIDATION_ERROR

logger = logging.getLogger(__name__)

# Internal test mode control - not exposed to external manipulation
_test_mode: ContextVar[bool] = ContextVar("tool_test_mode", default=False)


def enable_test_mode() -> None:
    """Enable test mode (for testing only)."""
    _test_mode.set(True)


def disable_test_mode() -> None:
    """Disable test mode."""
    _test_mode.set(False)


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
            if args_class is not None and description is None:
                from mcp_core.tool_arguments import ToolArguments

                final_description = ToolArguments.build_tool_description(func)

            # Determine prefix
            tool_prefix = prefix if prefix is not None else os.environ.get("MCP_TOOL_PREFIX", "")

            # Build tool name
            tool_name = f"{tool_prefix}_{func.__name__}" if tool_prefix else func.__name__

            # Create wrapper that FastMCP will register
            # FastMCP will create schema from wrapper's signature, not original function
            if inspect.iscoroutinefunction(func):

                @wraps(func)
                async def async_wrapper(**kwargs: Any) -> Any:
                    logger.trace(f"Invoking async tool: {tool_name}")  # type: ignore[attr-defined]
                    try:
                        # Transform arguments if args_class provided
                        if args_class is not None:
                            # Extract ctx if present (FastMCP injects it)
                            ctx = kwargs.pop("ctx", None)
                            # kwargs contains the raw arguments from MCP
                            try:
                                typed_args = args_class(**kwargs)
                            except Exception as e:
                                # Catch Pydantic ValidationError during argument transformation
                                # This is defense-in-depth - FastMCP validates first
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
                                    result: Result[Any] = Result.failure(
                                        f"Invalid tool arguments: {len(error_details)} validation error(s)",
                                        error_type="validation_error",
                                        instruction=INSTRUCTION_VALIDATION_ERROR,
                                    )
                                    result.error_data = {"validation_errors": error_details}
                                    logger.error(f"Tool {tool_name} argument validation failed: {error_details}")
                                    return result.to_json_str()
                                # Re-raise non-validation errors
                                raise
                            # Call function with typed args and ctx
                            result = await func(typed_args, ctx)
                        else:
                            result = await func(**kwargs)
                        logger.debug(f"Tool {tool_name} completed successfully")
                        return result
                    except Exception as e:
                        logger.error(f"Tool {tool_name} failed: {e}")
                        raise

                # Copy args_class fields to wrapper signature if provided
                if args_class is not None:
                    # Get the schema from args_class and add fields to wrapper
                    from typing import get_type_hints

                    from pydantic import BaseModel

                    # Get type hints from args_class
                    type_hints = get_type_hints(args_class)
                    params = []
                    # Check if args_class is a BaseModel subclass
                    if issubclass(args_class, BaseModel):
                        for field_name, field_info in args_class.model_fields.items():
                            annotation = type_hints.get(field_name, Any)

                            # Determine default value for signature
                            if field_info.is_required():
                                # Required field - no default
                                default = inspect.Parameter.empty
                            elif field_info.default_factory is not None:
                                # Has default_factory - mark as optional with None
                                # (actual factory will be called by Pydantic during validation)
                                default = None
                            else:
                                # Has explicit default value
                                default = field_info.default

                            params.append(
                                inspect.Parameter(
                                    field_name, inspect.Parameter.KEYWORD_ONLY, default=default, annotation=annotation
                                )
                            )

                        # Update wrapper signature
                        async_wrapper.__signature__ = inspect.Signature(params)  # type: ignore

                wrapped = async_wrapper
            else:
                # Sync tools are not supported - create wrapper that returns error

                @wraps(func)
                def sync_wrapper(**kwargs: Any) -> Any:
                    # Log error when sync tool is actually called
                    logger.error(
                        f"Sync tool {tool_name} called but sync tools are not supported. "
                        "All MCP tools must be async to properly handle Context parameter."
                    )
                    # Return error result immediately
                    from mcp_core.result import Result

                    return Result.failure(
                        "Tool implementation error: synchronous tools are not supported. "
                        "All MCP tools must be async to handle Context parameter.",
                        error_type="sync_tool_not_supported",
                    ).to_json_str()

                wrapped = sync_wrapper

            # Register with FastMCP
            self.mcp.tool(name=tool_name, description=final_description)(wrapped)

            return wrapped

        return decorator
