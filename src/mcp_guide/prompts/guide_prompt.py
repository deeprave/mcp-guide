# See src/mcp_guide/prompts/README.md for prompt documentation standards

"""Guide prompt implementation for direct content access."""

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import (
    TYPE_CHECKING,
    Annotated,
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
from fastmcp import Context
from mcp_types import InputRequiredResult
from pydantic import Field

from mcp_guide.commands.formatting import format_args_string
from mcp_guide.config_constants import COMMANDS_DIR
from mcp_guide.core.arguments import SESSION_ID_DESCRIPTION
from mcp_guide.core.mcp_log import get_logger
from mcp_guide.core.prompt_decorator import get_prompt_name, promptfunc
from mcp_guide.discovery.commands import CommandAliasMetadata, discover_commands, normalise_alias_metadata
from mcp_guide.discovery.files import FileInfo, discover_document_files
from mcp_guide.elicitation import resolve_elicitations
from mcp_guide.feature_flags.types import FeatureValue
from mcp_guide.models import resolve_all_flags
from mcp_guide.prompts.command_parser import parse_command_arguments
from mcp_guide.render import render_template
from mcp_guide.render.cache import get_template_contexts
from mcp_guide.render.context import TemplateContext, convert_lists_to_indexed, keyword_context
from mcp_guide.render.document_properties import DocumentProperties
from mcp_guide.render.template import collect_interactive_document_properties
from mcp_guide.result import Result
from mcp_guide.result_constants import (
    AGENT_ERROR,
    ERROR_CONTEXT,
    ERROR_FILE_ERROR,
    ERROR_NOT_FOUND,
    ERROR_RENDER,
    ERROR_SECURITY,
    ERROR_TEMPLATE,
    ERROR_VALIDATION,
    UNKNOWN_ERROR,
    USER_ERROR,
)
from mcp_guide.runtime import RequestContext
from mcp_guide.tools.tool_content import ContentArgs, internal_get_content
from mcp_guide.uri_parser import parse_query_kwargs
from mcp_guide.workflow.command_input import prepare_command_input

if TYPE_CHECKING:
    from mcp_guide.session import Session

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
        next_handler: Callable[[], Awaitable[Result[Any] | InputRequiredResult]],
    ) -> Result[Any] | InputRequiredResult:
        """Execute middleware logic."""
        ...


@dataclass(frozen=True)
class CommandAliasResolution:
    """Resolved command alias details."""

    command_path: str
    implied_kwargs: dict[str, AliasKwarg]


