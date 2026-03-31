"""Shared utilities for content retrieval tools."""

from pathlib import Path
from typing import Any, Optional

import yaml

from mcp_guide.core.mcp_log import get_logger
from mcp_guide.discovery.files import FileInfo
from mcp_guide.render import render_template
from mcp_guide.render.context import TemplateContext
from mcp_guide.render.frontmatter import (
    get_frontmatter_type,
    process_file,
    resolve_instruction,
)
from mcp_guide.render.renderer import is_template_file
from mcp_guide.result import Result
from mcp_guide.result_constants import (
    AGENT_INFO,
    AGENT_INSTRUCTION,
    USER_INFO,
)

logger = get_logger(__name__)

# Precedence for content disposition: higher value wins
_TYPE_PRECEDENCE = {
    USER_INFO: 0,
    AGENT_INFO: 1,
    AGENT_INSTRUCTION: 2,
}
_PRECEDENCE_TO_TYPE = {v: k for k, v in _TYPE_PRECEDENCE.items()}


def extract_and_deduplicate_instructions(files: list[FileInfo]) -> Optional[str]:
    """Extract instructions from frontmatter and deduplicate them.

    Args:
        files: List of FileInfo objects with frontmatter

    Returns:
        Combined instruction string or None if no instructions are found.
        Important instructions (starting with "^") override regular instructions.
    """
    instructions_with_importance = []
    for file_info in files:
        if not file_info.frontmatter:
            continue
        content_type = get_frontmatter_type(file_info.frontmatter)
        instruction, is_important = resolve_instruction(file_info.frontmatter, content_type)
        if instruction:
            instructions_with_importance.append((instruction, is_important))

    return combine_instructions(instructions_with_importance)


def resolve_content_disposition(files: list[FileInfo]) -> str:
    """Resolve the aggregate content disposition across collected files.

    Walks each file's frontmatter type and returns the highest-precedence value.

    Args:
        files: List of FileInfo objects with parsed frontmatter

    Returns:
        Highest-precedence type string, defaulting to user/information
    """
    max_precedence = 0
    for file_info in files:
        if not file_info.frontmatter:
            continue
        if (ft := get_frontmatter_type(file_info.frontmatter)) and ft in _TYPE_PRECEDENCE:
            max_precedence = max(max_precedence, _TYPE_PRECEDENCE[ft])
    return _PRECEDENCE_TO_TYPE[max_precedence]


def prepend_export_frontmatter(
    content: Optional[str], disposition: Optional[str], instruction: Optional[str]
) -> Optional[str]:
    """Prepend YAML frontmatter with disposition and instruction to exported content."""
    if content is None:
        return None
    fm: dict[str, str] = {}
    if disposition:
        fm["type"] = disposition
    if instruction:
        fm["instruction"] = instruction
    if not fm:
        return content
    return f"---\n{yaml.safe_dump(fm, default_flow_style=False, allow_unicode=True, sort_keys=False).rstrip()}\n---\n{content}"


def combine_instructions(instructions_with_importance: list[tuple[str, bool]]) -> Optional[str]:
    """Combine and deduplicate instructions with important/regular priority.

    Args:
        instructions_with_importance: List of (instruction, is_important) tuples

    Returns:
        Combined instruction string or None if no instructions.
        Important instructions (starting with "^") override regular instructions.
    """
    from mcp_guide.render.deduplicate import deduplicate_sentences

    regular_instructions = []
    important_instructions = []
    regular_seen = set()
    important_seen = set()

    for instruction, is_important in instructions_with_importance:
        if is_important:
            if instruction not in important_seen:
                important_instructions.append(instruction)
                important_seen.add(instruction)
        elif instruction not in regular_seen:
            regular_instructions.append(instruction)
            regular_seen.add(instruction)

    # Combine instructions: important overrides regular
    combined = None
    if important_instructions:
        combined = "\n".join(important_instructions)
    elif regular_instructions:
        combined = "\n".join(regular_instructions)

    # Apply sentence-level deduplication to combined instructions
    if combined:
        combined = deduplicate_sentences(combined)

    return combined or None


def resolve_patterns(override_pattern: Optional[str], default_patterns: list[str]) -> list[str]:
    """Resolve patterns with an optional override.

    Args:
        override_pattern: Optional pattern to override defaults
        default_patterns: Default patterns to use if no override

    Returns:
        List of patterns to use
    """
    return [override_pattern] if override_pattern else default_patterns


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
        category_prefix: Optional prefix to add to basenames (e.g. "category")

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

            # noinspection PyBroadException
            try:
                resolved_flags = await resolve_all_flags(template_context.session)  # ty: ignore[invalid-argument-type]
                requirements_context |= resolved_flags
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

    # Process files with the render_template API
    filtered_files = []
    for file_info in files:
        try:
            # Resolve the file path with security validation
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
                    # Use the render_template API (handles parsing and requirements checking)
                    rendered = await render_template(
                        file_info=file_info,
                        base_dir=base_dir,
                        project_flags=requirements_context,
                        context=template_context,
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
                # Non-template files: use process_file
                try:
                    processed = await process_file(file_info, requirements_context, template_context)
                except Exception as e:
                    # File processing raised an exception
                    error_path = f"{category_prefix}/{file_info.name}" if category_prefix else file_info.name
                    logger.exception(f"File processing failed for '{error_path}'")
                    file_read_errors.append(f"'{error_path}': {e}")
                    continue

                if processed is None:
                    # File filtered by requires-*
                    continue

                file_info.content = processed.content
                file_info.frontmatter = processed.frontmatter or file_info.frontmatter

            # Update content_size to reflect the final content size after all processing
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
    """Create a standard file read error result.

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
