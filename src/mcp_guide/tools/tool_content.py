# See src/mcp_guide/tools/README.md for tool documentation standards

"""Unified content access tool - get_content."""

import contextlib
import time
import zlib
from dataclasses import replace as dc_replace
from enum import Enum
from pathlib import Path
from typing import Optional

from fastmcp import Context
from pydantic import Field

from mcp_guide.content.formatters.selection import ContentFormat, get_formatter_from_flag
from mcp_guide.content.gathering import gather_content
from mcp_guide.content.utils import (
    create_file_read_error_result,
    extract_and_deduplicate_instructions,
    read_and_render_file_contents,
)
from mcp_guide.core.mcp_log import get_logger
from mcp_guide.core.tool_arguments import ToolArguments
from mcp_guide.core.tool_decorator import toolfunc
from mcp_guide.discovery.files import FileInfo
from mcp_guide.filesystem.read_write_security import ReadWriteSecurityPolicy, SecurityError
from mcp_guide.models import CategoryNotFoundError, CollectionNotFoundError, ExpressionParseError, FileReadError
from mcp_guide.models.project import Project
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
from mcp_guide.tools.tool_helpers import get_session_and_project
from mcp_guide.tools.tool_result import parse_options, tool_result

logger = get_logger(__name__)

__all__ = ["ContentArgs", "internal_get_content"]


class StaleState(str, Enum):
    """Staleness state for an export entry."""

    OK = "ok"
    STALE = "stale"
    UNKNOWN = "unknown"


def _build_expression(expression: str, pattern: Optional[str]) -> str:
    """Build a gather expression by appending pattern to each sub-expression."""
    if not pattern:
        return expression
    if "," in expression:
        return ",".join(f"{p.strip()}/{pattern}" for p in expression.split(","))
    return f"{expression}/{pattern}"


def compute_metadata_hash(files: list[FileInfo]) -> Optional[str]:
    """Compute CRC32 hash of file metadata for staleness detection.

    Args:
        files: List of FileInfo objects with paths as-is from discovery

    Returns:
        8-character hex string (CRC32 hash), or None if files is empty
    """
    if not files:
        return None

    entries = [f"{f.path.as_posix()}:{f.mtime.timestamp()}" for f in files]
    entries.sort()
    data = "|".join(entries).encode()
    return f"{zlib.crc32(data):08x}"


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
    force: bool = Field(
        False,
        description="If True, return full content even if exported. "
        "If False (default), return reference to exported content when available.",
    )


async def internal_get_content(
    args: ContentArgs,
    ctx: Optional[Context] = None,
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
    session, project = await get_session_and_project(ctx)
    if project is None:
        return Result.failure("No project available", error_type=ERROR_NO_PROJECT)

    # Get project
    docroot = Path(await session.get_docroot())

    # Check if content has been exported (unless force=True)
    if not args.force:
        export_entry = project.get_export_entry(args.expression, args.pattern)
        if export_entry:
            # Get the original content to extract its instruction
            original_result = await internal_get_content(
                ContentArgs(expression=args.expression, pattern=args.pattern, force=True), ctx
            )
            original_instruction = original_result.instruction if original_result.success else None

            # Content has been exported - return reference instructions
            from mcp_guide.render.context import TemplateContext
            from mcp_guide.render.rendering import render_content

            context = TemplateContext(
                {
                    "export": {
                        "path": export_entry.path,
                        "force": False,
                        "exists": True,
                        "expression": args.expression,
                        "pattern": args.pattern,
                        "instruction": original_instruction,
                    }
                }
            )

            rendered = await render_content("_export", "_system", context)
            if rendered:
                return Result.ok(rendered.content, instruction=rendered.instruction)

    try:
        # Use gather_content to handle comma-separated expressions
        # If a pattern is provided, append it to the expression
        expression = _build_expression(args.expression, args.pattern)

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
    ctx: Optional[Context] = None,
) -> str:
    """Get content from collections and categories.

    Searches collections first, then categories. Aggregates and deduplicates
    results from all matches. Supports pattern filtering for selective content retrieval.
    """
    result = await internal_get_content(args, ctx)
    return await tool_result("get_content", result)


class ExportContentArgs(ToolArguments):
    """Arguments for export_content tool."""

    expression: str = Field(
        ...,
        description="Name to match against collections and categories.",
    )
    pattern: str | None = Field(
        None,
        description="Optional glob pattern to filter files (e.g., '*.md').",
    )
    path: str = Field(
        ...,
        description="Output filename. If no directory component, uses resolved export directory. "
        "Extension .md added if missing.",
    )
    force: bool = Field(
        False,
        description="Overwrite existing file. Default is create-only.",
    )


