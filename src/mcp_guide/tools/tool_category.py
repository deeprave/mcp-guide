# See src/mcp_guide/tools/README.md for tool documentation standards

"""Category management tools."""

from dataclasses import replace
from pathlib import Path
from typing import Any, Optional, Union, cast

from anyio import Path as AsyncPath
from pydantic import Field

from mcp_core.tool_arguments import ToolArguments
from mcp_core.validation import ArgValidationError, validate_description, validate_directory_path, validate_pattern
from mcp_guide.feature_flags.resolution import resolve_flag
from mcp_guide.models import Category, CategoryNotFoundError, FileReadError, Project
from mcp_guide.result import Result
from mcp_guide.result_constants import (
    ERROR_FILE_READ,
    ERROR_NO_PROJECT,
    ERROR_NOT_FOUND,
    ERROR_SAVE,
    INSTRUCTION_FILE_ERROR,
    INSTRUCTION_NOTFOUND_ERROR,
    INSTRUCTION_PATTERN_ERROR,
)
from mcp_guide.server import tools
from mcp_guide.session import get_or_create_session
from mcp_guide.utils.content_common import gather_category_fileinfos, render_fileinfos
from mcp_guide.utils.file_discovery import discover_category_files
from mcp_guide.utils.formatter_selection import ContentFormat
from mcp_guide.utils.frontmatter import get_frontmatter_description_from_file

try:
    from mcp.server.fastmcp import Context
except ImportError:
    Context = None  # type: ignore


__all__ = [
    "internal_category_list",
    "internal_category_add",
    "internal_category_remove",
    "internal_category_change",
    "internal_category_update",
    "internal_category_content",
    "internal_category_list_files",
]


class CategoryListArgs(ToolArguments):
    """Arguments for category_list tool."""

    verbose: bool = Field(default=True, description="If True, return full details; if False, return names only")


class CategoryContentArgs(ToolArguments):
    """Arguments for category_content tool."""

    category: str = Field(description="Name of the category to retrieve content from")
    pattern: str | None = Field(
        default=None, description="Optional glob pattern to override category's default patterns"
    )


class CategoryListFilesArgs(ToolArguments):
    """Arguments for category_list_files tool."""

    name: str = Field(description="Name of the category to list files from")


async def internal_category_list(args: CategoryListArgs, ctx: Optional[Context] = None) -> Result[list]:  # type: ignore
    """List all categories in the current project.

    Args:
        args: Tool arguments with verbose flag
        ctx: MCP Context (auto-injected by FastMCP)

    Returns:
        Result containing:
        - If verbose=True: list of category dictionaries with name, dir, patterns, description
        - If verbose=False: list of category names only
    """
    try:
        session = await get_or_create_session(ctx)
    except ValueError as e:
        return Result.failure(str(e), error_type=ERROR_NO_PROJECT)

    project = await session.get_project()

    categories: Union[list[dict[str, Union[str, list[str], None]]], list[str]]
    if args.verbose:
        categories = cast(
            list[dict[str, Union[str, list[str], None]]],
            [
                {
                    "name": name,  # Inject name from dict key
                    "dir": category.dir,
                    "patterns": list(category.patterns),  # Convert to list[str]
                    "description": category.description,
                }
                for name, category in project.categories.items()  # Use dict.items()
            ],
        )
    else:
        categories = list(project.categories.keys())  # Use dict.keys()

    return Result.ok(categories)


