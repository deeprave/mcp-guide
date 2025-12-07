"""Unified content access tool - get_content."""

from pathlib import Path
from typing import Optional

from pydantic import Field

from mcp_core.result import Result
from mcp_core.tool_arguments import ToolArguments
from mcp_guide.server import tools
from mcp_guide.session import get_or_create_session
from mcp_guide.tools.tool_constants import (
    ERROR_FILE_READ,
    ERROR_NO_PROJECT,
    INSTRUCTION_FILE_ERROR,
    INSTRUCTION_PATTERN_ERROR,
)
from mcp_guide.utils.content_utils import create_file_read_error_result, read_file_contents, resolve_patterns
from mcp_guide.utils.file_discovery import FileInfo, discover_category_files
from mcp_guide.utils.formatter_selection import get_formatter

try:
    from mcp.server.fastmcp import Context
except ImportError:
    Context = None  # type: ignore[misc, assignment]


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
        JSON string with Result containing formatted content or error
    """
    # Get session
    try:
        session = await get_or_create_session(ctx)
    except ValueError as e:
        return Result.failure(str(e), error_type=ERROR_NO_PROJECT).to_json_str()

    # Get project
    project = await session.get_project()
    docroot = Path(session.get_docroot())

    # Collect all FileInfo from collections and categories
    all_files: list[tuple[FileInfo, Path]] = []  # (FileInfo, category_dir) pairs
    file_read_errors: list[str] = []

    # 1. Search collections first
    collection = next((c for c in project.collections if c.name == args.category_or_collection), None)
    if collection:
        for category_name in collection.categories:
            category = next((c for c in project.categories if c.name == category_name), None)
            if not category:
                continue

            patterns = resolve_patterns(args.pattern, category.patterns)
            category_dir = docroot / category.dir
            files = await discover_category_files(category_dir, patterns)

            # Set both category and collection fields
            for file in files:
                file.category = category.name
                file.collection = collection.name

            # Store with category_dir for later de-duplication
            all_files.extend((file, category_dir) for file in files)

    # 2. Search categories
    category = next((c for c in project.categories if c.name == args.category_or_collection), None)
    if category:
        patterns = resolve_patterns(args.pattern, category.patterns)
        category_dir = docroot / category.dir
        files = await discover_category_files(category_dir, patterns)

        # Set category field on all FileInfo objects
        for file in files:
            file.category = category.name

        # Store with category_dir for later de-duplication
        all_files.extend((file, category_dir) for file in files)

    # 3. De-duplicate by absolute path (preserves discovery order)
    seen_paths: set[Path] = set()
    unique_files: list[tuple[FileInfo, Path]] = []

    for file_info, category_dir in all_files:
        absolute_path = category_dir / file_info.path
        if absolute_path not in seen_paths:
            seen_paths.add(absolute_path)
            unique_files.append((file_info, category_dir))

    # 4. Read content for unique files
    if unique_files:
        # Group by category_dir for reading
        files_by_dir: dict[Path, list[FileInfo]] = {}
        for file_info, category_dir in unique_files:
            if category_dir not in files_by_dir:
                files_by_dir[category_dir] = []
            files_by_dir[category_dir].append(file_info)

        # Read content for each group
        final_files: list[FileInfo] = []
        for category_dir, files in files_by_dir.items():
            # Get category name from first file (they're all from same category)
            category_prefix = files[0].category if files else None
            errors = await read_file_contents(files, category_dir, category_prefix=category_prefix)
            file_read_errors.extend(errors)
            final_files.extend(files)

        # Check for file read errors
        if file_read_errors:
            return create_file_read_error_result(
                file_read_errors,
                args.category_or_collection,
                "content",
                ERROR_FILE_READ,
                INSTRUCTION_FILE_ERROR,
            ).to_json_str()

        # 5. Format and return content
        formatter = get_formatter()
        content = await formatter.format(final_files, args.category_or_collection)
        return Result.ok(content).to_json_str()

    # No files found
    return Result.ok(
        f"No matching content found for '{args.category_or_collection}'", instruction=INSTRUCTION_PATTERN_ERROR
    ).to_json_str()