async def get_command_help(
    session: "Session",
    command_context: TemplateContext,
    commands_dir: Path,
    resolve_document_path: Callable[[str | Path], Path],
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

        help_file_info.resolve(resolve_document_path, COMMANDS_DIR)

        # Render using the proper template rendering system
        rendered = await render_template(
            session,
            file_info=help_file_info,
            base_dir=help_file_info.path.parent,
            project_flags={},
            context=command_context,
            resolver=resolve_document_path,
        )

        if rendered is None:
            return Result.failure("Failed to render help template", error_type=ERROR_RENDER)

        if rendered.errors:
            rendered.log_discarded_errors("get_command_help")

        return Result.ok(rendered.content, instruction=rendered.instruction, disposition=rendered.disposition)

    except Exception as e:
        return Result.failure(str(e), error_type=ERROR_CONTEXT)


# MCP compatibility limit for variable arguments
MAX_PROMPT_ARGS = 15


async def handle_command(
    command_path: str,
    kwargs: Optional[dict[str, Union[str, bool, int]]] = None,
    args: Optional[list[str]] = None,
    *,
    request_context: RequestContext,
    middleware: Optional[List[CommandMiddleware]] = None,
    argv: Optional[list[str]] = None,
    mcp_context: Context | None = None,
) -> Result[Any] | InputRequiredResult:
    """Handle command execution with direct file discovery.

    Args:
        command_path: Command path (e.g. "help", "create/category")
        kwargs: Pre-parsed keyword arguments (used if argv not provided)
        args: Pre-parsed positional arguments (used if argv not provided)
        request_context: Resolved application request context
        middleware: Optional list of middleware to apply
        argv: Raw argument list; if provided, parsing is deferred to _execute_command

    Returns:
        Result containing rendered command output or error
    """
    if kwargs is None:
        kwargs = {}
    if args is None:
        args = []
    session = request_context.session

    # Add logging middleware by default
    from mcp_guide.middleware.logging_middleware import logging_middleware

    if middleware is None:
        middleware = []
    middleware = [logging_middleware] + middleware
    if middleware:
        # Apply the middleware chain
        async def next_handler() -> Result[Any] | InputRequiredResult:
            return await _execute_command(
                command_path, kwargs, args, request_context, argv=argv, mcp_context=mcp_context
            )

        # Build the middleware chain from right to left
        handler: Callable[[], Coroutine[Any, Any, Result[Any] | InputRequiredResult]] = next_handler
        for mw in reversed(middleware):
            # Capture current middleware in closure
            def make_handler(
                middleware_fn: CommandMiddleware,
                next_fn: Callable[[], Coroutine[Any, Any, Result[Any] | InputRequiredResult]],
            ) -> Callable[[], Coroutine[Any, Any, Result[Any] | InputRequiredResult]]:
                async def wrapper() -> Result[Any] | InputRequiredResult:
                    return await middleware_fn(command_path, kwargs, args, next_fn)

                return wrapper

            handler = make_handler(mw, handler)

        return await handler()
    return await _execute_command(command_path, kwargs, args, request_context, argv=argv, mcp_context=mcp_context)


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

    if files.truncation_reasons:
        return Result.failure(f"Command discovery was truncated: {command_path}", error_type=ERROR_FILE_ERROR)

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
        **keyword_context(kwargs),
        "elicitation": {"defaulted_forms": {form: True for form in getattr(kwargs, "defaulted_forms", frozenset())}},
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


async def _is_help_command(command_path: str, request_context: RequestContext) -> bool:
    """Check if command_path is a help command or alias."""
    # noinspection PyBroadException
    try:
        session = request_context.session
        commands_dir = request_context.resolve_document_path(COMMANDS_DIR)
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
    request_context: RequestContext,
    argv: Optional[list[str]] = None,
    mcp_context: Context | None = None,
) -> Result[Any] | InputRequiredResult:
    """Execute command without middleware."""
    session = request_context.session
    commands_dir = request_context.resolve_document_path(COMMANDS_DIR)
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
    file_info.resolve(request_context.resolve_document_path, COMMANDS_DIR)

    frontmatter: dict[str, Any] = {}
    try:
        frontmatter = await file_info.get_frontmatter() or {}
    except OSError as e:
        logger.warning(f"Failed to read frontmatter for command {command_path}: {e}.")

    # If raw argv provided, parse arguments using frontmatter argrequired
    if argv is not None:
        argrequired = frontmatter.get("argrequired") if isinstance(frontmatter.get("argrequired"), list) else None
        kwargs, args, parse_errors = parse_command_arguments(argv, argrequired=argrequired)
        if parse_errors:
            error_msg = "; ".join(parse_errors)
            result: Result[Any] = Result.failure(
                f"Argument parsing failed: {error_msg}", error_type=ERROR_VALIDATION, disposition=AGENT_ERROR
            )
            return result

        # Check minimum required positional arguments
        minargs = frontmatter.get("minargs", 0)
        if isinstance(minargs, int) and minargs > 0 and len(args) < minargs:
            usage = frontmatter.get("usage", "")
            msg = f"Missing required argument\n\nUsage: {usage}" if usage else "Missing required argument"
            result = Result.failure(msg, error_type=ERROR_VALIDATION, disposition=AGENT_ERROR)
            return result

    kwargs = _merge_alias_kwargs(default_kwargs=alias_implied_kwargs, override_kwargs=kwargs)

    requirements_context: dict[str, FeatureValue] = await resolve_all_flags(session)
    base_context = await get_template_contexts(session)
    command_context = _build_command_context(base_context, command_path, file_info, kwargs, args, commands)

    # Help describes a command without executing it, so it must not request its
    # execution inputs.
    if kwargs.get("_help"):
        return await get_command_help(session, command_context, commands_dir, request_context.resolve_document_path)
    if await _is_help_command(command_path, request_context) and args:
        return await get_command_help(session, command_context, commands_dir, request_context.resolve_document_path)

    # Resolve feature requirements before pre-render input collection so an
    # excluded entrypoint or partial cannot request input.
    interactive_properties = None
    if "elicitation" in frontmatter or "includes" in frontmatter:
        try:
            interactive_properties = await collect_interactive_document_properties(
                file_info,
                project_flags=requirements_context,
                context=command_context,
                resolver=request_context.get_docroot_resolver(),
            )
        except (OSError, ValueError) as error:
            return Result.failure(
                f"Command preflight failed: {error}", error_type=ERROR_FILE_ERROR, disposition=AGENT_ERROR
            )
    if interactive_properties is not None:
        if interactive_properties.elicitation.diagnostic:
            return Result.failure(interactive_properties.elicitation.diagnostic, error_type=ERROR_VALIDATION)
        try:
            entrypoint_path = file_info.path.relative_to(commands_dir).as_posix()
        except ValueError:
            return Result.failure(
                "Command preflight failed: command source is outside the commands directory.",
                error_type=ERROR_FILE_ERROR,
                disposition=AGENT_ERROR,
            )
        forms = interactive_properties.elicitation.forms
        forms = prepare_command_input(forms, command_context, args, kwargs)
        resolved_kwargs = await resolve_elicitations(
            {"elicitation": forms},
            kwargs,
            mcp_context,
            entrypoint=f"command:{entrypoint_path}",
            args=args,
        )
        if isinstance(resolved_kwargs, (Result, InputRequiredResult)):
            return resolved_kwargs
        kwargs = resolved_kwargs

    if command_path == "openspec/list":
        from mcp_guide.openspec.task import OpenSpecTask

        openspec_task = session.task_manager.get_task_by_type(OpenSpecTask)
        force_refresh = bool(kwargs.get("force", False))
        if openspec_task is not None and (force_refresh or not openspec_task.is_cache_valid()):
            openspec_task.prepare_changes_refresh(force=force_refresh)

    # Refresh the base context after command-specific state changes, then add
    # resolved elicitation keywords for rendering.
    base_context = await get_template_contexts(session)
    command_context = _build_command_context(base_context, command_path, file_info, kwargs, args, commands)

    # Render template using new API
    try:
        rendered = await render_template(
            session,
            file_info=file_info,
            base_dir=file_info.path.parent,
            project_flags=requirements_context,
            context=command_context,
            resolver=request_context.get_docroot_resolver(),
        )
    except FileNotFoundError as e:
        logger.exception(f"Command file not found: {command_path}")
        return Result.failure(
            f"Command file not found: {e}",
            error_type=ERROR_NOT_FOUND,
            disposition=AGENT_ERROR,
        )
    except PermissionError as e:
        logger.exception(f"Permission denied reading command: {command_path}")
        return Result.failure(
            f"Permission denied for command '{file_info.path}': {e}",
            error_type=ERROR_FILE_ERROR,
            disposition=USER_ERROR,
        )
    except RuntimeError as e:
        # Template rendering error (syntax, missing variables, etc.) — agent-fixable:
        # the agent authored or can edit the broken template (see template-support spec).
        logger.exception(f"Template rendering failed for command {command_path}")
        return Result.failure(
            f"Template rendering failed: {e}",
            error_type=ERROR_TEMPLATE,
            disposition=AGENT_ERROR,
        )
    except Exception as e:
        # Unexpected error
        logger.exception(f"Unexpected error rendering command {command_path}")
        return Result.failure(
            f"Unexpected error: {e}",
            error_type=ERROR_FILE_ERROR,
            disposition=UNKNOWN_ERROR,
        )

    if rendered is None:
        # File filtered by requires-* - treat as not found
        return Result.failure(
            f"Command '{command_path}' not found",
            error_type=ERROR_NOT_FOUND,
            disposition=AGENT_ERROR,
        )

    if interactive_properties is not None and interactive_properties.delivery_properties is not None:
        assert rendered.properties is not None
        rendered.properties = DocumentProperties.combine(
            (rendered.properties, interactive_properties.delivery_properties)
        )

    # Check for application-level errors signaled via {{#_error}} lambda
    if rendered.errors:
        errors = rendered.errors
        return Result.failure(
            "\n".join(errors),
            error_type=ERROR_VALIDATION,
            disposition=AGENT_ERROR,
            error_data={"errors": errors},
        )

    # Extract content and instruction from RenderedContent
    result = Result.ok(rendered.content, disposition=rendered.disposition)
    result.instruction = rendered.instruction  # Already has type-based default
    return result


