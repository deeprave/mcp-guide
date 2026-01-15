# See src/mcp_guide/prompts/README.md for prompt documentation standards

"""Guide prompt implementation for direct content access."""

from pathlib import Path
from typing import TYPE_CHECKING, Any, Awaitable, Callable, Coroutine, List, Optional, Protocol, Union

from anyio import Path as AsyncPath

from mcp_core.mcp_log import get_logger
from mcp_guide.config_constants import COMMANDS_DIR
from mcp_guide.prompts.command_parser import parse_command_arguments
from mcp_guide.result import Result
from mcp_guide.result_constants import INSTRUCTION_DISPLAY_ONLY
from mcp_guide.server import mcp
from mcp_guide.session import get_or_create_session
from mcp_guide.tools.tool_content import ContentArgs, internal_get_content
from mcp_guide.utils.command_discovery import discover_commands
from mcp_guide.utils.command_formatting import format_args_string
from mcp_guide.utils.file_discovery import FileInfo, discover_category_files
from mcp_guide.utils.frontmatter import (
    get_frontmatter_type,
    get_type_based_default_instruction,
)
from mcp_guide.utils.template_context import TemplateContext, convert_lists_to_indexed
from mcp_guide.utils.template_context_cache import get_template_contexts
from mcp_guide.utils.template_renderer import render_file_content, render_template_content

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


async def get_command_help(command_path: str, command_context: dict, ctx: Optional[Context]) -> Result[str]:  # type: ignore
    """Get help information for a command using template rendering."""
    from mcp_guide.utils.template_renderer import render_template_content

    try:
        # Use the help template with the pre-built command_context
        # The help template will handle --table flag via {{#kwargs._table}}
        from mcp_guide.session import get_or_create_session

        session = await get_or_create_session(ctx)
        docroot = Path(await session.get_docroot())
        commands_dir = docroot / COMMANDS_DIR
        help_template_path = commands_dir / "help.mustache"

        if await AsyncPath(help_template_path).exists():
            help_template_content = await AsyncPath(help_template_path).read_text()
        else:
            return Result.failure("Help template not found", error_type="not_found")

        # Render the template with the command_context
        rendered_result = await render_template_content(help_template_content, TemplateContext(command_context))
        if not rendered_result.success:
            return rendered_result

        result = Result.ok(rendered_result.value)
        result.instruction = command_context.get("instruction", INSTRUCTION_DISPLAY_ONLY)
        return result

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
        command_path: Command path (e.g., "help", "create/category")
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
        # Apply middleware chain
        async def next_handler() -> Result[Any]:
            return await _execute_command(command_path, kwargs, args, ctx)

        # Build middleware chain from right to left
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
    """Resolve command alias to actual command name."""
    for cmd in commands:
        if command_path in cmd.get("aliases", []):
            name = cmd.get("name")
            return str(name) if name is not None else command_path
    return command_path


async def _discover_command_file(commands_dir: Path, command_path: str) -> Result[FileInfo]:
    """Discover command file by path."""
    pattern = f"{command_path}.*"
    try:
        files = await discover_category_files(commands_dir, [pattern])
    except Exception as e:
        return Result.failure(f"Error discovering command files: {e}", error_type="file_error")

    if not files:
        return Result.failure(f"Command not found: {command_path}", error_type="not_found")

    return Result.ok(files[0])


def _build_command_context(
    base_context: Any,
    command_path: str,
    file_info: FileInfo,
    kwargs: dict[str, Any],
    args: list[str],
    commands: list[dict[str, Any]],
) -> Any:
    """Build template context for command execution."""

    # Use kwargs directly without underscore manipulation
    template_kwargs = convert_lists_to_indexed(kwargs.copy())

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

    # Convert to sorted list with title-case names
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

    return base_context.new_child(
        convert_lists_to_indexed(
            {
                "kwargs": template_kwargs,
                "raw_kwargs": kwargs,
                "args": args,
                "args_str": args_string,
                "command": {"name": command_path, "path": str(file_info.path)},
                "executed_command": command_path,
                "commands": commands,
                "command_categories": command_categories,
            }
        )
    )


def _validate_command_arguments(
    front_matter: dict[str, Any], kwargs: dict[str, Any], args: list[str]
) -> Optional[Result[str]]:
    """Validate command arguments against frontmatter requirements."""
    # Check required arguments
    required_args_value = front_matter.get("required_args", [])
    if isinstance(required_args_value, list):
        required_args = [str(arg) for arg in required_args_value if isinstance(arg, (str, int, float))]
        if len(args) < len(required_args):
            missing_args = required_args[len(args) :]
            return Result.failure(f"Missing required arguments: {', '.join(missing_args)}", error_type="validation")

    # Check required kwargs
    required_kwargs_value = front_matter.get("required_kwargs", [])
    if isinstance(required_kwargs_value, list):
        required_kwargs = [str(kwarg) for kwarg in required_kwargs_value if isinstance(kwarg, (str, int, float))]
        missing_kwargs: list[str] = []
        missing_kwargs.extend(k for k in required_kwargs if k not in kwargs and f"_{k}" not in kwargs)
        if missing_kwargs:
            return Result.failure(f"Missing required options: {', '.join(missing_kwargs)}", error_type="validation")

    return None