def _resolve_export_path(path: str, session_agent_name: str, resolved_export_flag: str | None) -> str:
    """Resolve the export path from user input.

    - Ensures .md extension
    - If no directory component, prepends the resolved export directory
    """
    from pathlib import PurePosixPath

    p = PurePosixPath(path)

    # Add .md if no extension
    if not p.suffix:
        p = p.with_suffix(".md")

    # If no directory component, prepend export directory
    if p.parent == PurePosixPath("."):
        if resolved_export_flag:
            export_dir = resolved_export_flag
        else:
            from mcp_guide.feature_flags.constants import AGENT_KNOWLEDGE_DIRS, DEFAULT_EXPORT_DIR

            export_dir = AGENT_KNOWLEDGE_DIRS.get(session_agent_name, DEFAULT_EXPORT_DIR)
        p = PurePosixPath(export_dir) / p

    return str(p)


@toolfunc(ExportContentArgs)
async def export_content(
    args: ExportContentArgs,
    ctx: Optional[Context] = None,
) -> str:
    """Export rendered content to a file for knowledge indexing.

    Reuses get_content logic to gather and render content, then returns it with
    an instruction to write to the resolved path.
    """
    session, project = await get_session_and_project(ctx)
    if project is None:
        return await tool_result("export_content", Result.failure("No project available", error_type=ERROR_NO_PROJECT))

    # Check for existing export (staleness detection)
    export_entry = project.get_export_entry(args.expression, args.pattern)

    # Get rendered content (force=True to bypass export check)
    content_args = ContentArgs(expression=args.expression, pattern=args.pattern, force=True)
    result = await internal_get_content(content_args, ctx)

    if not result.success:
        return await tool_result("export_content", result)

    # Compute metadata hash by gathering files for this expression
    gather_expression = _build_expression(args.expression, args.pattern)

    gathered_files: list[FileInfo] = []
    try:
        gathered_files = await gather_content(session, project, gather_expression)
    except Exception as exc:
        logger.warning(
            "Failed to gather content for metadata hash for expression '%s' (pattern='%s'): %s",
            args.expression,
            args.pattern,
            exc,
            exc_info=True,
        )
    metadata_hash = compute_metadata_hash(gathered_files)

    # Check staleness if not forced (path changes also require force=True)
    if not args.force and export_entry and metadata_hash is not None and metadata_hash == export_entry.metadata_hash:
        # Content hasn't changed since last export - use template for consistency
        # Get original instruction from the content
        original_instruction = result.instruction if result.success else None

        from mcp_guide.render.context import TemplateContext
        from mcp_guide.render.rendering import render_content

        context = TemplateContext(
            {
                "export": {
                    "path": export_entry.path,
                    "force": False,
                    "exists": True,
                    "expression": args.expression,
                    "pattern": args.pattern,
                    "instruction": original_instruction,
                }
            }
        )

        rendered = await render_content("_export", "_system", context)
        if rendered:
            return await tool_result("export_content", Result.ok(rendered.content, instruction=rendered.instruction))

        # Fallback if template fails
        message = f"Content for '{args.expression}' already exported to {export_entry.path}. Use force=True to overwrite or if file is missing."
        return await tool_result("export_content", Result.ok(message))

    # Resolve agent name
    agent_name = ""
    try:
        if session.agent_info:
            agent_name = session.agent_info.normalized_name.lower()
    except (AttributeError, LookupError) as e:
        logger.warning(f"Agent detection failed, using default export path: {e}")

    # Resolve path-export flag
    export_flag = None
    with contextlib.suppress(Exception):
        from mcp_guide.feature_flags.constants import FLAG_PATH_EXPORT
        from mcp_guide.feature_flags.utils import get_resolved_flag_value

        val = await get_resolved_flag_value(session, FLAG_PATH_EXPORT)
        if isinstance(val, str):
            export_flag = val

    # Resolve the output path
    output_path = _resolve_export_path(args.path, agent_name, export_flag)

    # Add the specific file path to allowed_write_paths only if not already covered
    # (project already fetched above)

    # Check if path is already permitted by testing against security policy
    def _apply_updates(p: Project) -> Project:
        pol = ReadWriteSecurityPolicy(
            write_allowed_paths=p.allowed_write_paths,
            additional_read_paths=p.additional_read_paths,
        )
        try:
            pol.validate_write_path(output_path)
        except SecurityError:
            logger.info(f"Added {output_path} to allowed_write_paths")
            p = dc_replace(p, allowed_write_paths=[*p.allowed_write_paths, output_path])
        if metadata_hash is not None:
            p = p.upsert_export_entry(
                args.expression, args.pattern, output_path, metadata_hash, exported_at=time.time()
            )
        return p

    await session.update_config(_apply_updates)

    # Render instruction from template
    from mcp_guide.render.context import TemplateContext
    from mcp_guide.render.rendering import render_content

    context = TemplateContext(
        {
            "export": {
                "path": output_path,
                "force": args.force,
                "exists": export_entry is not None,
                "expression": args.expression,
                "pattern": args.pattern,
            }
        }
    )

    rendered = await render_content("_export", "_system", context)
    instruction = rendered.instruction if rendered else None

    return await tool_result("export_content", Result.ok(result.value, instruction=instruction))


