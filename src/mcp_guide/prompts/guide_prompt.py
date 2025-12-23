# See src/mcp_guide/prompts/README.md for prompt documentation standards

"""Guide prompt implementation for direct content access."""

import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any, Awaitable, Callable, Coroutine, List, Optional, Protocol, Union

import aiofiles

from mcp_core.result import Result

logger = logging.getLogger(__name__)


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


if TYPE_CHECKING:
    from typing import Any

    from mcp.server.fastmcp import Context
else:
    try:
        from mcp.server.fastmcp import Context
    except ImportError:
        Context = None  # type: ignore

from mcp_guide.constants import COMMANDS_DIR
from mcp_guide.prompts.command_parser import parse_command_arguments
from mcp_guide.server import prompts
from mcp_guide.tools.tool_constants import INSTRUCTION_DISPLAY_ONLY
from mcp_guide.tools.tool_content import ContentArgs, internal_get_content
from mcp_guide.utils.command_discovery import discover_commands
from mcp_guide.utils.file_discovery import FileInfo, discover_category_files
from mcp_guide.utils.frontmatter import parse_frontmatter_content
from mcp_guide.utils.template_context_cache import get_template_contexts
from mcp_guide.utils.template_renderer import render_template_content


async def get_command_help(command_path: str, ctx: Optional["Context[Any, Any, Any]"]) -> Result[str]:
    """Get help information for a command."""
    from mcp_guide.session import get_or_create_session

    try:
        session = await get_or_create_session(ctx)
        docroot = Path(await session.get_docroot())
        commands_dir = docroot / COMMANDS_DIR

        # Discover commands to get metadata
        commands = await discover_commands(commands_dir)

        # Find the command
        for cmd in commands:
            if cmd["name"] == command_path or command_path in cmd.get("aliases", []):
                help_text = f"# {cmd['name']}\n\n"
                if cmd.get("description"):
                    help_text += f"{cmd['description']}\n\n"
                if cmd.get("usage"):
                    help_text += f"**Usage:** {cmd['usage']}\n\n"
                if cmd.get("aliases"):
                    help_text += f"**Aliases:** {', '.join(cmd['aliases'])}\n\n"
                if cmd.get("examples"):
                    help_text += "**Examples:**\n"
                    for example in cmd["examples"]:
                        help_text += f"- {example}\n"

                result = Result.ok(help_text)
                result.instruction = INSTRUCTION_DISPLAY_ONLY
                return result

        return Result.failure(f"Command not found: {command_path}", error_type="not_found")
    except ValueError as e:
        return Result.failure(str(e), error_type="context")


# MCP compatibility limit for variable arguments
MAX_PROMPT_ARGS = 15