async def _is_help_command(command_path: str, ctx: Optional[Context]) -> bool:  # type: ignore
    """Check if command_path is a help command or alias."""
    try:
        session = await get_or_create_session(ctx)
        docroot = Path(await session.get_docroot())
        commands_dir = docroot / COMMANDS_DIR
        commands = await discover_commands(commands_dir)

        # Find help command and its aliases
        help_aliases = ["help"]  # Always include base name
        for cmd in commands:
            if cmd["name"] == "help":
                help_aliases.extend(cmd.get("aliases", []))
                break

        return command_path in help_aliases
    except Exception:
        # Fallback to hardcoded aliases if discovery fails
        return command_path in {"help", "h", "?"}


async def _execute_command(
    command_path: str,
    kwargs: dict[str, Union[str, bool, int]],
    args: list[str],
    ctx: Optional[Context],  # type: ignore
) -> Result[Any]:
    """Execute command without middleware."""
    from mcp_guide.session import get_or_create_session

    # Initialize session and get paths
    try:
        session = await get_or_create_session(ctx)
        docroot = Path(await session.get_docroot())
    except ValueError as e:
        return Result.failure(str(e), error_type="context")

    commands_dir = docroot / COMMANDS_DIR
    if not await AsyncPath(commands_dir).exists():
        return Result.failure(f"Commands directory not found: {COMMANDS_DIR}", error_type="not_found")

    # Discover commands and try direct template file first (higher precedence)
    commands = await discover_commands(commands_dir)

    # First try to find command file directly (template files have higher precedence)
    file_result = await _discover_command_file(commands_dir, command_path)
    resolved_path = command_path

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

    # Set base path for content loading
    file_info.resolve(commands_dir, docroot)

    # Cache MCP context if available
    if ctx:
        from mcp_guide.mcp_context import cache_mcp_globals

        logger.debug(f"Caching MCP context for command: {command_path}")
        await cache_mcp_globals(ctx)
    else:
        logger.debug(f"No MCP context available for command: {command_path}")

    # Build template context
    base_context = await get_template_contexts()
    command_context = _build_command_context(base_context, command_path, file_info, kwargs, args, commands)

    # Check for help flag or help command with args (after context building)
    if kwargs.get("_help"):
        return await get_command_help(command_path, command_context, ctx)
    if await _is_help_command(command_path, ctx) and args:
        return await get_command_help(args[0], command_context, ctx)

    # Get content and frontmatter using accessors
    try:
        front_matter = await file_info.get_frontmatter() or {}
        template_content = await file_info.get_content() or ""
    except (OSError, PermissionError, FileNotFoundError) as e:
        return Result.failure(
            error=f"Error reading file {file_info.path}: {str(e)}",
            error_type="file_error",
            instruction="Check file permissions and ensure the file exists and is readable",
        )

    # Validate arguments against front matter
    if front_matter:
        if validation_error := _validate_command_arguments(front_matter, kwargs, args):
            return validation_error

    # Render template with partial support
    render_result = await render_file_content(file_info, command_context, commands_dir, docroot)
    if render_result.success:
        result = Result.ok(render_result.value)

        # Set instruction from frontmatter or default
        if front_matter and "instruction" in front_matter:
            instruction_result = await render_template_content(
                front_matter["instruction"], command_context, str(file_info.path)
            )
            result.instruction = instruction_result.value if instruction_result.success else INSTRUCTION_DISPLAY_ONLY
        else:
            # Check if instruction needs to be overridden with type-based default
            content_type = get_frontmatter_type(front_matter)
            default_instruction = get_type_based_default_instruction(content_type)

            # Override if instruction is None OR matches default instructions
            if (
                result.instruction is None
                or result.instruction == Result.success_instruction()
                or result.instruction == Result.failure_instruction()
            ):
                result.instruction = default_instruction or INSTRUCTION_DISPLAY_ONLY

        return result
    else:
        from mcp_guide.result_constants import ERROR_TEMPLATE, INSTRUCTION_TEMPLATE_ERROR

        return Result.failure(
            f"Template rendering failed: {render_result.error}",
            error_type=ERROR_TEMPLATE,
            instruction=INSTRUCTION_TEMPLATE_ERROR,
        )


async def _handle_command_request(argv: list[str], ctx: Optional["Context"]) -> Result[Any]:  # type: ignore[type-arg]
    """Handle command-mode request."""
    first_arg = argv[1]
    raw_command_path = first_arg[1:]  # Remove prefix

    if not raw_command_path:
        result: Result[Any] = Result.failure("Command name cannot be empty", error_type="validation")
        result.instruction = INSTRUCTION_DISPLAY_ONLY
        return result

    # Validate and sanitize
    from mcp_guide.utils.command_security import validate_command_path_full

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

    # Join content args as category expression
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
        result: Result[Any] = Result.failure("Requires 1 or more arguments", error_type="validation")
        result.instruction = INSTRUCTION_DISPLAY_ONLY
        return result

    # Check for command prefix
    first_arg = argv[1]
    if first_arg.startswith(":") or first_arg.startswith(";"):
        return await _handle_command_request(argv, ctx)
    else:
        return await _handle_content_request(argv, ctx)


@mcp.prompt() if mcp is not None else lambda f: f
async def guide(
    # MCP prompt handlers require explicit parameters - *args not supported
    # MAX_PROMPT_ARGS defined to match MCP protocol limit
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
    """Access guide functionality."""
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

    # Process result through task manager to pick up any queued instructions
    try:
        result = await task_manager.process_result(result)
    except Exception as e:
        logger.error(f"TaskManager processing failed for prompt: {e}")

    # Log the result before returning
    logger.trace("RESULT: Prompt guide returning result", extra=result.to_json())
    return result.to_json_str()
