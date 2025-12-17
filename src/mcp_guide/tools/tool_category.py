"""Category management tools."""

from dataclasses import replace
from pathlib import Path
from typing import Optional, Union

from pydantic import Field

from mcp_core.result import Result
from mcp_core.tool_arguments import ToolArguments
from mcp_core.validation import ArgValidationError, validate_description, validate_directory_path, validate_pattern
from mcp_guide.models import Category, Project
from mcp_guide.server import tools
from mcp_guide.session import get_or_create_session
from mcp_guide.tools.tool_constants import (
    ERROR_FILE_READ,
    ERROR_NO_PROJECT,
    ERROR_NOT_FOUND,
    ERROR_SAVE,
    INSTRUCTION_FILE_ERROR,
    INSTRUCTION_NOTFOUND_ERROR,
    INSTRUCTION_PATTERN_ERROR,
)
from mcp_guide.utils.content_utils import create_file_read_error_result, read_and_render_file_contents, resolve_patterns
from mcp_guide.utils.file_discovery import discover_category_files
from mcp_guide.utils.formatter_selection import get_formatter
from mcp_guide.utils.template_context_cache import get_template_context_if_needed

try:
    from mcp.server.fastmcp import Context
except ImportError:
    Context = None  # type: ignore


class CategoryListArgs(ToolArguments):
    """Arguments for category_list tool."""

    verbose: bool = True


class CategoryContentArgs(ToolArguments):
    """Arguments for category_content tool."""

    category: str = Field(description="Name of the category to retrieve content from")
    pattern: str | None = Field(
        default=None, description="Optional glob pattern to override category's default patterns"
    )


class CategoryListFilesArgs(ToolArguments):
    """Arguments for category_list_files tool."""

    name: str = Field(description="Name of the category to list files from")


@tools.tool(CategoryListArgs)
async def category_list(args: CategoryListArgs, ctx: Optional[Context] = None) -> str:  # type: ignore
    """List all categories in the current project.

    Args:
        args: Tool arguments with verbose flag
        ctx: MCP Context (auto-injected by FastMCP)

    Returns:
        JSON string with Result containing:
        - If verbose=True: list of category dictionaries with name, dir, patterns, description
        - If verbose=False: list of category names only
    """
    from mcp_guide.session import get_or_create_session

    try:
        session = await get_or_create_session(ctx)
    except ValueError as e:
        return Result.failure(str(e), error_type=ERROR_NO_PROJECT).to_json_str()

    project = await session.get_project()

    categories: Union[list[dict[str, str | list[str] | None]], list[str]]
    if args.verbose:
        categories = [
            {
                "name": name,  # Inject name from dict key
                "dir": category.dir,
                "patterns": list(category.patterns),
                "description": category.description,
            }
            for name, category in project.categories.items()  # Use dict.items()
        ]
    else:
        categories = list(project.categories.keys())  # Use dict.keys()

    return Result.ok(categories).to_json_str()


class CategoryAddArgs(ToolArguments):
    """Arguments for category_add tool."""

    name: str
    dir: Optional[str] = None
    patterns: list[str] = Field(default_factory=list)
    description: Optional[str] = None


@tools.tool(CategoryAddArgs)
async def category_add(args: CategoryAddArgs, ctx: Optional[Context] = None) -> str:  # type: ignore
    """Add a new category to the current project.

    Args:
        args: Tool arguments with name, dir, patterns, and description
        ctx: MCP Context (auto-injected by FastMCP)

    Returns:
        JSON string with Result containing success message
    """
    from mcp_guide.session import get_or_create_session

    try:
        session = await get_or_create_session(ctx)
    except ValueError as e:
        return Result.failure(str(e), error_type=ERROR_NO_PROJECT).to_json_str()

    project = await session.get_project()

    try:
        # Validate name is not empty
        if not args.name or not args.name.strip():
            raise ArgValidationError([{"field": "name", "message": "Category name cannot be empty"}])

        # Validate name doesn't contain invalid characters
        if "/" in args.name or "\\" in args.name or " " in args.name or "!" in args.name:
            raise ArgValidationError(
                [{"field": "name", "message": "Category name cannot contain spaces or special characters"}]
            )

        # Validate name length
        if len(args.name) > 30:
            raise ArgValidationError([{"field": "name", "message": "Category name must be 30 characters or less"}])

        # Use dict lookup for O(1) duplicate detection
        if args.name in project.categories:
            raise ArgValidationError([{"field": "name", "message": f"Category '{args.name}' already exists"}])

        validated_dir = validate_directory_path(args.dir, default=args.name)
        validated_description = validate_description(args.description) if args.description else None

        for pattern in args.patterns:
            validate_pattern(pattern)

    except ArgValidationError as e:
        return e.to_result().to_json_str()

    try:
        # Create category without name field (name becomes dict key)
        category = Category(dir=validated_dir, patterns=args.patterns, description=validated_description)
    except ValueError as e:
        return ArgValidationError([{"field": "name", "message": str(e)}]).to_result().to_json_str()

    # Create the directory if it doesn't exist
    try:
        docroot = Path(session.get_docroot())
        category_dir = docroot / validated_dir
        category_dir.mkdir(parents=True, exist_ok=True)
    except Exception:
        # Directory creation failed (e.g., in test environment) - continue anyway
        # The directory will be created when actually needed for file operations
        pass

    try:
        # Use new dict-based with_category method
        await session.update_config(lambda p: p.with_category(args.name, category))
    except Exception as e:
        return Result.failure(f"Failed to save project configuration: {e}", error_type=ERROR_SAVE).to_json_str()

    return Result.ok(f"Category '{args.name}' added successfully").to_json_str()