async def handle_command(
    command_path: str,
    kwargs: dict[str, Union[str, bool, int]],
    args: list[str],
    ctx: Optional["Context[Any, Any, Any]"],
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
    template_kwargs = {}
    for key, value in kwargs.items():
        if key.startswith("_"):
            clean_key = key[1:]
            template_kwargs[clean_key] = value
        else:
            template_kwargs[key] = value

    # Group commands by category dynamically
    categories: dict[str, list[dict[str, Any]]] = {}
    for cmd in commands:
        category = cmd.get("category", "general")
        if category not in categories:
            categories[category] = []
        categories[category].append(cmd)

    # Convert to sorted list with title-case names
    command_categories = []
    for category_name in sorted(categories.keys()):
        command_categories.append(
            {
                "name": category_name,
                "title": category_name.replace("_", " ").title() + " Commands",
                "commands": categories[category_name],
            }
        )

    return base_context.new_child(
        {
            "kwargs": template_kwargs,
            "raw_kwargs": kwargs,
            "args": args,
            "command": {"name": command_path, "path": str(file_info.path)},
            "commands": commands,
            "command_categories": command_categories,
        }
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
        missing_kwargs = []
        for k in required_kwargs:
            if k not in kwargs and f"_{k}" not in kwargs:
                missing_kwargs.append(k)
        if missing_kwargs:
            return Result.failure(f"Missing required options: {', '.join(missing_kwargs)}", error_type="validation")

    return None


async def _execute_command(
    command_path: str,
    kwargs: dict[str, Union[str, bool, int]],
    args: list[str],
    ctx: Optional["Context[Any, Any, Any]"],
) -> Result[Any]:
    """Execute command without middleware."""
    from mcp_guide.session import get_or_create_session

    # Check for help flag first
    if kwargs.get("_help"):
        return await get_command_help(command_path, ctx)

    # Initialize session and get paths
    try:
        session = await get_or_create_session(ctx)
        docroot = Path(await session.get_docroot())
    except ValueError as e:
        return Result.failure(str(e), error_type="context")

    commands_dir = docroot / COMMANDS_DIR
    if not commands_dir.exists():
        return Result.failure(f"Commands directory not found: {COMMANDS_DIR}", error_type="not_found")

    # Discover commands and resolve aliases
    commands = await discover_commands(commands_dir)
    resolved_path = _resolve_command_alias(command_path, commands)

    # Discover command file
    file_result = await _discover_command_file(commands_dir, resolved_path)
    if not file_result.success:
        return file_result
    file_info = file_result.value
    if not file_info:
        return Result.failure("No file info returned", error_type="file_error")

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

    # Read and render template
    try:
        absolute_path = commands_dir / file_info.path
        async with aiofiles.open(absolute_path, "r", encoding="utf-8") as f:
            content = await f.read()

        front_matter, template_content = parse_frontmatter_content(content)
        front_matter = front_matter or {}

        # Validate arguments against front matter
        if front_matter:
            if validation_error := _validate_command_arguments(front_matter, kwargs, args):
                return validation_error

        # Render template
        render_result = render_template_content(template_content, command_context, str(file_info.path))
        if render_result.success:
            result = Result.ok(render_result.value)

            # Set instruction from frontmatter or default
            if front_matter and "instruction" in front_matter:
                instruction_result = render_template_content(
                    front_matter["instruction"], command_context, str(file_info.path)
                )
                result.instruction = (
                    instruction_result.value if instruction_result.success else INSTRUCTION_DISPLAY_ONLY
                )
            else:
                result.instruction = INSTRUCTION_DISPLAY_ONLY

            return result
        else:
            from mcp_guide.tools.tool_constants import ERROR_TEMPLATE, INSTRUCTION_TEMPLATE_ERROR

            return Result.failure(
                f"Template rendering failed: {render_result.error}",
                error_type=ERROR_TEMPLATE,
                instruction=INSTRUCTION_TEMPLATE_ERROR,
            )

    except Exception as e:
        from mcp_guide.tools.tool_constants import ERROR_FILE_ERROR

        return Result.failure(f"Error reading command file: {e}", error_type=ERROR_FILE_ERROR)


async def _handle_command_request(argv: list[str], ctx: Optional["Context[Any, Any, Any]"]) -> Result[Any]:
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


async def _handle_content_request(argv: list[str], ctx: Optional["Context[Any, Any, Any]"]) -> Result[Any]:
    """Handle content-mode request."""
    category = ",".join(argv[1:])
    content_args = ContentArgs(expression=category, pattern=None)
    content_result = await internal_get_content(content_args, ctx)
    content_result.instruction = INSTRUCTION_DISPLAY_ONLY
    return content_result


async def _route_guide_request(argv: list[str], ctx: Optional["Context[Any, Any, Any]"]) -> Result[Any]:
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


@prompts.prompt()
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
    argA: Optional[str] = None,
    argB: Optional[str] = None,
    argC: Optional[str] = None,
    argD: Optional[str] = None,
    argE: Optional[str] = None,
    argF: Optional[str] = None,
    ctx: Optional["Context"] = None,  # type: ignore[type-arg]
) -> str:
    """Access guide functionality."""
    # Build argv list (MCP protocol requirement)
    argv = ["guide"]
    for arg in [arg1, arg2, arg3, arg4, arg5, arg6, arg7, arg8, arg9, argA, argB, argC, argD, argE, argF]:
        if arg is None:
            break
        argv.append(arg)

    # Route request
    result = await _route_guide_request(argv, ctx)
    return result.to_json_str()
