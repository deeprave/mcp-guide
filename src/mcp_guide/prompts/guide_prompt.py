# See src/mcp_guide/prompts/README.md for prompt documentation standards

"""Guide prompt implementation for direct content access."""

from pathlib import Path
from typing import TYPE_CHECKING, Any, Awaitable, Callable, Coroutine, List, Optional, Protocol, Union

from anyio import Path as AsyncPath

from mcp_guide.commands.formatting import format_args_string
from mcp_guide.config_constants import COMMANDS_DIR
from mcp_guide.core.mcp_log import get_logger
from mcp_guide.core.prompt_decorator import promptfunc
from mcp_guide.discovery.commands import discover_commands
from mcp_guide.discovery.files import FileInfo, discover_category_files
from mcp_guide.feature_flags.types import FeatureValue
from mcp_guide.models import resolve_all_flags
from mcp_guide.prompts.command_parser import parse_command_arguments
from mcp_guide.render import render_template
from mcp_guide.render.cache import get_template_contexts
from mcp_guide.render.context import TemplateContext, convert_lists_to_indexed
from mcp_guide.result import Result
from mcp_guide.result_constants import (
    ERROR_FILE_ERROR,
    ERROR_NOT_FOUND,
    ERROR_TEMPLATE,
    INSTRUCTION_DISPLAY_ONLY,
    INSTRUCTION_FILE_ERROR,
    INSTRUCTION_NOTFOUND_ERROR,
    INSTRUCTION_TEMPLATE_ERROR,
)
from mcp_guide.session import get_current_session, get_or_create_session
from mcp_guide.tools.tool_content import ContentArgs, internal_get_content

if TYPE_CHECKING:
    from typing import Any

    from mcp.server.fastmcp import Context
else:
    try:
        from mcp.server.fastmcp import Context
    except ImportError:
        Context = None  # type: ignore


logger = get_logger(__name__)


class CommandMiddleware(Protocol):
    """Protocol for command middleware."""

    async def __call__(
        self,
        command_path: str,
        kwargs: dict[str, Union[str, bool, int]],
        args: list[str],
        next_handler: Callable[[], Awaitable[Result[str]]],
    ) -> Result[str]:
        """Execute middleware logic."""
        ...


async def get_command_help(command_context: TemplateContext, commands_dir: Path, docroot: Path) -> Result[str]:
    """Get help information for a command using template rendering."""
    from mcp_guide.render.template import render_template

    try:
        # Discover the help command file through the proper discovery system
        help_result = await _discover_command_file(commands_dir, "help")
        if not help_result.success:
            return Result.failure("Help template not found", error_type="not_found")

        help_file_info = help_result.value
        if help_file_info is None:
            return Result.failure("Help template not found", error_type="not_found")

        help_file_info.resolve(commands_dir, docroot)

        # Render using the proper template rendering system
        rendered = await render_template(
            file_info=help_file_info,
            base_dir=help_file_info.path.parent,
            project_flags={},
            context=command_context,
        )

        if rendered is None:
            return Result.failure("Failed to render help template", error_type="render_error")

        return Result.ok(rendered.content, instruction=rendered.instruction)

    except Exception as e:
        return Result.failure(str(e), error_type="context")


# MCP compatibility limit for variable arguments
MAX_PROMPT_ARGS = 15


async def handle_command(
    command_path: str,
    kwargs: dict[str, Union[str, bool, int]],
    args: list[str],
    ctx: Optional[Context],  # type: ignore
    middleware: Optional[List[CommandMiddleware]] = None,
) -> Result[Any]:
    """Handle command execution with direct file discovery.

    Args:
        command_path: Command path (e.g. "help", "create/category")
        kwargs: Parsed keyword arguments and flags
        args: Positional arguments
        ctx: MCP context
        middleware: Optional list of middleware to apply

    Returns:
        Result containing rendered command output or error
    """
    # Add logging middleware by default
    from mcp_guide.middleware.logging_middleware import logging_middleware

    if middleware is None:
        middleware = []
    middleware = [logging_middleware] + middleware
    if middleware:
        # Apply the middleware chain
        async def next_handler() -> Result[Any]:
            return await _execute_command(command_path, kwargs, args, ctx)

        # Build the middleware chain from right to left
        handler: Callable[[], Coroutine[Any, Any, Result[Any]]] = next_handler
        for mw in reversed(middleware):
            # Capture current middleware in closure
            def make_handler(
                middleware_fn: CommandMiddleware, next_fn: Callable[[], Coroutine[Any, Any, Result[Any]]]
            ) -> Callable[[], Coroutine[Any, Any, Result[Any]]]:
                async def wrapper() -> Result[Any]:
                    return await middleware_fn(command_path, kwargs, args, next_fn)

                return wrapper

            handler = make_handler(mw, handler)

        return await handler()
    else:
        return await _execute_command(command_path, kwargs, args, ctx)


