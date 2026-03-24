# See src/mcp_guide/tools/README.md for tool documentation standards

"""Read resource tool for resolving guide:// URIs."""

from pathlib import Path
from typing import Any, Optional

from pydantic import Field

from mcp_guide.config_constants import COMMANDS_DIR
from mcp_guide.core.mcp_log import get_logger
from mcp_guide.core.tool_arguments import ToolArguments
from mcp_guide.core.tool_decorator import toolfunc
from mcp_guide.discovery.commands import discover_commands
from mcp_guide.prompts.guide_prompt import handle_command
from mcp_guide.result import Result
from mcp_guide.result_constants import ERROR_VALIDATION
from mcp_guide.session import get_session
from mcp_guide.tools.tool_content import ContentArgs, internal_get_content
from mcp_guide.tools.tool_result import tool_result
from mcp_guide.uri_parser import parse_guide_uri

try:
    from fastmcp import Context
except ImportError:
    Context = None  # ty: ignore[invalid-assignment]

logger = get_logger(__name__)


class ReadResourceArgs(ToolArguments):
    """Arguments for read_resource tool."""

    uri: str = Field(
        ...,
        description="A guide:// URI to resolve. "
        "Content URIs (guide://expression/pattern) return category or collection content. "
        "Command URIs (guide://_command/args?kwargs) execute server commands.",
    )


async def internal_read_resource(args: ReadResourceArgs, ctx: Optional[Context] = None) -> Result[Any]:
    """Resolve a guide:// URI and return its content or command output.

    Args:
        args: Tool arguments with URI
        ctx: MCP Context

    Returns:
        Result containing resolved content or command output
    """
    try:
        # First parse without command names to determine URI type
        parsed = parse_guide_uri(args.uri)
    except ValueError as e:
        return Result.failure(str(e), error_type=ERROR_VALIDATION)

    if parsed.is_command:
        if ctx is None:
            return Result.failure("Context is required for command URIs", error_type=ERROR_VALIDATION)
        try:
            session = await get_session(ctx)
            docroot = Path(await session.get_docroot())
            commands_dir = docroot / COMMANDS_DIR
            commands = await discover_commands(commands_dir)
            command_names: list[str] = [cmd["name"] for cmd in commands]
            for cmd in commands:
                command_names.extend(cmd.get("aliases", []))
            parsed = parse_guide_uri(args.uri, command_names)
        except ValueError as e:
            return Result.failure(str(e), error_type=ERROR_VALIDATION)

        return await handle_command(
            parsed.expression,
            kwargs=dict(parsed.kwargs),
            args=list(parsed.args),
            ctx=ctx,
        )

    content_args = ContentArgs(
        expression=parsed.expression,
        pattern=parsed.pattern,
        force=False,
    )
    return await internal_get_content(content_args, ctx)


@toolfunc(ReadResourceArgs)
async def read_resource(args: ReadResourceArgs, ctx: Optional[Context] = None) -> str:
    """Resolve a guide:// URI and return its content or command output.

    Accepts content URIs (guide://expression/pattern) to retrieve category or collection
    content, and command URIs (guide://_command) to execute server commands.
    """
    result = await internal_read_resource(args, ctx)
    return await tool_result("read_resource", result)