class CategoryRemoveArgs(ToolArguments):
    """Arguments for category_remove tool."""

    name: str


@tools.tool(CategoryRemoveArgs)
async def category_remove(args: CategoryRemoveArgs, ctx: Optional[Context] = None) -> str:  # type: ignore
    """Remove a category from the current project.

    Removes the specified category and automatically removes it from all collections.
    Changes are saved to the project configuration immediately.

    Args:
        args: Tool arguments with category name
        ctx: MCP Context (auto-injected by FastMCP)

    Returns:
        JSON string with Result containing success message

    Examples:
        >>> category_remove(name="docs")
    """
    from mcp_guide.session import get_or_create_session

    try:
        session = await get_or_create_session(ctx)
    except ValueError as e:
        return Result.failure(str(e), error_type=ERROR_NO_PROJECT).to_json_str()

    project = await session.get_project()

    # Use dict lookup for O(1) existence check
    if args.name not in project.categories:
        return Result.failure(f"Category '{args.name}' does not exist", error_type=ERROR_NOT_FOUND).to_json_str()

    def remove_category_and_update_collections(p: Project) -> Project:
        p_without_cat = p.without_category(args.name)
        # Update collections to use dict operations
        updated_collections = {
            name: replace(col, categories=[c for c in col.categories if c != args.name])
            for name, col in p_without_cat.collections.items()
        }
        return replace(p_without_cat, collections=updated_collections)

    try:
        await session.update_config(remove_category_and_update_collections)
    except Exception as e:
        return Result.failure(f"Failed to save project configuration: {e}", error_type=ERROR_SAVE).to_json_str()

    return Result.ok(f"Category '{args.name}' removed successfully").to_json_str()


class CategoryChangeArgs(ToolArguments):
    """Arguments for category_change tool."""

    name: str
    new_name: Optional[str] = None
    new_dir: Optional[str] = None
    new_patterns: Optional[list[str]] = None
    new_description: Optional[str] = None