def _resolve_command_alias(command_path: str, commands: list[dict[str, Any]]) -> str:
    """Resolve command alias to the actual command name."""
    for cmd in commands:
        if command_path in cmd.get("aliases", []):
            name = cmd.get("name")
            return str(name) if name is not None else command_path
    return command_path


async def _discover_command_file(commands_dir: Path, command_path: str) -> Result[FileInfo]:
    """Discover the command file by path."""
    pattern = f"{command_path}.*"
    try:
        files = await discover_category_files(commands_dir, [pattern])
    except Exception as e:
        return Result.failure(f"Error discovering command files: {e}", error_type="file_error")

    if not files:
        return Result.failure(f"Command not found: {command_path}", error_type="not_found")

    return Result.ok(files[0])


def _build_command_context(
    base_context: TemplateContext,
    command_path: str,
    file_info: FileInfo,
    kwargs: dict[str, Any],
    args: list[str],
    commands: list[dict[str, Any]],
) -> TemplateContext:
    """Build template context for command execution."""

    # Use kwargs directly without underscore manipulation
    template_kwargs = convert_lists_to_indexed(kwargs.copy())

    # If args provided (for help command), look up the requested command
    command_help = None
    if args:
        requested_cmd = args[0] if isinstance(args[0], str) else args[0].get("value")
        for cmd in commands:
            if cmd.get("name") == requested_cmd or requested_cmd in cmd.get("aliases", []):
                command_help = cmd
                break

    # Group commands by category dynamically, filtering out underscore-prefixed commands
    categories: dict[str, list[dict[str, Any]]] = {}
    for cmd in commands:
        # Skip commands in directories starting with underscore
        path_parts = cmd.get("name", "").split("/")
        if any(part.startswith("_") for part in path_parts):
            continue
        category = cmd.get("category", "general")
        if category not in categories:
            categories[category] = []
        categories[category].append(cmd)

    # Convert to a sorted list with title-case names
    command_categories: list[dict[str, Any]] = []
    command_categories.extend(
        {
            "name": category_name,
            "title": category_name.replace("_", " ").title() + " Commands",
            "commands": categories[category_name],
        }
        for category_name in sorted(categories.keys())
    )

    args_string = format_args_string(args)

    context_data = {
        "kwargs": template_kwargs,
        "raw_kwargs": kwargs,
        "args": args,
        "args_str": args_string,
        "command": {"name": command_path, "path": str(file_info.path)},
        "executed_command": command_path,
        "commands": commands,
        "command_categories": command_categories,
    }

    # Add command_help if found
    if command_help:
        context_data["command_help"] = command_help

    return base_context.new_child(convert_lists_to_indexed(context_data))


async def _is_help_command(command_path: str, ctx: Optional[Context]) -> bool:  # type: ignore
    """Check if command_path is a help command or alias."""
    # noinspection PyBroadException
    try:
        session = await get_or_create_session(ctx)
        docroot = Path(await session.get_docroot())
        commands_dir = docroot / COMMANDS_DIR
        commands = await discover_commands(commands_dir)

        # Find help command and its aliases
        help_aliases = ["help"]  # Always include the base name
        for cmd in commands:
            if cmd["name"] == "help":
                help_aliases.extend(cmd.get("aliases", []))
                break

        return command_path in help_aliases
    except Exception:
        # Fallback to hardcoded aliases if discovery fails for any reason
        return command_path in {"help", "h", "?"}