async def _handle_command_request(
    argv: list[str], request_context: RequestContext, mcp_context: Context | None = None
) -> Result[Any] | InputRequiredResult:
    """Handle command-mode request."""
    first_arg = argv[1]
    raw_command_path = first_arg[1:]  # Remove prefix

    if not raw_command_path:
        result: Result[Any] = Result.failure(
            "Command name cannot be empty", error_type=ERROR_VALIDATION, disposition=AGENT_ERROR
        )
        return result

    # Validate and sanitize
    from mcp_guide.commands.security import validate_command_path_full

    error, command_path = validate_command_path_full(raw_command_path)
    if error:
        result = Result.failure(
            f"Security validation failed: {error}", error_type=ERROR_SECURITY, disposition=AGENT_ERROR
        )
        return result

    return await handle_command(command_path, argv=argv[1:], request_context=request_context, mcp_context=mcp_context)


async def _handle_uri_namespace_request(
    argv: list[str], request_context: RequestContext, mcp_context: Context | None = None
) -> Result[Any] | InputRequiredResult:
    """Resolve an underscore- or dollar-prefixed prompt argument as a Guide URI."""
    from mcp_guide.tools.tool_resource import ReadResourceArgs, internal_read_resource

    result = await internal_read_resource(
        ReadResourceArgs(uri=f"guide://{argv[1]}", session_id=request_context.session_id),
        request_context,
        mcp_context=mcp_context,
    )
    return result