@tools.tool(CategoryListArgs)
async def category_list(args: CategoryListArgs, ctx: Optional[Context] = None) -> str:  # type: ignore
    """List all categories in the current project.

    Retrieves category information from the current project configuration.
    Useful for discovering available categories before accessing content.

    ## JSON Schema

    ```json
    {
      "type": "object",
      "properties": {
        "verbose": {
          "type": "boolean",
          "description": "If True, return full details; if False, return names only"
        }
      }
    }
    ```

    ## Usage Instructions

    ```python
    # List category names only
    await category_list(CategoryListArgs(verbose=False))

    # List full category details
    await category_list(CategoryListArgs(verbose=True))
    ```

    ## Concrete Examples

    ```python
    # Example 1: Get category names for overview
    result = await category_list(CategoryListArgs(verbose=False))
    # Returns: ["docs", "examples", "tests"]

    # Example 2: Get full category information
    result = await category_list(CategoryListArgs(verbose=True))
    # Returns: [{"name": "docs", "dir": "docs", "patterns": ["*.md"], "description": "Documentation files"}]
    ```
    """
    return (await internal_category_list(args, ctx)).to_json_str()


class CategoryAddArgs(ToolArguments):
    """Arguments for category_add tool."""

    name: str = Field(..., description="Name of the category to create")
    dir: Optional[str] = Field(None, description="Directory path relative to docroot (defaults to category name)")
    patterns: list[str] = Field(default_factory=list, description="File patterns to match (e.g., ['*.md', '*.txt'])")
    description: Optional[str] = Field(None, description="Optional description of the category's purpose")


async def internal_category_add(args: CategoryAddArgs, ctx: Optional[Context] = None) -> Result[str]:  # type: ignore
    """Add a new category to the current project.

    Args:
        args: Tool arguments with name, dir, patterns, and description
        ctx: MCP Context (auto-injected by FastMCP)

    Returns:
        Result containing success message
    """

    try:
        session = await get_or_create_session(ctx)
    except ValueError as e:
        return Result.failure(str(e), error_type=ERROR_NO_PROJECT)

    project = await session.get_project()

    try:
        # Validate name is not empty
        if not args.name or not args.name.strip():
            raise ArgValidationError([{"field": "name", "message": "Category name cannot be empty"}])

        # Validate name doesn't start with underscore (reserved for system categories)
        if args.name.startswith("_"):
            raise ArgValidationError(
                [{"field": "name", "message": "Category names cannot start with underscore (reserved for system use)"}]
            )

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
        return e.to_result()

    try:
        # Create category without name field (name becomes dict key)
        category = Category(dir=validated_dir, patterns=args.patterns, description=validated_description)
    except ValueError as e:
        return ArgValidationError([{"field": "name", "message": str(e)}]).to_result()

    # Create the directory if it doesn't exist
    try:
        docroot = Path(await session.get_docroot())
        category_dir = docroot / validated_dir
        await AsyncPath(category_dir).mkdir(parents=True, exist_ok=True)
    except Exception:
        # Directory creation failed (e.g., in test environment) - continue anyway
        # The directory will be created when actually needed for file operations
        pass

    try:
        # Use new dict-based with_category method
        await session.update_config(lambda p: p.with_category(args.name, category))
    except Exception as e:
        return Result.failure(f"Failed to save project configuration: {e}", error_type=ERROR_SAVE)

    return Result.ok(f"Category '{args.name}' added successfully")


@tools.tool(CategoryAddArgs)
async def category_add(args: CategoryAddArgs, ctx: Optional[Context] = None) -> str:  # type: ignore
    """Add a new category to the current project.

    Creates a new category with specified configuration including name,
    directory path, file patterns, and optional description.

    ## JSON Schema

    ```json
    {
      "type": "object",
      "properties": {
        "name": {
          "type": "string",
          "description": "Name of the category to create"
        },
        "dir": {
          "type": "string",
          "description": "Directory path relative to docroot (defaults to category name)"
        },
        "patterns": {
          "type": "array",
          "items": {"type": "string"},
          "description": "File patterns to match (e.g., ['*.md', '*.txt'])"
        },
        "description": {
          "type": "string",
          "description": "Optional description of the category's purpose"
        }
      },
      "required": ["name"]
    }
    ```

    ## Usage Instructions

    ```python
    # Basic category creation
    await category_add(CategoryAddArgs(name="docs"))

    # Category with custom directory and patterns
    await category_add(CategoryAddArgs(
        name="api-docs",
        dir="documentation/api",
        patterns=["*.md", "*.yaml"]
    ))
    ```

    ## Concrete Examples

    ```python
    # Example 1: Create simple documentation category
    result = await category_add(CategoryAddArgs(name="docs"))
    # Creates category "docs" using directory "docs" with default patterns

    # Example 2: Create specialized category with custom configuration
    result = await category_add(CategoryAddArgs(
        name="tutorials",
        dir="content/tutorials",
        patterns=["*.md", "*.rst"],
        description="Step-by-step tutorial content"
    ))
    # Creates category with custom directory and file patterns
    ```
    """
    return (await internal_category_add(args, ctx)).to_json_str()


