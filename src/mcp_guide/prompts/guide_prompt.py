# See src/mcp_guide/prompts/README.md for prompt documentation standards

"""Guide prompt implementation for direct content access."""

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import (
    TYPE_CHECKING,
    Any,
    Awaitable,
    Callable,
    Coroutine,
    List,
    Optional,
    Protocol,
    TypeVar,
    Union,
)

from anyio import Path as AsyncPath

from mcp_guide.commands.formatting import format_args_string
from mcp_guide.config_constants import COMMANDS_DIR
from mcp_guide.core.mcp_log import get_logger
from mcp_guide.core.prompt_decorator import get_prompt_name, promptfunc
from mcp_guide.discovery.commands import CommandAliasMetadata, discover_commands, normalise_alias_metadata
from mcp_guide.discovery.files import FileInfo, discover_document_files
from mcp_guide.feature_flags.types import FeatureValue
from mcp_guide.models import resolve_all_flags
from mcp_guide.prompts.command_parser import parse_command_arguments
from mcp_guide.render import render_template
from mcp_guide.render.cache import get_template_contexts
from mcp_guide.render.context import TemplateContext, convert_lists_to_indexed
from mcp_guide.result import Result
from mcp_guide.result_constants import (
    ERROR_CONTEXT,
    ERROR_FILE_ERROR,
    ERROR_NOT_FOUND,
    ERROR_RENDER,
    ERROR_SECURITY,
    ERROR_TEMPLATE,
    ERROR_VALIDATION,
    INSTRUCTION_FILE_ERROR,
    INSTRUCTION_NOTFOUND_ERROR,
    INSTRUCTION_TEMPLATE_ERROR,
    make_invalid_session_result,
)
from mcp_guide.session import InvalidGuideSessionError, get_session
from mcp_guide.tools.tool_content import ContentArgs, internal_get_content
from mcp_guide.uri_parser import parse_query_kwargs

if TYPE_CHECKING:
    from mcp_guide.session import Session

from fastmcp import Context

logger = get_logger(__name__)

AliasKwarg = str | bool
CommandKwarg = Union[str, bool, int]
_CommandValue = TypeVar("_CommandValue", bound=CommandKwarg)


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


@dataclass(frozen=True)
class CommandAliasResolution:
    """Resolved command alias details."""

    command_path: str
    implied_kwargs: dict[str, AliasKwarg]


async def get_command_help(
    session: "Session", command_context: TemplateContext, commands_dir: Path, docroot: Path
) -> Result[str]:
    """Get help information for a command using template rendering."""
    from mcp_guide.render.template import render_template

    try:
        # Discover the help command file through the proper discovery system
        help_result = await _discover_command_file(commands_dir, "help")
        if not help_result.success:
            return Result.failure("Help template not found", error_type=ERROR_NOT_FOUND)

        help_file_info = help_result.value
        if help_file_info is None:
            return Result.failure("Help template not found", error_type=ERROR_NOT_FOUND)

        help_file_info.resolve(commands_dir, docroot)

        # Render using the proper template rendering system
        rendered = await render_template(
            session,
            file_info=help_file_info,
            base_dir=help_file_info.path.parent,
            project_flags={},
            context=command_context,
        )

        if rendered is None:
            return Result.failure("Failed to render help template", error_type=ERROR_RENDER)

        if rendered.errors:
            rendered.log_discarded_errors("get_command_help")

        return Result.ok(rendered.content, instruction=rendered.instruction)

    except Exception as e:
        return Result.failure(str(e), error_type=ERROR_CONTEXT)


# MCP compatibility limit for variable arguments
MAX_PROMPT_ARGS = 15


async def handle_command(
    command_path: str,
    kwargs: Optional[dict[str, Union[str, bool, int]]] = None,
    args: Optional[list[str]] = None,
    ctx: Optional[Context] = None,
    session: "Session | None" = None,
    middleware: Optional[List[CommandMiddleware]] = None,
    argv: Optional[list[str]] = None,
    session_id: str | None = None,
) -> Result[Any]:
    """Handle command execution with direct file discovery.

    Args:
        command_path: Command path (e.g. "help", "create/category")
        kwargs: Pre-parsed keyword arguments (used if argv not provided)
        args: Pre-parsed positional arguments (used if argv not provided)
        ctx: MCP context
        middleware: Optional list of middleware to apply
        argv: Raw argument list; if provided, parsing is deferred to _execute_command

    Returns:
        Result containing rendered command output or error
    """
    if kwargs is None:
        kwargs = {}
    if args is None:
        args = []
    if session is None:
        session = await get_session(ctx, session_id=session_id)

    # Add logging middleware by default
    from mcp_guide.middleware.logging_middleware import logging_middleware

    if middleware is None:
        middleware = []
    middleware = [logging_middleware] + middleware
    if middleware:
        # Apply the middleware chain
        async def next_handler() -> Result[Any]:
            return await _execute_command(command_path, kwargs, args, ctx, session, argv=argv, session_id=session_id)

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
        return await _execute_command(command_path, kwargs, args, ctx, session, argv=argv, session_id=session_id)