async def _handle_content_request(argv: list[str], request_context: RequestContext) -> Result[Any]:
    """Handle content-mode request."""
    # Separate flags from content arguments
    content_args = []
    flags = []

    for arg in argv[1:]:
        if arg.startswith("-"):
            flags.append(arg)
        else:
            content_args.append(arg)

    # Parse flags only (parse_command_arguments expects argv[0] to be a command name it skips)
    kwargs, _, parse_errors = parse_command_arguments([argv[0], *flags])
    if parse_errors:
        error_msg = "; ".join(parse_errors)
        result: Result[str] = Result.failure(
            f"Flag parsing failed: {error_msg}", error_type=ERROR_VALIDATION, disposition=AGENT_ERROR
        )
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
    content_args_obj = ContentArgs(expression=category, pattern=pattern, session_id=request_context.session_id)
    return await internal_get_content(content_args_obj, request_context)


async def _route_guide_request(
    argv: list[str], request_context: RequestContext, mcp_context: Context | None = None
) -> Result[Any] | InputRequiredResult:
    """Route guide request to command or content handler."""
    # Validate arguments
    if len(argv) == 1 or (len(argv) == 2 and argv[1] == ""):
        # Get prompt prefix from session agent info
        prompt_prefix = "@"  # Default
        if request_context.session.agent_info:
            prompt_prefix = (
                request_context.session.agent_info.prompt_prefix.replace("{mcp_name}", get_prompt_name())
                if request_context.session.agent_info.prompt_prefix is not None
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

    # Route URI-compatible command and skill namespaces before content lookup.
    first_arg = argv[1]
    if first_arg.startswith((":", ";")):
        return await _handle_command_request(argv, request_context, mcp_context)
    if first_arg.startswith(("_", "$")):
        return await _handle_uri_namespace_request(argv, request_context, mcp_context)
    else:
        return await _handle_content_request(argv, request_context)


_GUIDE_ARG1_DESCRIPTION = (
    "First argument: a command starting with :, ;, or _ (for example :help or _status); "
    "a skill starting with $ (for example $workflow-status); or a content expression "
    "(collection or category name, optional /pattern)."
)
_GUIDE_ARGN_DESCRIPTION = (
    "Further positional argument in order after arg1. Commands use these as argv; "
    "content requests use them as additional path or expression segments. Skills "
    "and underscore-prefixed commands carry any member path and query arguments "
    "in their URI-compatible first argument. "
    "Stop at the first omitted argument. arga–argf are arguments 10–15."
)


@promptfunc()
async def guide(
    # MCP prompt handlers require explicit parameters - *args not supported
    # MAX_PROMPT_ARGS defined to match the MCP protocol limit
    arg1: Annotated[Optional[str], Field(description=_GUIDE_ARG1_DESCRIPTION)] = None,
    arg2: Annotated[Optional[str], Field(description=_GUIDE_ARGN_DESCRIPTION)] = None,
    arg3: Annotated[Optional[str], Field(description=_GUIDE_ARGN_DESCRIPTION)] = None,
    arg4: Annotated[Optional[str], Field(description=_GUIDE_ARGN_DESCRIPTION)] = None,
    arg5: Annotated[Optional[str], Field(description=_GUIDE_ARGN_DESCRIPTION)] = None,
    arg6: Annotated[Optional[str], Field(description=_GUIDE_ARGN_DESCRIPTION)] = None,
    arg7: Annotated[Optional[str], Field(description=_GUIDE_ARGN_DESCRIPTION)] = None,
    arg8: Annotated[Optional[str], Field(description=_GUIDE_ARGN_DESCRIPTION)] = None,
    arg9: Annotated[Optional[str], Field(description=_GUIDE_ARGN_DESCRIPTION)] = None,
    arga: Annotated[Optional[str], Field(description=_GUIDE_ARGN_DESCRIPTION)] = None,
    argb: Annotated[Optional[str], Field(description=_GUIDE_ARGN_DESCRIPTION)] = None,
    argc: Annotated[Optional[str], Field(description=_GUIDE_ARGN_DESCRIPTION)] = None,
    argd: Annotated[Optional[str], Field(description=_GUIDE_ARGN_DESCRIPTION)] = None,
    arge: Annotated[Optional[str], Field(description=_GUIDE_ARGN_DESCRIPTION)] = None,
    argf: Annotated[Optional[str], Field(description=_GUIDE_ARGN_DESCRIPTION)] = None,
    session_id: Annotated[Optional[str], Field(description=SESSION_ID_DESCRIPTION)] = None,
    *,
    request_context: RequestContext,
    mcp_context: Context | None = None,
) -> object:
    """Access Guide commands and project content.

    Pass arg1 as a command (:help, :status, _help), a skill ($workflow-status), or a
    content expression. Further arg2–argf continue command or content argv in order
    (arga–argf are arguments 10–15). Include session_id from set_project on later calls.
    """
    prompt_name = get_prompt_name()

    session = request_context.session

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
    result = await _route_guide_request(argv, request_context, mcp_context)

    if isinstance(result, InputRequiredResult):
        return result

    # Process result through the task manager
    from mcp_guide.tools.tool_result import prompt_result

    return await prompt_result(prompt_name, result, session=session, session_id=session.session_id)