@tools.tool(CategoryChangeArgs)
async def category_change(args: CategoryChangeArgs, ctx: Optional[Context] = None) -> str:  # type: ignore
    """Change properties of an existing category.

    Args:
        args: Tool arguments with name and optional new values
        ctx: MCP Context (auto-injected by FastMCP)

    Returns:
        JSON string with Result containing success message
    """
    from mcp_guide.session import get_or_create_session

    try:
        session = await get_or_create_session(ctx)
    except ValueError as e:
        return Result.failure(str(e), error_type=ERROR_NO_PROJECT).to_json_str()

    project = await session.get_project()

    # Use dict lookup for O(1) existence check
    if args.name not in project.categories:
        return Result.failure(f"Category '{args.name}' does not exist", error_type=ERROR_NOT_FOUND).to_json_str()

    existing_category = project.categories[args.name]

    if args.new_name is None and args.new_dir is None and args.new_patterns is None and args.new_description is None:
        return (
            ArgValidationError(
                [
                    {
                        "field": "changes",
                        "message": "At least one change must be provided (new_name, new_dir, new_patterns, or new_description)",
                    }
                ]
            )
            .to_result()
            .to_json_str()
        )

    try:
        if args.new_name is not None:
            # Validate new name is not empty
            if not args.new_name or not args.new_name.strip():
                raise ArgValidationError([{"field": "new_name", "message": "Category name cannot be empty"}])

            # Validate new name doesn't contain invalid characters
            if "/" in args.new_name or "\\" in args.new_name or " " in args.new_name or "!" in args.new_name:
                raise ArgValidationError(
                    [{"field": "new_name", "message": "Category name cannot contain spaces or special characters"}]
                )

            # Validate new name length
            if len(args.new_name) > 30:
                raise ArgValidationError(
                    [{"field": "new_name", "message": "Category name must be 30 characters or less"}]
                )

            if args.new_name in project.categories and args.new_name != args.name:
                raise ArgValidationError(
                    [{"field": "new_name", "message": f"Category '{args.new_name}' already exists"}]
                )

        if args.new_dir is not None:
            if args.new_dir == "":
                raise ArgValidationError([{"field": "new_dir", "message": "Directory path cannot be empty"}])
            validate_directory_path(args.new_dir, default=args.new_dir)

        if args.new_description is not None and args.new_description != "":
            validate_description(args.new_description)

        if args.new_patterns is not None:
            for pattern in args.new_patterns:
                validate_pattern(pattern)

    except ArgValidationError as e:
        return e.to_result().to_json_str()

    if args.new_description == "":
        final_description = None
    elif args.new_description is not None:
        final_description = args.new_description
    else:
        final_description = existing_category.description

    try:
        updated_category = Category(
            dir=args.new_dir if args.new_dir is not None else existing_category.dir,
            patterns=args.new_patterns if args.new_patterns is not None else existing_category.patterns,
            description=final_description,
        )
    except ValueError as e:
        return ArgValidationError([{"field": "new_name", "message": str(e)}]).to_result().to_json_str()

    # Create the directory if it's being updated
    if args.new_dir is not None:
        try:
            docroot = Path(session.get_docroot())
            category_dir = docroot / args.new_dir
            category_dir.mkdir(parents=True, exist_ok=True)
        except Exception:
            # Directory creation failed (e.g., in test environment) - continue anyway
            # The directory will be created when actually needed for file operations
            pass

    def update_category_and_collections(p: Project) -> Project:
        # Remove old category
        p_without_old = p.without_category(args.name)

        # Add updated category with new or existing name
        final_name = args.new_name if args.new_name is not None else args.name
        p_with_new = p_without_old.with_category(final_name, updated_category)

        # Update collections if category was renamed
        if args.new_name is not None and args.new_name != args.name:
            updated_collections = {
                name: replace(col, categories=[args.new_name if c == args.name else c for c in col.categories])
                for name, col in p_with_new.collections.items()
            }
            return replace(p_with_new, collections=updated_collections)

        return p_with_new

    try:
        await session.update_config(update_category_and_collections)
    except Exception as e:
        return Result.failure(f"Failed to save project configuration: {e}", error_type=ERROR_SAVE).to_json_str()

    change_msg = f"Category '{args.name}' updated successfully"
    if args.new_name is not None and args.new_name != args.name:
        change_msg = f"Category '{args.name}' renamed to '{args.new_name}' successfully"

    return Result.ok(change_msg).to_json_str()


class CategoryUpdateArgs(ToolArguments):
    """Arguments for category_update tool."""

    name: str
    add_patterns: Optional[list[str]] = None
    remove_patterns: Optional[list[str]] = None


