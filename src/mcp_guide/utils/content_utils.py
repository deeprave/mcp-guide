"""Shared utilities for content retrieval tools."""

import re
from pathlib import Path
from typing import Any, Optional

from mcp_core.file_reader import read_file_content
from mcp_guide.result import Result
from mcp_guide.utils.file_discovery import FileInfo
from mcp_guide.utils.frontmatter import (
    get_frontmatter_instruction,
    get_frontmatter_type,
    get_type_based_default_instruction,
    parse_content_with_frontmatter,
)
from mcp_guide.utils.template_context import TemplateContext
from mcp_guide.utils.template_renderer import is_template_file, render_file_content

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
    from mcp_guide.utils.frontmatter import check_frontmatter_requirements

    file_read_errors: list[str] = []

    # Check if any files are templates to avoid unnecessary context validation
    has_templates = template_context is not None and any(is_template_file(f) for f in files)

    # Build context for requirements checking
    requirements_context: dict[str, Any] = {}
    if template_context:
        # Add project flags to context
        if hasattr(template_context, "project") and template_context.project:
            project_flags = getattr(template_context.project, "project_flags", {})
            requirements_context.update(project_flags)

    # Filter files based on frontmatter requirements
    filtered_files = []
    for file_info in files:
        try:
            # Resolve file path with security validation
            file_info.resolve(base_dir, docroot)
            raw_content = await read_file_content(file_info.path)

            # Parse frontmatter and strip it from content
            parsed = parse_content_with_frontmatter(raw_content)
            metadata = parsed.frontmatter
            content = parsed.content

            # Check frontmatter requirements - skip file if not satisfied
            if metadata and not check_frontmatter_requirements(metadata, requirements_context):
                continue  # Skip this file entirely

            file_info.content = content
            file_info.frontmatter = metadata
            filtered_files.append(file_info)

        except Exception as e:
            file_read_errors.append(f"Failed to read {file_info.path}: {e}")
            continue

    # Process filtered files for template rendering
    for file_info in filtered_files:
        try:
            # Render templates if context provided and file is a template
            if has_templates and is_template_file(file_info):
                # Enhanced validation of template context
                if not isinstance(template_context, TemplateContext):
                    error_path = f"{category_prefix}/{file_info.name}" if category_prefix else file_info.name
                    file_read_errors.append(f"'{error_path}': Invalid template context type")
                    continue

                # Validate context data structure
                try:
                    # Test context access to catch corrupted internal state
                    _ = dict(template_context)
                except (TypeError, ValueError) as e:
                    error_path = f"{category_prefix}/{file_info.name}" if category_prefix else file_info.name
                    file_read_errors.append(f"'{error_path}': Invalid template context data: {str(e)}")
                    continue

                render_result = await render_file_content(file_info, template_context, base_dir, docroot)
                if render_result.is_failure():
                    # Skip file on template error for consistency with other validation failures
                    error_path = f"{category_prefix}/{file_info.name}" if category_prefix else file_info.name
                    file_read_errors.append(f"'{error_path}' template error: {render_result.error}")
                    continue
                else:
                    # Update content with rendered version
                    file_info.content = render_result.value

            # Update content_size to reflect final content size after all processing
            content = file_info.content or ""
            file_info.content_size = len(content.encode("utf-8"))

            # Apply category prefix
            if category_prefix:
                file_info.name = f"{category_prefix}/{file_info.name}"

        except (FileNotFoundError, PermissionError, UnicodeDecodeError) as e:
            error_path = f"{category_prefix}/{file_info.name}" if category_prefix else file_info.name
            file_read_errors.append(f"'{error_path}': {e}")

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