class CategoryRemoveArgs(ToolArguments):
    """Arguments for category_remove tool."""

    name: str = Field(..., description="Name of the category to remove")


async def internal_category_remove(args: CategoryRemoveArgs, ctx: Optional[Context] = None) -> Result[str]:  # type: ignore
    """Remove a category from the current project.

    Removes the specified category and automatically removes it from all collections.
    Changes are saved to the project configuration immediately.

    Args:
        args: Tool arguments with category name
        ctx: MCP Context (auto-injected by FastMCP)

    Returns:
        Result containing success message

    Examples:
        >>> category_remove(name="docs")
    """

    try:
        session = await get_or_create_session(ctx)
    except ValueError as e:
        return Result.failure(str(e), error_type=ERROR_NO_PROJECT)

    project = await session.get_project()

    # Use dict lookup for O(1) existence check
    if args.name not in project.categories:
        return Result.failure(f"Category '{args.name}' does not exist", error_type=ERROR_NOT_FOUND)

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
        return Result.failure(f"Failed to save project configuration: {e}", error_type=ERROR_SAVE)

    return Result.ok(f"Category '{args.name}' removed successfully")


@tools.tool(CategoryRemoveArgs)
async def category_remove(args: CategoryRemoveArgs, ctx: Optional[Context] = None) -> str:  # type: ignore
    """Remove a category from the current project.

    Removes the specified category and automatically removes it from all collections.
    Changes are saved to the project configuration immediately.

    Args:
        args: Tool arguments with category name
        ctx: MCP Context (auto-injected by FastMCP)

    Returns:
        Result containing success message

    Examples:
        >>> category_remove(name="docs")
    """
    return (await internal_category_remove(args, ctx)).to_json_str()


class CategoryChangeArgs(ToolArguments):
    """Arguments for category_change tool."""

    name: str = Field(..., description="Name of the category to modify")
    new_name: Optional[str] = Field(None, description="New name for the category")
    new_dir: Optional[str] = Field(None, description="New directory path for the category")
    new_patterns: Optional[list[str]] = Field(None, description="New file patterns to replace existing ones")
    new_description: Optional[str] = Field(None, description="New description for the category")