async def _execute_command(
    command_path: str,
    kwargs: dict[str, Union[str, bool, int]],
    args: list[str],
    ctx: Optional[Context],  # type: ignore
) -> Result[Any]:
    """Execute command without middleware."""
    from mcp_guide.session import get_or_create_session

    # Initialise session and get paths
    try:
        session = await get_or_create_session(ctx)
        docroot = Path(await session.get_docroot())
    except ValueError as e:
        return Result.failure(str(e), error_type="context")

    commands_dir = docroot / COMMANDS_DIR
    if not await AsyncPath(commands_dir).exists():
        return Result.failure(f"Commands directory not found: {COMMANDS_DIR}", error_type="not_found")

    # Discover commands and try the direct template file first (higher precedence)
    commands = await discover_commands(commands_dir)

    # First, try to find the command file directly (template files have higher precedence)
    file_result = await _discover_command_file(commands_dir, command_path)

    # If no direct template file found, try alias resolution
    if not file_result.success:
        resolved_path = _resolve_command_alias(command_path, commands)
        if resolved_path != command_path:  # Only retry if alias was found
            file_result = await _discover_command_file(commands_dir, resolved_path)

    # If still no file found, return the error
    if not file_result.success:
        return file_result
    file_info = file_result.value
    if not file_info:
        return Result.failure("No file info returned", error_type="file_error")

    # Set the base path for content loading
    file_info.resolve(commands_dir, docroot)

    # Build template context
    base_context = await get_template_contexts()
    command_context = _build_command_context(base_context, command_path, file_info, kwargs, args, commands)

    # Check for a help flag or help command with args (after context building)
    if kwargs.get("_help"):
        return await get_command_help(command_context, commands_dir, docroot)
    if await _is_help_command(command_path, ctx) and args:
        return await get_command_help(command_context, commands_dir, docroot)

    # Get resolved flags for requires-* checking
    current_session = get_current_session()
    requirements_context: dict[str, FeatureValue] = await resolve_all_flags(current_session)  # type: ignore[arg-type]

    # Render template using new API
    try:
        rendered = await render_template(
            file_info=file_info,
            base_dir=file_info.path.parent,
            project_flags=requirements_context,
            context=command_context,
        )
    except FileNotFoundError as e:
        logger.exception(f"Command file not found: {command_path}")
        return Result.failure(
            f"Command file not found: {e}",
            error_type=ERROR_NOT_FOUND,
            instruction=INSTRUCTION_NOTFOUND_ERROR,
        )
    except PermissionError as e:
        logger.exception(f"Permission denied reading command: {command_path}")
        return Result.failure(
            f"Permission denied for command '{file_info.path}': {e}",
            error_type=ERROR_FILE_ERROR,
            instruction=INSTRUCTION_FILE_ERROR,
        )
    except RuntimeError as e:
        # Template rendering error (syntax, missing variables, etc.)
        logger.exception(f"Template rendering failed for command {command_path}")
        return Result.failure(
            f"Template rendering failed: {e}",
            error_type=ERROR_TEMPLATE,
            instruction=INSTRUCTION_TEMPLATE_ERROR,
        )
    except Exception as e:
        # Unexpected error
        logger.exception(f"Unexpected error rendering command {command_path}")
        return Result.failure(
            f"Unexpected error: {e}",
            error_type=ERROR_FILE_ERROR,
            instruction=INSTRUCTION_FILE_ERROR,
        )

    if rendered is None:
        # File filtered by requires-* - treat as not found
        return Result.failure(
            f"Command '{command_path}' not found",
            error_type=ERROR_NOT_FOUND,
            instruction=INSTRUCTION_NOTFOUND_ERROR,
        )

    # Extract content and instruction from RenderedContent
    result = Result.ok(rendered.content)
    result.instruction = rendered.instruction  # Already has type-based default
    return result


async def _handle_command_request(argv: list[str], ctx: Optional["Context"]) -> Result[Any]:  # type: ignore[type-arg]
    """Handle command-mode request."""
    first_arg = argv[1]
    raw_command_path = first_arg[1:]  # Remove prefix

    if not raw_command_path:
        result: Result[Any] = Result.failure("Command name cannot be empty", error_type="validation")
        result.instruction = INSTRUCTION_DISPLAY_ONLY
        return result

    # Validate and sanitize
    from mcp_guide.commands.security import validate_command_path_full

    error, command_path = validate_command_path_full(raw_command_path)
    if error:
        result = Result.failure(f"Security validation failed: {error}", error_type="security")
        result.instruction = INSTRUCTION_DISPLAY_ONLY
        return result

    # Parse arguments
    kwargs, args, parse_errors = parse_command_arguments(argv[1:])
    if parse_errors:
        error_msg = "; ".join(parse_errors)
        result = Result.failure(f"Argument parsing failed: {error_msg}", error_type="validation")
        result.instruction = INSTRUCTION_DISPLAY_ONLY
        return result

    # Validate context
    if ctx is None:
        result = Result.failure("Context is required for command execution", error_type="validation")
        result.instruction = INSTRUCTION_DISPLAY_ONLY
        return result

    return await handle_command(command_path, kwargs, args, ctx)