def _resolve_command_alias(command_path: str, commands: list[dict[str, Any]]) -> CommandAliasResolution:
    """Resolve command alias to the actual command name plus alias-implied kwargs."""
    default_resolution = CommandAliasResolution(command_path=command_path, implied_kwargs={})
    for cmd in commands:
        for alias in _alias_metadata(cmd):
            if _matches_alias(command_path, alias):
                name = cmd.get("name")
                return CommandAliasResolution(
                    command_path=str(name) if name is not None else command_path,
                    implied_kwargs=_merge_alias_kwargs(
                        default_kwargs=alias.get("implied_kwargs", {}),
                        override_kwargs=_command_path_query_kwargs(command_path),
                    ),
                )
        if command_path in cmd.get("aliases", []):
            name = cmd.get("name")
            return CommandAliasResolution(
                command_path=str(name) if name is not None else command_path,
                implied_kwargs={},
            )
    return default_resolution


def _alias_metadata(command: dict[str, Any]) -> list[CommandAliasMetadata]:
    """Return normalized alias metadata for a discovered command."""
    return normalise_alias_metadata(command.get("alias_metadata", []))


def _command_path_without_query(command_path: object) -> str | None:
    """Return command path without any prompt query suffix."""
    if not isinstance(command_path, str):
        return None
    return command_path.partition("?")[0]


def _command_path_query_kwargs(command_path: str) -> dict[str, str | bool]:
    """Parse prompt command-path query kwargs, if present."""
    _, separator, query = command_path.partition("?")
    return parse_query_kwargs(query) if separator else {}


def _matches_alias(command_path: object, alias: CommandAliasMetadata) -> bool:
    """Return whether a command path matches a normalized or raw alias."""
    if not isinstance(command_path, str):
        return False
    command_path_base = _command_path_without_query(command_path)
    alias_path_base = _command_path_without_query(alias["path"])
    alias_raw_base = _command_path_without_query(alias["raw"])
    return command_path in {alias["path"], alias["raw"]} or command_path_base in {alias_path_base, alias_raw_base}


def _merge_alias_kwargs(
    default_kwargs: Mapping[str, AliasKwarg],
    override_kwargs: Mapping[str, _CommandValue],
) -> dict[str, AliasKwarg | _CommandValue]:
    """Merge default kwargs with explicit overrides."""
    return {**default_kwargs, **override_kwargs}


