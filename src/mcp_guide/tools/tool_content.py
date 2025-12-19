"""Unified content access tool - get_content."""

from pathlib import Path
from typing import Optional

from pydantic import Field

from mcp_core.result import Result
from mcp_core.tool_arguments import ToolArguments
from mcp_guide.models import CategoryNotFoundError, CollectionNotFoundError, ExpressionParseError, FileReadError
from mcp_guide.server import tools
from mcp_guide.session import get_or_create_session
from mcp_guide.tools.tool_constants import (
    ERROR_FILE_READ,
    ERROR_NO_PROJECT,
    ERROR_NOT_FOUND,
    INSTRUCTION_FILE_ERROR,
    INSTRUCTION_NOTFOUND_ERROR,
    INSTRUCTION_PATTERN_ERROR,
)
from mcp_guide.utils.content_common import gather_content
from mcp_guide.utils.content_utils import create_file_read_error_result, read_and_render_file_contents
from mcp_guide.utils.file_discovery import FileInfo
from mcp_guide.utils.formatter_selection import get_formatter
from mcp_guide.utils.template_context_cache import get_template_context_if_needed

try:
    from mcp.server.fastmcp import Context
except ImportError:
    Context = None  # type: ignore[misc, assignment]

__all__ = ["internal_get_content"]


class ContentArgs(ToolArguments):
    """Arguments for get_content tool.

    Provides unified access to content by searching both collections and categories.
    """

    category_or_collection: str = Field(
        ...,
        description="Name to match against collections and categories. "
        "Searches collections first, then categories. "
        "Aggregates and de-duplicates results from all matches.",
    )
    pattern: str | None = Field(
        None,
        description="Optional glob pattern to filter files (e.g., '*.md'). "
        "Overrides default patterns for all matched categories.",
    )


async def internal_get_content(
    args: ContentArgs,
    ctx: Optional[Context] = None,  # type: ignore[type-arg]
) -> Result[str]:
    """Get content from collections and categories (unified access).

    Searches collections first, then categories. Aggregates and de-duplicates
    results from all matches.

    Args:
        args: Tool arguments with name and optional pattern
        ctx: MCP Context (auto-injected by FastMCP)

    Returns:
        Result containing formatted content or error
    """
    # Get session
    try:
        session = await get_or_create_session(ctx)
    except ValueError as e:
        return Result.failure(str(e), error_type=ERROR_NO_PROJECT)

    # Get project
    project = await session.get_project()
    docroot = Path(session.get_docroot())

    try:
        # Use gather_content to handle comma-separated expressions
        # If pattern is provided, append it to the expression
        expression = args.category_or_collection
        if args.pattern:
            # Apply pattern to all expressions
            if "," in expression:
                # Multiple expressions - apply pattern to each
                parts = [f"{part.strip()}/{args.pattern}" for part in expression.split(",")]
                expression = ",".join(parts)
            else:
                # Single expression
                expression = f"{expression}/{args.pattern}"

        files = await gather_content(session, project, expression)

        if not files:
            return Result.ok(
                f"No matching content found for '{args.category_or_collection}'", instruction=INSTRUCTION_PATTERN_ERROR
            )

        # Group files by category for reading
        files_by_category: dict[str, list[FileInfo]] = {}
        for file in files:
            category_name = file.category or "unknown"
            if category_name not in files_by_category:
                files_by_category[category_name] = []
            files_by_category[category_name].append(file)

        # Read content for each category group
        final_files: list[FileInfo] = []
        file_read_errors: list[str] = []

        for category_name, category_files in files_by_category.items():
            category = project.categories.get(category_name)
            if not category:
                raise CategoryNotFoundError(f"Invalid category '{category_name}' found in FileInfo object")

            category_dir = docroot / category.dir
            template_context = await get_template_context_if_needed(category_files, category_name)

            errors = await read_and_render_file_contents(
                category_files, category_dir, template_context, category_prefix=category_name
            )
            file_read_errors.extend(errors)
            final_files.extend(category_files)

        # Check for file read errors
        if file_read_errors:
            return create_file_read_error_result(
                file_read_errors,
                args.category_or_collection,
                "content",
                ERROR_FILE_READ,
                INSTRUCTION_FILE_ERROR,
            )

        # Format and return content
        formatter = get_formatter()
        content = await formatter.format(final_files, args.category_or_collection)
        return Result.ok(content)

    except ExpressionParseError as e:
        return Result.failure(str(e), error_type=ERROR_NO_PROJECT)
    except (CategoryNotFoundError, CollectionNotFoundError) as e:
        return Result.failure(str(e), error_type=ERROR_NOT_FOUND, instruction=INSTRUCTION_NOTFOUND_ERROR)
    except FileReadError as e:
        return Result.failure(str(e), error_type=ERROR_FILE_READ, instruction=INSTRUCTION_FILE_ERROR)


@tools.tool(ContentArgs)
async def get_content(
    args: ContentArgs,
    ctx: Optional[Context] = None,  # type: ignore[type-arg]
) -> str:
    """Get content from collections and categories (unified access).

    Searches collections first, then categories. Aggregates and de-duplicates
    results from all matches.

    Args:
        args: Tool arguments with name and optional pattern
        ctx: MCP Context (auto-injected by FastMCP)

    Returns:
        Result containing formatted content or error
    """
    return (await internal_get_content(args, ctx)).to_json_str()