async def internal_category_change(args: CategoryChangeArgs, ctx: Optional[Context] = None) -> Result[str]:  # type: ignore
    """Change properties of an existing category.

    Args:
        args: Tool arguments with name and optional new values
        ctx: MCP Context (auto-injected by FastMCP)

    Returns:
        Result containing success message
    """

    try:
        session = await get_or_create_session(ctx)
    except ValueError as e:
        return Result.failure(str(e), error_type=ERROR_NO_PROJECT)

    project = await session.get_project()

    # Use dict lookup for O(1) existence check
    if args.name not in project.categories:
        return Result.failure(f"Category '{args.name}' does not exist", error_type=ERROR_NOT_FOUND)

    existing_category = project.categories[args.name]

    if args.new_name is None and args.new_dir is None and args.new_patterns is None and args.new_description is None:
        return ArgValidationError(
            [
                {
                    "field": "changes",
                    "message": "At least one change must be provided (new_name, new_dir, new_patterns, or new_description)",
                }
            ]
        ).to_result()

    try:
        if args.new_name is not None:
            # Validate new name is not empty
            if not args.new_name or not args.new_name.strip():
                raise ArgValidationError([{"field": "new_name", "message": "Category name cannot be empty"}])

            # Validate new name doesn't start with underscore (reserved for system categories)
            if args.new_name.startswith("_"):
                raise ArgValidationError(
                    [
                        {
                            "field": "new_name",
                            "message": "Category names cannot start with underscore (reserved for system use)",
                        }
                    ]
                )

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
            if args.new_dir.startswith("_"):
                raise ArgValidationError([{"field": "new_dir", "message": "Directory cannot start with underscore"}])
            validate_directory_path(args.new_dir, default=args.new_dir)

        if args.new_description is not None and args.new_description != "":
            validate_description(args.new_description)

        if args.new_patterns is not None:
            for pattern in args.new_patterns:
                validate_pattern(pattern)

    except ArgValidationError as e:
        return e.to_result()

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
        return ArgValidationError([{"field": "new_name", "message": str(e)}]).to_result()

    # Create the directory if it's being updated
    if args.new_dir is not None:
        try:
            docroot = Path(await session.get_docroot())
            category_dir = docroot / args.new_dir
            await AsyncPath(category_dir).mkdir(parents=True, exist_ok=True)
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
        return Result.failure(f"Failed to save project configuration: {e}", error_type=ERROR_SAVE)

    change_msg = f"Category '{args.name}' updated successfully"
    if args.new_name is not None and args.new_name != args.name:
        change_msg = f"Category '{args.name}' renamed to '{args.new_name}' successfully"

    return Result.ok(change_msg)


@tools.tool(CategoryChangeArgs)
async def category_change(args: CategoryChangeArgs, ctx: Optional[Context] = None) -> str:  # type: ignore
    """Change properties of an existing category.

    Args:
        args: Tool arguments with name and optional new values
        ctx: MCP Context (auto-injected by FastMCP)

    Returns:
        Result containing success message
    """
    return (await internal_category_change(args, ctx)).to_json_str()


class CategoryUpdateArgs(ToolArguments):
    """Arguments for category_update tool."""

    name: str = Field(..., description="Name of the category to update")
    add_patterns: Optional[list[str]] = Field(None, description="File patterns to add to the category")
    remove_patterns: Optional[list[str]] = Field(None, description="File patterns to remove from the category")


async def internal_category_update(args: CategoryUpdateArgs, ctx: Optional[Context] = None) -> Result[str]:  # type: ignore
    """Update category patterns incrementally.

    Args:
        args: Tool arguments with name and pattern changes
        ctx: MCP Context (auto-injected by FastMCP)

    Returns:
        Result containing success message
    """

    try:
        session = await get_or_create_session(ctx)
    except ValueError as e:
        return Result.failure(str(e), error_type=ERROR_NO_PROJECT)

    project = await session.get_project()

    existing_category = project.categories.get(args.name)
    if existing_category is None:
        return Result.failure(f"Category '{args.name}' does not exist", error_type=ERROR_NOT_FOUND)

    if args.add_patterns is None and args.remove_patterns is None:
        return ArgValidationError(
            [
                {
                    "field": "operations",
                    "message": "At least one operation must be provided (add_patterns or remove_patterns)",
                }
            ]
        ).to_result()

    try:
        if args.add_patterns:
            for pattern in args.add_patterns:
                validate_pattern(pattern)
        if args.remove_patterns:
            for pattern in args.remove_patterns:
                validate_pattern(pattern)
    except ArgValidationError as e:
        return e.to_result()

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
        return Result.failure(f"Failed to save project configuration: {e}", error_type=ERROR_SAVE)

    return Result.ok(f"Category '{args.name}' patterns updated successfully")


@tools.tool(CategoryUpdateArgs)
async def category_update(args: CategoryUpdateArgs, ctx: Optional[Context] = None) -> str:  # type: ignore
    """Update category patterns incrementally.

    Args:
        args: Tool arguments with name and pattern changes
        ctx: MCP Context (auto-injected by FastMCP)

    Returns:
        Result containing success message
    """
    result = await internal_category_update(args, ctx)
    return result.to_json_str()


