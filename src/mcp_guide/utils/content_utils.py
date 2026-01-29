"""Shared utilities for content retrieval tools."""

import re
from pathlib import Path
from typing import Any, Optional

from mcp_guide.core.file_reader import read_file_content
from mcp_guide.core.mcp_log import get_logger
from mcp_guide.render import render_template
from mcp_guide.result import Result
from mcp_guide.utils.file_discovery import FileInfo
from mcp_guide.utils.frontmatter import (
    check_frontmatter_requirements,
    get_frontmatter_instruction,
    get_frontmatter_type,
    get_type_based_default_instruction,
    parse_content_with_frontmatter,
)
from mcp_guide.utils.template_context import TemplateContext
from mcp_guide.utils.template_renderer import is_template_file

logger = get_logger(__name__)

# Pre-compile regex for better performance
IMPORTANT_PREFIX_PATTERN = re.compile(r"^!\s*")


def extract_and_deduplicate_instructions(files: list[FileInfo]) -> Optional[str]:
    """Extract instructions from frontmatter and deduplicate them.

    Args:
        files: List of FileInfo objects with frontmatter

    Returns:
        Combined instruction string or None if no instructions found.
        Important instructions (starting with "!") override regular instructions.
    """
    regular_instructions = []  # Regular instructions
    important_instructions = []  # Important instructions (override regular)
    regular_seen = set()
    important_seen = set()

    for file_info in files:
        if not file_info.frontmatter:
            continue

        # Get explicit instruction from frontmatter
        explicit_instruction = get_frontmatter_instruction(file_info.frontmatter)
        if explicit_instruction and explicit_instruction.strip():
            # Check if instruction is marked as important
            if explicit_instruction.startswith("!"):
                # Remove the "!" and any following whitespace
                clean_instruction = IMPORTANT_PREFIX_PATTERN.sub("", explicit_instruction).strip()
                # Validate that we have actual content after removing the prefix
                if clean_instruction:
                    if clean_instruction not in important_seen:
                        important_instructions.append(clean_instruction)
                        important_seen.add(clean_instruction)
                # If empty after removing prefix, ignore completely (no fallback)
            else:
                if explicit_instruction not in regular_seen:
                    regular_instructions.append(explicit_instruction)
                    regular_seen.add(explicit_instruction)
        else:
            # Get type-based default instruction
            content_type = get_frontmatter_type(file_info.frontmatter)
            default_instruction = get_type_based_default_instruction(content_type)
            if default_instruction and default_instruction not in regular_seen:
                regular_instructions.append(default_instruction)
                regular_seen.add(default_instruction)

    # If we have important instructions, use only those (ignore regular)
    if important_instructions:
        return "\n".join(important_instructions)

    # Otherwise use regular instructions
    if regular_instructions:
        return "\n".join(regular_instructions)

    return None


def resolve_patterns(override_pattern: Optional[str], default_patterns: list[str]) -> list[str]:
    """Resolve patterns with optional override.

    Args:
        override_pattern: Optional pattern to override defaults
        default_patterns: Default patterns to use if no override

    Returns:
        List of patterns to use
    """
    return [override_pattern] if override_pattern else default_patterns


async def read_file_contents(
    files: list[FileInfo],
    base_dir: Path,
    docroot: Path,
    category_prefix: Optional[str] = None,
) -> list[str]:
    """Read content for FileInfo objects and optionally prefix basenames.

    Args:
        files: List of FileInfo objects to read
        base_dir: Base directory for resolving file paths
        docroot: Document root for security validation
        category_prefix: Optional prefix to add to basenames (e.g., "category")

    Returns:
        List of error messages for files that failed to read
    """
    return await read_and_render_file_contents(files, base_dir, docroot, None, category_prefix)