def _command_help_lookup(commands: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Build lookup for command help by canonical name, legacy alias, raw alias, and alias path."""
    lookup: dict[str, dict[str, Any]] = {}
    for cmd in commands:
        name = cmd.get("name")
        if isinstance(name, str):
            lookup.setdefault(name, cmd)
        for alias in cmd.get("aliases", []):
            if isinstance(alias, str):
                lookup.setdefault(alias, cmd)
        for alias in _alias_metadata(cmd):
            lookup.setdefault(alias["path"], cmd)
            lookup.setdefault(alias["raw"], cmd)
    return lookup


async def _discover_command_file(commands_dir: Path, command_path: str) -> Result[FileInfo]:
    """Discover the command file by path."""
    pattern = f"{command_path}.*"
    try:
        files = await discover_document_files(commands_dir, [pattern])
    except Exception as e:
        return Result.failure(f"Error discovering command files: {e}", error_type=ERROR_FILE_ERROR)

    if not files:
        return Result.failure(f"Command not found: {command_path}", error_type=ERROR_NOT_FOUND)

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

    def enrich_command_metadata(command: dict[str, Any]) -> dict[str, Any]:
        enriched = dict(command)
        aliases = command.get("aliases", [])
        if aliases:
            enriched["aliases_csv"] = ",".join(str(alias) for alias in aliases)
        return enriched

    # Use kwargs directly without underscore manipulation
    template_kwargs = convert_lists_to_indexed(kwargs.copy())

    enriched_commands = [enrich_command_metadata(cmd) for cmd in commands]

    # If args provided (for help command), look up the requested command
    command_help = None
    if args:
        requested_cmd = args[0] if isinstance(args[0], str) else args[0].get("value")
        help_lookup = _command_help_lookup(enriched_commands)
        if isinstance(requested_cmd, str):
            command_help = help_lookup.get(requested_cmd) or help_lookup.get(
                _command_path_without_query(requested_cmd) or ""
            )

    # Group commands by category dynamically, filtering out underscore-prefixed commands
    categories: dict[str, list[dict[str, Any]]] = {}
    for cmd in enriched_commands:
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
        "commands": enriched_commands,
        "command_categories": command_categories,
    }

    # Add command_help if found
    if command_help:
        context_data["command_help"] = command_help

    return base_context.new_child(convert_lists_to_indexed(context_data))


async def _is_help_command(command_path: str, session: "Session") -> bool:
    """Check if command_path is a help command or alias."""
    # noinspection PyBroadException
    try:
        docroot = Path(await session.runtime.get_docroot())
        commands_dir = docroot / COMMANDS_DIR
        commands = await discover_commands(commands_dir, session)

        # Find help command and its aliases
        help_aliases = ["help"]  # Always include the base name
        for cmd in commands:
            if cmd["name"] == "help":
                help_aliases.extend(cmd.get("aliases", []))
                help_aliases.extend(alias["path"] for alias in _alias_metadata(cmd))
                break

        return command_path in help_aliases
    except Exception:
        # Fallback to hardcoded aliases if discovery fails for any reason
        return command_path in {"help", "h"}


async def _execute_command(
    command_path: str,
    kwargs: dict[str, Union[str, bool, int]],
    args: list[str],
    ctx: Optional[Context],
    session: "Session",
    argv: Optional[list[str]] = None,
    session_id: str | None = None,
) -> Result[Any]:
    """Execute command without middleware."""
    docroot = Path(await session.runtime.get_docroot())

    commands_dir = docroot / COMMANDS_DIR
    if not await AsyncPath(commands_dir).exists():
        return Result.failure(f"Commands directory not found: {COMMANDS_DIR}", error_type=ERROR_NOT_FOUND)

    # Discover commands and try the direct template file first (higher precedence)
    commands = await discover_commands(commands_dir, session)

    # First, try to find the command file directly (template files have higher precedence)
    file_result = await _discover_command_file(commands_dir, command_path)
    alias_implied_kwargs: dict[str, str | bool] = {}

    # If no direct template file found, try alias resolution
    if not file_result.success:
        resolved_alias = _resolve_command_alias(command_path, commands)
        resolved_path = resolved_alias.command_path
        alias_implied_kwargs = resolved_alias.implied_kwargs
        if resolved_path != command_path:  # Only retry if alias was found
            file_result = await _discover_command_file(commands_dir, resolved_path)

    # If still no file found, return the error
    if not file_result.success:
        return file_result
    file_info = file_result.value
    if not file_info:
        return Result.failure("No file info returned", error_type=ERROR_FILE_ERROR)

    # Set the base path for content loading
    file_info.resolve(commands_dir, docroot)

    # If raw argv provided, parse arguments using frontmatter argrequired
    if argv is not None:
        argrequired = None
        frontmatter: dict[str, Any] = {}
        try:
            frontmatter = await file_info.get_frontmatter() or {}
            argrequired_value = frontmatter.get("argrequired")
            if isinstance(argrequired_value, list):
                argrequired = argrequired_value
        except OSError as e:
            logger.warning(f"Failed to read frontmatter for command {command_path}: {e}. Parsing without argrequired.")
        kwargs, args, parse_errors = parse_command_arguments(argv, argrequired=argrequired)
        if parse_errors:
            error_msg = "; ".join(parse_errors)
            result: Result[Any] = Result.failure(f"Argument parsing failed: {error_msg}", error_type=ERROR_VALIDATION)
            return result

        # Check minimum required positional arguments
        minargs = frontmatter.get("minargs", 0)
        if isinstance(minargs, int) and minargs > 0 and len(args) < minargs:
            usage = frontmatter.get("usage", "")
            msg = f"Missing required argument\n\nUsage: {usage}" if usage else "Missing required argument"
            result = Result.failure(msg, error_type=ERROR_VALIDATION)
            return result

    kwargs = _merge_alias_kwargs(default_kwargs=alias_implied_kwargs, override_kwargs=kwargs)

    # Build template context
    base_context = await get_template_contexts(session)
    command_context = _build_command_context(base_context, command_path, file_info, kwargs, args, commands)

    # Check for a help flag or help command with args (after context building)
    if kwargs.get("_help"):
        return await get_command_help(session, command_context, commands_dir, docroot)
    if await _is_help_command(command_path, session) and args:
        return await get_command_help(session, command_context, commands_dir, docroot)

    # Get resolved flags for requires-* checking
    requirements_context: dict[str, FeatureValue] = await resolve_all_flags(session)

    # Render template using new API
    try:
        rendered = await render_template(
            session,
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

    # Check for application-level errors signaled via {{#_error}} lambda
    if rendered.errors:
        errors = rendered.errors
        return Result.failure(
            "\n".join(errors),
            error_type=ERROR_VALIDATION,
            error_data={"errors": errors},
        )

    # Extract content and instruction from RenderedContent
    result = Result.ok(rendered.content)
    result.instruction = rendered.instruction  # Already has type-based default
    return result


async def _handle_command_request(
    argv: list[str], ctx: Optional["Context"], session: "Session", session_id: str | None = None
) -> Result[Any]:
    """Handle command-mode request."""
    first_arg = argv[1]
    raw_command_path = first_arg[1:]  # Remove prefix

    if not raw_command_path:
        result: Result[Any] = Result.failure("Command name cannot be empty", error_type=ERROR_VALIDATION)
        return result

    # Validate and sanitize
    from mcp_guide.commands.security import validate_command_path_full

    error, command_path = validate_command_path_full(raw_command_path)
    if error:
        result = Result.failure(f"Security validation failed: {error}", error_type=ERROR_SECURITY)
        return result

    # Validate context
    if ctx is None:
        result = Result.failure(f"Context is required for command execution", error_type=ERROR_VALIDATION)
        return result

    return await handle_command(command_path, argv=argv[1:], ctx=ctx, session=session, session_id=session_id)


async def _handle_content_request(
    argv: list[str], ctx: Optional["Context"], session: "Session", session_id: str | None = None
) -> Result[Any]:
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
        result: Result[str] = Result.failure(f"Flag parsing failed: {error_msg}", error_type=ERROR_VALIDATION)
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
        return result

    # Create content args with pattern support
    pattern = kwargs.get("pattern")
    if isinstance(pattern, int):
        pattern = str(pattern)
    force = bool(kwargs.get("force", False))
    content_args_obj = ContentArgs(expression=category, pattern=pattern, force=force, session_id=session_id)
    return await internal_get_content(content_args_obj, ctx, session=session)


async def _route_guide_request(
    argv: list[str], ctx: Optional["Context"], session: "Session", session_id: str | None = None
) -> Result[Any]:
    """Route guide request to command or content handler."""
    # Validate arguments
    if len(argv) == 1 or (len(argv) == 2 and argv[1] == ""):
        # Get prompt prefix from session agent info
        prompt_prefix = "@"  # Default
        if session.agent_info:
            prompt_prefix = (
                session.agent_info.prompt_prefix.replace("{mcp_name}", get_prompt_name())
                if session.agent_info.prompt_prefix is not None
                else ""
            )

        if prompt_prefix:
            error_msg = f"The guide prompt requires one or more arguments. Use {prompt_prefix}{get_prompt_name()} :help to list commands"
        else:
            error_msg = (
                "The guide prompt requires one or more arguments. "
                "This client does not support prompts; use guide:// resources or tools instead."
            )
        result: Result[Any] = Result.failure(error_msg, error_type=ERROR_VALIDATION)
        return result

    # Check for command prefix
    first_arg = argv[1]
    if first_arg.startswith(":") or first_arg.startswith(";"):
        return await _handle_command_request(argv, ctx, session, session_id)
    else:
        return await _handle_content_request(argv, ctx, session, session_id)


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
    session_id: Optional[str] = None,
    ctx: Optional["Context"] = None,
) -> object:
    """Access guide functionality.

    Args:
        arg[1-f]: up to 15 positional args
        session_id: Optional explicit interaction identifier for modern clients
        ctx: mcp context
    """
    prompt_name = get_prompt_name()

    # Establish the same explicit interaction boundary used by tools before
    # any prompt helper reads session-dependent configuration or task state.
    from mcp_guide.session import get_session

    try:
        session = await get_session(ctx, session_id=session_id)
    except InvalidGuideSessionError:
        from mcp_guide.tools.tool_result import prompt_result

        return await prompt_result(prompt_name, make_invalid_session_result())

    # Cache MCP context if available
    if ctx:
        from mcp_guide.mcp_context import cache_mcp_globals

        logger.debug("Caching MCP context for guide request")
        # noinspection PyTypeChecker
        await cache_mcp_globals(ctx, session)

    # Call on_tool for all subscribers immediately
    task_manager = session.task_manager
    try:
        await task_manager.on_tool()
    except Exception as e:
        logger.error(f"on_tool failed at prompt start: {e}")

    # Build argv list (MCP protocol requirement)
    argv = [prompt_name]
    for arg in [arg1, arg2, arg3, arg4, arg5, arg6, arg7, arg8, arg9, arga, argb, argc, argd, arge, argf]:
        if arg is None:
            break
        argv.append(arg)

    # Route request
    result = await _route_guide_request(argv, ctx, session, session.session_id)

    # Process result through the task manager
    from mcp_guide.tools.tool_result import prompt_result

    return await prompt_result(prompt_name, result, session=session, session_id=session.session_id)