async def internal_category_list_files(
    args: CategoryListFilesArgs,
    ctx: Optional[Context] = None,  # type: ignore[type-arg]
) -> Result[list[dict[str, Any]]]:
    """List all files in a category directory.

    Args:
        args: Tool arguments with category name
        ctx: MCP Context (auto-injected by FastMCP)

    Returns:
        Result containing list of file information
    """
    # Get session
    try:
        session = await get_or_create_session(ctx)
    except ValueError as e:
        return Result.failure(str(e), error_type=ERROR_NO_PROJECT)

    # Get project
    project = await session.get_project()

    # Resolve category
    category = project.categories.get(args.name)
    if category is None:
        result: Result[list[dict[str, Any]]] = Result.failure(
            f"Category '{args.name}' not found in project",
            error_type=ERROR_NOT_FOUND,
            instruction=INSTRUCTION_NOTFOUND_ERROR,
        )
        return result

    # Discover files using **/* pattern to get all files
    docroot = Path(await session.get_docroot())
    category_dir = docroot / category.dir
    files = await discover_category_files(category_dir, ["**/*"])

    # Format as list of file info dictionaries with descriptions
    file_list = []
    for file in files:
        # Extract description from front-matter
        full_path = category_dir / file.path
        description = await get_frontmatter_description_from_file(full_path)

        file_info = {
            "path": file.name,
            "size": file.size,
            "basename": Path(file.name).name,
        }

        # Only add description if it exists
        if description:
            file_info["description"] = description

        file_list.append(file_info)

    return Result.ok(file_list)


@tools.tool(CategoryListFilesArgs)
async def category_list_files(args: CategoryListFilesArgs, ctx: Optional[Context] = None) -> str:  # type: ignore
    """List all files in a category directory.

    Args:
        args: Tool arguments with category name
        ctx: MCP Context (auto-injected by FastMCP)

    Returns:
        Result containing list of file information
    """
    result = await internal_category_list_files(args, ctx)
    return result.to_json_str()


async def internal_category_content(
    args: CategoryContentArgs,
    ctx: Optional[Context] = None,  # type: ignore[type-arg]
) -> Result[str]:
    """Get content from a category.

    Args:
        args: Tool arguments with category name and optional pattern
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

    try:
        # Gather FileInfo using common function
        patterns = [args.pattern] if args.pattern else None
        files = await gather_category_fileinfos(session, project, args.category, patterns)

        # Check for no matches
        if not files:
            message = (
                f"No files matched pattern '{args.pattern}' in category '{args.category}'"
                if args.pattern
                else f"No files found in category '{args.category}'"
            )
            return Result.ok(message, instruction=INSTRUCTION_PATTERN_ERROR)

        # Render using common function
        docroot = Path(await session.get_docroot())
        category = project.categories[args.category]  # We know it exists from gather_category_fileinfos
        category_dir = docroot / category.dir

        # Resolve content format flag
        project_flags = await session.project_flags().list()
        global_flags = await session.feature_flags().list()
        flag_value = resolve_flag("content-format-mime", project_flags, global_flags)

        if flag_value == "plain":
            format_type = ContentFormat.PLAIN
        elif flag_value == "mime":
            format_type = ContentFormat.MIME
        else:
            format_type = ContentFormat.NONE

        content = await render_fileinfos(files, args.category, category_dir, docroot, format_type)

        return Result.ok(content)

    except CategoryNotFoundError as e:
        return Result.failure(
            str(e),
            error_type=ERROR_NOT_FOUND,
            instruction=INSTRUCTION_NOTFOUND_ERROR,
        )
    except FileReadError as e:
        return Result.failure(
            str(e),
            error_type=ERROR_FILE_READ,
            instruction=INSTRUCTION_FILE_ERROR,
        )


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
        Result containing formatted content or error
    """
    result = await internal_category_content(args, ctx)
    return result.to_json_str()