class ListExportsArgs(ToolArguments):
    """Arguments for list_exports tool."""

    glob: str | None = Field(
        None,
        description="Optional glob pattern to filter exports by expression, pattern, or path.",
    )
    options: list[str] = Field(
        default_factory=list,
        description="Display options passed to template (e.g. verbose, table). If non-empty, renders formatted output.",
    )


@toolfunc(ListExportsArgs)
async def list_exports(
    args: ListExportsArgs,
    ctx: Optional[Context] = None,
) -> str:
    """List all tracked content exports with metadata.

    Returns export entries with expression, pattern, path, timestamp, and staleness indicator.
    Optional glob filtering matches against expression, pattern, or path.
    """
    from fnmatch import fnmatch
    from pathlib import PurePath

    session, project = await get_session_and_project(ctx)
    if project is None:
        return await tool_result("list_exports", Result.failure("No project available", error_type=ERROR_NO_PROJECT))

    # Build list of export dicts
    exports = []
    for (expression, pattern), exported_to in project.exports.items():
        # Apply glob filter if provided
        if args.glob:
            matches = False
            # Check expression
            if fnmatch(expression.lower(), args.glob.lower()):
                matches = True
            # Check pattern
            if pattern and fnmatch(pattern.lower(), args.glob.lower()):
                matches = True
            # Check path
            if fnmatch(exported_to.path.lower(), args.glob.lower()):
                matches = True

            if not matches:
                continue

        # Compute staleness
        stale_state = StaleState.OK
        try:
            gather_expression = _build_expression(expression, pattern)
            files = await gather_content(session, project, gather_expression)
            current_hash = compute_metadata_hash(files)
            if current_hash is None:
                stale_state = StaleState.UNKNOWN
            elif current_hash != exported_to.metadata_hash:
                stale_state = StaleState.STALE
        except Exception as e:
            logger.warning("list_exports: staleness check failed for %r: %s", expression, e, exc_info=True)
            stale_state = StaleState.UNKNOWN

        p = PurePath(exported_to.path)
        export_dict = {
            "expression": expression,
            "pattern": pattern,
            "file": p.name,
            "path": str(p.parent),
            "dest": exported_to.path,
            "exported_at": exported_to.exported_at,
            "stale_state": stale_state.value,
        }
        exports.append(export_dict)

    # Render using template if options provided
    if args.options:
        try:
            from mcp_guide.render.context import TemplateContext
            from mcp_guide.render.rendering import render_content

            context = TemplateContext({"exports": exports, **parse_options(args.options)})
            rendered = await render_content("_exports-format", "_system", context)
            if rendered:
                return await tool_result("list_exports", Result.ok(rendered.content))
        except Exception as e:
            logger.warning(f"list_exports: template rendering failed, falling back to JSON: {e}")

    return await tool_result("list_exports", Result.ok(exports))


class RemoveExportArgs(ToolArguments):
    """Arguments for remove_export tool."""

    expression: str = Field(
        ...,
        description="Content expression to remove from export tracking.",
    )
    pattern: str | None = Field(
        None,
        description="Optional pattern to match. Must match exactly if provided.",
    )


@toolfunc(RemoveExportArgs)
async def remove_export(
    args: RemoveExportArgs,
    ctx: Optional[Context] = None,
) -> str:
    """Remove export tracking entry from Project.exports.

    Removes only the tracking entry, not the actual exported file.
    Requires exact match of expression and pattern (if provided).
    """
    session, project = await get_session_and_project(ctx)
    if project is None:
        return await tool_result("remove_export", Result.failure("No project available", error_type=ERROR_NO_PROJECT))

    # Build key
    key = (args.expression, args.pattern)

    # Check if exists
    if key not in project.exports:
        return await tool_result(
            "remove_export",
            Result.failure(
                error=f"Export not found: expression='{args.expression}', pattern={args.pattern}",
                error_type=ERROR_NOT_FOUND,
            ),
        )

    # Remove entry
    await session.update_config(lambda p: dc_replace(p, exports={k: v for k, v in p.exports.items() if k != key}))

    return await tool_result("remove_export", Result.ok(f"Removed export tracking for '{args.expression}'"))