async def read_and_render_file_contents(
    files: list[FileInfo],
    base_dir: Path,
    docroot: Path,
    template_context: Optional[TemplateContext] = None,
    category_prefix: Optional[str] = None,
) -> list[str]:
    """Read and render content for FileInfo objects with template support.

    Args:
        files: List of FileInfo objects to read and render
        base_dir: Base directory for resolving file paths
        docroot: Document root for security validation
        template_context: Optional template context for rendering
        category_prefix: Optional prefix to add to basenames (e.g., "category")

    Returns:
        List of error messages for files that failed to read or render
    """
    file_read_errors: list[str] = []

    # Check if any files are templates to avoid unnecessary context validation
    has_templates = template_context is not None and any(is_template_file(f) for f in files)

    # Build context for requirements checking (resolved flags + workflow)
    requirements_context: dict[str, Any] = {}
    if template_context:
        # Add resolved flags (global + project) to context
        if hasattr(template_context, "session") and template_context.session:
            from mcp_guide.models import resolve_all_flags

            try:
                resolved_flags = await resolve_all_flags(template_context.session)
                requirements_context.update(resolved_flags)
            except Exception:
                # Fallback to project flags if resolution fails
                if hasattr(template_context, "project") and template_context.project:
                    project_flags = getattr(template_context.project, "project_flags", {})
                    requirements_context.update(project_flags)
        elif hasattr(template_context, "project") and template_context.project:
            # Fallback to just project flags if no session available
            project_flags = getattr(template_context.project, "project_flags", {})
            requirements_context.update(project_flags)

        # Add workflow state to requirements context
        if "workflow" in template_context:
            workflow_data = template_context["workflow"]
            requirements_context["workflow"] = workflow_data

    # Process files with new render_template API
    filtered_files = []
    for file_info in files:
        try:
            # Resolve file path with security validation
            file_info.resolve(base_dir, docroot)

            # For template files, use render_template API (it handles parsing)
            if has_templates and is_template_file(file_info):
                # Validate template context type
                if not isinstance(template_context, TemplateContext):
                    error_path = f"{category_prefix}/{file_info.name}" if category_prefix else file_info.name
                    file_read_errors.append(f"'{error_path}' template error: Invalid template context type")
                    continue  # Skip file on validation error

                # Validate context data structure
                try:
                    # Test context access to catch corrupted internal state
                    _ = dict(template_context)
                except (TypeError, ValueError) as e:
                    error_path = f"{category_prefix}/{file_info.name}" if category_prefix else file_info.name
                    file_read_errors.append(f"'{error_path}' template error: Invalid template context data: {str(e)}")
                    continue  # Skip file on validation error

                try:
                    # Use new render_template API (handles parsing and requirements checking)
                    rendered = await render_template(
                        file_info=file_info,
                        base_dir=base_dir,
                        project_flags=requirements_context,
                        context=template_context,
                        docroot=docroot,
                    )
                except Exception as e:
                    # Template rendering raised an exception - log with full context
                    error_path = f"{category_prefix}/{file_info.name}" if category_prefix else file_info.name
                    logger.exception(f"Template rendering failed for '{error_path}'")
                    file_read_errors.append(f"'{error_path}' template error: {e}")
                    continue  # Skip this file entirely

                if rendered is None:
                    # File filtered by requires-* (not an error)
                    continue

                # Extract rendered content and frontmatter
                file_info.content = rendered.content
                file_info.frontmatter = rendered.frontmatter
            else:
                # Non-template files: parse and check requirements
                raw_content = await read_file_content(file_info.path)
                parsed = parse_content_with_frontmatter(raw_content)

                # Check frontmatter requirements - skip file if not satisfied
                if parsed.frontmatter and requirements_context:
                    if not check_frontmatter_requirements(parsed.frontmatter, requirements_context):
                        continue  # Skip this file entirely (filtered by requires-*)

                file_info.content = parsed.content
                file_info.frontmatter = parsed.frontmatter

            # Update content_size to reflect final content size after all processing
            content = file_info.content or ""
            file_info.content_size = len(content.encode("utf-8"))

            # Apply category prefix
            if category_prefix:
                file_info.name = f"{category_prefix}/{file_info.name}"

            filtered_files.append(file_info)

        except (FileNotFoundError, PermissionError, UnicodeDecodeError) as e:
            error_path = f"{category_prefix}/{file_info.name}" if category_prefix else file_info.name
            file_read_errors.append(f"'{error_path}': {e}")
        except Exception as e:
            # Catch any unexpected exceptions to prevent batch termination
            error_path = f"{category_prefix}/{file_info.name}" if category_prefix else file_info.name
            logger.exception(f"Unexpected error processing '{error_path}'")
            file_read_errors.append(f"'{error_path}': Unexpected error: {e}")

    # Update the original files list to only contain filtered files
    files.clear()
    files.extend(filtered_files)

    return file_read_errors


def create_file_read_error_result(
    errors: list[str],
    context_name: str,
    context_type: str,
    error_type: str,
    instruction: str,
) -> Result[str]:
    """Create standardized file read error result.

    Args:
        errors: List of error messages
        context_name: Name of the category or collection
        context_type: Type of context ("category" or "collection")
        error_type: Error type constant
        instruction: Instruction constant

    Returns:
        Result object with error
    """
    error_message = f"Failed to read one or more files in {context_type} '{context_name}': " + "; ".join(errors)
    error_result: Result[str] = Result.failure(
        error_message,
        error_type=error_type,
        instruction=instruction,
    )
    return error_result