@tools.tool(CategoryUpdateArgs)
async def category_update(args: CategoryUpdateArgs, ctx: Optional[Context] = None) -> str:  # type: ignore
    """Update category patterns incrementally.

    Args:
        args: Tool arguments with name and pattern changes
        ctx: MCP Context (auto-injected by FastMCP)

    Returns:
        JSON string with Result containing success message
    """
    from mcp_guide.session import get_or_create_session

    try:
        session = await get_or_create_session(ctx)
    except ValueError as e:
        return Result.failure(str(e), error_type=ERROR_NO_PROJECT).to_json_str()

    project = await session.get_project()

    existing_category = project.categories.get(args.name)
    if existing_category is None:
        return Result.failure(f"Category '{args.name}' does not exist", error_type=ERROR_NOT_FOUND).to_json_str()

    if args.add_patterns is None and args.remove_patterns is None:
        return (
            ArgValidationError(
                [
                    {
                        "field": "operations",
                        "message": "At least one operation must be provided (add_patterns or remove_patterns)",
                    }
                ]
            )
            .to_result()
            .to_json_str()
        )

    try:
        if args.add_patterns:
            for pattern in args.add_patterns:
                validate_pattern(pattern)
        if args.remove_patterns:
            for pattern in args.remove_patterns:
                validate_pattern(pattern)
    except ArgValidationError as e:
        return e.to_result().to_json_str()

    current_patterns = list(existing_category.patterns)

    if args.remove_patterns:
        current_patterns = [p for p in current_patterns if p not in args.remove_patterns]

    if args.add_patterns:
        for pattern in args.add_patterns:
            if pattern not in current_patterns:
                current_patterns.append(pattern)

    # Deduplicate while preserving order
    current_patterns = list(dict.fromkeys(current_patterns))

    updated_category = replace(existing_category, patterns=current_patterns)

    def update_category_patterns(p: Project) -> Project:
        return p.without_category(args.name).with_category(args.name, updated_category)

    try:
        await session.update_config(update_category_patterns)
    except Exception as e:
        return Result.failure(f"Failed to save project configuration: {e}", error_type=ERROR_SAVE).to_json_str()

    return Result.ok(f"Category '{args.name}' patterns updated successfully").to_json_str()


from mcp_guide.utils.frontmatter import get_frontmatter_description


@tools.tool(CategoryListFilesArgs)
async def category_list_files(args: CategoryListFilesArgs, ctx: Optional[Context] = None) -> str:  # type: ignore
    """List all files in a category directory.

    Args:
        args: Tool arguments with category name
        ctx: MCP Context (auto-injected by FastMCP)

    Returns:
        JSON string with Result containing list of file information
    """
    # Get session
    try:
        session = await get_or_create_session(ctx)
    except ValueError as e:
        return Result.failure(str(e), error_type=ERROR_NO_PROJECT).to_json_str()

    # Get project
    project = await session.get_project()

    # Resolve category
    category = project.categories.get(args.name)
    if category is None:
        result: Result[str] = Result.failure(
            f"Category '{args.name}' not found in project",
            error_type=ERROR_NOT_FOUND,
            instruction=INSTRUCTION_NOTFOUND_ERROR,
        )
        return result.to_json_str()

    # Discover files using **/* pattern to get all files
    docroot = Path(session.get_docroot())
    category_dir = docroot / category.dir
    files = await discover_category_files(category_dir, ["**/*"])

    # Format as list of file info dictionaries with descriptions
    file_list = []
    for file in files:
        # Extract description from front-matter
        full_path = category_dir / file.path
        description = await get_frontmatter_description(full_path)

        file_info = {
            "path": str(file.path),
            "size": file.size,
            "basename": file.basename,
        }

        # Only add description if it exists
        if description:
            file_info["description"] = description

        file_list.append(file_info)

    return Result.ok(file_list).to_json_str()


@tools.tool(CategoryContentArgs)
async def category_content(
    args: CategoryContentArgs,
    ctx: Optional[Context] = None,  # type: ignore[type-arg]
) -> str:
    """Get content from a category.

    Args:
        args: Tool arguments with category name and optional pattern
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

    # Resolve category
    category = project.categories.get(args.category)
    if category is None:
        result: Result[str] = Result.failure(
            f"Category '{args.category}' not found in project",
            error_type=ERROR_NOT_FOUND,
            instruction=INSTRUCTION_NOTFOUND_ERROR,
        )
        return result.to_json_str()

    # Get patterns
    patterns = resolve_patterns(args.pattern, category.patterns)

    # Discover files
    docroot = Path(session.get_docroot())
    category_dir = docroot / category.dir
    files = await discover_category_files(category_dir, patterns)

    # Set category field on all FileInfo objects
    for file in files:
        file.category = args.category

    # Check for no matches
    if not files:
        message = (
            f"No files matched pattern '{args.pattern}' in category '{args.category}'"
            if args.pattern
            else f"No files found in category '{args.category}'"
        )
        return Result.ok(message, instruction=INSTRUCTION_PATTERN_ERROR).to_json_str()

    # Read file content with template rendering, collecting any failures
    template_context = await get_template_context_if_needed(files, args.category)
    file_read_errors = await read_and_render_file_contents(files, category_dir, template_context)

    if file_read_errors:
        return create_file_read_error_result(
            file_read_errors, args.category, "category", ERROR_FILE_READ, INSTRUCTION_FILE_ERROR
        ).to_json_str()

    # Format content
    formatter = get_formatter()
    content = await formatter.format(files, args.category)

    return Result.ok(content).to_json_str()
