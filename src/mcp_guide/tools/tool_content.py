# See src/mcp_guide/tools/README.md for tool documentation standards

"""Unified content access tool - get_content."""

from pathlib import Path
from typing import Optional

from mcp.server.fastmcp import Context
from pydantic import Field

from mcp_guide.content.formatters.selection import ContentFormat, get_formatter_from_flag
from mcp_guide.content.gathering import gather_content
from mcp_guide.content.utils import (
    create_file_read_error_result,
    extract_and_deduplicate_instructions,
    read_and_render_file_contents,
)
from mcp_guide.core.tool_arguments import ToolArguments
from mcp_guide.core.tool_decorator import toolfunc
from mcp_guide.discovery.files import FileInfo
from mcp_guide.models import CategoryNotFoundError, CollectionNotFoundError, ExpressionParseError, FileReadError
from mcp_guide.render.cache import get_template_context_if_needed
from mcp_guide.result import Result
from mcp_guide.result_constants import (
    ERROR_FILE_READ,
    ERROR_NO_PROJECT,
    ERROR_NOT_FOUND,
    INSTRUCTION_FILE_ERROR,
    INSTRUCTION_NOTFOUND_ERROR,
    INSTRUCTION_PATTERN_ERROR,
)
from mcp_guide.session import get_or_create_session
from mcp_guide.tools.tool_result import tool_result

__all__ = ["ContentArgs", "internal_get_content"]


class ContentArgs(ToolArguments):
    """Arguments for get_content tool.

    Provides unified access to content by searching both collections and categories.
    """

    expression: str = Field(
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

    Searches collections first, then categories. Aggregates and deduplicates
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
    docroot = Path(await session.get_docroot())

    try:
        # Use gather_content to handle comma-separated expressions
        # If a pattern is provided, append it to the expression
        expression = args.expression
        if args.pattern:
            # Apply each pattern to all expressions
            if "," in expression:
                # Multiple expressions - apply the pattern to each
                parts = [f"{part.strip()}/{args.pattern}" for part in expression.split(",")]
                expression = ",".join(parts)
            else:
                # Single expression
                expression = f"{expression}/{args.pattern}"

        files = await gather_content(session, project, expression)

        if not files:
            return Result.ok(
                f"No matching content found for '{args.expression}'", instruction=INSTRUCTION_PATTERN_ERROR
            )

        # Group files by category for reading
        files_by_category: dict[str, list[FileInfo]] = {}
        for file in files:
            category_name = (
                file.category.name if file.category else "unknown"
            )  # Category is always set by gather_content
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
                category_files, category_dir, docroot, template_context, category_prefix=category_name
            )
            file_read_errors.extend(errors)
            final_files.extend(category_files)

        # Check for file read errors
        if file_read_errors:
            return create_file_read_error_result(
                file_read_errors,
                args.expression,
                "content",
                ERROR_FILE_READ,
                INSTRUCTION_FILE_ERROR,
            )

        # Resolve content format flag
        from mcp_guide.feature_flags.constants import FLAG_CONTENT_FORMAT
        from mcp_guide.feature_flags.utils import get_resolved_flag_value

        flag_value = await get_resolved_flag_value(session, FLAG_CONTENT_FORMAT)
        format_type = ContentFormat.from_flag_value(flag_value)

        # Format and return content
        formatter = get_formatter_from_flag(format_type)
        content = await formatter.format(final_files, docroot)

        # Extract instructions from frontmatter
        instruction = extract_and_deduplicate_instructions(final_files)

        return Result.ok(content, instruction=instruction)

    except ExpressionParseError as e:
        return Result.failure(str(e), error_type=ERROR_NO_PROJECT)
    except (CategoryNotFoundError, CollectionNotFoundError) as e:
        return Result.failure(str(e), error_type=ERROR_NOT_FOUND, instruction=INSTRUCTION_NOTFOUND_ERROR)
    except FileReadError as e:
        return Result.failure(str(e), error_type=ERROR_FILE_READ, instruction=INSTRUCTION_FILE_ERROR)


@toolfunc(ContentArgs)
async def get_content(
    args: ContentArgs,
    ctx: Optional[Context] = None,  # type: ignore[type-arg]
) -> str:
    """Get content from collections and categories.

    Searches collections first, then categories. Aggregates and deduplicates
    results from all matches. Supports pattern filtering for selective content retrieval.

    ## JSON Schema

    ```json
    {
      "type": "object",
      "properties": {
        "expression": {
          "type": "string",
          "description": "Name to match against collections and categories. Searches collections first, then categories. Aggregates and deduplicates results from all matches."
        },
        "pattern": {
          "type": "string",
          "description": "Optional glob pattern to filter files (e.g., '*.md'). Overrides default patterns for all matched categories."
        }
      },
      "required": ["expression"]
    }
    ```

    ## Usage Instructions

    ```python
    # Get all content from a category or collection
    await get_content(ContentArgs(expression="docs"))

    # Filter content with pattern
    await get_content(ContentArgs(
        expression="docs",
        pattern="readthis"
    ))
    ```

    ## Concrete Examples

    ```python
    # Example 1: Get all documentation content
    result = await get_content(ContentArgs(expression="docs"))
    # Returns: All files from the docs category with default patterns

    # Example 2: Get only Markdown files from examples
    result = await get_content(ContentArgs(
        expression="examples",
        pattern="readthis"
    ))
    # Returns: Only readthis* files from the examples category

    # Example 3: Get content from a collection
    result = await get_content(ContentArgs(expression="getting-started"))
    # Returns: Combined content from all categories in the collection
    ```
    """
    result = await internal_get_content(args, ctx)
    return await tool_result("get_content", result)
