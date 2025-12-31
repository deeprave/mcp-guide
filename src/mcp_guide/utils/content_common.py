"""Common content gathering and rendering functions."""

from pathlib import Path
from typing import Optional

from mcp_guide.models import (
    CategoryNotFoundError,
    DocumentExpression,
    ExpressionParseError,
    FileReadError,
    Project,
)
from mcp_guide.session import Session
from mcp_guide.utils.content_utils import read_and_render_file_contents, resolve_patterns
from mcp_guide.utils.file_discovery import FileInfo, discover_category_files
from mcp_guide.utils.formatter_selection import get_formatter
from mcp_guide.utils.template_context_cache import get_template_context_if_needed


def parse_expression(expression: str) -> list[DocumentExpression]:
    """Parse comma-separated expression into DocumentExpression objects.

    Args:
        expression: User input expression (e.g., "cat1/pat1,cat2,cat3/pat2")

    Returns:
        List of DocumentExpression objects

    Raises:
        ExpressionParseError: If expression is malformed
    """
    if not expression or expression.isspace():
        raise ExpressionParseError("Expression cannot be empty")

    expressions = []

    # Split by comma and process each sub-expression
    for sub_expr in expression.split(","):
        sub_expr = sub_expr.strip()
        if not sub_expr:
            continue  # Skip empty sub-expressions

        # Handle multiple slashes - only first slash is delimiter
        if "/" in sub_expr:
            parts = sub_expr.split("/", 1)  # Split on first slash only
            name = parts[0].strip()
            pattern_part = parts[1].strip() if len(parts) > 1 else ""

            if not name:
                raise ExpressionParseError(f"Empty category/collection name in expression: '{sub_expr}'")

            if pattern_part:
                # Split patterns by + for multi-pattern support
                pattern_list: list[str] = []
                for p in pattern_part.split("+"):
                    if p := p.strip():
                        pattern_list.append(p)

                # If no valid patterns after filtering, treat as None
                patterns: Optional[list[str]] = pattern_list or None
            else:
                patterns = None
        else:
            name = sub_expr.strip()
            patterns = None

            if not name:
                raise ExpressionParseError(f"Empty category/collection name in expression: '{sub_expr}'")

        expressions.append(DocumentExpression(raw_input=sub_expr, name=name, patterns=patterns))

    if not expressions:
        raise ExpressionParseError("No valid expressions found")

    return expressions


async def gather_content(
    session: Session,
    project: Project,
    expression: str,
) -> list[FileInfo]:
    """Process expression and return unified FileInfo list.

    Args:
        session: Current session
        project: Project configuration
        expression: User expression to process

    Returns:
        List of FileInfo objects from all matched categories/collections

    Raises:
        ExpressionParseError: If expression parsing fails
        CategoryNotFoundError: If a referenced category doesn't exist
        CollectionNotFoundError: If a referenced collection doesn't exist
    """
    expressions = parse_expression(expression)
    all_files = []
    # Track processed (category_name, patterns) combinations to allow multiple pattern sets per category
    processed_combinations = set()

    for expr in expressions:
        if expr.name in project.collections:
            # Handle collection - expand to its categories
            collection = project.collections[expr.name]
            for category_name in collection.categories:
                # Create a combination key for deduplication
                patterns_key = tuple(sorted(expr.patterns)) if expr.patterns else None
                combination_key = (category_name, patterns_key)

                if combination_key not in processed_combinations:
                    try:
                        files = await gather_category_fileinfos(session, project, category_name, expr.patterns)
                        # Set the collection field on files
                        for file in files:
                            file.collection = expr.name
                        all_files.extend(files)
                        processed_combinations.add(combination_key)
                    except CategoryNotFoundError as e:
                        # Re-raise with context about which collection referenced the missing category
                        raise CategoryNotFoundError(f"{category_name} (referenced by collection '{expr.name}')") from e

        elif expr.name in project.categories:
            # Handle category - use gather_category_fileinfos
            patterns_key = tuple(sorted(expr.patterns)) if expr.patterns else None
            combination_key = (expr.name, patterns_key)

            if combination_key not in processed_combinations:
                files = await gather_category_fileinfos(session, project, expr.name, expr.patterns)
                all_files.extend(files)
                processed_combinations.add(combination_key)
        else:
            raise CategoryNotFoundError(expr.name)

    # De-duplicate by absolute path
    seen_paths = set()
    unique_files = []
    docroot = Path(await session.get_docroot())

    for file in all_files:
        # Get category to determine directory
        if file.category and file.category in project.categories:
            category = project.categories[file.category]
            category_dir = docroot / category.dir
            absolute_path = file.path

            if absolute_path not in seen_paths:
                seen_paths.add(absolute_path)
                unique_files.append(file)

    return unique_files


async def gather_category_fileinfos(
    session: Session,
    project: Project,
    category_name: str,
    patterns: Optional[list[str]] = None,
    collection_overrides: Optional[dict[str, list[str]]] = None,
) -> list[FileInfo]:
    """Common function to gather FileInfo for a category with pattern resolution.

    Args:
        session: Current session
        project: Project configuration
        category_name: Name of the category
        patterns: Optional patterns to override defaults
        collection_overrides: Optional collection pattern overrides

    Returns:
        List of FileInfo objects for the category

    Raises:
        CategoryNotFoundError: If category doesn't exist
    """
    # Resolve category
    category = project.categories.get(category_name)
    if category is None:
        raise CategoryNotFoundError(category_name)

    # Resolve patterns with three-tier priority:
    # 1. Explicit patterns parameter (highest)
    # 2. Collection overrides (medium)
    # 3. Category defaults (lowest)
    if patterns is not None:
        resolved_patterns = patterns
    elif collection_overrides and category_name in collection_overrides:
        resolved_patterns = collection_overrides[category_name]
    else:
        resolved_patterns = resolve_patterns(None, category.patterns)

    # Discover files
    docroot = Path(await session.get_docroot())
    category_dir = docroot / category.dir
    files = await discover_category_files(category_dir, resolved_patterns)

    # Set category field on all FileInfo objects
    for file in files:
        file.category = category_name

    return files


async def render_fileinfos(
    files: list[FileInfo],
    context_name: str,
    category_dir: Path,
    docroot: Path,
) -> str:
    """Common function to render FileInfo list to formatted content.

    Args:
        files: List of FileInfo objects to render
        context_name: Name for context (category or expression)
        category_dir: Directory path for reading files
        docroot: Document root for security validation

    Returns:
        Formatted content string

    Raises:
        FileReadError: If file reading fails
    """
    if not files:
        return f"No content found for '{context_name}'"

    # Read file content with template rendering
    template_context = await get_template_context_if_needed(files, context_name)
    file_read_errors = await read_and_render_file_contents(files, category_dir, docroot, template_context)

    if file_read_errors:
        raise FileReadError(f"Failed to read files: {'; '.join(file_read_errors)}")

    # Format content
    formatter = get_formatter()
    return await formatter.format(files, context_name)