async def _handle_content_request(argv: list[str], ctx: Optional["Context"]) -> Result[Any]:  # type: ignore[type-arg]
    """Handle content-mode request."""
    # Separate flags from content arguments
    content_args = []
    flags = []

    for arg in argv[1:]:
        if arg.startswith("-"):
            flags.append(arg)
        else:
            content_args.append(arg)

    # Parse flags only
    kwargs, _, parse_errors = parse_command_arguments(flags)
    if parse_errors:
        error_msg = "; ".join(parse_errors)
        result: Result[str] = Result.failure(f"Flag parsing failed: {error_msg}", error_type="validation")
        result.instruction = INSTRUCTION_DISPLAY_ONLY
        return result

    # Join content args as the category expression
    category = ",".join(content_args) if content_args else ""

    # Handle --help flag for content requests
    if kwargs.get("help"):
        help_text = """# Content Help

Usage: @guide <category|collection>

Examples:
  @guide docs                    # Get docs category content
  @guide code-review             # Get code-review collection content
  @guide docs,examples           # Get multiple categories with default patterns
"""
        result = Result.ok(help_text)
        result.instruction = INSTRUCTION_DISPLAY_ONLY
        return result

    # Create content args with pattern support
    pattern = kwargs.get("pattern")
    if isinstance(pattern, int):
        pattern = str(pattern)
    content_args_obj = ContentArgs(expression=category, pattern=pattern)
    return await internal_get_content(content_args_obj, ctx)


async def _route_guide_request(argv: list[str], ctx: Optional["Context"]) -> Result[Any]:  # type: ignore[type-arg]
    """Route guide request to command or content handler."""
    # Validate arguments
    if len(argv) == 1 or (len(argv) == 2 and argv[1] == ""):
        # Get prompt prefix from cached agent info
        from mcp_guide.mcp_context import cached_mcp_context

        prompt_prefix = "@"  # Default
        cached = cached_mcp_context.get()
        if cached and cached.agent_info:
            prompt_prefix = cached.agent_info.prompt_prefix.replace("{mcp_name}", "guide")

        error_msg = f"The guide prompt requires one or more arguments. Use {prompt_prefix}guide :help to list commands"
        result: Result[Any] = Result.failure(error_msg, error_type="validation")
        result.instruction = INSTRUCTION_DISPLAY_ONLY
        return result

    # Check for command prefix
    first_arg = argv[1]
    if first_arg.startswith(":") or first_arg.startswith(";"):
        return await _handle_command_request(argv, ctx)
    else:
        return await _handle_content_request(argv, ctx)


@promptfunc()
async def guide(
    # MCP prompt handlers require explicit parameters - *args not supported
    # MAX_PROMPT_ARGS defined to match the MCP protocol limit
    arg1: Optional[str] = None,
    arg2: Optional[str] = None,
    arg3: Optional[str] = None,
    arg4: Optional[str] = None,
    arg5: Optional[str] = None,
    arg6: Optional[str] = None,
    arg7: Optional[str] = None,
    arg8: Optional[str] = None,
    arg9: Optional[str] = None,
    arga: Optional[str] = None,
    argb: Optional[str] = None,
    argc: Optional[str] = None,
    argd: Optional[str] = None,
    arge: Optional[str] = None,
    argf: Optional[str] = None,
    ctx: Optional["Context"] = None,  # type: ignore[type-arg]
) -> str:
    """Access guide functionality.

    Args:
        arg1: positional arg
        arg2: positional arg
        arg3: positional arg
        arg4: positional arg
        arg5: positional arg
        arg6: positional arg
        arg7: positional arg
        arg8: positional arg
        arg9: positional arg
        arga: positional arg
        argb: positional arg
        argc: positional arg
        argd: positional arg
        arge: positional arg
        argf: positional arg
        ctx (Optional["Context"]):
    """
    # Cache MCP context if available
    if ctx:
        from mcp_guide.mcp_context import cache_mcp_globals

        logger.debug("Caching MCP context for guide request")
        # noinspection PyTypeChecker
        await cache_mcp_globals(ctx)

    # Call on_tool for all subscribers immediately
    from mcp_guide.task_manager import get_task_manager

    task_manager = get_task_manager()
    try:
        await task_manager.on_tool()
    except Exception as e:
        logger.error(f"on_tool failed at prompt start: {e}")

    # Build argv list (MCP protocol requirement)
    argv = ["guide"]
    for arg in [arg1, arg2, arg3, arg4, arg5, arg6, arg7, arg8, arg9, arga, argb, argc, argd, arge, argf]:
        if arg is None:
            break
        argv.append(arg)

    # Route request
    result = await _route_guide_request(argv, ctx)

    # Process result through the task manager
    from mcp_guide.tools.tool_result import prompt_result

    return await prompt_result("guide", result)
