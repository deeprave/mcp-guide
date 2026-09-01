# See src/mcp_guide/tools/README.md for tool documentation standards

"""Read resource tool for resolving guide:// URIs."""

from pathlib import Path
from typing import Any, Optional
from urllib.parse import parse_qs, urlsplit

from fastmcp import Context
from pydantic import Field

from mcp_guide.config_constants import COMMANDS_DIR
from mcp_guide.core.mcp_log import get_logger
from mcp_guide.core.tool_arguments import ToolArguments
from mcp_guide.core.tool_decorator import toolfunc
from mcp_guide.discovery.commands import discover_commands, normalise_alias_metadata
from mcp_guide.result import Result
from mcp_guide.result_constants import ERROR_VALIDATION
from mcp_guide.session import Session, get_session
from mcp_guide.tools.tool_content import ContentArgs, internal_get_content
from mcp_guide.tools.tool_result import ToolResult, tool_result
from mcp_guide.uri_parser import parse_guide_uri

logger = get_logger(__name__)


def session_id_from_guide_uri(uri: str) -> str | None:
    """Return the optional reserved session ID without interpreting it."""
    values = parse_qs(urlsplit(uri).query, keep_blank_values=True).get("session_id")
    if not values:
        return None
    if len(values) != 1:
        raise ValueError("Resource URI must contain at most one session_id value")
    return values[0]


class ReadResourceArgs(ToolArguments):
    """Arguments for read_resource tool."""

    uri: str = Field(
        ...,
        description="A guide:// URI to resolve. "
        "Content URIs (guide://expression/pattern) return category or collection content. "
        "Command URIs (guide://_command/args?kwargs) execute server commands.",
    )


async def internal_read_resource(
    args: ReadResourceArgs, ctx: Optional[Context] = None, *, session: Session | None = None
) -> Result[Any]:
    """Resolve a guide:// URI and return its content or command output.

    Args:
        args: Tool arguments with URI
        ctx: MCP Context
        session: Already-resolved request Session, when the caller owns one

    Returns:
        Result containing resolved content or command output
    """
    try:
        session_id = args.session_id if args.session_id is not None else session_id_from_guide_uri(args.uri)
        # First parse without command names to determine URI type
        parsed = parse_guide_uri(args.uri)
    except ValueError as e:
        return Result.failure(str(e), error_type=ERROR_VALIDATION)

    if parsed.is_command:
        if ctx is None:
            return Result.failure("Context is required for command URIs", error_type=ERROR_VALIDATION)
        if session is None:
            session = await get_session(ctx, session_id=session_id)
        try:
            docroot = Path(await session.runtime.get_docroot())
            commands_dir = docroot / COMMANDS_DIR
            commands = await discover_commands(commands_dir, session)
            command_names: list[str] = [cmd["name"] for cmd in commands]
            for cmd in commands:
                command_names.extend(cmd.get("aliases", []))
                command_names.extend(alias["path"] for alias in normalise_alias_metadata(cmd.get("alias_metadata", [])))
            parsed = parse_guide_uri(args.uri, command_names)
        except ValueError as e:
            return Result.failure(str(e), error_type=ERROR_VALIDATION)

        # Lazy import avoids a circular import: guide_prompt imports tool modules
        # during prompt setup, while command URI resolution needs handle_command.
        from mcp_guide.prompts.guide_prompt import handle_command

        return await handle_command(
            parsed.expression,
            kwargs=dict(parsed.kwargs),
            args=list(parsed.args),
            ctx=ctx,
            session=session,
            session_id=session_id,
        )

    content_args = ContentArgs(
        expression=parsed.expression,
        pattern=parsed.pattern,
        force=False,
        session_id=session_id,
    )
    return await internal_get_content(content_args, ctx, session=session)


@toolfunc(ReadResourceArgs)
async def read_resource(args: ReadResourceArgs, ctx: Optional[Context] = None) -> ToolResult:
    """Resolve a guide:// URI and return its content or command output.

    Accepts content URIs (guide://expression/pattern) to retrieve category or collection
    content, and command URIs (guide://_command) to execute server commands.
    """
    result = await internal_read_resource(args, ctx)
    return await tool_result("read_resource", result, ctx=ctx, session_id=args.session_id)
